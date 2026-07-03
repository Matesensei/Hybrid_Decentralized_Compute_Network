# HDCN direction modeling plan

This document is the canonical owner for pre-decision modeling across the four
major project directions. No production commitment to a token, own L1, bridge,
GPU inference payout, or single transport stack should happen until the relevant
gate below has data.

## Shared baseline

Every direction is compared against the same baseline:

- Simulator scenarios: `bear`, `base`, `bull`, `stress`, `security`.
- Minimum Monte Carlo run: 100 runs, 365 days for a candidate decision.
- Smoke run for CI: 3 runs, 30 days.
- Core KPIs: fill rate, reserve ratio, active nodes, margin per GPU-hour,
  gossip latency, undetected bad work share, corrupt committee probability.
- Security KPIs: replay resistance, signature coverage, deterministic receipt
  bytes, no custody, no private keys, no mainnet deployment.

## Track A: deterministic compute mesh

Scope:

- iroh transport and BLAKE3 content addressing.
- Deterministic WASM/WASI execution.
- FlowMate/backtest as the first useful dogfooding workload.
- Base-first EVM settlement adapter after receipt verification works.

Sprint 00 gate:

- `proto` has stable postcard receipt bytes and receipt IDs that exclude the
  signature.
- `settle-core` exposes chain-neutral escrow types with integer-only money.
- CI runs Rust tests and simulator smoke.

Sprint 01 gate:

- One deterministic WASM task produces the same `output_commit` across at least
  two machines or runners.
- A local verifier rejects tampered input/output commitments.

## Track B: multi-network render, token routing, and libp2p comparison

Scope:

- Preserve the older render/libp2p thesis as a competing prototype, not as the
  production default.
- Generalize the lane beyond Sui. ETH, SUI, SOL, BNB, Base, Polkadot, and future
  adapters are all target networks.
- Model HDCN's own token as the internal routing/accounting asset for payments,
  swaps, and validation, while external coins/tokens are priced and converted
  through explicit adapter/oracle/swap assumptions.
- Include both GPU-only and GPU+CPU home micro-nodes as validators/workers for
  compute receipts and settlement events.

Decision data needed:

- Render tile hash prototype.
- Multi-network adapter matrix for ETH, SUI, SOL, BNB, Base, Polkadot, and later
  chains.
- Token/coin price conversion model: oracle source, stale-price handling,
  slippage, fees, and failure modes.
- Swap/routing model: when HDCN token is used internally, when external assets
  are converted, and what remains non-custodial.
- Sui testnet escrow spike as one adapter example, not the whole lane.
- libp2p NAT traversal comparison against iroh on the same home-node topology.

Go condition:

- It gives a simpler first customer workload, materially better transport
  results, or a stronger multi-network token-routing model without turning HDCN
  into a single-chain or custodial project.

## Track C: own L1, token, bridge, hybrid L1/L2

Scope:

- Economic and security modeling only until legal/security gates clear.
- Token and own-L1 work is not part of Sprint 00 implementation.

Decision data needed:

- Token utility model that does not require custody or exchange-like operation.
- Bridge threat model and loss budget.
- L1/L2 state model: what must be consensus-critical versus what can remain in
  off-chain receipts and checkpoints.

Go condition:

- Real network volume and legal review justify the extra security and regulatory
  load. Before that, fee-only USDC settlement stays the safer path.

## Track D: GPU+CPU micro-node and trustless GPU inference

Scope:

- Hybrid node design, GPU worker process isolation, benchmark reporting,
  redundant verification, and challenge games.
- GPU worker stays outside the core daemon until verified.

Decision data needed:

- GPU benchmark and thermal/power stability on real home hardware.
- Cheating/lazy worker detection rate under redundant execution.
- Capability split for GPU-only nodes versus GPU+CPU nodes.
- Economics versus CPU deterministic workloads after electricity and capex.

Go condition:

- The verification model detects cheating reliably enough for payout and the
  simulator shows sustainable node margins in stress/security scenarios.

## First sprint modeling commands

```bash
cargo test --workspace --all-features
python sim/depin_network_model.py --scenario base --runs 3 --days 30 --out out/base-smoke
python sim/depin_network_model.py --scenario stress --runs 10 --days 90 --out out/stress-mini
python sim/depin_network_model.py --scenario security --runs 10 --days 90 --out out/security-mini
```

Full decision runs use `scripts/run_simulations.sh` after installing
`sim/requirements.txt`.
