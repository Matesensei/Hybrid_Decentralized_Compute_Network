# HDCN — Projekt-kézikönyv (agent-vezérelt fejlesztés, emberi merge-gate)

**Projekt:** Hybrid Decentralized Compute Network (HDCN) — chain-agnosztikus,
multi-network decentralizált compute hálózat.
**Ez a fájl:** ember-olvasó kézikönyv. A repóba kerülő agent-spec fájlok
(`AGENTS.md`, `SECURITY.md`, ADR-ek, workflow-ok) **angolul** vannak, mert azokat
az AI-agentek (Codex, Claude Code) parse-olják, és az angol a megbízható konvenció
— de minden indoklásuk itt, magyarul (és a `PROJECT_HANDBOOK_EN.md` tükörben)
olvasható. A tükörfordítás elve tehát: **a dokumentáció kétnyelvű; a kód-közeli
repó-artefaktumok angolul maradnak** (ha kifejezetten kéred, magyar olvasó-verziót
is csinálok belőlük).

---

## 0. Egymondatos összefoglaló

A ChatGPT stratégiai iránya jó ("compute-first, settlement-later", ne akarj mindent
egyszerre, ne GPU-inference-szel kezdd a trustless compute-ot) — ezt tartsd meg; a
két gyengéje (a multi-network keretezés és a projektre szabott konkrétumok) ebben a
csomagban van pótolva, egy kimásolható repó-vázzal együtt.

---

## 1. A ChatGPT-elemzés értékelése

### 1.1 Amiben igaza van (tartsd meg)

- **Compute-first, settlement-later**, és a projekt kettévágása (compute mesh vs.
  cross-chain settlement) — helyes reflex. Ne egyszerre épüld a P2P-t, a GPU-t, a
  tokent, a multi-chaint és az agent-workflow-t.
- **Ne GPU-inference-szel indíts trustless compute-ot.** A CUDA floating-point
  nemdeterminizmus + driververziók miatt a "lefutott, tehát igaz" nem elég;
  determinisztikus WASM / render-tile-hash / fix-seed Monte Carlo a jó első
  workload. Ez a legfontosabb technikai húzása, és korrekt.
- **AI-agent biztonsági szekció** (soha kulcs/seed/mainnet-deploy agentnek, soha
  auto-merge settlement PR-nál, mindig human approval + fine-grained token + branch
  protection). Ezt sokan elrontják — ő nem. Ez a memó legértékesebb része.
- **Nem csak beszél, szállít:** futtatható szimulátor (supply, áramköltség,
  treasury, Sybil, verification committee), és tisztességesen "döntéstámogató
  modellnek, nem jóslatnak" nevezi. Jó epistemikus higiénia.

### 1.2 Ahol gyenge vagy pontatlan (ezt pótoljuk)

- **A multi-network keretezést elrontja.** Base/EVM-re vált, és a Sui-t (meg a
  többit) mellékvágányra teszi. A te döntésed viszont: **ez multi-network projekt,
  a Sui nem fontosabb és nem kevésbé fontos a többinél.** A helyes keret: ~8
  egyenrangú settlement-adapter egy `SettlementAdapter` trait mögött; a **Base csak
  az első implementált** lánc, mert olcsó/gyors EVM és egy Solidity-kódbázis 4 EVM-
  láncot lefed. Ez **sorrendezés, nem rangsor.** (Ezt az egész csomag így kezeli;
  lásd ADR-0001.)
- **Nem ismerte fel a FlowMate-et mint kész dogfooding-workloadot.** Generikus
  "WASM backtestet" említ; a lényeg viszont, hogy neked *már van* egy backtesting
  frameworköd, ami az első valódi, láncoktól független workload lehet, és
  de-riskeli az egészet. A compute-hálózat külön projekt a FlowMate-től, de a
  FlowMate elosztott backtestje lehet az első terhelése.
- **Nulla idő/költség-becslés.** Egy solo devnek fontos. A korábbi kutatás konkrét
  számokat adott (durván ~9-11 hónap béta-ig; komfort AI-előfizetés ~$206/hó;
  infra ~€10-15/hó). Ezt tartsd fejben döntésnél.
