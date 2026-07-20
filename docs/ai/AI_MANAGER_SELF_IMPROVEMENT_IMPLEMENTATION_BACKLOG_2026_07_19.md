# HDCN AI Manager self-improvement implementation backlog

> **Canonical role:** PR-sized implementation backlog for research reproduction, protocol/scheduler
> simulation, anomaly learning, draft proposals, canary evaluation and rollback. It is subordinate
> to `AGENTS.md`, `SECURITY.md`, accepted ADRs, `docs/ai/REPO_MAP.md`, the current sprint and
> `AI_MANAGER_HYBRID_MASTER_DIRECTION_AND_CONSOLE_SPRINTS_2026_07_18.md`.

**Date:** 2026-07-19  
**Status:** important development milestones and console-programming specification  
**Current runtime:** read-only research/security/infrastructure watcher; no HDCN AI Manager adapter,
container executor, MLflow service, scheduler learner, protocol mutation, workflow dispatcher,
production node canary, deployment broker, signer, settlement or payout authority.

## 1. Outcome

Build a conservative HDCN self-improvement loop:

```text
observe sanitized evidence
-> form one exact hypothesis
-> reproduce in deterministic simulation/sandbox
-> compare frozen baseline and candidate
-> produce a typed proposal with receipts
-> independent AI and human review
-> optional bounded local canary after an accepted ADR
-> promote or roll back a versioned policy
```

The AI Manager is a supervision plane, not a second protocol, scheduler, verifier, settlement
system or node daemon. Research output, provider text, logs, GitHub content and dependency metadata
are untrusted evidence and never authorization.

HDCN Sprint 01 deterministic WASM/receipt work remains the protocol priority. This backlog must not
block or replace it.

## 2. Canonical owners and anti-duplication

Reuse:

- shared provider/scope/error/evidence/receipt contracts from the pinned FlowMate AI Manager
  contract version;
- HDCN protocol/wire types in `crates/proto/`;
- chain-neutral settlement types in `crates/settle-core/`;
- accepted decisions in `docs/adr/`;
- pre-decision analysis in `docs/modeling/`;
- sprint execution/evidence in `docs/sprints/`;
- simulator owner in `sim/`;
- AI workflow/orientation in `docs/ai/`;
- existing GitHub workflows and human merge gate.

Do not create a second receipt, scheduler, scoring, settlement, verification, queue, protocol or
research-watch system. If a new protocol or stack decision is proposed, it requires an ADR and the
repo's independent cross-review/human approval.

## 3. HDCN-specific strict contracts

The shared core contracts remain external/pinned owners. HDCN should add only domain extensions:

```text
HdcnResearchHypothesisV1
HdcnReproductionSpecV1
HdcnSandboxReceiptV1
HdcnSimulationManifestV1
HdcnSimulationComparisonV1
HdcnSchedulerCandidateV1
HdcnProtocolProposalV1
HdcnDependencyBenchmarkV1
HdcnAnomalyObservationV1
HdcnPromotionDecisionV1
HdcnDeploymentRevisionV1
HdcnRollbackReceiptV1
HdcnManagementObservationV1
```

Every domain object binds:

- `project_id=hdcn`, environment and exact repository commit;
- simulator/runner/image and policy hashes;
- scenario, seed set, duration, run count and workload distribution;
- protocol/package/toolchain version where relevant;
- node-pool/capacity/resource/cost scope;
- immutable input/output artifact references;
- deterministic or explicitly declared stochastic fields;
- UTC time, freshness/expiry, nonce/idempotency domain;
- action/iteration/cost/resource ceilings;
- policy/ADR/sprint reference;
- approver evidence when authority increases.

Unknown/duplicate fields, floats in consensus/money/authority paths, bool-as-int, noncanonical time,
path traversal, secret-like fields, hash mutation, stale evidence and cross-project grants fail
closed.

## 4. Milestone map

