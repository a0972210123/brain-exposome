# Local-session handoff — bulk data download + data-input engineering (July 2026)

*Hand this whole file to a **Claude Code session on your own machine** (open network, no corporate proxy).
It is the **current, authoritative** handoff and supersedes the scope notes in the older
`local-session-kickoff.md` / `local-session-handoff.md` (their pipeline mechanics are still valid; their
"only Taiwan is live" status is stale — a lot has shipped since). Prepared by the cloud session that just
built the all-country **source ledger**.*

---

## Mission in one paragraph

The cloud session has finished the **source map**: for essentially every country we now know *where* each
kind of data lives (organisation, URL, year). What it **cannot** do is fetch the numbers — the build
sandbox blocks every government/research portal and API (World Bank, IHME/GBD, WHO, NCD-RisC, WorldPop,
national stats offices, journal publishers); only `WebSearch` works there. **Your job: on an open network,
download the numbers the ledger points at, run them through the existing pipeline, wire each country/metric
into the tool, and flip its ledger status from `identified` → `live`.**

---

## The master worklist = the provenance ledger (READ THIS FIRST)

Three committed files are your single source of truth. Every cell with `status: "identified"` is a concrete
"go fetch this" task; the URL + year tell you exactly what to get.

| File | What it holds |
|---|---|
| `public/data/data-provenance.json` | The shipped table data: 175-country ISO list, per-type global **defaults**, and **171 country `overrides`**. This is what the on-page 資料齊全度與來源 table renders. |
| `scripts/provenance-audit.json` | The **aging + prevalence** audit — 146 non-map countries, per-country `natSrc/natUrl/natYear` (+ optional sub-national), with `note` annotations. |
| `scripts/provenance-audit-cognitive.json` | The **MCI + SCD** deep audit — 100 countries, same shape. Authority for those two tabs. |
| `scripts/gen_provenance.py` | The generator that merges the three above + `exposome.json` → `data-provenance.json`. **Re-run it whenever you edit a source or flip a status.** |

**Status semantics** (this is the whole game): `live` ✅ = numbers already in the tool · `seed` ◐ = partial
estimate in the tool · `identified` ○ = **source found, numbers NOT yet fetched — your queue** · `none` — =
no data exists anywhere.

Ledger-status snapshot (per `data-provenance.json`, today):

| Tab | live | seed | identified (← your queue) | none |
|---|---|---|---|---|
| 老年人口 65+ | 14 | 13 | **148** | 0 |
| 失智盛行率 | 15 | 0 | **160** | 0 |
| MCI | 0 | 0 | **99** | 76 |
| SCD | 0 | 0 | **32** | 143 |
| PM2.5 | 175* | — | — | 0 |
| 5 factors + PAF | 27 | 0 | **148** | 0 |

\*PM2.5 default is the global ACAG product; admin-1 zonal is live for the 27 map countries.

---

## What is already LIVE (do NOT redo)

- **27 "map" countries** (`tw jp kr cn us br mx ir in · th vn id ph my bd mm · pk gb de fr it es pl ca au nz tr`)
  each have, wired and shipping: **admin-1 dementia prevalence** (`public/data/dementia/{cc}-modelled.json`,
  27 files), **admin-1 PM2.5** (`public/data/pm25/`, 29 files), and the **5 exposome risk factors + composite
  PAF** (national). Their `-admin1.geojson` boundaries are in `public/data/geo/` (26 files).
- **Aging 65+ globe layer** renders **46 countries** (baked `pop65` in `world-globe.geojson` from
  `SEED_POP65` + optional `scripts/_data_in/world-65plus.csv` overlay).
- **World globe** country-level layers: `pm25` baked for 174/177 features, `paf` for 27, `pop65` for 46.
- **The disclosure table itself** — renders all of the above from `data-provenance.json`.

So the gaps to fill are: (a) the ~148 non-map countries' national numbers, (b) admin-1 detail for more of
them, and (c) **MCI/SCD everywhere** (99/32 sources found, zero numbers wired — the two tabs are still
"規劃中/planned").

---

## Prioritised plan (hybrid: global sweeps first, then per-country, per the owner's earlier decision)

### Phase 1 — global sweeps (one download → ~200 countries, uniformly comparable)
1. **Aging 65+** — World Bank `SP.POP.65UP.TO.ZS` (`?format=json&per_page=400&mrnev=1`) → save as
   `scripts/_data_in/world-65plus.csv` (`iso2,pct`). `_load_pop65()` (build_data.py:1185) overlays it onto
   `SEED_POP65` and bakes `pop65` into `world-globe.geojson`. Lifts aging from 46 → ~200 countries.
2. **National dementia prevalence** — IHME **GBD 2023** Results Tool export (cause *Alzheimer's & other
   dementias*, measure *Prevalence*, by location/age) → national %/rate for every country. Feeds a
   country-level prevalence layer for the ~148 non-map countries. (`GBD_DIR = _data_in/GBD`, build_data.py:666.)
3. **Risk factors** — **NCD-RisC** (raised BP / diabetes / BMI≥30) + **WHO GHO** (tobacco / insufficient
   activity) national files → extend the exposome layer beyond the current 27 (loader at build_data.py:1063,
   `_data_in/ncdrisc/`).

### Phase 2 — per-country deep-dives (admin-1 detail + national studies)
Walk the ledger's `identified` rows. Each names a real study/portal:
- **Quick wins** (a published table of final % per admin unit → just transcribe): use
  `build_direct_prevalence(cc, name, units)` (build_data.py:953) reading `_data_in/{cc}-admin1-prevalence.csv`.
