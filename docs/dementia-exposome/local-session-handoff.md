# Local-session handoff — download the blocked prevalence/population data

*A runbook for a **local Claude Code session** (or the owner) to fetch the datasets the cloud build can't reach, then produce the Japan/Korea (and town-level Taiwan) dementia-prevalence map layers. Prepared July 2026.*

> **Companion docs:** `data-download-points.md` (exact URLs + schemas — the source of truth for every link/filename below) and `scripts/scrape.py` (Playwright recipes). This doc is the *ordered procedure*; it references those instead of repeating them.

---

## Why a local session solves it (the cloud one can't)

The `claude.ai/code` build sandbox routes all egress through a **strict policy allowlist**. Government/research portals — Japan e-Stat, Korea KOSIS, Taiwan data.gov.tw / NHRI, IHME GBD — return **HTTP 000** there, and Playwright uses the same proxy, so it can't bypass them. A **Claude Code session on your own machine (home/office Wi-Fi, no corporate proxy)** has normal internet and reaches all of them. So: run this on your laptop, not on the web.

**What's already done (don't redo):** PM2.5 map layers for 🇹🇼🇯🇵🇰🇷 are live, and the pipeline hook that turns downloaded CSVs into a prevalence map already exists (`build_admin_prevalence` in `scripts/build_data.py`, added in BUILD-4). This handoff only needs you to **fetch two inputs per country — population-by-age and prevalence rates — and drop them in `scripts/_data_in/`**.

---

## Step 0 — Preflight (30 seconds)

```bash
# You are on an OPEN network only if these return HTTP 200 (not 000):
curl -s -o /dev/null -w "%{http_code}\n" https://www.e-stat.go.jp/en
curl -s -o /dev/null -w "%{http_code}\n" https://kosis.kr/eng/
# If you see 000 / a proxy error, you're still behind a policy proxy — stop; switch networks.

# Environment (once):
pip install playwright && playwright install chromium      # for scripts/scrape.py
pip install netCDF4 numpy shapely requests                 # for scripts/build_data.py
mkdir -p scripts/_data_in                                  # drop-zone (gitignored)
python3 scripts/scrape.py --list                           # sanity: recipes print
python3 scripts/scrape.py --smoke                          # sanity: browser harness OK
```

---

## Step 1 — Download the inputs

Open `data-download-points.md` alongside this — it has the **direct page, the export step, and the exact `Save as` filename** for each row. Two kinds of source:

### A. Direct (scriptable — no login)
These you can `curl`/GET straight into `scripts/_data_in/`:

- **🇹🇼 Taiwan MOI #77132** town population by single-year age — RIS open-data JSON, e.g.
  `https://www.ris.gov.tw/rs-opendata/api/v1/datastore/ODRP014/{yyymm}` (loop `page=1..N`).
  → convert to the town-pop schema in `data-download-points.md`.
- **🇹🇼 Taiwan #33935** county 5-yr-age population — CSV download link on the dataset page.
- Or let the recipe capture the distribution links first: `python3 scripts/scrape.py tw_moi_77132`.

### B. Interactive (headed browser / free API key / human click)
e-Stat, KOSIS, NHRI PDF and GBD gate their exports behind a query UI, a free API key, or a login. Run the recipe **with a visible browser** and complete the query/login by hand when it opens:

```bash
python3 scripts/scrape.py jp_estat_pop kr_kosis_pop nhri_mci --headed --slowmo 300
```

- **🇯🇵 Japan** → `scripts/_data_in/jp-admin1-pop.csv` (prefecture × age band) + `jp-dementia-rates.csv` (age-band %; from MHLW/Ninomiya or GBD).
- **🇰🇷 Korea** → `scripts/_data_in/kr-admin1-pop.csv` (시도 × age) + `kr-dementia-rates.csv` (from NID report or GBD).
- **🇹🇼 MCI** → `nhri-mci-rates.csv` (adds the MCI layer later).

**Filenames matter** — `build_data.py` looks for exactly `{cc}-admin1-pop.csv` and `{cc}-rates.csv` / `{cc}-dementia-rates.csv`. Match the schemas at the bottom of `data-download-points.md`.

---

## Step 2 — Build the layers

```bash
python3 scripts/build_data.py
```

For each country where `_data_in/{cc}-admin1-pop.csv` is present it writes
`public/data/dementia/{cc}-modelled.json` and logs
`"{Country}: modelled prevalence for N units"`; where it's absent it logs
`"prevalence layer pending"`. (Rates CSV is optional — without it, it falls back to a
single crude 65+ rate.) Taiwan's PM2.5/county assets rebuild too; the authoritative
**town-level** TW prevalence additionally needs the #77132 → age-band rollup (the
`fetch_population` TODO in `build_data.py`) — wire that if you grabbed #77132.

---

## Step 3 — Surface the prevalence layer on the map (one line per country)

In `src/pages/projects/dementia-exposome.astro`, the `MAP_CFG` object gates each
country's layers. For a country whose `{cc}-modelled.json` now exists, add two keys:

```js
jp: { geojson: '/data/geo/jp-admin1.geojson', codeProp: 'code',
      layers: ['prevalence', 'pm25'],                       // ← add 'prevalence'
      prev: '/data/dementia/jp-modelled.json',              // ← add this line
      pm: '/data/pm25/jp-admin1-pm25.json' },
```

The disabled 失智盛行 button re-enables and the "prevalence pending" note disappears
for that country automatically. Rebuild + eyeball: `npm run build` then open
`/projects/dementia-exposome` and switch to that country.

---

## Step 4 — Finish (pick one)

- **(A) Hand the data back** — if you'd rather the web session wire it up: commit just
  the generated assets (`public/data/dementia/*.json`, any refreshed `public/data/pm25|geo/*`)
  **or** send me the CSVs and I'll run steps 2–3 here. *(Do not commit `scripts/_data_in/` — it's gitignored raw source.)*
- **(B) Ship it locally** — commit the asset(s) + the one-line `MAP_CFG` edit and push:
  ```bash
  git add public/data src/pages/projects/dementia-exposome.astro
  git commit -m "data: add {JP/KR} dementia-prevalence map layer"
  git push origin claude/dementia-exposome-mvp     # PR #114 picks it up
  ```

---

## Honest caveats

- **Interactive portals need a human.** e-Stat/KOSIS/GBD may require a login, a free
  API key (e-Stat `appId`, KOSIS key), or solving a CAPTCHA — headless can't; use
  `--headed` and click through, or export manually.
- **Licences travel with the data.** Each source has its own terms (e-Stat, KOSIS,
  GBD, NHRI) — add the attribution to `manifest.json` when you wire a new source in.
- **Prevalence is always a *modelled estimate*** (population × age-band rate), never
  measured — keep that wording on the map, as the TW layer already does.
