# Decentralizált GPU Compute Hálózat (DePIN) — Teljes Technikai Architektúra és Megvalósítási Terv

## Executive Summary (Vezetői összefoglaló)

Ez a jelentés egy decentralizált GPU compute hálózat (DePIN) teljes architektúráját tervezi meg, ahol minden NVIDIA GPU-val rendelkező PC mikro-node-ként működik. Fő ajánlásom: **kezdd a Version A (Sui-alapú settlement) architektúrával, a 3D rendering (Blender Cycles) verticalra fókuszálva MVP-ként, no-token fee-only modellel (SUI/USDC).** Saját L1 (B1) építése egy solo fejlesztőnek irreális; a minimális proof-of-compute gossip réteg (B2) csak később, opcionálisan indokolt.

### TL;DR
- **Architektúra:** A Sui-alapú settlement (Version A) a helyes választás — a P2P compute réteg egyedi Rust/libp2p/QUIC, de minden pénzügyi elszámolás Sui Move szerződéseken fut. Saját BFT L1 (B1) egy solo devnek 2-4 év és értelmetlen; a lightweight proof-of-compute gossip (B2) csak kiegészítő finality/DA rétegként éri meg.
- **Vertical:** Batch rendering vagy ZK proving az MVP-hez — mindkettő latency-toleráns (otthoni kapcsolatnak megfelelő) és jól verifikálható; a ZK proof self-verifying, a rendering perceptual-hash-elhető. Az AI inference a legnehezebben verifikálható és latency-érzékeny.
- **Gazdasági realitás:** Egy otthoni RTX 4090 reálisan ~120-180 USD/hó bruttót termel a legjobb DePIN platformokon, de EU áramáron (0,25-0,40 €/kWh) a nettó nagyjából nullszaldó és ~50 €/hó között van — a hálózat értékajánlata az idle hardver monetizálása, nem a profit.

---

## Deliverable 2: Három Workload Vertical Egyenrangú Összehasonlítása

Az MVP vertical kiválasztása a legfontosabb stratégiai döntés. Három jelöltet hasonlítok össze egyenrangúan: AI inference, 3D rendering, ZK proving.

### 2.1 Piaci kereslet 2025-2026

**AI Inference:** A legnagyobb és leggyorsabban növő piac. Az io.net több mint 100 000 GPU-t aggregál; 2025 októberében jelentett ~20M USD annualizált on-chain bevétel-mérföldkövet (OurCryptoTalk, 2026), ~72%-os megtakarítással az AWS-hez képest. 2026 júniusi frissebb adat szerint egy $8M-os üzlet ~$650 000 havi on-chain bevételt ad hozzá, és a hálózat napi 4 milliárd+ AI tokent dolgoz fel; az első IO token burn 2026. június 11-én történt. Az Aethir a 2025-ös hivatalos Wrap-Up blogja szerint (aethir.com) $127,8M+ bevételt jelentett (jan-dec 2025), $166M ARR-rel Q3-ra, 435 000+ GPU konténerrel 93 országban — **fontos: ez teljesen önbevallott, nem on-chain auditált** (az Own Your Mind review megjegyzi: "zero independent verification"). A hyperscaler H100 óradíj 4,50-5,50 USD sávban; DePIN-en H100 1,20-1,80 USD/óra (Akash). Consumer GPU inference: pl. Llama 4 Scout RTX 4090-en ~0,0003 USD/M input token elektromos költség, szemben a ~2 USD/M GPT-4.1-osztályú API-val.

**3D Rendering:** Kisebb, de érett és fizetőképes piac. A globális 3D rendering piac becslései szórnak: a Global Market Insights szerint 2023-ban 4,4 Mrd USD, 25% CAGR-rel 2024-2032 között; az SNS Insider szerint 4,07 Mrd USD (2023) → 23,02 Mrd USD (2032), 21,27% CAGR; a Brainy Insights a legmagasabb, ~34,57 Mrd USD/2032 (27,67% CAGR). Render Network: $0,69/GPU-óra (vs AWS A10G $1,01/óra). OctaneBench-óra alapú árazás; render farmok GPU ára 0,004-0,008 USD/OB-óra (GarageFarm, RebusFarm). A Render Network 2025-ben 5 637 150 RENDER token emissziót adott ki, és 63M+ frame-et renderelt kumulatívan.

**ZK Proving:** Kicsi, de gyorsan növekvő és a legjobban a crypto gazdasághoz illeszkedő piac. A Succinct Prover Network mainnet-je 2025. augusztus 5-én indult (CEO Uma Roy, CTO John Guibas — "whitepaper to working mainnet in eight months"); a hivatalos közlemény szerint 35+ vezető protokollt szolgál ki, 1 700 egyedi program proofjait dolgozza fel, és 4 Mrd+ USD értéket biztosít (Polygon, Mantle, Celestia, Lido), több mint 5 millió teljesített prooffal. OP Succinct költségstruktúra: $0,0102/tranzakció, $0,0184/MGas. A Brevis ProverNet Pico Prism 64×RTX 5090 GPU klaszterrel real-time Ethereum block proofot ért el. A Succinct all-pay auction ("proof contest") mechanizmust használ, PROVE token staking-gel.

### 2.2 Technikai megvalósíthatóság consumer NVIDIA GPU-n (RTX 3060-4090)

**AI Inference:** VRAM a korlát. 8GB (RTX 3060/4060): 7-8B modellek Q4_K_M-en (Qwen3-8B Q4_K_M = 5,03 GB). 12GB (RTX 3060 12GB): 13B modellek. 24GB (RTX 3090/4090): akár 32B modellek Q4_K_M-en (Qwen3-32B Q4_K_M = 19,76 GB), MoE-k mint Qwen3-30B (19GB, csak 3B aktív param). 70B modell nem fér el egy 24GB kártyán (~40-48GB kell). KV cache 15-100% overhead a kontextushossztól függően. RTX 4090 ~40-50 tokens/sec 30B modellen.

**3D Rendering:** Licensz a fő kérdés. OctaneRender és Redshift kereskedelmi licenszet igényelnek; **Blender Cycles nyílt forráskódú és ingyenes** — ez a helyes választás egy permissionless hálózathoz. Cycles OptiX hardveres ray tracinget használ NVIDIA-n. Fontos: Octane GPU-only, nincs CPU fallback; EEVEE nem fut headless node-on (display context kell), tehát Cycles-re kell konvertálni.

