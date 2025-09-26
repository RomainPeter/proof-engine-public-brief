# Proof Engine — Public Brief

[![CI](https://img.shields.io/github/actions/workflow/status/OWNER/REPO/ci.yml?branch=main)](https://github.com/OWNER/REPO/actions)
![License Code](https://img.shields.io/badge/license-BUSL--1.1-blue)
![License Docs](https://img.shields.io/badge/docs-CC%20BY--NC--ND%204.0-orange)

Independent research brief on an auditable AI architecture: Orchestrator (deterministic), Semantic Engine (LLM as stochastic oracle — stubbed here), and Formal Verifier (deterministic). This repo provides:
- A minimal PCAP (Proof-Carrying Action) format
- JSON Schemas (X, PCAP)
- A tiny demo of code compliance verification (unit tests, type checks, lints)
- A mermaid diagram of the Plan–Execute–Replan double loop

No affiliation or endorsement by any third party.

## Why
Classical prompt work is opaque and hard to audit. We separate concerns and carry proofs with each action. Outputs include a trace and a verifier attestation.

## Two-command demo
```bash
make setup
make demo.pass   # or: make demo.fail
```

Outputs:
- PCAP: `out/pcap.add.json`
- Verifier attestation: `out/attestations/attestation.json`
- Workspace used for hermetic checks: `out/workspace/`

## Architecture (neutral)
- Orchestrator: owns state X, builds PCAPs, and selects operators.
- Semantic Engine (stub): would generate candidates via micro-prompts (not included here).
- Formal Verifier: validates PCAP obligations deterministically.

```mermaid
flowchart LR
  G[Goal + Constraints] --> P[Plan]
  P -->|operator| O[Orchestrator]
  O -->|micro-prompt| L[Semantic Engine LLM stub]
  L -->|candidate| O2[Orchestrator]
  O2 -->|CCA/PCAP| V[Formal Verifier]
  V -->|accepted/rejected + attestation| O3[Orchestrator]
  O3 -->|update X / replan| P
```

See docs/diagram.mmd for the loop.

## What's included
- Minimal PCAP schema and example
- Verifier that runs: jsonschema validation, ruff, mypy, pytest
- Reproducible run via pinned deps
- Public documentation under CC BY-NC-ND; code under BUSL-1.1

## Limits
- No real LLM; candidate generation is stubbed (files in examples/)
- Signing is a demo HMAC, not production-grade (see SECURITY.md)

## Quick start
- `examples/candidates/add_v1.py`: compliant version
- `examples/candidates/add_buggy.py`: fails tests (overflow logic)
- `examples/proofs/tests/test_add.py`: property tests
- `examples/constraints/obligations.simple.json`: obligations K

## License
- Code: BUSL-1.1 (see LICENSES/CODE_LICENSE.txt)
- Docs: CC BY-NC-ND 4.0 (see LICENSES/DOCS_LICENSE.txt)