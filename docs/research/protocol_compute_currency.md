# Protokoll-natív elszámoló érme ("compute currency") — teljes monetáris és tokenomikai terv

> **Research input — canonical owner: tokenomics / "compute-currency" (ADR-0002
> Track C).** Owns the monetary design (compute-peg, internal work-credit vs token),
> stabilization mechanisms, MiCA classification, and the economic simulation
> framework. The architecture docs (`hybrid_decentralized_compute_network.md`,
> `gpu_compute_network_sui_render_libp2p.md`) cross-reference this for ALL economic
> and regulatory detail rather than restating it. Reference input, not an accepted
> decision — see the ADR-0002 Track C gate.

## Executive summary

Máté, a rövid válasz: **igen, van értelme protokoll-natív elszámoló egységnek, de NEM szabad tokent kibocsátani a hálózat korai szakaszában.** A helyes út egy **belső, compute-alapú munkajegy (work-credit)**, amely nem tőzsdén jegyzett kriptovaluta, hanem zárt hurkú elszámoló egység — pontosan úgy, ahogy a Helium a "Data Credit" egységet használja. Az érme értékmércéje ne a USD legyen, hanem egy **gördülő (rolling) benchmarkhoz kötött standardizált munkaegység**, a protokoll pedig **market-maker-ként** vételi és beváltási árat jegyez.

Három fő megállapítás:
- **Value-base:** A tiszta compute-peg fix benchmarkkal determinisztikusan deflációssá teszi az érmét (a hardver-hatékonyság javulása miatt — az Epoch AI szerint "Performance per dollar improves around 30% each year", a FLOP/s-per-dollar "doubles every ~2.5 years"), ami Gresham-dinamikát okoz. A **gördülő benchmarkhoz kötött compute-peg** stabil a jelenlegi compute-árhoz képest — ez a helyes választás. Az energia-peg elméletileg elegáns, de a kWh-ár régiónkénti szórása megoldhatatlan "melyik kWh?" problémát okoz.
- **Funkcionális scope:** A **2A belső credit** MiCA-szempontból a legkönnyebb út (loyalty-scheme / limited-network kivétel). A **2B tőzsdei token** csak bizonyított organikus kereslet esetén.
- **Stabilizáció:** A **3C (tiszta belső credit) + buyback-floor** a legkoherensebb, kiegészítve a **3A (teljes fedezet)** treasury-elvekkel. A **3B (algoritmikus)** mechanizmust a Terra/Luna post-mortem alapján elutasítom a korai szakaszra.

A végső ajánlás egy archetípus-rangsor és egy P0-P5 bootstrapping ütemterv, amely a credit-et a P2 fázisban vezeti be, a 2B token döntést pedig a P5-re halasztja explicit metrika-kapukkal.

---

## 1. Monetáris elmélet sidebar

A pénz három funkciója: **unit of account** (stabil ár az árazáshoz — a compute-hálózat legfontosabb igénye), **medium of exchange** (likvid csere), **store of value** (vásárlóerő-megőrzés). Egyetlen eszköz ritkán tölti be mindhármat kiválóan egyszerre — ez a monetáris trilemma.

A DePIN compute-tokenek (RNDR, AKT, GLM, LPT, TAO) mind ugyanabban buknak el: lebegő tokenként jó store of value-lehetnek, de **rossz unit of account-ok** — ezért árazzák a munkát USD-ben/benchmark-egységben, és csak settlementkor váltják tokenre oracle-áron. Ez a probléma a compute currency tervezés magja.

A compute-peg mögött a **munkaérték-elmélet** (labor theory of value) vs. **határhaszon-elmélet** (marginal utility) régi vitája húzódik. Egy "1 munkaegység = 1 érme" konstrukció termelési-költség-alapú értékmérce — rokona a technokrata mozgalom 1930-as évekbeli "energia-tanúsítvány" (energy certificate) elképzelésének, ahol Howard Scott "energy theory of value"-je szerint minden jószág közös mértéke az energia (ergben/joule-ban denominálva). A modern közgazdaságtan elveti a tiszta munka/energia-értékelméletet, mert az árat végső soron a marginális haszon határozza meg, nem a ráfordítás — így a compute currency "belső értéke" a **beváltható compute haszna**, nem a ráfordított munka.

Gold standard analógia: a protokoll egy **központi bank compute-tartalékkal arany helyett**. A 3C+buyback modell ezt másolja: fix beváltási árfolyam, arbitrázs a piac és a protokoll-ablak között. Kulcskülönbség: az arany kínálata exogén és lassan nő, a compute kínálata **endogén és a hardverjavulással deflálódik** — ez a compute currency egyedi kihívása. Végül **Hayek "Denationalisation of Money" (1976)** tézise közvetlenül releváns: versengő magánvaluták jobb pénzt eredményeznek, mint az állami monopólium, mert a kibocsátó reputációja és a vásárlóerő-stabilitás versenyeznek — de Hayek is hangsúlyozta, hogy a **stabil vásárlóerő** a siker feltétele, nem a kibocsátó öncélú szűkössége.

---

## 2. DELIVERABLE 1 — Value-base összehasonlítás és ajánlás

### 2.1 (a) COMPUTE-PEG

**Létező hálózatok árazása:**
- **Render (RENDER):** OctaneBench-óra (OBh) az egység; a tudásbázisuk szerint "1€ RNDR Credit = 100 OBh Tier 1-en", saját render farm **$0.003/OBh**. Kulcs (SuperRenders): *"OctaneBench-hour billing normalizes render cost to throughput delivered: a faster GPU finishes in fewer hours, so the same work costs the same regardless of card generation."* Ez pontosan a **gördülő benchmark** elve — a throughput-alapú árazás automatikusan semlegesíti a hardvergeneráció-váltást.
- **Akash (AKT):** reverse auction — a piac (nem benchmark) árazza a compute-ot; az AKT csak "unit of measurement", fizetni USDC-ben is lehet (magasabb díjjal); 2026 márciusában bevezetett BME (USD-ben fizetett compute-ért AKT-t égetnek).
- **Livepeer (LPT):** munkát ETH-ben fizetik (~$0.02/perc transcoding), LPT staking/koordináció; kettős modell.
- **Bittensor (TAO):** 21M fix supply, block-emisszió 41% miner / 41% validator / 18% subnet owner; nincs presale/founder-allokáció (fair launch).
- **Golem (GLM), io.net, Nosana, Gensyn:** lebegő utility token, USD/benchmark-árazás, settlementkor tokenre váltás.