| ID | Milestone | First authority ceiling |
|---|---|---|
| H-SI-01 | Deterministic reproduction sandbox | Sandbox only |
| H-SI-02 | Protocol and scheduler simulation arena | Offline simulation only |
| H-SI-03 | Benchmark-gated code/workload proposal | Proposal only |
| H-SI-04 | Experiment lineage backend | Metadata/artifacts only |
| H-SI-05 | Capacity/queue/receipt anomaly and drift challengers | Observe/shadow only |
| H-SI-06 | Dependency/toolchain upgrade benchmark | Draft proposal only |
| H-SI-07 | Automatic draft PR broker | Draft GitHub write only |
| H-SI-08 | Shadow/local-canary promotion state machine | Separately approved |
| H-SI-09 | Rollback-capable scheduler/model deployment | Bounded non-settlement scope |
| H-SI-10 | Engineering/self-management improvement loop | Advice/draft issue only |

## 5. H-SI-01 — automatic research reproduction sandbox

### First implementation

Use the current Python simulator and fixed fixtures before connecting a real node or creating a new
Rust executor.

Preferred placement:

```text
scripts/ai_self_improvement/contracts.py
scripts/ai_self_improvement/reproduction/
config/ai/reproduction.policy.json
tests/test_ai_self_improvement_*.py
```

When deterministic WASM execution exists, a later ADR-reviewed adapter may use it; the first slice
must not preempt `crates/executor-wasm/` ownership.

### Sandbox architecture

```text
reviewed hypothesis
-> immutable HdcnReproductionSpecV1
-> separate rootless worker
-> exact checkout and pinned image/toolchain
-> read-only source and fixture inputs
-> allowlisted simulator/test preset
-> CPU/RAM/process/disk/network/time limits
-> receipt and artifact manifest
```

### Mandatory controls

- no host Docker socket, sudo, key, RPC secret, treasury or signer;
- network OFF by default;
- no production node, chain, settlement or compute dispatch;
- exact Rust/Python versions and dependency lockfiles;
- fixed seeds and canonical output ordering;
- source read-only, output directory empty and owned by the worker;
- bounded stdout/stderr, artifact count/bytes and process count;
- cancellation, timeout, OOM, fork, symlink/hardlink/FIFO and path-escape tests;
- TERM -> KILL -> reap cleanup;
- no dirty-workspace reuse.

### Acceptance

- same deterministic manifest produces the same canonical artifact hashes;
- stochastic simulations declare seed sets and compare distributions, not raw file order;
- all failed runs remain failed/diagnostic, never partially "verified";
- sandbox cannot open a branch, PR, workflow, node connection, settlement or deployment.

## 6. H-SI-02 — HDCN protocol and scheduler simulation arena

### Goal

Evaluate bounded hypotheses before changing the protocol or scheduler.

### Candidate policy families

- workload admission and rejection;
- queue ordering and fairness;
- node selection and capability matching;
- replication/redundancy count;
- verification committee size and sampling policy;
- timeout, retry, backoff and quarantine policy;
- relay/transport failure policy;
- reserve, price, payout and budget hypotheses in simulation only;
- capacity reservation and overload shedding;
- heterogeneous CPU/GPU/network/storage allocation;
- malicious, flaky, slow and colluding node scenarios.

A candidate may tune a simulation policy. It may not change `proto`, verifier, settlement or
production node behavior.

### Scenario matrix

At minimum:

```text
base demand
bursty demand
capacity shortage
network partition/latency
Byzantine/malformed result
receipt replay/duplicate
worker churn
provider outage
storage pressure
cost shock
spam/DDoS pressure
adversarial scheduler gaming
```

Use the canonical base/stress/security simulator scenarios where they exist. Add new scenarios to
the existing owner; do not fork a second simulator.

### Evidence

`HdcnSimulationComparisonV1` records:

- frozen baseline and candidate hashes;
- exact scenario/seed/run manifest;
- fill/completion/latency/fairness/cost/reserve metrics;
- verifier and receipt invariant failures;
- queue starvation and concentration;
- resource saturation and failure recovery;
- worst-case and confidence intervals;
- sensitivity to seeds and workload mix;
- failed run count and reasons.

