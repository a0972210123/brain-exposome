# Local-session kick-off — dementia-exposome data scraping

*Hand this whole file to a **Claude Code session running on your own machine** (open network, no corporate proxy). It contains the mission, the prioritised data list, the git paths to read first, and a copy-paste kick-off prompt. Prepared July 2026.*

---

## Why a local session (the cloud one can't)

The `claude.ai/code` build sandbox routes all egress through a **strict policy allowlist**. Reachable there (already wired): ACAG PM2.5 (S3), Natural Earth, npm/GitHub, PyPI. **Blocked there (HTTP 000/403):** every government/research portal — IHME GBD, WorldPop, WHO, Japan e-Stat, Korea KOSIS, Taiwan data.gov.tw / NHRI, and journal publishers. Playwright uses the same proxy, so `scripts/scrape.py` can't bypass it in the cloud. **A session on your home/office Wi-Fi reaches all of them** — that's this job.

## What is already done (DO NOT redo)

- **PM2.5 choropleth for 27 countries** — all live (ACAG zonal per admin-1). No more PM2.5 work needed.
- **Prevalence pipeline hooks** already exist in `scripts/build_data.py`:
  - `build_direct_prevalence(cc, name, units)` — reads `_data_in/{cc}-admin1-prevalence.csv` (one final % per admin unit). **This is the China/India path.**
  - `build_admin_prevalence(cc, name)` — reads `_data_in/{cc}-admin1-pop.csv` (+ optional `{cc}-rates.csv`) and models `Σ(pop_band × rate_band)`. **This is the Japan/Korea/other path.**
- **Map metric + legend for CN (盛行率 50+ %) and IN (盛行率 60+ %) are already wired** (`PREV_CN`/`PREV_IN` in the page). CN/IN only need the CSV downloaded + one `MAP_CFG` line.
- **Only Taiwan prevalence is live today.** Everything below is the gap.

---

## Data-fill strategy (confirmed: hybrid, global-first) + global sweeps

The owner chose a **hybrid** approach: **do the global-per-metric sweeps first** (any metric with a
complete global database → one pull covers ~200 countries, uniformly comparable), then per-country
deep-dives for the gaps (mostly admin-1 detail from national censuses / gov portals / single papers).
The cloud session can't reach these APIs (World Bank/OWID/UN all 403 there), so they run here.

### ⭐ Global sweep #1 — Aging 65+ (World Bank, one call)

The **aging-society layer already ships** with a partial seed (`SEED_POP65` in `build_data.py`, ~46
countries). Replace it with the full global set:

- **Fetch:** World Bank indicator **`SP.POP.65UP.TO.ZS`** ("population ages 65+, % of total"),
  most-recent value per economy:
  `https://api.worldbank.org/v2/country/all/indicator/SP.POP.65UP.TO.ZS?format=json&per_page=400&mrnev=1`