**Deflációs kiigazítási probléma (a fő elméleti kérdés):** A GPU price-performance az Epoch AI szerint évi ~30%-kal javul ("Performance per dollar improves around 30% each year"), a FLOP/s-per-dollar ~2,5 évente duplázódik (Hobbhahn & Besiroglu, 2022, ~2,45 év duplázódási idő).
- **Fix-benchmark peg:** ha 1 token = 1 "2026-os GPU-másodperc" örökre, a token reál-vásárlóereje compute-ban évente ~20-30%-kal **nő** → determinisztikus defláció. *Feature* a compute-vásárlónak (megtakarítási eszköz), *bug* a hálózatnak (Gresham-dinamika: senki nem költ felértékelődő érmét → megöli a forgalmat/medium-of-exchange funkciót). A node-ok szeretik (jövőbeli bevételük felértékelődik).
- **Gördülő-benchmark peg:** 1 token = 1 "aktuális csúcs-GPU-másodperc"; a benchmark rebasel, a token **stabil marad a jelenlegi compute-árhoz** képest. Helyes unit-of-account viselkedés.
- **Depreciation-indexed hybrid:** explicit ~20%/év deflációs index; kiszámítható, de bonyolult.

### 2.2 (b) ENERGY-PEG
Precedensek: technokrata energia-tanúsítványok (1930-as évek, Howard Scott, ergben/joule-ban), John Pease Norton 1932-es "electric dollar" javaslata; modern kripto: SolarCoin, Energy Web (de egyik sem valódi kWh-peg, csak energiatermelés-jutalmazó token).

"Melyik kWh?" probléma: az Eurostat szerint "The EU average price in the second half of 2025 was €0.1837 per kWh" (nem-háztartási), tartomány "highest in Ireland (€0.2552 per kWh)... lowest... Finland (€0.0748 per kWh)", Németország €0.2264/kWh. Nagykereskedelmi szinten a német day-ahead átlag 2025-ben €89.32/MWh (Bundesnetzagentur), €583/MWh csúccsal (2025. jan. 20.) és 573 negatív-áras órával. Egy energy-peg-nek konkrét nagykereskedelmi indexet kellene választania (pl. ENTSO-E day-ahead súlyozott átlag), különben manipulálható.

Fit: az energia a compute domináns marginális költsége, így energy-peg ≈ compute-költség-peg kevesebb hardvertorzítással. DE a perf/watt-javulás miatt az energy-peg is deflálódik compute-ban, csak lassabban. Őszinte ítélet: **nem jobb, mint a gördülő compute-peg**, és kevésbé intuitív a felhasználónak.

### 2.3 (c) BASKET/INDEX-PEG
Precedensek: IMF SDR (USD/EUR/CNY/JPY/GBP), Keynes "bancor" (1944, nyerscikk-kosár), Szabo kosár-koncepció. Konstrukció: pl. 40% compute + 30% energia + 30% fiat. Kritika: minden komponens külön oracle és manipulációs felület; a rebalancing governance-t igényel; solo fejlesztőnek kezelhetetlen. MiCA szerint **egyértelműen ART** ("több érték/jog kombinációja"). **Elutasítom.**

### 2.4 (d) ENDOGÉN / FLATCOIN
- **RAI (Reflexer):** legrelevánsabb precedens — nem-pegged, ETH-fedezetű stable asset, **on-chain PID-kontroller** (Kp/Ki/Kd) állítja a redemption-price-t egy target köré. 2020-as tesztben ~4% alatti volatilitás, míg az ETH 250%+-ot mozgott. A PID compute-ár-index körül is használható redemption-rate szabályozásra.
- **Frax Price Index (FPI):** CPI-U flatcoin. A Frax a FIP-188-cal (posztolva 2023. feb. 15., "98% voting in favor, according to a snapshot on Feb. 23", Cointelegraph) elhagyta a fractional-algoritmikus modellt és **100% fedezetre** váltott — a CoinDesk szerint az akkor 5. legnagyobb, >$1B kapitalizációjú stablecoint teljesen fedezetté tették, "using protocol earnings to increase the stablecoin reserves". Tanulság: **még a legkifinomultabb csapat is feladta a részleges fedezetet.**
- **Nuon (Laguna Labs):** első "flatcoin", Truflation napi inflációs oracle, Arbitrum, túlfedezett.
- **Ampleforth SPOT:** CPI-adjusted USD, zero-liquidation tranching.
- **Fully endogenous work-anchored:** a protokoll az egyetlen beváltási helyszín; cloud credit / airline miles / company scrip, de transzferálható. Ez a 3C magja.

### 2.5 (e) Miért NE USD-peg?
USDC létezik; MiCA szerint EMT, amihez credit/e-money institution engedély kell — solo fejlesztőnek elérhetetlen. Nulla differenciáció.

### 2.6 (f) Miért NE lebegő utility token?
A volatilitás megöli a unit-of-account funkciót — ez a RNDR/AKT/GLM baja (állandó USD-újraárazás). Egy jobot nem lehet értelmesen árazni egy 50-90%-ot ingadozó tokenben.

### 2.7 Értékelési mátrix

