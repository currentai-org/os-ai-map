"""Read-only platform METADATA over the OSO MCP server, for gates that SQL cannot answer.

## Why this exists next to build/warehouse.py

`build/warehouse.py` is the only supported way to read the warehouse, and it reads *data*:
it speaks SQL to `pyoso` and every question it can answer is a question about rows. A model's
revision number, its hash and its deployed code are not rows in any table. They are asset
metadata, and the only thing that serves them to a CI runner holding nothing but `OSO_API_KEY`
is the MCP server.

So this module is deliberately narrow. It does not query data, it does not write anything, and
it exposes exactly the one read `build/check_mirror_drift.py` needs. Anything wanting rows
should use `build/warehouse.query` and get the cache-busting nonce that comes with it.

## Two things that will waste an afternoon if they are not written down

**A default user agent can be banned at the edge.** `mcp.oso.xyz` sits behind Cloudflare with
a browser-signature rule. `python-urllib/3.12` came back `403 Error 1010:
browser_signature_banned` with `"Do not retry"` in the body, and the same key worked
immediately with a real `User-Agent`. The rule appears to be intermittent or has since
changed — a plain `python-requests` POST was accepted in a later session — so treat this as a
hazard rather than a certainty. `_UA` is cheap insurance either way, and worth keeping because
of how the failure presents: a 403 reads exactly like a bad token, and would send someone to
rotate a key that was never the problem.

**Responses are SSE, not JSON, and `response.text` mangles them.** The server answers a plain
POST with `text/event-stream`, one JSON-RPC envelope per `data:` line, and interleaves
`notifications/message` log frames ahead of the result, so `json.loads(response.text)` fails
on a *successful* call. Worse, `response.text` is wrong even once the frames are split out:
the content type carries no charset, and `requests` then falls back to ISO-8859-1 for any
`text/*`, which turns every em-dash in a model's comments into `â`. That is
not a cosmetic problem for this module's one caller — it makes a byte comparison of deployed
code against a mirror file fail on five of seventeen models with a two-to-six character
difference and no visible cause. `_post` decodes `response.content` as UTF-8 itself.

## The key never reaches a log

Every message raised here passes through `_scrub`, which replaces the token, and the two
raises that wrap a foreign exception use `from None` rather than `from exc` — a chained
`requests` exception prints its own `repr` in a traceback, and a prepared request's `repr` is
one plausible place for an `Authorization` header to surface. Neither the response body nor a
transport error string is under this module's control, and a CI log outlives the key in it.

## What the platform will and will not tell you

`GetDataModel` returns `latestRevision` — its number, hash, language, code and creation time.
It does **not** return release state, and nothing else on the tool surface does either:
`GetAssetChangelog` has a `publishStatus` field, and it is null on every revision of every
model in this org. There is no readable "which revision is released" fact.

That shapes what a drift gate can honestly claim, and `check_mirror_drift` says so in its own
docstring rather than quietly calling the latest revision the released one.
"""

from __future__ import annotations

import json
import os

# A real product name. See the module docstring: a default UA is 403'd at the CDN with an
# error that looks like an auth failure.
_UA = "os-ai-map-mirror-drift/1.0 (+https://github.com/currentai-org/os-ai-map)"
DEFAULT_URL = "https://mcp.oso.xyz/mcp"
PROTOCOL_VERSION = "2025-06-18"


class MCPUnreachable(RuntimeError):
    """The platform could not be reached, or answered something this module cannot parse.

    Held apart from a drift finding on purpose. "The mirror is stale" and "we could not
    tell" are different states, and a gate that reports the second as the first sends a
    maintainer to resync a file that is already correct.
    """


class MCPCallFailed(RuntimeError):
    """The server was reached, answered 200, and refused the call (`isError`).

    Held apart from `MCPUnreachable` because the two send a maintainer somewhere different,
    but they belong to the same *class* of outcome: nothing was read. An expired or rotated
    key arrives here rather than as a 401 — the server answers cheerfully with
    `UNAUTHENTICATED` inside a successful HTTP response — so a caller that lets this escape
    while catching `MCPUnreachable` reports an auth failure as whatever its default exit is.
    `build/check_mirror_drift.py` catches both and exits 2 for either.
    """


