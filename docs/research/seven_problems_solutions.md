# HDCN — The Seven Hard Problems: Research-Deepened Solution Plans

> **Canonical owner: the seven-hard-problems risk & solution register.** For each hard
> problem this maps the 2026 state of the art → the HDCN solution plan → an honest
> verdict → the P0–P5 phase that addresses it. It operationalizes the roadmap and is
> cross-referenced from it: the four-track matrix
> (`docs/adr/0002-four-track-decision-matrix.md`), the modeling gates
> (`docs/modeling/DIRECTION_MODELING_PLAN.md`), the architecture
> (`docs/research/hybrid_decentralized_compute_network.md` = "Report 1"), and the
> tokenomics (`docs/research/protocol_compute_currency.md` = "Report 3"). The risky
> problems (#2 Sybil, #3 slashing parameters, #7 sustainability) are quantified by the
> simulator (`sim/depin_network_model.py`, `security`/`stress` scenarios). This is a
> design/risk input, not an accepted ADR — open items are tracked in ADR-0002.

> Scope: the seven questions every decentralized-compute network must answer, treated
> in depth with the current (2026) state of the art and a concrete solution plan for
> the **Hybrid Decentralized Compute Network** (chain-agnostic, multi-network DePIN).
> Honest throughout: what is solved, what is partial, what is the weak point. Sources
> are attributed inline; verify current versions before building, as this field moves
> fast.

## Verdict at a glance

| # | Problem | Status for HDCN | One-line reason |
|---|---|---|---|
| 1 | Prove the GPU did the work | **Partial (workload-dependent)** | Clean for deterministic work; only statistical for GPU inference on consumer cards |
| 2 | Stop 10,000 fake nodes | **Conditional (scale-dependent)** | Stake + reputation + PoPW works, but weak while small → whitelist beta first |
| 3 | Punish bad results | **Solved** | Stake + slashing via optimistic fraud proof + dispute game |
| 4 | Spam / DDoS defense | **Weakest — needs explicit design** | Escrow-gating + stake help; transport-layer DDoS is standard ops hardening |
| 5 | NAT'd home PCs | **Solved** | iroh 1.0: QUIC + hole punching + relay fallback |
| 6 | Deterministic compute | **Solved for CPU/WASM, partial for GPU** | Wasmtime fuel metering is bit-deterministic; CUDA FP is not |
| 7 | Sustainable reward model | **Conditional (real demand + solvent treasury)** | Fee-only ties rewards to real demand; a tuning problem, not automatic |

The common thread: the architecture is deliberately sequenced so the MVP is built
from the cleanly-solvable pieces (deterministic verification, iroh NAT traversal,
stake/slashing, escrow-gated spam control, whitelist beta), and the hard/open pieces
(general GPU verification, Sybil at scale, general economic sustainability) run on a
separate, later track. The #2/#3/#7 risks are measured concretely by the simulator's
`security` and `stress` scenarios — this is not hand-waving.

---

## 1. How do you prove the GPU actually did the work?

**This is the hardest question, and there is no single universal answer** — which is
exactly why the plan says *don't start with GPU inference*.

### State of the art (2026)

Verifiable inference splits into three families (per Equilibrium Labs' and Gensyn's
surveys): trust-based (TEE / reputation), learning-based, and execution-based.

- **Redundant re-execution + hashing (deterministic case).** For deterministic
  workloads the verifier re-runs the job and compares a content-addressed output
  hash. This is cheap and near-absolute. It is the basis of HDCN's first workloads.
- **TOPLOC (Prime Intellect, ICML 2025).** A locality-sensitive hashing scheme:
  the provider commits to the top-k values of the last hidden state; a validator
  recomputes and checks, limiting overhead to roughly 1%. It detects undisclosed
  changes to the model, prompt, or numerical precision with near-100% accuracy in
  the authors' tests — but, being hash-based, the guarantee is **statistical**, with
  residual edge-case risk.
- **Verde + RepOps (Gensyn, in production 2025).** An optimistic "refereed
  delegation" protocol: on dispute, an interactive binary-search (the
  Teutsch–Reitwießner verification game used by optimistic rollups) narrows the
  disagreement to a single operation, which the referee re-runs. It assumes **at
  least one honest party**. RepOps/RepDL make float operators reproducible by fixing
  the order of floating-point operations, attacking the nondeterminism problem head
  on.