- **Vékony a MiCA/szabályozás.** EU-s (magyar/osztrák) solo devnek a "mikortól
  válik engedélykötelessé" kérdés projektölő tud lenni, és ez nem mérnöki probléma.
  Alapállás: **fee-only, token nélkül, non-custodial** — ez tartja a legkisebben a
  kitettséget; a VASP/CASP-kérdést ügyvéddel kell tisztázni a permissionless
  mainnet előtt.

### 1.3 "Nem túl korlátozó?" — a te aggodalmad

A ChatGPT enyhén a **konzervatív** oldalon van: sok mindent "későbbre" tol (token,
GPU, multi-chain, Sui). A sorrendezés nagyrészt helyes, de fontos látni: ezek
**prioritási döntések, nem örök tiltások.** A csomag ezért **megőrzi a kutatási
opciókat** (minden ADR-nek van "Open questions / research left" szekciója, a
settlement-rétegnél ott az ERC-7683 intent-solver mint későbbi opció, a GPU külön
track). A GPU-t és bármelyik láncot előrébb súlyozhatod, ha van rá okod.

---

## 2. Projekt-keretezés (a fejlesztés fő tengelyei)

1. **Compute-first.** A mesh a termék. Token/GPU/multi-chain szélesség később.
2. **Multi-network by design.** Semmi nem privilegizál egy láncot a core-ban; a
   lánc-specifikumok az adapter-crate-ekbe kerülnek. Base az első, sorrend-okból.
3. **Determinisztikus verifikáció > nyers throughput.** Első workloadok
   Wasmtime-ban, fuel-metered, bit-azonos újrafuttatással ellenőrizve. A GPU külön,
   későbbi, önálló szál (`executor-gpu`, külön processz).
4. **Emberi tulajdonú merge-gate.** Az agentek issue-t/PR-t nyitnak és review-znak;
   a gate a tiéd. Agent csak a te kifejezett, per-PR utasításodra mergelhet; a §2
   katasztrofális változásokat (settlement/kripto/CI-jog, mainnet, treasury)
   továbbra is te mergeled személyesen. Lásd `SECURITY.md` §1.

---

## 3. Repó-felállítás (lépésről lépésre)

A csomag `hdcn/` mappája egy kész repó-váz. Lépések:

**3.1 Repó + alapok**
1. Hozz létre egy privát GitHub repót (`hdcn`), és másold be a `hdcn/` tartalmát.
2. `rust-toolchain.toml`-ban rögzítsd a stable csatornát (reprodukálható build).
3. Töltsd fel a ChatGPT-féle `depin_network_model.py`-t a `sim/` mappába (a
   `ci.yml` és a `sim-dispatch.yml` innen hívja).

**3.2 Branch protection (`main`)** — Settings → Branches → Add rule:
- Require a pull request before merging → **Require approvals: 1** (te).
- Require status checks to pass → jelöld be a `ci` job-okat (test, supply-chain,
  determinism).
- **Do not allow force pushes**, **do not allow deletions**.
- (Opció) Require signed commits, ha a Claude/Codex commit-signinget használ.

**3.3 Secrets** — Settings → Secrets and variables → Actions:
- `ANTHROPIC_API_KEY` (vagy `CLAUDE_CODE_OAUTH_TOKEN`) a Claude Code-hoz.
- `OPENAI_API_KEY` a Codex-hez.
- **Fontos:** ezek repository secretek; fork PR-ok alapból **nem** látják őket
  (`pull_request` trigger), ezért az agent-lépés fork PR-nál no-op — ez a
  biztonságos default. Lásd `SECURITY.md` §4.
- Ideális esetben statikus kulcs helyett **OIDC / workload identity federation**
  (a Claude action támogatja) — nincs mit szivárogtatni/rotálni.

**3.4 GitHub App-ok telepítése**
- **Claude:** a legegyszerűbb a Claude Code CLI-ből `/install-github-app`
  (feltelepíti a GitHub App-ot + a secretet + a minta workflow-t). Admin-jog kell.
- **Codex:** kapcsold be a Codex cloudban a "Code review"-t a repóra (ehhez jön az
  `@codex review`), vagy használd a self-hosted `openai/codex-action`-t (a
  `codex-review.yml` már ezt tartalmazza).

