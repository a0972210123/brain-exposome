# Brain Exposome · 腦健康 Exposome 檢測

An educational, front-end-only brain-health self-check and interactive world map, grounded in the
2024 *Lancet* Commission on dementia's 14 modifiable risk factors plus cumulative air-pollution
(PM2.5) exposure. It estimates an educational "brain-age acceleration" reference value and visualises,
country by country, dementia prevalence, PM2.5, population aging, PAF (population attributable
fraction) of modifiable risk, and MCI / SCD (mild cognitive impairment & subjective cognitive
decline) prevalence.

All calculation happens in the browser — **no personal data is uploaded or stored.**

> Deployed at **https://brain-exposome.mattye.dev**. Previously lived at
> `mattye.dev/projects/dementia-exposome/`; that path 301-redirects here.

## Tech stack

- **Astro 6** (static output) · plain CSS · no JS framework
- **Leaflet** for admin-1 (county/province) choropleth maps
- **d3-geo** orthographic canvas globe for the national world layer
- Data pipeline in **Python** (`scripts/build_data.py`)

## Develop

```bash
npm install
npm run dev        # http://localhost:4321
npm run build      # → dist/
npm run preview
```

## Data

Derived, ready-to-serve assets live in `public/data/` (committed). Raw, non-redistributable inputs
(NCD-RisC / WHO GHO / GBD / WorldPop / publisher PDFs) live in `scripts/_data_in/` (gitignored).
Regenerate the derived assets with:

```bash
python scripts/build_data.py
```

Sources, PAF math, and per-country provenance are documented in `docs/dementia-exposome/` and cited
in-app (references §). Key backbone sources: Livingston et al. 2024 (*Lancet* Commission), NCD-RisC,
WHO Global Health Observatory, GBD 2021, World Bank, and Bai et al. 2022 (global MCI meta-analysis).

## Layout

```
public/data/        derived, served data (dementia, exposome, pm25, aging, mci, scd, geo)
scripts/            build_data.py + helpers
src/pages/index.astro   the single-page app
src/layouts/ src/components/ src/styles/
docs/dementia-exposome/ methodology, provenance, data-refresh + migration notes
```

All estimates are **modelled** and for education only — not clinical or diagnostic advice.
