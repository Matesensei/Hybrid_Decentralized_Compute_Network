# Sprint 01 design: FlowMate backtest → WASM port (deterministic first workload)

> **Status:** design input for Sprint 01, not an accepted implementation plan.
> Canonical owner: Sprint 01 deterministic-WASM execution track (ADR-0002
> Track A). This document specifies *how* to port a slice of the FlowMate
> backtest engine into a Wasmtime-fuel-metered deterministic WASM guest, so that
> the HDCN receipt verification story (`proto::ComputeReceipt`,
> `output_commit` BLAKE3 comparison) has its first real dogfooding workload. It
> is a design/spec input: implementation requires a separate code PR and the
> Sprint 01 acceptance gate (bit-identical `output_commit` across ≥2 machines).

## Purpose and authority

Sprint 00 (bootstrap) is complete. Sprint 01's headline deliverable, per
`SPRINT_00_BOOTSTRAP.md` §"Sprint 01 backlog" and the
`DIRECTION_MODELING_PLAN.md` Track A Sprint-01 gate, is:

> One deterministic WASM task produces the same `output_commit` across at least
> two machines or runners. A local verifier rejects tampered input/output
> commitments.

The recommended first workload is a **FlowMate distributed backtest slice** —
the project's own dogfood. This document specifies the port: which slice, which
crates, which fuel/determinism strategy, and what the acceptance test is. It is
**not** an architecture decision (no ADR needed — the WASM/wasmtime choice is
already in `AGENTS.md` §2 and ADR-0002 Track A); it is an implementation design
that the Sprint 01 code PR will follow.

## Scope — what gets ported (and what does NOT)

### In scope (the "minimal deterministic slice")

Port a **single, self-contained backtest computation** that:

1. Takes a **content-addressed input bundle**: OHLCV bars (CSV or postcard) +
   strategy parameters + a fixed random seed.
2. Produces a **deterministic output**: equity curve + trade log + summary
   metrics, all as canonical postcard bytes (so `blake3::hash(output_bytes)` is
   stable).
3. Runs **bit-identically** across machines when given the same
   `input_commit` + `max_fuel` + WASM module hash.

Concretely: a simple moving-average crossover backtest, or a single
parameter-grid cell of an existing FlowMate strategy. **Not** the full FlowMate
strategy zoo, ML search, or walk-forward framework — those are later, larger
workloads. The goal is to prove the determinism + receipt pipeline end-to-end on
the smallest non-trivial real computation.

### Out of scope (deliberately deferred)

- **The full FlowMate `core/` backtest engine** (`backtest.py`,
  `backtest_realistic/`, DSR/PBO/CPCV validation). Too large for Sprint 01;
  port a slice, not the framework.
- **ML strategy search, walk-forward, Monte Carlo ensembles.** These are
  embarrassingly parallel *collections* of deterministic jobs — they become a
  later workload once a single job is proven deterministic.
- **Live data ingestion, exchange API calls, network I/O from the guest.**
  WASI Preview 2 capability-based security means the guest starts with **zero**
  network/filesystem access; inputs arrive as a pre-loaded bundle.
- **GPU execution.** That is ADR-0002 Track D, a separate later track.
- **Settlement / on-chain escrow.** Sprint 01 is local proof-of-determinism
  only; settlement is Sprint 02+ (ADR-0001).

## Crate layout (Cargo workspace additions)

New crates under `crates/`, following the repo's existing workspace style and
the `hybrid_decentralized_compute_network.md` §"Repo-struktúra" plan:

```
crates/
├── proto/              # existing — receipt types, BLAKE3, postcard
├── settle-core/        # existing — chain-neutral settlement types
├── executor-wasm/      # NEW (Sprint 01) — Wasmtime host driver
└── flowmate-guest/     # NEW (Sprint 01) — the WASM guest (backtest slice)
```

### `crates/executor-wasm/` — the host driver

**Responsibility:** load a WASM module, instantiate it with
fuel-metered deterministic config, feed it the input bundle, collect the output
bytes, and produce a `proto::ComputeReceipt`.

**Concrete crate dependencies (verify latest versions before build — field
moves fast):**

| Dependency | Version (mid-2026 reference) | Role |
|---|---|---|
| `wasmtime` | 22.x–26.x (use latest stable; verify) | The runtime. Pull in `cranelift`, `cache`, `runtime`, `component-runtime`, `gc-cranelift`, `gc-drc` features as needed. |
| `wasmtime-wasi` | matching version | WASI Preview 2 host implementation, if any WASI imports are used (start with none — pure compute, no I/O). |
| `blake3` | 1.5.x | Already used by `proto`; hash the input bundle and output bytes. |
| `postcard` | 1.x | Already used by `proto`; canonical output encoding. |
| `thiserror` | 1.x / 2.x | Error type (no panics in library paths — `AGENTS.md` §"no_std where feasible"). |
| `serde` | 1.x | For any host-side config structs. |