**ZK Proving:** MSM (multi-scalar multiplication) és NTT (number-theoretic transform) a GPU-gyorsítható bottleneck-ek. GPU-barát rendszerek: Groth16, Plonk-variánsok, és a zkVM-ek (SP1, Pico) amelyek RISC-V programokat bizonyítanak Rustban. STARK-ok memória-intenzívebbek. A Brevis Pico Prism RTX 5090-eket használ (32GB), ami mutatja, hogy consumer GPU életképes, de a nagyobb proofok VRAM-igényesek.

### 2.3 Verifikálhatóság — a legfontosabb megkülönböztető

Ez a decentralizált hálózat legkritikusabb tulajdonsága, és itt drámai különbség van a három vertical között:

- **ZK Proving — TRIVIÁLISAN verifikálható (óriási előny):** A ZK proof definíció szerint self-verifying. A hálózatnak nem kell újraszámolnia semmit — a proof ellenőrzése milliszekundumok alatt, olcsón megtörténik (akár on-chain). Nincs szükség redundáns végrehajtásra, TEE-re vagy challenge window-ra a korrektség igazolásához. Ez messze a legjobban illeszkedik egy trustless hálózathoz.
- **3D Rendering — KÖNNYEN spot-checkelhető:** A kimenet determinisztikusabb, és perceptual hash / részleges újrarenderelés (pl. random tile-ok újraszámítása egy verifier node-on) hatékony. A Render Network manuális creator jóváhagyást használ (72 óra után auto-approve).
- **AI Inference — NEHEZEN verifikálható:** Ez a legnagyobb kihívás. Megközelítések: (1) redundáns inference + logit összehasonlítás toleranciával; (2) Gensyn RepOps/Verde — bitwise reprodukálható operátorok fix FP execution order-rel; (3) Prime Intellect TOPLOC — locality-sensitive hashing, ami tamper-t/precíziós eltérést detektál non-determinisztikus GPU-n; (4) TEE attestation (csak H100/H200); (5) optimistic verification (Ora/opML stílus) challenge window-val.

### 2.4 Determinizmus problémák

A CUDA floating-point non-determinizmus a központi probléma minden verifikációnál. Források: GPU architektúra, driver verzió, CUDA/cuDNN library különbségek, párhuzamos redukciók sorrendje. Megoldások: (1) fix seed-ek; (2) determinisztikus kernelek / fix execution order (Gensyn RepOps FP32-re, IEEE-754 compliance); (3) tolerancia-alapú összehasonlítás; (4) integer/fixed-point aritmetika. **Rendering:** Cycles path tracing seed-elhető, de a Monte Carlo mintavételezés miatt tolerancia kell. **ZK:** teljesen determinisztikus (a proof vagy érvényes, vagy nem). **Inference:** a legrosszabb — ezért a TOPLOC/RepOps megközelítés.

### 2.5 Latency tolerancia

- **AI Inference:** ALACSONY latency kell (interaktív chat), ami az otthoni feltöltési sávszélesség és NAT miatt PROBLÉMÁS. Batch inference (pl. embeddings, szintetikus adat generálás) viszont megfelelő.
- **3D Rendering:** BATCH — tökéletes otthoni node-oknak. Nincs latency-nyomás.
- **ZK Proving:** BATCH (bár egyes use case-ek mint PancakeSwap VIP sub-second proofot kérnek) — általában jól illeszkedik.

### 2.6 Verseny verticalonként

- **Inference/általános compute:** io.net, Akash, Nosana, Gensyn, Prime Intellect, Salad, Vast.ai, Aethir — **zsúfolt**.
- **Rendering:** Render Network dominancia (63M+ frame), de a piac szűkebb és specifikusabb; a Render most AI-ra is terjeszkedik (Dispersed subnet).
- **ZK Proving:** Succinct Prover Network, Brevis ProverNet, Fermah, Gevulot, =nil; — **feltörekvő, kevésbé telített**, de erősen technikai.

### 2.7 Bevételi realizmus otthoni consumer GPU-kra

Konkrét, forrásolt számok (2025-2026):
- **Salad:** RTX 4090 hivatalos videó szerint (Facebook/saladchefsapp): "Earn With Your RTX 4090 – Earn Up to $150/Month" — a felső határ óvatosan ~$150/hó (~4-5 USD/nap), balance/gift card fizetéssel. (A salad.com/download-high-end oldal "up to $180"-at is említ.)
- **Vast.ai:** RTX 4090 ~6 USD/nap bruttó (verified, RedPandaMining 2026 májusi dashboard videója alapján), ~50-60 USD/hó nettó (US áram); rate $0,32-0,49/óra. Kritikus: verifikáció nélkül ~0,05 USD/nap ugyanarra a kártyára.
- **Nosana:** RTX 4090 $0,32/óra rental rate, de alacsony kihasználtság (7/39 host rented a mintavételkor).
- **io.net:** consumer kártyák ritkán kapnak fizetős jobot, főleg idle block reward IO tokenben.
- **Render:** OB-alapú, high-end kártyáknak "meaningful side income", mid/low tier alig profitábilis.

**EU áram break-even:** RTX 4090 350-450W. 24/7 futás 400W-on: 9,6 kWh/nap = €2,40-3,84/nap (€0,25-0,40/kWh), ~€75-115/hó. **Verdikt:** EU-ban egyetlen consumer kártya nettó nullszaldó és ~€50/hó között. A margó csak (a) olcsó áram <$0,15/kWh, (b) már birtokolt hardver, (c) verified státusz, (d) skála esetén működik. Egy iparági ökölszabály szerint: "under $0.15/kWh you have real margin, over $0.25/kWh the economics for consumer cards get very hard".

### 2.8 Konklúzió — Ajánlási mátrix

| Kritérium | AI Inference | 3D Rendering | ZK Proving |
|---|---|---|---|
| Piac mérete | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Consumer GPU illeszkedés | ⭐⭐⭐ (VRAM limit) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ (VRAM limit) |
| Verifikálhatóság | ⭐ (nehéz) | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ (self-verifying) |
| Latency illeszkedés (otthoni) | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Verseny (kevesebb=jobb) | ⭐ (zsúfolt) | ⭐⭐ | ⭐⭐⭐⭐ |
| Solo dev megvalósíthatóság | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ (mély kripto tudás) |