### Adoption gate

A simulation winner is only an ADR candidate. It must pass:

- invariant and security review;
- canonical Rust/Python conformance where applicable;
- independent cross-review;
- reproducible artifact hashes;
- explicit rollback/migration plan;
- human decision.

## 7. H-SI-03 — benchmark-gated generated patch or workload proposal

Flow:

```text
approved hypothesis
-> frozen baseline
-> minimal patch/policy/workload candidate
-> same pinned reproduction/evaluation manifest
-> Rust/Python/CI/security/compatibility gates
-> HdcnSimulationComparisonV1
-> HdcnProtocolProposalV1 or tested patch proposal
```

Mandatory code checks:

- `cargo fmt --check`;
- `cargo clippy --workspace --all-targets --all-features -- -D warnings`;
- `cargo test --workspace --all-features`;
- `cargo deny check` and `cargo audit` when available;
- Python compile/tests and simulator smoke;
- postcard/golden-vector round trips;
- determinism, no-panic, no-float money/consensus checks;
- anti-duplication and repo-map impact;
- permission/secret/workflow diff;
- performance/resource comparison;
- rollback/migration.

A benchmark creates a proposal only. It cannot apply protocol state, start a node, dispatch compute,
choose settlement, change payout or promote itself.

## 8. H-SI-04 — experiment lineage backend

MLflow or another backend may be evaluated for Python simulation/ML experiment tracking. It must
not become the HDCN protocol registry or architecture authority.

Ownership:

```text
ADRs                 accepted architecture/protocol decisions
docs/modeling        pre-decision evidence and hypotheses
docs/sprints         execution and validation status
optional backend     run metrics/artifacts/lineage only
AI Manager           links evidence and proposes review
```

Preferred split:

```text
scripts/ai_self_improvement/experiment_contracts.py
scripts/integrations/mlflow_adapter.py
```

Use an in-memory fake in tests. The external client remains optional and outside Rust core.

Required lineage:

- exact code/toolchain/image;
- scenario/seed/workload/config;
- parent hypothesis/search;
- artifact checksums;
- metric definitions;
- policy/ADR/sprint reference;
- retention/classification;
- candidate stage and review evidence.

No `production` alias may authorize protocol or node behavior.

## 9. H-SI-05 — anomaly and drift challengers

### Safe use cases

- worker capacity and resource anomaly;
- queue latency/starvation/drift;
- completion/failure/retry pattern;
- receipt/manifest/freshness/reconciliation anomaly;
- node-pool concentration and churn;
- network/storage/cost change;
- simulator reserve/spiral-risk trend;
- CI/build/dependency health.

### Architecture

```text
sanitized metric stream
-> strict point-in-time feature schema
-> online detector/challenger
-> immutable snapshots
-> shadow score and DriftObservationV1
-> operator/retraining/simulation recommendation
```

The detector may use River-like algorithms in the Python supervision plane. It must not participate
in consensus, receipt verification or deterministic scheduler hot paths.

Forbidden:

- no automatic protocol/scheduler/payout/settlement mutation;
- no training on protected workload payloads;
- no model output as verifier truth;
- no drift-triggered promotion;
- no cross-project data or authority inheritance.

## 10. H-SI-06 — dependency and toolchain upgrade benchmark

Flow:

```text
RustSec/Dependabot/watcher/toolchain candidate
-> isolated Cargo/Python/Action update
-> transitive/license/security diff
-> full tests/golden vectors/simulator benchmark
-> performance/resource/compatibility report
-> rollback verification
-> draft proposal
```

Required:

- Rust crates, Python sim dependencies and GitHub Actions separate;
- immutable Action pins preserved;
- no workflow-permission widening or new secret consumer;
- iroh/Wasmtime/postcard/alloy changes checked against accepted stack/ADR;
- wire/golden vector compatibility;
- cargo deny/audit and license review;
- deterministic output and performance comparison;
- old/new lockfile evidence;
- stack decision change becomes ADR proposal, not silent dependency bump.

