"""The transport guarantees `build/check_mirror_drift.py` rests on, pinned against a fake session.

Three of these exist because the obvious, idiomatic edit breaks them silently.

The UTF-8 one is the sharpest. `_post` decodes `response.content` rather than reading
`response.text`, and `response.text` is the shorter, more natural line — a comment is the only
thing standing in the way of someone simplifying it back. Nothing would go red: the platform's
`text/event-stream` carries no charset, `requests` then falls back to ISO-8859-1, and every
em-dash in a model's comments becomes mojibake. Five of seventeen code comparisons reported
false drift that way, differing by two to six characters with no visible cause, and it cost an
afternoon to find. So the fake session below returns real UTF-8 bytes under a charset-less
header and the test asserts the round trip.

The key-redaction ones pin `_scrub`. Error text carries a response body and a transport
exception string, neither under this module's control, and a CI log outlives the key printed
into it.

No network. `Client` imports `requests` lazily and only touches `self._session`, so a stub
object with a `post` and a `headers` dict is a complete substitute.
"""

from __future__ import annotations

import json

import pytest
import requests

from build.oso_mcp import _UA, Client, MCPCallFailed, MCPUnreachable

KEY = "oso_test_key_do_not_log_5551234"
EM_DASH_TEXT = "OpenRouter model list — the release-watcher's first leg."


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200):
        self.content = body
        self.status_code = status

    @property
    def text(self) -> str:
        """What `requests` would hand back for a charset-less `text/*`: ISO-8859-1.

        Defined wrongly on purpose. If `_post` ever reads `.text` again, the UTF-8 test
        below fails instead of the bug reaching the mirror comparison.
        """
        return self.content.decode("iso-8859-1")


class FakeSession:
    """Enough of `requests.Session` for `_post`: a headers dict and a `post`."""

    def __init__(self, response=None, raises: Exception | None = None):
        self.headers: dict[str, str] = {}
        self.response = response
        self.raises = raises
        self.posts: list[tuple[str, str]] = []

    def post(self, url, data=None, timeout=None):
        self.posts.append((url, data))
        if self.raises is not None:
            raise self.raises
        return self.response


def client_with(session: FakeSession, *, handshaken: bool = True) -> Client:
    c = Client(url="https://mcp.example/mcp", token=KEY)
    c._session = session
    c._handshaken = handshaken
    return c


def sse(payload: dict) -> bytes:
    """One `data:` frame, UTF-8 encoded, as the server sends it."""
    return b"data: " + json.dumps(payload, ensure_ascii=False).encode("utf-8") + b"\n"


def tool_result(text: str, is_error: bool = False) -> bytes:
    return sse({"jsonrpc": "2.0", "id": 1,
                "result": {"content": [{"type": "text", "text": text}],
                           "isError": is_error}})


# --- the decode, which is the bug that cost an afternoon ---------------------------------

def test_a_charsetless_response_body_round_trips_as_utf8():
    """An em-dash in a model's source must survive the transport unchanged.

    This is the whole reason `_post` does its own decoding. Read as ISO-8859-1 the same
    bytes come back as three mojibake characters, the deployed code stops matching the
    mirror file, and the gate reports drift that is not there.
    """
    payload = json.dumps({"code": EM_DASH_TEXT}, ensure_ascii=False)
    session = FakeSession(FakeResponse(tool_result(payload)))
    got = client_with(session).call("GetDataModel", {"id": "x"})
    assert got["code"] == EM_DASH_TEXT
    assert "—" in got["code"]
    assert "â" not in got["code"], "body was decoded as ISO-8859-1, not UTF-8"


def test_undecodable_bytes_do_not_crash_the_sweep():
    """`errors="replace"` keeps a malformed byte a reportable failure, not a UnicodeError."""
    session = FakeSession(FakeResponse(b"data: {\xff\xfe not json}\n"))
    with pytest.raises(MCPUnreachable):
        client_with(session).call("GetDataModel", {"id": "x"})


# --- the headers -------------------------------------------------------------------------

def test_the_session_sends_a_real_user_agent_and_a_bearer_token():
    """A default UA has been refused at the CDN with a 403 that reads like a bad key."""
    c = Client(url="https://mcp.example/mcp", token=KEY)
    assert c._session.headers["User-Agent"] == _UA
    assert "python-requests" not in _UA and "urllib" not in _UA
    assert c._session.headers["Authorization"] == f"Bearer {KEY}"
    assert "text/event-stream" in c._session.headers["Accept"]


def test_a_missing_key_is_refused_before_any_request(monkeypatch):
    monkeypatch.delenv("OSO_API_KEY", raising=False)
    with pytest.raises(MCPUnreachable, match="OSO_API_KEY"):
        Client(url="https://mcp.example/mcp", token="")


# --- the key never appears in anything printable ----------------------------------------