**Ajánlás:** MVP-nek **3D rendering (Blender Cycles)** — a verifikálhatóság + latency-tolerancia + nyílt licensz + solo-dev megvalósíthatóság kombinációja a legjobb. A **ZK proving** a legelegánsabb verifikációs modell (érdemes második fázisban hozzáadni), de mély kriptográfiai tudást és szűk piacot jelent. Az **AI inference** a legnagyobb piac, de a verifikációs nehézség és latency miatt a legkockázatosabb solo MVP.

---

## Architektúra Version A — Sui-alapú Settlement (nincs saját L1)

Ez az **ajánlott architektúra**. A P2P compute réteg egyedi Rust, de minden pénzügyi elszámolás (escrow, staking, slashing, payment channel, reward) Sui Move szerződéseken fut.

### 3A.1 Szöveges architektúra diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      SUI BLOCKCHAIN (L1)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ JobEscrow│ │ Staking/ │ │Reputation│ │ PaymentChannel │  │
│  │ (shared) │ │ Slashing │ │ Registry │ │  / Session     │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
│         ▲            ▲            ▲              ▲             │
│         │ Programmable Transaction Blocks (PTB)               │
│         │ Sponsored tx (gas station) + zkLogin onboarding     │
└─────────┼────────────────────────────────────────────────────┘
          │ sui-sdk (Rust) — attestation submit / claim
          │
┌─────────┼────────────────────────────────────────────────────┐
│   OFF-CHAIN P2P COMPUTE NETWORK (Rust node daemon)             │
│                                                               │
│  ┌─────────────┐   libp2p (QUIC/Noise)   ┌─────────────┐     │
│  │ CLIENT node │◄──────gossipsub─────────►│ WORKER node │     │
│  │ (job submit)│   Kademlia DHT discovery │ (GPU exec)  │     │
│  └─────────────┘   DCUtR NAT holepunch    └─────────────┘     │
│         │                                        │            │
│         │           ┌──────────────┐             │            │
│         └──────────►│ VERIFIER pool│◄────────────┘            │
│                     │ (redundant / │                          │
│                     │  spot-check) │                          │
│                     └──────────────┘                          │
│  Walrus: job input/output blob DA (nagy fájlok)               │
└───────────────────────────────────────────────────────────────┘
```

### 3A.2 Job lifecycle szekvencia

1. **Job submit:** Client feltölti a scene fájlt Walrus-ra (blob DA), létrehoz egy `JobEscrow` shared objectet Sui-n (SUI/USDC lockolva), a Walrus blob ID + követelmények (min OctaneBench, VRAM) benne.
2. **Discovery:** Client gossipsub-on hirdeti a jobot; a capability registry alapján matching worker(ök) jelentkeznek.
3. **Assignment:** Worker lockolja a jobot (on-chain claim vagy off-chain lease), letölti a blobot Walrus-ról.
4. **Execution:** Worker rendereli/számol; deterministic seed + tile hash-ek.
5. **Attestation:** Worker feltölti az eredményt Walrus-ra, submitál egy signed compute receiptet (output hash + tile hash-ek) a Sui `JobEscrow`-ba.
6. **Verification (optimistic):** Challenge window (pl. 10 perc). Egy verifier node random tile-okat újraszámol; ha eltérés > tolerancia, fraud proofot submitál → slashing.
7. **Settlement:** Challenge window után a worker claim-eli a paymentet a PTB-ben (escrow release + reputation update egy atomi tranzakcióban).

### 3A.3 Sui Move modul vázlatok

**a) Job Escrow (shared object):**

```move
module gpunet::job_escrow {
    use sui::coin::{Self, Coin};
    use sui::balance::{Self, Balance};
    use sui::sui::SUI;
    use sui::clock::Clock;

    const EWrongWorker: u64 = 1;
    const EChallengeOpen: u64 = 2;
    const ENotExpired: u64 = 3;

    public struct JobEscrow<phantom T> has key {
        id: UID,
        client: address,
        worker: Option<address>,
        payment: Balance<T>,
        walrus_input_id: vector<u8>,   // input blob ID (Walrus)
        result_hash: Option<vector<u8>>,
        walrus_output_id: Option<vector<u8>>,
        min_octanebench: u64,
        min_vram_mb: u64,
        submitted_at_ms: u64,
        challenge_window_ms: u64,
        status: u8,  // 0=open,1=claimed,2=attested,3=settled,4=disputed
    }

    public struct JobCreated has copy, drop {
        job_id: ID, client: address, walrus_input_id: vector<u8>,
    }

    // Client létrehozza a shared escrow objectet
    public fun create<T>(
        payment: Coin<T>, walrus_input_id: vector<u8>,
        min_octanebench: u64, min_vram_mb: u64, challenge_window_ms: u64,
        ctx: &mut TxContext
    ) {
        let job = JobEscrow<T> {
            id: object::new(ctx),
            client: ctx.sender(),
            worker: option::none(),
            payment: payment.into_balance(),
            walrus_input_id,
            result_hash: option::none(),
            walrus_output_id: option::none(),
            min_octanebench, min_vram_mb,
            submitted_at_ms: 0,
            challenge_window_ms,
            status: 0,
        };
        sui::event::emit(JobCreated { job_id: object::id(&job), client: ctx.sender(), walrus_input_id });
        transfer::share_object(job);
    }

    // Worker claim-eli (staking modul ellenőrzi a min stake-et külön PTB lépésben)
    public fun claim<T>(job: &mut JobEscrow<T>, ctx: &TxContext) {
        assert!(job.status == 0, EChallengeOpen);
        job.worker = option::some(ctx.sender());
        job.status = 1;
    }

    // Worker attestál — result hash + output blob
    public fun attest<T>(
        job: &mut JobEscrow<T>, result_hash: vector<u8>,
        walrus_output_id: vector<u8>, clock: &Clock, ctx: &TxContext
    ) {
        assert!(job.worker.contains(&ctx.sender()), EWrongWorker);
        job.result_hash = option::some(result_hash);
        job.walrus_output_id = option::some(walrus_output_id);
        job.submitted_at_ms = clock.timestamp_ms();
        job.status = 2;
    }

    // Settle a challenge window után (PTB-ben reputáció-frissítéssel kombinálva)
    public fun settle<T>(job: &mut JobEscrow<T>, clock: &Clock, ctx: &mut TxContext): Coin<T> {
        assert!(job.status == 2, EChallengeOpen);
        assert!(clock.timestamp_ms() >= job.submitted_at_ms + job.challenge_window_ms, EChallengeOpen);
        job.status = 3;
        let amount = job.payment.value();
        coin::take(&mut job.payment, amount, ctx)
    }
}
```

**b) Staking / Slashing:**

```move
module gpunet::staking {
    use sui::balance::{Self, Balance};
    use sui::sui::SUI;
    use sui::table::{Self, Table};

