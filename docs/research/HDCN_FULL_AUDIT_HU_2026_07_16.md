> **Repository status:** dated external audit/research input, not an accepted ADR or
> production-readiness claim. Agents must read `AGENTS.md`, `docs/ai/REPO_MAP.md`,
> `SECURITY.md`, the current sprint, and applicable ADRs before acting on it.
> Use `docs/ai/CONSOLE_HANDOFF_AUDIT_AND_PRODUCT_STRATEGY_2026_07_16.md` as
> the machine-facing entry point.
# Hybrid Decentralized Compute Network — teljes projekt-, piaci, technikai, pénzügyi, kriptográfiai és stratégiai audit

**Vizsgálat dátuma:** 2026. július 16.

**HDCN vizsgált commit:** fb945f62a6cf7fe55915e88e5b87a43ff271811c, 2026. július 3.
**FlowMate vizsgált commit:** 6d703cdc66e4aff55c9a8b096f5e090515ad7bce, 2026. július 9.

## Vezetői összefoglaló

A Hybrid Decentralized Compute Network ötlete technikailag koherens és fejlesztésre érdemes, de a repository jelenleg nem működő decentralizált compute-hálózat. Egy jól dokumentált Sprint 00 kutatási és protokoll-scaffold: két kis Rust crate, egy Python szimulátor, valamint jelentős mennyiségű kutatási dokumentáció.

A legfontosabb döntés:

> **Ne általános GPU-piactérként, ne saját tokennel és ne saját blokklánccal induljon. A legjobb első termék egy FlowMate-tel dogfoodolt, reprodukálható és ellenőrizhető batch-compute réteg, whitelisted node-okkal, majd Base-en USDC settlementtel.**

Az értékelés röviden:

| Kérdés | Válasz |
|---|---|
| Van érték az alapötletben? | **Igen.** A verifiable/reproducible batch-compute irány differenciálható. |
| Kész termék a jelenlegi repository? | **Nem.** A teljes célarchitektúra becslésem szerint 5–10%-os kódkészültségű. |
| Működőképes a jelenlegi pénzügyi modell? | **Még nem igazolható.** A szimulátor lényeges költségeket kihagy, a verification feltételei mellett a 12%-os take-rate negatív marzsot is eredményezhet. |
| Kriptográfiailag biztonságos? | **Nem production szinten.** Az aláírás nincs ténylegesen ellenőrizve, a proof önbevallott metaadat, nincs megfelelő domain separation és replay-védelem. |
| Javítható és továbbfejleszthető? | **Igen**, de először protokoll-, sandbox-, accounting- és CI-hardening szükséges. |
| Összeköthető saját tokennel? | **Technikailag igen, stratégiailag most nem ajánlott.** Először USDC/fiat és valódi bevétel. |
| Összeköthető Ethereum/Base/Solana hálózattal? | **Igen.** Base legyen az első settlement chain, Ethereum csak ritka anchor/dispute, Solana a második adapter. |
| Kell saját L1 vagy bridge? | **Nem.** Jelenleg egyértelmű No-Go. |
| Összeköthető a FlowMate-tel? | **Igen, kifejezetten jól**, offline backtest, paraméterkeresés és validáció céljára. Élő kereskedésre és kulcskezelésre nem. |

## 1. Az audit hatóköre és korlátai

Átnéztem a két nyilvános GitHub repository fő ágát, fáit, Rust- és Python-forrásait, workflow-it, dokumentációját, nyitott issue-it, releváns korábbi PR-jeit, valamint a FlowMate jelenlegi research/backtest infrastruktúráját.

A HDCN repository fő forrásai:

