# HDCN AI Manager adapter handoff

**Status:** proposed implementation handoff; no HDCN AI Manager runtime adapter is implemented;
not an accepted ADR

**Repository snapshot:** `fb945f62a6cf7fe55915e88e5b87a43ff271811c`

**Documentation line:** introduced through draft PR #10 from base snapshot `fb945f62a6cf7fe55915e88e5b87a43ff271811c`; always resolve and record the current remote PR head before implementation.

## 2026-07-18 hybrid expansion

The next provider-neutral, multi-manager, Telegram, code/API debugging, compute-risk, and offline
AI+ML direction is owned by
`docs/ai/AI_MANAGER_HYBRID_MASTER_DIRECTION_AND_CONSOLE_SPRINTS_2026_07_18.md`.
This handoff remains authoritative for the narrower proposed adapter-v1 boundary.
The future FlowMate live-trading grant is project-specific and cannot authorize any HDCN trade,
signing, settlement, payout, treasury, workflow-dispatch, production-node, deployment, or merge
action.

## Purpose and authority

Specify how a future implementation may connect the reusable FlowMate AI Manager contracts to
HDCN without turning the manager into a deployment, workflow-dispatch, signing, settlement, or
protected-branch agent.

The proposed HDCN adapter v1 would be limited to:

- repository and policy reads;
- CI/workflow status reads;
- deterministic plan generation without dispatch;
- sandbox artifact and receipt ingestion;
- evidence-bound reports for human review.

No current HDCN component exposes this adapter contract. When implemented, adapter v1 must have
`max_side_effect_level = sandbox`. It must not dispatch a workflow, open an issue or pull request,
push a branch, deploy, merge, place a trade, or submit a settlement action. Any later external
write requires a new capability version, a separate exact-revision human approval, a separately
configured executor, provider readback, independent review, and the HDCN human merge gate.

This handoff does not accept `DecisionReceiptV1` as protocol architecture. Any
protocol or control-plane change still requires the normal ADR, anti-duplication
check, cross-review, and human merge gate.

## Existing integration seams

- `AGENTS.md`: Hermes is an optional command-only control plane and holds no keys.
- `SECURITY.md`: no autonomous merge, deployment, treasury, signing-policy, or
  permission changes.
- `.github/workflows/sim-dispatch.yml`: an existing workflow whose definition and
  status may be read, but which adapter v1 must not dispatch.
- `crates/proto/src/lib.rs`: `JobManifest`,
  `WorkloadKind::FlowMateBacktest`, and `ComputeReceipt`.
- `docs/ai/REPO_MAP.md`: canonical ownership and anti-duplication rules.
- `crates/settle-core/`: explicitly outside adapter v1.

The current `ComputeReceipt` checks signature length but does not perform strict
cryptographic signature verification or create an independent acceptance
certificate. Ingested receipt evidence must therefore remain
`experimental_unverified`; it cannot authorize payout, settlement, deployment,
or any correctness claim.

## FlowMate strict canonical profiles

FlowMate defines project-specific strict profiles. This handoff makes no claim
of full RFC 8785/JCS compatibility. An adapter must use the pinned FlowMate
implementation or pass byte-for-byte cross-language golden vectors; a JSON
library's default canonical mode is not a substitute.

### Contract and evidence digests

`core/ai_manager/canonical.py` and `TaskManifestV1` are authoritative for
manifest, plan, evidence, and receipt hashes:

- `json_value()` converts supported dataclasses, enums, paths, mappings,
  sequences, and timezone-aware datetimes;
- mapping keys must be non-empty strings;
- datetimes normalize to UTC ISO-8601 text ending in `Z`;
- naive datetimes, sets, bytes, unsupported objects, NaN, and infinity fail;
- serialization is UTF-8 JSON with `ensure_ascii=False`, `allow_nan=False`,
  compact separators, and recursively sorted keys;
- lowercase SHA-256 covers the exact emitted UTF-8 bytes;
- digest fields require 64-character lowercase SHA-256 values and Git bindings
  require full 40- or 64-character object IDs;
- finite floats are supported in general canonical evidence, but floats are
  forbidden in `TaskManifestV1.acceptance_criteria`; use integer value-plus-
  scale fields there.

### Persisted engine state

