# HDCN — Project Handbook (agent-driven development, human merge-gate)

**Project:** Hybrid Decentralized Compute Network (HDCN) — a chain-agnostic,
multi-network decentralized compute network.
**This file:** the human-facing handbook. The agent-spec files that live in the
repo (`AGENTS.md`, `SECURITY.md`, ADRs, workflows) are **in English**, because AI
agents (Codex, Claude Code) parse them and English is the reliable convention — but
all of their rationale is here (and mirrored in Hungarian in
`PROJEKT_KEZIKONYV_HU.md`). The mirror-translation principle is therefore: **the
documentation is bilingual; the code-adjacent repo artifacts stay in English** (if
you explicitly want Hungarian reading copies of them, I will produce those too).

---

## 0. One-sentence summary

ChatGPT's strategic direction is good ("compute-first, settlement-later," don't do
everything at once, don't start trustless compute with GPU inference) — keep it; its
two weaknesses (the multi-network framing and project-specific concreteness) are
filled in this pack, together with a copy-paste repo skeleton.

---

## 1. Evaluating the ChatGPT analysis

### 1.1 What it gets right (keep)

- **Compute-first, settlement-later**, and splitting the project (compute mesh vs.
  cross-chain settlement) — the right reflex. Don't build the P2P, GPU, token,
  multi-chain, and agent-workflow all at once.
- **Don't start trustless compute with GPU inference.** CUDA floating-point
  nondeterminism + driver versions mean "it ran, therefore it's correct" is not
  enough; deterministic WASM / render-tile-hash / fixed-seed Monte Carlo is the
  right first workload. This is its most important technical call, and it's correct.
- **The AI-agent security section** (never a key/seed/mainnet-deploy to an agent,
  never auto-merge a settlement PR, always human approval + fine-grained token +
  branch protection). Many people get this wrong — it doesn't. This is the memo's
  most valuable part.
- **It doesn't just talk, it ships:** a runnable simulator (supply, power cost,
  treasury, Sybil, verification committee), and it honestly calls it a
  "decision-support model, not a prediction." Good epistemic hygiene.

### 1.2 Where it's weak or imprecise (we fill this in)

- **It gets the multi-network framing wrong.** It pivots to Base/EVM and sidelines
  Sui (and the rest). Your decision, though: **this is a multi-network project;
  Sui is neither more nor less important than the others.** The correct frame: ~8
  equal settlement adapters behind one `SettlementAdapter` trait; **Base is merely
  the first implemented** chain because it's a cheap/fast EVM and one Solidity
  codebase covers four EVM chains. This is **sequencing, not ranking.** (The whole
  pack treats it this way; see ADR-0001.)
- **It didn't recognize FlowMate as a ready dogfooding workload.** It mentions a
  generic "WASM backtest"; the point is that you *already have* a backtesting
  framework that can be the first real, chain-independent workload and de-risks the
  whole thing. The compute network is a separate project from FlowMate, but
  FlowMate's distributed backtest can be its first load.
- **Zero time/cost estimate.** That matters to a solo dev. Prior research gave
  concrete numbers (roughly ~9-11 months to beta; comfortable AI subscription
  ~$206/month; infra ~€10-15/month). Keep this in mind when deciding.
- **Thin on MiCA/regulation.** For an EU (HU/AT) solo dev, "when does this become a
  licensed activity" can be project-ending, and it's not an engineering problem.
  Default posture: **fee-only, no token, non-custodial** — that minimizes exposure;
  the VASP/CASP question needs a lawyer before permissionless mainnet.

### 1.3 "Not too restrictive?" — your concern

ChatGPT leans slightly **conservative**: it pushes a lot "for later" (token, GPU,
multi-chain, Sui). The sequencing is mostly right, but it's important to see: these
are **priority decisions, not permanent bans.** This pack therefore **preserves the
research options** (every ADR has an "Open questions / research left" section; the
settlement layer keeps ERC-7683 intent/solver as a later option; GPU is a separate
track). You can move GPU or any chain earlier if you have a reason.

