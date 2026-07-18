# Planned Hermes + Telegram + HDCN AI Manager control plane

## Current implementation

HDCN currently has no AI Manager runtime adapter and no authenticated Hermes/Telegram gateway.
This document defines a proposed default-OFF boundary; it is not configuration or evidence of a
deployed service.

The proposed adapter v1 would be limited to read/status/plan and bounded local sandbox artifact
ingest. It must not receive wallet or signing keys and cannot dispatch workflows, modify GitHub,
deploy, settle, pay, merge, or trade.

The master roadmap is
`docs/ai/AI_MANAGER_HYBRID_MASTER_DIRECTION_AND_CONSOLE_SPRINTS_2026_07_18.md`; the proposed
adapter boundary remains `docs/ai/AI_MANAGER_ADAPTER_HANDOFF_2026_07_18.md`. `SECURITY.md` and
accepted ADRs win on conflict.

## Proposed v1 commands

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

When implemented, `/ai_sim_plan` may create a deterministic plan only; it must not call
`workflow_dispatch`.
`/ship_p0` and `/deploy_testnet` are not v1 commands. A future workflow or compute executor needs a
new HDCN capability version, accepted ADR, exact approval, separate credentialed executor,
operation/readback receipts, and independent review.

## Planned authentication and replay protection

- Allowlist both Telegram `user_id` and `chat_id`; a display name is not identity.
- Bind every request to `project_id=hdcn`, tenant/workspace, adapter, exact scope, mode, policy,
  nonce, Telegram `update_id`, creation time, expiry, and idempotency key.
- Accept state changes only through strict commands or signed button callbacks. Free text is
  advisory context and never becomes an executable payload.
- Enforce RBAC, rate/cooldown limits, exact object hashes, immutable receipts, and readback.
- `/ai_off`, `/ai_revoke`, and `/ai_kill` are immediate, idempotent, deny-overrides-allow actions
  whose operation does not depend on an external AI provider.
- Telegram may activate or narrow a pre-authorized HDCN capability; it cannot create a capability
  above the server policy ceiling.

## Data and credential boundary

Never send bot tokens, GitHub/API credentials, wallet/signing material, raw headers, raw stack
traces, private workloads, protected payloads, or personal/customer data to Telegram or an LLM.
Store only sanitized evidence references, fingerprints, exact revisions, and bounded operator-
safe summaries. Rotate the bot token through the secrets manager; do not place it in repository
configuration or chat history.

## Project isolation

A FlowMate live-trading capability has no meaning in HDCN and cannot authorize a trade,
settlement, payout, signing operation, treasury action, workflow dispatch, production node change,
deployment, or merge. Cross-project and cross-tenant grant reuse is a blocking security defect.
