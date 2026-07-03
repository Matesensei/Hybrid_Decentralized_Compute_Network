# Sprint 00: repository bootstrap and first deterministic receipt prototype

**Status:** in progress  
**Owner:** Codex bootstrap branch `feature/bootstrap-hdcn-sprint0`  
**Date:** 2026-07-02  
**Canonical inputs:** `Hybrid_Decentralized_Compute_Network.zip`, `files.zip`,
`depin_blueprint_pack.zip`, and local folder
`/home/matesensei/Asztal/hybrid_decentralized_compute_network`

## Goal

Turn the uploaded blueprint pack into a real, testable repository without making
a premature architecture decision. Sprint 00 should leave the repo ready for
Claude/Codex review, simulator runs, and Sprint 01 deterministic WASM execution.

## Scope

- Bootstrap Rust workspace and CI.
- Add `proto` receipt types with deterministic postcard encoding and BLAKE3 IDs.
- Add `settle-core` chain-neutral settlement types and validation.
- Add simulator dependency file and dispatch workflow.
- Preserve research inputs under `docs/research/`.
- Document the four-track decision matrix.
- Add a mandatory AI repo map with cross-review, documentation, and
  anti-duplication rules.
- Open a PR for review; no unattended auto-merge (an agent merges only on an
  explicit per-PR operator instruction — `SECURITY.md` §1).

## Acceptance criteria

- `cargo fmt --check` passes.
- `cargo clippy --workspace --all-targets --all-features -- -D warnings` passes.
- `cargo test --workspace --all-features` passes.
- `python -m py_compile sim/depin_network_model.py` passes.
- A local or CI simulator smoke run writes `summary.csv` and `scenario.json`.
- Codex review workflow is read-only and no-ops if `OPENAI_API_KEY` is absent.
- Claude workflow no-ops if `ANTHROPIC_API_KEY` is absent.
- `docs/adr/0002-four-track-decision-matrix.md` records the four preserved
  directions and their gates.
- Track B is recorded as multi-network render/token-routing research, not a
  Sui-only direction.
- `docs/ai/REPO_MAP.md` exists and is referenced from `AGENTS.md` as mandatory
  agent orientation.

## Local modeling snapshot

Local smoke runs on 2026-07-02 used `/tmp/hdcn-sim-venv` and wrote outputs under
`/tmp/hdcn-sim-*`:

| Scenario | Runs / days | Spiral flags | Median avg fill | Median min reserve | Note |
|---|---:|---:|---:|---:|---|
| base | 3 / 30 | 0 / 3 | 99.1% | 1.6712 | Healthy smoke baseline |
| stress | 10 / 90 | 10 / 10 | 79.2% | -1.1219 | Fails stress gate; treasury/cashout economics need tuning |
| security | 10 / 90 | 0 / 10 | 99.8% | 1.6861 | Security scenario remains economically stable in mini run |

This is not a production forecast. It is enough to prove the simulator runs and
to block premature token/L1/bridge decisions until full 100+ run decision models
are recorded.

## Agent lanes

| Lane | Agent | Work |
|---|---|---|
| Bootstrap implementation | Codex | Repo scaffold, tests, CI, sprint docs |
| Critical review | Claude | Review `proto`, `settle-core`, CI secrets/permissions |
| Adversarial review | Codex review workflow | P0/P1 findings only, read-only sandbox |
| Control-plane | Hermes/Telegram later | Dispatch simulator runs and summarize results only |
| Merge gate | Human owns it | Branch protection, secrets; §2 changes merged in person, other PRs by an agent only on explicit per-PR instruction (`SECURITY.md` §1) |

## Sprint 01 backlog

1. Add `executor-wasm` crate with Wasmtime fuel-metered deterministic execution.
2. Add a tiny deterministic WASM guest fixture.
3. Produce `input_commit`, `output_commit`, `ComputeReceipt`, and local verifier
   rejection tests for tampered commitments.
4. Add a FlowMate/backtest task adapter design doc before importing any FlowMate
   code.
5. Run mini simulations for `base`, `stress`, and `security` and record the
   result summary in `docs/sprints/`.
6. Track the seven-problems risk register
   (`docs/research/seven_problems_solutions.md`): Sprint 01 delivers problems #1/#6
   (deterministic WASM proof + committee re-execution, phase P1); problem #4
   (spam/DDoS) is the weakest area and needs an **explicit pre-mainnet design
   workstream** (RLN + relay hardening) — do not defer it silently. Run 100–500
   Monte Carlo runs per scenario before committing new Rust mechanisms.

## Out of scope for Sprint 00

- Mainnet or testnet deployment.
- Token issuance.
- Own L1 implementation.
- Bridge implementation.
- Production swap routing or oracle integration.
- GPU payout logic.
- Production node daemon.

These are intentionally preserved in the modeling plan and ADR-0002.
