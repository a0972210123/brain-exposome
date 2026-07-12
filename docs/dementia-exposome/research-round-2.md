# 🧠 Dementia-Exposome Calculator — Round 2: Scoring Engine + Data Pipeline Spec

*Prepared July 2026 · builds on Round 1 (`research-round-1.md`) · Scope: (A) concrete scoring algorithm with verified constants; (B) concrete static-asset build pipeline · Still spec-only, no app code.*

> **Status:** research/spec only — no application code written. Internal working notes (under `docs/`, outside `src/`, so Astro does not build or deploy it).

> **Confidence flags** carried from research: **[H]** verified from primary/measured · **[M]** corroborated via mirror/snippet · **[L]** inferred/estimate. Publisher full-text was egress-blocked this session, so several effect sizes rest on open manuscript mirrors + validated code implementations — anything marked **⚠️re-check** must be confirmed against the primary appendix before it is hard-coded. Non-diagnostic, educational; not medical advice.

---

## 0. Summary — both topics are now buildable

- **(A) Scoring engine:** the defensible design is **Lancet-14-factor relative risks → overlap-shrunk combination → an educational "brain-age acceleration (years)" readout**, with a **categorical modifiable-factor profile as the primary, non-diagnostic output**. The core math is settled: `Δbrain-years = log₂(RR_eff) × 5.5`, where `ln(RR_eff) = λ·Σ ln(RRᵢ)` (λ≈0.6 to discount correlated factors) and the result is capped at ±~12 years. A validated **LIBRA index** (published weights) powers a secondary "brain-health habits" gauge and the protective tips.
- **(B) Data pipeline:** all static assets fit a small budget (**< ~25 MB committed, mostly < 10 MB on the wire**). Taiwan PM2.5 ships as a **7.3 MB uint16 binary** (0.01°, 1998–2023); the world ships as a **~250 KB admin1 annual-mean JSON**; Taiwan districts as a **~70 KB-gzip TopoJSON** (368 districts, join key `TOWNCODE`); modelled prevalence as a **~50 KB JSON** (national NHRI age-rates × district age structure). A one-time offline `scripts/` job builds them all; Cloudflare Pages just serves `public/data/`.
- **Key safety rule (from A2):** **never multiply raw marginal RRs** for an individual — correlated dementia factors double-count and explode the number. Use shrinkage + a cap, output a **range**, and label it a population-level association, not a personal prediction.

---

# PART A — THE SCORING ENGINE

## A.1 Verified constants (the numbers to hard-code)

