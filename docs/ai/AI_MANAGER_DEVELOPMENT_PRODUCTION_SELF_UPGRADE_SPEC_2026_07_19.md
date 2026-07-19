# HDCN AI Manager: development, production management and stable self-upgrade specification

> **Canonical delta:** this document extends the HDCN Hybrid AI/ML Manager direction and the
> post-watcher self-improvement backlog with an implementation-ready split between repository
> development management, production operations management, and evidence-gated modernization.
> It is subordinate to `AGENTS.md`, `SECURITY.md`, accepted ADRs, `docs/ai/REPO_MAP.md`, the current
> sprint, deterministic protocol/receipt rules and the human merge gate.

**Date:** 2026-07-19  
**Status:** important development milestones and console-programming specification  
**Current reality:** the branch contains a read-only research/security/infrastructure watcher. It
has no HDCN AI Manager runtime adapter, container executor, production node operator, automatic
dependency installer, scheduler learner, signing, settlement, payout, workflow dispatch, deployment
or merge authority.

## 1. Outcome

Build an AI Manager that contributes continuously in two isolated scopes:

1. **Development management** — observe repository, Rust/Python build, CI, dependency, security,
   simulator, documentation and technical-debt evidence; reproduce failures in isolation; benchmark
   candidate changes; prepare exact reviewed proposals and, under a separate repository grant,
   tested draft pull requests.
2. **Production management** — observe scheduler, queue, worker, node-pool, receipt, verifier,
   capacity, resource, network, storage, cost and economic-risk health; explain incidents; recommend
   deterministic runbooks; later invoke only exact pre-approved non-consensus runbooks with readback.

A shared **technology radar** continuously finds relevant AI/ML, distributed-systems, Rust, WASM,
P2P, verification, security and operations developments. The Manager does not install the newest
version merely because it is new. A candidate must be stable, reproduced, compatible, secure,
resource-bounded, supportable and demonstrably better against HDCN-specific baselines.

```text
observe research + repository + production evidence
-> assess relevance and maturity
-> reproduce in deterministic simulation/sandbox
-> compare frozen baseline and candidate
-> security/license/protocol/compatibility review
-> prepare exact code, workload or policy proposal
-> independent AI and human review
-> draft PR or offline shadow
-> separately approved local canary
-> adopt, reject or roll back from immutable receipts
```

The AI Manager remains a supervision plane. It is not a second scheduler, verifier, protocol,
settlement system, node daemon or consensus authority.

## 2. One control plane, role-scoped instances

Do not create a competing manager. Extend the planned provider-neutral manager through distinct
immutable roles, each with exact project/environment/repository/component scope, policy, budget,
TTL and idempotency domain.

| Role | Main purpose | Initial authority ceiling |
|---|---|---|
| `development_observer` | Repo, CI, tests, dependency, security, documentation and tech-debt evidence | Read only |
| `development_planner` | Reproduction, patch, test, ADR/sprint and migration proposal | Advice only |
| `development_sandbox` | Exact allowlisted commands in an isolated simulator/worktree | Sandbox only |
| `development_draft_broker` | Commit/open an exact draft PR after a repository write grant | Draft GitHub write only |
| `production_observer` | Scheduler/queue/worker/node/receipt/resource/cost health | Read only |
| `production_advisor` | Incident, capacity, rollback, quarantine and runbook advice | Advice only |
| `production_runbook_broker` | Invoke one registered non-consensus/non-financial runbook after approval | Separately authorized |
| `technology_radar` | Track stable releases, research, CVEs and maintenance signals | Read only |
| `upgrade_evaluator` | Reproduce and compare candidate versus active baseline | Sandbox/shadow only |

A development grant cannot dispatch production compute or touch nodes. A production-management
grant cannot write source, approve an ADR, mutate consensus rules or open a PR. Consensus among
models never creates permission.

## 3. Definitions of self-improvement

### 3.1 Allowed

- improve diagnosis, tests, observability, documentation, runbooks and simulations;
- propose dependency, toolchain, provider, model, prompt, evaluator or infrastructure upgrades;
- create immutable challenger revisions;
- reproduce research methods against fixed HDCN scenarios and golden fixtures;
- benchmark correctness, determinism, resource use, latency, cost, resilience and security;
- prepare a draft PR after exact approval;
- move a reviewed scheduler/model/supporting-service candidate through offline shadow and local
  deterministic canary stages;
