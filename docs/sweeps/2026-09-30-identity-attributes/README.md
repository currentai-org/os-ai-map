# Identity attributes: country, steward, languages (#684)

Curation batch for [#684](https://github.com/currentai-org/os-ai-map/issues/684): record where an
organization is based, who stewards a product when it is not its owner, and which languages a
dataset serves, as controlled identity attributes rather than openness dimensions. Then retire
`openness.components.context.governance`, which those fields replace.

Branch `claude/happy-noether-2qd7ij`, one PR.

## Decisions

- `country` on an org is an ISO 3166-1 alpha-2 code, checked against
  `sources/snapshots/iso-3166-1.tsv` (Debian iso-codes `data/iso_3166-1.json`, 249 codes).
- `languages` on a `type: dataset` product is a sorted list of ISO 639-3 codes of scope `I`
  (individual) or `M` (macrolanguage), checked against `sources/snapshots/iso-639-3.tab` (SIL
  download, verbatim). Required on every product in `language_specific_datasets`; optional on
  other datasets, set wherever the card or paper names its languages.
- `steward` on a product is an org slug, set only when governance sits with a body other than
  the owning org.
- Individuals (`type: individual`) get no country: a person's location is personal data and the
  question the map asks is about institutions.
- `components.context.governance` is removed in the last commit, by a re-runnable script.

## Ledgers

One JSON object per line. Research writes a ledger; `build/apply_attributes.py` applies it. A row
without an `evidence` URL, or with `confidence: low`, is never applied; it stays in the ledger as
the record of why the field is unset.

`countries/batch-NN.jsonl`, batches listed in `countries/batches.tsv`:

```json
{"slug": "ai2", "country": "US", "evidence": "https://allenai.org/...", "basis": "Seattle, WA address on the contact page", "confidence": "high"}
```

`languages/batch-NN.jsonl`, batches listed in `languages/batches.tsv`:

```json
{"slug": "masakhaner", "languages": ["amh", "hau"], "evidence": "https://huggingface.co/datasets/...", "basis": "language list in the dataset card", "confidence": "high"}
```

`stewards.jsonl`: `{"slug", "steward", "evidence", "basis", "confidence"}`, plus any org files the
steward needs.

## Rules for country

The country of the org's headquarters, its principal place of business. The legal seat stands in
only when no headquarters is stated, so a company incorporated in the Netherlands and run from
California is `US`. A university lab takes its university's
country; a subsidiary recorded as its own org takes its own seat; a foundation takes its legal
seat. A project with no legal entity of its own that a foundation formally hosts (an LF Projects
series, a CNCF project) takes the country of the body that holds it. A community with no legal
entity and no host, an intergovernmental body, or an org that cannot be
identified gets `null`. Evidence is a page that was actually fetched and states the location:
the org's own about, contact, imprint or terms page first, a company or charity register next,
Wikipedia only when nothing primary exists (and then `confidence: medium`).

## Progress

Resume from the first unchecked line. Each line is one commit or more.

- [ ] Phase 0: code-list snapshots, schema, validate, serialize, registry, `apply_attributes`
- [ ] Phase 1: normalize the ten existing free-text countries
- [ ] Phase 2: country ledgers, batches 01-14, applied
- [ ] Phase 3: language ledgers, batches 01-06, applied; `language_specific_datasets` gate on
- [ ] Phase 4: stewards
- [ ] Phase 5: retire `components.context.governance`
- [ ] Phase 6: spot-check, preflight, PR ready
