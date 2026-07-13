# Global dementia-prevalence data sources — for expanding the prevalence map

*Deep-research pass (fan-out web search → source fetch → adversarial verification → synthesis; 103 agents, 22 claims confirmed / 3 refuted). Prepared July 2026. Verify exact per-unit tables against the primary source before ingestion — see caveats.*

## Why this exists

The map already shows **sub-national PM2.5** for TW/JP/KR/CN/US/IN. Only **Taiwan** has a *prevalence* layer, built by the tool's method: **age-band prevalence rate × population-by-age, per admin unit**. To extend prevalence maps to other countries we need three ingredients per country:

1. **age-specific dementia prevalence rates** (% by 5-yr age band),
2. **sub-national (admin-1) population by age**,
3. **country-level total** (to sanity-check the summed estimate).

**Headline:** open/free data now exists to model admin-1 prevalence for every priority country. **GBD 2021 (IHME)** is the universal rate backbone; **WorldPop age/sex grids** are the population denominator; **WHO 2021** is the global calibration anchor. **China and India already have published admin-1 modelled prevalence** and need no fallback.

---

## Prioritised shortlist (the fastest path)

| Category | Single best source | Access | Machine-fetchable? |
|---|---|---|---|
| **1. Age-specific rates** | **GBD 2021 Results Tool** (IHME), overridden by a national survey where one exists | free-login **query-export** | ⚠️ interactive export (one login step) |
| **2. Sub-national pop-by-age** | **WorldPop age/sex-structured gridded population** (CC-BY 4.0) | open | ✅ direct GeoTIFF URLs |
| **3. Country total (calibration)** | **WHO 2021 Global status report** + GBD 2021 per country | open PDF | ⚠️ human download (WHO 403s bots) |

**Ready at admin-1 now (published modelled studies, no fallback):** 🇨🇳 China (Liu/Gao 2024, 28 provinces), 🇮🇳 India (Lee 2023, states).
**Fallback = GBD 2021 national rates × WorldPop admin-1 pop-by-age:** 🇯🇵 Japan, 🇰🇷 Korea, 🇺🇸 USA, and every next-expansion country (UK, Germany, Canada, Australia, Brazil, Indonesia, Thailand, Vietnam).

---

## Category 1 — Age-specific dementia prevalence rates

### Backbone (any country): GBD 2021
- **IHME GBD Results Tool** — https://vizhub.healthdata.org/gbd-results/ · query `measure=Prevalence`, `cause=Alzheimer's disease and other dementias`, by location/age/sex/year → CSV.
- **Granularity:** national + GBD regions + global, by 5-yr age band and sex. **No admin-1** → must be paired with a sub-national population source.
- **Licence:** IHME Free-of-Charge **Non-commercial** User Agreement (attribution required; commercial redistribution needs permission — see open question on hosting derived values).
- **Access:** free registration → interactive **query-export** (not cleanly machine-fetchable without the session). Global age-standardised 55+ prevalence ≈ **3,975.8 / 100,000** (2021).

### National surveys (override GBD where they exist)
| Country | Survey | What it gives | Access |
|---|---|---|---|
| 🇨🇳 China | **Jia et al. 2020**, *Lancet Public Health* (CCAS, n=46,011, 60+) | National age/sex rates (overall **6.0%** in 60+); **total 15.07M** | journal (human DL; Lancet 403s bots) |
| 🇮🇳 India | **Lee et al. 2023**, *Alzheimer's & Dementia* (LASI-DAD) | National **7.4%** (60+, ≈8.8M) **+ state estimates** | PMC10338640 (open) |
| 🇯🇵 Japan | **Hisayama Study** (7 waves 1985→2022) | Japan age-band anchors (12.1% 65+ in 2022; vintage-sensitive) | PMC12751825 (open) |
| 🇺🇸 USA | **ADAMS / Plassman 2007** (n=856, 70+) | National age-specific rates (5.0% @71–79 → 37.4% @90+) | hrsdata.isr.umich.edu (free-login) |
| 🇰🇷 Korea | National Institute of Dementia / Korean Dementia Observatory | national rates (URL/licence unresolved — see open questions) | — |

