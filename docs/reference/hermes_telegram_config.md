# Hermes + Telegram + GitHub vezérlőpult

## Ajánlás

Hermes használható, de ne ő legyen a production kulcsokat kezelő automata. A legjobb szerepe: Telegram control-plane.

Feladatok:

- GitHub issue létrehozás Telegramból
- workflow_dispatch indítás GitHub Actionsben
- CI/PR státusz összefoglalás
- sim futtatás workflow-on keresztül
- PR review kérés Codex/Claude agentektől

## Javasolt Telegram parancsok

```text
/status
/ci
/issue <cím> | <leírás>
/run_sim base 50 365
/run_sim stress 100 365
/review 123
/ship_p0
/stop
```

## Biztonsági szabályok

- Telegram bot csak allowlistelt chat_id-ről fogad parancsot.
- Hermes nem kap wallet private key-t.
- GitHub token fine-grained és csak szükséges repo scope.
- Mainnet deploy parancs nincs Telegramból.
- Minden veszélyes parancshoz kétlépcsős megerősítés:

```text
/deploy_testnet base-sepolia
/confirm <nonce>
```

## GitHub Actions indítás

Hermes ne SSH-val fusson rá közvetlenül a szerverre production munkákhoz. Inkább hívja a GitHub REST workflow_dispatch API-t, és a runner végezze el a munkát auditálható loggal.
