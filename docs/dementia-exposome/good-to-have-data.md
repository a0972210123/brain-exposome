# Good-to-have data — dementia-exposome tool

*Datasets/literature that would make the calculator and map more precise. Prepared July 2026.*

**How to read the status column** (tested from the build/CI sandbox):
- ✅ **reachable here** — the pipeline (`scripts/build_data.py`) can fetch it directly; I can wire it in.
- 🔒 **blocked here** — the sandbox's egress proxy 403s this host; **owner downloads it** and drops the file in `public/data/…` (schema noted) or sends it to me → I wire `build_data.py` to consume it.
- 🔑 **needs account/query** — free but requires a login or an interactive query/export.

Current tool already uses: ACAG PM2.5 (county×year, town, world country), taiwan-atlas boundaries, and a **county-level** modelled prevalence from a committed MOI-2023 snapshot. The items below would upgrade those.

---

## 1. Taiwan (highest value)

| Dataset | What it upgrades | Source | Status |
|---|---|---|---|
| **鄉鎮市區 population by single-year age** (MOI 戶政司 #77132, `ODRP014`) | Turns the map's **county-level** prevalence into a real **town-level (368) estimate** (age structure varies within a county) | data.gov.tw/dataset/77132 · RIS API `ris.gov.tw/rs-opendata/api/v1/datastore/ODRP014/{yyymm}` | 🔒 blocked |
| **County population by 5-yr age band** (MOI) | Replaces the approximate committed county 65+ shares with exact age bands → better modelled rate | data.gov.tw / ris.gov.tw (`ODRP…`) | 🔒 blocked |
| **NHRI 2020–2023 survey — MCI prevalence by age** | Adds a second map layer / readout: **mild cognitive impairment** (the pre-dementia stage the owner asked about) | NHRI 全國社區失智症流行病學調查 (projects.nhri.edu.tw/spdc) + the 2024 press release tables | 🔒 blocked (PDF; owner extracts the MCI age-band table) |
| **NHIRD diagnosed dementia by county/age** | A *diagnosed* (healthcare-utilisation) prevalence layer to compare against the modelled one | 衛福部 NHIRD (application required) | 🔑 restricted |
| **County/district risk-factor prevalence** — hypertension, diabetes, hearing/vision, smoking | Lets the map show *modifiable-factor* burden by area, not just age-driven prevalence | 國健署 HPA 健康促進統計 / 國民健康訪問調查 (NHIS) | 🔒 blocked (owner downloads CSV/PDF) |
| **鄉鎮市區 boundary refresh** (latest MOI #7441) | Keeps district borders current (we use taiwan-atlas 2021) | data.gov.tw/dataset/7441 → NLSC | 🔒 blocked (npm `taiwan-atlas` mirror ✅ used instead) |

**Schema the pipeline expects for the town-level upgrade:** a CSV with `district_code` (village/town code) + single-year age × sex columns (`people_age_000_m/_f …`). `build_data.py` already has the roll-up hook (`fetch_population`) — drop the CSV in `scripts/_data_in/` and it will produce the authoritative `tw-dementia-modelled.json` at town granularity.

---

## 2. Global (for the country dropdown + future maps)

| Dataset | What it upgrades | Source | Status |
|---|---|---|---|
| **Country population by age** (UN WPP) | Enables modelled dementia prevalence for **other countries** (needed before any non-TW map) | population.un.org/wpp (CSV) or the Data Portal API | 🔒 blocked |
| **Country/subnational dementia prevalence** (GBD 2021) | Real per-country (and some subnational) prevalence → other-country maps & calibration | IHME GBD Results Tool `vizhub.healthdata.org/gbd-results` | 🔑 query/export |
| **ADI World Alzheimer Report figures** | Headline prevalence/projections per region | alzint.org/…/dementia-statistics | ✅ (web) |
| **ACAG sub-national PM2.5** — China / India / USA / Canada | Sub-national PM2.5 for those countries' future maps (finer than the country value) | `s3://satpmdata/V6GL03/RegionSummaries/{Country}…REGIONAL…csv` | ✅ reachable |
| **Country admin boundaries** (geoBoundaries ADM1/ADM2, Natural Earth ADM0) | Geometry for other-country choropleths | geoboundaries.org / raw.githubusercontent.com/nvkelso/natural-earth-vector | ✅ reachable |
| **GBD subnational risk-factor exposure** | Per-region modifiable-factor prevalence for richer maps | IHME GBD | 🔑 query/export |

---

## 3. Brain-age calibration (nice-to-have)

| Item | What it upgrades | Source | Status |
|---|---|---|---|
| **Published BrainAGE per-condition deltas** (diabetes ≈ +2–4.6 yr, stroke +2.6, smoking +2.1, PM2.5 +2–6…) | Lets us **calibrate/validate** the λ=0.6 + log₂×5.5 mapping against measured brain-age studies, or offer a "direct brain-clock" cross-check mode | Cole 2020 (PMC7280786), Moguilner/Ibáñez *Nat Med* 2024, cardiometabolic meta 2025 (PMC11908789) | ✅ (papers; extraction manual) |
| **Age/sex dementia incidence baseline** (EURODEM / GBD) | Optional absolute-risk framing alongside the relative readout | Launer 1999; GBD 2021 | 🔑 |

---

## What the owner can most usefully grab (priority)
1. **MOI #77132 town population by age** 🔒 → unlocks the real town-level Taiwan prevalence map (biggest single upgrade).
2. **NHRI MCI age-band table** 🔒 → adds the MCI layer the owner wanted.
3. **UN WPP country population by age** 🔒 → prerequisite for *any* other-country map.
4. **国健署 county risk-factor prevalence** 🔒 → a modifiable-factor burden map.

Send any of these (or drop into `scripts/_data_in/`) and I'll extend `build_data.py` + the page to consume them. All external data must keep its licence/attribution (see `manifest.json`).
