# AGENTS.md — crate `settle-core`

Scoped rules for the settlement abstraction. These **add to** the root
`AGENTS.md`; on conflict, the stricter rule wins. This is the crate closest to
money — treat every change as security-sensitive.

## Purpose

`settle-core` defines the chain-agnostic `SettlementAdapter` trait and the
netting/clearing logic. Concrete adapters (`settle-evm`, `settle-solana`,
`settle-sui`, `settle-polkadot`, `settle-xrpl`) implement the trait. **All
chains are equal endpoints**; nothing here may hardcode a preferred chain.
Base is merely the first adapter implemented downstream.

## Hard constraints

- **Multi-network invariants.** The trait and netting logic must remain
  chain-neutral. No `if chain == Base` special-casing in core; chain-specific
  behavior lives in the adapter crate. A new assumption that only holds for one
  chain is a **P0** review finding.
- **Non-custodial by construction.** The protocol must never require holding a
  user's funds outside an on-chain escrow whose release condition is explicit
  (hashlock / timelock / committee). Do not introduce a code path that takes
  custody. Any such path is **P0** and requires a human + likely legal review.
- **Release conditions are explicit and testable.** `escrow_release` must be
  reachable **only** when its condition is satisfied; `escrow_refund` only after
  `cancel_after`. Add tests proving funds cannot be released otherwise.
- **No secrets, ever.** No RPC keys, deployer keys, or mainnet addresses in code,
  fixtures, or logs. Endpoints/addresses come from config/secrets at runtime.
  Testnet only in code; mainnet values are injected by the human operator.
- **Amounts are integer base units.** USDC = 6 dp. No floats for money. Guard
  against overflow explicitly.
- **Idempotency + replay safety.** A settlement action must be safe to retry and
  must not be replayable to double-release. Document the anti-replay mechanism.

## Regulatory note for agents (not legal advice)

USDC settlement and any cross-chain movement carry EU (MiCA) exposure. The
default posture is **fee-only, no protocol token, non-custodial**. Do not add a
token, a custody step, or an exchange-like feature in this crate. If a task
seems to require one, **stop and open an issue for the human** — this is a legal
decision, not an engineering one.

## Review focus for `@codex review` here

- Any custody of user funds introduced? → **P0**.
- Any chain-specific special-casing leaking into core? → **P0**.
- Can `escrow_release` fire without its condition, or be replayed? → **P0**.
- Floats used for money, or unchecked arithmetic on amounts? → **P0**.
- Missing tests proving the negative (funds NOT releasable)? → **P1**.
