# Hibrid Decentralizált Compute Hálózat — Teljes Architektúra, Implementációs Terv és Multi-Agent AI Fejlesztési Workflow

> **Research input — canonical owner: whole-system architecture (ADR-0002 Track A).**
> Owns the multi-network settlement abstraction, checkpoint/anchoring, transport
> (iroh) + wire format (postcard), heterogeneous node model, and the master build
> roadmap. For tokenomics/MiCA → `protocol_compute_currency.md`; for the GPU-vertical
> comparison, GPU verification, and Sui Move reference → `gpu_compute_network_sui_render_libp2p.md`
> (superseded in part); for cross-chain swap/bridge feasibility → `cross_chain_p2p_feasibility_EN.md`.
> This is reference input, not an accepted architecture — accepted decisions live in
> `docs/adr/` (see `docs/ai/REPO_MAP.md`).

## TL;DR
- A javasolt hibrid architektúra a **B2 lightweight proof-of-compute + gossip** réteget egyesíti egy **teljesen chain-agnosztikus, több-láncú settlement adapter réteggel**, ahol Solana, Sui, Base, Ethereum, BNB, Polkadot, Avalanche és XRPL egyenrangú settlement-végpontok; a checkpoint-anchoring problémát a "cheapest-2-3 chain (XRPL+Solana) + per-corridor finality" pragmatikus modell oldja meg.
- A csomópont-modellek közül az **A+C hibrid (egységes daemon capability-alapú tiered szerepekkel: GPU heavy compute + CPU-only infrastruktúra-szerepek)** a nyertes, WASM-first CPU-sandbox (wasmtime, fuel-determinizmus) + CUDA-first GPU, **iroh 1.0 + iroh-gossip** hálózati stack, és **postcard** wire-formátum mellett; az első workload a FlowMate elosztott backtest (dogfooding), az első chain a **Base**.
- A solo+AI fejlesztés reálisan **~9-11 hónap béta-ig** (agresszíven ~5-6); a havi AI-előfizetés komfort-szcenárióban **~$206/hó** (Claude Max 5x $100 + ChatGPT Pro 5x $100 + GLM ~$6), az infra ~€10-15/hó; a 12 hónapos komfort-összköltség kb. **~$2,800** professzionális audit nélkül.

## Key Findings

1. **CCTP v2 a settlement-gerinc, de nem fed le mindent.** A Circle 2025. november 14-i blogja ("CCTP V1 deprecation: CCTP V2 is now the canonical CCTP") szerint a CCTP v2 ekkor **17 blockchainen élt** és ez a kanonikus verzió; a legacy v1 **manuális phase-out 2026. július 31-én kezdődik**. A kanonikus szerződések minden v1-láncon élnek **Aptos, Noble és Sui kivételével** — a Circle a Sui-t 2026 első felére ígérte. Ethereum, Base, Avalanche, Solana támogatott; **XRPL nincs a CCTP-n** — ott az RLUSD vagy natív híd-alternatívák jönnek szóba. Ez azt jelenti, hogy a "pay-on-any-chain" ígéretet corridor-szintű logikával és netting-gel kell kiegészíteni.

2. **A Rust SDK-érettség láncról láncra drasztikusan eltér.** Az EVM-oldal (**alloy v1.0**, Paradigm, "Introducing Alloy v1.0", 2025.05.15 — "our first stable release", a Reth/Foundry/Revm/SP1 zkVM core dependency-je) production-ready; a Solana (solana-sdk) és Polkadot (subxt 0.50) érett; a Sui Rust SDK hivatalos, de "rudimentary"; az **XRPL Rust ökoszisztéma a leggyengébb láncszem** — több párhuzamos, részben pre-alpha crate (sephynox/xrpl-rust 0.5, gmosx/KeyrockEU sdk pre-alpha, és a 2026-os xrpl-mithril XLS-85 escrow-támogatással).

3. **Az XRPL natív Escrow elegánsan illeszkedik az adapter-trait-hez.** Az XRPL natív `Escrow` objektum PREIMAGE-SHA-256 crypto-condition-nel, `FinishAfter`/`CancelAfter` mezőkkel pontosan leképezi az `escrow_create`/`escrow_release`/`claim_payment` szemantikát — és a 2026-os XLS-100 Smart Escrows (WASM-alapú, sandboxolt logika az Escrow-objektumon) még programozhatóbbá teszi. Ez a lánc smart contract nélkül is teljes escrow-funkciót ad.

4. **Az iroh 1.0 a helyes hálózati választás** a NAT mögötti micro-node-okhoz: QUIC + built-in hole punching + relay fallback, ed25519 kulcs-alapú címzés, és a **iroh-gossip** (HyParView + PlumTree) pontosan a szükséges pubsub-gossip-réteget adja. Az n0 saját 1.0 release-posztja szerint "the public relays we run have seen more than 200 million endpoints created, in the last 30 days alone", és a Nous Research elosztott AI-tréninghez használja (állításuk szerint 10x bandwidth-csökkenés, 50% költségmegtakarítás). Ez lényegesen egyszerűbb, mint a teljes libp2p stack. (Megj.: az iroh 1.0 a "Dial Keys, not IPs" release-poszt szerint 2026. június 15-én jelent meg.)

5. **A WASM+WASI (wasmtime) a CPU-jobok ideális univerzális sandboxa**: cross-OS, capability-alapú biztonság, és **fuel-alapú determinizmus** — ami egyszerre ad OS-függetlenséget ÉS verifikációs determinizmust a redundáns végrehajtás-összehasonlításhoz. A Wasm 3.0-t a W3C 2025. szeptember 17-én ratifikálta (WebAssembly.org, Andreas Rossberg: "Today, we are happy to announce the release of Wasm 3.0 as the new 'live' standard"), a WASI Preview 2 stabil.

6. **A checkpoint-anchoring "mit vesz és mit nem" kérdése kritikus.** Az anchoring időbélyegzést és non-equivocation-bizonyítékot ad (slashing/dispute-hoz), de **NEM teszi a compute-eredményt helyessé** — azt csak a sampled verifier committee + redundáns végrehajtás adja statisztikailag.

## Details

### 1. Hibrid architektúra áttekintés (szöveges diagram)

```
                    ┌───────────────────────────────────────────────┐
                    │   SETTLEMENT ABSTRACTION LAYER (chain-agnostic) │
                    │   trait SettlementAdapter                       │
                    │  ┌────┬────┬────┬────┬────┬────┬────┬────┐       │
                    │  │EVM │Sol │Sui │DOT │XRPL│... │... │... │       │
                    │  │Base│    │    │    │    │    │    │    │       │
                    │  │ETH │    │    │    │    │    │    │    │       │
                    │  │BNB │    │    │    │    │    │    │    │       │
                    │  │AVAX│    │    │    │    │    │    │    │       │
                    │  └────┴────┴────┴────┴────┴────┴────┴────┘       │
                    │  USDC/CCTP v2 universal rail + netting/clearing  │
                    └───────────────▲───────────────────────────────┘
                                    │ escrow / claim / anchor
   ┌────────────────────────────────┴────────────────────────────────┐
   │                    COMPUTE LAYER (B2: PoC + gossip)               │
   │                                                                   │
   │  Job post → Escrow lock → P2P dispatch → Execute (WASM/GPU)       │
   │       → signed Receipt → gossip propagate → Committee attest      │
   │       → DAG of receipts (local causal order) → reputation accrue  │
   │                                                                   │
   │  Transport: iroh 1.0 (QUIC + holepunch + relay)                   │
   │  Gossip: iroh-gossip (HyParView + PlumTree)                       │
   │  Executor: wasmtime (CPU, deterministic) | CUDA/candle/ort (GPU)  │
   │                                                                   │
   │  Node tiers:  [GPU heavy] [Hybrid] [CPU-only infra: verifier,     │
   │               gossip relay, NAT rendezvous, DA cache]             │
   └───────────────────────────────────────────────────────────────────┘

   Anchor: epoch Merkle root of receipt-DAG → cheapest 2-3 chains
           + per-payment-corridor finality (inherited from settle chain)
```

