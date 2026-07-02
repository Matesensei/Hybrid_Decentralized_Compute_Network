## Summary

- 

## Validation

- [ ] `cargo fmt --check`
- [ ] `cargo clippy --workspace --all-targets --all-features -- -D warnings`
- [ ] `cargo test --workspace --all-features`
- [ ] Simulator/modeling command, if relevant:

## Documentation

- [ ] Public API docs updated for public code changes
- [ ] ADR updated or added for architecture/stack decisions
- [ ] Sprint/modeling docs updated for validation results or decision gates
- [ ] `docs/ai/REPO_MAP.md` updated if layout, ownership, workflow, or navigation changed

## Anti-duplication

- [ ] Searched existing docs/code with `rg`
- [ ] Reused or extended the canonical owner from `docs/ai/REPO_MAP.md`
- [ ] Did not create a parallel `v2`, duplicate enum/model/type, or duplicate doc owner
- [ ] Any intentional parallel prototype is default-off and justified by ADR/modeling docs

## Cross-review

- [ ] Requested review from another AI agent
- [ ] Cross-review verdict is linked or quoted in this PR
- [ ] If second AI is unavailable, explicit human override is requested here

## Security

- [ ] No private keys, seed phrases, mnemonics, RPC secrets, API keys, or mainnet deploy keys
- [ ] Workflow permission or secret changes are explicitly called out
- [ ] No mainnet deployment, token issuance, bridge release, or funds movement
