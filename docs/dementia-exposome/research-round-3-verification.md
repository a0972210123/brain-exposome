# 🧠 Dementia-Exposome Calculator — Round 3-D: Verify-the-Numbers Pass

*Prepared July 2026 · verifies the ⚠️ items flagged in `research-round-2.md` · spec/verification only, no app code.*

> **Status:** research/verification only — no application code. Internal working notes (under `docs/`, not built or deployed).

> **Access caveat (applies throughout):** in this environment every publisher full-text (Lancet, PMC, PLOS, Frontiers, MGH card) **and** the raw data portals (data.gov.tw, ACAG, AWS registry pages) returned **HTTP 403**; only WebSearch, GitHub raw, and live S3 listings were reachable. So nothing below is graded **[Verified-primary]** — the ceiling is **[Verified-secondary]** (triangulated from underlying meta-analyses + validated code reproductions) and **[Verified-mirror/doc]** (read from live S3/GitHub or provider docs). Every number is transcribed from a named source; none invented. A final promotion to primary needs a library-access re-check + build-time `ncdump`/`ogrinfo`.

---

## 0. Summary — R3-D outcome

- **Lancet RRs: resolved with 95% CIs** for all 14 factors (V1), by reaching the underlying meta-analyses the Commission cited. **Three corrections** to the Round-2 spec (below).
- **ANU-ADRI age×sex bands: recovered** (men/women integers, from the validated reproduction) — the last gap in that table is closed.
- **Brain Care Score cutoffs: resolved** except the smoking intermediate tiers (1–2 pts).
- **Data technicals: resolved + one important correction** — the PM2.5 dataset version to target is **V6.GL.03 via `s3://satpmdata/`** (V6.GL.02.04's literal bucket 404s); Taiwan download routes/API endpoints confirmed.
- **Net:** the "safe-to-hard-code" set is now large and CI-backed. What remains is a nice-to-have **library-access primary confirmation** and a handful of **build-time file introspections** — none blocking a build.

---

## 1. ⚠️ CORRECTIONS to the Round-2 spec (the actionable output)

| Item | Round-2 said | Corrected value | Why it matters |
|---|---|---|---|
| **Hearing loss RR** | 1.9 | **1.37 (1.00–1.87)** — 2024 re-meta-analysed *down* (6 studies) | Materially smaller; use the 2024 value |
| **Depression RR** | 1.9 | **1.96 (1.59–2.43)** — 2024 re-meta-analysed (27 studies) | Minor up |
| **LDL cholesterol** | "~1.3 (categorical)" | **1.08 per 1 mmol/L (1.03–1.14)** — a **per-unit** RR, not categorical | The 7% PAF is built on the per-mmol/L figure; treat LDL as a dose (like PM2.5), or as a flagged categorical proxy if the user doesn't know their LDL |
| **Air pollution RR** | 1.1, mixed with a per-5 µg/m³ dose model | Lancet tabled **1.1 (1.0–1.2) is CATEGORICAL** (high-vs-low traffic PM2.5, Chen 2017) | **Do not use both** the Lancet categorical factor *and* the continuous PM2.5 dose model — that double-counts. **Recommendation:** handle PM2.5 continuously (it's the app's anchor exposome feature) via the dose-response HR (≈1.08 per 5 µg/m³, Lancet Planetary Health 2025) and **exclude** the discrete Lancet air-pollution RR from the factor sum |
| **2020 hearing CI** | "1.9 (1.0–3.6)" | **1.9 (1.4–2.7)** — the (1.0–…) lower bound belongs to the *2024* re-meta | Fix the citation |
| **ACAG dataset** | V6.GL.02.04 via `s3://v6.gl.02.04/` | **V6.GL.03 (1998–2024) via `s3://satpmdata/V6GL03/…`** — the literal `v6.gl.02.04` bucket returns 404 NoSuchBucket; that exact version is now Box/CloudFront-only | Point the build script at the current open-data bucket |

## 2. Lancet Commission RRs — resolved (V1) [Verified-secondary]

Use these as the engine's factor RRs (2024 values; all with CIs). Only depression & hearing were re-meta-analysed in 2024; LDL & vision are new; the other 10 carry 2020 RRs.

| Factor | RR (95% CI) | Definition / contrast | Source |
|---|---|---|---|
| Less education | 1.6 (1.3–2.0) | less/no vs more (early life) | 2020 Table 1 |
| **Hearing loss** | **1.37 (1.00–1.87)** | any hearing loss vs normal (2024 re-meta, 6 studies) | 2024 Commission |
| **LDL cholesterol** *(new)* | **1.08 per 1 mmol/L (1.03–1.14)** | per +1 mmol/L LDL-C, adults <65 | Commission meta of 3 UK cohorts (n≈1.14M); Iwagami 2021 |
| **Depression** | **1.96 (1.59–2.43)** | depression vs none (2024 re-meta, 27 studies) | 2024 Commission |
| Traumatic brain injury | 1.8 (1.5–2.2) | any TBI vs none | 2020 Table 1 (exact 1.84/1.54–2.20 unconfirmed) |
| Physical inactivity | 1.4 (1.2–1.7) | inactive vs active | 2020 Table 1 |
| Diabetes | 1.5 (1.3–1.8) | diabetes vs none | 2020 Table 1 |
| Smoking | 1.6 (1.2–2.2) | current vs non-smoker | 2020 Table 1 |
| Hypertension | 1.6 (1.2–2.2) | midlife SBP ≥130 vs <130 | 2020 Table 1 |
| Obesity | 1.6 (1.3–1.9) | midlife BMI ≥30 vs normal | 2020 Table 1 |
| Excessive alcohol | 1.2 (1.1–1.3) | >21 units/wk vs ≤21 | 2020 Table 1 (underlying 1.18, 1.06–1.31) |
| Social isolation | 1.6 (1.3–1.9) | isolated vs not | 2020 Table 1 |
| **Vision loss** *(new)* | **1.47 (1.36–1.60)** | vision impairment vs normal | Shang 2021, *Ophthalmology* (14 cohorts, n≈6.2M) |
| Air pollution (PM2.5) | 1.1 (1.0–1.2) **categorical** | high vs low traffic PM2.5 (Chen 2017) | 2020 Table 1 — see correction re: double-count |

## 3. ANU-ADRI age×sex points — resolved (V2) [Verified-secondary]
From the validated reproduction (`MelisAnaturk/dementia_risk_score`, weights per Anstey 2013); age is the dominant term. Sex-specific.

| Age band | Men pts | Women pts |
|---|---|---|
| <65 | 0 | 0 |
| 65–69 | 1 | 5 |
| 70–74 | 12 | 14 |
| 75–79 | 18 | 21 |
| 80–84 | 26 | 29 |
| 85–90 *(90 inclusive)* | 33 | 35 |
| >90 | 38 | 41 |

Bands are half-open `[x, x+5)`; age exactly 90 → the 85–90 band. Combined with the 13 factor-groups from Round-2 §A.1.5, the ANU-ADRI table is now complete for implementation (still to promote to primary vs PLoS ONE 2014 Table — note the point-allocation table may be **Table 5** `pone-0086141-t005`, not Table 2).

## 4. Brain Care Score item cutoffs — resolved (V2) [Verified-secondary]
Maxima checksum confirmed 8/9/4 = 21.

| Item (cap) | Value → points |
|---|---|
| Blood pressure (0–3) | ≥140/90 → 0 · 120–139/80–89 → 2 · <120/80 → 3 *(no "1" tier)* |
| HbA1c (0–2) | >6.4% → 0 · 5.7–6.4% → 1 · <5.7% → 2 |
| Cholesterol (0–1) | ≥190 mg/dL → 0 · <190 (or CVD+LDL at target) → 1 |
| BMI (0–2) | <18.5 → 1 · 18.5–25 → 2 · 25–29.9 → 1 · ≥30 → 0 |
| Nutrition (0–2) | <2 diet targets → 0 · ≥2 → 1 · ≥3 → 2 |
| Alcohol (0–2) | 4+/wk → 0 · 2–3/wk → 1 · 0–1/wk → 2 |
| Smoking (0–3) | current → 0 · never/quit >1yr → 3 · **tiers 1–2 ⚠️unresolved** |
| Aerobic (0–1) | <150 min mod → 0 · ≥150 → 1 |
| Sleep (0–1) | untreated disorder or <7h → 0 · treated & 7–8h → 1 |
| Stress (0–2) | high → 0 · moderate → 1 · manageable → 2 |
| Social (0–1) | few/none → 0 · ≥2 close people → 1 |
| Meaning (0–1) | struggles → 0 · has meaning → 1 |

## 5. ACAG PM2.5 technicals — resolved + corrected (V3)
- **Target V6.GL.03 (1998–2024)** via AWS Open Data bucket **`satpmdata`** (us-east-1). Live layout [Verified-mirror]: `s3://satpmdata/V6GL03/{CoarseResolution=0p10 | FineResolution=0p01}/{GL|AF|AS|EU|NA|SA}/{Annual|Monthly}/`. Global region = `GL`. Annual pattern `V6GL03.CNNPM25.0p10.GL.<YYYY>01-<YYYY>12.nc`. Anonymous `aws s3 ls --no-sign-request s3://satpmdata/V6GL03/CoarseResolution/GL/Annual/` works.
- For the exact **V6.GL.02.04** version: literal `s3://v6.gl.02.04/` **404s** — use WUSTL Box (`box.com/v/ACAG-V6GL0204-CNNPM25` 0.01° / `…c0p10` 0.1°) or CloudFront `d15downnhi4nn0.cloudfront.net`. **Prefer V6.GL.03** (newer, in the open bucket).
- **Lat extent clipped** [Verified-doc]: 0.01° cell centers −54.995°…+67.995° (12,300 rows × 36,000 cols); 0.1° ≈ −54.95°…+67.95° (1,230×3,600). Confirms the Round-2 "not full ±90°" note.
- **⚠️ Build-time `ncdump -h` still required for:** internal PM2.5 variable name (`GWRPM25` vs `CNNPM25` vs `PM25`), `_FillValue`/nodata, lat storage order (asc/desc), and exact cell-center values at 0.1°.

## 6. Taiwan data technicals — resolved (V3)
- **#7441 boundaries**: `TOWN_MOI_<ROC-date>.shp` (zip w/ .shp/.shx/.dbf/.prj), **EPSG:3824**, 368 features, fields `TOWNCODE/TOWNNAME/COUNTYCODE/COUNTYNAME`. Routes: NLSC `whgis-nlsc.moi.gov.tw/Opendata/Files.aspx`, g0v mirror `data.g0v.ronny.tw/index/data/7441`, GitHub `dkaoster/taiwan-atlas` (prebuilt TopoJSON) / `justinelliotmeyers/official_taiwan_administrative_boundary_shapefile` (raw SHP). Build-time: `ogrinfo`/`gdalsrsinfo` to confirm 368 features + Big5 encoding + EPSG:3824.
- **#77132 population**: RIS rs-opendata API **`https://www.ris.gov.tw/rs-opendata/api/v1/datastore/ODRP014/{yyymm}`** (ROC year-month, e.g. `11305`). **Confirm `ODRP014`** (the 新增區域代碼 variant with `district_code`) — not `ODRP005`/#32973. Columns `people_age_000_m/_f …`; roll up `district_code` → 8-digit `TOWNCODE`. Build-time: pull one month, confirm the digit-slice `district_code → TOWNCODE`.

## 7. Verified value set for the scoring engine (net result)
**Ready to hard-code now (CI-backed, Verified-secondary):** the full 14-factor RR table in §2; the LIBRA weights; the CAIDE table; the ANU-ADRI complete table (§3 + Round-2 §A.1.5); the BCS cutoffs (§4, minus smoking tiers 1–2); T=5.5 doubling; shrinkage+cap method. **PM2.5 handled continuously** (dose-response), Lancet air-pollution factor excluded to avoid double-counting.

## 8. Still open (honest list — none blocks a build)
- **Primary (library) confirmation** of every RR against the Lancet 2024 table / 2020 Table 1, and the ANU-ADRI point table (PLoS ONE 2014, possibly `-t005`), and the MGH BCS card — to promote [Verified-secondary]→[Verified-primary]. Exact still-fuzzy cells: TBI exact CI (1.5–2.2 vs 1.54–2.20), air-pollution exact CI + contrast, LDL→7%-PAF mechanics, BCS smoking tiers 1–2.
- **Build-time file introspection** (`ncdump -h` on ACAG; `ogrinfo`/`gdalsrsinfo` on #7441; one-month `ODRP014` pull) — settled during BUILD-2, not researchable.
- **λ=0.6 shrinkage & ±12-yr cap** remain tool assumptions (not published constants) — calibrate against the brain-clock ranges and document as such.

## 9. Readiness verdict & next step
**The numbers are now build-ready.** Every constant that ships in the calculator has a CI and a named source; the three corrections are captured; only a library-access primary re-check (nice-to-have) and build-time file introspection (part of BUILD-2) remain. Recommended next:
- **BUILD-1: scoring-engine prototype** — implement Round-2 §A.3 with this verified value set (categorical profile + brain-age readout), PM2.5 handled continuously; stub map/data.
- **BUILD-2: data pipeline** — `scripts/build_data.py` targeting ACAG V6.GL.03 + Taiwan #7441/#77132, doing the build-time confirmations in §5–6.
- (Optional) **library primary-verification** if/when unrestricted-network access is available, to stamp every cell [Verified-primary].

---

## References (Round 3-D)
Livingston 2024 *Lancet* 404:572–628 (DOI 10.1016/S0140-6736(24)01296-0) · Livingston 2020 396:413–446 (10.1016/S0140-6736(20)30367-6) · Shang 2021 *Ophthalmology* vision meta (PMID 33422559) · Iwagami 2021 *Lancet Healthy Longevity* (LDL) · Anstey 2013 *Prev Sci* (PMC3696462) / 2014 *PLoS ONE* e0086141 (PMC3900468) · `MelisAnaturk/dementia_risk_score` (ANU-ADRI reproduction) · Singh 2023 *Front Neurol* (PMC10725202) + MGH Brain Care Score card · ACAG V6.GL.03 (AWS `s3://satpmdata/`, registry surface-pm2-5-v6gl) · SEDAC V5.GL.04 (DOI 10.7927/AS2R-9P42) · Taiwan #7441 (NLSC), #77132 (RIS rs-opendata `ODRP014`) · Lancet Planetary Health 2025 (PM2.5 dose-response) · Wilker *BMJ* 2023.