| Kritérium | Compute-peg (gördülő) | Compute-peg (fix) | Energy-peg | Basket | RAI-PID | Endogén work-anchored |
|---|---|---|---|---|---|---|
| Unit-of-account | Kiváló | Gyenge | Jó | Jó | Közepes | Kiváló |
| Store-of-value | Stabil | Erős (felértékel) | Stabil | Stabil | Változó | Compute-ban stabil |
| Oracle-függés | Közepes | Alacsony | Közepes-magas | Magas | Magas | Alacsony |
| Halálspirál | Alacsony | Alacsony | Alacsony | Közepes | Közepes | Alacsony |
| MiCA | Bizonytalan | Bizonytalan | Valószínűleg ART | ART | Algoritmikus (tiltott) | Utility/kivétel |
| Komplexitás | Közepes | Alacsony | Közepes | Magas | Nagyon magas | Alacsony |

### 2.8 AJÁNLÁS (Deliverable 1)
**Compute-egység-alapú beváltható credit, gördülő benchmarkkal, protokoll-mint-market-maker.** Ez az egyetlen konstrukció, amely (1) kiváló unit-of-account, (2) elkerüli a fix-benchmark Gresham-csapdát, (3) legkedvezőbb MiCA-profil, (4) solo-fejlesztőnek implementálható. A RAI-féle PID-kontroller opcionális finomhangoló réteg a 2B fázisra.

---

## 3. DELIVERABLE 2 — Funkcionális scope modellek

### 3.1 Model 2A — BELSŐ CREDIT (zárt hurok)
Felhasználó USDC/fiat on-ramppel (CCTP multi-chain rail) creditet vásárol jegyzett áron (1 credit = 1.00 USDC). Node-ok munkával creditet keresnek. Beváltható compute-ra vagy készpénzre a treasuryn keresztül (díjjal/késleltetéssel). Nem tőzsdén jegyzett.

Analógiák és tanulságok: **AWS credits / Steam wallet** (zárt hurok, limited network); **airline miles** (transzferálható másodpiac, kibocsátó kontrollál); **BOINC credit** (nincs cash-out → "pontrendszerré" degradál, gyenge node-incentíva); **WoW gold** (endogén infláció mob-farmolásból → a creditet valós munkához kell kötni, nem korlátlan mintelés).

MiCA: a Recital kizárja a scope-ból a *"csak a kibocsátó által elfogadott, birtokosok között technikailag nem transzferálható"* eszközöket (loyalty-scheme példa). **Kritikus tervezési döntés: ha a credit nem transzferálható → teljesen MiCA-n kívül** (mint egy loyalty-pont). Ha transzferálható → utility-token (Title II whitepaper-notifikáció), de nem EMT/ART, ha nem fiat-referált. Ez a regulatórikusan legkönnyebb út. Magyar/osztrák szempont: az EMT-t a MiCA harmonizálja EU-szinten; ha a credit nem fiat-par-value, nem e-money (ügyvédi megerősítés szükséges, ez nem jogi tanács).

### 3.2 Model 2B — TŐZSDEI TOKEN
Kezdeti elosztás: **fair launch / work-mining only** (node-ok 100% munkával keresik, nincs presale/VC/airdrop) — legtisztább jogi/közösségi narratíva; a Bittensor pontosan ezt csinálja (nincs pre-mine/presale/founder-allokáció). Előny: nincs "unregistered security" gyanú, nincs bennfentes-dump. Alternatíva presale/points-airdrop: gyorsabb tőke, de whitepaper-terhek és reputációs kockázat.

Likviditás: **POL** (protocol-owned liquidity, a PUMPKIN-kontextusból ismert); **LBP** (Balancer-aukció, fair ár-felfedezés); DEX chainenként (Solana→Raydium/Orca, Base/ETH→Uniswap, Sui→Cetus).

MiCA teljes megfelelés (utility): whitepaper (CA-WP) notifikáció NCA-nak (nincs előzetes jóváhagyás utility tokennél); kivételek <150 személy/tagállam VAGY ≤€1M/12hó VAGY qualified investor. Költség: CASP tőkekövetelmény €50,000 (tanácsadás) / €125,000 (custody/exchange) / €150,000 (trading platform) + jogi díjak (~€30-80k utility whitepaper-notifikáció).

Volatilitás-kezelés: **quote work-egységben, settle tokenben oracle-áron** (RNDR/AKT minta); a node és user árfolyamkockázatot visel a job idejére — mitigáció: rövid árfolyam-lock, vagy a credit-réteg megtartása unit-of-account-ként a lebegő token felett (→ kettős-token).

### 3.3 Hibrid út: 2A → 2B
One-way door: a tőzsdére kerülés után a "limited network" MiCA-kivétel elvész, beindul a spekuláció — ezért a 2B döntést halaszd és metrika-kapuhoz kösd. Migráció: a credit-ledger fix rátával (1 credit = 1 token) tokenre konvertálható egy "conversion event"-kor. **A 2A-t mint-on-work modellel tervezd (nem fix supply)**, hogy a token később 1:1 leképezhető legyen; tartsd a benchmark-verziózást és rebase-historyt on-chain kezdettől a folytonos unit-of-account-ért.

---

## 4. DELIVERABLE 3 — Stabilizációs mechanizmusok

### 4.1 Mechanizmus 3A — TELJESEN FEDEZETT (≥100%)
Reserve: USDC (elsődleges, CCTP minden chainen), SUI/ETH/SOL (≤20% cap), T-bill RWA (sDAI/USDY/BUIDL) hozamért.

Multi-chain PoR: a treasury 8 chainen fragmentált. **Chainlink Proof of Reserve + Secure Mint** (a mintelés leáll, ha a supply meghaladná a reserve-et); cross-chain aggregátor (CCIP vagy a checkpoint-mechanizmus) medianizált feedet publikál. MakerDAO tanulság: surplus buffer a peg-védelemhez (a DAI túlélt több crypto-telet RWA + USDC fedezettel).

