# ADR-0002: Four-track decision matrix before choosing the production direction

- **Status:** accepted
- **Date:** 2026-07-02
- **Deciders:** Máté (operator), Codex bootstrap synthesis
- **Tags:** roadmap, modeling, gpu, settlement, transport, l1-l2

## Context and problem statement

The uploaded source documents contain a real conflict:

- Older `GPU_Compute_Network.md` pushes a Sui-first, 3D rendering, libp2p-style
  direction.
- Newer `hybrid_decentralized_compute_network.md` and the HDCN blueprint pack
  correct that into multi-network by design, Base-first only as an
  implementation sequence, iroh transport, and FlowMate/backtest as the first
  useful workload.
- The operator also wants own L1, token, multi-chain bridge, trustless GPU
  inference, GPU+CPU nodes, a stable micro-node system, and a fast network
  protocol to remain in scope.

The risk is prematurely deleting a promising route or mixing all routes into one
unreviewable architecture. The decision must be model-driven.

## Decision

Keep four tracks active until each has a measurable prototype and explicit
go/no-go criteria:

| Track | Direction | First testable artifact | Decision gate |
|---|---|---|---|
| A | Multi-network compute-first mesh: iroh, deterministic receipts, FlowMate/backtest workload, Base-first EVM adapter | WASM/receipt mini-prototype + simulator baseline | Deterministic output commitments match across machines; simulator base/stress/security runs are healthy |
| B | Legacy Sui-first + 3D rendering + libp2p direction | Render-tile hash prototype and Sui adapter spike | Beats Track A on verification simplicity, latency, or developer speed without chain lock-in |
| C | Own L1/token + multi-chain bridge + hybrid L1/L2 | Token/economic model and L1/L2 threat model, no mainnet code | Legal and security review clears it; bridge risk is justified by measured network volume |
| D | GPU+CPU micro-node and trustless GPU inference | GPU worker process benchmark + redundant verification/challenge model | Cheating worker detection is reliable and economics beat CPU-only workloads |

Track A remains the implementation default for Sprint 00 and Sprint 01 because it
is the fastest path to a safe, deterministic, testable network. Tracks B-D are
not rejected; they are research and prototype lanes with their own gates.

## Consequences

- New production code must not hardcode one chain or one workload as the only
  future.
- GPU, token, bridge, and own-L1 work must enter through ADRs and prototypes
  before production code.
- Base-first does not mean Base-only. It means the first concrete EVM adapter can
  be reused for Base, Ethereum, BNB, and Avalanche C-Chain.
- Sui/render/libp2p material is preserved under `docs/research/` and can win a
  later decision if prototype data supports it.

## Open questions / research left

- Can render-tile verification be cheaper and more compelling than deterministic
  FlowMate/backtest execution for the first real users?
- Which parts of GPU inference can be made reproducible enough for trustless
  payout, and which require probabilistic/redundant verification?
- At what volume does a token, own L1, or bridge become worth the regulatory and
  security burden?
- Is iroh materially better than libp2p for home-node NAT traversal in this
  project's actual geography and workload mix?

## Links

- `docs/modeling/DIRECTION_MODELING_PLAN.md`
- `docs/sprints/SPRINT_00_BOOTSTRAP.md`
- `docs/research/gpu_compute_network_sui_render_libp2p.md`
- `docs/research/hybrid_decentralized_compute_network.md`