A kulcsgondolat: **a compute-réteg lánc-független marad** (a receipt-ek, gossip, DAG, reputáció offline/P2P), és a lánc csak akkor lép be, amikor (a) escrow lock kell a job-poszthoz, (b) claim/payout történik, (c) epoch-anchoring. Így egyetlen "home chain" sincs; minden lánc egyenrangú settlement-végpont, és a felhasználó/node választja, hol settle-el.

### 1a. Compute-réteg specifikáció (lightweight PoC + gossip)

**Receipt adatstruktúra (Rust):**

```rust
// crate: proto
use serde::{Serialize, Deserialize};

pub type NodeId = [u8; 32];      // ed25519 public key (iroh EndpointId)
pub type JobId = [u8; 32];       // BLAKE3 of job manifest
pub type ReceiptId = [u8; 32];   // BLAKE3 of canonical receipt bytes

#[derive(Serialize, Deserialize, Clone)]
pub struct ComputeReceipt {
    pub receipt_id: ReceiptId,
    pub job_id: JobId,
    pub worker: NodeId,
    pub epoch: u64,
    pub input_commit: [u8; 32],    // BLAKE3 of input blob (content-addressed)
    pub output_commit: [u8; 32],   // BLAKE3 of output blob
    pub exec_kind: ExecKind,       // Wasm { fuel_used } | Gpu { device, ms }
    pub fuel_or_metric: u64,       // deterministic work-unit metering
    pub started_at: u64,           // unix millis (advisory only)
    pub finished_at: u64,
    pub parents: Vec<ReceiptId>,   // DAG edges -> local causal order
    pub sig: [u8; 64],             // ed25519 over all above fields
}

#[derive(Serialize, Deserialize, Clone)]
pub enum ExecKind {
    Wasm { module_hash: [u8; 32], fuel_used: u64 },
    Gpu  { backend: GpuBackend, kernel_hash: [u8; 32], ms: u32 },
}
```

**Gossip topics** (iroh-gossip TopicId = 32 byte):
- `jobs/announce` — új job manifestek (job creator → workerek)
- `receipts/<epoch>` — signed compute receipt-ek propagálása
- `attest/<epoch>` — committee attesztációk
- `disputes` — challenge-ek és fulfillment-ek
- `reputation/<epoch>` — epoch-végi reputáció-delta gossip

**Sampled verifier committee (VRF-alapú):** minden epochban minden befejezett job-hoz egy `k`-fős committee-t sorsolunk. A VRF input `= BLAKE3(job_id || epoch_seed)`, ahol az `epoch_seed` a legutolsó anchored Merkle-root (ez köti a kihúzást az anchorhoz, csökkentve a grinding-et). Egy node akkor tagja a committee-nek, ha `VRF_output(node_sk, input) < threshold(stake, reputation)`. **Kvórum-küszöb:** kis hálózaton `k=3`, `2/3` egyetértés kell az attesztációhoz; nagyobb hálózaton `k=7..21`, `⌈2k/3⌉` küszöb.

**Verifikáció mechanizmusa:** a committee-tagok **redundánsan végrehajtják** a WASM-jobot (determinisztikus fuel-metering miatt bit-azonos `output_commit` várható) és/vagy összevetik a content-addressed output-hasht. Ha egyezik → attest; ha eltér → dispute.

**Dispute-flow:** eltérés esetén `disputes` topikra kerül a konfliktus; egy nagyobb (pl. `2k+1`) fallback-committee dönt szavazással. A vesztes fél (worker vagy hazug verifier) elveszti a stake-jét (slashing) és negatív reputáció-deltát kap. A dispute-window a claim előtt/alatt zajlik (lásd 1e).

**Reputáció-akkréció:** epochonként `rep += w1*attested_ok - w2*disputes_lost`, decay-vel. A reputáció (a) növeli a job-dispatch prioritást, (b) csökkenti a stakelési követelményt, (c) növeli a committee-kiválasztási esélyt (fee-bevétel).

**Epoch-struktúra:** javaslat **1 óra/epoch**. Epoch végén: (1) receipt-DAG lezárása, (2) Merkle-root számítás, (3) anchoring a kiválasztott láncokra, (4) reputáció-delta commit, (5) új `epoch_seed` = anchored root.

### 1b. Több-láncú settlement absztrakció

**A `SettlementAdapter` trait (Rust):**

```rust
// crate: settle-core
use async_trait::async_trait;

#[async_trait]
pub trait SettlementAdapter: Send + Sync {
    fn chain_id(&self) -> ChainId;
    fn asset(&self) -> SettlementAsset;         // USDC | RLUSD | native

    async fn escrow_create(&self, p: EscrowParams) -> Result<EscrowHandle>;
    async fn escrow_release(&self, h: &EscrowHandle, proof: ReleaseProof) -> Result<TxId>;
    async fn escrow_refund(&self, h: &EscrowHandle) -> Result<TxId>;   // timeout path
    async fn claim_payment(&self, c: ClaimParams) -> Result<TxId>;
    async fn anchor_checkpoint(&self, root: [u8; 32], epoch: u64) -> Result<TxId>;
    async fn verify_anchor(&self, epoch: u64, root: [u8; 32]) -> Result<bool>;
    async fn balance_query(&self, addr: &ChainAddress) -> Result<u128>;
    async fn finality(&self, tx: &TxId) -> Result<FinalityStatus>;
}

pub struct EscrowParams {
    pub payer: ChainAddress,
    pub payee: Option<ChainAddress>,     // may be resolved at release
    pub amount: u128,                    // asset base units (USDC = 6 dp)
    pub condition: ReleaseCondition,     // Hashlock([u8;32]) | Timelock | Committee
    pub cancel_after: u64,               // unix seconds (refund path)
}
```

**Per-chain SDK-érettségi tábla:**

