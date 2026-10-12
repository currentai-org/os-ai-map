# Organization countries, second batch: 2026-10-12

Follow-up to `docs/sweeps/2026-09-30-identity-attributes/` (#684). That batch gave every org file
then on `main` a `country`, or a ledger row saying why it stays unset. Since then, nineteen
institutional orgs (companies, labs, foundations, a government body) were created by later sweeps
with neither, because only `add-product.md` told an editor to set the field. This batch closes that gap.
The workflow and test fix that stops it recurring is a separate pull request.

The rules are the first batch's (`docs/reference/identity.md`, "Country"): the headquarters or
principal place of business, the legal seat only when no headquarters is stated; a project hosted by
a foundation takes its host's country. The evidence is a fetched page that states a location: the org's own about,
contact, imprint, terms or privacy page. **Governing law is not a seat**, and neither is an "Inc." in
a footer.

## Ledger

`countries/batch-01.jsonl`, in the first batch's row format (`slug`, `country`, `evidence`, `basis`,
`confidence`). Applied with:

```bash
D=docs/sweeps/2026-10-12-org-countries
uv run python -m build.apply_attributes --kind country --ledger "$D/countries/batch-01.jsonl" --write
```

Every page was read on 2026-10-12.

## Outcome

**Set (5):**

| Org | Country | Confidence | Evidence |
|---|---|---|---|
| `common-crawl` | US | high | Beverly Hills, CA address in the privacy policy |
| `openid-foundation` | US | high | San Ramon, CA address in the site footer |
| `ietf` | US | high | IETF Administration LLC, Wilmington, DE, on the contact page |
| `x402-foundation` | US | medium | A series of LF Projects, LLC, a Delaware series LLC; host's country, as for `kubernetes` and `modelcontextprotocol` |
| `mem0` | US | medium | Embedchain, Inc.: every open role in San Francisco, California law |

**Unset, with the reason recorded (14):**

`567-labs`, `bananaml`, `covenant-ai`, `dottxt`, `earendil`, `genlm`, `lightning-labs`, `maritime`,
`musubi-labs`, `orchestrum`, `silverhand`, `tempo`, `typesafe-ai` and `zkprova`. None has a fetched
page that states a location. Several name only a legal form (`dottxt, Inc.`, `Tempo Labs Inc.`) or
only a governing law (Delaware for Maritime, New York for Musubi). A later pass can settle any of
them from a company register.

The four new orgs from #896 that have seats (`novasky-ai`, `prime-intellect`, `nebius`, `mila`) were
set in that pull request and are not repeated here.
