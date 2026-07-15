# Data-sourcing execution plan — dementia-exposome (27 countries)

*A source-backed plan for the **local (open-network) session** to progressively fill the map's data.
Built from a 5-region WebSearch research pass (July 2026). **This is a plan of WHERE to fetch, not the
data itself** — verify exact table IDs / DOIs / latest years at fetch time (WebFetch & most APIs are
blocked in the cloud build sandbox, so these were gathered from search snippets; confidence tags below).*

> Companion docs: `local-session-kickoff.md` (mission + drop-in mechanics), `data-download-points.md`
> (TW/JP/KR exact URLs), `prevalence-data-sources.md` (earlier deep-research), `good-to-have-data.md`.

---

## Answers to the 4 considerations (the owner's questions)

**1. Big databases lag 2–5 years; national offices & journals are fresher.**
World Bank / UN WPP 2024 sit ~1 yr back but WB pop is just re-badged WPP (no independent gain). **GBD 2021**
carries a 2021 data year (~4 yr lag); a **GBD 2023** release exists (~2 yr lag). NCD-RisC is uneven (BMI/diabetes
→2022, **blood pressure only →2019**). The worst lag is **national census age-structure**: fine where a fresh
census exists (Thailand 2025, Malaysia 2025 est., Pakistan 2023, Bangladesh 2022, most of Europe/Americas to
2024–25) but badly stale for **India (Census 2011, 2021 postponed → use MoSPI projections)**, **Myanmar (2014)**,
**Iran (2016, next round postponed)**. → **Rule: prefer the national stats office / a 2023–25 journal over the
global DB whenever one exists; fall back to WPP 2024 + WorldPop (modelled to 2030) for the stale-census countries.**

**2. Open API vs manual — very uneven.** All the *global aggregators* have open APIs (World Bank REST, UN WPP
Data Portal, WHO GHO OData, OECD SDMX). Among *national offices*, open/near-open APIs: **Japan e-Stat, Korea
KOSIS, US Census, Canada StatCan (SDMX), Brazil IBGE SIDRA, Mexico INEGI (token), Australia ABS (SDMX), NZ
Stats NZ, all EU offices (ONS/Nomis, Destatis GENESIS, INSEE, ISTAT, INE, GUS) + Eurostat, Turkey TÜİK (SDMX),
Malaysia OpenDOSM, Philippines OpenSTAT (PX-Web, semi-API)**. **Manual/interactive only:** Taiwan (per-dataset
data.gov.tw APIs, no unified one), China NBS, Thailand NSO, Vietnam GSO, Indonesia BPS, Myanmar CSO, India MoSPI/
Census, Pakistan PBS, Bangladesh BBS, Iran SCI. **GBD** is a middle case: rich, but needs a free login + interactive/
GHDx export.

**3. Sub-national disclosure varies by metric.** *Population-by-age* is the easiest sub-national layer (available
almost everywhere at admin-1, often admin-2). *Risk factors* are patchy. *Dementia prevalence* is rarely sub-national.
**WorldPop gridded age/sex is the universal equalizer** — it gives a sub-national age denominator below any admin
boundary for every country. **Genuinely sub-national dementia** exists directly only for: **Korea (si/do, NID),
India (states, LASI-DAD), Malaysia (states, NHMS), US (states, Alz Assoc), Canada (province, CCDSS), Australia
(state, AIHW)**; and via **GBD subnational modelling** for **Iran, China, India, Indonesia, Pakistan, Philippines,
Brazil, Mexico, Japan, UK** (NB **Turkey is national-only in GBD**). Europe has no pan-EU NUTS dementia layer.

**4. Journal papers lead the big DBs for dementia prevalence** in most countries — they *feed* GBD and are usually
fresher/more granular. Lead papers per country are in the tables below (e.g. India Lee 2023, China Jia 2020 +
Liu-Gao 2024, Japan Hisayama/Ninomiya, Korea NaSDEK 2023, Taiwan NHRI 2025, UK CFAS II, Bangladesh Lancet-SEA 2023,
Malaysia NHMS 2025, Iran/Turkey 2024–25 studies). **Practice: use GBD as the harmonized backbone + the only
internally-consistent risk-factor exposure set; overlay the national journal figure as the country-specific
cross-check.**