---

## 2. Project framing (the main axes of development)

1. **Compute-first.** The mesh is the product. Token/GPU/multi-chain breadth later.
2. **Multi-network by design.** Nothing privileges one chain in the core;
   chain-specifics go into adapter crates. Base is first, for sequencing reasons.
3. **Deterministic verification > raw throughput.** First workloads in Wasmtime,
   fuel-metered, verified by bit-identical re-execution. GPU is a separate, later,
   standalone track (`executor-gpu`, separate process).
4. **Human merge-gate.** Agents open issues/PRs and review; **you merge.**
   Settlement/crypto/CI-permission PRs are yours alone.

---

## 3. Repo setup (step by step)

The pack's `hdcn/` folder is a ready repo skeleton. Steps:

**3.1 Repo + basics**
1. Create a private GitHub repo (`hdcn`) and copy in the contents of `hdcn/`.
2. Pin the stable channel in `rust-toolchain.toml` (reproducible build).
3. Drop ChatGPT's `depin_network_model.py` into `sim/` (both `ci.yml` and
   `sim-dispatch.yml` call it from there).

**3.2 Branch protection (`main`)** — Settings → Branches → Add rule:
- Require a pull request before merging → **Require approvals: 1** (you).
- Require status checks to pass → check the `ci` jobs (test, supply-chain,
  determinism).
- **Do not allow force pushes**, **do not allow deletions**.
- (Optional) Require signed commits if Claude/Codex use commit signing.

**3.3 Secrets** — Settings → Secrets and variables → Actions:
- `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_OAUTH_TOKEN`) for Claude Code.
- `OPENAI_API_KEY` for Codex.
- **Important:** these are repository secrets; fork PRs do **not** see them by
  default (`pull_request` trigger), so the agent step no-ops on a fork PR — this is
  the safe default. See `SECURITY.md` §4.
- Ideally, instead of a static key, use **OIDC / workload identity federation**
  (the Claude action supports it) — nothing to leak/rotate.

**3.4 Installing the GitHub Apps**
- **Claude:** easiest is `/install-github-app` from the Claude Code CLI (installs
  the GitHub App + the secret + a sample workflow). Requires admin.
- **Codex:** turn on "Code review" for the repo in Codex cloud (that's what enables
  `@codex review`), or use the self-hosted `openai/codex-action` (the
  `codex-review.yml` already does this).

**3.5 Verification**
- Open a dummy PR → `@claude` in a comment → replies within ~30-60s.
- `@codex review` on a PR (if the cloud path is on) → 👀 reaction, then a P0/P1
  review.
- Trigger the simulator from the UI: Actions → sim-dispatch → Run workflow.

---

## 4. The repo file set — what each file does

| File | Role |
|---|---|
| `AGENTS.md` (root) | The master agent contract: what the project is, the stack, agent roles, coding rules, review guidelines (Codex reads `## Review guidelines` from here), and the hard stops. |
| `crates/proto/AGENTS.md` | Per-crate tightening for the wire format: postcard-only, canonical byte layout, zero nondeterminism, signature coverage, mandatory round-trip tests. |
| `crates/settle-core/AGENTS.md` | Per-crate tightening for settlement: stay chain-neutral, non-custodial, explicit release conditions, no floats for money, replay safety, MiCA warning. |
| `SECURITY.md` | Agent guardrails: never a key/seed/mainnet-deploy; never auto-merge; fork-PR and sandbox rules; the Telegram/Hermes control-plane boundary; disclosure. |
| `docs/adr/0000-adr-template.md` | MADR-format ADR template (has an "Open questions / research left" section — to preserve research options). |
| `docs/adr/0001-multi-network-settlement.md` | Filled example: the multi-network decision + Base-first sequencing recorded. |
| `.github/workflows/ci.yml` | fmt/clippy/test OS matrix + Miri (core crates) + cargo-deny/audit + sim-smoke. |
| `.github/workflows/claude.yml` | `@claude` interactive agent (fork-safe triggers, `--max-turns` bound). |
| `.github/workflows/codex-review.yml` | Self-hosted Codex PR review (read-only sandbox, allow-users). |
| `.github/codex/prompts/review.md` | The Codex review prompt (P0/P1 checklist). |
| `.github/workflows/sim-dispatch.yml` | `workflow_dispatch` for the simulator — triggerable from Telegram via REST. |

