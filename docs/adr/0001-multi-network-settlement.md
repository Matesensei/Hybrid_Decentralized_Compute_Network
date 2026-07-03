# ADR-0001: Chain-agnostic settlement with Base implemented first

- **Status:** accepted
- **Date:** 2026-07-02
- **Deciders:** Máté (operator); synthesized from two independent research reports
- **Tags:** settlement, architecture, multi-network

## Context and problem statement

HDCN must let a job creator pay on one chain and a worker get paid on their
preferred chain, across a wide set of networks (Solana, Sui, Base, Ethereum, BNB,
Polkadot, Avalanche, XRPL). We need to decide whether the protocol has a single
"home chain" or treats chains as equal, and which chain to build **first** given
solo-dev time.

## Decision drivers

- **Multi-network is a core property**, not a feature — no chain may be privileged
  in the core protocol. (Operator directive: Sui is not more important than the
  others; this is a multi-network project.)
- Solo-dev time is the scarcest resource; the first adapter should maximize reuse.
- Verification/settlement must stay non-custodial and MiCA-light (fee-only, no
  token initially).
- The "single fast P2P layer above all chains" is not literally feasible: there is
  no shared state across chains and finality differs per chain, so settlement must
  ultimately land on-chain per corridor.

## Considered options

- **Option A** — Single home chain (e.g. Sui or Base), bridge others to it.
- **Option B** — Chain-agnostic `SettlementAdapter` trait; all chains equal;
  implement adapters in a deliberate order.
- **Option C** — Intent/solver (ERC-7683) layer from day one as the settlement
  primitive.

## Decision outcome

Chosen option: **Option B**, with **Base implemented first**.

- All chains are equal endpoints behind one `SettlementAdapter` trait
  (`escrow_create` / `escrow_release` / `escrow_refund` / `claim_payment` /
  `anchor_checkpoint`). Core logic is chain-neutral; specifics live in adapter
  crates.
- **Base is first** purely for sequencing: cheapest/fastest EVM to bootstrap, and
  one Solidity/Foundry codebase (`ComputeEscrow.sol`) covers four EVM chains
  (Base, Ethereum, BNB, Avalanche C). This is not a downgrade of Sui, Solana,
  Polkadot, or XRPL — those follow.
- USDC via CCTP V2 is the default settlement asset where available (native
  burn/mint, non-custodial); RLUSD or a corridor bridge for XRPL, which is not on
  CCTP. Chain support must be re-verified at implementation time.
- ERC-7683 intent/solver (Option C) is **adopted later** as an optimization for
  large one-off cross-corridor payouts, not as the base primitive — it separates
  "what the user wants" from "how a solver fulfills it," which is useful once
  volume justifies solver dependency. Captured as open research below.

### Consequences

- Good: no lock-in; adding a chain is a new crate, not a redesign; solo-dev builds
  one EVM contract for four chains first.
- Bad / cost: a netting/clearing layer is needed so per-job settlement is not paid
  on every corridor; treasury rebalancing via CCTP adds accounting complexity.
- Follow-up: order after Base → Solana → Sui → BNB/Avalanche (same EVM contract) →
  Polkadot → XRPL (last, weakest Rust SDK).

## Pros and cons of the options

### Option A — single home chain + bridges
- Good: simplest settlement code; one finality model.
- Bad: violates the multi-network directive; bridge risk; privileges one chain.

### Option B — chain-agnostic adapter, Base first
- Good: equal chains; maximal reuse; incremental; matches both research reports.
- Bad: netting complexity; more adapters to maintain over time.

### Option C — ERC-7683 intents from day one
- Good: capital-efficient cross-chain UX; strong ecosystem momentum.
- Bad: solver/relayer dependency and fees before there is volume; heavier than a
  bootstrap needs.

## Open questions / research left

- CCTP V2 chain coverage at build time (esp. Sui timing); XRPL corridor asset
  (RLUSD vs bridge) — re-verify before implementing each adapter.
- When does ERC-7683 intent/solver settlement earn its keep vs internal netting?
  Revisit once real corridor volume exists.
- VASP/CASP registration exposure for operating matching + settlement — legal
  question, not engineering; must be resolved before permissionless mainnet.

## Links

- Related: `PROJECT_HANDBOOK_EN.md` Settlement section.
- Related: ADR-0002 (four-track decision matrix).
- Related: uploaded cross-chain feasibility analysis; ERC-7683 funding memo.