- **CPU re-derivation (Hawkeye, 2026).** Frameworks now let anyone re-execute the
  exact NVIDIA-GPU matmul operations on a CPU, making a GPU run independently
  checkable — useful for spot audits.
- **zkML** (zero-knowledge proofs of inference) is the cryptographic ideal —
  self-verifying, no honest-majority assumption — but for LLM-scale inference it is
  still far too expensive (published proving times run into thousands of seconds per
  component). Viable today only for small models / narrow circuits.
- **TEE attestation** (NVIDIA H100/H200 confidential computing, Intel SGX enclaves)
  gives hardware-signed proof of correct execution, but it is a developing
  technology with a history of vulnerabilities, and crucially **consumer RTX cards
  have no such TEE**.

### HDCN solution plan

1. **Start deterministic.** First workloads are WASM (Wasmtime, fuel-metered),
   render-tile hashing, and ZK-proof generation — all verifiable by exact
   re-execution + BLAKE3 output-commit comparison, or self-verifying (ZK). The
   FlowMate distributed backtest is the first such workload.
2. **Sampled verifier committee.** A VRF-selected committee re-executes and compares
   the content-addressed output; quorum attests, disagreement opens a dispute
   (see #3). Committee size and redundancy are tunable per job class.
3. **When GPU inference comes (separate, later track):** layer TOPLOC-style LSH
   commitments + RepOps-style reproducible operators + redundant execution +
   reputation weighting, and use TEE attestation *only* where the hardware supports
   it (datacenter H100/H200), never assuming it on consumer cards.

### Honest verdict

Solved for deterministic work; only **statistical** for GPU inference on consumer
hardware. Do not promise absolute proof of arbitrary GPU inference — the field
cannot deliver that cheaply yet. Sequencing around this is the whole point.

**Phases:** P1 (deterministic WASM proof) → P4 (GPU track with statistical
verification).

---

## 2. How do you stop an attacker spinning up 10,000 fake nodes?

Faking hardware is cheap — io.net's postmortem reported roughly 1.8M fake GPUs
attempting to join before its proof-of-work patch cut active GPUs from ~600k to
~10k. Hardware alone therefore proves nothing.

### State of the art (2026)

The Sybil-resistance literature is blunt: **strong** resistance comes from
Proof-of-Work or Proof-of-Stake (a real economic cost per identity); reputation
systems and physical-world linking give only **limited** resistance on their own.
DePIN adds physical-work proofs on top:

- **Proof of Physical Work (PoPW).** Helium's Proof of Coverage (RF-signal witnesses
  from peer devices), Filecoin's Proof-of-Replication + Proof-of-Spacetime (Merkle
  challenges over stored data). Each ties rewards to demonstrable real work.
- **Proof-of-Presence / device KYC (2026).** Hardware-rooted identity via a TEE or
  secure element, minted as a non-transferable on-chain credential (SBT) bound to a
  specific CPU/TPM rather than a person. Adds ~20-30% overhead but creates real
  hardware scarcity. Not available on all consumer hardware.
- **Stake + reputation + slashing + heartbeat**, with new nodes starting at low
  priority and earning trust over time.

### HDCN solution plan

- **Stake per identity** on the node's chosen settlement chain (via the multi-network
  `SettlementAdapter` — every fake identity costs real collateral).
- **Reputation accrual:** new nodes get low job-dispatch priority and must earn
  standing; reputation lowers the staking requirement and raises committee-selection
  odds. This makes 10,000 fresh identities economically pointless.
- **Proof-of-GPU-work at registration:** a benchmark/stress challenge (io.net-style)
  to filter trivially-fake capacity.
- **VRF committee bound to the anchored epoch root** to resist grinding.
- **Whitelist / permissioned beta FIRST.** The honest core: statistical guarantees
  are weak on a small network, so HDCN gates entry until node count and total stake
  cross a security threshold, then opens permissionless.

### Honest verdict