---

## Execution order (do it in these phases)

**Phase 0 — done / shipped:** PM2.5 (ACAG, 27+ countries), composite PAF (27, exposome.json), aging 65+ seed (46).

**Phase 1 — Global sweeps (breadth first; a few open pulls cover ~all countries).** Highest value/effort ratio.
| # | Pull | Source | Access | Fills |
|---|---|---|---|---|
| 1 | **65+ % all countries** | World Bank `SP.POP.65UP.TO.ZS` (`mrnev=1`) | open REST API | replaces the aging seed → `_data_in/world-65plus.csv` (iso2,pct) |
| 2 | **National pop-by-5yr-age** | UN WPP 2024 Data Portal / CSV | open API + CSV | aging + prevalence denominators, all countries |
| 3 | **Sub-national age denominator** | **WorldPop** age/sex GeoTIFF (R2025A, aligned to WPP 2024) | direct GeoTIFF | admin-1 65+ **and** the pop for admin-1 prevalence, every country |
| 4 | **Dementia prevalence + 4 risk exposures** | **GBD 2023** (IHME) Results Tool / GHDx | free login → CSV | national everywhere + admin-1 for the GBD-subnational set |
| 5 | **Measured risk factors** | NCD-RisC CSV (BP/BMI/diabetes) + WHO GHO OData | open | national exposome refresh (note BP →2019) |

**Phase 2 — Sub-national, low-effort (rich open APIs).** Wire admin-1/2 layers where an API makes it cheap:
**US** (Census ACS/PEP + CDC BRFSS/PLACES), **EU-6 via Eurostat** (`demo_r_pjangrp3` NUTS-3 age, `demo_r_pjanind2`
NUTS-2 65+ %, EHIS NUTS-2 risk for DE/ES/IT/PL) + national APIs (Nomis/Destatis/ISTAT/INE/GUS/INSEE), **Canada
StatCan**, **Australia ABS**, **NZ Stats NZ**, **Brazil IBGE SIDRA**, **Mexico INEGI**, **Japan e-Stat**, **Korea
KOSIS + KCHS (admin-2 risk factors!)**, **Malaysia OpenDOSM (state+district)**, **Turkey TÜİK (81 provinces)**,
**Philippines OpenSTAT**.

**Phase 3 — Per-country deep-dives (manual / paper; the gaps).** Interactive/PDF portals + journal extraction:
China NBS + Liu-Gao 2024, Taiwan (data.gov.tw + NHRI 2025), Thailand NSO 2025 census, Vietnam GSO, Indonesia
BPS + SKI 2023, India MoSPI + NFHS-5 (**district-level risk factors — best granularity anywhere**) + LASI-DAD,
Pakistan Census 2023, Bangladesh Census 2022 + Lancet-SEA 2023, Myanmar (2014 census — stale), Iran (SCI 2016 +
STEPS + 2024 meta-analysis).

---

## Global databases (fetch once, reuse everywhere)

