# AGENTS.md — Hybrid Decentralized Compute Network (HDCN)

> This file is the **root contract** for every AI coding agent (Codex, Claude Code,
> GLM, or any other) that touches this repository. Agents MUST read this file and the
> nearest `AGENTS.md` to each changed file before making changes. A human is the sole
> merge gate — see `SECURITY.md`.
>
> This file is intentionally written in **English**: `AGENTS.md` is a machine-facing
> convention that both Codex and Claude Code parse, and English maximizes their
> reliability. The human-facing rationale for every rule here lives in the project
> handbook (`PROJECT_HANDBOOK_EN.md` / `PROJEKT_KEZIKONYV_HU.md`).
>
> Mandatory orientation: before planning or editing, agents MUST read
> `docs/ai/REPO_MAP.md` and follow its cross-review, anti-duplication, and
> documentation rules.

## 1. What this project is

HDCN is a **chain-agnostic, multi-network decentralized compute network** (DePIN).
Home/edge PCs contribute CPU (and later GPU) capacity; work is verified by
signed receipts + redundant execution; payment settles on-chain through a
**settlement adapter layer** where multiple chains are **equal endpoints**
(no single "home chain").

Non-negotiable framing:

- **Compute-first, settlement-later.** The compute mesh is the product. Tokens,
  GPU, and multi-chain breadth come in later phases (see roadmap in the handbook).
- **Multi-network by design.** Solana, Sui, Base, Ethereum, BNB, Polkadot,
  Avalanche, XRPL are all first-class settlement targets behind one
  `SettlementAdapter` trait. **Base is implemented first** only because it is the
  cheapest/fastest EVM to bootstrap and one Solidity codebase covers four EVM
  chains — this is sequencing, not a downgrade of any other chain.
- **Deterministic verification over raw throughput.** The first compute workloads
  are deterministic (WASM/Wasmtime, fuel-metered), because GPU inference is hard
  to verify. GPU is a separate, later track.
- **Four directions stay alive until data decides.** Track A is the current
  implementation default (multi-network + iroh + deterministic receipts +
  FlowMate/backtest). Track B preserves the render/libp2p thesis as a
  multi-network spike across ETH, SUI, SOL, BNB, Base, Polkadot, and future
  adapters; Sui is only one target, not the track. Track C covers own
  L1/token/bridge/hybrid L1-L2. Track D covers GPU/GPU+CPU micro-nodes and
  trustless GPU inference. See ADR-0002 before deleting or privileging any
  track.

## 2. Chosen stack (do not silently change)

| Layer | Choice |
|---|---|
| Language (core) | Rust (stable toolchain, pinned in `rust-toolchain.toml`) |
| Transport | iroh 1.0 (QUIC + hole punching + relay fallback) |
| Gossip | iroh-gossip (HyParView + PlumTree) |
| Blob transfer | iroh-blobs (BLAKE3 content addressing) |
| Wire format | postcard (`no_std`-friendly, deterministic) |
| Hashing | blake3 |
| Node identity / signatures | ed25519 (ed25519-dalek) |
| Local state | redb (or sled) — embedded |
| CPU sandbox | Wasmtime / WASI Preview 2, fuel-metered, deterministic |
| GPU worker (later) | separate process, CUDA/C++; never in the core daemon |
| EVM settlement | alloy (Rust) + Solidity/Foundry contracts |
| Simulation / research | Python (numpy, pandas, matplotlib) |
| Agent control-plane | GitHub Actions (auditable) + optional Hermes/Telegram (commands only) |

Any change to a row above requires an **ADR** (`docs/adr/`) and explicit human
approval. Agents may *propose* changes via an ADR PR; they may not merge them.
The older libp2p direction is preserved as Track B research; switching the
production transport from iroh to libp2p requires prototype data plus an ADR.

## 3. Agent roles

- **Claude Code** — lead architect + implementer of critical/consensus-adjacent
  crates (`proto`, `verify`, `settle-core`, `receipts`, cryptography). Also does
  larger refactors and second-opinion reviews.
- **Codex** — adversarial reviewer + test author + second implementer on
  parallel crates. Owns PR review (`@codex review`).
- **GLM** — bulk/boilerplate implementer (adapter scaffolding, CI glue, docs).
- **Hermes (optional)** — Telegram control-plane only: opens issues, triggers
  workflows, requests reviews, summarizes CI. It never holds keys and never
  deploys. See `SECURITY.md`.
- **Human (Máté)** — merge gate and security authority. The only actor that
  merges settlement/security PRs or touches mainnet.

Cross-review rule: a crate implemented by agent X is reviewed by a different
agent Y. On disagreement, escalate to the human with both positions summarized.
For substantive PRs this is mandatory before merge: Claude-authored work needs
Codex review, Codex-authored work needs Claude review when available, and human
override must be explicit if a second AI reviewer is unavailable.

## 3.1 Mandatory agent workflow