Beváltás: instant (kicsi) vs. queued (nagy, T+n a bank-run ellen). **Díj-korridor** soft-peg sávot hoz létre (vétel 1.00, beváltás 0.99 → arbitrázs a [0.99, 1.00] sávba tereli).

Reserve-hozam fedezheti a fejlesztést. **MiCA:** EMT-knél tilos kamatot fizetni birtokosoknak; ha a credit nem EMT (nem fiat-par-value), a protokoll megtarthatja a hozamot (besorolás-függő, ügyvédi megerősítés). Tőkehatékonysági kritika: 100%+ fedezet lassítja a bootstrapot (valós USDC-t kell behozni), de ez az ára a halálspirál-immunitásnak.

### 4.2 Mechanizmus 3B — ALGORITMIKUS / HIBRID
Mechanizmus: token-mintelés node-fizetésre keresletnél (seigniorage), burn a díjakból; PID-kontroller redemption-rate a gördülő compute-index körül; fractional reserve ratio (Frax v1).

**KÖTELEZŐ Terra/Luna post-mortem:** a UST bukása 2022 májusában a **reflexív körkörös fedezet** miatt történt: az UST-t a LUNA értéke fedezte, a LUNA értéke az UST-keresletből jött. Bizalomvesztéskor a mechanizmus egyre több LUNA-t mintelt egy zuhanó piacra — halálspirál. A méret drámai: a Bloomberg szerint a UST és a Luna "melted down in spectacular fashion... a shadow of the combined $60 billion they once commanded"; a LUNA a $119.18-as csúcsról (2022. ápr. 5.) omlott össze, a MIT Sloan/CFI szerint "wiped out $50 billion in valuation" három nap alatt.
- Hasonlóság (veszély): ha a token-jutalmat a token-kibocsátás fedezi, kereslet-összeomláskor ugyanaz a spirál fenyeget.
- Különbség (védelem): ha a credit mögött **exogén compute-kereslet** áll (userek USDC-t hoznak compute-ért), van exogén értékhorgony — de csak ha a fedezet **nem** a saját token.

Circuit breakerek: min collateral floor (≥40%), bounded issuance (max X% mint/epoch), oracle-védelem (TWAP + több forrás + kiugrás-limit). Stressz-tesztek: kereslet -80%, token -90%, reserve-drawdown, oracle-attack (Deliverable 4 mátrixban futtatandó).

**Ítélet:** **elutasítom a korai szakaszra** — solo fejlesztő nem tud PID-et kalibrálni és halálspirált menedzselni. Csak nagy hálózatnál, kettős-token modellben (HNT↔DC), ahol a governance-token abszorbeálja a volatilitást.

### 4.3 Mechanizmus 3C — TISZTA BELSŐ CREDIT (protokoll-only beváltás)
1 credit = 1 munkaegység örökre (gördülő benchmarkkal rebaselve). Transzferálható P2P, de egyetlen sink a compute-vásárlás, egyetlen source a compute-teljesítés (+ protokoll kezdeti eladása jegyzett áron). Protokoll vételi árat jegyez (1.00 USDC/credit).

Természetes arbitrázs-sáv: **plafon** = protokoll eladási ár (senki nem fizet többet a másodpiacon); **padló** = compute utility-value (ha az ár ez alá esik, érdemes creditet venni és compute-ra beváltani). **Buyback-floor mitigáció:** a protokoll a díjbevételből buyback-programot futtat floor-áron (0.95 USDC) → fél-fedezett hibrid, erősíti a node-incentívát (a node tudja, hogy ki tud szállni a floor-áron).

Gyengeség: a node-nak bíznia kell a jövőbeli keresletben (nehéz cash-out). Mitigáció: OTC desk, buyback, részleges beváltási garancia (→ konvergál 3A felé). Könyvelési egyszerűség és MiCA-könnyűség: nincs mint/burn algoritmus, csak ledger + jegyzett ár; legvédhetőbb (utility/limited-network).

### 4.4 Token-flow diagramok
**3A (fedezett):**
```
User --USDC--> Treasury --mint--> Credit --> User
User --Credit--> Node (compute payment)
Node --Credit--> Treasury --USDC (minus fee)--> Node   [cash-out]
Treasury: reserve_USDC >= credits_outstanding * peg_price  [PoR-enforced]
```
**3C (credit + buyback):**
```
Protocol --sell @ 1.00--> Credit --> User
User --Credit--> Node (job payment)
Node --Credit--> {hold | spend | sell OTC | buyback@floor}
Protocol fee revenue --> Buyback pool --buy @ 0.95 floor--> recycle Credit
Peg band: [0.95 floor, 1.00 ceiling]
```

### 4.5 Formulák
```
p_t = peg-ár USDC-ben; W_t = munkaegység t-ben; f = take-rate (0.05)
credits_minted_t = W_t * (1 - f)          # node reward
protocol_fee_t   = W_t * f
credits_bought   = USDC_in / p_t
compute_delivered = credits_spent          # 1:1 (rebased)
if market_price < floor: credits_bought_back = min(fee_pool, demand) / floor_price
RR_t = reserve_USDC_t / (credits_outstanding_t * p_t);  require RR_t >= 1.0
```

### 4.6 Coherence archetípus-térkép (3×2×4)

| # | Archetípus | Value-base | Scope | Stabilizáció | Rang |
|---|---|---|---|---|---|
| A1 | Compute-pegged belső credit, market-maker | gördülő | 2A | 3C + buyback | **★ 1.** |
| A2 | Fedezett compute-credit beváltási garanciával | gördülő | 2A | 3A | 2. |
| A3 | Kettős-token: fix credit + lebegő token | gördülő+endogén | 2B | 3C+3A-lite | 3. (P5+) |
| A4 | Energia-indexelt fedezett token | energia | 2B | 3A | 4. |
| A5 | RAI-szerű PID compute-flatcoin | RAI-PID | 2B | 3B | 5. (kísérleti) |

