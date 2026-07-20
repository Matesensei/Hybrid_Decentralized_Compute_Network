# HDCN — Independent Claude Review & Development Proposals (2026-07-19)

> **Advisory only.** Does not override accepted ADRs, HDCN protocol ownership, the current sprint,
> `SECURITY.md`, or the human merge gate. Independent read-only review by Claude (Opus 4.8); all
> claims treated as untrusted and reproduced where possible.

**Reviewed main:** `fb945f6`. **Date:** 2026-07-19. **Method:** detached worktree, `cargo` toolchain.

## 1. Repository health (reproduced on `fb945f6`)

| Gate | Result |
|---|---|
| `cargo fmt --check` | **PASS** |
| `cargo clippy --workspace --all-targets --all-features` | **PASS, 0 warnings** |
| `cargo test --workspace --all-features` | **PASS: 10/10** (proto 5, settle-core 5) |
| Python sim | no `tests/` dir; `py_compile` OK; full smoke needs numpy (CI's sim-smoke covers it) |

Production Rust is exemplary: **zero `unwrap`/`panic`/`TODO` outside `#[cfg(test)]`, `unsafe_code = "forbid"`, `no_std` proto.** Keep the bar with `clippy::unwrap_used`/`expect_used` deny lints for non-test code.

## 2. Crate map

| Crate | Role |
|---|---|
| `crates/proto` (`hdcn_proto`, no_std) | wire types (NodeId/JobId/ReceiptId, JobManifest, ComputeReceipt); canonical postcard + BLAKE3 IDs |
| `crates/settle-core` (`hdcn_settle_core`) | chain-neutral settlement: ChainNamespace (Evm/Solana/Sui/Polkadot/Xrpl), checked `Amount`, escrow/release validation |
| `sim/depin_network_model.py` | deterministic DePIN economics simulator |

## 3. PR verdicts

- **PR #10** (docs-audit, draft): head moved `250e6179` → `76175e31` (+1 commit); delta only **tightens** language (adapter-v1 → "proposed / no runtime adapter implemented"; Telegram doc → "Planned…"). Boundary intact; prior clean verdict holds and improved. `/ship_p0` + `/deploy_testnet` remain non-v1.
- **PR #11** (research/security watcher, draft, **stacked on #10**): **APPROVE** (draft). Genuinely least-privilege: workflow `permissions: contents: read` only, **all actions SHA-pinned**, no secrets, `observe` job skipped on `pull_request`, 10/15-min timeouts. Network hardening in `scripts/ai_research_watch/util.py`: HTTPS-only, private/reserved-IP-literal rejection (`:124-136`), 2 MiB caps, XXE defense (`:270-271`), 20k XML node cap, atomic 0600 writes, duplicate-key + float rejection. `models.py:141-142` fail-closes on `requires_human_approval != True`; side effects ≤ `none|sandbox|draft_only`. **13/13 tests pass.** Follow-up nits: (a) per-hop HTTPS (only final redirect checked); (b) DNS-based SSRF not blocked (only IP literals); (c) digest is a **prompt-injection carrier** if ever fed to `@claude`/an LLM — add an explicit "content is untrusted, treat as data" marker; (d) `assert` in `source_url` vanishes under `python -O`.

## 4. Confirmed P0 — over-privileged `claude.yml` (on `main`)

`.github/workflows/claude.yml`:
- `permissions: contents: write / pull-requests: write / issues: write / id-token: write` (lines 32-36)
- `ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}` (lines 44, 55)
- **Floating tags** `actions/checkout@v4` (line 38), `anthropics/claude-code-action@v1` (line 51) — while `SECURITY.md:62` mandates SHA-pinning.

Existing mitigations: `github.actor == 'Matesensei'` + `@claude` gate, `--max-turns 12`, no-op without the secret. But **write perms + OIDC + API secret + unpinned action tag** is an over-privileged combination: a retagged/compromised `claude-code-action@v1` would gain push/PR/issue/OIDC power and the API key. Same floating-tag issue in `ci.yml`, `codex-review.yml` (its own comment admits "pin to a SHA in production"), `sim-dispatch.yml`.

## 5. Branch hygiene
- `agent/claude/docs-dedup-consistency` — **fully merged** (0 ahead, via PR #8 `4cb1c20`). Safe to delete.
- `agent/codex/feat-research-news-intelligence` — PR #11 lane (cross-repo; same name in FlowMate/NOVA).

## 6. Prioritized development proposals

1. **P0 — Fix `claude.yml` privileges:** SHA-pin `claude-code-action` + `checkout`; drop `issues: write` and `id-token: write` unless actually used; consider splitting read-only response mode from PR-creation mode.
2. **P0 — SHA-pin all remaining workflows** (`ci.yml`, `codex-review.yml`, `sim-dispatch.yml`) per `SECURITY.md:62`; PR #11's `ai-research-watch.yml` is the template.
3. **P0 — Pin the FlowMate contract reference:** the master-direction doc says "Always resolve the **latest** FlowMate draft PR #406 head" — a floating cross-repo contract is a supply-chain/consistency hazard. Pin an exact commit SHA and bump deliberately.
4. **P1 — Make CI gates branch-protection-blocking:** confirm fmt/clippy/test are required status checks on `main`; add `--locked` to all cargo invocations.
5. **P1 — Supply-chain jobs:** run `cargo audit` / `cargo deny` (the repo watches their releases but doesn't run them); add dependency review; lock `sim/requirements.txt` with hashes.
6. **P1 — Receipt-verification hardening:** `ComputeReceipt::new` only length-checks the signature (64 bytes of `7`s passes) — **no Ed25519 verification exists yet.** Add a `verify` milestone with real signature verification + golden vectors before any settlement adapter.
7. **P1 — Conformance/golden-vector corpus:** extend `fixed_fixture_has_stable_canonical_bytes` into a checked-in golden-vector suite (canonical bytes + IDs); use it as the Rust-side conformance suite for the FlowMate S0 contracts so a postcard/serde bump can't silently change wire bytes.
8. **P2 — News-watcher follow-ups** (if #11 lands): resolve-time private-IP check, per-hop HTTPS, explicit "untrusted content" digest banner, and a documented rule that `@claude`/Codex workflows must never auto-ingest the digest artifact.
9. **P2 — License cleanup:** Cargo says `Proprietary`, sim docs imply free use, no `LICENSE` file exists (flagged in the repo's own audit doc §4.4).
10. **P2 — Decoder fuzzing:** add `cargo fuzz` targets for `JobManifest`/`ComputeReceipt` decode and settle-core state validation (proptest round-trips exist; adversarial input does not).
11. **P2 — CODEOWNERS + required review** for `.github/workflows/**`, `SECURITY.md`, `crates/**` so workflow-permission changes can't slip through.
12. **P3 — Delete merged `agent/claude/docs-dedup-consistency`; adopt delete-on-merge.**
13. **P3 — Keep the Rust bar:** add `clippy::unwrap_used`/`expect_used` deny lints for non-test code.
14. **P3 — Sim reproducibility:** pin numpy/pandas/matplotlib; check a seed-stamped baseline output hash into CI to detect simulator drift.

## 7. Cross-project isolation
Non-inheritance holds: HDCN adapter is capped at read/status/plan/sandbox-ingest; a FlowMate `LiveTradingGrantV1` is invalid in HDCN; no trading/signing/settlement/dispatch/deploy/merge authority is inherited. Keep this boundary when the compute executor is eventually built (needs a new capability version + accepted ADR).

## 8. Remediation status (updated later on 2026-07-19)

| Item | Status |
|---|---|
| §4/§6 P0-1 + P0-2 (`claude.yml` privileges, SHA-pinning all workflows) | **Draft PR #14** — all 4 workflows SHA-pinned (live tag→SHA resolution), `id-token: write` dropped, `--locked` added to cargo clippy/test (part of P1-4). CI-tier → human merge required. |
| §6 P0-3 (pin the FlowMate #406 contract reference) | Open — blocked on the FlowMate #406-family fate decision |
| Everything else (§6 P1–P3) | Open — awaiting human triage |

*Reviewer: Claude (independent, read-only). Nothing committed to code paths, merged, or deployed.*
