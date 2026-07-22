# ADR-0003: Internal work-credit ledger (A1 archetype) — proposed, not yet triggered

- **Status:** proposed (decision deferred to a P2.5 trigger gate; see "Decision outcome")
- **Date:** 2026-07-22
- **Deciders:** Máté (operator); proposed by GLM, pending Codex/Claude cross-review
- **Tags:** tokenomics, settlement, economics, MiCA, architecture

> This ADR is **proposed**, not accepted. It records the design of an *optional*
> internal work-credit ledger (the A1 archetype from
> `docs/research/protocol_compute_currency.md`) so that the decision is ready if
> and when the P2.5 trigger fires. **No credit ledger, contract, or monetary
> state is introduced by accepting this ADR.** Accepting it only adopts the design
> as the canonical reference for *how* a credit would be built, not a commitment
> to build one. The human operator remains the only authority who can trigger the
> implementation.

## Context and problem statement

The protocol's default settlement path is **fee-only USDC** (ADR-0001 + ADR-0002
Track A). That is correct for P0-P2: it minimizes MiCA exposure, avoids a
token-launch burden, and lets a solo developer prove real demand before adding
monetary complexity.

The open question is whether and when to add a **unit-of-account layer** between
"raw USDC payment" and "a tradable protocol token". Two operational problems can
emerge during P2 (first paid jobs on Base/Solana):

1. **Unit-of-account instability.** Pricing a job directly in a volatile gas
   token, or re-quoting every job in USDC against a moving compute benchmark,
   creates friction: a job quoted at job-post time and settled at claim time can
   drift. The `protocol_compute_currency.md` research (§2.1) shows every DePIN
   compute-token (RNDR, AKT, GLM, LPT) hits this — they all price work in
   USD/benchmark and only settle in token at an oracle rate.
2. **Treasury float and netting.** Per-corridor CCTP rebalancing (ADR-0001) and
   internal netting want a single internal denomination to clear against, so
   that not every micro-job crosses a chain boundary.

The question this ADR answers: **if** the operator decides a unit-of-account
layer is needed, what is its shape, scope, and trigger gate — so the decision is
made *now* (cheaply, in docs) rather than under time pressure *later* (when it
could be rushed into a bad design).

## Decision drivers

- **MiCA-light posture.** The protocol must stay out of ART/EMT/CASP scope for
  as long as possible. Any internal unit-of-account must qualify for the
  limited-network / loyalty-scheme exclusion (MiCA Recital) or the utility-token
  exemption (Art. 4), and must **not** be fiat-par-value (which would make it
  EMT) or a reference to a basket of values (which would make it ART).
- **Unit-of-account stability.** The denomination must stay stable against the
  *current* compute price, not the historical one — otherwise the
  Gresham/deterministic-deflation trap bites (holders hoard, nobody spends).
- **Solo-dev implementability.** The design must be buildable by one developer
  without a PID controller, a seigniorage algorithm, or a live market-making
  operation.
- **No custody.** The credit ledger must not make the protocol a custodian of
  user funds in the MiCA/CASP sense; the existing non-custodial escrow pattern
  (ADR-0001 `SettlementAdapter`) must be preserved.
- **Reversibility.** This must be a *one-way door that can stay closed*. The
  credit design must be compatible with a future "do nothing" outcome where the
  protocol stays fee-only USDC forever.

## Considered options

- **Option A — Internal non-transferable work-credit, protocol-as-market-maker
  (the A1 archetype).** A ledger entry denominated in a rolling compute
  benchmark unit; the protocol sells credits at a posted USDC price and buys
  them back at a floor. Not transferable peer-to-peer (only
  protocol-redeemable). MiCA limited-network exclusion applies.
- **Option B — Fully-backed transferable credit (A2).** Same denomination, but
  transferable and backed ≥100% by a USDC treasury with Chainlink Proof of
  Reserve. Stronger redemption guarantee, but heavier bootstrap (real USDC must
  be brought in before any credit exists) and MiCA utility-token scope.
- **Option C — Dual-token Helium BME model (A3).** Internal credit (fix) +
  floating value-token (work-mining, fair launch). The full Helium pattern.
  Defer to ADR-0002 Track C P5+ gate; **not** this ADR's scope.

## Decision outcome

Chosen option: **Option A — Internal non-transferable work-credit (A1), with an
explicit P2.5 trigger gate. Accepting this ADR does not implement it.**

The A1 design is adopted as the **canonical reference** for how an internal
unit-of-account would be built *if* the operator triggers it. The trigger is
**not** "we want a credit" — it is a concrete, measurable operational signal
that the fee-only USDC path is insufficient. Until that signal fires, the
protocol stays fee-only USDC and **no credit ledger, contract, or monetary state
is built**.

### The P2.5 trigger gate (acceptance criteria for actually building this)

The operator may authorize implementation of the A1 credit **only when at least
one** of these is true, documented with real measurements:

1. **Unit-of-account friction is observed.** Job pricing drift between post and
   claim causes operator-visible rework (re-quoting, disputes, or manual
   adjustments) on more than ~5% of paid jobs over a ≥1 month observation
   window.
2. **Cross-corridor netting volume justifies it.** Internal netting of
   per-corridor USDC flows reaches a level where a single internal denomination
   would save material settlement cost (re-benchmarked against the
   `stress`/`security` simulator scenarios).
3. **Treasury float becomes operationally useful.** A credit-denominated float
   would let the protocol fund node onboarding, buyback, or reserves from real
   fee revenue in a way that direct USDC accounting cannot — and the
   `protocol_compute_currency.md` A1 simulation shows the float is solvent
   across 100+ Monte Carlo `stress` runs.