Security updates do not auto-merge.

## 11. H-SI-07 — automatic draft PR broker

Use a separate broker and fine-grained repository grant. The model/provider never sees credentials.

Grant:

```text
repository and exact base SHA
branch prefix agent/<agent>/<type>-<slug>
path/operation allowlist
max files/lines/bytes/commits
allowed test presets
expiry/nonce/cost/action caps
required cross-review lanes
```

Behavior:

- isolated worktree from exact base;
- one task and draft PR;
- stage only approved proposal files;
- PR body lists tests, docs, anti-dup, security, artifact hashes, limitations, rollback and
  cross-review state;
- remote commit/PR readback;
- stop on moved base, permission change or stale proposal;
- never ready/approve/merge/deploy/dispatch/sign/settle/change workflow/secret.

The proposal author cannot approve the exact same revision.

## 12. H-SI-08 — shadow and local-canary promotion state machine

Canonical states:

```text
OBSERVED
REPRODUCTION_APPROVED
REPRODUCED
BENCHMARKED
INDEPENDENTLY_REVIEWED
OFFLINE_SHADOW
LOCAL_SANDBOX_CANARY_ELIGIBLE
LOCAL_SANDBOX_CANARY_ACTIVE
BOUNDED_NODE_POOL_ELIGIBLE
BOUNDED_NODE_POOL_ACTIVE
PROMOTED
ROLLED_BACK
REVOKED
REJECTED
```

### Stage meaning

- **Offline shadow:** simulator reports only;
- **Local sandbox canary:** deterministic local fixtures/WASM when the canonical executor exists;
- **Bounded node pool:** only after S6, accepted ADR, separate executor/capability, proto/receipt
  verification and security review;
- **Promoted:** explicit human decision and versioned policy;
- **Rollback:** restore known-good policy/config and stop new candidate scheduling.

This backlog does not authorize mainnet/testnet deployment, keys, signing, settlement, payouts,
production dispatch or treasury action.

## 13. H-SI-09 — rollback-capable scheduler/model deployment

First scope: offline simulator policy and local supervision model, not protocol consensus.

`HdcnDeploymentRevisionV1` binds:

- policy/model/artifact digest;
- runtime image/toolchain digest;
- compatible code/protocol range;
- scenario/evidence and approval hash;
- node-pool/environment scope;
- health/readiness/readback contract;
- resource/cost/action limits;
- rollback thresholds;
- previous known-good revision;
- expiry/owner.

Required:

- immutable revisions;
- atomic config/policy switch;
- readiness and semantic readback;
- shadow comparison before candidate traffic/work;
- deterministic kill/disable path independent of AI providers;
- rollback receipt and incident bundle;
- no in-place policy/model overwrite;
- promotion freeze after rollback.

Any stateful work already dispatched requires deterministic reconciliation; rollback must not make
receipts or jobs disappear.

## 14. H-SI-10 — engineering and self-management improvement loop

Observe weekly:

- active PR/worktree/WIP count;
- PR size, review age and cross-review latency;
- CI failure/retry/flaky tests;
- change-failure and rollback rate;
- incident MTTR and recurring fingerprints;
- dependency/RustSec backlog;
- simulator duration, cost and capacity saturation;
- queue/scheduler research backlog age;
- documentation/ADR/repo-map drift;
- duplicated owner proposals;
- security/threat-model issue age.

May recommend:

- smaller PR/WIP limits;
- missing tests, ADRs, runbooks or postmortems;
- dependency/performance work;
- scenario/chaos coverage;
- review-lane or sprint ordering;
- technical-debt reduction.

May not automatically rewrite `AGENTS.md`, `SECURITY.md`, accepted ADRs, branch protection, reviewer
requirements, stack decisions, protocol parameters, payout policy or deployment permissions.

## 15. Console implementation order

### HDCN-SI-01 — strict contracts and fake sandbox