---

## 5. GitHub Actions AI automation (2026 syntax)

### 5.1 Claude Code — `@claude`

`anthropics/claude-code-action@v1` runs the full Claude Code runtime on the
GitHub runner; the code never leaves GitHub's infrastructure, the API call goes to
your chosen provider. **v1** consolidated the CLI options under `claude_args`, and
the mode (interactive `@claude` vs. automation prompt) is auto-detected. Triggers:
`issue_comment` / `pull_request_review_comment` / `issues` / `pull_request_review`.
Permissions: `contents`, `pull-requests`, `issues` write + `id-token: write`
(OIDC). Auth: `anthropic_api_key`, or `claude_code_oauth_token` (Pro/Max: `claude
setup-token`), or — best — workload identity federation (no static key).
`--max-turns` is mandatory for cost/safety (3-5 for review, 10-15 for complex
tasks). See `claude.yml`.

### 5.2 Codex — `@codex review` and the self-hosted action

Two paths, both worth knowing:

- **Cloud path (`@codex review`):** turn on "Code review" in Codex settings, then
  comment `@codex review` on a PR. Codex reacts with 👀 and posts a review; it
  applies the **nearest `AGENTS.md`** guidelines to each changed file, and on
  GitHub it flags **only P0/P1**. With "Automatic reviews" on, it reviews every new
  PR automatically. This is the simplest — no YAML.
- **Self-hosted path (`openai/codex-action@v1`):** when you want full control of the
  prompt/model. `codex-review.yml` does this: on `pull_request`, checkout the merge
  ref, Codex in a **read-only** sandbox with the `review.md` prompt, then a second
  job posts the result as a comment. Sandbox modes: `read-only` / `workspace-write`
  / `danger-full-access` — always `read-only` for review. Restrict who can trigger
  with `allow-users`. Pin the action to a **SHA** in production (trust boundary).

Key link to `AGENTS.md`: Codex specifically looks for and applies the
`## Review guidelines` section — hence it's in the root `AGENTS.md`, and the
per-crate `proto`/`settle-core` guidelines are stricter.

### 5.3 `workflow_dispatch` (triggerable from Telegram too)

`sim-dispatch.yml` runs on `workflow_dispatch` with `scenario`/`runs`/`days`
inputs. It can be triggered programmatically (e.g. from a Telegram bot) via REST:

```
POST /repos/{owner}/{repo}/actions/workflows/sim-dispatch.yml/dispatches
Authorization: Bearer <fine-grained PAT, "Actions: write">
X-GitHub-Api-Version: 2022-11-28
{ "ref": "main", "inputs": { "scenario": "stress", "runs": "100", "days": "365" } }
```

The bot only **dispatches** — it holds no keys and deploys nothing. The token is
fine-grained, scoped to this repo. On the Telegram side, the official HTTP Bot API
+ webhook is the right pattern (webhook → FastAPI → `workflow_dispatch` → Actions →
artifact + summary → Telegram reply), with a `chat_id` allowlist. See `SECURITY.md`
§5.

### 5.4 The agent workflow in one picture

```
You (Telegram/GitHub)
  └─ open issue / workflow_dispatch
       ├─ Hermes: summarize, classify, dispatch (NO KEYS)
       ├─ Claude Code (@claude): architecture, critical crates, open PR
       ├─ Codex (@codex review): adversarial review, P0/P1
       ├─ GitHub Actions CI: fmt/clippy/test/miri/deny/audit + sim-smoke
       └─ YOU: merge-gate (settlement/crypto/CI-permission PRs are yours only)
```

---

## 6. Development sprints (solo dev + agents)