- roll back to a previously approved immutable revision.

### 3.2 Prohibited

The Manager may not:

- overwrite its active evaluator, policy kernel, receipt verifier, approval logic, audit ledger or
  kill switch;
- approve its own proposal or ADR;
- hide negative simulation, invariant, security or production results;
- install dependencies, change a provider/model/prompt, alter production configuration or restart a
  node without a separate exact grant;
- merge, deploy, administer workflows, publish packages or widen permissions through draft-PR
  authority;
- change protocol, scheduler, verification, receipt, settlement, token, payout or economic rules
  because a paper, release or model recommends it;
- sign, settle, dispatch production work, access treasury or handle keys;
- convert logs, work payloads, GitHub text, provider output or retrieved pages into commands.

## 4. Technology radar: newest stable, not newest available

### 4.1 Sources

Prefer primary sources:

- official Rust/toolchain/crate releases and changelogs;
- official Wasmtime/WASI, iroh, libp2p, Tokio, Postcard and relevant runtime releases;
- RustSec, GitHub security advisories, CVEs and supply-chain alerts;
- official protocol/package/model/provider documentation and deprecation notices;
- arXiv/OpenAlex/Hugging Face/GitHub for research discovery;
- reproducible distributed-systems, verification, scheduling and economic-model benchmarks;
- HDCN CI, simulator, worker, receipt, capacity, resource, cost and incident evidence.

International and multilingual discovery is useful, but an implementation decision must cite the
original technical source or a reproducible artifact. Stars, social hype, token price, vendor claims
and unreproduced benchmark screenshots are insufficient.

### 4.2 Maturity states

```text
WATCHED
-> SCREENED
-> REPRODUCTION_APPROVED
-> REPRODUCED
-> BENCHMARKED
-> SECURITY_REVIEWED
-> PROTOCOL_COMPATIBILITY_VERIFIED
-> DETERMINISM_VERIFIED
-> SHADOW_READY
-> LOCAL_CANARY_READY
-> ADOPTED
```

Corrective states:

```text
REJECTED
DEFERRED
SUPERSEDED
QUARANTINED
ROLLED_BACK
REVOKED
```

### 4.3 Default stability windows

| Risk tier | Examples | Minimum evidence before canary consideration |
|---|---|---|
| Low | Docs generator, dev-only report, lint/test utility | Official stable release plus 7-day observation and green isolated tests |
| Medium | Non-authoritative model, simulator helper, observability library, provider adapter | Official stable release plus 14-day observation, compatibility benchmark and shadow |
| High | Runtime, networking, storage, scheduler support, receipt/verification dependency, production supervisor | 30-day observation or LTS evidence, independent security review, failure injection and local canary |
| Critical | Consensus/protocol, identity/keys, settlement, payout, production dispatch, receipt authority | No automatic adoption; accepted ADR, exact human review, protocol conformance, independent security review and separately authorized canary |

Pre-release/nightly/unpinned commits are research-only by default. The Manager may prefer an older
LTS or pinned known-good release. Security emergencies may shorten an observation window only through
a documented emergency process with rollback and human approval.

### 4.4 Candidate evidence

- exact upstream project, version, commit/tag and release channel;
- release date, changelog, migration/deprecation and support horizon;
- license and HDCN compatibility;
- CVE/RustSec/supply-chain provenance;
- exact Cargo/Python lockfile, toolchain and image digest;
- exact HDCN base commit, simulator/evaluator/policy hash;
- golden-vector and cross-language conformance results;
- deterministic/stochastic declaration, scenario seeds and run count;
- correctness, invariant, resource, latency, capacity, reliability and cost comparison;
- protocol/ADR/sprint impact;
- rollback target and rollback procedure;
- independent reviewer evidence for medium/high/critical changes.

## 5. Strict contracts

Shared core contracts remain pinned external owners. HDCN adds only domain extensions and must not
fork duplicate receipt, scheduler, verification, scoring or routing types.

