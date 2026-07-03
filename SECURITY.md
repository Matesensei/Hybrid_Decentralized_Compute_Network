# Security Policy

This repository is developed with AI coding agents (Codex, Claude Code, GLM) and
an optional Telegram control-plane (Hermes). Because this is a crypto/DePIN
project, an over-privileged agent can do more harm than good. This policy is
binding on **all** agents and on the human operator.

## 1. The human is the merge gate

- Agents may open issues, branches, and pull requests, and may review each other.
- **Only the human operator merges.** No workflow, bot, or agent is permitted to
  auto-merge.
- Settlement-, cryptography-, and CI-permission-related PRs require explicit human
  review even if all automated checks pass.

## 2. Never, under any circumstance (agents)

- Generate, request, store, print, or commit a **private key, seed phrase,
  mnemonic, or wallet secret**.
- Deploy to any **mainnet**, move treasury/production funds, or change
  signing/settlement-release logic **and** merge it.
- Commit **RPC keys, API keys, or production endpoints/addresses**. Use GitHub
  Secrets injected at runtime.
- Widen a workflow's `permissions:`, add a new secret consumer, disable a required
  check, or weaken branch protection. Any of these is a **trust-boundary change**
  and must be raised as an issue for the human, never merged by an agent.
- Run against **untrusted fork PRs** with secrets in scope (see §4).

## 3. Always (agents and operator)

- Use a **fine-grained GitHub token** with the minimum scopes for the task.
- Keep **branch protection** on `main`: required CI, required human review, no
  force-push.
- Store all secrets in **GitHub Secrets** (or, preferably, use OIDC/workload
  identity so there is no static key to leak).
- Keep an **audit trail**: every agent action arrives as an issue/PR/commit;
  every Telegram command is logged with its actor.
- Restrict the Telegram control-plane to an **allowlist of `chat_id`s**, and
  restrict CI agent triggers to an **allowlist of GitHub usernames**
  (`allow-users` on the Codex action; actor checks on the Claude action).

## 4. Fork-PR and CI safety

- Default PR trigger is **`pull_request`**, which does **not** expose repository
  secrets to fork PRs — this is the safe default. A fork PR sees empty secrets
  and the agent step no-ops rather than leaking credentials.
- Do **not** switch to `pull_request_target` unless you fully understand that it
  runs with access to secrets; never check out untrusted fork code in that job.
- Run agents in the **most restrictive sandbox** that still lets them do the job:
  read-only for review; workspace-write only when they must edit; never
  `danger-full-access`/`unsafe` on untrusted input.
- **Pin third-party actions to immutable commit SHAs** (not floating tags) so an
  upstream change cannot silently alter the trust boundary.

## 5. Telegram / Hermes control-plane boundary

The control-plane may issue **commands**, e.g.:

- "run the simulation workflow", "open an issue", "request a Codex review",
  "summarize the last CI failure", "show status".

The control-plane may **not** perform:

- "deploy to mainnet", "move treasury", "rewrite signing logic and merge",
  "reveal a secret".

Hermes/Telegram never holds keys and never has direct write access to protected
branches; it acts only by dispatching auditable GitHub workflows.

## 6. Reporting a vulnerability

Report security issues privately to the operator (contact in repo metadata) — do
not open a public issue for an exploitable finding. Include a description, an
affected-component list, and a reproduction if possible. No key material in the
report.