| Database | URL | Vintage | Access | Sub-national | Licence |
|---|---|---|---|---|---|
| World Bank WDI (65+, risk factors) | data.worldbank.org · api.worldbank.org/v2 | ~2024 (=WPP) | **open REST API** + CSV | national | CC BY 4.0 |
| UN WPP 2024 | population.un.org/wpp | 2024 rev | **open API** + CSV | national | CC BY 3.0 IGO |
| IHME **GBD 2021 & 2023** | vizhub.healthdata.org/gbd-results · ghdx.healthdata.org | 2021 / 2023 | **free login** → export/GHDx | national + subnat set* | IHME non-commercial (attribution) |
| **WorldPop** age/sex grids | hub.worldpop.org · data.humdata.org/organization/worldpop | R2025A (→2030) | **direct GeoTIFF** | gridded (below any admin) | CC BY 4.0 |
| NCD-RisC | ncdrisc.org/data-downloads.html | BP→2019; BMI/DM→2022 | **open CSV** | national | free academic |
| WHO GHO | who.int/data/gho · ghoapi.azureedge.net/api | ~2021–22 | **open OData API** | national | open |
| OECD | data-explorer.oecd.org · sdmx.oecd.org | ~2023–24 | **open SDMX API** | national (members) | open |
| Alzheimer Europe — *Prevalence of Dementia in Europe 2025* | alzheimer-europe.org · zenodo.org/records/18339752 | **2025** | PDF + Zenodo data | national (EU) | open |
| ADI World Alzheimer Reports | alzint.org | WAR 2015 (prev.) | PDF | national | ADI terms |

\* GBD subnational set includes **Iran, China, India, Indonesia, Pakistan, Philippines, Brazil, Mexico, Japan, UK,
US** (and more) — **not Turkey, not the small EU states**. Global benchmark: Nichols 2022, *Lancet Public Health*
(GBD 2019) 57M→153M by 2050.

---

## Per-country source inventory (condensed)

Columns: **Dementia** (lead source · year · sub-national) · **Aging/pop-by-age** (office · API? · sub-national) ·
**Risk factors** (source · year · sub-national) · **Lead journal (DOI/PMID)**. Full URLs in the region notes at the
bottom; confidence noted where a value/DOI needs fetch-time verification.

### East Asia
| Country | Dementia | Aging / pop-by-age | Risk factors | Lead journal |
|---|---|---|---|---|
| 🇹🇼 Taiwan | NHRI nationwide survey · 2019–23 (**7.99%** 65+) · national (admin-1 frame) | DGBAS + 戶政司 via data.gov.tw · per-dataset API · **admin-2** (district, single-age, monthly) | HPA (smoking county-level) · ~2021–23 · county | NHRI 2025, **PMC12726225** (TW excluded from WHO GHO) |
| 🇯🇵 Japan | Hisayama/Ninomiya (12.1% 65+ 2022) + Toyama prefecture projections · national+pref | **e-Stat** · **open API (appID)** · admin-1/2 | NHNS (MHLW) · ~2019–23 · partial pref | Hisayama 10.1186/s13195-025-01909-1; Toyama 10.1186/s12877-021-02540-z |
| 🇰🇷 South Korea | **NaSDEK 2023 (9.25% 65+)** + NID observatory · **admin-1 (si/do)** | **KOSIS** · **open API** · admin-1/2 | **KCHS (KDCA) · 2024 · admin-2 (si-gun-gu!)** + KNHANES 2023 | Fact Sheet 2022 PMC9081392 |
| 🇨🇳 China | **Jia 2020 (6.0% 60+)** + **Liu-Gao 2024 (28 provinces)** | NBS 7th Census 2020 · interactive/manual · admin-1 | CCDRFS (China CDC) + CHARLS · →2018–19 · province/DSP | Jia PMID 33271079; Liu-Gao PMC11225804 |