**Key APIs:**

- `Engine::config()` with **`strategy(Cranelift)`**, **`consume_fuel(true)`**,
  **`cranelift_nan_canonicalization(true)`** (the single most important flag for
  cross-machine determinism — canonicalizes NaN payloads), and
  **`cache_config` disabled or pinned** (a cached compilation can break
  determinism if it leaks host-specific artifacts — start with cache OFF for
  the receipt path, investigate later).
- `Store::set_fuel(max_fuel)` — bounds execution; a job that exceeds `max_fuel`
  traps, and the receipt records the fuel consumed.
- `Linker` with **no WASI imports by default** (the guest is pure compute). If
  a clock or filesystem is ever needed, use `wasi-virt` to virtualize them so
  the guest sees deterministic values, not host wall-clock.

### `crates/flowmate-guest/` — the WASM guest

**Responsibility:** a `cdylib`/`wasm32-wasip2` target that exports a single
function (e.g. `run_backtest(input_ptr, input_len) -> (output_ptr, output_len)`)
implementing the backtest slice in pure Rust, compiled to WASM.

**Key points:**

- Target `wasm32-wasip2` (WASI Preview 2; Wasm 3.0 was ratified September 2025,
  Preview 2 is stable — per `hybrid_decentralized_compute_network.md`).