class Client:
    """One MCP session. Construct it once and reuse it across models.

    The handshake costs a round trip, and the drift check makes one call per contract, so a
    per-call session would triple the gate's runtime for nothing.
    """

    def __init__(self, url: str | None = None, token: str | None = None):
        import requests

        self.url = url or os.environ.get("OSO_MCP_URL") or DEFAULT_URL
        self.token = token or os.environ.get("OSO_API_KEY") or ""
        if not self.token:
            raise MCPUnreachable("OSO_API_KEY must be set to read platform metadata")
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": _UA,
        })
        self._handshaken = False

    def _scrub(self, text: str) -> str:
        """`text` with the API key replaced, for anything that might be printed.

        Every message this module raises goes through here. Error text carries a response
        body and a `requests` exception string, and neither is under our control: a proxy
        that echoes request headers, or an SDK that puts the prepared request in its
        `repr`, would otherwise put the key in CI logs that outlive the key. Scrubbing at
        the one place messages are built is cheaper than auditing each of them.
        """
        return text.replace(self.token, "<OSO_API_KEY>") if self.token else text

    def _post(self, payload: dict) -> str:
        import requests

        try:
            response = self._session.post(self.url, data=json.dumps(payload), timeout=90)
        except requests.RequestException as exc:
            raise MCPUnreachable(self._scrub(f"POST {self.url} failed: {exc}")) from None
        # Decode explicitly. See the module docstring: requests guesses ISO-8859-1 for a
        # charset-less text/event-stream and silently corrupts every non-ASCII character.
        body = response.content.decode("utf-8", errors="replace")
        if response.status_code >= 400:
            # Surface the body. A Cloudflare 1010 and an expired key are both 403 and the
            # body is the only thing that tells them apart.
            raise MCPUnreachable(self._scrub(
                f"POST {self.url} returned {response.status_code}: {body[:400]}"
            ))
        return body

    def _rpc(self, method: str, params: dict, *, notify: bool = False) -> dict | None:
        payload: dict = {"jsonrpc": "2.0", "method": method, "params": params}
        if not notify:
            payload["id"] = 1
        body = self._post(payload)
        if notify:
            return None
        for line in body.splitlines():
            if not line.startswith("data: "):
                continue
            try:
                frame = json.loads(line[len("data: "):])
            except json.JSONDecodeError:
                # A frame that will not parse is a failure to read, and it must arrive at the
                # caller as one. Left bare, a JSONDecodeError escapes past every handler in
                # check_mirror_drift.main and lands on the drift exit code, which is the one
                # outcome this module exists to keep apart from "we could not tell".
                raise MCPUnreachable(self._scrub(
                    f"{method} returned an unparseable frame: {line[:200]!r}")) from None
            if frame.get("id") != 1:
                continue  # a log notification ahead of the answer
            if "error" in frame:
                raise MCPUnreachable(
                    self._scrub(f"{method} returned a JSON-RPC error: {frame['error']}"))
            return frame.get("result") or {}
        raise MCPUnreachable(
            self._scrub(f"{method} returned no result frame; body began {body[:300]!r}"))

    def _handshake(self) -> None:
        if self._handshaken:
            return
        self._rpc("initialize", {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "os-ai-map", "version": "1"},
        })
        self._rpc("notifications/initialized", {}, notify=True)
        self._handshaken = True

    def call(self, tool: str, variables: dict) -> dict:
        """Run one MCP tool and return its decoded JSON payload.

        Every OSO tool takes its arguments under a single `variables` key — a flat
        `{"id": ...}` is rejected with a pydantic `missing_argument` on `variables`, which
        is a confusing way to be told about one level of nesting.
        """
        self._handshake()
        result = self._rpc("tools/call", {"name": tool, "arguments": {"variables": variables}})
        content = (result or {}).get("content") or []
        text = content[0].get("text", "") if content else ""
        if (result or {}).get("isError"):
            raise MCPCallFailed(self._scrub(f"{tool} failed: {text[:400]}"))
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            raise MCPUnreachable(
                self._scrub(f"{tool} returned non-JSON content: {text[:300]!r}")) from None

    def data_model(self, model_id: str) -> dict | None:
        """The data model node for `model_id`, or None when the platform has no such model.

        None is a finding, not an error: a contract naming a model id the platform does not
        serve is drift of the worst kind — the mirror is anchored to something that no longer
        exists — so the caller reports it rather than crashing on it.
        """
        payload = self.call("GetDataModel", {"id": model_id})
        edges = ((payload or {}).get("dataModels") or {}).get("edges") or []
        return edges[0].get("node") if edges else None