**3.5 Ellenőrzés**
- Nyiss egy dummy PR-t → `@claude` egy kommentben → válaszol ~30-60 mp-en belül.
- `@codex review` egy PR-ban (ha a cloud path be van kapcsolva) → 👀 reakció, majd
  P0/P1 review.
- Indítsd a szimulátort a UI-ból: Actions → sim-dispatch → Run workflow.

---

## 4. A repó-fájlkészlet — mit csinál melyik fájl

| Fájl | Szerep |
|---|---|
| `AGENTS.md` (gyökér) | A központi agent-szerződés: mi a projekt, a stack, az agent-szerepek, a kódszabályok, a review-guideline-ok (Codex innen olvassa a `## Review guidelines`-t), és a hard-stopok. |
| `crates/proto/AGENTS.md` | Per-crate szigorítás a wire-formátumra: postcard-only, kanonikus bájt-layout, nulla nemdeterminizmus, aláírás-lefedettség, kötelező round-trip tesztek. |
| `crates/settle-core/AGENTS.md` | Per-crate szigorítás a settlementre: chain-neutrális maradjon, non-custodial, explicit release-feltételek, nincs float a pénzre, replay-védelem, MiCA-figyelmeztetés. |
| `SECURITY.md` | Agent-guardrailek: soha kulcs/seed/mainnet-deploy; soha auto-merge; fork-PR- és sandbox-szabályok; a Telegram/Hermes control-plane határai; disclosure. |
| `docs/adr/0000-adr-template.md` | MADR-formátumú ADR-sablon (van "Open questions / research left" szekció — a kutatási opciók megőrzésére). |
| `docs/adr/0001-multi-network-settlement.md` | Kitöltött példa: a multi-network döntés + Base-first sorrendezés rögzítve. |
| `.github/workflows/ci.yml` | fmt/clippy/test OS-mátrix + Miri (core crate-ek) + cargo-deny/audit + sim-smoke. |
| `.github/workflows/claude.yml` | `@claude` interaktív agent (fork-safe triggerek, `--max-turns` korlát). |
| `.github/workflows/codex-review.yml` | Self-hosted Codex PR-review (read-only sandbox, allow-users). |
| `.github/codex/prompts/review.md` | A Codex-review prompt (P0/P1 checklist). |
| `.github/workflows/sim-dispatch.yml` | `workflow_dispatch` a szimulátorra — Telegramból REST-tel indítható. |

---

## 5. GitHub Actions AI-automatizálás (2026-os szintaxis)

### 5.1 Claude Code — `@claude`

Az `anthropics/claude-code-action@v1` a GitHub-runneren futtatja a teljes Claude
Code runtime-ot; a kód nem hagyja el a GitHub-infrastruktúrát, az API-hívás megy a
választott providerhez. A **v1** összevonta a CLI-opciókat a `claude_args` alá, és
a mód (interaktív `@claude` vs. automation-prompt) automatikusan eldől. Trigger:
`issue_comment` / `pull_request_review_comment` / `issues` / `pull_request_review`.
Jogosultság: `contents`, `pull-requests`, `issues` write + `id-token: write` (OIDC).
Auth: `anthropic_api_key`, vagy `claude_code_oauth_token` (Pro/Max: `claude
setup-token`), vagy — legjobb — workload identity federation (nincs statikus kulcs).
`--max-turns` kötelező a költség/biztonság miatt (review-hoz 3-5, komplex feladathoz
10-15). Lásd `claude.yml`.

### 5.2 Codex — `@codex review` és self-hosted action

Két út van, és mindkettőt érdemes ismerni:

- **Cloud path (`@codex review`):** kapcsold be a Codex-settingsben a "Code
  review"-t, majd írd egy PR-kommentbe: `@codex review`. Codex 👀-val reagál, és
  review-t posztol; a **legközelebbi `AGENTS.md`** guideline-jait alkalmazza minden
  megváltozott fájlra, és GitHubon **csak P0/P1**-et jelez. "Automatic reviews"
  bekapcsolva minden új PR-t automatikusan átnéz. Ez a legegyszerűbb — nem kell
  YAML.
