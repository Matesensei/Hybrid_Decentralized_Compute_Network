# ADR-0002: Four-track decision matrix before choosing the production direction

- **Status:** accepted
- **Date:** 2026-07-02
- **Deciders:** Máté (operator), Codex bootstrap synthesis
- **Tags:** roadmap, modeling, gpu, settlement, transport, l1-l2

## Context and problem statement

The uploaded source documents contain a real conflict:

- Older `docs/research/gpu_compute_network_sui_render_libp2p.md` pushes a Sui-first,
  3D rendering, libp2p-style direction. The operator clarified that this must be
  generalized: Sui is only
  one target; the lane must remain multi-network across ETH, SUI, SOL, BNB,
  Base, Polkadot, and later adapters.
- Newer `hybrid_decentralized_compute_network.md` and the HDCN blueprint pack
  correct that into multi-network by design, Base-first only as an
  implementation sequence, iroh transport, and FlowMate/backtest as the first
  useful workload.
- The operator also wants own L1, token, multi-chain bridge, token/coin price
  conversion, swap/routing, trustless validation, GPU-only nodes, GPU+CPU nodes,
  a stable micro-node system, and a fast network protocol to remain in scope.

The risk is prematurely deleting a promising route or mixing all routes into one
unreviewable architecture. The decision must be model-driven.

## Decision

Keep four tracks active until each has a measurable prototype and explicit
go/no-go criteria:

| Track | Direction | First testable artifact | Decision gate |
|---|---|---|---|
| A | Multi-network compute-first mesh: iroh, deterministic receipts, FlowMate/backtest workload, Base-first EVM adapter | WASM/receipt mini-prototype + simulator baseline | Deterministic output commitments match across machines; simulator base/stress/security runs are healthy |
| B | Multi-network render/token-routing spike: render proof, libp2p-vs-iroh comparison, settlement/swap validation across ETH/SUI/SOL/BNB/Base/Polkadot/etc. through the HDCN token model | Render-tile hash prototype + multi-network adapter matrix + price/swap validation model | Beats Track A on verification simplicity, latency, routing coverage, or developer speed without chain lock-in |
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
- Sui/render/libp2p material is preserved under `docs/research/`, but it is not
  Sui-only. The production question is whether the render/token-routing route can
  work across every supported network while micro-nodes validate compute and
  settlement events.

## Open questions / research left

- Can render-tile verification be cheaper and more compelling than deterministic
  FlowMate/backtest execution for the first real users across multiple networks?
- Can HDCN's own token be modeled as the internal accounting/routing asset while
  safely converting ETH, SUI, SOL, BNB, Base assets, Polkadot assets, and later
  chains without custody or hidden bridge risk?
- Which parts of GPU inference can be made reproducible enough for trustless
  payout, and which require probabilistic/redundant verification?
- At what volume does a token, own L1, or bridge become worth the regulatory and
  security burden?
- Is iroh materially better than libp2p for home-node NAT traversal in this
  project's actual geography and workload mix?

## Links

- `docs/modeling/DIRECTION_MODELING_PLAN.md`
- `docs/sprints/SPRINT_00_BOOTSTRAP.md`
- `docs/research/gpu_compute_network_sui_render_libp2p.md` (Track B, superseded in part)
- `docs/research/hybrid_decentralized_compute_network.md` (Track A canonical architecture)
- `docs/research/protocol_compute_currency.md` (Track C tokenomics)
- `docs/research/cross_chain_p2p_feasibility_EN.md` (Track C swap/bridge feasibility)
- `docs/research/seven_problems_solutions.md` (seven-hard-problems risk/solution register + P0-P5 phase mapping; its open-research list expands the open questions above)