### Regional fallback (last resort)
- **Prince et al. 2013**, *Alzheimer's & Dementia* — age-specific prevalence for 60+ across **21 GBD regions** (most 5–7%; Latin America 8.5%). Data through 2009 → **secondary multiplier only**, superseded by GBD 2021. None of our target countries are in the (contested) sub-Saharan band.

---

## Category 2 — Sub-national population by age

### Primary: WorldPop age/sex-structured gridded population
- https://www.worldpop.org — per-country grids split by **sex × 5-yr age band**, GeoTIFF, **CC-BY 4.0**, **machine-fetchable** (direct URLs).
- Zonally aggregate to Natural Earth admin-1 polygons (the same polygons the PM2.5 layers already use) → the **age-banded denominator** GBD/national rates multiply against. **This is the age-band source** (see the HRSL caveat below).

### High-resolution total-count cross-check: Meta/CIESIN HRSL
- https://registry.opendata.aws/dataforgood-fb-hrsl/ · S3 `dataforgood-fb-data/hrsl-cogs/` (us-east-1), **CC-BY 4.0**, **no login** (anonymous `aws s3 --no-sign-request`, verified HTTP 200).
- **Limitation (a stronger claim was refuted):** HRSL gives **total counts + only coarse subgroups** (e.g. 60+), **NOT 5-yr age bands**. Use it as a high-res total-count sanity check, **not** as the age-band denominator.

### National-only: UN World Population Prospects
- population.un.org/wpp — authoritative national by-age, **but national only** (no admin-1). Useful for calibrating WorldPop national totals, not for the map itself.

---

## Category 3 — Country-level totals (calibration)

- **WHO 2021 Global status report on the public health response to dementia** — https://www.who.int/publications/i/item/9789240033245 · **55M now → 78M (2030) → 139M (2050)**. Free PDF (human DL; WHO 403s bots). Global sanity-check for summed admin-1 case counts.
- **National totals:** China **15.07M** (Jia 2020), India **8.8M** (Lee 2023); GBD 2021 per-country counts for the rest.

---

## Per-country expansion status

| Country | Rates | Sub-national pop | Admin-1 prevalence today | Route |
|---|---|---|---|---|
| 🇹🇼 Taiwan | NHRI 2020–23 ✅ | MOI (county snapshot) | **live** | done |
| 🇨🇳 China | Jia 2020 national ✅ | WorldPop | **Liu/Gao 2024, 28 provinces** ✅ | ingest study table |
| 🇮🇳 India | Lee 2023 national ✅ | WorldPop | **Lee 2023, ~14–18 states** ✅ (rest → GBD) | ingest study table |
| 🇯🇵 Japan | Hisayama / GBD | WorldPop | none | GBD/national rates × WorldPop |
| 🇰🇷 Korea | Korean Dementia Obs. / GBD | WorldPop | none | GBD/national rates × WorldPop |
| 🇺🇸 USA | ADAMS/Plassman / GBD | WorldPop | none (Dhana 2023 used this method) | GBD/national rates × WorldPop |
| 🇬🇧🇩🇪🇨🇦🇦🇺🇧🇷🇮🇩🇹🇭🇻🇳 | GBD 2021 | WorldPop | none | GBD national × WorldPop |

---

## Caveats & gotchas (from adversarial verification)

- **Don't mix raw rates across borders.** Diagnostic-criteria differences (DSM-III vs ICD-10 …) can swing measured prevalence ~10× (Wu 2015). Use **one harmonised backbone (GBD 2021)** for cross-country comparability; treat national surveys as country-specific refinements.
- **Feed age-SPECIFIC rates, not crude aggregates.** The China provincial (2.62–13.53%) and Hisayama figures are crude/community prevalence blending age structure with rate; the tool's method only recovers the age-structure component if the *rate inputs* are age-specific.
- **HRSL ≠ age bands** (refuted claim): use WorldPop for the age-banded denominator.
- **ADAMS exact bands** (refuted claim): use Plassman's real bands (5.0% @71–79 → 37.4% @90+), not the "4/11/28%" figures that circulated.
- **Sex stratification cautiously** (refuted claim): higher female *prevalence* is largely longevity-driven; age-specific *incidence* is often sex-similar.
- **Coverage gaps:** India's states cover ~14–18 of 36; China's study excludes Tibet/Ningxia/Hainan → remaining units still need GBD fallback.
- **Fetchability:** only WorldPop/HRSL are cleanly machine-fetchable. GBD needs an interactive login-export; all journal/WHO sources are human downloads whose publisher domains frequently 403 bots — **the exact per-province/per-state tables must be transcribed/verified by a human** (or the local session, see `local-session-handoff.md`) before ingestion.
- **Licence:** GBD is non-commercial (fine for this open educational tool, attribution required); WorldPop + HRSL are permissive CC-BY 4.0.