- **Self-hosted path (`openai/codex-action@v1`):** ha teljes kontroll kell a
  promptra/modellre. A `codex-review.yml` ezt csinálja: `pull_request`-en checkout
  a merge-refre, Codex **read-only** sandboxban a `review.md` prompttal, majd egy
  második job kommentként kiposztolja az eredményt. Sandbox-módok: `read-only` /
  `workspace-write` / `danger-full-access` — reviewhoz mindig `read-only`.
  `allow-users`-szel korlátozd, ki indíthatja. Prodban **pin-eld SHA-ra** az
  action-t (trust-boundary).

Kulcs a `AGENTS.md`-hez: a `## Review guidelines` szekciót a Codex kifejezetten
keresi és alkalmazza — ezért van benne a gyökér-`AGENTS.md`-ben, és ezért erősebb a
per-crate `proto`/`settle-core` guideline.

### 5.3 `workflow_dispatch` (Telegramból is indítható)

A `sim-dispatch.yml` `workflow_dispatch`-csel fut, `scenario`/`runs`/`days`
inputokkal. Programból (pl. Telegram-botból) a REST-tel indítható:

```
POST /repos/{owner}/{repo}/actions/workflows/sim-dispatch.yml/dispatches
Authorization: Bearer <fine-grained PAT, "Actions: write">
X-GitHub-Api-Version: 2022-11-28
{ "ref": "main", "inputs": { "scenario": "stress", "runs": "100", "days": "365" } }
```

A bot **csak dispatch-el** — nincs nála kulcs, nem deployol. A token fine-grained,
erre a repóra szűkítve. A Telegram oldalon a hivatalos HTTP Bot API + webhook a jó
minta (webhook → FastAPI → `workflow_dispatch` → Actions → artifact + summary →
Telegram-válasz), `chat_id` allowlisttel. Lásd `SECURITY.md` §5.

### 5.4 Az agent-workflow egy képben

```
Te (Telegram/GitHub)
  └─ issue nyitás / workflow_dispatch
       ├─ Hermes: összefoglal, besorol, dispatch-el (KULCS NÉLKÜL)
       ├─ Claude Code (@claude): architektúra, kritikus crate-ek, PR nyitás
       ├─ Codex (@codex review): adversarial review, P0/P1
       ├─ GitHub Actions CI: fmt/clippy/test/miri/deny/audit + sim-smoke
       └─ TE: tiéd a merge-gate (agent csak a te per-PR utasításodra mergel;
          a §2 settlement/kripto/CI-jog PR-t te mergeled személyesen)
```

---

## 6. Fejlesztési sprintek (solo dev + agentek)

### 6.1 A sprint-ciklus (issue → spec → impl → review → CI → merge)

Egy feladat útja mindig ugyanaz, és te a kapuban állsz:

1. **Issue** (te, vagy Telegramból Hermes) — világos leírás, elfogadási kritérium.
2. **Spec/ADR** (architect-agent, jellemzően Claude Code) — ha a feladat érint egy
   stack-döntést vagy protokoll-elemet, előbb ADR-PR (`proposed`).
3. **Implementáció** külön branchen (`agent/<name>/<type>-<slug>`) — egy crate =
   egy agent; a `proto`/`verify`/`settle-core` Claude, a párhuzamos/teszt-oldal
   Codex, a boilerplate GLM.
4. **Cross-review** — a másik agent (`@codex review` vagy `@claude`) átnézi;
   egyet-nem-értésnél eszkaláció hozzád.
5. **CI** — fmt/clippy/test/miri/deny/audit + sim-smoke zöld.
6. **Merge** — **tiéd a gate;** agent a te kifejezett per-PR utasításodra mergelhet
   (a §2 katasztrofális változásokat te személyesen). Az ADR-t te mozgatod
   `accepted`-re.

### 6.2 Ütem (cadence)

Solo devnek a "sprint" inkább **1-2 hetes fókuszblokk** egy fázison belül, mint
ceremónia. Ajánlás: **hetes ciklus** — hétfő: issue-k kijelölése + ADR-ek; hét
közben agent-implementáció + review; péntek: merge-ablak + a szimulátor futtatása a
döntésekhez (`base`/`stress`/`security`, 100-500 Monte Carlo run). A limit-terhelést
figyeld: a Claude/Codex előfizetéseknél a token-keret a szűk keresztmetszet, nem az
óra.

