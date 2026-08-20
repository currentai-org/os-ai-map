# ADR-001: The repository owns scoring semantics

**Status:** Accepted 2026-08-20
**Context:** `data-architecture.md` AD-1, AD-8

## Decision

This repository is the only semantic implementation of the Gap Map's scoring rules. It owns
product, organization, category, artifact, alias and lineage identity; category membership
and taxonomy; rubrics, dimensions, bands, routing, abstentions and scoring policy; the
canonical deterministic evaluator; accepted axis assessments; and release construction.

OSO may execute repository-owned logic or materialize its output. It must not carry an
independently maintained interpretation of the same rubric indefinitely.

Scaling research to thousands of products does not change this. Agents and warehouse models
may generate observations and candidate assessments at any volume; acceptance still happens
through a repository change that a person reviews.

## Why

Openness is currently computed twice — once by `build/check_rubric.py` from `sources/`, and
once by `currentai.scores.openness_facts` and `openness_computed` in Trino.
`build/check_parity.py` exists solely to compare them. Two implementations of one rubric
drift, and the only reason this pair has not drifted visibly is that a gate compares them
every week. That gate is a symptom, not a design.

The failure this prevents is specific. A warehouse model that reinterprets a rule is
invisible to repository review: a scoring change can land in Trino without a diff anyone
reads, and the corpus will still validate. Ownership in one place makes every semantic
change a reviewable commit.

## Consequences

Routing is the live example. `sources/signal_routing.yaml` declares which signal is
authoritative for which dimension, routed by artifact kind, with an abstain-rather-than-
substitute rule. Today `registry.adoption_bands` exports thresholds and nothing else — no
route order, artifact applicability, authority, cap, freshness or abstention behaviour. Any
evaluation SQL needing that has to reinterpret the YAML, which is the violation this ADR
forbids.

`currentai.signal_github.product_adoption` already does it: it builds an `already_measured`
set from `signal_pypi` and `signal_huggingface`, then bands GitHub stars only for the
products those channels missed. The route precedence `pypi > huggingface > stars` lives in
that SQL and nowhere else. Retiring the model without first compiling the ordering into
`registry.adoption_routes` loses it silently, and nothing fails.

So AD-1 obliges the compiler, not just the reader: `registry.adoption_routes` and its
companion tables must round-trip every semantic field of the adoption routing declaration,
or be explicitly classified documentation-only.

The warehouse openness chain stays during migration and is retired only after a
repository-owned evaluator publishes equivalent queryable trace tables and dual-running
shows complete agreement over multiple releases. `check_parity` is removed when there is no
second implementation left to compare, not before.