| Lánc(család) | Rust crate | Verzió/állapot (2026) | Érettség/kockázat |
|---|---|---|---|
| Base/ETH/BNB/Avalanche C | **alloy** (`alloy-rs`) | v1.0 stable (2025.05.15), aktív (1288★, commit 2026-06) | **Alacsony** — production-grade, network-generic, Reth/Foundry/Revm/SP1 alap |
| Solana | **solana-sdk / solana-client / anchor-client** | érett, széles körű | Alacsony-közepes |
| Sui | **sui-sdk** (Mysten) + új `sui-transaction-builder` | hivatalos, de "rudimentary", gas-smashing helper hiányzik | **Közepes** — reuse a korábbi Move-modulból |
| Polkadot | **subxt** 0.50 + subxt-signer | érett, type-safe, light-client támogatás | Alacsony-közepes |
| XRPL | sephynox/**xrpl-rust** (0.5), gmosx sdk (pre-alpha), **xrpl-mithril** (2026, XLS-85 escrow) | fragmentált, pre-alpha/új | **Magas** — a leggyengébb láncszem; ajánlott a mithril kiértékelése vagy saját vékony JSON-RPC wrapper |

**Smart contract követelmények lánccsaládonként:**

- **EVM (Base/ETH/BNB/Avalanche C):** *egyetlen* Solidity escrow contract, 4 láncra deployelhető (azonos bytecode). Vázlat:

```solidity
// contracts/solidity/ComputeEscrow.sol
// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.24;
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract ComputeEscrow {
    struct Escrow { address payer; address payee; uint256 amount;
                    bytes32 condition; uint64 cancelAfter; bool released; }
    IERC20 public immutable usdc;
    mapping(bytes32 => Escrow) public escrows;         // escrowId => Escrow
    mapping(uint64 => bytes32) public anchors;         // epoch => merkle root

    constructor(address _usdc) { usdc = IERC20(_usdc); }

    function escrowCreate(bytes32 id, address payee, uint256 amount,
                          bytes32 condition, uint64 cancelAfter) external {
        require(escrows[id].amount == 0, "exists");
        usdc.transferFrom(msg.sender, address(this), amount);
        escrows[id] = Escrow(msg.sender, payee, amount, condition, cancelAfter, false);
    }
    // Hashlock release: preimage hashes to condition (mirrors XRPL crypto-condition)
    function escrowRelease(bytes32 id, bytes32 preimage) external {
        Escrow storage e = escrows[id];
        require(!e.released && sha256(abi.encode(preimage)) == e.condition, "bad");
        e.released = true;
        usdc.transfer(e.payee, e.amount);
    }
    function escrowRefund(bytes32 id) external {
        Escrow storage e = escrows[id];
        require(block.timestamp >= e.cancelAfter && !e.released, "no");
        e.released = true; usdc.transfer(e.payer, e.amount);
    }
    function anchorCheckpoint(uint64 epoch, bytes32 root) external {
        anchors[epoch] = root;   // event + storage; caller = protocol anchor key
    }
}
```

- **Solana:** Anchor program `escrow_create` / `escrow_release` / `anchor_checkpoint` instrukciókkal; PDA-alapú escrow-account, SPL-token (USDC) CPI-vel. Deploy-költség a bytecode-mérettől függ (egy hello-world Anchor-program ~2.47 SOL a RareSkills szerint, főleg rent).
- **Sui:** a korábbi report Move-modulja újrahasznosítható; `Escrow` mint shared object, `escrow_release` entry function preimage-ellenőrzéssel.
- **Polkadot:** két opció — **(a) ink! smart contract** a Polkadot Hub-on (REVM/PVM dual-VM, 2026), vagy **(b)** ha nincs saját parachain, akkor a **Hub EVM-kompatibilis rétegére** ugyanaz a Solidity escrow deployelhető (a Hub teljes JSON-RPC + Hardhat/Foundry/Remix támogatással). Solo-dev-nek az EVM-út a legkevesebb új tanulás. Egy dedikált pallet overkill.
- **XRPL:** **nincs szükség smart contractra** — a natív `EscrowCreate`/`EscrowFinish` PREIMAGE-SHA-256 crypto-condition-nel közvetlenül megvalósítja a hashlock-escrow-t. Ez a leképezés:
  - `escrow_create` → `EscrowCreate` tx (`Condition` = crypto-condition, `CancelAfter` = timeout, `FinishAfter` opcionális)
  - `escrow_release` → `EscrowFinish` tx a `Fulfillment` preimage-dzsel
  - `escrow_refund` → `EscrowCancel` a `CancelAfter` után
  - a token-escrow (XLS-85, 2026) kötelező `CancelAfter`-t ír elő. A conditional EscrowFinish tx-költség: min. 330 drops + 10 drops/16 byte fulfillment.

### 1c. Univerzális settlement-asset stratégia

**Alapdöntés: USDC via CCTP v2 mint univerzális rail**, ahol elérhető. A CCTP v2 burn-mint modell (nincs wrapped token, nincs harmadik fél custodian) 2025. november 14-én 17 láncon élt. Ethereum, Base, Avalanche, Solana kanonikus; Sui a 2026 H1-re volt ígérve; **XRPL nem CCTP-lánc** → ott **RLUSD** vagy corridor-híd.

**Hogyan kap fizetést a node a preferált láncán, ha a job-creator máshol fizetett?** Négy opció:

| Opció | Mechanizmus | Előny | Hátrány |
|---|---|---|---|
| (a) Per-corridor CCTP burn-mint | protokoll burn-eli az USDC-t forrás-láncon, mint-eli a cél-láncon | trustless, natív USDC | latencia (Standard: finality-ig; Fast: 8-20s díjjal), gas 2 láncon |
| (b) Solver/intent-hálózat | ERC-7683 / deBridge / Across relayer teljesíti | gyors, tőkehatékony | relayer-függőség, díj |
| (c) Belső netting/clearing | protokoll-treasury nettózza a corridor-flow-kat, periodikus rebalance CCTP-vel | minimális on-chain tx per job | treasury tőkeigény, számviteli komplexitás |
| (d) Node multi-chain balansz | a node több láncon tart egyenleget | egyszerű | szórt likviditás node-oldalon |

**Ajánlás:** kombinált modell. Alapból **(c) internal netting** a fő clearing-mechanizmus (a legtöbb job kis összegű, a per-tx anchoring drága lenne), periodikus **(a) CCTP rebalance**-szel a corridor-egyenlegek kiegyenlítésére. Nagy egyszeri kifizetéseknél **(b) intent-solver**. XRPL-corridorra RLUSD, mert nincs CCTP.

### 1d. Checkpoint/finality anchoring — költség és bizalom

**Per-tx anchoring költség (32-byte hash commit), 2026 tipikus árakon:**

| Lánc | Natív költség | USD/tx | Forrás |
|---|---|---|---|
| XRP Ledger | 10 drops (0.00001 XRP) | ~$0.00001 | XRPL.org tx-cost docs |
| Solana | 5,000 lamports base | ~$0.0004 (all-in $0.001-0.005) | solana.com/docs/core/fees |
| BNB Chain | ~0.0000021 BNB @0.1 gwei | ~$0.005-0.01 | BscScan gas tracker |
| Avalanche C | ~0.0005 AVAX @25 nAVAX | ~$0.005-0.02 | Snowtrace / Eco.com |
| Polkadot (remark) | ~0.001-0.0015 DOT | ~$0.002-0.003 | Polkadot Wiki (base 0.001 DOT) |
| Sui | ~0.001-0.0028 SUI | ~$0.002-0.006 | Sui docs / blog.sui.io |
| Base (L2) | tiny L2 + L1 data fee | ~$0.002-0.02 (tip. <$0.01) | Base docs |
| Ethereum L1 | ~40k gas @0.345 gwei | ~$0.03-0.15 | Etherscan gas tracker (0.345 gwei, 2026.07.01) |

**Havi anchoring-költség modell** (24 epoch/nap óránkénti anchoringnál = 720 anchor/hó láncanként):

| Frekvencia | XRPL | Solana | Base | BNB | Sui | ETH L1 |
|---|---|---|---|---|---|---|
| Óránként (720/hó) | ~$0.007 | ~$0.29 | ~$3.6-14 | ~$3.6-7 | ~$1.4-4.3 | ~$22-108 |
| Naponta (30/hó) | ~$0.0003 | ~$0.012 | ~$0.15-0.6 | ~$0.15-0.3 | ~$0.06-0.18 | ~$0.9-4.5 |

**Négy anchoring-stratégia és bizalmi elemzés:**

- **(a) Minden láncra egyszerre:** legdrágább (ETH L1 dominál), redundáns non-equivocation-bizonyíték mindenhol. Óránkénti mind-8-láncra ~$30-140/hó, főleg ETH miatt.
- **(b) Legolcsóbb 2-3 láncra + kereszthivatkozás:** pl. **XRPL + Solana + Base** — óránkénti anchoring ~$4-14/hó. A drágább láncokra (ETH) csak a settlement-corridor-onként történik commit.
- **(c) Forgó anchor-lánc epochonként:** minden epoch más láncra anchorol; szétteríti a költséget és a bizalmat, de a verifikáció komplexebb (a verifier-nek tudnia kell, melyik epoch hol van).
- **(d) Nincs globális anchor — csak per-payment-corridor finality:** a settlement-finality abból a láncból öröklődik, ahol az adott fizetés settle-el. Legolcsóbb, de nincs globális non-equivocation-evidencia a compute-DAG-ra.

**Mit vesz az anchoring és mit NEM:** Az anchoring **időbélyegzést** és **non-equivocation-bizonyítékot** ad — bizonyítható, hogy egy adott epoch receipt-DAG-ja egy adott root-tal létezett egy adott időpontban, ami slashing/dispute-nál perdöntő (egy hazug node nem tud utólag más DAG-ot mutatni). **NEM teszi a compute-eredményt helyessé** — a helyességet kizárólag a sampled committee + redundáns végrehajtás adja statisztikailag; és nem ad globális total order-t.

**Pragmatikus alapértelmezés (ajánlás):** **(b) stratégia — XRPL + Solana anchoring óránként** (~$0.3/hó együtt), **+ per-corridor finality (d)** a tényleges fizetésekre. Az XRPL a leggazdaságosabb non-equivocation-horgony (~$0.00001/tx), a Solana pedig gyors finality-t és széles ökoszisztémát ad. Ha egy dispute nagy értékű, akkor ad-hoc ETH L1 anchor is tehető. Ez a modell havi néhány dollár alatt tartja az anchoring-költséget, miközben megőrzi a slashing-hez szükséges bizonyítékokat.

### 1e. Job-lifecycle end-to-end + wire-formátum

**Szekvencia:**
```
1. Job post      — creator kiválasztja a fizető láncot (pl. Base/USDC)
2. Escrow lock   — SettlementAdapter.escrow_create (hashlock condition)
3. P2P dispatch  — jobs/announce gossip → capability-matched worker(s)
4. Compute       — wasmtime (CPU) vagy CUDA/candle (GPU)
5. Receipt+gossip— signed ComputeReceipt → receipts/<epoch>
6. Committee att.— VRF-selected committee redundáns exec / hash-compare
7. Claim on chain— worker/committee reveal preimage → escrow_release
8. Challenge win.— opcionális dispute-window (pl. 10 perc) claim előtt
9. Payout        — USDC a worker preferált láncán (netting/CCTP)
10. Anchor       — epoch végén Merkle-root → XRPL + Solana
```

**Wire-formátum döntés: postcard** (nem bincode, nem protobuf). Indoklás: Rust-first rendszer, a **postcard `no_std`-barát és kompakt** (fontos a micro-node-okhoz és a WASM-guest-hez), determinisztikus szerializáció (jó a hash-commit-hoz), és a `serde`-vel natívan működik. A bincode alternatíva, de a postcard kompaktabb és beágyazott-barátabb. A protobuf feleslegesen nehéz egy homogén Rust-hálózaton, cross-language előny itt nem számít.

**Message struct vázlatok:**
```rust
// crate: proto  (all wire types derive Serialize/Deserialize, encoded via postcard)
#[derive(Serialize, Deserialize)]
pub enum GossipMsg {
    JobAnnounce(JobManifest),
    Receipt(ComputeReceipt),
    Attest { receipt_id: ReceiptId, verifier: NodeId, ok: bool, sig: [u8;64] },
    Dispute { receipt_id: ReceiptId, claimed: [u8;32], observed: [u8;32] },
    RepDelta { node: NodeId, epoch: u64, delta: i32 },
}

#[derive(Serialize, Deserialize)]
pub struct JobManifest {
    pub job_id: JobId,
    pub kind: JobKind,             // WasmModule | GpuKernel | Backtest
    pub input_blob: [u8; 32],      // iroh-blobs BLAKE3 hash
    pub pay_chain: ChainId,
    pub reward: u128,
    pub deadline: u64,
    pub redundancy: u8,            // how many workers / committee size
}
```

### 2. GPU+CPU heterogén node-design — modellek és ajánlás

**Model A — Unified node:** egyetlen daemon, capability flag-ekkel (`has_cuda`, `has_metal`, `cpu_cores`, `ram`, `bandwidth`); minden job capability-registry alapján routolódik.
*Pro:* egyszerű deploy, egy binary. *Kontra:* a gyenge hardver és az erős GPU-node ugyanaz a kód-út, nehéz külön reputáció/stake-track.

**Model B — Separate node classes:** GPU-node vs CPU-node vs hybrid, külön reputáció/stake-track, külön job-queue.
*Pro:* tiszta specializáció. *Kontra:* fragmentált reputáció, több deploy-variáns, a hybrid-node kétszer regisztrál.

**Model C — Tiered functional roles:** GPU-node = heavy compute; CPU-only node = verifier committee-tag, gossip-relay, NAT relay/rendezvous, DA-cache — kisebb, de stabil fee-ért. Ez a gyenge hardvert hálózati infrastruktúrává alakítja.
*Pro:* minden hardver hasznos, a micro-node-ok stabilizálják a hálózatot, természetes fee-diverzifikáció. *Kontra:* összetettebb szerep-koordináció.

**Ajánlás: A+C hibrid.** Egyetlen unified daemon (Model A egyszerűsége) **capability-alapú szerep-aktivációval** (Model C ereje): a daemon induláskor detektálja a hardvert (`nvml-wrapper` + `sysinfo`), és automatikusan felveszi a lehetséges szerepeket. Egy CUDA-s gép GPU-heavy + verifier + relay; egy micro-node (pl. mini-PC vagy VPS) csak verifier + gossip-relay + NAT-rendezvous + DA-cache. Ez pontosan illik a felhasználó céljához: **hatékony, gyors, STABIL micro-node-ok gyors hálózati kapcsolattal** — a stabil, jó felcsatlakozású gyenge gépek a hálózat gerincét adják, nem parlagon heverő kapacitást.

**CPU-job taxonómia — piaci valóság-check:**

| Workload | Valódi fizetős kereslet? | Megjegyzés |
|---|---|---|
| Video transcoding (FFmpeg) | Van, DE **Livepeer/Openpeer** uralja | Messari State of Livepeer Q1 2026: 134.4M perc feldolgozva (+71.9% QoQ a Q4 2025-ös 78.2M-ről), az AI-inference ~$154,700 fee = a protokoll-bevétel ~60%-a; a Livepeer 2026.05.28-án "Openpeer"-re nevezte át magát. Nehéz belépni. |
| Financial backtesting | **Igen — dogfooding!** FlowMate elosztott backtest/walk-forward/Monte Carlo | Első CPU-workload, azonnali személyes érték |
| Data processing / ETL | Közepes | Embarrassingly parallel batch jó fit |
| Compilation / CI runners | Van (self-hosted CI piac) | Determinizmus + sandbox kritikus |
| Web scraping / indexing | Van, de jogi/ToS-kockázat | Óvatosan |
| Scientific batch (Monte Carlo, folding) | BOINC-örökség, főleg grant/hobbi | Kevés közvetlen fizetős kereslet |

A **FlowMate elosztott backtest a killer első workload**: embarrassingly parallel (paraméter-sweep, walk-forward ablakok, Monte Carlo futások), determinisztikus (WASM-ban verifikálható), és azonnal hasznos a felhasználónak akkor is, ha a hálózat sosem megy publikusra — ez **de-riskeli a projektet**.

**GPU-job taxonómia (recap):** AI inference, rendering, ZK proving — ezek a heterogén schedulerben a `GpuKernel` JobKind-ba esnek, `has_cuda`/`has_metal` capability-vel matchelve. A scheduler a `redundancy` mezőt kisebbre veszi drága GPU-jobnál (a redundáns exec drága), helyette erősebb stake + reputáció-súlyozás.

### OS-függetlenség és sandbox-mátrix

**Rust cross-platform daemon:** tokio async runtime, cross-compilation, `cargo-dist` release-binárisokhoz mindhárom OS-re. GPU-hozzáférés: Windows natív CUDA + NVML (`nvml-wrapper` Windows-támogatással), Linux CUDA, macOS = NINCS NVIDIA → Apple Silicon Metal-út (`candle` Metal-backend, MLX, vagy wgpu).

**wgpu/WebGPU mint cross-vendor GPU-absztrakció** (Vulkan/Metal/DX12): a valóság-check fontos — a mért **wgpu/Vulkan compute-kernel hatékonyság egy nem optimalizált WGSL shaderrel csak 1-2% az FP32 peak-nek** (RTX 5090, arXiv 2604.02344), harmadik féltől optimalizált WGSL ~17%; a CUDA-hoz képest a fő különbség a **per-operation dispatch-overhead**, nem a kernel-minőség. A tensor-core-t a WGSL egyáltalán nem éri el. Ezért: **CUDA-first a komoly GPU-workloadhoz**, wgpu csak experimentális/cross-vendor fallback.

**WASM+WASI (wasmtime) mint univerzális CPU-sandbox:** ez a rendszer sarokköve a CPU-jobokhoz. Cross-OS, capability-alapú biztonság (alapból zéró filesystem/network hozzáférés), és **fuel-alapú determinizmus** — a fuel-metering teljesen determinisztikus (ugyanaz a program ugyanannyi fuellel mindig ugyanott áll meg), ellentétben az epoch-interruption-nel (~10% overhead, de nem-determinisztikus). A NaN-kanonizáció (`cranelift_nan_canonicalization`) és a `wasi-virt` a clock/filesystem virtualizálására biztosítja a bit-azonos determinizmust a verifikációhoz. A Wasm 3.0-t a W3C 2025. szeptember 17-én ratifikálta, WASI Preview 2 stabil.

**OS-support mátrix:**

| OS | CPU-job (WASM) | GPU-job | Sandbox (native) | Státusz |
|---|---|---|---|---|
| Linux | ✅ wasmtime teljes | ✅ CUDA teljes | gVisor / Firecracker / bubblewrap / landlock | **Elsődleges** |
| Windows | ✅ wasmtime teljes | ✅ natív CUDA + NVML, vagy WSL2 GPU-passthrough | AppContainer / Windows Sandbox / WSL2 | **Támogatott** (WSL2 ajánlott GPU-hoz) |
| macOS | ✅ wasmtime teljes | ⚠️ CSAK Metal-inference (candle/MLX), nincs CUDA | sandbox-exec / App Sandbox | **CPU + Metal-inference only** |

**Ajánlás:** WASM-first minden CPU-jobra (portábilis + determinisztikus); containerized/native GPU-jobokra per-OS support-matrix szerint (Linux full, Windows WSL2 vagy natív csökkentett sandbox-szal, macOS CPU + Metal-inference).

### Hálózati stack döntés: iroh vs libp2p

| Kritérium | iroh 1.0 + iroh-gossip | rust-libp2p | quinn + custom |
|---|---|---|---|
| NAT hole-punching | ✅ beépített, relay-fallback | ✅ dcutr, manuálisabb | ❌ saját implementáció |
| Pubsub gossip | ✅ iroh-gossip (HyParView+PlumTree) | ✅ gossipsub (battle-tested) | ❌ saját |
| Direkt transfer | ✅ iroh-blobs (BLAKE3) | ✅ | ✅ nyers |
| Egyszerűség | ✅✅ "dial keys not IPs" | ⚠️ nehezebb | ⚠️ sok saját kód |
| Érettség | 1.0 (2026-06-15), 200M+ endpoint/30 nap, Nous Research használja | nagyon érett | — |
| Kockázat | relay-sunset pre-1.0 verziókra 2026-09-30 (1.0-ra migrálni kell) | nagyobb boilerplate | legtöbb saját kód |

**Ajánlás: iroh 1.0 + iroh-gossip + iroh-blobs.** Ez pontosan a use-case-re (home NAT'd micro-node-ok, pubsub gossip + direkt transfer) lett tervezve, ed25519 kulcs-alapú perzisztens identitással (ami egyben a `NodeId` a receipt-ekben), és lényegesen kevesebb boilerplate, mint a libp2p. A iroh-gossip HyParView (active-view 5, passive-view 30) + PlumTree pontosan a szükséges skálázható, öngyógyító gossip. A libp2p csak akkor jönne szóba, ha később Kademlia-DHT-alapú globális discovery kellene a relay-k helyett.

### 3. Multi-agent AI fejlesztési terv — idő és pénz

**Előfizetések (2026-os árak):**

| Eszköz | Ár | Limit-jellemző |
|---|---|---|
| Claude Pro | $20/hó ($17 éves) | 5 órás rolling window |
| Claude Max 5x | $100/hó | 5x Pro usage |
| Claude Max 20x | $200/hó | 20x Pro; full-nap fejlesztéshez |
| ChatGPT Plus (Codex) | $20/hó | 15-80 GPT-5.5 msg/5h |
| ChatGPT Pro 5x (Codex) | $100/hó | 5x Plus (2026 áprilistól a Pro $100-ról indul, 5x/20x választható) |
| ChatGPT Pro 20x (Codex) | $200/hó | 20x Plus |
| GLM coding plan (Z.AI) | ~$3-6/hó tier | bulk boilerplate |

> **Fontos limit-figyelmeztetés:** a Claude Code v2.1.100+ verzió ~40% token-inflációt okozott (workaround: downgrade v2.1.34-re vagy npm-reinstall); a Codex 2026. április 2-tól token-alapú credit-árazásra váltott (üzenet-alapú helyett). Deploy előtt ellenőrizd az aktuális limiteket.

**Cross-consensus workflow — ágens-szerepek:**

- **Claude Code = lead architect + kritikus crate-ek implementálója** (consensus-adjacent kód, settlement-adapterek, kriptográfia, verify).
- **Codex = adversarial reviewer + test-író + második implementáló** párhuzamos crate-ekre.
- **GLM = bulk implementáló** boilerplate-re (adapter-scaffolding, CI, docs).

**Cross-review protokoll:** minden X ágens által írt PR-t Y ágens review-zol strukturált prompt-tal (security checklist, determinism checklist, error handling, no-panic policy, unsafe audit). Egyet-nem-értés esetén eszkaláció Máté-hoz mindkét ágens érveinek összefoglalójával.

**Git-fegyelem:** worktree-izoláció ágensenként, branch-naming (`agent/claude/feat-*`, `agent/codex/review-*`), conventional commits, PR-template-ek, per-session dev-log.

**Verifikációs kapuk modulonként:**
```
cargo fmt --check
cargo clippy -- -D warnings
cargo test
cargo deny check          # licenses + advisories
cargo audit               # RUSTSEC
proptest                  # wire-format round-trip + receipt verify
cargo fuzz                # parser/wire-format fuzzing
cargo miri test           # unsafe-free core crates
```

**GitHub Actions workflow-váz (OS-mátrix):**
```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with: { components: "clippy, rustfmt" }
      - run: cargo fmt --check
      - run: cargo clippy --all-targets -- -D warnings
      - run: cargo test --all
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: cargo install cargo-deny cargo-audit
      - run: cargo deny check
      - run: cargo audit
```

**PR review prompt template (reviewer ágensnek, angolul):**
```
You are the adversarial reviewer for PR #{n} authored by {other_agent}.
Review ONLY against this checklist and cite file:line for each finding.
[ ] SECURITY: any unvalidated input, signature check missing, replay risk?
[ ] DETERMINISM: any HashMap iteration, system time, float NaN, RNG in
    consensus/verify path?
[ ] ERROR HANDLING: any .unwrap()/.expect()/panic! in library code?
[ ] UNSAFE: justify every `unsafe` block or reject it.
[ ] WIRE FORMAT: postcard round-trip covered by proptest?
[ ] TESTS: does the PR add tests proving the claim in its description?
Output: APPROVE / REQUEST_CHANGES + numbered findings. If you disagree
with the author's design, state both positions for human escalation.
```

**Implementation task prompt template (angolul):**
```
Implement crate `{crate}` per spec section {ref}. Constraints:
- no_std where feasible; postcard for wire types; thiserror for errors.
- NO panics in library paths; return Result. NO unwrap outside tests.
- Every public fn documented; every wire type has a proptest round-trip.
- Deterministic: no wall-clock/RNG/HashMap-iteration in verify/consensus.
Deliver: code + unit tests + a 5-line dev-log entry. Then request review
from {reviewer_agent}.
```

**RACI-szerű crate-tulajdonlási tábla:**

| Crate | Owner (implement) | Reviewer | Bulk-assist |
|---|---|---|---|
| proto | Claude | Codex | — |
| transport (iroh) | Claude | Codex | GLM (glue) |
| gossip | Claude | Codex | — |
| identity | Claude | Codex | — |
| capability | Codex | Claude | GLM |
| executor-wasm | Claude | Codex | — |
| executor-gpu | Codex | Claude | — |
| verify | Claude | Codex | — |
| receipts (DAG) | Claude | Codex | — |
| settle-core | Claude | Codex | — |
| settle-evm | Codex | Claude | GLM (scaffolding) |
| settle-solana | Codex | Claude | GLM |
| settle-sui | Codex | Claude | GLM |
| settle-polkadot | GLM | Claude | — |
| settle-xrpl | Claude (magas kockázat) | Codex | — |
| checkpoint | Claude | Codex | — |
| node (daemon) | Claude | Codex | GLM |
| cli | GLM | Codex | — |

### Repo-struktúra (Cargo workspace)

```
compute-net/
├── Cargo.toml                 # [workspace]
├── crates/
│   ├── proto/                 # wire format, receipt types (postcard)
│   ├── transport/             # iroh/QUIC endpoint
│   ├── gossip/                # iroh-gossip topics
│   ├── identity/              # ed25519 keys, NodeId
│   ├── capability/            # hw detect: nvml-wrapper, sysinfo
│   ├── executor-wasm/         # wasmtime CPU jobs (fuel-metered)
│   ├── executor-gpu/          # CUDA/candle/ort
│   ├── verify/                # committee, VRF sampling, redundant compare
│   ├── receipts/              # DAG store (sled/redb)
│   ├── settle-core/           # SettlementAdapter trait, netting
│   ├── settle-evm/            # alloy
│   ├── settle-solana/         # solana-sdk/anchor-client
│   ├── settle-sui/            # sui-sdk
│   ├── settle-polkadot/       # subxt
│   ├── settle-xrpl/           # xrpl-rust / mithril
│   ├── checkpoint/            # anchoring
│   ├── node/                  # daemon binary
│   └── cli/
├── contracts/
│   ├── solidity/              # ComputeEscrow.sol (Base/ETH/BNB/AVAX)
│   ├── anchor/                # Solana program
│   └── move/                  # Sui module (reused)
└── infra/
    ├── docker/
    └── ansible/               # bootstrap relays
```

**Implementációs függőségi sorrend:** `proto` → `identity` → `transport` → `gossip` → `capability` → `executor-wasm` → `receipts` → `verify` → `settle-core` → `settle-evm` → (`checkpoint`, `node`, `cli`) → többi settle-* adapter → `executor-gpu`.

### IDŐSZÁMÍTÁS

**Velocity-feltevés:** AI-asszisztált Rust-áteresztés solo-dev-nek reálisan **~3-5x** a kézi tempó, de a cross-review 20-30% overhead-et ad. Feltételezés: ~15-20 produktív "agent-hour"/nap érdemi felügyelt fejlesztéssel.

| Fázis | Deliverable | Agent-óra (konzervatív / agresszív) | Naptári hét (konz./aggr.) |
|---|---|---|---|
| P0 | Local mesh 2-3 gép: iroh transport, WASM executor, egyszerű job-queue, **FlowMate backtest** | 120 / 70 | 4 / 2 |
| P1 | P2P discovery + gossip + receipts + capability registry | 180 / 110 | 6 / 3.5 |
| P2 | Első settlement-adapter (**Base**) + USDC testnet | 140 / 80 | 5 / 2.5 |
| P3 | Verifikációs committee + reputáció + Sybil (stake) | 200 / 120 | 7 / 4 |
| P4 | További adapterek (Solana, Sui, EVM-maradék, Polkadot, XRPL) + checkpoint anchoring | 240 / 140 | 8 / 4.5 |
| P5 | Hardening, security review, permissionless béta | 200 / 120 | 7 / 4 |
| **Összesen** | | **~1080 / 640 agent-óra** | **~37 / 20.5 hét** |

**Realista béta-idő solo+AI: ~9-11 hónap** (konzervatív, a párhuzamos crate-fejlesztés és a valós élet-overhead figyelembevételével), agresszíven ~5-6 hónap.

### PÉNZSZÁMÍTÁS

**(a) AI-előfizetések havonta:**

| Szcenárió | Összeállítás | Havi |
|---|---|---|
| Minimal | Claude Pro $20 + ChatGPT Plus $20 + GLM ~$6 | **~$46/hó** (komolyabb tempóhoz kevés lehet) |
| Comfortable | Claude Max 5x $100 + ChatGPT Pro 5x $100 + GLM ~$6 | **~$206/hó** |
| Accelerated | Claude Max 20x $200 + ChatGPT Pro 20x $200 + GLM ~$6 | **~$406/hó** |

**(b) Infra havonta:**

| Tétel | Költség |
|---|---|
| 2-3 bootstrap relay VPS (Hetzner CX22, €4.49/hó 2026. április 1-től, előtte €3.29 — a DRAM ~171% YoY dráguása miatt) | €9-13.5/hó |
| Domain | ~€1/hó |
| Monitoring (Grafana Cloud free tier) | €0 |
| **Összesen** | **~€10-15/hó (~$11-16)** |

**(c) Lánc-költségek:**
- Testnetek: ingyenes.
- Mainnet contract-deploy: EVM (Base) ~$5-50/lánc, ETH L1 $100+; Solana program ~2.47 SOL (hello-world, Anchor, főleg rent); Sui publish ~0.02-0.1 SUI; Polkadot Hub EVM-deploy hasonló az EVM-hez; XRPL nincs contract (csak account-reserve).
- Checkpoint anchoring: az ajánlott XRPL+Solana óránkénti modell **~$0.3/hó**.

**(d) Opcionális:**
- Professzionális code audit valóság-check: **$30-80k** (jelezve mint jövő/közösségi alternatíva — kezdetben peer-review + cargo-audit/deny + fuzzing helyettesíti).
- Cégalapítás (EU/Magyarország/Ausztria): csak megjegyzésként, MiCA fee-only modellel light-touch.

**TELJES BUDGET-szcenáriók:**

| Szcenárió | 6 hónap | 12 hónap |
|---|---|---|
| Minimal ($46 AI + $15 infra) | ~$366 | ~$732 + deploy ~$100 = **~$832** |
| Comfortable ($206 + $15) | ~$1,326 | ~$2,652 + deploy ~$150 = **~$2,800** |
| Accelerated ($406 + $15 + intent-tesztek) | ~$2,526 | ~$5,052 + deploy ~$200 = **~$5,250** |

Professzionális audit nélkül. Az audit külön $30-80k-s tétel, amit béta után, bevétel/grant terhére érdemes időzíteni.

### 4. Frissített fázisos roadmap (P0→P5)

| Fázis | Deliverable | Effort | Költség | Fő kockázat | Go/No-Go |
|---|---|---|---|---|---|
| **P0** | Local mesh + iroh + WASM executor + **FlowMate elosztott backtest** | 70-120 ó / 2-4 hét | AI + 0 infra (lokál) | iroh API-változás | FlowMate backtest 3 gépen determinisztikusan lefut, azonos hash |
| **P1** | P2P discovery + gossip + receipts + capability registry | 110-180 ó / 3.5-6 hét | + €10/hó VPS relay | gossip-skálázás NAT mögött | 10+ node stabil gossip, receipt-DAG épül |
| **P2** | Base settlement-adapter + USDC testnet | 80-140 ó / 2.5-5 hét | testnet ingyenes | alloy/contract bug | escrow_create→release→claim testneten zöld |
| **P3** | Verifikációs committee + reputáció + Sybil-stake | 120-200 ó / 4-7 hét | testnet | committee-bribery kis hálózaton | VRF-committee + slashing működik, dispute-flow tesztelt |
| **P4** | Solana/Sui/BNB/AVAX/Polkadot/XRPL adapterek + checkpoint anchoring | 140-240 ó / 4.5-8 hét | mainnet deploy ~$150 | XRPL SDK-éretlenség | 3+ lánc mainnet escrow + XRPL+Solana anchor él |
| **P5** | Hardening + security review + permissionless béta | 120-200 ó / 4-7 hét | audit later | bootstrapping trust | whitelist-béta stabil, security-checklist zöld |

**Dogfooding-szög:** a FlowMate elosztott backtesting **P0-P1 killer app** — azonnali személyes hasznot ad (a felhasználó saját backtest-jeit gyorsítja), függetlenül attól, hogy a hálózat publikus lesz-e. Ez a legfontosabb de-risking elem: a projekt akkor is értékes, ha sosem skálázódik hálózattá.

### Őszinte biztonsági értékelés

**Milyen garanciák VANNAK:**
- **Per-chain settlement finality** — a fizetés véglegessége abból a láncból öröklődik, ahol settle-el (CCTP hard finality attesztáció után).
- **Statisztikai compute-helyesség** — sampled committee + redundáns WASM-exec (determinisztikus fuel-metering miatt bit-azonos output várható).
- **Anchored non-equivocation** — az epoch-root anchoring bizonyítja, hogy egy node nem tud utólag más DAG-ot mutatni (slashing-evidencia).

**Milyen garanciák NINCSENEK:**
- **Nincs globális total order** — csak lokális kauzális rendezés a receipt-DAG-ban.
- **Committee-bribery / Sybil kis hálózaton** — kis node-számnál a VRF-committee megvesztegethető vagy Sybil-elárasztható; a stake + reputáció csak részben véd.
- **Bootstrapping trust probléma** — induláskor kevés node, kevés stake, gyenge statisztikai garancia.

**Attack-szcenáriók és mitigáció kis skálán:**
- *Lazy worker* (hamis output): redundáns exec + slashing.
- *Colluding committee*: nagyobb `k`, VRF-kihúzás az anchored root-hoz kötve (grinding ellen), reputáció-súlyozás.
- *Sybil*: stake-követelmény a preferált láncon + reputáció-akkréció (új node alacsony prioritás).
- **Fő mitigáció: whitelist/permissioned béta ELŐSZÖR** — a permissionless nyitás csak akkor, ha a node-szám és stake elér egy statisztikai biztonsági küszöböt.

### Versenytárs-landscape delta (multi-chain + CPU szög)

| Projekt | Fókusz | Settlement | Delta a mi modellünkhöz |
|---|---|---|---|
| **Acurast** | Smartphone/TEE compute (Polkadot) | ACU token, USDC on Base x402 | TEE-alapú (nem WASM-verifikáció); token-modell; 70k+ telefon, $11M funding (2025.11) |
| **Fluence** | CPU DePIN VM-marketplace | saját chain (Arbitrum Orbit), FLT + USDC/USDT | VM-alapú, nem lightweight-PoC; single-chain settlement |
| **Golem** | HPC rendering/batch | GLM token | régi, token-központú |
| **BOINC** | Tudományos batch | credit-rendszer (nem pénz) | **credit-lecke a heterogén work-unit-hoz!** |
| **Livepeer/Openpeer** | Video transcoding → AI video | ETH/Arbitrum, LPT | GPU-orchestrator, single-chain |
| **Theta EdgeCloud** | Edge GPU | THETA | token-központú |
| **Holepunch/Pear** | P2P runtime (chain nélkül) | nincs on-chain settlement | tanulság: P2P chain nélkül is működhet |
| **exo/Petals** | Home inference | nincs settlement | tisztán technikai |
| **Akash** | K8s container compute | AKT + bridged USDC, credit-card API | **single-chain (Cosmos)** |
| **io.net** | GPU AI clusters | **Solana** IO token | **single-chain** |

**Mi a valódi újdonság / a rés:** Az Akash, io.net, Fluence, Acurast, Livepeer **mind egyetlen settlement-láncra** kötöttek (Cosmos/Solana/Arbitrum/Polkadot). **Senki nem csinál igazi "pay-on-any-chain" chain-agnosztikus settlementet compute-ért.** A három genuinely novel elem: **(1) chain-agnosztikus settlement-választás** (a node ÉS a job-creator külön láncot választhat), **(2) WASM-determinisztikus CPU-verifikáció** (a legtöbb versenytárs GPU-fókuszú vagy TEE-alapú), **(3) tiered szerepek** amelyek a micro-node-okat hálózati infrastruktúrává teszik. A BOINC credit-rendszere adja a heterogén work-unit árazás mintáját.

### Gazdasági modell (heterogén árazás)

- **Benchmark-alapú work-unit-ok** (BOINC credit-lecke): a WASM fuel-metering natívan ad determinisztikus CPU-work-unit-ot; a GPU-oldal `GpuSecond` normalizált benchmark-kal.
- **Külön árazás:** GPU-second vs CPU-core-second, külön díjszabás; a tier-C node-ok bandwidth/relay-fee-t kapnak (kisebb, stabil).
- **Take-rate:** **fee-only, token NÉLKÜL** (konzisztens a korábbi MiCA-ajánlással) — a protokoll a settlement-flow-ból von le egy százalékot.
- **Price discovery:** **kezdetben posted-price** (egyszerű), később opcionális auction. A posted-price a béta-fázisban elég, és kevesebb támadási felület.

### Szabályozási brief (nem jogi tanács)

- **Fee-only, no-token modell MiCA alatt továbbra is ajánlott** — token kibocsátása nélkül nincs "asset-referenced token"/"e-money token" kibocsátói kötelezettség a protokoll oldalán.
- **Multi-chain stablecoin settlement:** az USDC MiCA szerint e-money token; mivel a **protokoll nem custody-zol** (a CCTP burn-mint és az escrow non-custodial), az érintettség light-touch — **de ez őszinte bizonytalanság**, mert a matching + settlement üzemeltetése felvetheti a VASP/CASP-regisztráció kérdését. Ez ügyvédi konzultációt igényel a béta előtt, nem oldható meg mérnökileg.
- **Cégalapítás:** EU/Magyarország vagy Ausztria; csak megjegyzés, a fee-only modell egyszerűsíti.

### Végső ajánlás — a választott stack egy táblában

| Réteg | Választás | Indoklás |
|---|---|---|
| Transport | **iroh 1.0** | QUIC + holepunch + relay, kulcs-alapú címzés, egyszerűbb mint libp2p |
| Gossip | **iroh-gossip** (HyParView+PlumTree) | pontosan a szükséges skálázható pubsub |
| CPU sandbox | **wasmtime (WASM/WASI)** | cross-OS + fuel-determinizmus a verifikációhoz |
| GPU | **CUDA-first** (Linux/Windows), wgpu experimentális | a wgpu 1-2% (opt. ~17%) FP32-hatékonyság kizárja komoly workloadra |
| Első chain | **Base** | olcsó EVM, egy Solidity-codebase 4 láncra, CCTP v2 kanonikus |
| Settlement asset | **USDC via CCTP v2** (XRPL-en RLUSD) | natív burn-mint, non-custodial |
| Node-modell | **A+C hibrid** (unified daemon + capability-tiered szerepek) | minden hardver hasznos, stabil micro-node infrastruktúra |
| Wire-formátum | **postcard** | no_std-barát, kompakt, determinisztikus |
| Anchoring | **XRPL + Solana óránként + per-corridor finality** | ~$0.3/hó, megőrzi a non-equivocation-bizonyítékot |
| Első workload | **FlowMate elosztott backtest** + egy GPU-vertikum (AI inference) | dogfooding, azonnali személyes érték |

## Recommendations

**Azonnali lépések (P0, 2-4 hét):**
1. Állítsd fel a Cargo workspace-t a fenti struktúrával; implementáld a `proto` + `identity` + `transport` (iroh 1.0) + `executor-wasm` (wasmtime, fuel-metered) crate-eket.
2. Portold a **FlowMate backtest-et WASM-modullá** és futtasd 2-3 gépen determinisztikusan (azonos `output_commit` hash a go-kritérium).
3. Indíts **1 Hetzner CX22 relay-t** (€4.49/hó) bootstrap-hoz.
4. AI-setup: kezdd **Comfortable szcenárióval** (Claude Max 5x + ChatGPT Pro 5x + GLM, ~$206/hó) — a cross-consensus workflow ezt indokolja.

**Fázis-kapuk (benchmarkok, amelyek változtatnak a terven):**
- Ha a P0 WASM-determinizmus **nem** ad bit-azonos hasht cross-OS → maradj Linux-only workereken a bétáig (a macOS/Windows nice-to-have).
- Ha a iroh-gossip **nem** skálázódik 50+ node fölött NAT mögött → fontold meg a libp2p gossipsub-ra váltást (a transport maradhat iroh).
- Ha az XRPL Rust SDK **túl éretlen** a P4-ben → halaszd az XRPL-adaptert béta utánra; RLUSD-corridor helyett kezdetben csak CCTP-láncok.
- Ha a hálózat elér **stabil node-számot + stake-küszöböt** → nyisd a permissionless bétát (addig whitelist).

**Chain-prioritás:** **Base ELŐSZÖR** (olcsó EVM, egy Solidity-codebase 4 láncra újrahasznosítható, CCTP v2 kanonikus) → Solana → Sui → BNB/Avalanche (ugyanaz az EVM-contract) → Polkadot → XRPL (utolsó, SDK-kockázat miatt).

**AI-budget-eszkaláció:** kezdd Comfortable-lel; válts Accelerated-re (Max 20x + Pro 20x) csak akkor, ha 2 héten át folyamatosan limitbe ütközöl valós munkával.

## Caveats

- **Árak és SDK-verziók 2026 közepén érvényesek és gyorsan változnak** — a Claude Code v2.1.100+ token-infláció, a Codex 2026 áprilisi token-alapú átállás, a Hetzner 2026 áprilisi ~30-50% cloud-áremelés (RAM-hiány miatt) mind friss, volatilis tényezők; deploy előtt ellenőrizd a hivatalos ár-oldalakat.
- **A token-árak (ETH, SOL, DOT, XRP, SUI, BNB, AVAX) mid-2026-ban volatilisak** — az anchoring-USD-költségek, különösen az Ethereum/Base sorok, lineárisan skálázódnak az ETH-árral (a források $1,620 és $3,500 között szórtak); a Sui token-ár becslés (~$2) nem volt közvetlenül forrásolva. Az anchoring-táblák tájékoztató jellegűek.
- **A CCTP Sui-támogatás 2026 H1-re volt ígérve** — ellenőrizd a tényleges élesedést a Sui-adapter implementálása előtt; az XRPL nincs a CCTP-n (RLUSD-alternatíva).
- **A wgpu 1-2% FP32-hatékonyság egy nem optimalizált WGSL shaderre vonatkozik** — optimalizált shaderrel ~17% érhető el; a szám nem a WGSL plafonja, de a CUDA-first ajánlás így is áll a per-operation overhead miatt.
- **A biztonsági garanciák statisztikaiak és kis hálózaton gyengék** — a permissionless nyitás előtt kötelező a whitelist-béta; a committee-bribery/Sybil valós kockázat induláskor.
- **A VASP/CASP-regisztráció kérdése nyitott** — ügyvédi konzultációt igényel, nem mérnöki döntés.
- **Az iroh 1.0 megjelenési dátuma** a release-poszt szerint 2026. június 15. (nem 2025) — a pre-1.0 relay-támogatás 2026. szeptember 30-án szűnik meg, ezért a 1.0-ra kell építeni.