There is a real plan, but the guarantee is **statistical and weak at small scale** —
the defense that actually matters (economically painful stake) only bites once stake
is large and real. Until then, you gate the door. This is a scale-dependent problem,
handled by sequencing (whitelist → permissionless), not by a clever trick.

**Simulator link:** the `security` scenario models Sybil fake-node pressure,
committee size, and sampling rate, and it flagged the "bad work" share as still too
high — i.e. the verification parameters need to be more aggressive. That is a
calibration signal, not a prediction.

---

## 3. How do you punish a bad result?

### State of the art (2026)

The mature pattern is **optimistic verification + a dispute game**: assume results
are correct, open a challenge window, and on dispute run a refereed-delegation
interactive protocol (Truebit / Arbitrum / Optimism lineage; Gensyn's Verde applies
it to ML) that narrows disagreement to one re-runnable step. Stake is slashed on the
losing side. Restaking systems (EigenLayer-style) generalize slashing — though the
2026 discourse also flags restaking's compounding risks, so keep slashing scoped and
legible. Two-tier designs (e.g. the HadAgent proof-of-inference work) let trusted
nodes serve optimistically while untrusted nodes face full verification.

### HDCN solution plan

- **Min-stake to participate**, locked in an on-chain escrow / staking module on the
  worker's settlement chain (EVM escrow, Move staking module, etc.).
- **Detection:** redundant execution or committee mismatch surfaces a bad output; the
  conflict goes to the `disputes` gossip topic.
- **Dispute resolution:** a larger fallback committee votes; the losing party — a
  cheating worker **or** a lying verifier — is slashed and takes a negative
  reputation delta. Anchoring the epoch root gives non-equivocation evidence so a
  node cannot retroactively show a different history.
- **Economic sizing:** stake must exceed the profit from cheating; slashing revenue
  can partly fund honest verifiers.

### Honest verdict

**Solved**, with two caveats: slashing only deters when stake value > cheating
profit, and detection must be reliable — on a small network, committee collusion is a
real risk (mitigated by larger `k`, VRF binding, and reputation weighting). The
mechanism is standard and well-understood; the risk is parameterization, which the
simulator exists to tune.

**Phases:** P3 (verification committee + reputation + Sybil stake + slashing).

---

## 4. How do you defend against spam / DDoS?

**This is the weakest point in the current plan** — partly economic, partly standard
infrastructure hardening, and the least developed of the seven. Worth stating plainly
rather than papering over.

### State of the art (2026)

- **Gossipsub already ships graded defenses.** v1.1 added peer scoring + behavioral
  penalties; v1.2 added IDONTWANT filtering; v1.4 added rate limiting + GRAFT-flood
  protection; v2.0 added advanced peer scoring. Peer-score thresholds
  (gossip/publish/graylist) progressively suppress and then graylist low-scoring
  peers; mesh degree D≈6 (range 4–12) bounds fan-out; IWANT requests and RPC sizes
  are capped and duplicates deduped via an LRU cache.
- **Peer scoring has known limits.** Audits note it can leak scoring info, be gamed,
  or nudge centralization, and it is beatable by cheap bot-flooding — so it is
  necessary but not sufficient.