- **No `std::time`, no `std::fs`, no randomness, no `HashMap` iteration in the
  compute path.** Use `BTreeMap`/sorted structures for deterministic ordering.
  This is the Sprint 01 determinism checklist (`AGENTS.md` §"no_std where
  feasible"; `DIRECTION_MODELING_PLAN.md` core KPIs: "no wall-clock/RNG/HashMap
  iteration in verify/consensus").
- **Fixed-point or integer arithmetic for money.** The existing
  `settle-core` `Amount`/`u128` pattern is the model; do not introduce `f64`
  in the equity curve if it can be avoided. Where `f64` is unavoidable (e.g.
  indicator math), enable `cranelift_nan_canonicalization` AND pin a specific
  rounding/precision policy in the guest, documented in the code.
- **Output is canonical postcard bytes** of a `BacktestResult` struct (equity
  curve as `Vec<i64>` basis points, trade log, summary metrics), so that
  `blake3::hash(&output_bytes)` is the `output_commit`.

## Fuel-metering strategy

Fuel is the **deterministic** metering primitive (unlike epoch interruption,
which is ~10% overhead but non-deterministic — per
`hybrid_decentralized_compute_network.md` §"WASM+WASI (wasmtime)"). The plan:

1. **`JobManifest.max_fuel`** (already in `proto`) bounds the job. The host
   sets `Store::set_fuel(max_fuel)` before instantiation.
2. **The guest calls `tlb::fuel()`-equivalent / the host observes**
   `Store::get_fuel()` after execution; the consumed fuel becomes
   `proto::ExecutionMetrics.fuel_consumed`.
3. **A job that traps with `Trap::OutOfFuel`** produces no receipt (it did not
   complete); the host records a failed-job event. This is the abuse/spin-loop
   defense — an adversarial or buggy guest cannot burn unbounded host CPU.
4. **`billable_units`** (already in `proto::ExecutionMetrics`) is derived from
   fuel via a documented, versioned policy (e.g. `billable = fuel / K`), set by
   the workload adapter, not by the guest. This keeps billing in the host's
   control (consistent with `settle-core` non-custodial money handling).

## Determinism guarantees and the acceptance test

### What guarantees bit-identical `output_commit`

- Same `input_commit` (BLAKE3 of the input bundle).
- Same WASM module hash (BLAKE3 of the `.wasm` bytes — the
  `ExecKind::Wasm { module_hash, fuel_used }` from
  `hybrid_decentralized_compute_network.md` §1a).
- Same `max_fuel`.
- Same Wasmtime version + config (pin the version in `Cargo.toml`; the module
  hash + version form the canonical execution environment).
- `cranelift_nan_canonicalization(true)`, no host-clock/filesystem access,
  sorted-container discipline in the guest.

### The Sprint 01 acceptance gate (this is the go/no-go)

The Sprint 01 code PR is **accepted** only when:

1. **Cross-machine bit-identity.** The same `(input_commit, module_hash,
   max_fuel)` produces the **same `output_commit`** (BLAKE3) on at least two
   machines (or two CI runners, e.g. `ubuntu-latest` + `macos-latest`, or two
   local hosts). This is the `DIRECTION_MODELING_PLAN.md` Track A Sprint-01
   gate.
2. **Tamper rejection.** A local verifier (a small `verify` module or test
   harness) re-runs the job and **rejects** a receipt whose `output_commit`
   does not match the re-computed hash, and rejects a receipt whose
   `input_commit` does not match the supplied bundle.
3. **Fuel bounded.** A deliberately-spinning guest (an infinite loop) traps
   with `OutOfFuel` at exactly `max_fuel`, does not hang, and produces no
   receipt.
4. **Standard CI gates.** `cargo fmt --check`,
   `cargo clippy --workspace --all-targets --all-features -- -D warnings`,
   `cargo test --workspace --all-features` all pass. `cargo miri test` on the
   core crates (per `AGENTS.md` verification gates).

### What is explicitly NOT guaranteed at Sprint 01

- **Committee verification across independent nodes.** Sprint 01 is local
  proof; the P3 verifier-committee layer (VRF sampling, redundant execution
  across nodes, dispute game) comes later. The Sprint 01 "verifier" is a
  deterministic re-execution in the same process/CI, not a network committee.
- **Cross-OS determinism if NaN paths diverge.** If `f64` is used and
  `cranelift_nan_canonicalization` proves insufficient on some platform, the
  fallback is **integer-only arithmetic** for the equity curve. This is a known
  risk; the acceptance test will surface it.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| `f64` NaN/rounding diverges across hosts | Start with integer/basis-point money; if `f64` is needed, canonicalize + pin precision policy; acceptance test catches divergence |
| Wasmtime version drift breaks determinism | Pin wasmtime in `Cargo.toml`; module hash + version = canonical execution env; CI re-runs on each dependency bump |
| The "minimal slice" creeps into the full engine | Strict scope: one strategy, one parameter cell, no ML, no walk-forward. Enlarging is a later PR. |
| Fuel accounting is guest-gameable | `billable_units` derived host-side from observed fuel, not guest-reported |
| FlowMate license/ownership blocks the port | Operator owns FlowMate; the port is a fresh Rust implementation of a well-known algorithm, not a copy of proprietary code. Confirm with operator before importing any FlowMate code directly (the Sprint 00 plan said "Add a FlowMate/backtest task adapter design doc before importing any FlowMate code" — this doc satisfies that). |

## Dependencies on other work

- **`crates/proto`** — already exists; the guest/host produce
  `proto::ComputeReceipt`, `proto::JobManifest`, `proto::ReceiptBody`. The
  existing `ED25519_SIGNATURE_LEN` check and `hash_canonical` are reused.
- **`crates/settle-core`** — not needed for Sprint 01 (no settlement yet), but
  the eventual settlement path will consume the receipt's `output_commit`.
- **FlowMate repo** — referenced as the dogfood source, but Sprint 01 ports a
  fresh Rust slice, not the Python engine. No code import without operator
  sign-off.

## Open questions / research left

- **Exact wasmtime version + feature set.** Verify the latest stable at
  implementation time; the field moves fast. Pin it.
- **Whether `wasi-virt` is needed.** If the guest stays pure-compute (no clock,
  no fs), it is not needed. If any virtualization is required for a later
  workload, add it then — not speculatively.
- **Cross-OS vs Linux-only.** The acceptance gate should try cross-OS first;
  if it fails on macOS/Windows but passes on Linux-Linux, fall back to
  "Linux-only workers until further notice" (the handbook already lists this as
  an acceptable fallback).
- **The `billable_units` policy.** Pinned in this design as "host-derived from
  fuel"; the exact `fuel / K` constant is a calibration question for the
  simulator, not for Sprint 01.

## Links

- Implements: `SPRINT_00_BOOTSTRAP.md` §"Sprint 01 backlog" items 1-3.
- Satisfies: `DIRECTION_MODELING_PLAN.md` Track A Sprint-01 gate.
- Related: `AGENTS.md` §2 (WASM/wasmtime is the chosen CPU sandbox),
  §verification gates.
- Related: `docs/research/hybrid_decentralized_compute_network.md` §1a
  (receipt spec), §"WASM+WASI (wasmtime)" (fuel determinism rationale).
- Related: `docs/research/seven_problems_solutions.md` §6 (deterministic
  compute — "solved for CPU/WASM").
- Dogfood source: FlowMate backtest engine
  (`/home/matesensei/ZCodeProject/FlowMate_Trading_Assistant/core/backtest.py`
  and `core/backtest_realistic/`) — referenced for algorithmic faithfulness,
  not for code import.