Inkoherens (elvetve): basket + 2A (értelmetlen zárt hurokban); 3B + 2A (a seigniorage tőzsdei árat igényel); fix-benchmark + 2B (determinisztikus defláció → spekulatív buborék). Az A1 nyer: legegyszerűbb, legkönnyebb MiCA-profil, és a buyback-floor pótolja a 3C node-incentíva gyengeséget.

---

## 5. Helium BME deep-dive + kettős-token értékelés

### 5.1 Helium BME (a KULCS precedens)
A Helium modell **pontosan** a "belső credit + lebegő token" minta:
- **HNT:** lebegő value-token, 223M max supply, kétéves halving, Pyth-oracle ár.
- **Data Credit (DC):** fix USD-értékű ($0.00001/DC, $1 = 100,000 DC), **nem transzferálható**, csak HNT égetésével keletkezik.
- **BME:** userek DC-t vesznek (HNT-t égetve); node-ok HNT-t kapnak (mintelve); egyensúlyban mintelt = égetett HNT.
- **Net Emissions (HIP-20):** napi 1,643.84 HNT cap; ha kevesebb HNT ég, a különbözetet újra-mintelik a subnetwork-treasurybe.
- Subnetworkök: IOT/MOBILE al-tokenek, HNT-re válthatók.

Tanulság: a **DC = fix-értékű work-credit** (unit of account), a **HNT = value-accrual token** (store of value). Ez feloldja a trilemmát. **Ez a user eredeti kérdésének a válasza:** a "stablecoin-szerű exchange coin" = work-credit (DC-analóg); az értékfelhalmozás = lebegő token (HNT-analóg).

### 5.2 Helium usage reality-check
A Messari State of Helium Q4 2025 szerint a Helium bevétele rekordot döntött 2025 decemberben **$1.9M havi** szinten, **$22.4M annualizált** run-rate szinten; "Helium's annualized revenue, excluding discretionary burns, reached $11.0 million" (a Q4 diszkrecionális burn $2.9M volt, $31,765/nap). A Messari szerint "On January 2, 2026, Helium's CEO, Amir Haleem, announced the suspension of this experiment to focus on user growth and carrier offload rather than discretionary burn" — a 2025 augusztusától futó, a Helium Mobile 100%-os előfizetői bevételét HNT-vételre/burnre irányító kísérletet leállította. Tanulság: még a legnagyobb DePIN-ek organikus bevétele is szerény ($11-22M/év) a piaci kapitalizációhoz képest — ez a kettős-token modell realitás-horgonya.

### 5.3 Egy-token vs. kettős-token

| Szempont | Egy-token | Kettős-token |
|---|---|---|
| Unit-of-account | Gyenge (volatilis) | Kiváló (fix credit) |
| Store-of-value | A tokenben | A value-tokenben |
| Komplexitás | Alacsonyabb | Magasabb |
| MiCA | Utility/ART | Credit=limited-network, token=utility |
| Node-incentíva | Közvetlen | Credit-et keres, token opcionális |
| Precedens | RNDR, AKT | **Helium (bizonyított)** |

Ítélet: a kettős-token a **P5+ végállapot**; P2-P4-ben az egy-credit modell (A1) elég — a value-token korai bevezetése felesleges komplexitás és MiCA-kockázat.

---

## 6. DELIVERABLE 4 — Hálózati modellezési mátrix (szimulációs keretrendszer)

### 6.1 Állapotváltozók és ágensek
```python
@dataclass
class NetworkState:
    n_gpu_heavy: int; n_cpu_verifier: int   # tiered model
    hw_efficiency: float                    # +25%/yr drift
    credits_outstanding: float; treasury_usdc: float
    token_price: float; peg_price: float    # peg = USDC per work-unit (rolling)
    elec_cost: np.ndarray                    # per-region €/kWh
    reputation: np.ndarray
    job_demand: float; demand_elasticity: float; churn_rate: float
```
Régiós villamosenergia-kalibráció: EU nem-háztartási átlag €0.1837/kWh (Eurostat 2025 H2), Finnország €0.0748 – Írország €0.2552, Németország €0.2264; nagykereskedelmi német €0.089/kWh (Bundesnetzagentur 2025).

### 6.2 Flow-egyenletek
```
job_cost_credits = work_units                          # 3C: 1:1
# 2B: job_cost_tokens = work_units * peg_price / oracle_token_price
revenue_node = work_units_done * credit_price_usdc * (1 - take_rate)
cost_node    = (gpu_watt * hours * elec_cost_region) + amortized_hw
profit_node  = revenue_node - cost_node
hw_efficiency_{t+1} = hw_efficiency_t * (1 + 0.25)^(1/epochs_per_year)
job_demand_t = base_demand * (price_t / price_0) ** (-elasticity)
treasury_{t+1} = treasury_t + usdc_inflow - cashouts + reserve_yield
reserve_ratio  = treasury_t / (credits_outstanding * peg_price)
```

### 6.3 Szcenárió-mátrix

| Paraméter | Bear | Base | Bull |
|---|---|---|---|
| Kereslet-növekedés/év | -50% | +100% | +500% |
| Token-spekuláció (2B) | pánik | semleges | FOMO |
| Hardver-defláció | 20%/év | 25%/év | 35%/év |
| Villamosenergia-sokk | +50% | 0% | -30% |
| Versenytárs GPU-ár (ceiling) | RTX 4090 $0.16/hr (Salad) | $0.35/hr (Vast.ai) | $0.52/hr median |
| Regulatórikus sokk | delisting/geo-block | nincs | kedvező |
| Node-churn | +40% | 10% | 5% |

Versenytárs-kalibráció (2026): RTX 4090 — Salad $0.16/hr, Vast.ai $0.17-0.35/hr, RunPod $0.20/hr, medián ~$0.52/hr (AIMultiple index); RTX 5090 medián $0.66/hr; H100 SXM $1.33-3.29/hr. Ezek az **exogén ár-plafonok** — a hálózat nem árazhat feljebb.