    public struct StakePool has key {
        id: UID,
        stakes: Table<address, Balance<SUI>>,
        min_stake: u64,
        slash_bps: u64,       // slashing arány basis pointban
        treasury: Balance<SUI>,
    }

    public struct SlashCap has key, store { id: UID }  // csak dispute modul birtokolja

    public fun stake(pool: &mut StakePool, coin: Coin<SUI>, ctx: &TxContext) {
        let addr = ctx.sender();
        if (pool.stakes.contains(addr)) {
            pool.stakes.borrow_mut(addr).join(coin.into_balance());
        } else {
            pool.stakes.add(addr, coin.into_balance());
        }
    }

    // Slashing — csak a SlashCap birtokosa (dispute resolution) hívhatja
    public fun slash(_cap: &SlashCap, pool: &mut StakePool, offender: address) {
        let stake = pool.stakes.borrow_mut(offender);
        let total = stake.value();
        let penalty = total * pool.slash_bps / 10000;
        pool.treasury.join(stake.split(penalty));
    }
}
```

**c) Payment Channel / session-alapú mikrofizetés:**

A gyakori mikro-settlement gázköltsége miatt payment channelt/sessiont használunk. A worker off-chain aláírt "ticketeket" halmoz (monoton növekvő összeg), és csak a session végén settle-el on-chain egyszer.

```move
module gpunet::payment_channel {
    use sui::balance::{Self, Balance};
    use sui::sui::SUI;

    public struct Channel<phantom T> has key {
        id: UID,
        client: address,
        worker: address,
        deposit: Balance<T>,
        claimed: u64,          // eddig kifizetett kumulatív összeg
        nonce: u64,
        expires_at_ms: u64,
    }

    // Worker beváltja a legutolsó signed ticketet (kumulatív összeg + client aláírás)
    // Az aláírás-ellenőrzés a sui::ed25519 / ecdsa modullal történik
    public fun redeem<T>(
        chan: &mut Channel<T>, cumulative_amount: u64,
        client_sig: vector<u8>, ctx: &mut TxContext
    ): Coin<T> {
        // verify_signature(chan.client, cumulative_amount || chan.nonce, client_sig)
        assert!(cumulative_amount > chan.claimed, 0);
        let delta = cumulative_amount - chan.claimed;
        chan.claimed = cumulative_amount;
        coin::take(&mut chan.deposit, delta, ctx)
    }
}
```

**d) Reputation Registry (shared, append-only):**

```move
module gpunet::reputation {
    use sui::table::{Self, Table};