### Southeast + South Asia
| Country | Dementia | Aging / pop-by-age | Risk factors | Lead journal |
|---|---|---|---|---|
| 🇹🇭 Thailand | Jitapunkul **2001** (3.3%, stale) → use GBD · national | NSO + **2025 census** · manual · province | NHES VI · 2020 · region | PMID 11460954 (stale) |
| 🇻🇳 Vietnam | Nguyen 2019 (~5%) · local; GBD national | GSO + 2019 census dashboard · interactive · province | WHO STEPS 2021 · national | PMID 31462907 |
| 🇮🇩 Indonesia | STRiDE 2022 (~27.9% adj) · national; **GBD admin-1** | BPS 2020 census · interactive · admin-1/2 | **SKI 2023** (588k) · province | STRiDE PMC10305093 |
| 🇵🇭 Philippines | Dominguez 2018 (community); **GBD admin-1** | **PSA OpenSTAT** (PX-Web) · semi-API · region/prov | FNRI eNNS · 2018–21 · region | 10.3233/JAD-180095 |
| 🇲🇾 Malaysia | **NHMS 2025 (~10% 60+) · admin-1 (state)** | **OpenDOSM** · **open API** · **state+district** | **NHMS 2025** (same survey) · state | PMID 33370858 |
| 🇲🇲 Myanmar | Aung 2020 (cognitive, local); GBD national | 2014 census + MMSIS · manual · State/Region (**stale**) | WHO STEPS 2014 · State/Region | PMID 32722689 |
| 🇮🇳 India | **Lee 2023 (7.4% 60+) · STATE (LASI-DAD)** | Census 2011 (**stale**, use MoSPI proj) + LASI · manual · district | **NFHS-5 2021 · DISTRICT (best anywhere)** | **10.1002/alz.12928**, PMID 36637034 |
| 🇵🇰 Pakistan | regional only; **GBD admin-1** | **Census 2023 (digital)** · PowerBI/PDF · district/tehsil | WHO STEPS 2013–14 (**2 provinces only**) | 10.1093/geroni/igae007 |
| 🇧🇩 Bangladesh | **Lancet-SEA 2023 (~8% 60+)** · national | **Census 2022 (digital)** · PDF · division/district | WHO STEPS 2018 · division | PIIS2772-3682(23)00117-8 (DOI verify) |

### Europe (+ pan-EU Eurostat)
| Country | Dementia | Aging / pop-by-age | Risk factors | Lead journal |
|---|---|---|---|---|
| 🇬🇧 UK | OHID Fingertips (recorded, **API, LAD/ICB**) + Alz Society | **ONS/Nomis** · **open API** · LAD/ward/OA | Fingertips (QOF+Active Lives) · 2023/24 · **LAD (API)** | CFAS II 10.1016/S0140-6736(13)61570-6 |
| 🇩🇪 Germany | Thyrian 2020 (**Kreis map**) + DAlzG | **Destatis GENESIS** · **open API** · **Kreis (NUTS-3)** | RKI GEDA · 2022 · Bundesland (Eurostat EHIS NUTS-2) | 10.1007/s00115-020-00923-y |
| 🇫🇷 France | Assurance Maladie (**département**) + France Alzheimer | **INSEE** · commune API + XLS · commune/dépt/région | SpF Baromètre **2024** · région (**not in Eurostat EHIS**) | PAQUID (Dartigues); BEH 2016;28-29 |
| 🇮🇹 Italy | ISS Osservatorio + Bacigalupo 2018 | **ISTAT** (esploradati) · **SDMX API** · provincia | ISS **PASSI**/d'Argento · 2021–23 · regione/ASL | 10.3233/JAD-180416 |
| 🇪🇸 Spain | Madrid drug-db (región) + Alz Europe 2025 | **INE Tempus3** · **open JSON API** · provincia | **ENSE 2023** · CCAA (NUTS-2) | PMID 25444413; 10.1038/s41598-025-10079-x |
| 🇵🇱 Poland | NFZ registered + Alz Europe 2025 (no real prev study) | **GUS BDL** · **open API** · gmina/powiat/woj | WOBASZ II + Eurostat EHIS · woj (NUTS-2) | PolSenior PMID 24937034 |
| 🇪🇺 **Eurostat** (all 6) | — (no NUTS dementia) | `demo_r_pjangrp3` NUTS-3 age; `demo_r_pjanind2` **NUTS-2 65+ % to 2025** · **open API+bulk** | EHIS NUTS-2 risk **DE/ES/IT/PL only** (not FR/UK) · 2019 | Alz Europe 2025 (Zenodo 18339752) |