**If none of (1)/(2)/(3) is true, the credit is not built.** The protocol
remains fee-only USDC, and this ADR stays `proposed` indefinitely. That is an
acceptable outcome — the research (`protocol_compute_currency.md` §11, §13)
concludes that for a solo-dev early-stage network, the no-coin/fee-only path is
the correct default unless the unit-of-account/float benefit is concrete.

### Consequences

- **Good:** the decision is made now, cheaply, while there is no time pressure
  and no monetary state to migrate. The A1 design is MiCA-light
  (limited-network exclusion), solo-dev-implementable, and avoids the
  deterministic-deflation trap via a rolling compute benchmark. It is
  reversible: staying fee-only is the default, not a regression.
- **Bad / cost:** if the trigger never fires, this ADR is "wasted" design work
  (acceptable — it is a small doc cost for a large future option). If the
  trigger fires, the operator must still commission a MiCA opinion
  (limited-network exclusion is a legal judgment, not an engineering one) and
  add an audit budget for the ledger contract.
- **Follow-up:** (a) a `crates/credit-ledger` design (if triggered) that
  implements the A1 ledger as a new `SettlementAdapter` (per
  `protocol_compute_currency.md` §9); (b) a rolling compute-benchmark oracle
  spec (medianized, multi-source, TWAP-guarded); (c) a simulator
  `stress`/`security` re-run with the credit model active.

### Out of scope (deliberately deferred)

- **A floating tradable token (Option C / A3).** That remains ADR-0002 Track C,
  P5+ gate, with its own metrics (organic fee revenue ≥ Helium-class ~$11M/yr
  for multiple months, independent node count above Sybil threshold, credit
  velocity not hoarded). **This ADR does not authorize a token launch.**
- **The exact oracle source mix, rebase cadence, and buyback-floor percentage.**
  These are calibration parameters for the simulator + a future implementation
  PR, not for this design ADR.
- **VASP/CASP determination.** Whether operating a non-custodial credit ledger
  triggers registration is a legal question that must be answered before
  implementation, not by this ADR.

## Pros and cons of the options

### Option A — Internal non-transferable work-credit, protocol-as-market-maker (A1)
- Good: MiCA limited-network exclusion is the strongest available legal posture
  (AWS-credit / Steam-wallet analog); rolling compute peg gives stable
  unit-of-account (no Gresham trap); no PID controller or seigniorage to
  calibrate; solo-dev implementable as a new `SettlementAdapter` (the ledger is
  "just another chain" behind the trait); reversible (fee-only is the default).
- Bad: nodes cannot cash out to USDC on demand except through the protocol's
  buyback window (mitigated by a buyback-floor funded from fee revenue); the
  unit-of-account benefit is only real if jobs are actually quoted in credits,
  which requires operator discipline; a MiCA opinion is still needed to confirm
  the limited-network exclusion holds.

### Option B — Fully-backed transferable credit (A2)
- Good: strongest redemption guarantee (≥100% USDC reserve, Chainlink PoR);
  nodes can cash out at par; closest to a "stablecoin-ish" experience.
- Bad: bootstrap requires real USDC in the treasury before any credit exists
  (slows launch); transferability pushes the asset toward MiCA utility-token
  scope (Title II whitepaper notification) rather than the limited-network
  exclusion; heavier accounting (PoR per corridor).

### Option C — Dual-token Helium BME (A3)
- Good: proven at Helium scale; separates unit-of-account (DC) from
  value-accrual (HNT); lets the market price the network's future.
- Bad: the highest MiCA and complexity burden (a tradable value-token triggers
  the full Title II/III regime); introduces a death-spiral surface
  (`protocol_compute_currency.md` §4.2 Terra/Luna post-mortem); not
  solo-dev-calibratable at P2.5 scale. Belongs at the P5+ gate, not here.

## Open questions / research left

- **The exact trigger threshold values** in the P2.5 gate (e.g. "5% of jobs
  re-quoted") are initial proposals. They should be revisited once P2 paid-job
  data exists, and re-benchmarked against the simulator.
- **Oracle design.** A rolling compute benchmark needs a medianized multi-source
  feed (internal auction data if volume exists; otherwise Vast.ai / Akash / io.net
  public APIs + ENTSO-E energy as a secondary anchor). TWAP-guarded, with a
  rebase protocol for when a new GPU generation ships (e.g. RTX 6090). This is
  an implementation-PR concern, not an ADR concern.
- **MiCA limited-network confirmation.** The exclusion requires the credit to be
  "technically not transferable between holders" and accepted "only by the
  issuer". A legal opinion must confirm the planned ledger design satisfies
  this before any code ships. **This is a blocking legal gate, not an
  engineering one.**
- **Whether A1 actually beats fee-only.** The `protocol_compute_currency.md`
  risk register (§11) notes the net assessment leans no-coin in the early stage.
  This ADR preserves the option but does not override that lean — the P2.5
  trigger gate exists precisely to require measured evidence before building.

## Links

- Supersedes / superseded by: none (this is a new, narrower ADR scoped to the
  internal credit only; the broader token/L1/bridge question remains ADR-0002
  Track C).
- Related: `docs/research/protocol_compute_currency.md` (Report 3 — the full
  tokenomics analysis this ADR operationalizes; A1 = archetype 1 in its §4.6
  coherence map).
- Related: `docs/adr/0001-multi-network-settlement.md` (the credit ledger, if
  built, becomes a new `SettlementAdapter` behind the same trait).
- Related: `docs/adr/0002-four-track-decision-matrix.md` (Track C; this ADR is
  a strict subset — internal credit only, no token/L1/bridge).
- Related: `SECURITY.md` §2 (a credit ledger is a settlement-release-adjacent
  change; the merge remains the operator's in person, never an agent's).