    public struct RepRegistry has key {
        id: UID,
        scores: Table<address, RepEntry>,
    }
    public struct RepEntry has store {
        jobs_completed: u64,
        jobs_failed: u64,
        total_octanebench_hours: u64,
        last_updated_ms: u64,
    }
    // Csak job_escrow settle/dispute hívhatja (witness pattern)
    public fun record_success(reg: &mut RepRegistry, worker: address, obh: u64, ts: u64) { /* ... */ }
    public fun record_failure(reg: &mut RepRegistry, worker: address, ts: u64) { /* ... */ }
}
```

**e) Dispute Resolution:** Optimistic — a challenge window alatt bárki (vagy egy sampled verifier committee) submitálhat fraud proofot (a vitatott tile újraszámolt hash-ét + a Walrus blob referenciát). Ha a fraud proof érvényes, a worker stake-je slashelődik és a client visszakapja az escrow-t.

### 3A.4 Sui-specifikus funkciók kihasználása

- **Owned vs shared objects:** A `JobEscrow` shared (több fél mutálja: client, worker, verifier). A `Channel` és a stake-ek lehetnek owned a hatékonyságért. A shared object konszenzuson megy át (Mysticeti DAG), az owned object fast-path (single-owner) — a mikrofizetéseket owned/channel útvonalon tartsuk.
- **Programmable Transaction Blocks (PTB):** Egyetlen atomi tranzakcióban: claim + reputation check + escrow release + rep update. Ez csökkenti a tranzakciószámot és a gázt.
- **Sponsored transactions (gas station):** A worker node-oknak nem kell SUI-t tartaniuk — a protokoll gas station sponsorálja a claim/attest tranzakciókat. A `GasData` owner ≠ sender. Eszközök: Shinami Gas Station, Mysten Enoki.
- **zkLogin:** Onboarding OAuth-tal (Google) — a node operátor privát kulcs nélkül kezdhet, ephemeral key + salt. Sui-natív, kombinálható sponsored tx-szel és multisig-gel.
- **Walrus:** Job input/output blobok (scene fájlok, renderelt frame-ek, proof witness-ek) decentralizált DA-ja. On-chain csak a blob ID + hash kerül. Mainnet 2025. március 27-én indult.

### 3A.5 Gázköltség és batching

A Sui gázdíj átlagosan ~0,003 SUI/tranzakció vagy alatta (12 hónapos átlag, Shinami/Sui docs). A gázképlet: `GasFees = ComputationUnits × ComputationPrice + StorageUnits × StoragePrice`. A computation bucketing-et használ (legkisebb bucket 1000 unit, legnagyobb 5 000 000). A storage 100 unit/byte, 99% rebate törléskor (1% nem-visszatérítendő). **Batching stratégiák:** (1) payment channel — 1 on-chain settlement N job helyett; (2) PTB — több művelet egy tranzakcióban; (3) periodikus net-settlement — a worker naponta egyszer claim-el minden felhalmozott jobra; (4) escrow objectek törlése a storage rebate-ért.

### 3A.6 Rust node daemon — konkrét crate-ek

| Réteg | Crate | Verzió (2025-26) | Megjegyzés |
|---|---|---|---|
| P2P | `libp2p` | ~0.54+ | quic, gossipsub (~0.47), kad (~0.48), noise, identify (~0.48), relay, dcutr (~0.44), autonat |
| QUIC transport | `quinn` | 0.11+ | alternatív/direkt QUIC ha kell |
| Async runtime | `tokio` | 1.4x | teljes feature set |
| GPU detektálás | `nvml-wrapper` | 0.10+ | NVIDIA Management Library binding (VRAM, utilization, power) |
| AI inference | `candle` vagy `ort` | candle 0.7+, ort 2.0 | candle=pure Rust; ort=ONNX Runtime binding |
| Local state | `rusqlite` / `redb` / `sled` | — | redb pure-Rust, sled egyszerű, sqlite érett |
| Wire format | `bincode` (2.0) + `serde` | bincode 2.0.1 | lásd 5. szakasz |
| Sui interakció | `sui-sdk` (Rust) | mainnet-kompatibilis | escrow/claim/attestation tranzakciók |
| Kriptográfia | `ed25519-dalek`, `blake3` | — | node identity, tile hashing |

---

## Architektúra Version B1 — Saját L1 (teljes BFT)

**Őszinte értékelés: egy solo fejlesztőnek ez irreális (2-4 év, csapat kell).** Mégis teljes tervet adok.

### 3B1.1 Consensus választás

- **CometBFT/Malachite (Tendermint):** A Malachite egy Rust BFT consensus engine (Informal Systems, most Circle/Arc). ~780ms finalizáció 100 validátornál 1MB blokkal, akár 2,5 blokk/sec, ~13,5 MB/sec (~50 000 tps). Rust crate: `informalsystems-malachitebft-core-consensus` (0.5.0), minimum Rust v1.85. Coroutine-alapú effect system, tokio integráció. **Ez a legjobb választás Rustban**, ha saját L1 kell.
- **Narwhal-Bullshark/Mysticeti (DAG):** Amit a Sui használ — magas throughput, de komplex. Nincs kész standalone Rust library egy solo devnek.
- **Substrate:** Teljes framework (Polkadot), sok batteriát ad (wallet, explorer), de nehéz tanulási görbe és Rust-specifikus komplexitás.
- **Commonware:** Primitívek (P2P, consensus building blocks) Rustban — modulárisabb mint Substrate.

### 3B1.2 Miért nem térképeződik a GPU tulajdonlás konszenzus-biztonságra

A BFT biztonság ⅔ honest stake-en alapul, nem hardveren. A GPU birtoklása nem garantál Sybil-rezisztenciát: valaki sok olcsó GPU-t vagy hamis GPU-t regisztrálhat — ezt élesben bizonyította az io.net Sybil-támadása, ahol Ahmad Shadid CEO 2024. április 28-i postmortemje szerint "~1.8M fake GPUs" próbált csatlakozni, és a Proof-of-Work patch után az aktív GPU-k 600 000-ről ~10 000-re estek. A konszenzus-biztonsághoz **stake** kell, nem compute. Ezért a GPU node-ok validátorként való használata összekeveri a két különböző biztonsági modellt (compute correctness vs consensus safety). A validátor-készlet is korlátozott (BFT jellemzően <150 validátor a kommunikációs overhead miatt), miközben a GPU hálózat tízezres.

### 3B1.3 Economic security, token teher

Saját L1 igényel: token launch (MiCA!), bridge, wallet, block explorer, RPC infrastruktúra, validátor onboarding, gazdasági biztonság (a stake értékének > a támadás nyereségének kell lennie). Ez a "token launch/bridge/wallet/explorer burden" — több ember-év. Egy solo devnek **nem ajánlott**.

### 3B1.4 State machine, staking, slashing, block struktúra

Malachite-ra építve: az alkalmazás egy `Context` trait-et implementál. State: account balances, staking table, job registry, reputation. Slashing feltételek: double-sign (konszenzus), invalid compute attestation (fraud proof), liveness failure. Block struktúra: header (prev hash, state root, timestamp, proposer) + tx-ek (transfer, stake, job_submit, attest, challenge). Rust path: `informalsystems-malachitebft-app-channel` a channel-alapú alkalmazásinterfészhez.

---

## Architektúra Version B2 — Minimális Lightweight Consensus (proof-of-compute + gossip)

Ez a **legérdekesebb "true decentralized" opció** a Version A kiegészítéseként vagy alternatívájaként. Nincs globális tranzakció-rendezés — csak verifiable compute receipt-ek, gossip propagáció, sampled verifier committee attestation, lokális kauzális rendezés, és periodikus checkpoint egyetlen hash-commit-tal Sui-ra/Bitcoinra/Ethereumra.

### 3B2.1 Protokoll dizájn

- **Compute receipts:** Minden befejezett job egy signed receiptet generál: `{job_id, worker_pubkey, input_hash, output_hash, tile_hashes[], timestamp, nonce}`. Ez a hálózat alap "tranzakciója", de nincs globálisan rendezve.
- **Gossip propagáció:** A receiptek gossipsub-on terjednek. Nincs szükség minden node-nak minden receiptet látnia — csak az érintett feleknek + verifier committee-nek.
- **Sampled verifier committee:** Determinisztikus VRF-alapú sampling (a receipt hash-e seed-el) kiválaszt K verifiert. Ezek újraszámolnak (rendering: tile-ok; ZK: proof verify) és quorum attestationt adnak (pl. K-ból ⅔).
- **Lokális kauzális rendezés:** DAG of receipts / vector clock. Minden receipt hivatkozik az előzőekre (per-worker lánc), így parciális rendezés van globális konszenzus nélkül (hashgraph-lite).
- **Periodikus checkpoint:** Adott intervallumonként (pl. óránként) a hálózat egy Merkle root-ot számol az összes finalizált receiptre, és egyetlen hash-t commitál Sui-ra (olcsó, 1 tranzakció). Ez ad finality anchor-t és vitarendezési alapot. (A Neurolov hasonló modellt használ Solanán: proof-of-compute program, batch-elt settlement.)

### 3B2.2 Fizetés teljes konszenzus nélkül

- **Payment channels:** Client↔worker bilaterális channel (mint Version A), off-chain signed ticketek, periodikus net-settlement Sui-n.
- **Credit network (trust-line, egyszerűsített):** Ripple-szerű trust line-ok, ahol a node-ok credit limitet adnak egymásnak; a fizetés a hálózaton "átfolyik". A "credit limits beyond full collateralization" megközelítés (stake + credit expansion) csökkenti a lockolt tőkét, de gyengíti a garanciákat.
- **Periodic net-settlement:** N job → 1 settlement.

### 3B2.3 Biztonsági garanciák — őszinte összehasonlítás

- **Version A (Sui):** Legerősebb settlement finality (Sui BFT konszenzus), de a compute correctness külön verifikációs réteg. Trust: Sui validátorok.
- **B1 (saját L1):** Teljes kontroll, de a gazdasági biztonság csak akkora, mint a stake értéke — egy fiatal hálózatnál gyenge. Támadható amíg a token cap alacsony.
- **B2 (lightweight):** Nincs globális safety garancia — csak lokális/statisztikai. A sampled committee megbízhatósága a sampling méretén és a Sybil-rezisztencián múlik. **Gyengébb garanciák**, de sokkal olcsóbb és "igazán decentralizált". A finality a Sui checkpoint-tól függ (tehát valójában B2 is Sui-ra támaszkodik a végső elszámolásban).

---

## A vs B1 vs B2 Összehasonlító Mátrix

| Kritérium | Version A (Sui) | B1 (saját L1) | B2 (lightweight) |
|---|---|---|---|
| Biztonság (settlement) | ⭐⭐⭐⭐⭐ (Sui BFT) | ⭐⭐⭐ (stake-függő) | ⭐⭐ (statisztikai + Sui anchor) |
| Komplexitás | ⭐⭐ (közepes) | ⭐⭐⭐⭐⭐ (extrém) | ⭐⭐⭐ (közepes-magas) |
| Time-to-market | ⭐⭐⭐⭐⭐ (hónapok) | ⭐ (évek) | ⭐⭐⭐ (közepes) |
| Decentralizáció | ⭐⭐⭐ (Sui-függő) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Költség (solo dev) | ⭐⭐⭐⭐⭐ (alacsony) | ⭐ (magas) | ⭐⭐⭐ |
| **Ajánlás** | **✅ MVP** | ❌ kerülendő | 🔷 későbbi opció |

---

## Technológiai Stack — Konkrét Rust Crate-ek és Verziók

Lásd 3A.6 táblázat. Kiegészítés:
- **Sandboxing:** `Docker` GPU passthrough (`--gpus`, NVIDIA Container Toolkit), vagy `Firecracker` microVM (nehéz GPU passthrough), vagy `gVisor` (GPU support korlátozott). WASM+WebGPU alternatíva könnyű workloadokhoz. **A Windows probléma:** a legtöbb gaming GPU Windows-on van. WSL2 GPU passthrough működik (CUDA on WSL2), de a natív Windows sandboxing gyengébb (Windows Sandbox + GPU korlátozott). Ajánlás: Linux node-okat célozz először (Docker + NVIDIA Container Toolkit), Windows-ra WSL2-t.
- **NAT traversal:** libp2p relay v2 + DCUtR hole punching + AutoNAT + Identify. Public relay node-ok kellenek (cloud VM) a koordinációhoz. A relay v2 korlátozott (byte/idő) — a DCUtR upgrade-eli direkt kapcsolattá. Ha a hole punch elbukik, a relayed kapcsolat marad fallbackként (limitált).

---

## Wire Format Ajánlás

Benchmarkok alapján (rust_serialization_benchmark, erickt/rust-serialization-benchmarks): a **`bincode` 2.0** a helyes választás a belső node-to-node kommunikációhoz — gyors (encode ~135ns, ~2962 MB/s), kompakt, natív serde integráció, tiszta Rust. **Miért nem a többi:**
- **protobuf (prost):** cross-language, sémafüggő, lassabb (~640ns encode) — csak akkor kell, ha nem-Rust kliensek is lesznek.
- **capnproto:** zero-copy, nagyon gyors serialize (~32ns), de rosszabb access time és pazarlóbb nagy adatra.
- **flatbuffers:** zero-copy read, de lassú serialize strukturált adatra.
- **rkyv:** a leggyorsabb zero-copy (0.8+), ha extrém teljesítmény kell — érdemes megfontolni a nagy blob metaadatokra.

**Ajánlás:** `bincode` 2.0 a belső protokollra; `protobuf`/`prost` csak a külső/publikus API-ra ha heterogén kliensek kellenek. A Sui-ra kerülő adat BCS (Binary Canonical Serialization) — a Sui natív formátuma.

### Miért rossz az SSH mint base transport (röviden)
(Már megbeszélve.) Az SSH connection-oriented, nehéz, nincs beépített peer discovery/multiplexing/NAT traversal, és nem P2P-natív. QUIC stream multiplexinget, 0-RTT-t, beépített TLS-t és jobb NAT-viselkedést ad.

### QUIC vs raw UDP vs WireGuard (röviden)
- **QUIC:** stream multiplexing, beépített titkosítás (TLS 1.3), connection migration, libp2p-natív — **ez az ajánlott**.
- **raw UDP:** minden magadnak (megbízhatóság, titkosítás, sorrend) — felesleges munka.
- **WireGuard:** kiváló mesh VPN (Phase 0-ra tökéletes 2-3 gép közt), de nem P2P discovery, statikus konfiguráció — nem skálázódik permissionless hálózatra.

---

## Verifikációs Dizájn (részletes)

**Rendering (MVP):** (1) determinisztikus seed a Cycles-ben; (2) a worker minden tile-ra BLAKE3 hash-t submitál; (3) sampled verifier random N tile-t újrarenderel; (4) tolerancia-alapú összehasonlítás (perceptual hash / SSIM a Monte Carlo zaj miatt); (5) eltérés → fraud proof → slashing. Redundáns végrehajtás a kritikus jobokra.

**ZK proving:** self-verifying — a verifier egyszerűen lefuttatja a proof verify-t. Nincs szükség redundanciára. Ez a legtisztább.

**AI inference:** (1) TOPLOC (Prime Intellect) locality-sensitive hashing — vLLM/SGLang integrációval, non-determinisztikus GPU-n is működik, gyorsabb mint a generálás; (2) RepOps/Verde (Gensyn) bitwise reprodukálható operátorok FP32-re, CUDA 12.1, PyTorch 2.4/ONNX; (3) redundáns inference + logit tolerancia; (4) TEE csak H100/H200 (consumer GPU-n nincs).

---

## Sybil / Biztonsági Dizájn

- **Stake-alapú:** minden worker min stake-et lockol (Version A staking modul); a slashing gazdaságilag bünteti a csalást.
- **Hardware attestation:** NVIDIA Confidential Computing (H100/H200) TEE-t és remote attestationt ad (NVIDIA Root CA-val aláírt report, on-die hardware root of trust, IK kulcs fuse-olva a chipbe), de **consumer GPU-n (RTX 30/40) NINCS TEE** — tehát a fő hálózatnál nem támaszkodhatunk rá. (Ráadásul CPU TEE-t is igényel: AMD SEV-SNP vagy Intel TDX.) Helyette proof-of-GPU-work benchmark (OctaneBench/egyedi kernel) a capability regisztrációnál.
- **Proof-of-GPU-work:** stress test (mint io.net 12 órás teszt) + periodikus benchmark challenge.
- **Verifikáció:** redundáns végrehajtás, spot-checking, optimistic fraud proof, sampled committee.
- **Node churn:** heartbeat monitoring, job reassignment timeout-nál (mint Neurolov scheduler), reputation penalty offline node-oknak.
- **Verified vs unverified:** kritikus — a Vast.ai adat mutatja, hogy a verifikált GPU ~6 USD/nap, a verifikálatlan ugyanaz a kártya ~0,05 USD/nap. A verifikációs badge/reputation rendszer alapvető.

---

## Deliverable 3: Fázisos Roadmap Milestone-okkal

Solo dev + AI-assisted development (Claude Code + multi-agent workflow) feltételezésével. Az effort-becslések durvák; az AI-asszisztencia jelentősen gyorsíthat, de a debugging/integráció (különösen NAT és on-chain) nehezen jósolható.

### Phase 0: Compute Pipeline Validáció (becsült: 3-5 hét)
- **Deliverables:** 2-3 saját gép, WireGuard mesh vagy direkt QUIC, alap job queue, GPU worker (Blender Cycles headless render), nvml-wrapper GPU detektálás.
- **Kockázatok:** GPU driver/CUDA környezet konzisztencia; Windows vs Linux.
- **Go/No-Go:** egy scene fájl megbízhatóan renderelődik több node-on, az eredmény hash-elhető és összehasonlítható toleranciával.

### Phase 1: P2P Réteg (becsült: 6-10 hét)
- **Deliverables:** libp2p Kademlia DHT discovery, gossipsub job hirdetés, DCUtR NAT traversal + public relay node, node identity (ed25519), capability registry (VRAM, OctaneBench), benchmark protokoll.
- **Kockázatok:** NAT hole punching megbízhatatlanság otthoni router-eknél (relay fallback kell); libp2p API változások.
- **Go/No-Go:** két otthoni PC NAT mögött direkt kapcsolatot létesít; job hirdetés és matching működik.

### Phase 2: Sui Settlement Integráció (becsült: 6-10 hét)
- **Deliverables:** JobEscrow + staking Move contractok testneten, sui-sdk Rust integráció, attestation flow, payment claim, Walrus blob DA a scene fájlokra.
- **Kockázatok:** Move tanulási görbe (bár a user tapasztalt Sui-val); gázoptimalizálás.
- **Go/No-Go:** end-to-end job testneten: escrow lock → render → attest → challenge window → claim.

### Phase 3: Verifikációs Réteg (becsült: 8-12 hét)
- **Deliverables:** redundáns végrehajtás, sampled verifier committee (VRF), fraud proof + challenge, reputation registry, Sybil-rezisztencia (stake + proof-of-GPU-work), slashing.
- **Kockázatok:** verifikáció false-positive (determinizmus/tolerancia hangolás); verifier collusion.
- **Go/No-Go:** egy csaló worker (rossz output) megbízhatóan detektálódik és slashelődik <5% false positive-val.

### Phase 4: Permissionless Mainnet (becsült: 8-16 hét + folyamatos)
- **Deliverables:** mainnet deploy, no-token fee modell (protocol fee SUI/USDC-ben), governance (kezdetben multisig, később DAO), monitoring/explorer.
- **Kockázatok:** MiCA megfelelés ha token; likviditás/kereslet bootstrap; verseny.
- **Go/No-Go:** fizető külső kliensek + külső GPU providerek a hálózaton, pozitív unit economics.

---

## Kompetitív Tájkép Összefoglaló — Mit Érdemes Átvenni

- **io.net:** Solana settlement, Ray framework scheduling, 100k+ GPU. Tanulság: verifikáció-hiány (1,8M fake GPU Sybil-támadás) → erős Sybil-rezisztencia kell.
- **Akash (Cosmos SDK):** auction-alapú marketplace, Kubernetes-native, $AKT + axlUSDC fizetés. Tanulság: bidding mechanizmus, de lassú job pickup.
- **Nosana (Solana):** **legrelevánsabb referencia** — GPU inference, Docker jobok, Solana smart contract settlement (staking, jobs, nodes, pools). Nyílt TS SDK. Node-ok Solana címmel azonosítva; proof-of-work verifikáció signed output hash-ekkel Merkle root ellen.
- **Render Network (Solana):** OctaneBench-óra árazás, 3 tier rendszer, burn-mint equilibrium, manuális + auto-approve (72h). Tanulság: a rendering piac validált modellje; Blender Cycles integráció (RNP-014).
- **Gensyn:** RepOps/Verde bitwise reprodukálható operátorok (repop-demo), Truebit-stílusú dispute game. Tanulság: a determinizmus-probléma megoldása.
- **Prime Intellect:** TOPLOC verifiable inference (LSH, vLLM/SGLang integráció), PRIME-RL async training, SHARDCAST weight propagáció. Tanulság: consumer GPU-n működő verifikáció (INTELLECT-2, 32B, 100+ heterogén node 3 kontinensen).
- **Bittensor:** Yuma Consensus (stake-weighted validator scoring, top 64 validátor, min 1000 stake weight), subnet modell, dTAO AMM. Tanulság: incentive mechanizmus, de komplex; Subtensor PoA-ra épül.
- **BOINC/Golem:** volunteer computing tanulságok (churn, redundancia). **Petals/exo:** distributed inference otthoni klaszteren.
- **Salad:** 60k consumer GPU, idle monetizálás — a Render RNP-023 subnet-ként integrálná. Tanulság: a consumer GPU aggregáció működik.

---

## Gazdasági Modell Vázlatok

- **Fee-only (AJÁNLOTT MVP):** protocol take rate (pl. 10-20%) a job fizetésből, SUI/USDC-ben. **Nincs saját token → nincs MiCA token-kibocsátási teher.** Legegyszerűbb, leggyorsabb, legkevesebb jogi kockázat.
- **Burn-mint equilibrium (mint Render):** saját token, jobok tokent burn-ölnek, node reward-ok mint-elnek. Token-függő, MiCA-köteles.
- **Take rate + reputation staking:** a fee mellett a workerök stake-elnek reputációért.

**Ajánlás:** kezdd fee-only USDC/SUI modellel. Token csak akkor, ha a hálózat validált és a jogi/gazdasági teher indokolt.

---

## Szabályozási Megjegyzések (EU — Magyarország/Ausztria, MiCA)

A MiCA (Markets in Crypto-Assets) 2024. december 30-tól teljesen alkalmazandó, a CASP átmeneti időszakok 2026. július 1-ig tartanak a legtöbb tagállamban (egyes tagállamok rövidebbet választottak, pl. Hollandia 2025. július). Kulcs pontok:
- **Utility token kivétel:** A MiCA **nem alkalmazandó olyan utility tokenekre, amelyek egy létező termékhez/szolgáltatáshoz adnak hozzáférést** (Squire Patton Boggs elemzés) — DE ez a kivétel nem érvényes, ha a tokent fundraising célra használják, vagy ha kereskedésre bocsátják.
- **No-token fee modell:** ha SUI/USDC-ben szedsz protocol fee-t és nem bocsátasz ki saját tokent, **elkerülöd a MiCA token-kibocsátási (Title III) kötelezettségeket**. Ez erősen ajánlott az MVP-hez.
- **CASP engedély:** ha custody/exchange szolgáltatást nyújtasz, CASP engedély kellhet. Egy tiszta P2P compute marketplace, ahol a fizetés közvetlenül a felek közt megy (non-custodial escrow smart contracton), valószínűleg elkerüli ezt — de **jogi tanácsadás szükséges**.
- **Enforcement:** A Cyfrin MiCA guide szerint 2025 novemberéig 540M+ EUR bírságot szabtak ki a MiCA bevezetése óta; a licencvesztésre a pontos szám forrásfüggő (SQ Magazine: "28 crypto firms lost licences by mid-2025"; más forrás 50+/58 CASP-t említ). A megfelelés nem opcionális.

**Ajánlás:** no-token, non-custodial, fee-only modell induláshoz. Token/staking csak jogi konzultáció után.

---

## Consumer vs Datacenter GPU — Őszinte Verseny-értékelés

Verticalonként:
- **Rendering:** Consumer GPU **versenyképes** — a rendering batch, VRAM-igénye moderált, és a Render Network bizonyítja a consumer GPU modell életképességét. EU áram a fő hátrány.
- **Inference:** Consumer GPU **korlátozott** — VRAM cap (24GB), latency (otthoni upload), és a datacenter H100/H200 dominancia. Batch/kis modell inference-re OK.
- **ZK proving:** Consumer GPU **részben versenyképes** — RTX 5090 (32GB) használható (Brevis Pico Prism), de a nagy proofok datacenter GPU-t igényelnek.

**Áram és optimalizáció:** EU 0,25-0,40 €/kWh vs US datacenter ~0,05-0,12 USD/kWh — ez a strukturális hátrány. Undervolting csökkentheti a fogyasztást ~20-30%-kal minimális teljesítményveszteséggel. Spot pricing (csak akkor futni, amikor a job díja > áramköltség) elengedhetetlen EU-ban. **Realitás:** az otthoni EU GPU nem versenyzik árban a datacenterrel; az értékajánlat az **idle hardver monetizálása** (a fix költség már elsüllyedt) és a **decentralizáció/censorship-resistance**, nem a nyers ár.

---

## Végső Ajánlás

1. **Architektúra:** Version A (Sui settlement) — non-custodial escrow, staking, payment channel Move contractokkal; egyedi Rust/libp2p/QUIC P2P compute réteg. A B2 lightweight gossip réteg opcionális későbbi kiegészítés a receipt-propagációra; B1 (saját L1) kerülendő.
2. **Vertical:** MVP = 3D rendering (Blender Cycles) — legjobb verifikálhatóság/latency/licensz/solo-dev kombináció. ZK proving mint elegáns második fázis.
3. **Gazdasági modell:** fee-only USDC/SUI, no-token → MiCA-egyszerűség.
4. **Stack:** libp2p 0.54+, tokio, quinn, nvml-wrapper, bincode 2.0, sui-sdk, Docker+NVIDIA Container Toolkit (Linux first, WSL2 Windows-ra).
5. **Roadmap:** Phase 0-4, ~7-14 hónap AI-assisted solo fejlesztéssel az MVP-ig.
6. **Realitás:** a home consumer GPU EU-ban marginális profitú; a hálózat sikere a kritikus tömegen, a verifikáció megbízhatóságán és a valós keresleten múlik.

---

## Caveats (Korlátok és megjegyzések)

- **Bevételi adatok:** A DePIN GPU-earnings számok jelentős része önbevallott vagy affiliate-blogokból származik (Aethir bevétele nem on-chain auditált; a "€610-1412/hó" ShareAI-becslések hipotetikus marketing, nem valós earnings — ~8-12× túlbecsülik a valós marketplace rátákat). A legmegbízhatóbb hard szám: verified Vast.ai 4090 ~6 USD/nap bruttó.
- **Verzioszámok:** A crate-verziók (libp2p, bincode, Malachite 0.5.0) a kutatás időpontjában (2025-26) érvényesek; a libp2p API gyorsan változik, ellenőrizd a legfrissebbet a crates.io-n build előtt.
- **Move kód:** A modul-vázlatok skeleton szintűek (illusztratív), nem auditált, production-ready kód — az aláírás-ellenőrzés, hozzáférés-kontroll (capability/witness pattern) és edge case-ek részletes kidolgozást igényelnek.
- **Malachite:** alpha szoftver, "not for production, not externally audited" — saját L1-hez kockázatos.
- **Piaci becslések:** A 3D rendering piacméret-becslések házanként szórnak (GMI: 4,4 Mrd/2023, 25% CAGR; SNS: 23 Mrd/2032; Brainy: 34,6 Mrd/2032) — használj konkrét forrást döntéshez.
- **Jogi:** A MiCA-értelmezés nem jogi tanács; a no-token modell csökkenti a kockázatot, de Magyarországon/Ausztriában a nemzeti competent authority-nál (MNB / FMA) érdemes megerősíttetni a non-custodial P2P marketplace besorolását.
- **Sui-függőség:** A Version A és B2 is a Sui hálózat elérhetőségére/finality-jára támaszkodik — ez a "true decentralization" korlátja, amit a felhasználó tudatosan vállal (csak Sui-ban bízik).