# Console handoff: 2026-07-16 audit and product-strategy research

**Status:** machine-facing orientation for dated research inputs

**Authority:** navigation and conflict-resolution aid only; not an ADR
**Snapshot:** HDCN `fb945f62a6cf7fe55915e88e5b87a43ff271811c`; FlowMate
`6d703cdc66e4aff55c9a8b096f5e090515ad7bce`

## Purpose

This file gives Codex CLI, Claude Code, GLM, and other console agents a short,
safe entry point to the two detailed Hungarian reports added on 2026-07-16:

- `docs/research/HDCN_FULL_AUDIT_HU_2026_07_16.md`
- `docs/research/HDCN_INNOVATION_PRODUCT_STRATEGY_HU_2026_07_16.md`

The reports are decision-support research. They do not change the accepted
architecture, the current sprint, the security boundary, or the four-track ADR.
Reframing HDCN from the accepted compute-first Track-A mission into a generic
decision network, or making CarryLens the repository's primary implementation
mission, requires a new architecture/product ADR (provisionally ADR-0003) and
explicit operator approval.

## Mandatory read order

Before acting on either report, read:

1. `AGENTS.md`
2. the nearest nested `AGENTS.md`, if one exists
3. `docs/ai/REPO_MAP.md`
4. `SECURITY.md`
5. `docs/sprints/SPRINT_00_BOOTSTRAP.md`
6. `docs/adr/0001-multi-network-settlement.md`
7. `docs/adr/0002-four-track-decision-matrix.md`
8. `docs/modeling/DIRECTION_MODELING_PLAN.md`
9. the relevant GitHub issue or PR
10. the two dated reports above

If a dated report conflicts with an accepted ADR, root `AGENTS.md`, `SECURITY.md`,
or the current sprint, the accepted repository owner wins. Propose an ADR or
sprint update; do not silently implement the report.

## Current evidence-backed verdict

The audit found a well-documented Sprint-00 scaffold, not a production network.
The current Rust implementation is limited to the `proto` and `settle-core`
crates plus the Python simulator. There is no production node, executor,
verifier network, chain adapter, contract, token, bridge, or FlowMate adapter.

The dated strategy ranks these bounded product hypotheses highest:

1. read-only funding/carry intelligence using FlowMate research components;
2. workload-specific signed compute quotes and verified usage/output receipts;
3. rights-aware, first-seen market-evidence provenance;
4. risk-adjusted rebalancing proposals over existing intent/solver systems;
5. GitHub/milestone evidence for project-funding decisions.

The shared primitive is a versioned, domain-separated decision/compute receipt
that binds source/input manifests, code/runtime versions, cost components,
uncertainty, verification policy, signatures, expiry, and outcome rules.

These are hypotheses, not accepted product names or protocol types. `CarryLens`,
`ProofQuote`, `ComputeQuote`, `EvidenceGraph`, `Rebalance Guard`, and `BuildProof`
are working names only and require naming/trademark checks before public use.

## Repository-normalized interpretation

| Research statement | Repository-safe interpretation |
|---|---|
| Start with a funding/carry commercial wedge | Does not replace Sprint 01. Deterministic WASM/receipt work remains the canonical next implementation unless the operator updates the sprint. Carry research can be a parallel design issue/PR. |
| Add `DecisionReceiptV1` / `CarryQuoteV1` | Treat as schema proposals. Search `crates/proto/` first, avoid duplicate envelopes, and require proto/security cross-review before code. |
| Use SQLite/WAL for a light MVP | Conflicts with root stack choice. Use `redb` or `sled` unless an ADR explicitly changes local state. |
| Base + USDC first | Base is implementation sequence only. Preserve chain-neutral core and equal settlement endpoints under ADR-0001/0002. |
| No native token, L1, or bridge now | This is a sequencing recommendation, not deletion of Tracks B-D. Preserve all four tracks and enforce their modeling gates. |
| Add CPU/GPU conversion | Use workload-specific stable-denominated quotes. Do not define compute value from a native-token price or claim one universal GPU/CPU unit. |
| Add rebalancing | Start read-only and adapter-first. Do not build a new bridge/solver network, take custody, move treasury funds, or add unlimited approvals. |
| Add news/market evidence | Provenance is not truth. Require `published_at`, `first_seen_at`, source-family deduplication, rights metadata, and leakage-safe outcome tests. |
| Connect FlowMate | Offline research/backtest only first. No exchange keys, wallet secrets, live order placement, strategy IP, or private data on untrusted workers. |
| Use Python adapters initially | Python is allowed for research, simulation, and bounded ingest prototypes. Production protocol/settlement adapters remain Rust-core work unless an ADR changes the stack. |
| Use an on-chain anchor | Keep the hot path off-chain. Any Base testnet batch anchor needs a bounded design, adapter review, and no mainnet or treasury action. |
| Use budgets/revenue projections | Treat all figures as dated scenarios, not forecasts, quotes, or profit promises. Revalidate vendor, legal, and market assumptions. |