- **Save as** `scripts/_data_in/world-65plus.csv` with header `iso2,pct` (map the API's ISO3 → ISO2).
  `build_data.py` `_load_pop65()` overlays it onto the seed → bakes `pop65` into `world-globe.geojson`.
  Then `python3 scripts/build_data.py` (or just re-run `build_world_globe_geojson()`).
- **Admin-1 aging (縣市/州省 65+):** the WorldPop 2020 age surfaces you already downloaded for the
  prevalence layer contain the 65+ counts. Emit a `{cc}-aging.json` (unit_code → 65+ %) per country
  and (fast-follow) wire an admin-1 aging layer — same drill-down pattern as prevalence.

### Other global sweeps (same idea, when their DB is reachable here)
- **GBD 2021/2023 national prevalence** (all countries) — IHME Results Tool export (backbone).
- **NCD-RisC risk factors** (BP / diabetes / BMI / smoking / inactivity) — extend the exposome layer
  beyond the current 27 countries.
- **UN WPP** national by-age — cross-check WorldPop / aging.

### Then: per-country deep-dives (the gaps)
Admin-1 prevalence where no global study exists, national dementia surveys, etc. — the per-country
list below (China/India done; Japan/Korea via e-Stat/KOSIS; others via GBD×WorldPop).

---

## The data list to fetch (priority order)

Exact URLs, export steps, `Save as` filenames, and schemas live in **`data-download-points.md`** — that is the source of truth; this is the ordered summary. Drop every file in `scripts/_data_in/` (gitignored), then run `python3 scripts/build_data.py`.

### ⭐ Tier 1 — quick wins (one CSV each → lights up a whole country immediately)
These studies publish a **final modelled prevalence per province/state**, so no population×rate step — just transcribe the table.

| # | Country | Source table | Metric | Save as → `scripts/_data_in/` |
|---|---|---|---|---|
| 1 | 🇨🇳 China | **Liu/Gao et al. 2024**, *Lancet Reg Health – W Pac*, "Geographical variation in dementia prevalence across China" — **Appendix G** (28 provinces, CHARLS 2018) · PMC11225804 | % among 50+ (range 2.62–13.53%) | `cn-admin1-prevalence.csv` |
| 2 | 🇮🇳 India | **Lee et al. 2023**, *Alzheimer's & Dementia*, "Prevalence of dementia in India" — **Table 2** (states/UTs, LASI-DAD) · PMC10338640 / doi:10.1002/alz.12928 | % among 60+ (Delhi 4.5%, J&K 11.0%) | `in-admin1-prevalence.csv` |

Schema (`{cc}-admin1-prevalence.csv`): `unit_name,prevalence_pct` — match `unit_name` (case-insensitive) to the English name in `public/data/geo/{cn,in}-admin1.geojson` (e.g. `Xinjiang`, `Beijing`; `Delhi`, `Jammu and Kashmir`), or give `unit_code` (ISO-3166-2, `CN-XJ` / `IN-DL`). Unmatched rows are logged.

### Tier 2 — Taiwan upgrades
| # | Feeds | Source | Save as |
|---|---|---|---|
| 3 | Town-level (368) prevalence — upgrades the map from county to 鄉鎮市區 | MOI **#77132** 鄉鎮市區單一年齡人口 · data.gov.tw/dataset/77132 · API `ris.gov.tw/rs-opendata/api/v1/datastore/ODRP014/{yyymm}` (`page=1..N`) | `tw-town-pop.csv` |
| 4 | **MCI** layer (owner asked for it) | NHRI 全國社區失智症流行病學調查 (projects.nhri.edu.tw/spdc) + 2024 press release age-band MCI% table | `nhri-mci-rates.csv` |

### Tier 3 — Japan / Korea prevalence (population × rate)
| # | Country | Population half | Rates half | Save as |
|---|---|---|---|---|
| 5 | 🇯🇵 Japan | e-Stat 都道府県×年齢(5歳階級) | MHLW/Ninomiya (久山町研究) or GBD 2021 | `jp-admin1-pop.csv` + `jp-dementia-rates.csv` |
| 6 | 🇰🇷 Korea | KOSIS 시도×age | 중앙치매센터 (nid.or.kr) or GBD 2021 | `kr-admin1-pop.csv` + `kr-dementia-rates.csv` |

### Tier 4 — broad expansion (the 21 other PM2.5 countries)
Backbone route (from `prevalence-data-sources.md`): **GBD 2021 national age-specific rates × WorldPop admin-1 population-by-age.**
| # | Feeds | Source | Notes |
|---|---|---|---|
| 7 | Universal rate backbone | **IHME GBD 2021 Results Tool** (vizhub.healthdata.org/gbd-results) — cause *Alzheimer's & other dementias*, measure *Prevalence*, by location/age/sex → CSV | free login; interactive export; non-commercial licence (attribution) |
| 8 | Admin-1 population by age | **WorldPop** age/sex gridded population (CC BY 4.0, direct GeoTIFF URLs) → zonal-aggregate to the existing Natural Earth admin-1 polygons | machine-fetchable |

### Tier 5 — nice-to-have (see `good-to-have-data.md`)
Taiwan county/district **risk-factor** prevalence (国健署 HPA/NHIS) → modifiable-factor burden map; NHIRD diagnosed-prevalence layer (application required); ADI World Alzheimer Report figures.

### Also resolve (deep-research open questions — from `prevalence-data-sources.md`)
1. Concrete URL + table + licence for **Korea** (nid.or.kr) and **Japan** national rates (Ninomiya/MHLW).
2. Downloadable per-province/state CSV for Liu/Gao 2024 & Lee 2023, or must admin-1 values be transcribed from figures?
3. Do any expansion countries (UK CFAS, Brazil ELSI, Indonesia/Thailand/Vietnam 10/66) have **published admin-1** prevalence, or all GBD fallback?
4. Best WorldPop→Natural-Earth-admin-1 crosswalk with consistent 5-yr bands + recent vintage.
5. Is IHME's non-commercial licence OK for hosting derived admin-1 values in a public client-side map (attribution vs permission)?

---

## Git paths to read first (in this order)

| Path | Why |
|---|---|
| `docs/side-projects/dementia-exposome/local-session-kickoff.md` | **this file** — the mission & list |
| `docs/side-projects/dementia-exposome/data-download-points.md` | exact URLs + `Save as` names + **schemas** (source of truth) |
| `docs/side-projects/dementia-exposome/prevalence-data-sources.md` | deep-research report — sources, caveats, open questions |
| `docs/side-projects/dementia-exposome/local-session-handoff.md` | the older ordered runbook (preflight, step-by-step) |
| `docs/side-projects/dementia-exposome/good-to-have-data.md` | priority/status of every candidate dataset |
| `docs/side-projects/dementia-exposome/other-country-maps-pipeline.md` | per-country expansion pattern |
| `scripts/build_data.py` | pipeline — `build_direct_prevalence` (~L566), `build_admin_prevalence` (~L541), `DATA_IN` (L43), manifest loop (~L727) |
| `scripts/scrape.py` | Playwright recipes — registered: `nhri_mci`, `jp_estat_pop`, `kr_kosis_pop` (`--list` / `--headed`) |
| `src/pages/projects/dementia-exposome.astro` | `MAP_CFG` — the one-line-per-country switch to light up a prevalence layer |
| `public/data/geo/{cn,in,jp,kr,…}-admin1.geojson` | the **exact admin-unit names** to match your CSV `unit_name` against |
| `public/data/manifest.json` | attribution — add a line when you wire a new source |

## The workflow once data is in

1. `python3 scripts/build_data.py` → writes `public/data/dementia/{cc}-modelled.json`; logs `"{Country}: modelled prevalence for N units"` or `"pending"`.
2. **Light up the country** — one `MAP_CFG` entry in `dementia-exposome.astro`:
   ```js
   // China (metric PREV_CN already defined):
   cn: { …, layers: ['prevalence', 'pm25'], prevMetric: PREV_CN, prev: '/data/dementia/cn-modelled.json' },
   in: { …, layers: ['prevalence', 'pm25'], prevMetric: PREV_IN, prev: '/data/dementia/in-modelled.json' },
   // Japan/Korea (cases-per-1000 style, like TW):
   jp: { …, layers: ['prevalence', 'pm25'], prev: '/data/dementia/jp-modelled.json' },
   ```
3. `npm run build` → open `/projects/dementia-exposome`, switch to that country, confirm the 失智盛行 button re-enables and the choropleth renders.
4. Commit **generated assets + the `MAP_CFG` edit + manifest attribution** (NOT `scripts/_data_in/` — it's gitignored). One PR per country/batch, merge-commit, per `CLAUDE.md`.

## Guardrails
- **Prevalence is always a *modelled estimate*** (or a published modelled study) — never call it measured; keep that wording on the map.
- **Metrics differ by source** (TW = cases/1,000 all-ages; CN = % 50+; IN = % 60+) → per-country legends already exist; **don't compare colours across countries.**
- **Licences travel with data** — GBD non-commercial (attribution); WorldPop/HRSL CC BY 4.0; e-Stat/KOSIS/NHRI each their own. Add to `manifest.json`.
- **Match boundary names exactly** — transcribe against the `-admin1.geojson`; log & alias unmatched units.
- Interactive portals (GBD/e-Stat/KOSIS) need a human click / free API key / login — run `scrape.py --headed` and complete by hand, or export manually.
