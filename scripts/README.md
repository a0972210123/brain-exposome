# scripts/ — data pipeline for the dementia-exposome project

Offline tooling that produces the static assets under `public/data/` consumed by
`/projects/dementia-exposome`. Nothing here runs at request time; the site stays
fully static.

## `build_data.py` — builds the map/calculator assets

```
pip install netCDF4 numpy shapely requests
python3 scripts/build_data.py        # run from repo root
```

Fetches ACAG satellite PM2.5 (S3), Taiwan boundaries (npm `taiwan-atlas`), and
Natural Earth admin-1, then writes:

- `pm25/tw-county-pm25.json`, `pm25/tw-district-pm25.json`, `pm25/world-country-pm25.json`
- `pm25/jp-admin1-pm25.json`, `pm25/kr-admin1-pm25.json` (Japan 47 / Korea 17 units)
- `geo/tw-districts.topo.json`, `geo/jp-admin1.geojson`, `geo/kr-admin1.geojson`
- `dementia/tw-dementia-modelled.json` (county-level modelled prevalence)
- `manifest.json` (provenance / licences)

If `_data_in/{cc}-admin1-pop.csv` is present (rates CSV optional — see below), it
also emits `dementia/{cc}-modelled.json` for that country. Surfacing it on the map
is a one-line `MAP_CFG` edit (documented in `data-download-points.md`); the page
ships PM2.5-only for JP/KR until real prevalence data exists.

## `scrape.py` — Playwright scraper for the blocked sources

```
pip install playwright
python3 scripts/scrape.py --list          # show recipes
python3 scripts/scrape.py --smoke         # harness self-test (no network)
python3 scripts/scrape.py tw_moi_77132 jp_estat_pop kr_kosis_pop
```

Drives a real browser through the government/research query pages (population by
age, prevalence rates) that `build_data.py` can't reach directly, saving into
`_data_in/`. **These targets are policy-blocked in this repo's CI sandbox** — the
scraper is meant to run on the owner's unrestricted network. `--smoke` proves the
browser harness works locally. Exact landing URLs + expected schemas:
`docs/side-projects/dementia-exposome/data-download-points.md`. **Step-by-step
runbook for a local session:** `docs/side-projects/dementia-exposome/local-session-handoff.md`.

## `_data_in/` (gitignored)

Drop-zone for downloaded CSV/PDF inputs. `build_data.py` consumes them; nothing
here is committed.