```text
Branch: agent/codex/feat-self-improvement-contracts
Scope:
- section 3 HDCN domain contracts;
- in-memory fake reproduction broker;
- canonical JSON/golden/negative vectors;
- no Docker, MLflow, node, provider or learning library.
```

### HDCN-SI-02 — deterministic reproduction worker

```text
Branch: agent/codex/feat-reproduction-worker
Depends on: HDCN-SI-01
Scope:
- rootless reference worker for simulator/test presets;
- quotas, cancellation, receipts, failure injection;
- no network/default external writes.
```

### HDCN-SI-03 — scheduler simulation comparison

```text
Branch: agent/codex/feat-scheduler-simulation-arena
Scope:
- extend existing sim owner;
- frozen baseline/candidate manifests and adversarial scenarios;
- distribution/worst-case evidence;
- no Rust protocol mutation.
```

### HDCN-SI-04 — experiment lineage adapter

```text
Branch: agent/codex/feat-experiment-lineage
Scope:
- in-memory protocol plus optional Python MLflow adapter;
- ADR/modeling/sprint docs remain authority.
```

### HDCN-SI-05 — anomaly/drift shadow

```text
Branch: agent/codex/feat-anomaly-drift-shadow
Scope:
- one capacity/queue or receipt-health detector;
- snapshots and shadow reports;
- no scheduler/verifier authority.
```

### HDCN-SI-06 — benchmark proposal bundle

```text
Branch: agent/codex/feat-benchmark-proposals
Scope:
- code/simulation/dependency comparison;
- exact tests/docs/anti-dup/security/rollback evidence;
- no GitHub write.
```

### HDCN-SI-07 — draft PR broker

Only after independent security review and a dedicated repository grant. Draft-only; no merge,
deploy, workflow dispatch, signing, settlement or production compute.

### HDCN-SI-08 — promotion/rollback

Offline shadow, local deterministic canary and any bounded node-pool executor are separate PRs and
ADRs. Do not combine them.

## 16. Copy-ready console brief

```text
Implement only the next uncompleted HDCN-SI task from
AI_MANAGER_SELF_IMPROVEMENT_IMPLEMENTATION_BACKLOG_2026_07_19.md.

Resolve the latest remote heads of the HDCN AI Manager/research branches. Read AGENTS.md, the
nearest AGENTS.md, docs/ai/REPO_MAP.md, SECURITY.md, current sprint, relevant ADR/modeling docs,
the AI Manager master direction and watcher handoff. Search for canonical owners and do not create
a second protocol, scheduler, verifier, receipt, settlement, scoring or queue system.

Hard boundaries:
- default OFF/read-only/sandbox;
- no keys, signing, settlement, payout, treasury, mainnet/testnet deploy or production dispatch;
- no arbitrary model-produced shell;
- no provider/GitHub/deployment credentials in the manager or sandbox;
- no protocol or stack decision without an ADR;
- all outputs strict, hash-bound, deterministic or seed-declared, resource-bounded and independently
  reviewable;
- simulation success is not protocol adoption.

Use one isolated branch/worktree and one PR-sized scope. Run Rust/Python focused checks, fmt,
clippy, tests, cargo deny/audit where available, compile/simulator smoke and git diff --check.
Return exact SHAs, changed files, anti-duplication result, commands/results, artifact hashes,
security/authority limitations, rollback, dependency order and a draft PR link. Do not self-approve
or merge.
```

## 17. Completion gate

The first self-improvement release is complete only when it can:

1. reproduce a selected hypothesis from immutable inputs;
2. compare a frozen baseline and candidate fairly;
3. create a typed, tested proposal without applying it;
4. pass independent cross-review and human decision;
5. retain complete run/artifact/ADR/sprint lineage;
6. run only in offline/local shadow before separately authorized bounded canary;
7. restore the exact known-good policy/model and reconcile in-flight work;
8. retain tamper-evident receipts;
9. prove no path from news/model output directly to protocol mutation, node dispatch, signing,
   settlement, payout, deployment or merge.
