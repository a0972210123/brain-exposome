# Data acquisition status & deferred list — 2026-07 local session

*Single-glance status of every country/dataset the prevalence + MCI maps need, and — per the
owner's request — the explicit **deferred list** with reasons. Companion to `data-download-points.md`
(exact URLs/schemas) and `prevalence-data-sources.md` (the "Resolved 2026-07" section: JP/KR/WorldPop/
IHME-licence answers). Reachability tested from an open-network machine, July 2026.*

## Live now

| Layer | Coverage |
|---|---|
| PM2.5 (admin-1) | 27 countries (ACAG V6.GL.03) — done |
| Dementia prevalence | 🇹🇼 Taiwan **town-level, 368 鄉鎮市區** (PR #128) · 🇨🇳 China 28 provinces (#125) · 🇮🇳 India 22 states/UTs (#126) |

## What each remaining prevalence layer needs

Three ingredients per country: **(1) admin-1 population by 5-yr age**, **(2) age-specific dementia
(and/or MCI) rate**, **(3) a national total to sanity-check**. A map lights up only when (1)+(2) exist.

| Country | (1) Admin-1 pop×age | (2) Dementia rate | MCI | Verdict |
|---|---|---|---|---|
| 🇹🇼 Taiwan | ✅ MOI #77132 (done) | ✅ NHRI 2020–23 | ⚠️ NHRI has national MCI age-band; **no map layer yet** | **live (dementia)**; MCI = build layer |
| 🇯🇵 Japan | 🔑 e-Stat (needs free API key) / WorldPop | ⚠️ Hisayama 2025 = **figure only**; 2015 MHLW/Ninomiya table = clean bands | ✅ 2024 MHLW national MCI | **deferred** (pop key + clean rate table) |
| 🇰🇷 Korea | 🔑 KOSIS (needs free API key) / WorldPop | ⚠️ NID report (PDF, transcribe) | ✅ NID national MCI | **deferred** (pop key + rate transcription) |
| 🌏 21 expansion countries | ✅ WorldPop (direct URL, heavy) | ❌ **GBD 2021 login-gated** | ❌ none per-country | **deferred** (GBD rate access) |

## Deferred list — grouped by blocker

**A. GBD-login-gated rates — Tier 4 (21 countries): 🇺🇸🇬🇧🇩🇪🇫🇷🇮🇹🇪🇸🇵🇱🇨🇦🇧🇷🇲🇽🇦🇺🇳🇿🇹🇷🇮🇷🇹🇭🇻🇳🇮🇩🇵🇭🇲🇾🇵🇰🇧🇩🇲🇲**
- The universal rate backbone is **GBD 2021 age-specific dementia prevalence**. The Results Tool
  (`vizhub.healthdata.org/gbd-results`) requires a **free login + interactive export**; the anonymous
  API returns 404 (verified). Creating an account / logging in is out of scope for an autonomous
  session → **rate half blocked for all 21**.
- Population half is **fetchable**: WorldPop age/sex 2020 GeoTIFFs download by direct URL
  (`data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020/2020/{ISO3}/{iso3}_{m,f}_{age}_2020.tif`,
  CC BY 4.0 — verified 200). But it is ~9 rasters × 21 countries of 100 m data (many GB) and is
  **useless without the rates**, so not fetched speculatively.

**B. Registration-gated national population — 🇯🇵 Japan, 🇰🇷 Korea**
- **e-Stat** (JP) and **KOSIS** (KR) population-by-age APIs need a **free application key** (account).
  Their websites *may* allow manual CSV download without login (owner can do this in a browser).
  **WorldPop** is a keyless alternative for the pop half (heavy).
- Rate half: **Japan** — the 2025 Hisayama paper reports age bands **only as a figure**; the clean
  age-band table is the **2015 MHLW/Ninomiya** "将来推計" (transcribe). **Korea** — NID
  《대한민국 치매현황》 age-band table is in the report PDF (transcribe).

**C. MCI layer — 🇹🇼🇯🇵🇰🇷 have national rates; nobody has admin-1 MCI**
- MCI age-band prevalence exists nationally for Taiwan (NHRI), Japan (2024 MHLW), Korea (NID), but
  **not sub-nationally** anywhere. Surfacing it also needs a **new map layer/metric** in
  `dementia-exposome.astro` (a second toggle like prevalence/PM2.5). → deferred to the "one-shot
  update"; gather the three national MCI tables as `_data_in` rate CSVs first.

## Fetchable now — recipes for the one-shot update
- **Taiwan county pop** (#33935) if a county view is ever wanted — `data.gov.tw/dataset/33935` (done for town via #77132).
- **WorldPop** (any country, keyless, CC BY 4.0): URL pattern above → `rasterio`/`rasterstats`
  zonal-**sum** over `public/data/geo/{cc}-admin1.geojson`; top band is **80+** (coarser than the
  85+ split — pair with a GBD 80+ rate). See `prevalence-data-sources.md` §Resolved Q4.

## To unblock (owner action)
1. **GBD 2021**: log in to the Results Tool and export *Alzheimer's & other dementias → Prevalence →
   by location/age/sex* as CSV (one export covers all 21 countries) **or** grant access → unblocks
   Tier 4 rates. Licence: IHME non-commercial + attribution (OK for this site — see Resolved Q5).
2. **Japan / Korea**: an e-Stat and a KOSIS free **API key** (or a manual CSV export of prefecture /
   시도 × 5-yr-age population) → unblocks JP/KR pop; I'll transcribe the MHLW/NID rate tables.
