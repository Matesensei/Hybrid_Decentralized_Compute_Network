# HDCN AI repo map

**Canonical owner:** this file is the orientation map for AI agents working in
the HDCN repository. Every agent must read it before planning or editing a task.
Update this file in the same PR whenever a new top-level area, crate, workflow,
or canonical documentation owner is added.

## Source provenance

Operator-provided source data for Sprint 00:

- Primary archive:
  `/home/matesensei/Asztal/hybrid_decentralized_compute_network/Hybrid_Decentralized_Compute_Network.zip`
- Additional bootstrap archives used in PR #1:
  `/home/matesensei/Asztal/hybrid_decentralized_compute_network/files.zip`
  and `depin_blueprint_pack.zip`

Extracted research/source material is preserved under `docs/research/`. Agents
must treat those files as reference inputs, not as production decisions. Accepted
decisions live in `docs/adr/`, current work planning lives in `docs/sprints/`,
and pre-decision modeling lives in `docs/modeling/`.

Point-in-time 2026-07-16 advisory inputs:

- `docs/research/HDCN_FULL_AUDIT_HU_2026_07_16.md`
- `docs/research/HDCN_INNOVATION_PRODUCT_STRATEGY_HU_2026_07_16.md`

Console agents must enter those reports through
`docs/ai/CONSOLE_HANDOFF_AUDIT_AND_PRODUCT_STRATEGY_2026_07_16.md`. Dated
analyses never override root agent/security rules, accepted ADRs, or the current
sprint.

## Mandatory agent cold start

Before editing code or docs, every agent must read, in order:

1. `AGENTS.md`
2. The nearest nested `AGENTS.md` for the files being changed
3. `docs/ai/REPO_MAP.md`
4. `SECURITY.md`
5. The current sprint doc under `docs/sprints/`
6. Relevant ADRs under `docs/adr/`
7. The GitHub issue or PR being worked on

If any requested change conflicts with these files, the agent must document the
conflict in the PR and ask for human direction or propose an ADR.

## Current repository map

| Path | Owner / purpose | Rules |
|---|---|---|
| `AGENTS.md` | Root AI contract | Keep short enough for agents; update when workflow rules change |
| `SECURITY.md` | Security and merge-gate policy | Never weaken permissions or secret handling without explicit human review |
| `README.md` | Human quickstart and project status | Keep aligned with the real scaffold and CI |
| `Cargo.toml` / `Cargo.lock` | Rust workspace root | Add crates deliberately; commit lockfile for reproducible CI |
| `rust-toolchain.toml` | Rust toolchain pin | Stack changes require ADR |
| `.github/workflows/ci.yml` | Rust and simulator CI | Least privilege; no secrets in normal CI |
| `.github/workflows/codex-review.yml` | Optional read-only Codex PR review | Must remain secret-gated and operator-trigger constrained |
| `.github/workflows/claude.yml` | Optional Claude issue/PR assistant | Must remain operator-trigger constrained; no auto-merge |
| `.github/workflows/sim-dispatch.yml` | Manual simulator dispatch | Telegram/Hermes may dispatch only; no deployment |
| `.github/workflows/ai-research-watch.yml` | Read-only research, security and infrastructure observer plus contract tests | Immutable action pins, `contents: read`, no secrets, dispatch, deployment or merge |
| `.github/pull_request_template.md` | Required PR checklist | Must include validation, docs, anti-dup, cross-review, and security sections |
| `.github/codex/prompts/review.md` | Codex review rubric | P0/P1 findings only; include cross-review and anti-dup checks |
| `crates/proto/` | Wire types, receipts, canonical encoding | Postcard only; deterministic bytes; no chain-specific logic |
| `crates/settle-core/` | Chain-neutral settlement trait/types | No custody, no floats for money, no chain priority |
| `config/ai/research_sources.json` | Reviewed source allowlist, scoring metadata and advisory recommendation rules | Configuration only; never grants runtime authority |
| `docs/adr/` | Accepted/proposed architecture decisions | One decision per ADR; update when stack/track decisions change |
| `docs/modeling/` | Pre-decision modeling plans and outputs | Use before token/L1/bridge/GPU payout decisions |
| `docs/sprints/` | Sprint plans, validation snapshots, handoffs | Record what was tested and what remains blocked |
| `docs/research/` | Extracted/raw research inputs | Reference only; do not treat as accepted architecture |
| `docs/reference/` | External integration notes | Keep separate from accepted decisions |
| `docs/ai/` | Agent workflow, repo map, anti-dup rules, dated console orientation | Must be kept current for all AI agents; handoffs do not become architecture authority |
| `docs/ai/AI_MANAGER_SELF_IMPROVEMENT_IMPLEMENTATION_BACKLOG_2026_07_19.md` | PR-sized self-improvement milestones for sandbox reproduction, scheduler/protocol simulation, draft proposals, canary and rollback | Planning only; no protocol, node, signing, settlement, payout, deploy or merge authority |
| `sim/` | Python DePIN network simulator | Dependency list in `sim/requirements.txt`; outputs not written to source paths |
| `sim_outputs/` | Checked-in baseline simulator outputs | Small reference outputs only; large generated runs go to artifacts/docs |
| `scripts/` | Local helper scripts, including the read-only `ai_research_watch/` package | Must be deterministic and safe; no secrets or production side effects |
| `tests/test_ai_research_watch.py` | Research-watcher parser, state, scoring and safety contracts | Standard-library tests; fail closed on schema and authority drift |

## Planned crate map

These are not production commitments until added by PR and ADR where needed:

