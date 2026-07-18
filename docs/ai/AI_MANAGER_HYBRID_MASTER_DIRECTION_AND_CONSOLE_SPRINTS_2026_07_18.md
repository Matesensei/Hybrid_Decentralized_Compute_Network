# HDCN Hybrid AI/ML Manager master direction

> **Canonical planning role:** this document owns HDCN's cross-project AI Manager roadmap.
> It is not an accepted ADR and does not replace `AGENTS.md`, `SECURITY.md`, accepted ADRs,
> `docs/ai/REPO_MAP.md`, or the current deterministic WASM/receipt sprint.

**Date:** 2026-07-18

**Status:** documentation and staged implementation direction

**Current implementation:** no HDCN AI Manager runtime adapter or Telegram gateway; the proposed
adapter-v1 ceiling is default OFF and limited to read/status/plan plus bounded sandbox ingest

## Outcome

HDCN will consume the same provider-neutral Hybrid AI/ML Manager contracts used by FlowMate and
NOVA, but through an HDCN-specific adapter and authority profile. The manager may observe,
diagnose, explain, plan, simulate, and later propose tested patches or bounded compute work. It
does not inherit another project's permissions.

The operator-provided development vision supplies the multi-agent, tool-using, long-term learning,
and failure-recovery direction. HDCN interprets it conservatively:

- self-healing is sanitized incident detection, isolated reproduction, minimal patch proposal,
  tests, independent review, and human-controlled rollout;
- learning is versioned evidence and offline evaluation, not production self-rewriting;
- provider/model output is untrusted advice, not authorization;
- quantum ML remains a research hypothesis and cannot displace the classical deterministic
  baseline without reproducible evidence.

The full cross-repository architecture and complete Claude Code, Codex CLI, and GLM 5.2 prompts
are owned by FlowMate at
`docs/ai_handoff/AI_MANAGER_HYBRID_MASTER_DIRECTION_AND_CONSOLE_SPRINTS_2026_07_18.md`.
Always resolve the latest FlowMate draft PR #406 head before consuming those contracts.

## HDCN roles

The HDCN adapter observes:

- repository, build, CI, dependency, configuration, and external API errors;
- scheduler, queue, worker, node-pool, capacity, CPU/GPU/RAM/storage/network, and cost health;
- manifest, receipt, verifier, nonce/replay, freshness, and reconciliation failures;
- simulator reserve/spiral flags and economic-risk indicators;
- policy, scope, provider, Telegram, and sandbox-broker health.

The AI layer explains and creates typed hypotheses. The ML layer detects drift/anomalies and ranks
bounded candidates. Deterministic policy, receipt verification, resource limits, and accepted
protocol rules remain authoritative.

## Providers and instances

Adapters may be implemented for Codex, Claude, GLM 5.2, Kimi, DeepSeek, and Fable. The operator
supplied `falbe`; confirm the exact vendor/API/model identity before enabling that profile.
Console coding tools and callable runtime model APIs are different capabilities and must not be
treated as interchangeable.

Each provider profile binds exact provider/model/adapter version, planner/critic/shadow role,
prompt/tool-schema hashes, data classification, network/tools, timeout/token/cost caps, typed
output, receipt, region/retention policy, and failover. Provider failure never widens authority.

Multiple manager instances are allowed only when each has a distinct immutable identity,
project/tenant/workspace, adapter, role, scope, budget, TTL, policy hash, and idempotency domain.
Consensus can prioritize review but cannot create permission.

## Scope and non-inheritance

`ScopeGrantV1` binds:

- `project_id=hdcn`, organization/workspace/environment;
- repository and exact commit;
- adapter/provider allowlists and operation kinds;
- node pool, workload, crate/component, resource and budget scope;
- mode, UTC start/end, expiry, action/iteration/cost caps;
- evidence freshness, policy hash, approvers, nonce, and revocation state.

Effective capability is the intersection of global policy, HDCN policy, adapter capability,
provider profile, active scope, current health, and exact operation constraints. Any deny, expiry,
revoke, ambiguity, stale evidence, budget trip, or kill switch wins.