### 6.1 The sprint cycle (issue → spec → impl → review → CI → merge)

A task's path is always the same, and you stand at the gate:

1. **Issue** (you, or Hermes from Telegram) — clear description, acceptance
   criteria.
2. **Spec/ADR** (architect agent, usually Claude Code) — if the task touches a
   stack decision or protocol element, an ADR PR first (`proposed`).
3. **Implementation** on a separate branch (`agent/<name>/<type>-<slug>`) — one
   crate = one agent; `proto`/`verify`/`settle-core` is Claude, the parallel/test
   side is Codex, boilerplate is GLM.
4. **Cross-review** — the other agent (`@codex review` or `@claude`) reviews; on
   disagreement, escalate to you.
5. **CI** — fmt/clippy/test/miri/deny/audit + sim-smoke green.
6. **Merge** — **you.** You move the ADR to `accepted`.

### 6.2 Cadence

For a solo dev, a "sprint" is more a **1-2 week focus block** within a phase than a
ceremony. Suggestion: a **weekly cycle** — Monday: pick issues + ADRs; midweek:
agent implementation + review; Friday: merge window + run the simulator for
decisions (`base`/`stress`/`security`, 100-500 Monte Carlo runs). Watch the rate
limits: on the Claude/Codex subscriptions the token budget is the bottleneck, not
the clock.

### 6.3 Phased roadmap (P0 → P5)

| Phase | Goal / deliverable | Go/No-Go |
|---|---|---|
| **P0** | Working repo: `sim/` simulator, CI, `AGENTS.md` set, Telegram/Hermes control, ADRs. | The `base`/`stress`/`security` scenarios run in CI; `@claude`/`@codex` respond. |
| **P1** | Local compute proof: Rust CLI + Wasmtime task runner + input/output hash + signed receipt + local verifier. | One deterministic WASM task (e.g. a FlowMate subtask) yields a **bit-identical** `output_commit` on 2-3 machines. |
| **P2** | iroh P2P mesh: 3-10 nodes, capability announce, job gossip, bid, assignment, result commit, receipt, latency/relay metrics. | 10+ nodes with stable gossip, receipt DAG being built behind NAT. |
| **P3** | Base escrow: Foundry `ComputeEscrow.sol`, receipt submit, release, dispute placeholder, Base Sepolia deploy. | `escrow_create → release → claim` green on testnet. |
| **P4** | GPU worker (SEPARATE track): NVML detection, CUDA benchmark, GPU task runner, redundant verification, challenge. | A cheating GPU worker is reliably detected; the GPU process is isolated. |
| **P5** | Multi-chain / intent layer: CCTP adapter, ERC-7683-compatible intent representation, LI.FI/Socket quote layer, solver integration; more chains. | 3+ chains with mainnet escrow; intent-solver only with validated corridor volume. |

The order of GPU (P4) and Base (P3) is swappable if your priority differs — GPU is a
separate project track that can run alongside FlowMate's CPU workload.

---

## 7. Settlement layer (multi-network) — the uploaded analyses folded in

### 7.1 The main lesson from the cross-chain analysis

A "single fast P2P layer above all chains/DEXs" is **not feasible** in its literal
form: there is no shared state across chains, finality differs per chain, and
settlement must ultimately happen **on-chain** (the slowest chain is the
bottleneck). The closest realistic model is an **intent/solver/filler**
architecture around **ERC-7683**, with aggregators (LI.FI, Socket/Bungee). At
solo/small-team scale, **not your own base protocol/L1** is the right direction, but
a layer built on existing settlement/bridge/aggregator infrastructure. Therefore:

- The P2P overlay is useful in the **compute layer** (job gossip, discovery, receipt
  DAG, censorship resistance), **not** in financial finality.
- Financial finality happens **on-chain**, per corridor.

### 7.2 The chosen model (ADR-0001)

- **Chain-agnostic `SettlementAdapter` trait**; every chain is equal.
  `escrow_create / escrow_release / escrow_refund / claim_payment /
  anchor_checkpoint`. Core is chain-neutral; specifics live in the adapter crate.