- [HDCN repository](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network)
- [README](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/README.md)
- [proto crate](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/crates/proto/src/lib.rs)
- [settle-core crate](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/crates/settle-core/src/lib.rs)
- [Python gazdasági és hálózati szimulátor](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/sim/depin_network_model.py)
- [Sprint 00](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/docs/sprints/SPRINT_00_BOOTSTRAP.md)
- [bootstrap PR #1](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/pull/1)

Helyben a Python fájl szintaktikai ellenőrzése és egy 3 futásos, 30 napos smoke simulation sikeres volt. A Rust toolchain ebben az auditkörnyezetben nem állt rendelkezésre, ezért a Rust-kód értékelése statikus. A bootstrap PR korábbi CI-je zöld volt és 10 Rust-tesztről számolt be, de ez nem helyettesít aktuális, független reprodukciót vagy security auditot. A merge commithez aktuális GitHub status contextet nem találtam.

A pénzügyi számok döntéstámogató forgatókönyvek, nem befektetési ígéretek. A jogi rész nem jogi tanács; EU/MiCA/PSD2 minősítéshez szakjogász szükséges.

## 2. Mi van ténylegesen implementálva?

### 2.1 Repository-leltár

A HDCN kis repository: a tényleges Rust workspace két crate-et tartalmaz.

| Komponens | Tényleges állapot | Értékelés |
|---|---|---|
| proto | Job- és receipt-típusok, postcard serialization, BLAKE3 hash, 5 teszt | Hasznos prototípus, de security semantics nélkül |
| settle-core | Chain-neutral adattípusok, u128 money, trait, 5 teszt | Jó absztrakciós kezdet, adapter és state machine nélkül |
| Python szimulátor | Egyszerűsített gazdasági, kapacitás-, hálózati és Sybil-modell | Döntéstámogató toy model, nem forecast vagy security proof |
| Dokumentáció | Piac, token, multi-chain, P2P, modell és architektúra | Erős problémafeltárás, több helyen túl késznek mutatja a megoldást |
| CI | fmt, clippy, teszt, Python smoke és AI review workflow-k | Alapvető automatizálás, komoly supply-chain hardening kell |

### 2.2 Mi nincs implementálva?

Jelenleg nincs:

- futó node daemon;
- iroh/libp2p transport vagy gossip;
- peer identity-, key rotation- és revocation-réteg;
- scheduler, bid, assignment vagy job state machine;
- WASM executor vagy Wasmtime dependency;
- GPU worker, sandbox vagy capability benchmark;
- verifier committee, VRF, attestation vagy valódi fraud proof;
- receipt DAG, Merkle store vagy checkpoint rendszer;
- EVM, Base, Solana, Sui vagy más settlement adapter;
- smart contract;
- token, staking, slashing vagy bridge;
- confidential-compute/TEE megoldás;
- FlowMate adapter;
- production observability, SRE vagy incident response.

A README maga is jelzi, hogy nincs mainnet contract, token vagy production worker. Ezt fontos megőrizni: a projektet nem szabad működő DePIN hálózatként kommunikálni.

### 2.3 Készültségi becslés

Az alábbi százalékok szakmai becslések, nem objektív mérőszámok:

| Terület | Készültség |
|---|---:|
| Problémafeltárás és kutatási irány | 65–75% |
| Repository-struktúra és dokumentáció | 70–80% |
| Szimulátor mint kutatási eszköz | 20–30% |
| Wire protocol/schema | 15–25% |
| Settlement-absztrakció | 10–15% |
| Determinisztikus executor | 0–3% |
| P2P hálózat és node runtime | 0–3% |
| Verifier/security protocol | 0–3% |
| Láncadapterek és contractok | 0–3% |
| FlowMate end-to-end integráció | 0–3% |
| Permissioned PoC összességében | kb. 8–12% |
| Auditált permissionless production | kb. 1–3% |

## 3. Technikai és számítástechnikai elemzés

### 3.1 Ami jó alap

- A Rust jó választás a node-, protokoll- és settlement-kritikus réteghez.
- Az unsafe tiltása és a no_std-kompatibilis protokollirány csökkentheti a támadási felületet.
- A pénz egész számú base unitként, u128 típussal és checked arithmetic-kal jelenik meg.
- A BLAKE3 jó, gyors content-addressing és commitment primitive.
- A determinisztikus WASM/Wasmtime irány jó az első CPU batch workloadhoz.
- A chain-neutral settlement interface segít megakadályozni, hogy az architektúra túl korán egy lánchoz kötődjön.
- A repository nem deployolt elsietett tokent vagy mainnet contractot; ez jelenleg előny.

### 3.2 A proto crate kritikus hiányai

Az aláírás jelenleg csak egy 64 byte hosszúnak szánt mező. Nincs Ed25519 dependency, public-key parsing vagy verify függvény. A konstruktor csak a hosszt ellenőrzi, és a publikus deserialization a konstruktort is megkerülheti. Ez azt jelenti, hogy a receipt a jelen formájában nem kriptográfiailag hitelesített állítás.

További problémák:

- nincs protocol-, network- és message-type domain separation;
- a generikus hash különböző típusok azonos byte-sorozatára azonos commitmentet adhat;
- nincs replay window, expiry, escrow binding vagy consumed nonce;
- a NodeId nincs bizonyítottan public keyhez kötve;
- a signature Vec és más String/Vec mezők nincsenek méretkorlátozva;
- a ProofBundle csak committee_size és quorum mezőket hordoz, de nem tartalmaz member ID-kat, aláírásokat, vote-okat, epochot, randomness proofot vagy ellenőrizhető transcriptet;
- a JobManifestből hiányzik többek között a client identity, code/module digest, execution profile, adat-root, output schema, memory/disk/GPU limit, ár, payment/escrow ID, deadline, verification policy és privacy class;
- a billable_units, fuel_consumed és peak_memory_bytes worker által aláírt önbevallás, amíg egy verifier nem számolja újra.

Ajánlott proto-v2:

- auditált Ed25519 implementáció és strict verification;
- fix méretű signature és bounded types;
- HDCN:v1:Network:MessageType jellegű domain-separated envelope;
- explicit chain/network/deployment ID;
- creator signature, nonce, expiry és escrow reference;
- külön WorkerReceipt és AcceptanceCertificate;
- committee snapshot, taglista, vote/signature és randomness proof;
- signature_suite mező a későbbi crypto-agilityhez;
- golden cross-language test vectors és verziómigráció.

Az Ed25519 jó MVP-választás, ha szigorúan implementálják az [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032.html) szerint. Nem posztkvantum-biztos; hosszú távon algoritmus-agilitás és opcionális hibrid root identity indokolt. Az ML-DSA szabványos posztkvantum irányát a [NIST FIPS 204](https://csrc.nist.gov/pubs/fips/204/final) rögzíti.

### 3.3 A settle-core hiányai

Az absztrakció jó irány, de production settlementhez nem elegendő:

- a release proof conditionje nincs bizonyíthatóan az eredeti escrow feltételéhez kötve;
- az escrow handle nem commitol a teljes terms-höz;
- nincs implementált nonce registry, replay/idempotency vagy duplicate submission kezelés;
- az asset symbol és decimals nem elég a valódi token azonosításához;
- üres/hibás account, chain mismatch, zero job ID, duplicate receipt, expiry és proof size nincs teljesen validálva;
- nincs pontos finality/reorg state machine;
- a trait szinkron, nincs signer boundary, fee quote, RPC policy, transaction replacement vagy read/write szétválasztás;
- nincs valódi adapter.

A szükséges állapotgép:

Draft → EscrowSubmitted → EscrowFinalized → Announced → Assigned → Running → ResultCommitted → Verifying → Accepted/Challenged/Rejected → PayoutSubmitted/RefundSubmitted → Finalized.

Minden átmenet legyen tartós, monoton és idempotens.

### 3.4 WASM executor

A Wasmtime helyes első végrehajtási környezet, de a fuel önmagában nem teljes sandbox. A determinisztikus profile-nak legalább ezt kell rögzítenie:

- pontos Wasmtime-, Rust- és host ABI-verzió;
- module/component hash;
- NaN canonicalization;
- relaxed SIMD, thread és shared memory tiltás az MVP-ben;
- memória-, table-, instance-, output- és host-call limit;
- fuel mellett külső watchdog timeout;
- hálózat és filesystem default-deny;
- read-only filesystem;
- külön unprivileged process és OS user;
- Linux cgroup és seccomp/Landlock;
- semmilyen Docker socket vagy host secret.

A Wasmtime dokumentációja szerint a ResourceLimiter nem önmagában teljes memória- vagy CPU-biztonsági mechanizmus; fuel/epoch és OS-szintű kontroll is kell. [Wasmtime security](https://docs.wasmtime.dev/security.html), [ResourceLimiter](https://docs.rs/wasmtime/latest/wasmtime/trait.ResourceLimiter.html).

A fuel legyen reprodukálható work unit, de ne legyen automatikusan valós CPU-másodperc vagy piaci ár. Árazáshoz benchmark class kell.

### 3.5 GPU compute

GPU workload csak későbbi fázis:

- a worker mindig külön processzben, user alatt, containerben vagy VM-ben fusson;
- a GPU driver kernel attack surface, ezért ne legyen a core node daemon része;
- VRAM, PCIe, driver, CUDA/ROCm, bandwidth és multi-GPU topology capabilityként jelenjen meg;
- consumer GPU-n nincs általános trustless execution proof;
- determinisztikus CPU/WASM, TEE, statistical verification és zk/ML külön job class legyen;
- nondeterminisztikus GPU mismatch miatt automatikus slashing helyett először payout hold és dispute szükséges.

### 3.6 Hálózat és NAT

Az iroh jó kiindulópont: QUIC, hole punching és relay fallback áll rendelkezésre. A transport titkosítása azonban nem azonos az alkalmazás-hozzáférés vagy a Sybil-védelem megoldásával. Az alkalmazásnak kell eldöntenie, ki jogosult csatlakozni. [iroh dokumentáció](https://docs.iroh.computer/rust-api)

Kell:

- versioned ALPN;
- max frame/message/blob size;
- peer-, IP- és NodeId-kvóta;
- bounded queue és backpressure;
- signature verification gossip forwarding előtt;
- escrow finality ellenőrzés job forwarding előtt;
- duplicate cache és replay window;
- topic authorization;
- relay rate limit és több régiós redundancia;
- no state-changing 0-RTT;
- whitelist a béta alatt.

A repository egy kutatási dokumentuma a NAT-ot és a slashinget a megoldott problémák között tárgyalja. Pontosabb megfogalmazás kell: az iroh jelentősen segít a kapcsolódásban, de az abuse, relay economics, access control és Sybil security nincs implementálva; a slashinghez pedig nincs contract vagy objektív dispute protocol.

### 3.7 Adatbizalmasság

Jelenleg nincs confidential compute. Az in-transit encryption nem védi az adatot a worker hostjától vagy a verifierektől. A redundant re-execution még növeli is az adatot látó felek számát.

Javasolt job privacy class:

- Public;
- TransportEncrypted;
- TEERequired;
- később ClientPartitioned.

FlowMate-stratégia, privát orderflow-adat, exchange API key, wallet seed vagy Telegram secret soha ne kerüljön nem megbízható node-ra. TEE esetén attestationhöz kötött key release kell; több címzetthez szabványos HPKE használható az [RFC 9180](https://www.rfc-editor.org/rfc/rfc9180.html) szerint.

## 4. Kriptográfiai és biztonsági elemzés

### 4.1 Kockázati mátrix

| Súlyosság | Megállapítás | Következmény | Javítás |
|---|---|---|---|
| Kritikus | Nincs tényleges receipt signature verification | Hamis worker receipt elfogadhatóvá válhat | Ed25519 strict verify, public-key-bound identity |
| Kritikus | A ProofBundle nem committee proof | A worker önmaga állíthatja a quorum metaadatait | Külön AcceptanceCertificate és committee signature |
| Kritikus | Settlement proof nincs az eredeti escrow termshöz kötve | Hibás vagy más feltétellel történő release veszélye | terms hash és on-chain state binding |
| Kritikus | Nincs izolált executor | Untrusted job host kompromittálásához vezethet | Külön processz, OS sandbox, default-deny |
| Magas | Nincs domain separation és explicit replay-védelem | Cross-network/cross-message replay | typed envelope, network ID, nonce, expiry, consumed state |
| Magas | Korlátlan deserialization mezők | Memory/DoS támadás | bounded decode és fuzzing |
| Magas | Workflow actionök lebegő tageket és széles jogokat használnak | Supply-chain compromise, secret exfiltration | immutable SHA, least privilege |
| Magas | sim-dispatch szabad szöveget interpolál shellbe | Writer-szintű command injection/runner DoS | env átadás, regex és range validation |
| Magas | Dokumentációs Solidity-vázlat nem production-safe | Token elvesztése vagy jogosulatlan anchor/release | új contract design, SafeERC20, audit |
| Közepes | Nincs key rotation/revocation | Kompromittált key tartós reputációs hozzáférést kaphat | role-separated certificate hierarchy |
| Közepes | Receipt-root alapú randomness grindolható lehet | Committee manipuláció | külső finalizált beacon + VRF |
| Közepes | Nincs crypto agility | Nehéz későbbi algoritmusváltás | signature suite és versioned envelope |

### 4.2 Identity és kulcshierarchia

Egyetlen kulcs ne szolgáljon transport-, receipt-, VRF- és chain-wallet szerepre. Ajánlott:

1. offline vagy erősen védett node root identity;
2. rövid életű, aláírt transport certificate;
3. külön receipt-signing certificate;
4. külön VRF key;
5. külön chain payout address és külön contract admin/multisig;
6. validity epoch, sequence és revocation counter.

Az iroh endpoint cryptographic identity, de a HDCN reputációt a root identityhez kell kötni, hogy transport-key rotációkor ne vesszen el.

### 4.3 VRF, committee és slashing

A következő epoch receipt rootja önmagában nem jó random beacon, mert a rootot előállító fél a receipt halmazt, sorrendet vagy anchor időpontját befolyásolhatja. Szabványos VRF, például [RFC 9381](https://www.rfc-editor.org/rfc/rfc9381.html), előre rögzített stake/registry snapshot és a job után megismerhető, finalizált entropy szükséges.

Automatikusan csak objektíven bizonyítható esemény slashelhető:

- equivocation;
- invalid signature;
- replay;
- determinisztikus output mismatch;
- challenge elmulasztása.

Lebegőpontos vagy GPU tolerance mismatch esetén először payout hold, újrafuttatás és reputation penalty indokolt. Egy committee többségi vote nem automatikusan fraud proof.

### 4.4 CI és software supply chain

A SECURITY.md immutable action SHA-kat ír elő, miközben a workflow-k lebegő tageket használnak, például actions/checkout@v4, rust-toolchain@stable és AI action @v1. A Claude workflow ráadásul write-, issue/PR- és OIDC-jogokat, valamint API secretet kap. Ez P0 security probléma. [SECURITY.md](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/SECURITY.md), [Claude workflow](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/blob/main/.github/workflows/claude.yml)

További szükséges lépések:

- pinelt Rust toolchain;
- cargo parancsok --locked flaggel;
- cargo deny és audit;
- Python lockfile és hash;
- decoder és settlement state-machine fuzzing;
- secret scanning, dependency review, SBOM és artifact provenance;
- CODEOWNERS és kötelező review a security-critical részeken;
- a repository licencének rendezése: a Cargo proprietary jelölése és a szimulátor szabad felhasználásra utaló szövege ellentmond, miközben nincs egyértelmű LICENSE.

## 5. A szimulátor auditja

### 5.1 Checked-in eredmények

| Szcenárió | Futás/idő | Átlagos fill | Min. reserve ratio | Final treasury | Undetected bad share | Spiral |
|---|---:|---:|---:|---:|---:|---:|
| Base | 10 × 180 nap | 97,89% | 1,6678 | 136 497 USD | 1,23% | 0/10 |
| Security | 20 × 365 nap | 86,85% | 1,6857 | 202 017 USD | 3,76% | 0/20 |
| Stress | 20 × 365 nap | 52,99% | −1,1033 | 56 163 USD | 3,60% | 20/20 |

Ezek nem forecastok. A saját modeling gate 100 Monte Carlo futást és 365 napot kér; a base output csak 10 × 180 nap. A security modell 3,76%-os átlagos észrevétlen rossz work share-je settlementhez elfogadhatatlan.

### 5.2 Modellhibák

1. Az ügyfél inflow a treasuryhez adódik, miközben a node earnings új creditként keletkezik; nincs koherens credit purchase, spend, liability és redemption ledger.
2. A cashoutot a credit mennyisége, nem a treasury cash korlátozza, ezért a treasury negatív lehet, majd később vissza is térhet.
3. A kereslet a régi árral, az aznapi számlázás az új árral számol.
4. A verifier compute, reward, relay, gas, storage, dispute, support és fraud költsége hiányzik.
5. A slashing csak mérőszám, nem változtat stake-en, payouton vagy viselkedésen.
6. A security képlet nem modellez bribe-ot, collusiont, stake weightinget, common ownershipot, adaptive corruptiont, chain reorgot vagy randomness grindinget.
7. A P2P modell Erdős–Rényi/log-hop proxy; nincs relay capacity, NAT-eloszlás, queue, backpressure vagy churn topology.
8. A GPU-kapacitás tökéletesen aggregálható; hiányzik a VRAM/job compatibility, setup/download, bandwidth, failure és fragmentation.
9. A base demand growth 100%/év és több más input nincs piaci adatokkal kalibrálva.
10. Nincs sensitivity/Sobol analysis, confidence interval vagy out-of-sample kalibráció.

### 5.3 Kötelező modelljavítás

Kettős könyvelésű ledger kell legalább ezekkel:

- customer cash;
- purchased credit vagy prepaid balance;
- outstanding customer liability;
- credit spend;
- provider payable;
- protocol revenue;
- verifier payable;
- payout/refund;
- insurance reserve;
- corporate treasury.

Minden napra teljesüljön a pénz- és liability-megmaradási invariáns. Az insolvency ne csak jelzőszám legyen, hanem tiltson kifizetést és indítson explicit state transitiont.

## 6. Pénzügyi elemzés

### 6.1 A verification gazdaságtana a jelenlegi paraméterekkel

A szimulátor 18%-os samplinget, 7 fős committee-t és 12%-os platform take-rate-et feltételez.

Ha minden mintázott feladatot mind a hét verifier teljesen újrafuttat:

R = 1 + 0,18 × 7 = 2,26 végrehajtás egy hasznos compute-egységre.

Ha az alap worker payout a vevői ár 88%-a:

CM = 1 − 2,26 × 0,88 = −98,88%.

Még ha a mintázott jobot csak egyetlen verifier futtatja újra:

R = 1,18, és CM = 1 − 1,18 × 0,88 = −3,84%.

Ez relay, storage, settlement, support, fraud és payroll előtt negatív. Következésképp a verification nem lehet ingyenes háttérréteg.

Helyes customer price:

P_customer = verification multiplier × worker price + relay + storage + settlement + risk reserve + protocol margin.

Kell:

- külön security/verification surcharge;
- job value és verification tier;
- olcsó signature/hash ellenőrzés;
- ritkább teljes re-execution;
- challenge-triggerelt mély ellenőrzés;
- magas értékű munkánál quorum vagy teljes duplikáció.

### 6.2 Egyszerű platformbevétel

0,30 USD/GPU-óra és 12% take mellett a platform bruttó bevétele csak 0,036 USD/GPU-óra, még minden egyéb költség előtt.

| Fizetett GPU-óra/hó | Bruttó platformbevétel/hó |
|---:|---:|
| 10 000 | 360 USD |
| 100 000 | 3 600 USD |
| 1 000 000 | 36 000 USD |

Ha ennek csak 50%-a contribution margin és a havi burn 30 000 USD, hozzávetőleg 1,67 millió fizetett GPU-óra/hó kell a nullszaldóhoz. Ez mutatja, miért fontos a magasabb értékű vertical SaaS és verified-compute díj.

### 6.3 Bottom-up üzleti forgatókönyvek

| Szcenárió | Fizető ügyfél | Átlagos havi compute-GMV | Éves GMV | Platformbevétel |
|---|---:|---:|---:|---:|
| Pilot | 25 | 300 EUR | 90 000 EUR | 13 500 EUR, 15% take mellett |
| Beachhead | 200 | 1 000 EUR | 2,4 M EUR | 288 000 EUR, 12% take mellett |
| Erős niche | 1 000 | 2 500 EUR | 30 M EUR | 3 M EUR, 10% take mellett |

Ezek aritmetikai szcenáriók, nem bevételi előrejelzések.

### 6.4 Reális bevételi modell

A token nem revenue model. Ajánlott:

- compute marketplace fee: 8–12%;
- verification cost plusz 10–20% markup;
- Developer/FlowMate runner: 99–499 EUR/hó + usage;
- Quant/AI team: 500–2 500 EUR/hó + usage;
- private enterprise cluster: 2 000–20 000 EUR/hó;
- SLA, prioritás és hosszabb receipt retention;
- storage/egress pass-through;
- auditálható receipt/attestation szolgáltatás.

A slashing ne legyen tervezett bevétel; a károsult és az insurance fund védelmét szolgálja.

### 6.5 Node unit economics

Egy RTX 4090 hivatalos teljesítménykerete 450 W. [NVIDIA](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4090/) Az EU 2025 második félévi átlagos lakossági áramára 0,2896 EUR/kWh volt. [Eurostat](https://ec.europa.eu/eurostat/web/products-eurostat-news/w/ddn-20260505-1)

Csak a GPU áramköltsége:

0,45 kW × 0,2896 EUR/kWh ≈ 0,130 EUR/óra.

A teljes gép, hűtés, amortizáció, downtime, javítás és adó ezt növeli. A RunPod jelenlegi hivatalos model page-e az RTX 4090 community cloudot 0,34 USD/óra körüli induló áron mutatja, így az európai otthoni node marginja könnyen nagyon szűk. [RunPod RTX 4090](https://www.runpod.io/gpu-models/rtx-4090)

Az ellátás első célpontja inkább:

- olcsó energiájú régió;
- már amortizált professzionális géppark;
- kisebb adatközpont;
- whitelisted provider.

Nem célszerű garantált passzív jövedelmet ígérni gamer PC-tulajdonosoknak.

### 6.6 Fejlesztési költség és idő

| Szint | Idő | Reális költség |
|---|---:|---:|
| Hardened determinisztikus PoC/private alpha | 3–5 hónap | 40 000–120 000 USD |
| Permissioned commercial beta | 6–9 hónap összesen | 250 000–650 000 USD |
| Auditált permissionless public beta | 12–18 hónap | 1–2,5 M USD |
| Multi-chain/tokenizált expansion | 18–30 hónap | 2,5–6 M+ USD |

Egy founder-unpaid kísérlet készpénzigénye alacsonyabb lehet, de ez nem a munka gazdasági értéke. AI coding agent gyorsíthatja a fejlesztést, de nem helyettesíti a security auditot, jogi vizsgálatot, SRE-t, supportot és customer acquisitiont.

## 7. Piaci elemzés

### 7.1 A piac valós, de a TAM-mal óvatosan

Az AI-, cloud- és adatközpontpiac óriási, de ezekből nem következik, hogy a HDCN közvetlenül billió dolláros TAM-mal rendelkezik. A decentralizált compute tényleges, nyilvánosan látható forgalma nagyságrendekkel kisebb.

Az Akash saját 2025-ös jelentése 3,15 millió USD éves spendet, 126 025 új lease-t és 60%-os átlagos GPU-kihasználtságot közöl; az aktív deploymentek száma ugyanakkor év végére 1 330-ra esett. [Akash 2025](https://akash.network/blog/akash-2025-year-in-review/)

A Vast.ai saját közlése 14 000 feletti fizető havi aktív ügyfelet és egymillió USD feletti havi bevételt említ; ez vállalati, nem auditált adat. [Vast.ai growth report](https://vast.ai/article/ramp-brex-fastest-growing-vendor)

A tanulság: van fizető kereslet, de a supply felépítése könnyebb, mint stabil, visszatérő vevői keresletet és jó unit economicst szerezni.

### 7.2 Versenytér

| Szereplő | Fő pozíció | HDCN-következmény |
|---|---|---|
| Akash | Általános Docker cloud, reverse auction és tokenes settlement | Generic marketplace esetén közvetlen, érettebb versenytárs |
| Vast.ai | Nagy third-party GPU kínálat és árverseny | Puszta árban nehéz legyőzni |
| RunPod | Fejlesztőbarát, olcsó GPU cloud | A normál cloud UX a minimum elvárás |
| Render | Rendering és generatív média vertikum, BME modell | A specializáció erejét bizonyítja |
| Gensyn | Decentralizált ML és verification kutatás/testnet | Középtávú technológiai versenytárs |
| io.net/Aethir/Nosana | GPU/AI cluster és DePIN supply | Erős supply- és token-verseny |
| Bacalhau/Expanso | Compute-over-data, Docker/WASM | Technikailag közel áll a determinisztikus irányhoz |
| Bittensor | Mérhető digitális commodity subnetek | Későbbi integráció lehetséges, de nem shortcut a PMF-hez |
| Livepeer | Vertikális video/AI pipeline | További bizonyíték a vertical wedge mellett |

Az Akash 2026-ban burn-mint equilibrium modellt vezetett be, ahol a felhasználó USD-áras creditet kap az AKT burn után; ez mutatja, hogy az ügyfelek stabil árának és a volatilis tokennek az összehangolása egy érett hálózatnak is komoly probléma. [Akash BME](https://akash.network/blog/what-burn-mint-equilibrium-means-for-akash/)

A Render szintén USD-hez kötött compute credit/BME logikát használ, és a vertikális renderből bővíti az általánosabb AI/ML workloadot. [Render BME](https://know.rendernetwork.com/basics/burn-mint-equilibrium), [Render AI/ML](https://know.rendernetwork.com/getting-started/generative-workflows-on-the-render-network)

### 7.3 A legjobb beachhead

Nem ajánlott:

- általános olcsó GPU marketplace;
- frontier LLM distributed training;
- élő trading execution;
- nyolcláncos tokenes DePIN launch.

Ajánlott:

> **Reprodukálható és ellenőrizhető batch-compute heterogén infrastruktúrán, elsőként kvantitatív kutatáshoz, backtesthez és szimulációhoz.**

Jó első workloadok:

- FlowMate OHLCV backtest-mátrix;
- EventTape replay shardok;
- CPCV foldok;
- PBO/DSR és Monte Carlo;
- paraméter- és feature search;
- economic/protocol simulation;
- CI/fuzzing és open-science batch feladatok.

A frontier szinkronizált LLM-training nem illik szétszórt home node-okhoz. A modern klaszterek nagyon nagy GPU–GPU és hálózati sávszélességre támaszkodnak; egy DGX H100 például 900 GB/s NVLink és 400 Gb/s InfiniBand kategóriájú kapcsolatokat használ. [NVIDIA DGX H100](https://docs.nvidia.com/dgx/dgxh100-user-guide/introduction-to-dgxh100.html)

### 7.4 Go-to-market

Első 90 nap:

- 20 probléma- és willingness-to-pay interjú;
- 5 design partner, legalább 3 fizető;
- 10–20 ellenőrzött node;
- 500–1 000 valós job;
- FlowMate mint dogfood, de legalább 3 külső use case;
- tokenjutalom nélkül.

Pilot acceptance gate:

- legalább 99% job completion;
- P95 start 60 másodperc alatt a támogatott kategóriában;
- referenciajoboknál 100% reprodukálható receipt;
- legalább 30% repeat usage;
- pozitív contribution margin a verification után;
- legalább 30% megtakarítás vagy dokumentált audit/reproducibility többletérték.

## 8. Saját token elemzése

### 8.1 Technikai megvalósíthatóság

Igen, a HDCN összeköthető saját ERC-20, Solana SPL vagy más tokennel. Ez egyszerűbb feladat, mint egy biztonságos compute- és settlement-hálózat felépítése. A technikai lehetőség ezért nem üzleti indok.

### 8.2 Miért nem ajánlott most?

- nincs igazolt külső kereslet vagy product–market fit;
- nincs permissionless security protocol;
- nincs auditált staking/slashing;
- USDC vagy fiat megoldja az ügyfél- és providerfizetést;
- a volatilis stake értéke támadáskor eshet;
- a token növeli a compliance-, oracle-, treasury-, liquidity- és governance-kockázatot;
- a tokeneladás elrejtheti a negatív unit economicst;
- a spekulatív narratíva elvonhatja a figyelmet a termékről.

### 8.3 Ajánlott token-lépcső

**0. szakasz:** nincs kibocsátott token vagy cash-outolható credit. USD-alapú quote, belső usage metering, USDC/fiat settlement.

**1. szakasz:** jogi vizsgálat után esetleg nem transzferálható szolgáltatási credit, visszaváltási vagy értékgarancia nélkül.

**2. szakasz:** transferable token csak organikus használat, security need, audit és jogi memo után.

Javasolt tokenkapu:

- legalább 12 hónap működő szolgáltatás;
- 6–12 hónapon át legalább 500 000 EUR havi organikus GCV;
- legalább 50 fizető szervezet;
- legalább 500 gazdaságilag független worker;
- 90 napos ügyfélretention 60% felett;
- top-10 provider kapacitása 35% alatt;
- verification utáni pozitív contribution margin;
- két független audit;
- 24 hónap fiat/stablecoin runway tokeneladás nélkül;
- írásos MiCA/MiFID/PSD2 classification memo.

### 8.4 Értelmes későbbi utility

- worker/verifier security bond;
- challenge collateral;
- korlátozott governance;
- fee rebate vagy capacity priority;
- kiegészítő, nem elsődleges provider incentive.

Az ügyfél továbbra is fiatban vagy USDC-ben fizessen. A work payout elsődlegesen valódi bevételből, stablecoinban történjen. Ne legyen árfolyamígéret, garantált hozam, profit-share vagy korlátlan emission.

A bond először USD/USDC-alapú legyen:

RequiredBond ≥ gamma × max(JobValue, CheatGain).

Ha később token is része a collateralnak, erős volatility haircut és részben stablecoin bond szükséges. A reputáció ne legyen transzferálható.

### 8.5 EU/MiCA

A repository jogi állításai közül több túl kategorikus. A nem transzferálható credit lehet MiCA-n kívüli, de ettől még PSD2, e-money, fogyasztóvédelmi vagy nemzeti szabály alkalmazható. Az algoritmikus tokenek sincsenek általánosan betiltva; a besorolás az értékstabilizáció és a jogosultságok tényleges szerkezetétől függ.

A MiCA crypto-asset, utility token, ART és EMT definícióit a [MiCA 3. cikke](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02023R1114-20240109) tartalmazza. Profit-share vagy befektetési jelleg esetén MiFID szerinti pénzügyi eszközminősítés is felmerülhet. [ESMA iránymutatás](https://www.esma.europa.eu/document/guidelines-conditions-and-criteria-qualification-crypto-assets-financial-instruments)

Az MVP legkisebb jogi kockázatú formája:

- nincs saját kibocsátott credit/token;
- non-custodial escrow;
- USDC/fiat fizetés;
- nincs saját swap vagy bridge;
- szabályozott partner a váltáshoz;
- public beta előtt EU-s jogi memo.

## 9. Crypto network integráció

### 9.1 Ajánlott láncsorrend

| Lánc | Ajánlott szerep | Döntés |
|---|---|---|
| Base | Első escrow és USDC settlement | **Igen, elsőként** |
| Ethereum L1 | Ritka high-value root anchor/dispute | **Igen, de nem per-job** |
| Solana | Második adapter, ha van mért igény | **Később** |
| Sui | Csak külön ügyféligénynél | **Halasztani** |
| BNB | Későbbi EVM adapter, corridor ellenőrzéssel | **Halasztani** |
| Saját L1 | Saját consensus, validator és bridge | **No-Go** |

### 9.2 Base MVP

Először Base Sepolia same-chain escrow:

- allowlisted natív USDC;
- OpenZeppelin SafeERC20;
- determinisztikus escrow ID;
- EIP-712 typed acceptance;
- explicit chain ID, verifying contract, network ID, receipt root, committee snapshot, expiry és nonce;
- külön consumed nonce, mert az EIP-712 önmagában nem replay-védelem. [EIP-712](https://eips.ethereum.org/EIPS/eip-712)
- permissioned beta alatt multisig vagy allowlisted verifier threshold;
- append-only epoch checkpoint;
- Foundry unit, fuzz, invariant és fork tesztek;
- admin multisig, hardware wallet és timelock;
- node daemonban soha nincs deployer/admin key.

A Base L2 olcsó és EVM-kompatibilis, de a sequencer inclusion, safe és Ethereum-finalized állapot nem azonos; a settlement state machine ezt külön kezelje. [Base finality](https://docs.base.org/base-chain/network-information/transaction-finality)

### 9.3 Solana

Későbbi Solana adapter:

- PDA-alapú escrow;
- allowlisted klasszikus USDC mint;
- TransferChecked;
- initialize/accept/refund/close state machine;
- exact account owner, signer, seeds, bump, mint és token program validation;
- Ed25519 instruction és message binding ellenőrzés;
- finalized commitment pénzügyi állapotnál.

Források: [Solana PDA](https://solana.com/docs/core/pda), [Solana fees](https://solana.com/docs/core/fees).

### 9.4 Cross-chain

Saját bridge helyett CCTP vagy más auditált, támogatott rendszer. A Circle aktuális listája alapján Base, Ethereum és Solana támogatott USDC CCTP útvonalak; Sui legacy V1, BNB V2-n pedig jelenleg USYC és nem natív USDC szerepel. [Circle supported chains](https://developers.circle.com/cctp/concepts/supported-chains-and-domains)

A CCTP is külső trust és operational dependency, valamint finality- és retry-state machine-t igényel. [Circle finality](https://developers.circle.com/cctp/concepts/finality-and-block-confirmations)

Ajánlott:

- ugyanazon láncú settlementtel indulni;
- payout batch/netting;
- egyetlen canonical token home chain;
- cross-chain csak mérhető volumen után;
- saját bridge-et nem építeni.

## 10. FlowMate integráció

### 10.1 Rövid válasz

Igen, a két projekt technikailag és stratégiailag jól összeköthető. A HDCN proto már tartalmaz FlowMateBacktest workload típust, a FlowMate fő ágán pedig létezik EventTape, orderflow bridge, CPCV/DSR/PBO gate és edge-search infrastruktúra. [FlowMate repository](https://github.com/Matesensei/FlowMate_Trading_Assistant)

Az integráció azonban kizárólag offline research/backtest útvonal legyen. A HDCN ne kerüljön az élő market-data, signal, risk vagy order execution kritikus útjába.

### 10.2 Ajánlott architektúra

~~~mermaid
flowchart TD
  F["FlowMate koordinátor"] --> M["Aláírt job manifest"]
  M --> H["HDCN scheduler"]
  H --> W["Izolált worker pool"]
  W --> V["Független ellenőrzés"]
  V --> R["Receipt + eredmény-root"]
  R --> G["FlowMate research gate"]
  R --> E["Base USDC escrow"]
~~~

### 10.3 BacktestJobSpec

A FlowMate készítsen egy aláírt job specet legalább ezekkel:

- FlowMate repository commit;
- container vagy WASM module digest;
- engine és gate verzió;
- EventTape/dataset Merkle root;
- venue, symbol és time range;
- strategy ID és paraméterek;
- determinisztikus seed;
- fee, slippage és latency model;
- tick/lot, rounding és numeric profile;
- resource limit;
- output schema;
- privacy class;
- verification tier;
- price, escrow ID, deadline és nonce.

A worker eredménycsomagja:

- trades digest;
- equity curve digest;
- metrics;
- CPCV/PBO/DSR/gate evidence;
- logs és artifact root;
- signed WorkerReceipt.

A verifier készítsen külön AcceptanceCertificate-et. Az elfogadott eredmény a FlowMate research registrybe kerülhet, de soha ne váljon automatikusan paper vagy live stratégiává.

### 10.4 Determinizmus

A jelenlegi Python/Pandas/NumPy/BLAS backtest nem garantáltan byte-identikus különböző hardveren. Kétfázisú megoldás:

**MVP:** whitelisted, homogén OCI image, pinelt dependency, fix seed és rounding; szemantikai hash és toleranciaalapú ellenőrzés.

**Hosszú táv:** a kritikus backtest kernel Rust/fixed-point/WASM implementációja, stabil reducer sorrenddel.

Ezért az első FlowMate output research evidence, nem settlement-grade truth.

### 10.5 Jó és tiltott workloadok

| Jó első workload | Ne kerüljön HDCN-re |
|---|---|
| OHLCV backtest matrix | Élő websocket feed |
| EventTape replay shard | Order execution |
| CPCV/PBO/DSR | Exchange vagy wallet key |
| Monte Carlo | Sub-second signal path |
| Paraméter- és feature search | Licencileg nem továbbítható adat |
| ML training publikus vagy engedélyezett adattal | Titkos stratégia untrusted home node-on |

## 11. Stratégiai elemzés

### 11.1 Pozicionálás

Rossz pozicionálás:

> újabb olcsó decentralizált GPU marketplace saját tokennel.

Ajánlott pozicionálás:

> **HDCN reprodukálható, bizonyítható batch-compute-ot nyújt heterogén infrastruktúrán, elsőként kvantitatív kutatáshoz és szimulációhoz.**

A legerősebb kezdeti architektúra egy verification/control plane. Először whitelisted saját node-okat és akár meglévő compute provider adaptereket aggregáljon. A permissionless home-node supply később legyen egy adapter, ne a teljes termék első napi feltétele.

### 11.2 Stratégiai trackek

| Track | Döntés | Indok |
|---|---|---|
| A. Determinisztikus CPU/WASM + FlowMate | **Most ezt** | Szűk, mérhető, párhuzamosítható, auditálható |
| B. Általános render/AI GPU marketplace | **Halasztani** | Nagyon erős verseny és gyenge differenciálás |
| C. Saját L1, token, bridge | **Elutasítani most** | Nagy security/capital burden, nincs vevőérték |
| D. Permissionless GPU payout | **Kutatás később** | Verification és unit economics még megoldatlan |

A nyitott [Issue #2](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/issues/2), a determinisztikus WASM executor és lokális verifier, a helyes következő product step. Előtte vagy vele párhuzamosan azonban a proto-v2 és a security hardening szükséges. A saját L1/token/bridge [Issue #3](https://github.com/Matesensei/Hybrid_Decentralized_Compute_Network/issues/3) jelenleg research-only maradjon.

### 11.3 Fő kockázatok

1. Cold start: node-ot könnyebb találni, mint fizető ügyfelet.
2. Árverseny: a generic 4090 compute már nagyon olcsó.
3. Verification COGS: a teljes újrafuttatás eltünteti a margin nagy részét.
4. Adat- és IP-szivárgás.
5. Heterogén node reliability és benchmark gaming.
6. Készletillúzió: headline price mellett nincs használható availability.
7. Tokenes UX és compliance.
8. Bridge/contract exploit.
9. Magas EU home-node energiaár.
10. Provider-koncentráció és álfüggetlen Sybil node-ok.
11. Nondeterminisztikus GPU eredmények.
12. FlowMate dogfood nem azonos külső PMF-fel.

### 11.4 Védhető moat

Nem a token és nem önmagában az olcsó GPU a moat. Védhetőbb lehet:

- reproducibility certificate;
- workload-specific deterministic execution profile;
- cross-provider verification;
- FlowMate és más research workflow integráció;
- artifact/receipt provenance;
- megbízhatósági és fraud dataset;
- private pool és később TEE;
- normál cloud UX és stable pricing;
- provider- és chain-absztrakció.

## 12. Prioritásos fejlesztési terv

### P0 — 0–6 hét

1. A szimulátor double-entry accountingra átírása és pénzmegmaradási tesztek.
2. Verification-cost és security-tier beépítése.
3. Ed25519 strict sign/verify, public-key identity és tampered test.
4. Domain-separated proto-v2, bounded decoding, replay/expiry/nonce.
5. WorkerReceipt és AcceptanceCertificate szétválasztása.
6. Job és escrow state machine specifikáció.
7. License rendezése.
8. Rust toolchain, dependencies és GitHub actionök pinelése.
9. AI workflow permission minimalizálása.
10. sim-dispatch input validation.
11. Threat model és security invariant dokumentum.

**P0 exit gate:** nincs kritikus statikus protocol/CI finding; a szimulátor accounting invariánsai minden tesztben teljesülnek.

### P1 — 6–14 hét

1. Determinisztikus Wasmtime executor.
2. Lokális verifier és kétfüggetlen-futás összehasonlítás.
3. iroh coordinator/worker 3–10 whitelist node-dal.
4. Tartós job state és idempotency.
5. Egy FlowMate read-only workload adapter.
6. Homogén, pinelt container profile.
7. Cross-machine golden és fuzz teszt.
8. Nincs token és nincs on-chain settlement.

**P1 exit gate:** legalább 1 000 sikeres, reprodukálható belső job; 99% feletti completion; mért cost/job.

### P2 — 3–6 hónap

1. Receipt/artifact store és canonical checkpoint.
2. Capability registry, scheduler, quotas és rate limit.
3. Telemetry, failure recovery és dispute flow.
4. Base Sepolia escrow + Foundry invariant/fuzz test.
5. 5–20 node-os pilot.
6. Benchmark RunPod/Vast ellen.
7. Három külső design partner.

**P2 exit gate:** pozitív contribution margin legalább egy verification tiernél; nincs kritikus security finding; legalább három visszatérő külső pilot.

### P3 — 6–12 hónap

1. Fizetős private beta USDC-ben.
2. 20–50 whitelisted provider.
3. SLA, support, privacy class és legal/compliance.
4. Külső contract és protocol security review.
5. Base mainnet csak alacsony capekkel.
6. Insurance/dispute reserve.

**P3 exit gate:** 3–5 fizető design partner, ismételt használat, legalább hat hónap stabil unit economics előtt nincs permissionless launch.

### P4 — 12–18+ hónap

1. Permissionless registry és stake/dispute.
2. GPU statistical verification.
3. Solana adapter.
4. CCTP csak szükséges route-okra.
5. TEE/confidential tier.
6. Független audit és bug bounty.
7. Token-döntés csak a korábban leírt üzleti és jogi kapuk után.

## 13. Mit javítanék elsőként a kódban?

A legjobb első fejlesztési csomag nem token- vagy chain-PR:

1. **P0 security/CI hardening PR**
   - action SHA pin;
   - permission minimum;
   - sim-dispatch validáció;
   - toolchain/dependency lock;
   - license tisztázása.

2. **proto-v2 PR**
   - domain-separated envelope;
   - valódi Ed25519;
   - bounded decode;
   - full JobSpec;
   - WorkerReceipt/AcceptanceCertificate;
   - replay és crypto agility.

3. **simulator accounting PR**
   - double-entry ledger;
   - verifier COGS;
   - settlement/relay/storage;
   - calibrated scenarios és sensitivity.

4. **executor/verifier vertical slice**
   - determinisztikus WASM;
   - három gép;
   - egy FlowMate backtest;
   - signed receipt;
   - még chain és token nélkül.

Ezek után jöhet Base Sepolia.

## 14. Végső döntés

### Go

Egy 3–6 hónapos, szűk private MVP:

- FlowMate batch backtest;
- determinisztikus CPU/WASM;
- 3–10 whitelisted node;
- nincs live trading;
- nincs token;
- nincs saját chain;
- nincs permissionless worker;
- 1 000+ mérhető job;
- valódi verification cost;
- külső design partner interjú.

### Feltételes Go

Base Sepolia escrow, miután az off-chain receipt és state machine stabil. Base mainnet csak audit, limitált cap és fizető pilot után. Solana csak valós igény után.

### No-Go jelenleg

- saját L1;
- saját bridge;
- nyolcláncos parallel deployment;
- liquid token;
- compute-peg és cash-out guarantee;
- buyback floor;
- permissionless mainnet;
- untrusted GPU inference payout;
- élő trading a HDCN-en;
- tokenértékesítésből finanszírozott product–market fit.

## Konklúzió

A HDCN-ben van életképes projektmag, de nem ott, ahol a legnagyobb crypto narratíva csábít. A jelenlegi legjobb út:

> **FlowMate által validált, determinisztikus és auditálható batch-compute szolgáltatás → whitelisted private network → Base USDC settlement → külső fizető ügyfelek → később permissionless supply → és csak ezután esetleges token.**

Ha ezt a sorrendet tartják, a projektből lehet értékes verifiable-compute termék még akkor is, ha soha nem készül saját token vagy saját lánc. Ha tokennel, bridge-dzsel és több lánccal indul, a security-, compliance- és likviditási kockázat valószínűleg megelőzi a termék- és bevételi validációt.