## Security and product hard stops

Do not:

- deploy a mainnet contract or issue a token;
- implement a bridge or own L1 from these reports;
- store, request, print, or transmit keys, mnemonics, exchange credentials, or
  production RPC secrets;
- give a worker custody or authority to place live trades;
- equate a capacity/metering receipt with output correctness;
- use floating point for money, deterministic verification, or hash commitments;
- hardcode the previous ERC-7683 draft;
- claim C2PA, a signature, identity, source count, stake, or quorum proves truth;
- ingest or redistribute a feed without a rights record;
- convert a research ranking into personalized investment advice without legal
  perimeter review;
- merge this or follow-up substantive work without the required independent AI
  review and human merge gate.

## Important external-repository finding

The audit identified a likely unit mismatch in FlowMate
`crypto_bot/arbitrage/funding_arb.py`: `spot_perp_spread_pct` is stored as a
decimal ratio while `round_trip_fee_pct` is a percentage, and the break-even/net
APR paths combine them directly. It also hardcodes three funding intervals per
day.

This HDCN documentation PR must not modify the FlowMate repository. Validate the
finding in a dedicated FlowMate issue/branch with regression tests, typed units,
venue-specific funding intervals, and historical-distribution output before any
product or execution claim.

## Safe next-task menu

An agent may propose one bounded follow-up at a time:

1. **Sprint 01 executor:** implement the already-planned deterministic WASM guest,
   metering, output commitment, and tamper-rejection tests.
2. **Proto-v2 design issue:** specify domain separation, bounded decoding,
   signature verification, replay protection, worker receipt vs acceptance
   certificate, and golden vectors before implementation.
3. **FlowMate adapter design:** define immutable manifests and research-only
   result exchange without importing credentials or live execution.
4. **Carry quote design:** document typed bps/base-unit inputs, historical
   funding distributions, basis/fee/borrow/liquidation components, and
   P10/P50/P90 outputs. Keep it design-only in HDCN until product priority is
   accepted.
5. **Compute quote modeling:** define versioned workload profiles and explicitly
   separate capacity proof, usage metering, and correctness verification.
6. **Market evidence modeling:** define rights records, `first_seen_at`, source
   independence, claims/challenges, and leakage-safe FlowMate outcome labels.
7. **Economic simulations:** update the canonical modeling plan and simulator
   before any take rate, verifier payout, token, GPU, L1, bridge, or treasury
   decision.

Any task that changes a stack row or accepted architecture needs an ADR and
explicit human approval.

The reports' present-tense NO-GO language for token, L1, bridge, render, and GPU
means **no production implementation now**. It does not delete Tracks B, C, or D;
ADR-0002 keeps those research lanes alive until their measured prototype gates
produce an explicit decision.

## Validation gates for follow-up work

- deterministic byte-identical replay for deterministic jobs;
- strict typed units and property/regression tests for money/rates;
- expiry, freshness, source, and uncertainty on every quote;
- bounded input/output sizes and default-deny sandboxing;
- explicit verification class and payout cap;
- rights metadata for every market-evidence source;
- no look-ahead leakage (`published_at` and `first_seen_at` stay distinct);
- simulator evidence and positive contribution margin before economic expansion;
- another AI's substantive review before merge.

## Cross-review state

This upload is a Codex-authored substantive documentation/navigation change.
It requires an independent Claude/other-AI review before merge under
`AGENTS.md` §3. The human operator retains the merge gate. The PR must remain
draft until that review and any requested corrections are complete.

## Scope of this upload

Documentation only:

- two dated research reports;
- this console-agent entry point;
- README and repo-map navigation.

No Rust/Python behavior, dependency, workflow, secret, permission, contract,
chain state, token, treasury, or live-trading path is changed.