### 6.3 Fázisos roadmap (P0 → P5)

| Fázis | Cél / deliverable | Go/No-Go |
|---|---|---|
| **P0** | Működő repó: `sim/` szimulátor, CI, `AGENTS.md`-készlet, Telegram/Hermes control, ADR-ek. | A `base`/`stress`/`security` szcenárió lefut CI-ban; `@claude`/`@codex` válaszol. |
| **P1** | Lokális compute-proof: Rust CLI + Wasmtime task-runner + input/output hash + signed receipt + lokális verifier. | Egy determinisztikus WASM-task (pl. FlowMate-részfeladat) **bit-azonos** `output_commit`-ot ad 2-3 gépen. |
| **P2** | iroh P2P mesh: 3-10 node, capability-announce, job-gossip, bid, assignment, result-commit, receipt, latency/relay-metrika. | 10+ node stabil gossip, épül a receipt-DAG NAT mögött. |
| **P3** | Base escrow: Foundry `ComputeEscrow.sol`, receipt-submit, release, dispute-placeholder, Base Sepolia deploy. | `escrow_create → release → claim` zöld testneten. |
| **P4** | GPU worker (KÜLÖN track): NVML-detektálás, CUDA-benchmark, GPU task-runner, redundáns verifikáció, challenge. | Egy csaló GPU-worker megbízhatóan detektálódik; a GPU-processz izolált. |
| **P5** | Multi-chain / intent-réteg: CCTP-adapter, ERC-7683-kompatibilis intent-reprezentáció, LI.FI/Socket quote-réteg, solver-integráció; további láncok. | 3+ lánc mainnet-escrow; intent-solver csak validált corridor-forgalomnál. |

A GPU (P4) és a Base (P3) sorrendje felcserélhető, ha a te prioritásod más — a GPU
külön projekt-szál, a FlowMate CPU-workloadja mellett futhat.

---

## 7. Settlement-réteg (multi-network) — a feltöltött elemzések beépítve

### 7.1 A fő tanulság a cross-chain elemzésből

A "minden lánc/DEX fölötti egyetlen gyors P2P réteg" tiszta formában **nem reális**:
nincs közös állapot a láncok között, a finality lánconként eltér, és a settlementnek
végül **on-chain** kell megtörténnie (a leglassabb lánc a szűk keresztmetszet). A
legközelebbi reális modell az **intent/solver/filler** architektúra az **ERC-7683**
körül, aggregátorokkal (LI.FI, Socket/Bungee). Solo/kis-csapat szinten **nem saját
base-protokoll/L1** a jó irány, hanem meglévő settlement/bridge/aggregátor
infrastruktúrára épített réteg. Ezért:

- A P2P-overlay a **compute-rétegben** hasznos (job-gossip, discovery, receipt-DAG,
  censorship-resistance), **nem** a pénzügyi finalityben.
- A pénzügyi finality **láncon** történik, corridoronként.

### 7.2 A választott modell (ADR-0001)

> Kanonikus döntés + teljes indoklás: `docs/adr/0001-multi-network-settlement.md`.
> Ez a szakasz az ember-olvasható kivonat; ha eltérnek, az ADR az irányadó.

- **Chain-agnosztikus `SettlementAdapter` trait**; minden lánc egyenrangú.
  `escrow_create / escrow_release / escrow_refund / claim_payment /
  anchor_checkpoint`. A core chain-neutrális; a specifikum az adapter-crate-ben.
- **Base az első adapter** (olcsó EVM, egy Solidity-kódbázis 4 EVM-láncra) —
  sorrendezés, nem rangsor. Sorrend: Base → Solana → Sui → BNB/Avalanche (ugyanaz a
  contract) → Polkadot → XRPL (utolsó, leggyengébb Rust-SDK).
- **Settlement-asset:** USDC via **CCTP V2** ahol elérhető (natív burn/mint,
  non-custodial, nincs wrapped bridge); a chain-support **implementáció előtt friss
  ellenőrzést** igényel (Circle a kanonikus verziót változtathatja/bővítheti).
  XRPL nincs CCTP-n → **RLUSD** vagy corridor-híd.