```text
HdcnManagerRoleProfileV1
HdcnTechnologyCandidateV1
HdcnTechnologyMaturityAssessmentV1
HdcnUpgradeEvaluationSpecV1
HdcnUpgradeBenchmarkReceiptV1
HdcnProtocolCompatibilityAssessmentV1
HdcnSecurityLicenseAssessmentV1
HdcnDevelopmentChangeProposalV1
HdcnProductionChangeProposalV1
HdcnProductionRunbookIntentV1
HdcnManagerRevisionV1
HdcnDeploymentRevisionV1
HdcnRollbackReceiptV1
HdcnProductionHealthSnapshotV1
HdcnProductionIncidentObservationV1
HdcnEngineeringManagementObservationV1
```

Every authority-bearing object binds:

- `project_id=hdcn`, environment, repository and exact commit;
- immutable role identity, component/node-pool/workload scope, policy hash, TTL and nonce;
- exact provider/model/prompt/tool/evaluator/simulator/image/toolchain hashes;
- exact candidate and active baseline revision;
- scenario, seed, duration, run count and workload distribution;
- protocol/package versions and golden-vector hashes;
- resource/action/iteration/request/cost ceilings;
- immutable evidence/output artifact refs;
- approval/ADR/sprint evidence when authority increases;
- readback and rollback requirements.

Unknown/duplicate fields, floats in authority/consensus/money paths, bool-as-int, noncanonical time,
secret-like fields, path traversal, symlink/hardlink, stale evidence, hash mutation, wrong project/
environment/component and cross-role grants fail closed.

## 6. Development-management loop

### 6.1 Evidence observed

- Rust/Python build, test, format, clippy, lint and type failures;
- workflow, dependency, configuration and external API errors;
- RustSec/CVE/deprecation/unsupported toolchain evidence;
- simulator regressions, nondeterminism and scenario coverage gaps;
- receipt/manifest/proto/golden-vector incompatibility;
- architecture/ADR/sprint/repo-map drift and duplicate owners;
- PR size, WIP, review latency, change-failure rate and recurring incidents;
- resource/cost/performance regressions;
- relevant research-watcher recommendations.

### 6.2 Workflow

```text
observe
-> classify and deduplicate
-> exact reproduction/simulation plan
-> isolated pinned worktree/container/simulator
-> smallest reviewable change
-> Rust/Python tests, format, clippy, lint, security and conformance
-> proposal bundle + ADR/sprint delta + rollback
-> independent AI and human review
-> optional draft PR through a separate repository grant
```

Proposal bundle:

```text
problem + evidence
exact baseline/candidate revisions
canonical owner and anti-dup result
changed-file allowlist
minimal diff plan
commands/tests/negative tests/golden vectors
security/license/protocol compatibility
resource/cost/performance comparison
ADR/sprint/migration/rollback
known limitations
```

### 6.3 Engineering/self-management metrics

- active WIP and cross-review latency;
- Rust/Python CI duration, retry and flaky-test rate;
- RustSec/dependency backlog age;
- simulator duration, resource use and capacity;
- threat-model/security issue age;
- duplicate owner proposals and repo-map drift;
- recurring incident fingerprints and MTTR;
- protocol/ADR/sprint evidence freshness;
- research recommendation age and disposition.

These metrics may create advice or a draft issue. They cannot rewrite `AGENTS.md`, `SECURITY.md`,
branch protection, accepted ADRs, protocol rules or human review requirements.

## 7. Production-management loop

### 7.1 Initial observation scope

- scheduler, queue, lease, retry, worker and node-pool health;
- capability reports, CPU/GPU/RAM/storage/network and cost;
- workload admission, saturation, starvation and latency;
- manifest, receipt, verifier, freshness, replay and reconciliation evidence;
- node/provider divergence, stream gaps and API health;
- simulator reserve/spiral and economic-risk indicators;
- model/anomaly/evaluation freshness and drift;
- backup/restore, storage pressure and incident SLO;
- offline shadow/local canary state and rollback conditions;
- dependency/runtime/protocol deprecations and security advisories.

### 7.2 Authority stages

| Stage | Allowed behavior |
|---|---|
| P0 Observe | Health snapshots, alerts, reports and incident deduplication |
| P1 Advise | Exact quarantine, rollback, capacity or runbook recommendation; no effect |
| P2 Approved runbook | Invoke one pre-registered, hashed, non-consensus/non-financial runbook after approval and readback |
| P3 Local canary manager | Start/stop a separately approved simulator/local worker canary with exact limits |
| P4 Bounded node-pool broker | Only after accepted ADR, protocol/receipt verification and separate security review |

