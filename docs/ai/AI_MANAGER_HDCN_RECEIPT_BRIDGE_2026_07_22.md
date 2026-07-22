# AI Manager ↔ HDCN compute-receipt bridge — design

> **Status:** design input for the HDCN↔FlowMate integration seam. Canonical
> owner: the AI Manager adapter boundary (`docs/ai/AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`
> from PR #10). This document specifies *how* signed HDCN `ComputeReceipt`s
> (produced by the `proto`/`executor-wasm` path) flow into the FlowMate AI
> Manager as read-only `COMPUTE_RECEIPT` observations, without crossing the
> adapter authority ceiling. It is a design/spec input; implementation requires
> a separate code PR on the FlowMate side (the adapter port lives there) and
> Sprint 01+ on the HDCN side (the receipts do not exist yet).

## Purpose and authority

The FlowMate AI Manager already declares a hash-bound `ProjectAdapter` protocol
and a `ProjectDomain.HDCN` enum value (see
`FlowMate_Trading_Assistant/core/ai_manager/adapters.py` and `models.py`). The
`ObservationKind.COMPUTE_RECEIPT` value already exists. The HDCN side already
produces (will produce, post-Sprint 01) signed `proto::ComputeReceipt` values
with BLAKE3 `input_commit`/`output_commit`. This design specifies the bridge
between them: **HDCN receipts become AI Manager observations; the AI Manager
never commands HDCN compute.**

This is consistent with the HDCN adapter-v1 boundary in
`AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`: read/status/plan/sandbox-ingest
only, no workflow dispatch, no signing, no settlement, no deployment, no merge.
The bridge is **one-directional at the data plane** (HDCN → AI Manager) and
**zero-directional at the control plane** (the AI Manager cannot dispatch
HDCN jobs). The relationship is observation, not orchestration.

## Scope

### In scope

- The **data-plane contract**: how a signed `proto::ComputeReceipt` is mapped
  to an AI Manager `Observation(kind=COMPUTE_RECEIPT, domain=HDCN)` with an
  `EvidenceRef` pointing at the canonical receipt bytes.
- The **adapter capability ceiling**: why the HDCN adapter is
  `SideEffectLevel.SANDBOX` (ingest-only), and how the existing
  `CapabilitySnapshot` ceiling check (`max_side_effect > DRAFT_WRITE` rejects)
  enforces "no control-plane authority."
- The **failure and verification model**: what happens when a receipt is
  invalid, unverifiable, or references a missing input bundle.

### Out of scope (deliberately deferred)

- **Control-plane dispatch from the AI Manager to HDCN.** The AI Manager must
  not trigger HDCN job execution. If a future operator decision authorizes
  that, it requires a new capability version, a separate exact-revision human
  approval, a separately configured executor, provider readback, independent
  review, and the HDCN human merge gate (per
  `AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`). **This design does not enable
  it.**
- **Settlement / on-chain claim.** The bridge carries receipts, not payments.
  Settlement remains ADR-0001 (CCTP/USDC, non-custodial).
- **The FlowMate `ProjectAdapter` implementation itself.** That code lives in
  the FlowMate repo; this design is the spec it must conform to. A separate
  FlowMate PR will implement it.
- **GPU receipts.** Until the GPU track (ADR-0002 Track D) ships, only
  deterministic WASM receipts (Sprint 01+) are bridged.

## The data-plane mapping

### Source: HDCN `proto::ComputeReceipt`

From `crates/proto/src/lib.rs`, a signed receipt carries:

```
ComputeReceipt {
    body: ReceiptBody {
        schema_version: u16,            // = 1
        job_id: JobId,                  // BLAKE3 of JobManifest
        worker: NodeId,                 // ed25519 public key
        executor: ExecutorKind,         // CpuWasm | HybridGpuCpu
        input_commit: Hash32,           // BLAKE3 of input bundle
        output_commit: Hash32,          // BLAKE3 of output bundle
        metrics: ExecutionMetrics { fuel_consumed, peak_memory_bytes, billable_units },
        proof: ProofBundle { kind, witness_commit, committee_size, quorum },
    },
    signature: Vec<u8>,                 // ed25519 over signing_payload(body)
}
```

The receipt is postcard-canonical-encodable (`to_canonical_bytes`), and
`receipt_id()` is `BLAKE3(body)` (excluding the signature — see the
`receipt_id_ignores_signature_bytes` test in `proto/src/lib.rs`).

### Target: FlowMate AI Manager `Observation`

From `FlowMate_Trading_Assistant/core/ai_manager/models.py`, the observation:

```
Observation(
    observation_id, project_id, domain=ProjectDomain.HDCN,
    kind=ObservationKind.COMPUTE_RECEIPT,
    source, subject, observed_at, received_at,
    severity=Severity.INFO,
    actionable=False,                   # a receipt is a fact, not a request
    summary,
    metrics={...},                      # fuel, memory, billable, executor
    evidence=(EvidenceRef(...),),       # the canonical receipt bytes
    suggested_job_kind=None,            # NEVER suggest an HDCN job (no dispatch)
    target_component=None,
    tags=("hdcn", "compute-receipt", executor_kind),
)
```

### Field mapping table

| HDCN receipt field | AI Manager observation field | Notes |
|---|---|---|
| `receipt_id()` (BLAKE3 of body, hex) | `observation_id` (prefixed `hdcn_rec_<hex24>`) | The receipt ID is content-addressed; the observation ID reuses it so dedup is automatic. |
| `body.job_id` (hex) | `subject` | "what was computed" |
| `body.worker` (hex) | `source` | "who computed it" (the node's ed25519 key) |
| `body.executor` (`CpuWasm`/`HybridGpuCpu`) | `tags` | executor class as a tag |
| `body.metrics.fuel_consumed` | `metrics["hdcn.fuel_consumed"]` | integer |
| `body.metrics.peak_memory_bytes` | `metrics["hdcn.peak_memory_bytes"]` | integer |
| `body.metrics.billable_units` | `metrics["hdcn.billable_units"]` | integer |
| `body.proof.committee_size` | `metrics["hdcn.proof.committee_size"]` | integer; absent for `DeterministicReplay` solo runs |
| `body.proof.quorum` | `metrics["hdcn.proof.quorum"]` | integer |
| `body.input_commit` (hex) | `metrics["hdcn.input_commit"]` | the input bundle hash |
| `body.output_commit` (hex) | `metrics["hdcn.output_commit"]` | the verified output hash |
| canonical postcard bytes of the receipt | `EvidenceRef(artifact_id="hdcn-receipt", sha256=BLAKE3→sha256-or-hex, media_type="application/vnd.hdcn.receipt.v1+postcard")` | the verifiable artifact |
| wall-clock of bridge ingestion | `observed_at` / `received_at` | UTC, tz-aware (existing `utc_datetime` validator) |
| n/a | `actionable=False`, `suggested_job_kind=None` | **the ceiling: no dispatch** |

### The `EvidenceRef` hash question

The AI Manager `EvidenceRef.sha256` is a SHA-256. HDCN receipts are BLAKE3.
**Do not conflate the two.** The bridge stores the receipt's canonical postcard
bytes as the evidence artifact, and `EvidenceRef.sha256` is the **SHA-256 of
those bytes** (computed by the bridge, not by HDCN). The BLAKE3 receipt ID is
preserved separately in `observation_id` and `metrics["hdcn.output_commit"]`.
This keeps each system's hash discipline intact: HDCN stays BLAKE3-native
(per `AGENTS.md` §2); the AI Manager evidence stays SHA-256-native (per its
existing `require_sha256` validator). The bridge is the only place both hashes
appear together.

## The adapter capability ceiling

The HDCN-side adapter, when registered with the AI Manager, publishes a
`CapabilitySnapshot` with:

```
domain = ProjectDomain.HDCN
max_side_effect = SideEffectLevel.SANDBOX    # ingest + sandbox artifact read; NOT DRAFT_WRITE+ control
operations = ("ingest_receipt", "read_status")  # read-only data plane
supports_idempotency = True                  # receipt_id is content-addressed
supports_readback = True                     # the receipt IS the readback
tool_allowlist = ()                          # no external tools
network_allowlist = ()                       # no outbound from the manager to HDCN
```

This deliberately stays **at or below `SANDBOX`**, well under the
`SideEffectLevel.DRAFT_WRITE` ceiling that the `CapabilitySnapshot.__post_init__`
enforces (`adapters.py` line 91-92: `if self.max_side_effect >
SideEffectLevel.DRAFT_WRITE: raise ValueError("adapter capability exceeds AI
Manager authority ceiling")`). The HDCN adapter therefore **cannot** issue a
`PlanReceipt` or `OperationReceipt` that dispatches compute, signs, settles, or
deploys — those would require `EXTERNAL_WRITE` or `FINANCIAL`, which the ceiling
rejects. This is the architectural enforcement of "observation, not
orchestration."

### Why `SANDBOX` and not `NONE`

`NONE` would mean the adapter contributes no evidence at all. The HDCN adapter
contributes sandbox-ingested artifacts (receipts, input/output bundle hashes)
that the manager reasons over — that is `SANDBOX` (read local sandbox
artifacts), not `NONE`. It is still strictly below `DRAFT_WRITE`, so no plan or
operation it produces can mutate anything outside the sandbox.

## Failure and verification model

### Receipt validation (bridge-side, before observation emission)

Before a receipt becomes an observation, the bridge validates:

1. **Postcard decode.** `proto::from_canonical_bytes(&receipt_bytes)` succeeds;
   the schema version is the expected one.
2. **Signature length.** `ComputeReceipt::new` already enforces
   `ED25519_SIGNATURE_LEN` (64 bytes) — a malformed signature raises
   `ProtoError::InvalidSignatureLength`. The bridge surfaces this as a
   `severity=WARNING` observation with `summary="malformed receipt rejected"`,
   not as an exception.
3. **Signature verification.** **Note:** the current `proto` crate checks
   signature *length* but does not perform strict cryptographic verification
   (per `AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`: "The current
   `ComputeReceipt` checks signature length but does not perform strict
   cryptographic signature verification"). Until that lands, **every bridged
   receipt carries `classification="experimental_unverified"`** in its
   `EvidenceRef`, and the observation's `metrics["hdcn.verification"] =
   "length_only"`. The manager must not treat `experimental_unverified`
   receipts as authorizing payout, settlement, deployment, or correctness —
   consistent with the existing handoff's guard.

### What the bridge does NOT verify

- **Output correctness.** The bridge does not re-execute the job. Correctness
  comes from the HDCN verifier committee (Sprint 03+, ADR-0002 Track A P3
  gate) or from deterministic re-execution by an independent verifier. The
  bridge carries the `output_commit` as a *claim*, verified elsewhere.
- **Input bundle availability.** The bridge records `input_commit` but does
  not fetch the bundle. If the manager needs the bundle (e.g. for a sandbox
  re-execution plan), that is a separate `read_status`-scoped fetch into the
  sandbox, not a bridge concern.

### Failure modes and severities

| Failure | Severity | Action |
|---|---|---|
| Postcard decode failure | `WARNING` | Emit observation with `summary="undecodable receipt"`, no evidence; do not crash the bridge |
| Signature length wrong | `WARNING` | Same; the receipt is dropped |
| Schema version mismatch | `WARNING` | Same; flag for operator review (a version skew between HDCN and the bridge) |
| Signature cryptographically invalid (once verification lands) | `ERROR` | Emit observation; flag as potential adversarial/forged receipt |
| Valid receipt, `experimental_unverified` | `INFO` | Emit observation with the `experimental_unverified` classification |
| Valid receipt, committee-attested (post-P3) | `INFO` | Emit observation with `metrics["hdcn.verification"] = "committee_quorum"` |

## Sequence (end-to-end)

```
HDCN worker (Wasmtime, Sprint 01+)
  → produces proto::ComputeReceipt (signed, postcard-canonical)
  → receipt propagated via iroh-gossip (Sprint 02+) OR pulled by the bridge

FlowMate AI Manager HDCN adapter (bridge)
  → decodes postcard bytes
  → validates (decode, sig length, schema version)
  → constructs Observation(kind=COMPUTE_RECEIPT, domain=HDCN, actionable=False)
  → EvidenceRef points at the canonical bytes (SHA-256), BLAKE3 id preserved
  → submits to the deterministic manager engine

FlowMate AI Manager engine
  → dedups by observation_id (content-addressed receipt id)
  → reasons over metrics (fuel, billable, output_commit) for planning/observability
  → NEVER dispatches an HDCN job (ceiling forbids it)
  → a planning output that would dispatch compute is rejected at PlanReceipt creation
```

## Trust boundary and authority

- **The bridge trusts the HDCN receipt only as far as the receipt's verification
  level allows.** `experimental_unverified` → advisory only; committee-quorum →
  stronger, but still not a payout authorization. Payout/settlement authority
  remains with the on-chain escrow (ADR-0001), never with the AI Manager.
- **The AI Manager's FlowMate live-trading capability has no meaning in HDCN.**
  Per `AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`, a FlowMate trading grant
  cannot authorize an HDCN trade, signing, settlement, payout, treasury,
  workflow-dispatch, production-node, deployment, or merge action. The bridge
  enforces this by staying at `SANDBOX` ceiling — there is no code path from
  the manager to an HDCN external write.
- **Cross-project grant reuse is a blocking security defect.** The
  `ProjectDomain` enum exists precisely so that a FlowMate observation cannot
  be misread as an HDCN authorization and vice versa. The bridge sets
  `domain=ProjectDomain.HDCN` unambiguously.

## Dependencies and sequencing

- **HDCN side:** requires Sprint 01 (`executor-wasm` producing real receipts,
  per `SPRINT_01_DESIGN_FLOWMATE_WASM_PORT.md`). Until receipts exist, the
  bridge has nothing to ingest; it can be built and tested against fixtures.
- **FlowMate side:** the `ProjectAdapter` implementation is a FlowMate-repo PR.
  The `adapters.py`/`models.py` contracts it depends on already exist; no
  FlowMate-side schema change is required for the bridge to be built.
- **Verification upgrade:** when `proto` adds strict Ed25519 verification (a
  future HDCN PR), the bridge flips `experimental_unverified` → verified and
  updates `metrics["hdcn.verification"]`. This is a non-breaking change.

## Open questions / research left

- **Whether the bridge lives in the FlowMate repo or as a shared crate.**
  Initial recommendation: FlowMate repo (the adapter port is FlowMate's; HDCN
  stays agnostic of the AI Manager's existence). A shared crate would create a
  coupling that the current design avoids. Revisit if a third consumer (Nova)
  needs the same mapping.
- **The observation volume ceiling.** If HDCN produces receipts at high
  frequency, the AI Manager observation queue could flood. The bridge should
  batch and/or dedup aggressively (the content-addressed `observation_id`
  makes dedup free). A rate limit is an operational concern, not a design one.
- **Whether Nova `DELIVERY_METRICS` observations follow the same pattern.**
  They likely do (Nova is the third `ProjectDomain`), but that is a separate
  design doc for the Nova side. This design is HDCN-only.
- **Media type registry.** `application/vnd.hdcn.receipt.v1+postcard` is a
  proposed media type; if the bridge ever publishes receipts to an external
  store, register it properly.

## Links

- Implements the data-plane half of: `docs/ai/AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`
  (PR #10) — the read/status/plan/sandbox-ingest boundary.
- Consumes: `crates/proto/src/lib.rs` (`ComputeReceipt`, `ReceiptBody`,
  `ExecutionMetrics`, `ProofBundle`) — once Sprint 01 produces them.
- Depends on contracts in: `FlowMate_Trading_Assistant/core/ai_manager/adapters.py`
  (`ProjectAdapter`, `CapabilitySnapshot`, `OperationReceipt`),
  `core/ai_manager/models.py` (`Observation`, `ObservationKind.COMPUTE_RECEIPT`,
  `ProjectDomain.HDCN`, `SideEffectLevel`, `EvidenceRef`).
- Related: `docs/sprints/SPRINT_01_DESIGN_FLOWMATE_WASM_PORT.md` (the receipts
  this bridge ingests are produced by that Sprint 01 workload).
- Related: `SECURITY.md` §2 (the bridge touches neither keys nor settlement;
  it is a read-only data-plane path, not a §2 catastrophic action).