Output-metrikák: peg-deviáció, treasury-runway (hó), node-profitabilitás tierenként/régiónként, halálspirál-indikátorok, token-holding Gini.

**EU-gazdasági valóság-check:** egy német otthoni RTX 4090 (~450W) €0.387/kWh háztartási ár mellett ~0.45 kWh × €0.387 = **€0.174 áramköltség/óra**, míg a Vast.ai piaci ár $0.16-0.35/óra (~€0.15-0.32). **A német otthoni GPU marginálisan veszteséges vagy alig nyereséges**; egy finn (€0.0748/kWh) vagy izlandi node profitábilis. A szimulációnak ezt régiónként kell modelleznie — a prior report is jelezte ezt.

### 6.4 Monte Carlo + ABM
Ajánlott stack: **radCAD** (a cadCAD egyszerűbb/gyorsabb API-jú derivatívája, CADLabs) — token-engineering standard, PID/GEB-szimulációkhoz bizonyított (a RAI-t is ezzel modellezték); polars-kompatibilis. Alternatíva: custom ABM numpy/polars, mesa (ágens-központú), TokenSPICE (EVM-in-the-loop), Machinations.io (kereskedelmi, vizuális).

```python
import numpy as np, polars as pl
from dataclasses import dataclass

def policy_demand(state, params, rng):
    shock = rng.normal(params['demand_growth'], params['demand_vol'])
    return state.base_demand * (1 + shock) * (state.credit_price/params['price_0'])**(-params['elasticity'])

def policy_node_supply(state, params):
    profit = state.credit_price*(1-params['take_rate']) - state.gpu_watt_hr*state.elec_cost
    active = profit > 0
    churn = np.where(active, params['churn_base'], params['churn_base']*4)
    return active, churn

def policy_peg_rebase(state, params, t):
    if t % params['rebase_period'] == 0:
        state.peg_price *= (1 + params['hw_deflation'])**0.25   # rolling benchmark
    return state.peg_price

def update_treasury(state, inflow, cashout, params):
    yield_ = state.treasury_usdc*params['tbill_apy']/params['epochs_yr']
    state.treasury_usdc += inflow - cashout + yield_
    state.reserve_ratio = state.treasury_usdc/max(state.credits_outstanding*state.peg_price,1e-9)
    return state

def buyback(state, params):
    if state.market_price < params['floor']:
        buy = min(state.fee_pool, state.sell_pressure)
        state.fee_pool -= buy; state.credits_outstanding -= buy/params['floor']
    return state

def run_sim(params, n_epochs=1460, seed=0):    # 4 yrs daily
    rng = np.random.default_rng(seed); state = init_state(params); rows=[]
    for t in range(n_epochs):
        demand = policy_demand(state, params, rng)
        active, churn = policy_node_supply(state, params)
        state.peg_price = policy_peg_rebase(state, params, t)
        work = min(demand, active.sum()*params['cap_per_node'])
        fee = work*params['take_rate']
        state.credits_outstanding += work*(1-params['take_rate'])
        state.fee_pool += fee*state.credit_price
        inflow = work*state.credit_price
        cashout = churn.sum()*params['avg_balance']
        state = update_treasury(state, inflow, cashout, params)
        state = buyback(state, params)
        rows.append(snapshot(state, t))
    return pl.DataFrame(rows)

def monte_carlo(param_grid, n_runs=500):
    results=[]
    for scenario in param_grid:
        for seed in range(n_runs):
            results.append(compute_metrics(run_sim(scenario, seed=seed), scenario, seed))
    return pl.DataFrame(results)   # peg_dev, runway, gini, spiral_flag
```
Kalibráció: a 10. szakasz P/S-táblázata mint sanity-anchor — a DePIN compute-tokenek 13x-500x P/S-en forognak (narratíva-, nem cash-flow-alapú árazás).

### 6.5 Kettős-token variáns
Két mód: **single-token (A1)** — csak credit, token_price=peg_price konstans, nincs spekuláció; **two-token (A3)** — credit (fix) + value-token (lebegő, BME); `token_price = f(fee_burn, emission, speculation_overlay)`, itt aktiválódik a spekulációs sokk és halálspirál-indikátor.

---

## 7. Oracle-dizájn + rebase-protokoll
Manipuláció-rezisztens work-unit-ár: belső aukciós adat (ha van volumen — chicken-egg); külső referenciák (Vast.ai/io.net/Akash API + ENTSO-E energia); **medianizált több-forrású oracle** (median(belső, Vast.ai, Akash, energia)); TWAP a flash-manipuláció ellen; peg-ár napi/heti, benchmark-verzió negyedéves.

Rebase-protokoll (RTX 6090 érkezésekor):
```
1. Új GPU → governance/bizottság méri az új perf-et.
2. rebase_factor = perf(RTX6090) / perf(reference_card)
3. Peg-rebase: peg_price *= rebase_factor, benchmark_version++
4. On-chain rebase-event; grace period N epochig (régi+új párhuzam)
5. Credit-egyenlegek nominálisan változatlanok; a beváltható compute rebasel.
```

---

## 8. Bootstrapping (P0-P5)

| Fázis | Mi történik | Coin-lépés |
|---|---|---|
| P0 | PoC, iroh P2P, WASM/CUDA execution | Nincs coin; fee-only USDC |
| P1 | Első settlement-adapter, néhány node | Nincs coin; USDC |
| P2 | Első fizetős jobok, credit-ledger | **Belső work-credit (A1: 2A+3C+gördülő peg+buyback)** |
| P3 | Reputáció, tier-modell, több chain | PoR-treasury (3A-elvek) |
| P4 | Skálázódó kereslet, OTC-desk | Buyback-program a díjbevételből |
| P5+ | Bizonyított organikus kereslet | **2B kettős-token DÖNTÉS (A3), csak metrika-kapunál** |

