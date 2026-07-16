# MCI / SCD research → handoff to the local session

*Cloud session output for `cloud-research-brief-mci-scd.md` (PR #156). This tells the local session exactly
what it can wire now, what to download, and how to treat SCD. Built 2026-07-16 via a 66-agent deep-research
fan-out (Tier A per-country + Tier B regional), WebSearch-only. Deliverables in this PR:*
- **`scripts/mci-scd-sources.json`** — machine-readable, ISO alpha-2 keyed, full schema (the thing you ingest).
- **`docs/side-projects/dementia-exposome/mci-scd-sources.md`** — human-readable MCI + SCD tables.
- **`docs/side-projects/dementia-exposome/mci-scd-download-worklist.md`** — OA / paywalled / govt download list.
- this handoff.

## Coverage
- **97 countries** with ≥1 value · **MCI 92** · **SCD 38**.
- MCI: **43** from a national/govt survey or cohort, **14** high-confidence; the rest are sub-national cohorts,
  screening studies, or SHARE-harmonised estimates (all flagged in `criteria`/`confidence`).
- **35 countries carry a sub-national MCI breakdown** (see `subnational` in the JSON) → seed for a future admin-1 MCI layer.
- Anchors all upgraded to high-confidence national values: **US** HCAP 22% + BRFSS SCD 11.2%; **China** Jia 2020
  15.5% + SCD 46.4%; **Japan** JPSC-AD 17% + SCD 47.4%; **Korea** NaSDEK 22.25% + SCD 38.3%; **Taiwan** 18.76% + SCD 24.3%.

## 1. Directly usable — wire the whole JSON now
Every country in `scripts/mci-scd-sources.json` already has its **headline value extracted** (`prev_pct`,
`age`, `criteria`, `year`, `citation`, `doi_url`, `confidence`). You do **not** need to download anything to
populate the map. Suggested wiring:
- **MCI**: extend `MCI_NATIONAL` in `build_data.py` from the 5 current overrides to all `mci` entries here
  (keep `kind:"national"`; carry `criteria`+`confidence` into the JSON note so the legend can warn on MoCA/CIND).
  Countries not present keep the **Bai 2022 WB-region baseline** already in `build_mci_national()`.
- **SCD** (new): add `build_scd_national()` mirroring `build_mci_national()`, reading the `scd` entries →
  `public/data/scd/scd-national.json`, then a new globe layer. **But read §4 first** — SCD is not comparable across countries.
- The 5 existing MCI overrides: my values differ slightly (better criteria/recency) — e.g. JP 17% (JPSC-AD,
  Petersen) vs current 15.5; KR 22.25 (DSM-IV+IWG) vs 22.7; TW 18.76 vs 18.7; CN 15.5 vs 15.4. Your call whether to update.

## 2. Download for enrichment (OA — `fitz`)
90 open-access sources (full list in the worklist). Only needed if you want the **95% CI**, **age-band splits**,
or the **sub-national tables** the abstract didn't carry. Priority = the 35 sub-national-MCI countries (China,
Japan, Taiwan, Korea-adjacent, UK, Spain, Nigeria, Thailand, Malaysia, Philippines, Vietnam, Peru, Argentina…).

## 3. Owner VPN downloads (paywalled — 38)
Values were read from abstracts (verify). Pull the PDF via school VPN **only if** you need deeper data. Main
publishers: Oxford Academic, Elsevier/ScienceDirect, SAGE, Wiley, Karger, Cambridge, Springer/BMC (BMC
redirects to Springer IDP → use the DOI). Each is tagged with its publisher in `access`. Highest-value:
Canada (Lancet CSHA), Mexico (OUP Mex-Cog — green-OA mirror noted), and several EU cohorts.

## 4. SCD feasibility conclusion (important)
SCD is **feasible as a national-overrides layer for ~38 countries, but there is no clean comparable baseline**
like Bai 2022 is for MCI:
- The instrument dominates the number. **Single-item self-report inflates to 40-60%** (China 46.4%, Japan 47.4%,
  Da Nang ~64%), while a **conservatively-worded single item** (US BRFSS 11.2%) or a structured **SCD-I** measure
  reads far lower. These are **not comparable** — do NOT put them on one colour scale.
- The only multi-country pooled anchor is **COSMIC** (~25.6%, 15 cohorts/15 countries) — too thin to use as a
  global regional baseline the way Bai 2022 works for MCI.
- **Recommendation**: ship SCD as **national-only** (no regional fill), label each country with its `criteria`,
  and either (a) split the legend by instrument, or (b) show SCD only for the subset with structured/SCD-I or
  conservative measures and mark the rest "self-report, indicative". Lead with a prominent heterogeneity caveat.

## 5. Then
`git pull` this PR → decide MCI/SCD wiring per above → download any §2/§3 items you need into `scripts/_data_in/`
→ update `build_mci_national()` + add `build_scd_national()` → bake into `world-globe.geojson` → open the
implementation PR (merge-commit, wait for owner). Keep the "modelled / heterogeneous / not cross-country
comparable" framing on both layers.
