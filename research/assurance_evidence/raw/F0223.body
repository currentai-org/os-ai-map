<!-- mcp-name: io.github.kuzivaai/regula -->
# Regula

**Offline-capable, code-native AI governance scanning. The core scan runs locally, does not upload scanned file contents, and needs no account; telemetry is sent only with explicit opt-in consent. Regula flags patterns that may need review under the EU AI Act, South Korea's AI Basic Act, and Colorado SB 26-189, records the deployment facts code cannot show, and reports insufficient information rather than inventing a score.**

[![Distribution: source](https://img.shields.io/badge/distribution-source%20install-orange.svg)](docs/installation.md)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE.txt)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![CI](https://github.com/kuzivaai/getregula/actions/workflows/ci.yaml/badge.svg)](https://github.com/kuzivaai/getregula/actions)
[![Tests](https://img.shields.io/badge/tests-2936%20collected-blue.svg)](#verified-numbers)
[![Accessibility target: WCAG 2.2 AA](https://img.shields.io/badge/accessibility%20target-WCAG%202.2%20AA-blue.svg)](docs/accessibility/README.md)

---

## Table of contents

- [What it does](#what-it-does)
- [Choose how to start](#choose-how-to-start)
- [Quick start](#quick-start)
- [What Regula tells you](#what-regula-tells-you)
- [Key commands](#key-commands)
- [Who is this for?](#who-is-this-for)
- [What Regula is (and isn't)](#what-regula-is-and-isnt)
- [Bias evaluation: methodology and ethics](#bias-evaluation-methodology-and-ethics)
- [Important limitations](#important-limitations)
- [Verified numbers](#verified-numbers)
- [Contributing](#contributing)
- [Licence](#licence)

---

```console
$ regula check examples/cv-screening-app --scope all

Decision: insufficient_information
Jurisdiction: eu
Rule resolution: unresolved
Facts needed to resolve the next decision: 2
  - is_ai_system: Does the subject meet the governing law's definition of an AI system or regulated automated technology?
  - jurisdiction_in_scope: Does this jurisdiction's territorial and operator scope apply?

Detector observations (not legal facts):

  Detector summary: ANNEX III OR SECURITY PATTERNS
  The scanner found patterns relevant to Annex III or security review.
  Resolve the facts listed above before attaching Article 9 to 15 duties.
  Files scanned:      1
  High-risk:          1
  INFO tier:          1

  HIGH-RISK INDICATORS:
    [INFO] [ 43] app.py — Employment and workers management [plan]

  Detector priority: 0-100 (higher = more code patterns matched; not a correctness probability)
```

*Excerpt from the real output of the command shown, against the tracked fixture
[`examples/cv-screening-app`](examples/cv-screening-app/). The per-category
counts that read zero and the next-steps footer are omitted for length; nothing
else is edited. `scripts/verify_transcripts.py` re-runs this command on every
check and fails if any line above stops appearing in its output.*

---

## What it does

Regula scans a local source-code folder for patterns that may need AI governance review. A questionnaire records facts that code cannot show, such as where and how a system will be used. Results identify candidate risk categories and link to provisions that may be relevant. Regula does not determine legal classification, compliance, or the obligations that apply to a real deployment.

Reference material covers the EU AI Act, South Korea's AI Basic Act (Act No. 20676), and Colorado SB 26-189. The core install has no required third-party runtime dependencies. Optional extras add dependencies, and some optional commands or configured features can contact external services. Assess territorial scope and data-processing duties independently.

In plain English: give Regula a source-code folder and answer questions about how the system will be used. It returns possible issues and a review trail so a developer, governance lead, or adviser can decide what to investigate next. A scan with no findings does not prove that a system is compliant or low risk.

## Choose how to start

| If you want to… | Start here |
|---|---|
| Explore the questions without installing anything | The browser assessment source is in [`site/assess/`](site/assess/). The public Pages deployment is currently unavailable; when restored, it records declared context for review but does not inspect your repository or make a legal determination. |
| Check a local codebase | Follow the [Quick start](#quick-start), then run `regula check .`. |
| Evaluate Regula before adopting it | Follow the [10-minute example journey](examples/cv-screening-app/) and read the [documented limitations and verification evidence](docs/TRUST.md). |
| Add a repeatable team check | Use the [CI/CD example](#cicd) and review the exit-code policy before making it blocking. |
| Prepare material for a human reviewer | Generate a reviewer-completable evidence scaffold, then complete and validate its contextual fields. |

## Quick start

```bash
pipx install git+https://github.com/kuzivaai/getregula.git@main
```

PyPI distribution is currently unavailable. The command above installs a moving public source reference; pin a reviewed commit hash for reproducible use. See [`docs/installation.md`](docs/installation.md) for the verified status and alternatives.

**Not sure if the AI Act applies?** No code needed:
```bash
regula assess               # record declared context for human review
regula assess --save-facts  # and write the answers where `regula check` reads them
```

The scan tells you which facts it needs and cannot get from code. You supply
them, and the decision moves:

```bash
regula check . --list-facts                     # every fact id the model defines
regula check . --fact is_ai_system=yes \
               --fact jurisdiction_in_scope=yes # declare them for one run
```

Declared facts are **yours**, not Regula's. Each is stored with who declared it,
through which command, in answer to which question, and when, in
`.regula/facts.json`, and the scan prints that provenance beside the decision.
`unknown` is an answer and is never read as `no`. A declared fact can move a
decision from `insufficient_information` to an indication; it does not produce a
risk tier, a compliance score, a readiness percentage or an effort estimate.

**Want to scan your code?**
```bash
regula check .              # 423 tier patterns, 8 language families; runtime varies
regula check . --jurisdictions eu,korea,colorado  # selected reference mappings
```

**Need a review pack?**
```bash
regula evidence-pack --project .   # reviewer-completable evidence scaffold
regula conform --sign --timestamp  # integrity metadata (requires regula[signing])
```

Generated files are inputs to human review, not an audit opinion, certification, or proof of compliance.

**Just want to see it work?** (requires the cloned repo :  `examples/` is not bundled in the pip package)
```bash
git clone https://github.com/kuzivaai/getregula && cd getregula
regula demo                 # scan a bundled example project
```

### Install details

The recommended install is **pipx** :  it isolates Regula from your system Python and avoids the `externally-managed-environment` error on Ubuntu 22.04+, Debian 12+, Fedora, Arch, and Homebrew Python.

If you don't have pipx yet, install it first (one-time):

| Platform | Install pipx |
|---|---|
| macOS | `brew install pipx && pipx ensurepath` |
| Debian / Ubuntu | `sudo apt install pipx && pipx ensurepath` |
| Fedora | `sudo dnf install pipx && pipx ensurepath` |
| Arch | `sudo pacman -S python-pipx && pipx ensurepath` |
| Windows | `python -m pip install --user pipx && python -m pipx ensurepath` |

**Already using uv?** `uvx --from git+https://github.com/kuzivaai/getregula.git@main regula` runs the public source without a persistent install. Or install it with `uv tool install git+https://github.com/kuzivaai/getregula.git@main`.

**Running inside a venv or conda env?** Use `pip install git+https://github.com/kuzivaai/getregula.git@main`. The PEP 668 restriction applies to managed system Python, not an activated virtual environment.

See [`docs/installation.md`](docs/installation.md) for troubleshooting (`externally-managed-environment`, `command not found: regula` after install, PATH setup per shell).

### Try it against a known high-risk fixture:

```bash
regula check examples/cv-screening-app --scope all
```

The `--scope all` flag is needed because Regula's default scope (`production`) skips example directories. This fixture intentionally contains employment-related code indicators that exercise the Annex III Category 4 detector; the resulting label is a detector observation, not a legal determination.

See [`examples/`](examples/) for runnable reference projects covering prohibited-practice, high-risk, transparency, and no-elevated-indicator scenarios, or walk through the full 10-minute evaluation journey in [`examples/cv-screening-app/`](examples/cv-screening-app/) :  install, scan, plan, gap, conform, verify, handoff to red-team tooling.

For a deeper first-time-user walk-through (policy tuning, CI integration, baselining) see [`docs/QUICKSTART.md`](docs/QUICKSTART.md). The full documentation is indexed by type (tutorials / how-to / reference / explanation) in [`docs/README.md`](docs/README.md).

### CI/CD

```yaml
# .github/workflows/regula.yaml
name: AI Governance Check
on: [push, pull_request]
jobs:
  regula:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: kuzivaai/getregula@v1
        with:
          path: '.'
          upload-sarif: 'true'
          fail-on-prohibited: 'true'
```

## What Regula tells you

The EU AI Act defines four risk tiers. Regula maps code patterns to each:

| Tier | Action | What it means |
|------|--------|---------------|
| **Potentially prohibited** (Article 5) | Block indicator | Reports code patterns associated with listed practices for urgent contextual review. |
| **Potentially high-risk** (Article 6 and Annex III) | Warn + review map | Reports candidate use categories and maps provisions that may be relevant if a reviewer confirms the legal classification. |
| **Potential transparency duty** (Article 50) | Transparency indicator | Reports chatbot, synthetic-content and related implementation signals; the applicable paragraph and exceptions require review. |
| **No elevated code indicator** | Log only | Means the scanner did not observe a configured elevated indicator. It does not establish minimal-risk status or absence of legal duties. |

Every finding includes the relevant Article reference and explains when exceptions may apply. Regula flags patterns -- it does not make legal determinations.

**Coverage has explicit levels.** Regula has an evidence-gated questionnaire
and decision model for the EU AI Act, South Korea's AI Basic Act (Act No.
20676), and Colorado SB 26-189. It separately maps findings to selected control
or provision references in 13 frameworks, and publishes dated regional
trackers. A crosswalk or tracker is not an executable applicability decision or
a compliance assessment. See [product coverage and user
journeys](docs/PRODUCT_COVERAGE_AND_JOURNEYS.md) for the current capability
matrix and claim boundary. Use `--jurisdictions` on `regula check` to filter
selected reference mappings; that option also accepts `uk`, `brazil`, `nist`,
and `iso`, but it does not run an applicability decision. Use `--jurisdiction
eu`, `korea`, or `colorado` on `regula assess` for the three implemented
decision-support configurations.

**Developer guide sources:**
[Python](site/guides/eu-ai-act-python.html) |
[JavaScript](site/guides/eu-ai-act-javascript.html) |
[Healthcare](site/guides/eu-ai-act-healthcare.html) |
[Recruitment](site/guides/eu-ai-act-recruitment-hiring.html) |
[Article 5](site/guides/article-5-prohibited-practices.html) |
[Article 9](site/guides/article-9-risk-management.html) |
[Article 14](site/guides/article-14-human-oversight.html) |
[Article 50](site/guides/article-50-transparency.html)

## Key commands

| Command | What it does |
|---------|-------------|
| `regula` | Scan the current directory, show an indicator summary and next steps |
| `regula check .` | Detailed risk scan with per-file findings |
| `regula comply` | EU AI Act obligation evidence and unresolved facts; `--article 50` separates declared applicability facts from static implementation signals |
| `regula gap --project .` | Compliance gap assessment against Articles 9-15 |
| `regula plan --project .` | Prioritised remediation plan based on gap results |
| `regula fix --project .` | Generate compliance fix scaffolds for findings |
| `regula evidence-pack --project .` | Reviewer-completable evidence scaffold with integrity metadata |
| `regula conform --project .` | Article 43 conformity assessment evidence pack |
| `regula dpv --project .` | Export the risk indication as DPV-AIAct JSON-LD (aligned to the DPVCG EU-AIAct vocabulary) for RDF/GRC tooling |
| `regula check --ci .` | CI mode -- exit code 1 on any WARN or BLOCK finding, SARIF output |
| `regula assess` | Structured declared-context questionnaire for applicability and risk review |
| `regula demo` | Scan a bundled example project -- zero-commitment trial |
| `regula api-server` | Start the REST API (localhost:8487) with web dashboard |
| `regula conform --organisational` | Governance self-assessment for Articles 9/17/27/72 |
| `regula questionnaire` | Context-driven risk assessment questionnaire (also via REST API) |
| `regula exempt` | Article 6(3) high-risk exemption decision tree |
| `regula oversight .` | Article 14 human oversight analysis (cross-file flow tracing) |
| `regula guardrails .` | Article 15 guardrail implementation coverage detection |
| `regula owasp-agentic` | OWASP Top 10 for Agentic Applications assessment |
| `regula monitor` | Analyse locally recorded agent/tool events for selected Article 12 record-keeping signals; it does not observe a running system by itself |
| `regula gdpr` | GDPR cross-reference scan ([14 focused checks](scripts/gdpr_scan.py), 4 AI Act/GDPR hotspots) |
| `regula bias` | CrowS-Pairs bias evaluation (1,508 sentence pairs) with optional BBQ benchmark. Aligned with Digital Omnibus bias-testing safeguards (Article 4a, COM(2025)836). |
| `regula mcp-server` | MCP server (JSON-RPC stdio) exposing three tools :  `regula_check`, `regula_classify`, `regula_gap` :  for Claude Code, Cursor, and other MCP clients |
| `regula install <integration>` | Set up the pre-commit framework or direct Git hook integration |

Regula has 62 commands in total. Run `regula --help-all` for the full list, or see [`docs/cli-reference.md`](docs/cli-reference.md).

### REST API and web dashboard

For GRC integration or non-terminal users:

```bash
python3 scripts/api_server.py --port 8487
# Open http://localhost:8487/v1/dashboard
```

Seven endpoints: `/health`, `/v1/check`, `/v1/classify`, `/v1/gap`, `/v1/questionnaire`, `/v1/questionnaire/evaluate`, `/v1/dashboard`. All return the same JSON envelope as the CLI. No auth -- run behind a reverse proxy for remote access.

## Who is this for?

- **Builders and maintainers** who need an initial list of source-code signals to investigate before contextual and legal review.
- **Governance and assurance reviewers** who need observations, declared facts, unresolved questions, and provenance kept visibly separate.
- **Evaluators and adopters** who need reproducible tests, completion data, known failure modes, and a non-blocking path to test Regula on their own representative sample.
- **Qualified contextual reviewers** who may use Regula artefacts as inputs. Regula does not make their legal, conformity, security, accessibility, or domain determination.

The detailed tasks, failure paths, and required interface states are defined in
[product coverage and user journeys](docs/PRODUCT_COVERAGE_AND_JOURNEYS.md).

## What Regula is (and isn't)

**Regula is:**

- A development-time evidence and triage tool that combines static code
  analysis with governance questionnaires, mapping observations and declared
  facts to possible obligations across 3 jurisdictions (EU AI Act, South
  Korea AI Basic Act, Colorado SB 26-189)
- A shift-left code-indicator scanner -- like ESLint for governance review, running in your terminal or CI/CD pipeline
- A questionnaire-based assessment tool for organisational obligations that code patterns cannot verify (Articles 9, 17, 27, 72)
- Pattern-based risk indication across 3 jurisdictions, not a legal compliance certificate
- A starting point for compliance awareness, not a finish line

**Regula is not:**

- A runtime monitoring system (it analyses source code, not running systems)
- A legal compliance certificate (findings are indicators, not legal determinations)
- A replacement for enterprise GRC platforms like Credo AI or Holistic AI (it complements them)
- A production fairness testing platform (`regula bias` runs benchmark probes against a local model as a starting point, but does not replace runtime fairness monitoring)
- Legal advice (consult qualified legal counsel for compliance decisions)

Regula helps development teams find AI-governance questions earlier across its
implemented jurisdictions and reference frameworks. It does not replace the
organisational, procedural, domain, and legal work required for compliance. For
a detailed account of what falls outside Regula's scope, see
[`docs/what-regula-does-not-do.md`](docs/what-regula-does-not-do.md), and for
Regula's own model card (intended use, training data, evaluation, known failure
modes) see [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md).

## Bias evaluation: methodology and ethics

`regula bias` runs two social-bias benchmarks against a locally-hosted
language model (Ollama, `llama3.2`/`mistral`/`qwen` variants supported)
as evidence for EU AI Act Article 10 data-governance documentation.

| Benchmark | Paper | Method | What it measures |
|---|---|---|---|
| CrowS-Pairs | Nangia et al., 2020 | Log-probability difference between stereotypical and anti-stereotypical sentence pairs | Intrinsic bias in masked/causal LM output |
| BBQ | Parrish et al., 2022 | Question-answering on ambiguous-context prompts | Bias surfacing in downstream QA behaviour |

Both include Wilson confidence intervals for small-sample reliability and
bootstrap CIs for distribution estimates. Full methodology lives in
[`scripts/bias_eval.py`](scripts/bias_eval.py) and
[`docs/benchmarks/PRECISION_RECALL_2026_04.md`](docs/benchmarks/PRECISION_RECALL_2026_04.md).

**Ethics statement.** CrowS-Pairs and BBQ stereotype pairs are used
**solely for scientific evaluation** of model behaviour under controlled
conditions. Regula does **not display individual stereotype pairs** in
terminal output or reports :  only aggregated scores, confidence
intervals, and benchmark-level verdicts. The pairs are distributed under
the dataset's own licence (CC BY-SA 4.0 for CrowS-Pairs) and are not
redistributed or modified by Regula. Opinions encoded in the stereotype
pairs do not reflect the views of the maintainer, Regula contributors,
or any user running the tool; their presence is instrumental, not
endorsing. `regula bias` is a development-time starting point for bias
documentation, not a production fairness monitor :  see "What Regula is
(and isn't)" above.

## Important limitations

Regula performs **pattern-based risk indication**, not legal risk classification.

- The EU AI Act classifies risk based on intended purpose and deployment context (Article 6), not code patterns. Regula's findings are indicators that warrant human review.
- **False positives will occur.** Regula has no current, independently
  labelled real-world precision estimate. Its development corpora are
  single-reviewer records, and the older random-corpus result cannot be
  re-derived from a clean checkout because its measured subset and pinned
  source snapshots were not preserved. The arithmetic, limitations, and
  superseded measurement remain available as a dated research record in
  [`benchmarks/README.md`](benchmarks/README.md); they are not evidence of the
  current detector's accuracy.
- **TypeScript findings are advisory:** current real-world precision is
  unmeasured. A dated six-finding development slice contained six false
  positives, which is a warning signal rather than a dependable rate.
- **False negatives will occur.** Novel risk patterns not in the database will be missed.
- Article 5 prohibitions have conditions and exceptions that require human judgment.
- The audit trail is self-attesting (locally verifiable, not externally witnessed).
- This is not a substitute for legal advice or DPO review.

## Verified numbers

| What | Count |
|------|------:|
| CLI commands | 62 |
| Risk detection patterns (regexes) | 423 |
| Language families scanned | 8 (Python, JS, TS, Java, Go, Rust, C/C++, Jupyter) |
| Framework identifiers with selected references | 13 |
| Tests (pytest --collect-only) | 2,936 |
| Required production dependencies | 0 |

For reproduction commands, version-bounded benchmarks, known exceptions, security posture, and audit-trail design, see [`docs/TRUST.md`](docs/TRUST.md). What version numbers promise, the public API they cover, and the deprecation policy: [`docs/VERSIONING.md`](docs/VERSIONING.md).

## Privacy and data handling

Regula's core scan runs on your machine. No code, findings, or metadata are transmitted during a default scan. There is no account system or API key, and no telemetry by default (crash reporting requires both `regula telemetry enable` **and** an endpoint you configure yourself via `REGULA_SENTRY_DSN`; published builds ship none, and `DO_NOT_TRACK` suppresses it regardless). The tool reads your source files, analyses them locally, and writes output to your local filesystem. Explicit network-enabled operations include RFC 3161 timestamping, feed or update checks, and integrations you configure. See [`SECURITY.md`](SECURITY.md) for the full security posture.

## Contributing

Bug reports and pull requests are welcome.

- Run `pytest tests/ -q` before opening a PR.
- Pattern additions go in `scripts/risk_patterns.py`. Each pattern should have a corresponding test.
- Regula is intentionally risk *indication*, not legal classification. New patterns should be conservative -- false positives erode trust more than false negatives for a developer tool.
- See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full contributor guide and [`CHANGELOG.md`](CHANGELOG.md) for version history.

### Authorship

Regula currently has a single maintainer. Where commits identify a co-author, that attribution records the tools or collaborators involved. The maintainer remains accountable for reviewing and accepting every merged change. See [GOVERNANCE.md](GOVERNANCE.md) for the bus-factor limitation.

## Licence

**Engine and CLI:** [Apache License 2.0](LICENSE.txt) **OR** [European Union Public Licence v. 1.2](LICENSE.EUPL) :  at your option. Pick the one that fits your context:

- **Apache 2.0** includes an explicit patent grant, making it the preferred choice for enterprise adoption, commercial redistribution, and any context where patent clarity matters.
- **EUPL-1.2** is explicitly recognised inside EU institutions and public-sector procurement, is strongly-copyleft on software, and has a formal compatibility appendix (GPL v2/v3, AGPL v3, OSL, EPL, CeCILL, MPL 2.0, LGPL, CC BY-SA 3.0) for downstream projects. If you work with a European public administration, EUPL is often the required or preferred licence.

You may choose either licence for any use. You do not need to state which one you picked, but attribution (keep the copyright notice and NOTICE file) is required under both.

**Risk patterns and regulatory data:** [Detection Rule License (DRL) 1.1](docs/LICENSE.Detection.Rules.md). You may use, modify, and redistribute the patterns freely. Attribution is required if you redistribute the patterns or use them in a product. If your tool generates match output from these patterns, the output must credit the source.

The SPDX expression for the full package is `(Apache-2.0 OR EUPL-1.2) AND LicenseRef-DRL-1.1`.
