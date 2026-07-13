# Other-country maps — build pipeline & expansion plan

*How to add a dementia/PM2.5 choropleth for any country, then expand one country at a time. Prepared July 2026.*

The Taiwan map (`scripts/build_data.py` → `public/data/{geo,dementia,pm25}`) is the reference implementation. This doc generalises it so a new country can be added incrementally without re-architecting.

---

## The four ingredients per country

| # | Ingredient | Taiwan source (done) | Generic source for country X |
|---|---|---|---|
| 1 | **Admin boundaries** (choropleth geometry) | taiwan-atlas 鄉鎮市區 (MOI #7441), TopoJSON | **geoBoundaries** ADM1/ADM2 (`geoboundaries.org/api/current/gbOpen/{ISO3}/ADM1/`) or **Natural Earth** ADM1; else the national mapping agency |
| 2 | **Population by age** (per admin unit) | MOI #77132 (blocked → county snapshot) | National statistics office; else **UN WPP** subnational where available |
| 3 | **Dementia prevalence rates** (age-band) | NHRI 2020–2023 survey | National survey if it exists; else **GBD 2021** (IHME) country/subnational age-specific rates |
| 4 | **PM2.5** (per admin unit) | ACAG 0.1° zonal per town/county | **ACAG sub-national REGIONAL CSV** where it exists (**China, India, USA, Canada** — `s3://satpmdata/V6GL03/RegionSummaries/{Country}PM25…REGIONAL…csv`); else **zonal over the ACAG grid** (the `county_year_series` / `town_recent_pm` method in `build_data.py`) using the ingredient-1 polygons |

Prevalence model is the same everywhere: `modelled_cases = Σ_ageband(pop_unit,band × rate_band)`; colour by cases per 1,000 residents. Always label it a **modelled estimate**.

---

## Generalising `build_data.py`

Refactor into a per-country config + a shared engine:

```python
COUNTRIES = {
  "TW": { "iso3": "TWN", "bbox": (118.0,122.5,21.4,26.5),
          "boundaries": ("taiwan-atlas", "towns"),      # loader id + object
          "join_key": "TOWNCODE",
          "population": ("moi_77132", ...),               # loader + args (or committed snapshot)
          "rates": NHRI_RATES,                            # age-band -> prevalence
          "pm25": ("acag_zonal", "0p10") },               # or ("acag_region_csv", "China")
  "JP": { "iso3": "JPN", "bbox": (122.0,154.0,24.0,46.0),
          "boundaries": ("geoboundaries", "ADM1"),
          "join_key": "shapeID",
          "population": ("unwpp_subnational", ...),
          "rates": JP_RATES,                              # from a national survey or GBD
          "pm25": ("acag_zonal", "0p10") },
  # …
}
```

The shared engine already exists in `build_data.py`:
- `load_pm25_years()` — crop ACAG to a **bbox** (parametrise the constant `TW_BBOX`).
- `county_year_series()` / `town_recent_pm()` — zonal mean by polygon (works for any polygons).
- `build_world_country_pm25()` — country-level fallback (already global).
- Add loaders: `acag_region_csv(country)` (parse the sub-national REGIONAL CSV like the Global one), `geoboundaries(iso3, level)`, `unwpp_subnational(...)`, `gbd_rates(iso3)`.

Outputs per country → `public/data/geo/{iso3}-districts.topo.json`, `public/data/dementia/{iso3}-modelled.json`, `public/data/pm25/{iso3}-district-pm25.json` (mirror the TW filenames).

---

## Page / map integration

The map section in `src/pages/projects/dementia-exposome.astro` is currently hard-wired to the TW assets. To support multiple countries:
1. Add a **country switcher** above the map (reuse the residence `COUNTRY_LIST`); on change, `fetch` that country's `geo`/`dementia`/`pm25` assets and re-init the Leaflet layer (`geoLayer.clearLayers()` + re-add, `fitBounds`).
2. Keep the same `styleFn`/`tooltipFor`/legend — they already read a generic `{byTown/byUnit, districts}` shape; standardise the JSON keys across countries (`join_key`, `rate_per_1000`, `pm25`).
3. Manifest + attribution per country (each has its own boundary/population/rate licences).

The calculator's residence PM2.5 already works globally (country dropdown → `world-country-pm25.json`); sub-national residence PM2.5 per country is a later enhancement (use the same REGIONAL CSVs / zonal outputs).

---

## Per-country expansion checklist (priority queue)

Fill a row's cells as each ingredient is secured; flip **status** to *ready* when all four are in and the assets build.

| Country | 1 Boundaries | 2 Population by age | 3 Prevalence rates | 4 PM2.5 | Status |
|---|---|---|---|---|---|
| 🇹🇼 Taiwan | ✅ taiwan-atlas | ⚠️ county snapshot (want #77132) | ✅ NHRI 2020–23 | ✅ ACAG zonal | **live (county-level prevalence + town PM2.5)** |
| 🇯🇵 Japan | ✅ Natural Earth admin-1 (47) | ⏳ e-Stat (download) | ⏳ GBD / Ninomiya-Kyushu (download) | ✅ ACAG zonal (8.9–12.9 µg/m³) | **PM2.5 live; prevalence pending download** |
| 🇰🇷 South Korea | ✅ Natural Earth admin-1 (17) | ⏳ KOSIS (download) | ⏳ NID report / GBD (download) | ✅ ACAG zonal (12.8–22.1 µg/m³) | **PM2.5 live; prevalence pending download** |
| 🇨🇳 China | ✅ Natural Earth admin-1 (31) | — (direct study) | ✅ **Liu/Gao 2024 provinces (download)** | ✅ ACAG zonal (9.8–41.6) | **PM2.5 live; prevalence drop-in ready (download Appendix G)** |
| 🇺🇸 USA | ✅ Natural Earth admin-1 (49) | US Census | GBD / CDC | ✅ ACAG zonal (4.4–8.5) | **PM2.5 live; prevalence pending** |
| 🇮🇳 India | ✅ Natural Earth admin-1 (36) | — (direct study) | ✅ **Lee 2023 states (download)** | ✅ ACAG zonal (11.5–86.2) | **PM2.5 live; prevalence drop-in ready (download Table 2)** |
| 🇬🇧 UK | Natural Earth admin-1 | ONS | GBD / national | ACAG zonal | not started |

**Done this round (Japan + South Korea):** boundaries via **Natural Earth admin-1** (`iso_a2 ∈ {JP,KR}` → `public/data/geo/{jp,kr}-admin1.geojson`, code = ISO-3166-2) and **real sub-national PM2.5** via ACAG zonal-mean per unit (`public/data/pm25/{jp,kr}-admin1-pm25.json`, recent-3-yr mean). The page's map country switcher renders both. **Prevalence maps are NOT built** — population-by-age + prevalence rates are policy-blocked here; the owner downloads them (`data-download-points.md`) and the pipeline emits `{jp,kr}-modelled.json`, which auto-enables the prevalence layer.

**Next expansion:** China / USA / India — their **sub-national PM2.5 is already published by ACAG** (REGIONAL CSV), so only population + rates remain.

**Reachability note (from the build sandbox):** ACAG (S3), Natural Earth, geoBoundaries, npm/GitHub, pypi are reachable; UN WPP, WHO, GBD export, and every national stats portal (e-Stat, KOSIS, data.gov.tw) are **policy-blocked here** — and **Playwright routes through the same proxy, so `scripts/scrape.py` cannot bypass it in this sandbox** (it's built for the owner's open network). The owner downloads those (see `data-download-points.md` / `good-to-have-data.md`) and drops them in `scripts/_data_in/` for the pipeline.
