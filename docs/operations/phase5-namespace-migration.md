# Plan: Phase 5 — catalog split and long-tail namespace migration (SUPERSEDED)

> **Superseded and deleted (ADR-003, 2026-08-29).** This plan proposed relocating the peripheral
> pipelines into repo-owned namespaces. ADR-003 found them out of scope — they model the OSO
> organization, not the Gap Map's data system — so instead of relocating them they were
> **externalized**: frozen under platform ownership (`frozen-without-producer`, recorded in
> `../../warehouse/audits/externalization.json`) and removed from this repo's inventory and
> publisher. No namespace move was executed. The authoritative record is
> `../architecture/adr-003-repository-scope-boundary.md`; nothing here is executable.