- **Model from pop×rate** (census/WorldPop age bands × GBD/national rates): use
  `build_admin_prevalence(cc, name)` (build_data.py:635) reading `_data_in/{cc}-admin1-pop.csv` (+ optional rates).
- **Aging admin-1**: emit `{cc}-aging.json` from WorldPop/census age surfaces (same drill-down pattern).

### Phase 3 — MCI / SCD (new — 99 + 32 sources in `provenance-audit-cognitive.json`)
These two tabs are `planned` with no numbers. For the data-rich anchors first — **US** (Mayo MCSA + CDC BRFSS),
**China** (Jia 2020), **Japan** (JPSC-AD), **Korea** (NaSDEK), **Taiwan** (Sun 2014), major Europe (SHARE
harmonised 2025 gives country-specific MCI for many EU members in one export) — fetch the prevalence figures,
then decide with the owner whether MCI/SCD become their own choropleth layers or national-only table values.
Many entries are sub-national cohorts or screening (not diagnostic MCI) — respect the `note` caveats.

---

## Pipeline drop-in (the mechanics that already exist)

1. Drop downloaded inputs in **`scripts/_data_in/`** (gitignored — never commit raw inputs). Schemas +
   exact `Save as` names live in `data-download-points.md` (the source of truth for filenames).
2. Run **`python3 scripts/build_data.py`** → writes `public/data/dementia/{cc}-modelled.json`,
   `world-globe.geojson`, etc.; logs `"{Country}: modelled prevalence for N units"` or `"pending"`.
3. **Light up a map country** — one `MAP_CFG` entry in `src/pages/projects/dementia-exposome.astro`
   (~line 1403). Copy an existing row; pick the right `prevMetric` (`PREV_60`, `PREV_CN`, `PREV_IN`,
   `PREV_60_SEA`, or a new per-country legend) and point `prev`/`pm` at the generated JSONs.
4. **Update the ledger** so the disclosure table tells the truth: edit the matching entry in
   `scripts/provenance-audit.json` / `provenance-audit-cognitive.json` (or the hand-authored `OV` block in
   `gen_provenance.py` for a map country), change `status` `identified` → `live`/`seed`, then
   **`python3 scripts/gen_provenance.py`** to regenerate `data-provenance.json`.
5. Add attribution in **`public/data/manifest.json`** for every new source.
6. `npm run build`, eyeball the page, commit **generated assets + the `MAP_CFG`/ledger edits + manifest**
   (NOT `_data_in/`). **One PR per country/batch**, merge-commit, per `CLAUDE.md`.

`scripts/scrape.py` has Playwright recipes for the interactive portals (`--list`, `--headed`) —
registered: `nhri_mci`, `jp_estat_pop`, `kr_kosis_pop`; add more as needed.

---

## Guardrails (carry these into every commit)

- **Prevalence is always a *modelled / latest-available estimate*** — keep that wording; never call it measured.
- **Metrics differ by source** (TW = cases/1,000 all-ages; CN = % 50+; IN = % 60+; GBD = % 60+) → per-country
  legends already exist; **don't compare colours across countries.**
- **Match boundary names exactly** against the `-admin1.geojson` (`unit_name` case-insensitive, or ISO-3166-2
  `unit_code`); log & alias unmatched units.
- **Licences travel with data** — GBD non-commercial (attribution); WorldPop/HRSL CC BY 4.0; NCD-RisC, WHO,
  e-Stat/KOSIS/national offices each their own. Add to `manifest.json`.
- **MCI/SCD**: many ledger entries are screening-tool or sub-national figures (flagged in `note`) — surface
  that caveat; don't present a Kinshasa cohort as a national rate.

## Read-first files (in order)

1. **this file** — mission, worklist, priorities.
2. `docs/side-projects/dementia-exposome/all-country-source-audit.md` — how the ledger was built + coverage.
3. `public/data/data-provenance.json` + `scripts/provenance-audit*.json` — the actual worklist.
4. `data-download-points.md` — exact URLs, `Save as` names, **schemas**.
5. `scripts/build_data.py` — the pipeline (hooks cited above).
6. `src/pages/projects/dementia-exposome.astro` `MAP_CFG` (~L1403) — the one-line-per-country switch.
7. `public/data/geo/{cc}-admin1.geojson` — the exact admin-unit names to match.

## Copy-paste kick-off prompt (paste into your local Claude Code session)

> You are picking up the dementia-exposome data-ingestion job on an open network. Read
> `docs/side-projects/dementia-exposome/local-session-handoff-2026-07.md` first, then
> `public/data/data-provenance.json` + `scripts/provenance-audit.json` +
> `scripts/provenance-audit-cognitive.json` — every `status:"identified"` cell is a download task with its
> source URL + year. Start with **Phase 1 global sweeps** (World Bank 65+, GBD 2023 national prevalence,
> NCD-RisC/WHO factors), dropping inputs in `scripts/_data_in/`, then `python3 scripts/build_data.py`. For
> each country/batch you light up: add/adjust its `MAP_CFG` row, flip its ledger `status` to `live`/`seed`
> and re-run `python3 scripts/gen_provenance.py`, add `manifest.json` attribution, `npm run build`, and open
> **one PR per batch** (merge-commit, wait for the owner's 「可以 merge」) per `CLAUDE.md`. Keep the
> "modelled estimate" wording and per-country legends; never compare colours across countries.