@pytest.mark.parametrize("session", [
    # A proxy that echoes the request headers back in an error body.
    FakeSession(FakeResponse(f"upstream rejected Authorization: Bearer {KEY}".encode(), 502)),
    # A transport exception whose own string carries the prepared request.
    FakeSession(raises=requests.ConnectionError(f"failed sending Bearer {KEY}")),
    # A 200 refusing the call, echoing the credential it refused.
    FakeSession(FakeResponse(tool_result(f"UNAUTHENTICATED: {KEY}", is_error=True))),
])
def test_the_key_never_appears_in_an_exception_message(session):
    with pytest.raises((MCPUnreachable, MCPCallFailed)) as caught:
        client_with(session).call("GetDataModel", {"id": "x"})
    assert KEY not in str(caught.value)
    assert "<OSO_API_KEY>" in str(caught.value)


def test_the_key_never_appears_in_a_chained_traceback():
    """`from None`, not `from exc`: a chained exception prints its own repr in a traceback.

    Walked the way a traceback walks it. `from None` leaves `__context__` set — the
    interpreter still knows what it was handling — but sets `__suppress_context__`, which is
    what stops the printer following it. So the assertion is about what would actually reach
    a CI log, not about the attribute being absent.
    """
    session = FakeSession(raises=requests.ConnectionError(f"Bearer {KEY}"))
    with pytest.raises(MCPUnreachable) as caught:
        client_with(session).call("GetDataModel", {"id": "x"})
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__, "a traceback would follow __context__ and print the key"

    printed, exc = [], caught.value
    while exc is not None:
        printed.append(str(exc))
        if exc.__cause__ is not None:
            exc = exc.__cause__
        elif exc.__context__ is not None and not exc.__suppress_context__:
            exc = exc.__context__
        else:
            break
    assert not any(KEY in link for link in printed), printed


# --- the two failure classes -------------------------------------------------------------

def test_a_200_carrying_iserror_is_a_call_failure_not_unreachable():
    """What a rotated key looks like: the server answers cheerfully and refuses the call."""
    session = FakeSession(FakeResponse(tool_result("UNAUTHENTICATED", is_error=True)))
    with pytest.raises(MCPCallFailed, match="UNAUTHENTICATED"):
        client_with(session).call("GetDataModel", {"id": "x"})


def test_a_connection_error_is_unreachable():
    session = FakeSession(raises=requests.ConnectionError("no route to host"))
    with pytest.raises(MCPUnreachable, match="no route to host"):
        client_with(session).call("GetDataModel", {"id": "x"})


def test_a_non_200_is_unreachable_and_surfaces_the_body():
    """A Cloudflare 1010 and an expired key are both 403; the body is what separates them."""
    session = FakeSession(FakeResponse(b"error 1010: browser_signature_banned", 403))
    with pytest.raises(MCPUnreachable, match="browser_signature_banned") as caught:
        client_with(session).call("GetDataModel", {"id": "x"})
    assert "403" in str(caught.value)


def test_a_body_with_no_result_frame_is_unreachable():
    """Only log notifications came back. Not a result, so not treated as one."""
    session = FakeSession(FakeResponse(
        sse({"jsonrpc": "2.0", "method": "notifications/message", "params": {}})))
    with pytest.raises(MCPUnreachable, match="no result frame"):
        client_with(session).call("GetDataModel", {"id": "x"})


# --- the shapes the caller depends on ----------------------------------------------------

def test_arguments_are_nested_under_variables():
    """A flat `{"id": ...}` is rejected with a pydantic `missing_argument` on `variables`."""
    session = FakeSession(FakeResponse(tool_result('{"dataModels": {"edges": []}}')))
    client_with(session).call("GetDataModel", {"id": "abc"})
    _url, body = session.posts[-1]
    assert json.loads(body)["params"]["arguments"] == {"variables": {"id": "abc"}}


def test_an_unknown_model_id_returns_none_rather_than_raising():
    """`data_model` reports absence; the caller turns it into a `missing` finding."""
    session = FakeSession(FakeResponse(tool_result('{"dataModels": {"edges": []}}')))
    assert client_with(session).data_model("nope") is None


def test_data_model_unwraps_the_edge_node():
    node = {"id": "m1", "latestRevision": {"revisionNumber": 4}}
    session = FakeSession(FakeResponse(
        tool_result(json.dumps({"dataModels": {"edges": [{"node": node}]}}))))
    assert client_with(session).data_model("m1") == node


def test_the_handshake_runs_once_for_many_calls():
    """The sweep makes one call per contract; a per-call handshake would triple its cost."""
    session = FakeSession(FakeResponse(tool_result('{"dataModels": {"edges": []}}')))
    c = client_with(session, handshaken=False)
    c.data_model("a")
    c.data_model("b")
    methods = [json.loads(body)["method"] for _url, body in session.posts]
    assert methods.count("initialize") == 1
    assert methods.count("notifications/initialized") == 1
    assert methods.count("tools/call") == 2