`core/ai_manager/state_codec.py` and `persistence.py` define a stricter storage
profile. Decoders require exact field sets, reject unknown or missing fields,
and never coerce booleans, integers, strings, enum values, or identifiers.
Model constructors must revalidate derived IDs and every SHA-chain binding.

The state root has exactly `schema_version`, `policy_version`,
`policy_sha256`, `seen_observation_ids`, `last_sequence`,
`trigger_observations`, `last_work_order_at`, `work_orders`,
`experiment_results`, `proposals`, `decision_ledger_receipts`, and `blocked`.
Generic metric/evidence values use an explicit tagged tree:

- null, bool, int, and string use `kind` plus the exact permitted fields;
- arrays use `{"kind":"array","items":[...]}`;
- objects use `{"kind":"object","entries":[{"key":...,"value":...},...]}`
  with strictly increasing, unique string keys;
- floats use `{"kind":"float","hex":"<float.hex()>"}`; only finite values
  are valid, and decode plus `float.hex()` re-encode must reproduce the exact
  text.

Timestamps must be timezone-aware, canonical UTC `...Z`, and survive exact
decode/re-encode validation. The SQLite payload then contains only JSON null,
bool, int, string, list, and map values; direct floats, duplicate keys, NaN,
infinity, malformed UTF-8/JSON, oversized payloads, policy mismatch, and stale
compare-and-swap revisions fail closed. Storage uses compact sorted UTF-8 JSON,
an exact SHA-256, bounded size, revision-based CAS, and owner-only SQLite/WAL
file permissions. Individual inputs have pre-hash canonical byte, depth, node,
and cycle limits. The current 4 MiB full-state default is a bounded research
profile; 24/7 operation requires segmented retention, anchored rotation, rate
limits, and longevity tests.

Project approval roles and deterministic checks are mandatory minimums for
every research route. A route may add stricter gates but cannot remove a
project gate. Exact/prefix routes that could authorize the same action are
rejected as ambiguous.

## `TaskManifestV1` binding

Every plan and ingested artifact binds the following fields:

- `manifest_id`, derived as `aim_<canonical_sha256[:24]>`;
- `canonical_sha256` over the manifest payload;
- `project_id`, `domain`, `organization_id`, `workspace_id`;
- `repository` and exact `exact_commit_sha`;
- `policy_version` and `policy_sha256`;
- `operation_kind`, `target_component`;
- requested `side_effect_level` and `max_side_effect_level`;
- non-empty `input_evidence` with artifact ID, SHA-256, capture time,
  classification, and optional safe URI;
- `adapter_id`, `adapter_version`;
- `timeout_seconds`, `max_cost_microunits`;
- `hypothesis` and strict `acceptance_criteria`;
- `required_approvals`, `required_ci_checks`;
- `idempotency_key`, `created_at`, `expires_at`;
- optional runner, prompt bundle, model policy, baseline receipt, dataset
  manifest, and split manifest SHA-256 values;
- tool and network allowlists.

Secrets, exchange credentials, wallet material, production RPC data, raw private
strategy data, and personal data are forbidden. Only server-owned, non-secret
evidence references may appear.

## HDCN plan-only projection

Adapter v1 may calculate, record, and display an `HDCNJobProjectionV1`; it must
not submit or dispatch it.

- `manifest_bytes = canonical_json(manifest.payload()).encode("utf-8")`.
- `input_commit = BLAKE3(manifest_bytes)`.
- `nonce = BLAKE3("hdcn.ai-manager.task.v1\0" || idempotency_key)`.
- FlowMate research maps to `WorkloadKind::FlowMateBacktest`.
- Other eligible deterministic research maps to `WasmDeterministic`.
- `max_fuel` comes only from an approved deterministic execution profile.
- The projection records both FlowMate `canonical_sha256` and the HDCN BLAKE3
  commitment.

Do not add generic manager fields directly to `JobManifest` v1. Its field layout
is a wire contract. A future executable mapping requires an accepted proto-v2
ADR, schema bump, bounded decoding, domain separation, nonce/expiry enforcement,
strict Ed25519 verification, replay state, separate `WorkerReceipt` and
`AcceptanceCertificate`, and golden vectors.

## Adapter behavior

Implement `ProjectAdapter` with the following v1 behavior:

- `capability_snapshot()` returns only read/status/plan and sandbox-ingest
  operations, `supports_idempotency=true`, `supports_readback=true`, an empty
  execution network allowlist, and a sandbox authority ceiling.
- `prepare()` validates policy, exact commit, freshness, evidence hashes, tool
  allowlist, and the plan-only HDCN projection, then emits a `PlanReceipt`.
- `execute()` is permitted only for local sandbox artifact ingestion. It never
  invokes GitHub workflow dispatch or any HDCN runtime/settlement endpoint.
- `readback()` re-hashes the stored sandbox artifact and verifies exact manifest,
  plan, adapter, repository, commit, and idempotency bindings.
- HDCN `ComputeReceipt` ingestion always returns `verified=false` at the
  correctness layer until an independent acceptance verifier exists.
- `cancel()` may cancel only an uncommitted local sandbox ingest.

The shared in-process orchestrator validates contracts but is not an operating-
system sandbox. Before execution is enabled, use a separate broker that enforces
filesystem, process, credential, network, time, cost, and resource limits. The
manager durably claims `PENDING -> RUNNING` before the broker starts. A result
requires distinct operation and readback receipts in its hash-bound artifacts.
A `RUNNING` claim is never replayed automatically after restart; durable broker
attempt state, fencing, and receipt reconciliation determine its terminal state.

The manager planner cannot call an external write API. A future write must flow
through `ChangeProposal -> exact manifest/plan approval -> separate executor ->
readback receipt`; an LLM response or client-supplied approval flag is never an
authorization.

## Rollout

1. Add this handoff and, if implementation changes control-plane architecture,
   propose an ADR.
2. Add shared FlowMate/HDCN canonical golden fixtures.
3. Implement read-only capability and repository/status adapters.
4. Add plan-only HDCN job projection with no dispatch code path.
5. Add local sandbox artifact/receipt ingest and immutable evidence.
6. Add explicit `experimental_unverified` reporting for current receipts.
7. Add an out-of-process sandbox broker, durable attempt ledger, leases,
   fencing, and operation/readback reconciliation.
8. Add segmented/anchored retention and long-duration restart tests.
9. Reassess executable work only after proto-v2 verification and a separate
   security-reviewed rollout.

## Required tests

- Python/Rust strict-canonical golden vectors.
- Exact persisted-state root and per-model field-set fixtures; unknown, missing,
  or type-coerced fields fail closed.
- Tagged float-hex round trips, canonical UTC round trips, sorted unique object
  entries, and negative fixtures for non-canonical hex, duplicate keys, NaN,
  infinity, and direct storage floats.
- Persistence corruption, payload-size, policy-binding, and stale-CAS tests.
- Stable SHA-256, BLAKE3 `input_commit`, nonce, and projected job-ID fixtures.
- Any manifest mutation changes all downstream bindings.
- NaN, infinity, naive timestamps, unsupported values, secret-like fields,
  stale evidence, and non-exact commit SHAs fail closed.
- Duplicate exact sandbox ingest is idempotent; key rebinding is rejected.
- Wrong repository, tenant, workspace, commit, policy, plan, or artifact receipt
  is rejected.
- The capability snapshot exposes no workflow-dispatch or external-write tool.
- Static tests prove no adapter-v1 call to workflow dispatch, protected branches,
  settlement, signing, or live trading.
- Tampered artifact and receipt evidence fails readback.
- Current `ComputeReceipt` evidence cannot become verified or settlement-eligible.
- Timeout, cancellation, and partial artifact writes do not create false success.
- A result is rejected before a durable running claim or without distinct,
  artifact-bound operation/readback receipts.
- Restart never auto-replays a running attempt; broker reconciliation and
  fencing prevent duplicate execution.
- Oversized/deep/cyclic single inputs fail before manager mutation; SQLite files
  are owner-only and lagging projections repair only from authoritative state.
- `cargo fmt --check`, Clippy, workspace tests, simulator smoke, and independent
  AI review pass.

## Completion gate

Adapter v1 is complete only when an exact FlowMate manifest can be read, planned,
and reconciled against locally ingested sandbox evidence without any workflow
dispatch, external write, credentials, live trading, settlement, deployment, or
merge authority.