| Planned path | Purpose | Depends on |
|---|---|---|
| `crates/executor-wasm/` | Wasmtime/WASI deterministic executor | `proto` |
| `crates/verify/` | Receipt verification, committees, redundant compare | `proto` |
| `crates/receipts/` | Receipt DAG/storage | `proto`, `verify` |
| `crates/identity/` | Ed25519 keys and node IDs | `proto` |
| `crates/transport/` | iroh endpoint and connection handling | `identity`, `proto` |
| `crates/gossip/` | iroh-gossip topics and job propagation | `transport`, `proto` |
| `crates/capability/` | CPU/GPU capability reporting | `proto` |
| `crates/executor-gpu/` | Isolated GPU worker control plane | `capability`, `proto`, `verify` |
| `crates/settle-evm/` | EVM adapter, Base first by sequence only; BNB/Avalanche reuse this adapter (no separate crate) | `settle-core` |
| `crates/settle-solana/` | Solana settlement adapter | `settle-core` |
| `crates/settle-sui/` | Sui settlement adapter | `settle-core` |
| `crates/settle-polkadot/` | Polkadot/Substrate adapter | `settle-core` |
| `crates/settle-xrpl/` | XRPL settlement adapter | `settle-core` |
| `crates/node/` | Node daemon | transport, gossip, executors, verify |
| `crates/cli/` | Operator CLI | node/client crates |
| `contracts/` | Settlement contracts after adapter specs | `settle-core`, ADR approval |

## Canonical ownership rules

Use the existing owner before creating a new module or document:

- Wire/network/hashable data types: `crates/proto/`
- Chain-neutral settlement abstractions: `crates/settle-core/`
- Chain-specific settlement behavior: `crates/settle-*`
- Deterministic CPU execution: `crates/executor-wasm/`
- GPU execution and GPU+CPU node behavior: `crates/executor-gpu/` and
  `crates/capability/`
- Protocol decisions: `docs/adr/`
- Modeling before decisions: `docs/modeling/`
- Sprint execution and validation notes: `docs/sprints/`
- Raw uploaded research/input material: `docs/research/`
- Seven-hard-problems risk/solution register + P0-P5 phase mapping:
  `docs/research/seven_problems_solutions.md`
- Dated 2026-07-16 audit/product research entry point:
  `docs/ai/CONSOLE_HANDOFF_AUDIT_AND_PRODUCT_STRATEGY_2026_07_16.md`
- AI operating rules and maps: `docs/ai/`
- Runnable read-only research-watcher handoff:
  `docs/ai/AI_RESEARCH_NEWS_WATCHER_2026_07_19.md`
- Post-watcher self-improvement implementation backlog:
  `docs/ai/AI_MANAGER_SELF_IMPROVEMENT_IMPLEMENTATION_BACKLOG_2026_07_19.md`

If an owner exists, extend it or reference it. Do not create a parallel `v2`,
`new`, `final`, or agent-specific copy.

## Anti-duplication checklist

Every PR that adds or moves files must include evidence that the agent checked
for duplication:

- Search existing docs and code with `rg` before creating a file.
- Reuse the canonical owner above when it exists.
- Do not define a second enum/model/type for the same concept.
- Do not fork a second scoring, settlement, verification, or routing model
  without an ADR explaining why convergence is impossible.
- If a file is added, update this repo map when the file creates a new area or
  ownership boundary.
- If a doc repeats existing content, replace the repetition with a link and a
  short delta.

## Cross-review rule

**Canonical owner: `AGENTS.md` §3.** Summary for orientation: every substantive PR
must be reviewed by another AI before it is merged — merged by the operator, or by
an agent on an explicit per-PR operator instruction (`SECURITY.md` §1). Settlement,
crypto, verification, workflow-permission, token, bridge, L1/L2, and GPU-payout
changes require explicit cross-review plus human review; the author may not approve
their own substantive work, and disagreements are recorded in the PR with both
positions and a human decision.

Pure documentation typo fixes may skip a full second-agent review, but
documentation that changes architecture, workflow, security, or the repo map is
substantive.

## Documentation requirements

Canonical owner of the general PR-documentation rule is `AGENTS.md` §3.1; the
repo-map-specific triggers below are what an agent must keep current here:

- Update public Rust docs for public API changes.
- Add or update an ADR for architecture or stack decisions.
- Add or update sprint notes for validation results, blocked gates, and
  remaining work.
- Update `docs/modeling/` before decisions involving token economics, own L1,
  bridge routing, GPU payout, or multi-network settlement.
- Update `docs/ai/REPO_MAP.md` when navigation, ownership, or repo layout
  changes.
- PR descriptions must list tests run, docs changed, anti-dup checks, and
  cross-review status.

## Hybrid AI/ML Manager canonical owners (2026-07-19)

- Master direction and console sprint coordination:
  `docs/ai/AI_MANAGER_HYBRID_MASTER_DIRECTION_AND_CONSOLE_SPRINTS_2026_07_18.md`.
- Proposed/default-OFF HDCN adapter-v1 boundary (documentation only; no runtime adapter exists):
  `docs/ai/AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`.
- Proposed Telegram operational boundary (documentation only):
  `docs/reference/hermes_telegram_config.md`.
- Runnable advisory observation slice:
  `docs/ai/AI_RESEARCH_NEWS_WATCHER_2026_07_19.md`, with runtime, configuration
  and workflow authority limited to read-only collection and artifact output.
- Concrete post-watcher implementation order:
  `docs/ai/AI_MANAGER_SELF_IMPROVEMENT_IMPLEMENTATION_BACKLOG_2026_07_19.md`, covering
  deterministic sandbox reproduction, scheduler/protocol simulation, benchmark proposals,
  dependency tests, draft-only PRs, offline/local canary and rollback without authority increase.

These planning handoffs do not override accepted ADRs, HDCN protocol ownership, Sprint 01,
`SECURITY.md`, or the human merge gate. HDCN never inherits a FlowMate trading capability.