## Open questions (for a follow-up pass or the owner)
1. Concrete URL + table + licence for **Korea** (NaSDEB / nid.or.kr) and **Japan** national (Ninomiya/MHLW).
2. Is there a **downloadable per-province/per-state CSV** from Liu/Gao 2024 (China) and Lee 2023 (India), or must admin-1 values be transcribed from figures?
3. Do any next-expansion countries (UK CFAS, Brazil ELSI, Indonesia/Thailand/Vietnam 10/66) have **published admin-1** prevalence, or all GBD fallback?
4. Does WorldPop age/sex cover all targets at admin-1 with consistent 5-yr bands + recent vintage; best crosswalk to Natural Earth admin-1?
5. Is IHME's **non-commercial** licence compatible with hosting derived admin-1 values in a public client-side map (attribution-only vs permission request)?

## Resolved — 2026-07 local session

*Answered from an open-network machine (the local session in `local-session-kickoff.md`). Each item cites what was actually fetched/verified.*

1. **Korea & Japan national rates — found; both usable.**
   - **Korea:** 중앙치매센터 (National Institute of Dementia) annual **「대한민국 치매현황」 / Korean Dementia Observatory** — https://www.nid.or.kr (publications). 65+ age-band prevalence (65+ standardised ≈ **9.25% (2023)**, rising to **≈38% at 85+**), from the national dementia registry + KOSIS population; cross-check *Dementia Epidemiology Fact Sheet 2022* (Ann Rehabil Med, e-arm.org). Population half: **KOSIS** 시도×age (kosis.kr/eng). Licence: NID reports public; KOSIS is **KOGL** (Korea Open Government Licence, attribution). → `kr-dementia-rates.csv`.
   - **Japan:** the **2024 MHLW research group (Ninomiya, Kyushu U — 久山町/Hisayama + 3 towns, surveyed 2022–23)** produced the current nationwide age-band dementia + MCI estimates (65+ ≈ **12.1%** in 2022; projections to 2050/2060). Peer-reviewed age-band anchor: **Hisayama 37-yr trends**, *Alz Res Ther* 2025, **PMC12751825** (open, CC BY). Population half: **e-Stat** 都道府県×5歳階級 (e-stat.go.jp/en; 政府統計, free reuse w/ attribution). → `jp-dementia-rates.csv`.