- **Base is the first adapter** (cheap EVM, one Solidity codebase for 4 EVM chains)
  — sequencing, not ranking. Order: Base → Solana → Sui → BNB/Avalanche (same
  contract) → Polkadot → XRPL (last, weakest Rust SDK).
- **Settlement asset:** USDC via **CCTP V2** where available (native burn/mint,
  non-custodial, no wrapped bridge); chain support needs a **fresh check before
  implementation** (Circle may change/expand the canonical version). XRPL is not on
  CCTP → **RLUSD** or a corridor bridge.
- **ERC-7683 intent/solver** = a **later** optimization for large one-off
  cross-corridor payouts (it separates "what the user wants" vs. "how the solver
  fulfills it"), **not** the base primitive. Internal netting/clearing is the
  default; the intent-solver pays off once there is corridor volume.

### 7.3 The settlement ladder (tied to phases)

```
P0: mock/local accounting
P1: signed receipts + redb/SQLite ledger
P2/P3: Base Sepolia escrow → Base mainnet small USDC escrow
P4-P5: CCTP/USDC where stable → ERC-7683 intent/solver, LI.FI/Socket quote layer
```

### 7.4 Regulation (not legal advice)

Default posture: **fee-only, no protocol token, non-custodial** — this keeps MiCA
exposure light-touch (no asset-referenced/e-money token issuer obligation on the
protocol side). Operating the matching + settlement may raise the **VASP/CASP**
registration question — that's a **legal** decision before permissionless mainnet,
not an engineering one. `settle-core/AGENTS.md` therefore forbids an agent from
introducing a token/custody; on such a task the agent must **stop** and open an
issue for you.

---

## 8. Open research questions / preserved options

These are **deliberately left open** — every ADR has a "research left" section:

- **Consensus/verification depth:** committee size (`k`), VRF sampling parameters,
  redundancy ratio for GPU vs. CPU jobs — the simulator's `security` scenario showed
  the "bad work" share is still too high, so verification parameters need to be more
  aggressive. This is a calibration question.
- **Network scaling:** iroh-gossip at 50+ nodes behind NAT — if it doesn't scale,
  switch to libp2p gossipsub (transport can stay iroh). A benchmark decides.
- **Wire format:** postcard is the default; if a non-Rust client is ever needed,
  protobuf for the external API (internal stays postcard).
- **Anchoring strategy:** "cheapest 2-3 chains + per-corridor finality" (e.g.
  XRPL+Solana) vs. a rotating anchor chain — a cost/trust trade-off, and chain
  prices are volatile.
- **ERC-7683 timing:** when the intent/solver beats internal netting — a function of
  corridor volume.
- **GPU track:** when and which vertical (AI inference / rendering / ZK proving) — a
  separate project track, after the deterministic CPU core is stabilized.
- **Simulation tool:** the current numpy/pandas model is enough for P0-P2; for a
  more complex agent-based model, cadCAD/radCAD/Mesa later.
- **AI budget:** Comfortable (~$206/month) is the starting tier; Accelerated only if
  you keep hitting limits with real work for 2 weeks straight.

---

## 9. The next best step

1. Create the repo with this pack; `depin_network_model.py` into `sim/`.
2. Set up branch protection + secrets + the two GitHub Apps (Claude, Codex).
3. Run the `base`/`stress`/`security` scenarios with 100-500 Monte Carlo runs (the
   `stress` scenario immediately shows the network collapses under a demand shock
   without treasury + node onboarding — decision support, not a prediction).
4. Only then the Rust P1 skeleton (`proto` + `identity` + `transport` +
   `executor-wasm`), with a FlowMate subtask as the first deterministic WASM task.

> **Source handling in the files:** the concrete syntax in the `AGENTS.md`/workflows
> follows the official `anthropics/claude-code-action` and `openai/codex-action`
> documentation (mid-2026); `workflow_dispatch` follows the GitHub REST API. Verify
> the current versions before production use, as these change quickly.