Go/no-go metrikák (P5 kapu): organikus havi díjbevétel küszöb felett több hónapon át (benchmark: Helium ~$11M/év organikus, Livepeer ~$1M/év); független node-ok száma küszöb felett (nem Sybil); credit-forgási sebesség (költik, nem hoardolják); kényelmes treasury-runway. Ha nem teljesül: **maradj credit-only.** A token nem cél, hanem eszköz.

---

## 9. Architektúra-integráció (trait/contract vázlatok)

SettlementAdapter trait (credit-ledger mint új "chain" — elegáns újrahasznosítás, a meglévő checkpoint-mechanizmus horgonyozza):
```rust
pub trait SettlementAdapter {
    fn settle(&self, job: &JobReceipt) -> Result<SettlementProof>;
    fn balance(&self, account: &AccountId) -> Amount;
}
pub struct CreditLedgerAdapter {
    peg_price: PegOracle, ledger: MerkleLedger, treasury: MultiChainTreasury,
}
impl SettlementAdapter for CreditLedgerAdapter {
    fn settle(&self, job: &JobReceipt) -> Result<SettlementProof> {
        let credits = job.work_units;          // 1:1 in 3C
        self.ledger.transfer(job.payer, job.node, credits)?;
        self.checkpoint_anchor()               // reuse existing mechanism
    }
    fn balance(&self, account: &AccountId) -> Amount { self.ledger.balance(account) }
}
```
Move (Sui) credit modul:
```move
module compute_credit::credit {
    struct Credit has key, store { value: u64 }
    struct Treasury has key { reserve_usdc: u64, peg_price: u64, credits_out: u64 }
    public fun buy_credit(t: &mut Treasury, usdc: Coin<USDC>): Credit {
        let amount = coin::value(&usdc) / t.peg_price;
        t.reserve_usdc = t.reserve_usdc + coin::value(&usdc);
        t.credits_out = t.credits_out + amount;
        assert!(t.reserve_usdc >= t.credits_out * t.peg_price, E_UNDERCOLLATERALIZED);
        Credit { value: amount }
    }
    public fun redeem_for_compute(c: Credit): u64 { let Credit { value } = c; value }
}
```
Solidity (EVM):
```solidity
contract ComputeCredit {
    uint256 public pegPrice; uint256 public creditsOut; IERC20 public usdc;
    AggregatorV3Interface public reserveFeed;   // Chainlink PoR
    function buyCredit(uint256 usdcIn) external returns (uint256 credits) {
        credits = usdcIn / pegPrice;
        usdc.transferFrom(msg.sender, address(this), usdcIn);
        creditsOut += credits;
        require(reserve() >= creditsOut * pegPrice, "undercollateralized");
        _mint(msg.sender, credits);
    }
    function redeemForCompute(uint256 credits) external { _burn(msg.sender, credits); }
}
```
CCTP on-ramp flow: USDC bármely chainen → CCTP a treasury-chainre → `buyCredit` mintel → credit-ledger jóváír. Közvetlenül a prior report CCTP-railjére épül.

---

## 10. DePIN comparables (P/S és usage-realitás)

| Token | Annualizált bevétel (forrás) | Típus | Market cap | P/S |
|---|---|---|---|---|
| RENDER | ~$2.0-2.7M (est., Messari burns 2025 + Render 2025 Annual Report) | Job burn (BME) | ~$680M-1.3B | ~270x-500x |
| HNT | $22.4M run-rate / $11.0M organikus (Messari Q4 2025) | DC burn (USD) | ~$346-454M (2025 vége) vs ~$45M (2026 közepe, ⚠️ konfliktus) | ~2x-15x |
| TAO | ~$172M (⚠️ CMC AI, nem-verifikált) | AI subnet usage | ~$2.0-2.6B (2026) | ~13x (puha) |
| LPT | ~$1.0M (4× Q1 2026 fees $257.3K, Messari) | ETH fees | ~$77.6-111.8M | ~75x-108x |
| FIL | ~$2.0-3.0M network fees (Messari 2025) | On-chain fees (burned) | ~$567-590M (2026) | ~230x |
| AKT | ~$253K (Messari Q1 2026 lease) / ~$5M (self-reported) | Lease spend | ~$175-330M | ~35x-1,300x |

Kulcs-takeaway: minden DePIN compute-token nagyon magas P/S-en (75x-500x) forog → **narratíva/jövőbeli-növekedés, nem cash-flow alapú árazás**. A self-reported vs. analyst szakadék (Akash $5M vs. $253K) univerzális — óvatosan kalibrálj. Az adatok 2025-2026-os "extreme fear" piacon készültek (FIL all-time-low, HNT/LPT/RENDER 70-99% le a ciklus-csúcsokról) — konzisztens valuációs dátumot válassz a modellben. Megjegyzés: a HNT market cap 2025 vége vs. 2026 közepe között rendelési nagyságrendbeli eltérést mutat (⚠️ dátum-bázist ellenőrizni kell), a TAO $43M/negyedév ($172M/év) bevétele pedig CoinMarketCap "CMC AI" forrásból származik, nem elsődleges kutatóházból — kezeld puha adatként.

---

## 11. Risk register: coin vs. no-coin

| # | Kockázat | Coin | No-coin (fee-only USDC) | Net |
|---|---|---|---|---|
| 1 | MiCA-besorolási hiba | Magas | Nincs | No-coin |
| 2 | Halálspirál/reflexivitás | Közepes (3C-nél alacsony) | Nincs | No-coin |
| 3 | Oracle-manipuláció | Közepes | Alacsony | No-coin |
| 4 | Bootstrapping (chicken-egg) | Magas | Közepes | No-coin |
| 5 | Fejlesztői komplexitás (solo) | Magas | Alacsony | No-coin |
| 6 | Unit-of-account instabilitás | Alacsony (credit stabil) | Nincs (USD) | Döntetlen |
| 7 | Likviditás-fragmentáció (8 chain) | Magas (2B) | Alacsony | No-coin |
| 8 | Node-incentíva-gyengeség | Közepes (buyback mitigál) | Alacsony | No-coin enyhén |
| 9 | Reputációs/rug-gyanú | Közepes | Alacsony | No-coin |
| 10 | Elmulasztott value-capture upside | — (coin megfogja) | Magas (elmarad) | **Coin** |