- **Rate-Limiting Nullifiers (RLN, Waku's WAKU2-RLN-RELAY).** A cryptographic,
  economic spam defense (Semaphore-based) that caps each participant's message rate
  *globally*; exceeding the rate is cryptographically punished financially, and peers
  who catch spammers are rewarded. Stronger than peer scoring (global, not local) and
  lighter than per-message PoW (which excludes resource-limited devices).
- **Reputation-filtered gossip (StarveSpam, 2026).** Forward high-reputation traffic
  freely; forward low-reputation traffic at reduced priority, sampled, or dropped
  under congestion.
- **libp2p DoS first principles.** Use minimum resources, ensure **no untrusted
  amplification** (an attacker must never force >1× the work it does), price each
  connection, and log + action misbehavers out-of-band (fail2ban-style). Rendezvous
  points need their own spam mitigation.

### HDCN solution plan

- **Economic gating first.** A job only reaches the market after the client locks
  payment on-chain (escrow-first) → job-spam costs money. Participation requires
  stake → the Sybil cost is simultaneously the spam cost.
- **Transport layer:** iroh/QUIC connection limits + gossip peer-scoring and rate
  limiting + reputation-gated job dispatch (StarveSpam-style). Adopt **RLN-style rate
  limiting** on the gossip topics as the principled global cap once the protocol
  matures.
- **Infrastructure hardening:** run your own rate-limited relays/rendezvous (public
  iroh relays are rate-limited anyway), ensure no amplification vectors, add
  fail2ban-style logging/action.

### Honest verdict

The **weakest** area: application-layer DDoS against public relays/rendezvous is a
real operational risk, and the current answer is mostly standard ops hardening plus
economic gating, not a novel mechanism. This needs **explicit design** (it is on the
open-questions list). RLN is the most promising principled addition. Treat this as a
first-class design task before permissionless launch, not an afterthought.

**Phases:** transport-layer defenses in P2; economic gating in P2/P3; RLN and relay
hardening tracked as an explicit pre-mainnet workstream.

---

## 5. How do you handle NAT'd home PCs?

### State of the art (2026)

This is the most confidently solved of the seven. **iroh 1.0** ("dial keys, not IPs")
gives QUIC + built-in hole punching + relay fallback + ed25519 key-based addressing,
with **iroh-gossip** (HyParView + PlumTree) as the pubsub overlay and **iroh-blobs**
(BLAKE3) for transfer. n0 reports its public relays saw very large endpoint volumes,
and projects like Nous Research use iroh for distributed AI. If hole punching fails,
the relayed connection persists as a (limited) fallback.

### HDCN solution plan

- **iroh 1.0 as transport**, ed25519 node key = the `NodeId` in receipts.
- **Own relays in beta** (public relays are rate-limited; pre-1.0 relay sunset means
  staying on 1.0).
- If iroh-gossip does not scale past ~50 nodes behind NAT, switch the gossip layer to
  libp2p gossipsub while keeping iroh transport (captured as an open question).

### Honest verdict

**Solved.** This is precisely why iroh was chosen over raw libp2p — it collapses the
NAT/hole-punch/relay problem into one well-supported library.

**Phases:** P2 (iroh P2P mesh).

---

## 6. How do you make the computation deterministic?

### State of the art (2026)

- **CPU/WASM is cleanly deterministic.** Wasmtime **fuel metering** is fully
  deterministic (the same program with the same fuel always halts at the same point),
  unlike epoch interruption (~10% overhead but nondeterministic). Combined with NaN
  canonicalization, `wasi-virt` to virtualize the clock/filesystem, and control over
  memory/table growth and relaxed-SIMD, this yields bit-identical output across
  machines. WASI Preview 2 is stable; Wasm 3.0 was ratified in September 2025.
- **GPU is not deterministic by default.** CUDA floating-point results vary across
  architecture and driver; academic work (Srivastava/Arora/Boneh, "Optimistic
  Verifiable Training by Controlling Hardware Nondeterminism") shows even identical
  seed + data order can diverge across GPU types. Mitigations — fixed seeds,
  deterministic/reproducible kernels (RepOps/RepDL fixing FP operation order),
  tolerance-based comparison — are **partial**.

### HDCN solution plan

- **All first CPU workloads run in Wasmtime, fuel-metered**, with clock/filesystem
  virtualized and NaN canonicalized → bit-identical `output_commit`, which is what
  makes #1's re-execution verification cheap and near-absolute.
- **GPU determinism (later):** RepOps-style reproducible operators where possible;
  otherwise tolerance-based comparison (perceptual hash / SSIM for rendering, logit
  tolerance for inference) rather than exact equality.

### Honest verdict

**Solved for CPU/WASM, partial for GPU.** The deterministic CPU core is the
foundation of the whole verification story — again the reason deterministic workloads
lead and GPU follows.

**Phases:** P1 (deterministic WASM) → P4 (GPU, partial determinism).

---

## 7. How do you make the reward model economically sustainable?

This is the entire subject of Report 3 plus the simulator.

### State of the art (2026)

- **The DePIN flywheel = Burn-and-Mint Equilibrium (BME).** Per the Frontiers 2026
  DePIN-tokenomics review, the dominant pattern burns the native token to mint
  USD-denominated usage credits (Helium Data Credits at $0.00001; Render Credits) and
  mints new tokens on a schedule to reward providers — shielding users from token
  volatility and tying value to real usage. Akash launched BME in March 2026
  (compute spend buys and burns AKT).
- **The sustainability equation is unforgiving:** long-term issuance must not exceed
  burns + organic demand growth, or the surplus is sell pressure. Utilization above
  ~80% signals real demand (Akash, io.net); below ~20% means subsidizing capacity
  nobody wants. Valuation multiples have compressed to ~10–25× revenue (from ~1000×
  in 2021), and of 650+ DePIN projects fewer than ~20 have meaningful revenue — a
  shakeout is underway.
- **Cautionary tales:** Bittensor's centralization (top-10 validators ~67% of stake;
  a major operator exit in April 2026 triggered a ~20% crash) shows governance and
  concentration risk; Helium's own history (HNT ~$55 in 2021 → ~$1.30–1.80 in 2024)
  shows how far token price can diverge from network usefulness.

### HDCN solution plan

- **Fee-only, no token, to start (MiCA-light).** The protocol takes a percentage of
  the job payment in USDC/native — rewards come from **real paying demand**, not token
  emission. This sidesteps the BME sustainability equation entirely at the MVP stage
  and minimizes regulatory exposure (no asset-referenced/e-money token issuer
  obligation on the protocol side). It matches Report 3's recommendation of a
  compute-pegged internal work-credit over a market-traded token.
- **Reality anchor (from Report 1):** an EU home GPU nets roughly break-even to
  ~€50/month after electricity — the value proposition is monetizing already-sunk
  hardware, not profit. The model must not promise a large margin.
- **A token only later, if ever**, and only after validated demand + legal review; if
  adopted, use BME with governance-calibrated issuance and a treasury reserve (the
  Helium pattern: re-mint burned amount to treasury below a threshold, cap net
  inflation to vesting unlocks, never exceed max supply) — but keep concentration low
  to avoid the Bittensor failure mode.

### Honest verdict

**Conditional.** Sustainable only with real demand + a solvent treasury buffer +
realistic (modest) node economics — it is a tuning problem, not automatic. The
simulator exists precisely to measure this.

**Simulator link:** the model tracks treasury reserve ratio, cashout pressure, demand
elasticity, and node churn. The **`stress` scenario shows the network collapsing
under a demand shock without a treasury + onboarding buffer** (negative minimum
reserve, spiral flags), which is the single most important design warning. Decision
support, not prophecy.

**Phases:** P0 (simulator-driven design) → P5 (optional token/DeFi only after
validated demand).

---

## How the simulator stress-tests the risky problems

The three problems whose status is "conditional" or "weak" (#2 Sybil, #3 slashing
parameterization, #7 sustainability) are exactly the ones the Python simulator
measures, so these are engineering-tunable rather than matters of faith:

- **`base`** — healthy baseline (high fill rate, solvent reserve).
- **`stress`** — demand/price shock; exposes treasury insolvency and collapse without
  onboarding buffers (drives #7).
- **`security`** — Sybil fake-node pressure + verification committee sizing; flagged
  the undetected-bad-work share as too high, i.e. verification must be more aggressive
  (drives #2 and #3).

Run 100–500 Monte Carlo runs per scenario before committing Rust, and re-run whenever
a mechanism parameter changes.

## Open research (deliberately not closed)

- General GPU-inference verification cheap enough for consumer cards (TOPLOC/Verde/
  zkML trajectory).
- Sybil resistance at permissionless scale (stake sizing, Proof-of-Presence adoption
  on heterogeneous consumer hardware).
- Committee parameters (`k`, sampling rate, redundancy) per job class — a calibration
  problem the `security` scenario informs.
- Spam/DDoS: RLN integration and relay/rendezvous hardening — the explicit
  pre-mainnet workstream.
- Reward sustainability: fee-only vs. later BME, treasury reserve sizing, and
  avoiding governance concentration.

The consistent design philosophy: **build from the cleanly-solvable pieces first
(deterministic verification + iroh NAT traversal + stake/slashing + escrow-gated spam
control + whitelist beta), and route the hard/open pieces (general GPU verification,
Sybil at scale, general sustainability) onto a separate, later track — with the
simulator quantifying the risky ones.**