### A.1.1 Lancet Commission relative risks + weighted PAFs
> ⚠️ **Superseded by Round 3-D** (`research-round-3-verification.md` §1–2): the ⚠️re-check RRs below were verified and **some corrected** — hearing loss → **1.37**, depression → **1.96**, LDL → **1.08 per 1 mmol/L** (per-unit, not categorical), vision → **1.47 (1.36–1.60)**, air pollution **1.1 is categorical** (don't combine with the continuous PM2.5 dose model). Use the Round-3 §2 table as the source of truth.

The **weighted-PAF split is [H] verified** for both years (2024 sums to 45%, 2020 to 39.7%). RRs: the 9 "carried-over" factors are **[H/M] verified from the open UCL manuscripts**; the 2024-new and re-meta-analysed ones are **⚠️re-check**.

| Factor | 2024 wPAF | RR (use) | Confidence |
|---|---|---|---|
| Hearing loss | 7% | 1.9 | RR [M] ⚠️re-check (2024 may differ) |
| High LDL cholesterol *(new 2024)* | 7% | ~1.3 | ⚠️re-check |
| Less education | 5% | 1.6 | [H] |
| Social isolation | 5% | 1.6 | [H] |
| Depression | 3% | 1.9 | [M] ⚠️re-check |
| Traumatic brain injury | 3% | 1.8 (≈1.84) | [M] ⚠️re-check |
| Air pollution (PM2.5) | 3% | 1.1 | [M] ⚠️re-check |
| Physical inactivity | 2% | 1.4 | [H] |
| Diabetes | 2% | 1.5 | [H] |
| Smoking | 2% | 1.6 | [H] |
| Hypertension | 2% | 1.6 | [H] |
| Vision loss, untreated *(new 2024)* | 2% | ~1.47 | ⚠️re-check |
| Obesity | 1% | 1.6 | [H] |
| Excessive alcohol | 1% | 1.2 | [M] ⚠️re-check |
| **TOTAL** | **45%** | | wPAF [H] |

> The 2020 report (RRs identical for carried-over factors, total 39.7%) is the primary source for these RRs. Prevalences the Commission used were **not obtainable** this session — only needed if you recompute PAFs yourself (you don't; use the published wPAFs).

### A.1.2 LIBRA index weights — [H] (range-verified: +12.7 / −5.9)
Backbone for the secondary "habits gauge" + protective factors. Higher = worse.

| Risk (+) | wt | Protective (−) | wt |
|---|---|---|---|
| Depression | +2.1 | High cognitive activity | −3.2 |
| Hypertension | +1.6 | Mediterranean diet | −1.7 |
| Obesity | +1.6 | Low–moderate alcohol | −1.0 |
| Smoking | +1.5 | | |
| Hypercholesterolaemia | +1.4 | | |
| Diabetes (T2) | +1.3 | | |
| Chronic kidney disease | +1.1 | | |
| Physical inactivity | +1.1 | | |
| Coronary heart disease | +1.0 | | |

### A.1.3 CAIDE point table — [M] (base model 0–15, internally consistent)
Optional "midlife simple mode." Age (<47=0, 47–53=3, >53=4) · Education (≥10y=0, 7–9=2, 0–6=3) · Sex (F=0, M=1) · SBP (≤140=0, >140=2) · BMI (≤30=0, >30=2) · Total chol (≤6.5 mmol/L=0, >6.5=2) · Inactive=1. **Score→20-yr risk:** 0–5→1.0% · 6–7→1.9% · 8–9→4.2% · 10–11→7.4% · 12–15→16.4%.

### A.1.4 McCance Brain Care Score — [M] (12 items, 21 pts; caps 8/9/4)
Physical (BP 0–3, HbA1c 0–2, cholesterol 0–1, BMI 0–2) · Lifestyle (diet 0–2, alcohol 0–2, smoking 0–3, aerobic 0–1, sleep 0–1) · Social-emotional (stress 0–2, relationships 0–1, meaning 0–1). Higher = better. ⚠️re-check intermediate cutoffs vs the official MGH card.

### A.1.5 ANU-ADRI point table — [M/H] (13 of 14 factor-groups now recovered)
**Self-report only, no lab values** → the best-UX validated index for a consumer tool (users needn't know their LDL/BP). Points verified from a peer-reviewed reproduction (Borges 2018, PMC6200163) cross-checked against an R implementation; higher = worse. Protective factors go negative.

| Factor | Response → points |
|---|---|
| Education | >11 y = 0 · 8–11 = +3 · <8 = +6 |
| BMI *(midlife 18–59 only; ≥60 → 0)* | ≤25 = 0 · 25–30 = +2 · >30 = +5 |
| High cholesterol | No 0 · Yes +3 |
| Diabetes | No 0 · Yes +3 |
| TBI | No 0 · Yes +4 |
| Depressive symptoms (CES-D ≥16) | No 0 · Yes +2 |
| Smoking | Never 0 · Past +1 · Current +4 |
| Pesticide/toxic exposure | No 0 · Yes +2 |
| Physical activity | low 0 · moderate −2 · vigorous −3 |
| Cognitive activity | low 0 · moderate −7 · high −6 *(table quirk: mod > high)* |
| Social engagement | low +6 · low-mod +4 · mod-high +1 · high 0 |
| Fish (servings/wk) | 0–0.25 = 0 · 0.26–2 = −3 · 2.1–4 = −4 · ≥4.1 = −5 |
| Alcohol | none/abstinent 0 · light-moderate −3 *(no heavy penalty in table)* |
| **Age × sex** | both sexes <65 = 0; older bands sex-specific & steep ⚠️**NOT VERIFIED** — read from PLoS ONE 2014 Table 2 (PMC3900468) |

Sample composite range ≈ **−18 … +10** (the −18 min reproduces from summing protective maxima). **CogDrisk:** 17-factor list verified but exact weights are not public (live inside cogdrisk.com) — don't fabricate; use ANU-ADRI / LIBRA / Lancet RRs instead.

## A.2 The combination math + brain-age conversion (settled)

- **Age-doubling constant** [H]: dementia frequency rises log-linearly with age; **prevalence doubles ≈5.1 yr (Jorm 1987), AD incidence ≈5.5 yr (Ziegler-Graham 2008)**. **Use T=5.5 yr, sensitivity band 5.0–6.3.** (The "6.3 yr" from Matt's notes couldn't be pinned — treat as the upper band, not a point value.)
- **Do NOT multiply marginal RRs** [H]: correlated dementia factors double-count → absurd 5–20× products. The Lancet Commission itself down-weights by **communality** (PCA of the tetrachoric correlation matrix). We approximate that with a **shrinkage λ**.
- **Baseline hazard** (optional, for absolute framing): EURODEM all-dementia incidence /1,000 PY ≈ 2.5 (65) → ~86 (90+); women's AD risk diverges above ~85 (cumulative AD 65→95: women 0.22, men 0.09). Treat as shape, not 2026-absolute (rates have declined ~13%/decade).
- **Brain-clock effect sizes** (for cross-check / sanity): diabetes ≈ +2 to +4.6 brain-yr, stroke +2.6, current smoking +2.1, heavy alcohol +1, high PM2.5 ≈ +2–6 (bio-behavioural); each +1 BrainAGE-yr → +10% MCI→AD conversion hazard (HR 1.10). A realistic worst-case modifiable profile ≈ **+5 to +10 equivalent brain-years** — this is the target range the engine should land in.

## A.3 Recommended engine (concrete, client-side, non-diagnostic)

```
INPUT: demographics (age, sex, education), 14 Lancet factors (present/level),
       residence history → time-weighted mean PM2.5 (see A.4)

STEP 1 — per-factor RR:
  for each factor present: RRᵢ = table value (A.1.1); absent → 1.0
  graded factors scale on the log axis:
    smoking: never→1.0, past→exp(0.5·ln(RR_current)), current→RR
    PM2.5:   RR_pm = 1.08 ^ ((meanPM25 − 5) / 5)   // per +5 µg/m³ over WHO 5 guideline; floor at meanPM25=5 → RR 1.0
             (1.08 per 5 µg/m³ = Lancet Planetary Health 2025; ≈ the 1.1 tabled value)

STEP 2 — combine with overlap shrinkage:
  lnRR_eff = λ · Σ ln(RRᵢ)          // λ = 0.6 (band 0.5–0.7)  ← discounts correlated double-counting

STEP 3 — cap:
  lnRR_eff = min(lnRR_eff, ln(4.5)) // ceiling ≈ +12 brain-years

STEP 4 — brain-age readout:
  Δyears     = log2(exp(lnRR_eff)) · 5.5
  Δyears_lo  = … · 5.0 ;  Δyears_hi = … · 6.3    // show as a RANGE

STEP 5 — categorical profile (PRIMARY OUTPUT, non-diagnostic):
  count present modifiable factors, grouped by the 6 categories;
  band overall as e.g. "few / several / many modifiable factors present"

STEP 6 — protective actions:
  for each present factor → WHO-determinant-organised suggestion
  (LIBRA protective weights guide "biggest wins": cognitive activity, diet, BP…)
OUTPUT: categorical profile (lead) + "≈ +X yr (range) educational brain-age estimate" (secondary) + actions
```

**Why this design:** it is transparent (every constant cited), uses the app's own Lancet-14 framing, avoids the RR-multiplication trap, lands in the literature-plausible ±single-digit range, and stays non-diagnostic (categorical lead, no personal % of getting dementia). The **LIBRA gauge** (normalise the −5.9…+12.7 sum to 0–100) is an optional second lens that also credits protective habits.

## A.4 PM2.5 cumulative sub-model (realises the "accumulated exposome" idea)

From the residence table rows `(place, startYear, endYear)`:
- `meanPM25 = Σ(years_i · PM25_i) / Σ(years_i)` — time-weighted lifetime mean → feeds Step 1.
- `cumulativeDose = Σ(years_i · PM25_i)` µg/m³·years — shown as the headline "exposome" number (illustrative).
- PM25_i comes from the pre-baked grid (Part B): Taiwan 0.01° for TW residences, admin1 mean elsewhere; pre-1998 clamped to 1998 and flagged.

## A.5 Output design + mandatory disclaimers

**Lead with the categorical profile**, not the number. Show the brain-age estimate as a clearly-labelled educational illustration with a visible range. Always display:
1. Not an MRI/EEG brain clock — an estimate from self-reported factors.
2. Population-level average association, **not a personal prediction** (±7 yr individual variation).
3. Associations, not proven causation for every factor.
4. Overlap is modelled (λ), and the combined figure is model-sensitive.
5. Non-diagnostic; most factors are modifiable; see a clinician if worried.
6. Processed entirely in your browser; nothing uploaded. (Bilingual zh/en.)

## A.6 Safe-to-hard-code vs ⚠️re-check
- **Safe now [H/M]:** all weighted PAFs (2024 & 2020); carried-over RRs (education 1.6, hearing 1.9, hypertension 1.6, obesity 1.6, smoking 1.6, depression 1.9, isolation 1.6, diabetes 1.5, inactivity 1.4); LIBRA weights + range; **ANU-ADRI 13 non-age factor-groups (A.1.5)**; CAIDE table + risk map; BCS structure/total; T=5.5; the shrinkage+cap method.
- **⚠️re-check before shipping numbers:** RRs for LDL (~1.3), vision (~1.47), and any 2024 change to hearing/depression; TBI (1.8)/alcohol (1.2)/air-pollution (1.1) against the printed table; **ANU-ADRI age×sex band integers only** (rest now recovered); BCS intermediate cutoffs. Sources to check: Lancet 2024 appendix, Deckers 2015/2018 (LIBRA), Anstey 2014 PLoS ONE Table 2 (PMC3900468), MGH BCS card.

---

# PART B — THE DATA PIPELINE

## B.1 Static-asset inventory & budget

| Asset | File | Raw | On-wire (gzip/brotli) | Conf. |
|---|---|---|---|---|
| Taiwan PM2.5 grid 0.01°, 1998–2023 | `pm25/taiwan/tw_pm25_0p01_1998_2023.u16.bin` | 7.3 MB | ~3–5 MB | [H] |
| Global admin1 annual-mean PM2.5 | `pm25/global/admin1_annual_pm25.json` | ~0.75 MB | ~250 KB | [H] |
| Global 0.5° PM2.5 fallback *(optional)* | `pm25/global/global_0p5deg_1998_2023.u16.bin` | 13.5 MB | ~6–10 MB | [H] |
| Taiwan district boundaries (368) | `geo/tw-districts.topo.json` | ~200 KB | **~70 KB** | [H measured] |
| Modelled prevalence (368) | `data/tw-dementia-modelled.json` | ~50 KB | ~15 KB | [H] |
| Meta/manifest sidecars | `*_meta.json`, `manifest.json` | few KB | — | — |

**Committed total < ~25 MB** (put the two `.bin` files in Git LFS or Cloudflare R2 if you'd rather keep the repo light). The optional global 0.5° raster is only needed for arbitrary non-Taiwan points; the admin1 table already covers named places.

## B.2 ACAG PM2.5 pipeline (topic B1)

> ⚠️ **Superseded by Round 3-D** (`research-round-3-verification.md` §5): target **V6.GL.03 (1998–2024)** via `s3://satpmdata/V6GL03/…` — the literal `s3://v6.gl.02.04/` bucket 404s. Live S3 layout + build-time `ncdump` checklist are in Round-3 §5.

- **Dataset** [H]: ACAG/WashU **V6.GL.02.04**, NetCDF-4, var `PM25` (µg/m³), WGS84, **annual 1998–2023**, tiers 0.01° & 0.1°. Grid is lat-clipped ≈55°S–68°N (verify with `ncdump -h`). Access: AWS Open Data `s3://v6.gl.02.04/ --no-sign-request` (us-west-2), CloudFront `d15downnhi4nn0.cloudfront.net`, or WUSTL Box (0.1°). Alt: NASA SEDAC V5.GL.04 (GeoTIFF, var `GWRPM25`, DOI 10.7927/AS2R-9P42, 1998–2022). **License CC BY 4.0** → must credit Shen et al. 2024 (ACS ES&T Air) + van Donkelaar et al. 2021.
- **Read/process** (Python: xarray+netCDF4, rioxarray/rasterio, numpy, geopandas+exactextract):
  ```python
  ds = xr.open_dataset("V6GL02.04.CNNPM25.Global.201501-201512.nc")
  val = ds["PM25"].sel(lat=25.03, lon=121.56, method="nearest").item()   # Taipei
  tw  = ds["PM25"].sel(lat=slice(25.5,21.5), lon=slice(119.0,122.5))     # note lat may be descending
  coarse = ds["PM25"].coarsen(lat=5, lon=5, boundary="trim").mean(skipna=True)  # 0.1°→0.5°
  ```
- **Packaging** = **uint16 scaled** (value=raw/10, nodata 65535), stacked `[year][row][col]` typed-array binary + sidecar `meta.json` header. Taiwan bbox 119–122.5°E / 21.5–25.5°N at 0.01° = 350×400×26 = **7.28 MB**. Admin1 table = zonal-mean ACAG (over geoBoundaries ADM1, run on the 0.1° raster) → `{ISO3:{adm1:{name,[26 floats]}}}`. Browser lookup is O(1):
  ```js
  const c = Math.floor((lon-H.lon_min)/H.res), r = Math.floor((H.lat_max-lat)/H.res);
  const v = grid[((year-H.year0)*H.nrows + r)*H.ncols + c];
  return v===H.nodata ? null : v/H.scale;   // µg/m³; ocean cell → snap to nearest land or admin1 mean
  ```
- **Pre-1998**: clamp to the 1998 (or 1998–2000 mean) value and flag it in the UI as inferred (phase-2: back-cast with a country emissions trend).

## B.3 Taiwan boundaries + population + modelled prevalence (topic B2)

- **Boundaries** [H]: data.gov.tw **#7441** 鄉鎮市區界線, Shapefile, **EPSG:3824** (geographic TWD97 ≈ WGS84), **368 features**, join key **`TOWNCODE`** (8-digit), Big5-encoded names. License **OGDL-Taiwan-1.0 ≈ CC BY 4.0**. Pipeline: `ogr2ogr`/`mapshaper` → reproject 3824→4326, `encoding=big5`, keep `TOWNCODE,TOWNNAME,COUNTYNAME`, Visvalingam simplify ~12%, emit **TopoJSON** (`topoquantize 1e5`) ≈ **200 KB raw / ~70 KB gzip**.
- **Population** [M]: data.gov.tw **#77132** 村里戶數、單一年齡人口（新增區域代碼）, CSV UTF-8, **single-year ages** → sum villages to 8-digit `TOWNCODE`, aggregate to the 6 bands (65–69…90+). Pin one `statistic_yyymm` and record it.
- **Modelled prevalence** = national NHRI 2020–23 rates × local age structure (indirect standardisation — label as ESTIMATE):
  ```
  modelled_cases_d = Σ_b pop_{d,b}·r_b ,  r = {65-69:.024,70-74:.0516,75-79:.091,80-84:.16,85-89:.2004,90+:.2945}
  rate_of_65plus_pct = 100·cases_d / Σ_b pop_{d,b}
  ```
  National sanity check: ≈8–10% of 65+ (~400–430k cases) — matches published Taiwan figures. **Output JSON** `tw-dementia-modelled.json`: `{meta{method,disclaimer,rates,population_source,boundary_source,license}, districts:[{townCode,countyName,townName,pop_total,pop_65plus,modelled_cases,modelled_rate_of_total_pct,modelled_rate_of_65plus_pct}]}` (townCode as **string**, keep leading zeros). Caveats to surface: estimate not measurement; national rates assumed uniform; grey out tiny-population districts.

## B.4 Map consumption (no framework)

Leaflet (simplest raster choropleth) or MapLibre GL (vector, smoother) — both are libraries, loaded via `<script>`, compliant with the "no JS framework" rule. Expand TopoJSON with `topojson-client` (`topojson.feature`), join prevalence by `TOWNCODE`, colour by `modelled_rate_of_65plus_pct` (ColorBrewer YlOrRd, colour-blind-safe), grey `#eee` for null. **Basemap:** do **not** hit `tile.openstreetmap.org` in production — use **OpenFreeMap** (free, no key, MapLibre-native) or render polygons on a plain background (often clearest for a health choropleth). **Attribution (required):** 界線 © 內政部NLSC｜人口 © 內政部戶政司｜OGDL-Taiwan-1.0｜失智盛行率為模型估計值 (NHRI 2020–23 × 在地年齡結構).

## B.5 Build script + layout

One-time **offline** job `scripts/build_data.(py|sh)` (NOT part of the Cloudflare build — too heavy; Pages just serves committed `public/data/`). Steps: download & cache ACAG annual files → crop Taiwan + uint16 pack → (optional) 0.5° global downsample → admin1 zonal means (on 0.1°) → boundary reproject/simplify/topojson → population roll-up + prevalence compute → write manifest (provenance/citation/license/backcast policy). Runtime ~15–30 min if Taiwan uses a 0.01° bbox window and global uses 0.1° (hours only if pulling the full 0.01° globe). Layout:
```
public/data/
  manifest.json
  pm25/taiwan/{tw_pm25_0p01_1998_2023.u16.bin, tw_pm25_meta.json}
  pm25/global/{admin1_annual_pm25.json, global_0p5deg_1998_2023.u16.bin, *_meta.json}
  geo/tw-districts.topo.json
  data/tw-dementia-modelled.json
```

---

## C. Licensing / attribution summary (all bundled data)
| Data | License | Required credit |
|---|---|---|
| ACAG PM2.5 (V6.GL.02.04) | CC BY 4.0 | Shen et al. 2024, ACS ES&T Air; van Donkelaar et al. 2021, ES&T |
| SEDAC PM2.5 (alt) | CC BY | DOI 10.7927/AS2R-9P42 |
| Taiwan boundaries #7441 | OGDL-Taiwan-1.0 (≈CC BY 4.0) | 內政部國土測繪中心 (NLSC) |
| Taiwan population #77132 | OGDL-Taiwan-1.0 | 內政部戶政司 (MOI) |
| NHRI prevalence rates | cite | NHRI dementia survey 2020–2023 |
| geoBoundaries admin1 (global, later) | CC BY 4.0 | geoBoundaries (W&M geoLab) |
| Basemap tiles | per provider | OpenFreeMap / OSM © OpenStreetMap contributors |

## D. Open items to verify before shipping numbers
- **RRs** ⚠️: LDL ~1.3, vision ~1.47, 2024 hearing/depression, TBI 1.8, alcohol 1.2, air-pollution 1.1 → Lancet 2024 appendix.
- **ANU-ADRI** age×sex band integers → Anstey 2014 PLoS ONE Table 2 (PMC3900468) (only if you use ANU-ADRI; the 13 other factor-groups are recovered in A.1.5).
- **BCS** intermediate cutoffs → MGH card.
- **ACAG** actual lat extent / no-data sentinel / lat ordering → `ncdump -h`; exact S3 sub-paths → `aws s3 ls`.
- **Taiwan** exact behind-403 file URLs (#7441 `.shp.zip`, #77132 monthly CSV) → the 資源下載 buttons.
- **λ shrinkage (0.6)** and the **±12-year cap** are defensible defaults, not published constants — calibrate against the brain-clock ranges (A.2) and document them as tool assumptions.

## E. Recommended next step (pick to steer Round 3 / build)
- **BUILD-1 (recommended): scoring-engine prototype** — implement A.3 as a single client-side module + a minimal `/projects/dementia-exposome` page (residence table + factor toggles → categorical profile + brain-age readout), using only the ⚠️-cleared constants; stub the map/PM2.5 with placeholder data first.
- **BUILD-2: data pipeline** — write `scripts/build_data.py`, produce the real `public/data/` assets, wire the Taiwan map + PM2.5 lookup.
- **R3-C: UX / copy** — wireframe the table + results (Spider-Web-inspired) + bilingual disclaimer text.
- **R3-D: verify-the-numbers pass** — a focused round to clear every ⚠️re-check item against primary appendices before any number ships.

---

## References (Round 2)
Livingston 2024 Lancet (DOI 10.1016/S0140-6736(24)01296-0; open ms discovery.ucl.ac.uk/id/eprint/10196488) · Livingston 2020 (10.1016/S0140-6736(20)30367-6; ucl 10106893) · LIBRA: Deckers 2015 / Schiepers 2018 (Evidencio #1041) · CAIDE: Kivipelto 2006 (Lancet Neurol) · ANU-ADRI: Anstey 2014 PLoS ONE (PMC3900468), Borges 2018 validation (PMC6200163) · CogDrisk: Anstey 2022 (PMC9275658) · McCance BCS: Singh 2023 Front Neurol (PMC10725202) · doubling: Jorm 1987 (PMID 3324647), Ziegler-Graham 2008 (PMID 18790458), Jorm & Jolley 1998 (PMID 9748017) · baseline: EURODEM Launer 1999 (PMID 9921852), Andersen 1999 (PMID 10599770) · BrainAGE: Franke 2010, Gaser 2013 (PLoS ONE e67346), Cole 2020 (PMC7280786), cardiometabolic meta 2025 (PMC11908789), Moguilner/Ibáñez 2024 Nat Med (10.1038/s41591-024-03209-x) · PAF-combination critique: AJE 2023;192(10):1763 · ACAG (sites.wustl.edu/acag; AWS s3://v6.gl.02.04) · SEDAC V5.GL.04 (DOI 10.7927/AS2R-9P42) · Taiwan #7441/#7442/#7438, #77132 (data.gov.tw) · NHRI 2020–23 survey · geoBoundaries (geoboundaries.org) · OpenFreeMap.
