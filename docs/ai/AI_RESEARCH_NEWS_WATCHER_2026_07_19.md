# HDCN AI research, security and infrastructure watcher — 2026-07-19

## Status and scope

This is the first runnable read-only observation slice for the planned Hybrid AI/ML Manager.
It follows distributed-systems and cryptography research, Rust/runtime releases, P2P and WASM
infrastructure, security advisories, capacity/economic signals and engineering-management
methods. It emits advisory JSON and Markdown for operator review.

It does **not** dispatch compute, contact a node, sign anything, create a key, alter protocol
state, choose a settlement chain, modify payouts, deploy, merge or write to production.
Sprint 00 and the human merge gate remain authoritative.

## Canonical files

- `scripts/ai_research_watch/`: bounded standard-library collector and deterministic
  recommendation engine.
- `config/ai/research_sources.json`: reviewed RSS/arXiv/GitHub-release sources, keyword
  weights and recommendation rules.
- `.github/workflows/ai-research-watch.yml`: daily least-privilege observer and PR contract
  tests. All actions are pinned to immutable commits and permissions are `contents: read`.
- `tests/test_ai_research_watch.py`: parser, schema, state, fail-closed and policy tests.

The parser rejects non-HTTPS sources, private/reserved literal IP targets, oversized feeds,
DOCTYPE/entity declarations and oversized XML trees. Feed text is sanitized and never
becomes execution authority. Partial source failures are visible; all-source failure makes
the scheduled job fail while still uploading diagnostics.

## Run locally

```bash
python -m scripts.ai_research_watch \
  --config config/ai/research_sources.json \
  --output out/ai-research-watch/digest.json \
  --markdown-output out/ai-research-watch/summary.md \
  --state out/ai-research-watch/state.json \
  --new-only \
  --strict
```

## Recommendation lanes

- security evidence -> draft a threat-model update;
- protocol/scheduler evidence -> reproduce in the deterministic simulation sandbox;
- Rust/runtime dependency evidence -> benchmark in an isolated upgrade sandbox;
- GPU/cloud/DePIN market evidence -> review simulation assumptions only;
- SRE/architecture/management evidence -> draft an operator-review proposal.

Every recommendation requires human approval and has no execution authority. Allowed side
effects are limited to `none`, `sandbox` and `draft_only`.

## Important next development milestones

The complete PR-sized implementation backlog is:

```text
docs/ai/AI_MANAGER_SELF_IMPROVEMENT_IMPLEMENTATION_BACKLOG_2026_07_19.md
```

It documents:

- rootless, resource-bounded deterministic research reproduction;
- a protocol/scheduler simulation arena that extends `sim/` instead of creating a second
  scheduler or protocol;
- baseline/candidate code, simulation and workload benchmark receipts;
- optional experiment/artifact lineage without replacing ADR/modeling/sprint authority;
- capacity, queue, worker, receipt and economic-risk anomaly/drift challengers with no
  consensus or verifier authority;
- Rust/Python/Actions dependency and toolchain benchmarks;
- a separately granted automatic **draft-only** PR broker;
- offline shadow -> local deterministic canary -> later bounded node-pool stages;
- rollback-capable scheduler/model revisions that cannot sign, settle, pay or dispatch
  production compute;
- evidence-driven engineering and self-management recommendations.

The mandatory ordering is:

```text
strict contracts and observability
-> deterministic sandbox reproduction
-> baseline/candidate simulation and benchmark
-> independent review and ADR where required
-> offline/local canary
-> rollback-capable bounded promotion
```

## Next gated increments

1. Freeze an HDCN observation adapter contract without duplicating the FlowMate core types.
2. Implement `HDCN-SI-01` HDCN domain contracts and a fake reproduction broker before
   connecting Docker, MLflow, online-learning libraries or any node.
3. Add signed/attested provenance only after an ADR and threat-model review.
4. Reproduce selected research in `sim/` and attach deterministic receipts/seed/config data.
5. Generate draft proposal bundles; never autonomous production changes.

This file is a dated implementation handoff. It does not override `AGENTS.md`,
`SECURITY.md`, accepted ADRs, the current sprint or the AI Manager master direction.
