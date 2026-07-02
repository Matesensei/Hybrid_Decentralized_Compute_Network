# Hybrid Decentralized Compute Network

HDCN is a chain-agnostic decentralized compute network scaffold. The first
implementation path is deterministic compute receipts, simulator-backed decision
gates, and a multi-network settlement adapter surface. The project deliberately
keeps the GPU, Sui/render, own L1/token, and hybrid micro-node directions alive
until they are modeled and tested.

## Current Status

This repository is at Sprint 00 bootstrap:

- Rust workspace with `proto` and `settle-core` crates.
- Deterministic postcard/BLAKE3 receipt envelope prototype.
- Chain-neutral settlement adapter types with integer-only money.
- Python DePIN network simulator and precomputed baseline outputs.
- CI plus optional Claude/Codex review workflows.
- ADRs and sprint docs for four-track decision-making.

No mainnet contracts, tokens, production workers, or private keys exist in this
repo.

## Quickstart

```bash
cargo fmt --check
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features

python -m py_compile sim/depin_network_model.py
python sim/depin_network_model.py --scenario base --runs 3 --days 30 --out out/base-smoke
```

For full simulator runs:

```bash
python -m venv .venv
.venv/bin/pip install -r sim/requirements.txt
scripts/run_simulations.sh
```

## Canonical Planning Docs

- `docs/sprints/SPRINT_00_BOOTSTRAP.md` - first sprint execution plan.
- `docs/ai/REPO_MAP.md` - mandatory AI orientation map, cross-review rule, and
  anti-duplication checklist.
- `docs/modeling/DIRECTION_MODELING_PLAN.md` - model/test gates before choosing
  a direction.
- `docs/adr/0001-multi-network-settlement.md` - multi-network settlement with
  Base implemented first.
- `docs/adr/0002-four-track-decision-matrix.md` - preserves the four major
  technical directions until data decides.
- `PROJECT_HANDBOOK_EN.md` / `PROJEKT_KEZIKONYV_HU.md` - human-facing handbook.

## Agent Workflow

The human operator is the merge gate. Claude and Codex may open or review PRs,
but no workflow auto-merges. The Codex/Claude GitHub workflows are intentionally
secret-gated and no-op when the required API keys are not configured.
Substantive PRs require another AI's review before merge, or an explicit human
override if the second AI is unavailable.