- **ERC-7683 intent/solver** = **későbbi** optimalizáció nagy, egyszeri
  cross-corridor kifizetésekre (szétválasztja: "mit akar a user" vs. "hogyan
  teljesíti a solver"), **nem** az alap-primitív. Belső netting/clearing a
  default; az intent-solver akkor éri meg, ha van corridor-forgalom.

### 7.3 Settlement-lépcső (fázisokhoz kötve)

```
P0: mock/local accounting
P1: signed receipts + redb/SQLite ledger
P2/P3: Base Sepolia escrow → Base mainnet kis USDC escrow
P4-P5: CCTP/USDC ahol stabil → ERC-7683 intent/solver, LI.FI/Socket quote-réteg
```

### 7.4 Szabályozás (nem jogi tanács)

Alapállás: **fee-only, protokoll-token nélkül, non-custodial** — így a MiCA-kitettség
light-touch (nincs asset-referenced/e-money token kibocsátói kötelezettség a
protokoll oldalán). A matching + settlement üzemeltetése felvetheti a **VASP/CASP**-
regisztráció kérdését — ez **ügyvédi** döntés a permissionless mainnet előtt, nem
mérnöki. A `settle-core/AGENTS.md` ezért tiltja, hogy egy agent tokent/custody-t
vezessen be; ilyennél az agentnek **meg kell állnia** és issue-t nyitnia neked.

---

## 8. Nyitott kutatási kérdések / megőrzött opciók

Ezeket **szándékosan nem zárjuk le** — minden ADR-ben ott a "research left" szekció:

- **Consensus/verifikáció mélysége:** committee-méret (`k`), VRF-sampling
  paraméterek, redundancia-arány GPU-jobra vs. CPU-jobra — a szimulátor
  `security` szcenáriója mutatta, hogy a "bad work" arány még túl magas, tehát a
  verifikációs paramétereket agresszívebbre kell venni. Ez kalibrációs kérdés.
- **Hálózati skálázás:** iroh-gossip 50+ node NAT mögött — ha nem skálázódik,
  libp2p gossipsub-ra váltás (a transport maradhat iroh). Benchmark dönt.
- **Wire-formátum:** postcard a default; ha valaha nem-Rust kliens kell, protobuf a
  külső API-ra (a belső marad postcard).
- **Anchoring-stratégia:** "legolcsóbb 2-3 lánc + per-corridor finality" (pl.
  XRPL+Solana) vs. forgó anchor-lánc — költség/bizalom trade-off, a lánc-árak
  volatilisek.
- **ERC-7683 időzítése:** mikor éri meg az intent/solver a belső nettinggel
  szemben — corridor-forgalom függvénye.
- **GPU-track:** mikor és melyik vertikum (AI inference / rendering / ZK proving) —
  külön projekt-szál, a determinisztikus CPU-mag stabilizálása után.
- **Simulation-eszköz:** a jelenlegi numpy/pandas modell elég P0-P2-re; komplexebb
  agent-based modellhez cadCAD/radCAD/Mesa később.
- **AI-budget:** Comfortable (~$206/hó) az induló szint; Accelerated csak ha 2 héten
  át folyamatosan limitbe ütközöl valós munkával.

---

## 9. A következő legjobb lépés

1. Repó létrehozása ezzel a csomaggal; `depin_network_model.py` a `sim/`-be.
2. Branch protection + secrets + a két GitHub App (Claude, Codex) beállítása.
3. Futtasd a `base`/`stress`/`security` szcenáriót 100-500 Monte Carlo runnal
   (a `stress` azonnal megmutatja, hogy treasury + node-onboarding nélkül a hálózat
   összeomlik keresleti sokknál — ez döntéstámogatás, nem jóslat).
4. Csak ezután a Rust P1-skeleton (`proto` + `identity` + `transport` +
   `executor-wasm`), a FlowMate-részfeladattal mint első determinisztikus WASM-task.

> **Forráskezelés a fájlokban:** az `AGENTS.md`/workflow-ok konkrét szintaxisa az
> `anthropics/claude-code-action` és az `openai/codex-action` hivatalos
> dokumentációját követi (2026 közép); a `workflow_dispatch` a GitHub REST API
> szerinti. Éles használat előtt érdemes a friss verziót ellenőrizni, mert ezek
> gyorsan változnak.