Before editing, every agent must complete the cold-start checklist in
`docs/ai/REPO_MAP.md`: read the repo map, nearest `AGENTS.md`, `SECURITY.md`, the
current sprint doc, relevant ADRs, and the issue/PR. PRs must document:

- tests and simulations run;
- files/docs changed;
- anti-duplication checks performed;
- cross-review status or explicit human-override need.

Agents must avoid duplicate systems and duplicate documents. Before adding a new
file, type, crate, workflow, ADR, or model, search the repo with `rg` and use the
canonical owner in `docs/ai/REPO_MAP.md`. If an owner exists, extend it or link
to it instead of creating a parallel copy.

## 4. Repository layout (Cargo workspace)

```
hdcn/
├── AGENTS.md                  # this file (root contract)
├── SECURITY.md                # agent guardrails + disclosure policy
├── rust-toolchain.toml
├── Cargo.toml                 # [workspace]
├── crates/
│   ├── proto/                 # wire types, receipts (postcard) — AGENTS.md present
│   ├── identity/              # ed25519 keys, NodeId
│   ├── transport/             # iroh endpoint
│   ├── gossip/                # iroh-gossip topics
│   ├── capability/            # hw detect (sysinfo; nvml later)
│   ├── executor-wasm/         # Wasmtime, fuel-metered, deterministic
│   ├── executor-gpu/          # LATER: CUDA/C++ worker, separate process
│   ├── verify/                # committee, VRF sampling, redundant compare
│   ├── receipts/              # DAG store (redb)
│   ├── settle-core/           # SettlementAdapter trait, netting — AGENTS.md present
│   ├── settle-evm/            # alloy (Base first)
│   ├── settle-*               # solana / sui / polkadot / xrpl (later)
│   ├── checkpoint/            # epoch anchoring
│   ├── node/                  # daemon binary
│   └── cli/
├── contracts/                 # solidity (Foundry), move, anchor
├── sim/                       # Python simulator (depin_network_model.py)
├── docs/ai/                   # AI repo map, workflow, anti-dup rules
└── docs/adr/                  # Architecture Decision Records
```

## 5. Coding rules (enforced by CI — see `.github/workflows/ci.yml`)

- **No panics in library code.** Return `Result`; use `thiserror` for error types.
  `.unwrap()`/`.expect()`/`panic!` are allowed only in tests and `main`.
- **Determinism in verify/consensus paths.** No wall-clock, no RNG, no `HashMap`
  iteration order dependence, no float NaN reliance in any code that a verifier
  re-executes or that feeds a hash commit. Use ordered maps and fixed seeds.
- **Wire types round-trip.** Every type that crosses the network has a `proptest`
  postcard round-trip test.
- **`unsafe` is justified or rejected.** Every `unsafe` block needs a comment
  proving why it is sound; prefer none. Core crates should pass `cargo miri test`.
- **Every public item is documented.**
- **Every substantive PR is documented.** Update ADRs, sprint notes, modeling
  docs, and the AI repo map when the changed area requires it.
- **Conventional commits** and branch naming: `agent/<name>/<type>-<slug>`
  (e.g. `agent/claude/feat-receipt-dag`, `agent/codex/test-proto-roundtrip`).

Required local gates before opening a PR:

```
cargo fmt --check
cargo clippy --all-targets -- -D warnings
cargo test --all
cargo deny check        # licenses + RUSTSEC advisories
cargo audit
```

## 6. Review guidelines

> This section is read by Codex (`@codex review`) and by Claude Code. Flag issues
> with a severity. In GitHub, Codex surfaces only **P0** and **P1**.

- **P0 (block merge):**
  - Missing or incorrect signature/verification on any receipt, attestation, or
    settlement message; any replay-attack opening.
  - Any private key, seed phrase, mnemonic, RPC secret, or mainnet address/endpoint
    committed to the repo or printed to logs.
  - Non-determinism introduced into a verify/consensus/hash-commit path.
  - `unwrap`/`panic!` on attacker-influenced input in library code.
  - A settlement code path that can release funds without the intended condition.
  - Substantive PR merged without required cross-review or explicit human
    override.
- **P1 (should fix):**
  - Missing `proptest` round-trip for a new wire type.
  - Missing tests for the behavior a PR claims to add.
  - `unsafe` without a soundness comment.
  - Public API without docs; TODOs left in shipped code paths.
  - Silent change to a stack decision from §2 without an ADR.
  - New file/crate/workflow/doc without an anti-duplication check or repo-map
    update when it changes ownership/navigation.

## 7. What agents must NOT do (hard stops)

See `SECURITY.md` for the full policy. Summary:

- Never generate, request, store, or log private keys / seed phrases / mnemonics.
- Never deploy to any mainnet, move treasury funds, or edit
  signing/settlement-release logic **and** merge it. Such PRs require a human.
- Never auto-merge. Agents open PRs; the human merges.
- Never widen `permissions:` in a workflow, add a new secret consumer, or change
  branch-protection expectations without flagging it as a trust-boundary change.
- When uncertain about a security-relevant choice, stop and open an issue for the
  human instead of guessing.