Possible later P2 runbooks:

- stop a bounded research/simulation job;
- restart an allowlisted non-consensus observer/worker service;
- quarantine a stale or unhealthy research worker;
- restore a known-good model/scheduler-support revision in local/offline scope;
- pause a local canary;
- switch to a pre-approved backup observation provider profile.

Not allowed:

```text
arbitrary shell
source edit
key/credential rotation
node identity mutation
production compute dispatch
protocol/consensus mutation
signing
settlement/payout/treasury
workflow administration
```

### 7.3 Production state machine

```text
PROPOSED
-> SIMULATED
-> VERIFIED
-> OFFLINE_SHADOW
-> LOCAL_CANARY_APPROVED
-> LOCAL_CANARY_ACTIVE
-> PROMOTED
-> MONITORED
```

Corrective states:

```text
QUARANTINED
PAUSED
ROLLED_BACK
REVOKED
REJECTED
EXPIRED
```

An emergency path may select only a deterministic pre-approved rollback to a known-good revision.
It may not hot-patch a running node with AI-generated code.

## 8. HDCN-specific self-upgrade targets

### Development targets

- provider adapters, prompt/tool schemas and evaluation harnesses;
- research watcher source/scoring;
- manager domain contracts, receipts, quotas and sandbox workers;
- simulator, scenario, scheduler/economic modeling and golden vectors;
- Rust/Python/Actions/toolchain/dependency benchmark;
- observability, incident, capacity and cost tooling;
- docs, ADR, sprint, threat model and repo map.

### Production targets

- non-authoritative anomaly/model revision;
- capacity/queue/receipt/data-quality monitor;
- observation provider/fallback profile;
- simulator/local-worker resource quotas and job presets;
- offline shadow/local canary policy;
- deterministic non-consensus runbook catalog;
- quarantine/pause/rollback revision.

### Never self-upgraded without critical approval

- protocol/consensus/wire/receipt authority;
- identity, keys, signing or node credentials;
- settlement, payout, token, treasury or economic rules;
- production compute dispatch and node-pool authority;
- verifier/consensus thresholds;
- workflow permissions, merge rules and kill switches.

## 9. Console milestones

These extend the `H-SI-*` backlog; they do not replace it.

| ID | Deliverable | Authority ceiling |
|---|---|---|
| H-DP-01 | Strict role/candidate/revision/health/upgrade domain contracts + in-memory fakes | None |
| H-DP-02 | Technology-radar maturity classifier and stable-release policy tests | Read only |
| H-DP-03 | Development observer/advisor for repo/CI/dependency/security/simulator evidence | Advice only |
| H-DP-04 | Production observer/advisor for scheduler/worker/receipt/resource/cost health | Advice only |
| H-DP-05 | Deterministic upgrade evaluator with frozen baseline/candidate receipts | Sandbox only |
| H-DP-06 | Security/license/protocol/golden-vector/compatibility gate | Proposal only |
| H-DP-07 | Exact draft-PR broker behind a separate repository write grant | Draft GitHub write only |
| H-DP-08 | Offline shadow/local canary/revision/rollback state machine | Separately approved local scope |
| H-DP-09 | Pre-registered non-consensus production runbook broker with readback | Non-consensus runbooks only |
| H-DP-10 | Reassess bounded node-pool management only after accepted ADR and protocol verification | Separately authorized critical scope |

Suggested placement after anti-dup review:

```text
scripts/ai_self_improvement/upgrade_contracts.py
scripts/ai_self_improvement/technology_radar/
scripts/ai_self_improvement/development_manager/
scripts/ai_self_improvement/production_manager/
scripts/ai_self_improvement/upgrade_evaluator/
config/ai/upgrade.policy.json
config/ai/production-management.policy.json
tests/test_ai_self_improvement_upgrade_*.py
tests/test_ai_production_manager_*.py
```

A future Rust runtime adapter requires an ADR and must reuse `crates/proto` canonical wire/receipt
owners. The first implementation remains Python/in-memory/mock-first.

## 10. Mandatory tests

### Authority and protocol boundaries