2. **China & India per-admin tables — resolved (shipped this session).** No publisher ships a clean per-row CSV, but **both are transcribable tables, not figures**:
   - China **Appendix G** = *Supplementary Table 4* inside supplementary **`mmc1.docx`**, reachable via the **Elsevier OA CDN** `https://ars.els-cdn.com/content/image/1-s2.0-S2666606524001111-mmc1.docx` (PMC gates `/bin/` binaries behind a JS proof-of-work; the els-cdn mirror does not). `python-docx` → 28 provinces.
   - India **Table 2** = in-article HTML at `pmc.ncbi.nlm.nih.gov/articles/PMC10338640/` (`id=T2`), BeautifulSoup → 22 states/UTs (+ a pooled "NE states" row and the national row, both excluded).
   Now shipped as `{cn,in}-modelled.json` (PRs #125, #126).

3. **Expansion-country admin-1 — effectively all GBD fallback; two partial exceptions.**
   - **UK:** no modelled *community* admin-1 layer, but **OHID/PHE Fingertips "Dementia Profile"** has **recorded (diagnosed, QOF) prevalence by local authority + ICB** for England — https://fingertips.phe.org.uk/profile-group/mental-health/profile/dementia. Usable as a *diagnosed-prevalence* layer (different metric label; England only). CFAS = national age-specific community rates.
   - **Brazil:** **ELSI-Brazil** (Bertola et al. 2023, *Alz & Dementia*) gives national + **5 macro-regions** (N/NE/Midwest/SE/S), **not** the 27 states → state-level still GBD.
   - **Indonesia / Thailand / Vietnam:** **10/66** = catchment-site prevalence only, no admin-1 → GBD.
   ⇒ Keep **GBD 2021 national × WorldPop admin-1** as the comparable backbone for all of these; UK-England-diagnosed and Brazil-5-region are optional, separately-labelled extras.

4. **WorldPop → Natural-Earth admin-1 crosswalk — feasible; one band caveat.**
   - Source: **WorldPop "Age and sex structures", 2020, 1km GeoTIFF**, per-country + global, unconstrained + constrained, **CC BY 4.0** — https://hub.worldpop.org/geodata/summary?id=24798 (also on HDX). Files `…_{m,f}_{age}_2020_1km.tif`; age codes `00` (0–1), `01` (1–4), then 5-yr `05…80`, **top band `80` = 80+**.
   - Crosswalk: zonal-**sum** each age×sex raster over the *same* Natural-Earth admin-1 polygons the PM2.5 layers use (`rasterstats.zonal_stats(polys, tif, stats='sum')`), m+f per band. Prefer **unconstrained 2020** for consistent global coverage; calibrate national totals against **UN WPP**.
   - **Caveat:** WorldPop tops out at **80+**, coarser than the pipeline's `POP_BANDS` (…`80_84`,`85p`). Either model 80+ as one band (pair with a GBD **80+** rate) or split 80+ using a national 80–84 / 85+ ratio from UN WPP. All targets covered at admin-1; vintage 2020.

5. **IHME licence — OK for a free, non-commercial map with attribution; two hard limits.**
   Per the **IHME Free-of-Charge Non-Commercial User Agreement** (https://www.healthdata.org/Data-tools-practices/data-practices/ihme-free-charge-non-commercial-user-agreement) + Terms:
   - Non-commercial users get a royalty-free licence to download and **use, share, modify or build upon** the data — incl. publishing results on a **website** — **with attribution**. Hosting our **derived** admin-1 values (national rate × WorldPop pop = a transformed estimate) is within this.
   - **Limit 1 — don't re-host the raw dataset:** users "may not provide third parties the ability to download IHME datasets from user-provided hosting facilities" (linking to IHME's own download is fine) ⇒ ship only the **derived** per-admin numbers, never the raw GBD CSV as a download.
   - **Limit 2 — non-commercial only:** ads/monetisation = "commercial use" → needs an IHME commercial licence. (IHME's own visualisations are **CC BY-NC-ND 4.0**.)
   ⇒ For the current free/ad-free educational site: **attribution-only is fine** ("IHME GBD 2021, non-commercial"). If the site ever runs ads, request commercial permission (services@healthdata.org) first.

## Key sources
- GBD 2021 Results Tool — https://vizhub.healthdata.org/gbd-results/
- WorldPop — https://www.worldpop.org · HRSL — https://registry.opendata.aws/dataforgood-fb-hrsl/
- WHO 2021 — https://www.who.int/publications/i/item/9789240033245
- Jia 2020 (China) — Lancet Public Health, PIIS2468-2667(20)30185-7 · Lee 2023 (India) — *Alzheimer's & Dementia*, doi:10.1002/alz.12928 (PMC10338640)
- Liu/Gao 2024 (China provinces) — Lancet Reg Health W Pac, PIIS2666-6065(24)00111-1 · Hisayama 2025 — PMC12751825 · ADAMS/Plassman 2007 — hrsdata.isr.umich.edu · Prince 2013 — *Alzheimer's & Dementia*, doi:10.1016/j.jalz.2012.11.007 · Wu 2015 — PMC4510821