A FlowMate `LiveTradingGrantV1` is invalid in HDCN. Even when FlowMate is configured to let its AI
Manager open or close live positions, that grant cannot authorize HDCN trade execution, signing,
settlement, payout, treasury access, workflow dispatch, production nodes, deployment, or merge.

## Code and API debugging

```text
sanitized error evidence
-> deterministic fingerprint and classification
-> AI reproduction plan
-> isolated pinned reproduction
-> minimal patch proposal
-> Rust/Python tests, lint, security and compatibility gates
-> draft PR
-> independent review and human merge decision
```

Raw headers, tokens, keys, private workloads, protected payloads, and unrestricted stack traces do
not enter prompts, Telegram, or durable evidence. Logs and API responses are untrusted data. The
manager may not hot-patch a node, modify its active evaluator, rotate keys, restart production,
force-push, deploy, merge, or mark its own proposal approved.

## Telegram operator gateway

Initial commands are status and control-plane operations only:

```text
/ai_status
/ai_providers
/ai_scope
/ai_on observe <scope> <ttl>
/ai_on advise <scope> <ttl>
/ai_off [scope]
/ai_alerts
/ai_ack <alert_id>
/ai_explain <decision_id>
/ai_debug <incident_id>
/ai_sim_plan <scenario>
/ai_revoke <grant_id>
/ai_kill <scope>
```

Every state change requires allowlisted user/chat identity, HDCN RBAC, strict command or signed
callback, nonce/update-ID replay protection, expiry, exact object hash, rate limit, immutable
receipt, and readback. Free text is context only. `/ai_off`, `/ai_revoke`, and `/ai_kill` remain
available when all AI providers fail.

The existing `/ship_p0` and `/deploy_testnet` examples are removed from the v1 configuration.
Workflow dispatch or deployment requires a later HDCN capability version, accepted ADR, separate
executor, exact approval, readback, and security review.

## Staged rollout

| Sprint | HDCN deliverable | Authority |
|---|---|---|
| S0 | Threat model, provider/scope/error/Telegram contracts, shared golden-vector plan | None |
| S1 | Sanitized repo/API/worker/receipt observations and deduplicated Telegram alerts | Read only |
| S2 | Mock-first provider router, quotas, receipts, outage and prompt-injection tests | No external write |
| S3 | Sandbox reproduction and deterministic simulation plan/ingest | Sandbox only |
| S4 | Offline anomaly/drift/economic-risk evaluation and challenger reports | Offline only |
| S5 | Tested draft patch/workload proposal through exact approval | Draft proposal only |
| S6 | Reassess a bounded compute executor only after proto verification and accepted ADR | Separately authorized |

HDCN Sprint 01's deterministic WASM/receipt work remains the protocol priority. This manager is a
cross-cutting supervision plane, not a replacement protocol or duplicate scheduler.

## Console ownership

- Codex: master plan, adapter handoff, repo map, mock-first contract implementation and tests.
- Claude Code: read-only threat model, Telegram/provider/security and authority adversarial review.
- GLM 5.2: Rust/Python canonical golden vectors, mutation/negative fixtures, HDCN modeling and
  cross-language conformance after the FlowMate contract SHA is pinned.

Agents start from the latest draft PR #10 head, create isolated stacked branches, never force-push,
and return exact SHAs, changed files, anti-duplication result, checks, artifact hashes,
limitations, rollback, dependency order, and draft PR links. No agent merges, deploys, dispatches
production compute, uses keys, settles funds, or claims verified receipts without evidence.

## Completion gate

The first HDCN release is complete only when strict, shared contracts can drive tenant/project-
scoped observation, sanitized diagnosis, Telegram status/alerts, and bounded sandbox evidence with
replay/idempotency, resource/cost limits, tamper-evident receipts, failure tests, and no path to
trading, signing, settlement, payout, production dispatch, deployment, or merge.