- wrong project/environment/role/component/node-pool/repository hash rejected;
- development grant cannot invoke production runbooks;
- production grant cannot edit source or open a PR;
- draft PR does not imply merge/deploy/dispatch;
- self-approval and active-evaluator mutation rejected;
- stale/revoked/replayed approval rejected;
- FlowMate/NOVA grants cannot deserialize as HDCN capabilities;
- provider/model consensus never creates authority.

### Stable-upgrade policy

- prerelease/nightly/unpinned commit research-only;
- newer version loses to older LTS when evidence is weaker;
- missing changelog/license/RustSec/CVE/provenance/golden-vector/rollback evidence blocks;
- risk-tier-specific soak/canary requirements enforced;
- abandoned/unsupported dependency quarantined;
- protocol/toolchain upgrade requires deterministic and cross-language conformance.

### Sandbox/supply chain

- rootless/no privileged/no Docker socket, network OFF default;
- exact image/toolchain/Cargo/Python lock digest;
- path/symlink/hardlink/FIFO/device attack rejected;
- timeout/quota/TERM->KILL->reap/orphan detection;
- no keys, protected workloads, private payloads or production state available;
- SBOM/license/security artifact hash-bound;
- deterministic seed/config/scenario receipt verified.

### Production management

- stale receipt/freshness/provider evidence fails closed;
- provider outage never widens authority;
- logs/work payloads cannot become commands;
- runbook intent matches exact unit/action/revision/TTL/approval/readback;
- resource/cost/SLO/security/kill-switch trip blocks promotion;
- emergency can only restore a known-good immutable revision;
- no production-management path signs, settles, pays, dispatches production compute or mutates protocol.

## 11. Copy-ready console implementation brief

```text
You are implementing the next HDCN AI Manager development/production-management slice.

Start from the latest remote head of draft PR #11 and record exact base/head SHA. Read AGENTS.md,
the nearest nested rules, SECURITY.md, docs/ai/REPO_MAP.md, current sprint, accepted ADRs, the Hybrid
AI/ML Manager direction, the watcher handoff, the self-improvement backlog and this specification.
Abort on a dirty tree, unknown concurrent edits or duplicate canonical owners.

Mission for the first PR: implement H-DP-01 only.

1. Add or extend strict HDCN domain contracts for immutable manager roles, technology candidates,
   maturity assessments, upgrade evaluation specs/receipts, production health/incidents, manager
   revisions and rollback receipts.
2. Reuse pinned shared provider-neutral contract semantics and existing HDCN proto/receipt owners;
   do not fork duplicate protocol types.
3. Add exact-field canonical JSON/in-memory fake adapters only. No runtime provider, node or network.
4. Enforce project/environment/role/component/node-pool separation, protocol/toolchain hashes,
   expiry, nonce/idempotency, resource/cost ceilings, approval/ADR evidence and readback.
5. Add negative vectors for self-approval, evaluator mutation, prerelease adoption, stale evidence,
   wrong role/project/environment, replay, path attacks, cross-project grants and golden-vector drift.
6. Do not connect Docker, MLflow, provider APIs, GitHub write, Telegram, production services, nodes,
   workflow dispatch, signing, settlement, payout, deployment or merge.
7. Update the backlog/repo map/verification handoff with implemented, planned and absent behavior.

Use an isolated stacked branch. Run focused Python tests, Ruff lint/format, compileall, JSON fixtures,
Rust format/clippy/tests for any touched Rust owner, golden-vector checks and git diff --check; run
full CI when feasible. Open a draft PR only. Return exact SHAs, changed files, anti-duplication
result, commands/results, fixture hashes, security limitations, rollback and dependency order.
Never merge, deploy, dispatch production compute, sign, settle or pay.
```

## 12. Completion gate

The program is not complete until:

- development and production role/authority separation is enforced by strict contracts and negative tests;
- technology candidates carry stable-release, provenance, license, security, protocol and rollback evidence;
- upgrades are reproduced against the exact active baseline with deterministic receipts;
- development proposals can reach only a tested draft PR through a separate grant;
- production management starts read-only and can later invoke only exact allowlisted non-consensus runbooks;
- offline shadow/local canary/rollback revisions are immutable and independently approved;
- the active Manager cannot change its own evaluator, policy, grant, verifier or kill switch;
- no path from research, development management, production management or self-upgrade directly reaches protocol mutation, signing, settlement, payout, production dispatch, deployment or merge.