Net assessment: a mérleg a **no-coin (fee-only USDC) felé billen** a korai szakaszban — a prior report ajánlása helyes volt P0-P1-re. A coin egyetlen erős érve a **value-capture upside** (10. sor): sikeres hálózat esetén egy token milliárdos value-t foghat meg (lásd comparables). Döntési kritérium: a credit-et (A1) akkor vezesd be, ha a unit-of-account előny (stabil compute-árazás) és a treasury-float konkrét operatív hasznot hoz; a lebegő tokent (2B) csak a P5-kapunál.

---

## 12. Regulatórikus elemzés — MiCA (őszinte bizonytalanság)
**Ez nem jogi tanács; ügyvédi megerősítés kötelező.**
- **ART:** "nem-EMT crypto-asset, amely stabil értéket céloz más értékre/jogra/kombinációra hivatkozva." A basket (1c) egyértelműen ART. A compute-peg **bizonytalan:** ha a compute-egység "érték/jog, amelyre hivatkozik" → ART; ellenérv: **hozzáférést ad egy szolgáltatáshoz** (compute) → utility-token.
- **Utility token:** "egyetlen célja hozzáférést adni a kibocsátó szolgáltatásához." A compute-credit valószínűleg ide esik, ha nem fiat-par-value. Feltétel: a szolgáltatásnak **működnie kell** → ezért P2 a helyes bevezetési pont, nem korábban.
- **EMT:** csak egy hivatalos valutára hivatkozik. A compute-credit nem EMT, ha nem USD-par-value. **Kerüld a fiat-peg-et.**
- **Limited-network/loyalty kivétel:** ha csak a kibocsátó fogadja el és nem transzferálható → teljesen MiCA-n kívül (AWS-credit/loyalty-pont). Legerősebb védelmi pozíció.
- **Algoritmikus stablecoin:** a MiCA gyakorlatilag **betiltja** ("nem tekinti ART-nak, mert nincs explicit reserve") → a 3B jogilag veszélyes az EU-ban. Újabb érv a 3C/3A mellett.
- **Kivételek:** ART <€5M/12hó átlagos kinnlevőség alatt engedély-mentes (whitepaper kell); utility <€1M/12hó vagy <150 személy/tagállam whitepaper-mentes. Reális mentességek a korai hálózatnak.

Összegzés: a legvédhetőbb út a **nem-transzferálható vagy protokoll-only-beváltható compute-credit (A1)**, a limited-network/utility kivételre támaszkodva, a fiat-peg (nem EMT), a basket (nem ART) és az algoritmikus mechanizmus (nem tiltott) elkerülésével.

---

## 13. Végső ajánlás + döntési tábla

Rangsorolt archetípusok: **1. A1** (compute-pegged belső credit, 2A+3C+gördülő peg+buyback — ajánlott indulás); 2. A2 (fedezett, 2A+3A); 3. A3 (kettős-token, Helium-modell, P5+); 4-5. A4/A5 nem ajánlott.

Ajánlott path: **P2-ben indíts belső work-creditet (A1). Halaszd a 2B kettős-token döntést P5-re explicit metrika-kapuval.**

| Kérdés | Döntés | Trigger a változtatáshoz |
|---|---|---|
| Kell coin? | Igen, de credit-only (nem token) P2-től | Ha a unit-of-account/float haszon nem realizálódik → maradj fee-only |
| Value-base? | Gördülő compute-peg | Súlyos oracle-manipuláció → energia-index fallback |
| Scope? | 2A belső credit | 2B csak P5-kapunál |
| Stabilizáció? | 3C + buyback-floor | 3A-elvek, ha beváltási-hitelesség kell |
| Fiat-peg? | Soha (EMT elkerülés) | — |
| Basket? | Soha (ART elkerülés) | — |
| Algoritmikus? | Soha (MiCA-tiltás) | — |
| Transzferálható? | Kezdetben nem (limited-network) | Csak token-launchkor |
| Kettős-token? | P5+, ha metrika-kapu OK | Helium-szerű organikus bevétel több hónapon át |
| Szimulációs stack? | radCAD + polars | — |

**Bottom line, Máté:** ne építs tokent most. Építs egy **gördülő-compute-pegged, protokoll-market-maker belső creditet buyback-floorral (A1)** — a Helium Data Credit és az AWS-credit metszete: stabil unit-of-account a job-árazáshoz, MiCA-könnyű (limited-network/utility), és egy solo fejlesztőnek implementálható. A lebegő value-tokent (Helium HNT-analóg) tartsd fenn a P5+ végállapotra, és csak akkor húzd meg a ravaszt, ha a hálózat bizonyítja az organikus keresletet. A no-coin/fee-only mérce marad a benchmark, amit a credit-nek konkrét operatív haszonnal kell felülmúlnia.

---

### Módszertani megjegyzés a forrásokról
A DePIN pénzügyi mutatók (10. szakasz) 2025-2026-os adatok; a bevétel-definíciók protokollonként eltérnek (burn vs. fee vs. lease-spend), és több market-cap konzisztencia-ellenőrzést igényel a felhasználástól függő valuációs dátum miatt. A TAO-bevétel puha (nem elsődleges) forrásból. A monetáris-elméleti és regulatórikus állítások nyilvános forrásokra (Eurostat, Bundesnetzagentur, Epoch AI, Messari, MiCA-szövegek, Chainlink, Reflexer/RAI, Frax dokumentáció) épülnek; a MiCA-besorolás bizonytalan és **nem helyettesíti a jogi tanácsadást**.