### Americas + Oceania
| Country | Dementia | Aging / pop-by-age | Risk factors | Lead journal |
|---|---|---|---|---|
| 🇺🇸 US | Alz Assoc F&F (**state**) + HRS-HCAP | **Census ACS/PEP** · **open API** · **tract** | **CDC BRFSS (state) + PLACES (county/tract, API)** · 2023–24 | Manly HCAP JAMA Neurol 2022 (DOI verify) |
| 🇨🇦 Canada | **CCDSS (province/health region)** + Alz Society Landmark | **StatCan** · **SDMX API** · DA/CSD | CCHS · 2021–22 · **province/health region (API)** | (CCDSS admin; Landmark grey-lit) |
| 🇧🇷 Brazil | **ELSI-Brasil (5.8% 60+)** · national | **IBGE SIDRA** (2022 census) · **open API** · município | Vigitel 2023 (capitals) / PNS 2019 (**state**) | ELSI 10.1093/gerona/glad025 (verify) |
| 🇲🇽 Mexico | ENASEM/MHAS (~6.1%) · national | **INEGI** (2020) + CONAPO · **API (token)** · municipio | ENSANUT 2022 · national (state in microdata) | ENASEM PMC3557523 |
| 🇦🇺 Australia | **AIHW (state/territory)** + Dementia Australia | **ABS** · **SDMX API** · SA2/LGA | ABS NHS 2022 · **state/territory** | (AIHW model-based — rate caveat) |
| 🇳🇿 NZ | capture-recapture 2024 (national) | **Stats NZ** (to Jun 2025) · **API** · TA/local board | NZ Health Survey **2024/25** · region | 10.1002/gps.6131, PMID 39123300 |

### Middle East
| Country | Dementia | Aging / pop-by-age | Risk factors | Lead journal |
|---|---|---|---|---|
| 🇹🇷 Turkey | 2025 nationwide AD study + 2024 EHR (247k) · national (**not in GBD subnat**) | **TÜİK ABPRS 2024** · **API/SDMX** · **province (81)** | TÜİK Health Survey 2025 · NUTS-1 (coarse); STEPS 2025 pending | 10.1007/s44197-025-00435-5 |
| 🇮🇷 Iran | 2024 meta-analysis (BMC Public Health) · pooled; **GBD 31 provinces** | SCI Census **2016** (**stale**) · manual/PDF · province (31) | Iran STEPS (→2021, **31 provinces**) + GBD · province | 10.1186/s12889-024-18415-y |

---

## How each lands in the pipeline (drop-in reminders)

- **Aging 65+ (national):** `_data_in/world-65plus.csv` (`iso2,pct`) → `_load_pop65()` bakes `pop65` into `world-globe.geojson`. (World Bank sweep #1.)
- **Admin-1 prevalence (direct study):** `_data_in/{cc}-admin1-prevalence.csv` → `build_direct_prevalence()`. (China/India pattern.)
- **Admin-1 prevalence (rate × pop):** `_data_in/{cc}-admin1-pop.csv` (+ rates) → `build_admin_prevalence()` / `build_pop_rate_prev60()` (GBD rates × WorldPop). (JP/KR/WorldPop pattern.)
- **Admin-1 aging / risk factors (new layers):** emit `{cc}-aging.json` / extend `exposome.json`; add a `MAP_CFG`/`WORLD_METRICS` entry (mirror the `pop65`/PAF wiring).
- Always keep the **"modelled estimate"** wording and add each source's **licence/attribution** to `manifest.json`.

## Verify-at-fetch flags (marked MED/LOW in research)
- Exact DOIs: Manly HCAP (JAMA Neurol 2022), ELSI-Brasil (glad025), Bangladesh Lancet-SEA (lansea 100257), Taiwan NHRI & Liu-Gao — confirm from PMC/Crossref before citing.
- Latest years: WHO GHO per-indicator, WorldPop mosaic tag (R2025A?), India NFHS-6 release status, Myanmar 2024 census reliability, Bangladesh STEPS 2018 percentages (looked inconsistent in snippets).
- IHME GBD licence is **non-commercial (attribution)** — fine for this open educational tool; keep the attribution.
