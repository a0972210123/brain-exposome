# All-country source audit — dementia-exposome provenance ledger

*Prepared July 2026. This is the human-readable companion to the machine-readable ledger
`scripts/provenance-audit.json` (146 non-map countries) + `public/data/data-provenance.json`
(the shipped table data). It records **where each country's data lives** — it does not fetch the
numeric values (that stays the local session's job, see `local-session-kickoff.md`).*

---

## Why this pass

The on-page **資料齊全度與來源** disclosure table (`/projects/dementia-exposome`, 11 tabs × all
countries) originally carried hand-researched `overrides` for only the **27 map countries**. Every
other country fell through to the global default (GBD 2023 for prevalence, World Bank for aging). The
owner asked to **「再次徹底清查所有國家各面向資料」** — audit *every* country across *every* aspect so the
ledger shows each country's *best available* national/sub-national source, not a blanket fallback.

## How it was done

The build sandbox can only reach `WebSearch` (WebFetch + World Bank / OWID / Wikipedia APIs are
proxy-blocked). So this pass expands the **source map**, run as **13 regional WebSearch research
agents** in parallel, each covering every country in its region across prevalence (national +
sub-national), aging (national statistics office), and MCI/SCD existence. Findings were merged,
HTML-entity-cleaned, and folded into the generator.

Regenerate any time with:

```
python3 scripts/gen_provenance.py     # world-globe.geojson + provenance-audit.json + provenance-audit-cognitive.json + exposome.json
```

## Follow-up passes (owner review)

- **Factor-cell links.** The 27 map countries' 5 risk-factor cells come from `exposome.json` (source + year
  only), so they rendered as plain text while every other country's factor cell was linked. Fixed in
  `gen_provenance.py` with a source→URL map (NCD-RisC → ncdrisc.org, WHO GHO → who.int/data/gho, Taiwan NHIS
  → nhis.nhri.edu.tw) — **every cell on every tab is now a hyperlink.**
- **MCI/SCD deep audit.** The first audit skipped the 27, so US/China/Japan/Korea/Taiwan had no MCI/SCD entry.
  A dedicated MCI + SCD WebSearch pass over **all** countries (incl. the 27) lives in
  `scripts/provenance-audit-cognitive.json` and is the generator's single authority for those two aspects:
  **99 countries now have an MCI source and 32 an SCD source** (US = Mayo MCSA + CDC BRFSS; China = Jia 2020;
  Japan = JPSC-AD; Korea = NaSDEK; Taiwan = Sun 2014; Europe via national cohorts / SHARE / Alzheimer Europe).

## Coverage (after the audits)

| | Before | After |
|---|---|---|
| Countries with any override | 27 | **171** / 175 |
| Distinct **dementia-prevalence** source | 27 | **125** (27 map + 98 audited) |
| National **aging** (65+) source | 27 | **171** |
| **MCI** source | 0 | **99** |
| **SCD** source | 0 | **32** |

The 4 countries with **no** override (all defaults): `AQ`, `TF` (uninhabited — no agent run), `ER`
(Eritrea — never held a census, no public stats portal), `EH` (Western Sahara — disputed, no NSO).

## What varies by country vs what stays global

- **Prevalence** — the real yield. 98 of the 146 audited countries have a distinct national study,
  a sub-national cohort, or a named regional study; the rest keep the **GBD 2023** default.
- **Aging 65+** — 144 of 146 now point at the country's **own census / statistics office** (more
  specific than the World Bank default).
- **MCI / SCD** — after the dedicated cognitive pass, **99** countries have an MCI source and **32** an SCD
  source. Many are sub-national cohorts or screening studies (flagged in `note`s); SHARE's harmonised 2025
  paper backstops several EU members, and SCD is dominated by a handful of national instruments (US CDC BRFSS,
  Canada CLSA, national cohorts in DE/GB/FR/ES/IT/NL/SE/NO). Countries with no study still render `—`.
- **PM2.5** — already a global **ACAG** default (live at admin-1 for the 27); **not re-audited**.
- **5 risk factors + composite PAF** — global **NCD-RisC / WHO GHO** defaults; per-country overrides
  exist only for the 27 (pulled from `exposome.json`). Extending them needs numeric NCD-RisC pulls
  (blocked here) → they stay on the global default for the other ~148 countries.

## Notable prevalence sources found (highlights — full list in `provenance-audit.json`)

| Region | Genuine national / landmark studies | Regional or fallback source |
|---|---|---|
| **East / Central Asia** | Mongolia (VCI overview); Kazakhstan/Kyrgyzstan (Int. Psychogeriatrics); Georgia (Alz-Europe-rate estimate) | GBD for AZ/TJ/TM/UZ |
| **South Asia** | Afghanistan (Trani 2023, RUDAS); Sri Lanka (de Silva 2003); Nepal (Thapa 2025, Dharan) | South-Asia GBD for Bhutan |
| **Middle East** | Israel (national cohort); Saudi (Hajjar 2025 + Alkhunizan 2018); Jordan (Kofahi); Lebanon (Phung, 10/66) | Qassem 2023 *Dementia in the Arab world* for AE/IQ/KW/OM/PS/QA/SY/YE |
| **North Africa** | Morocco (Chahidi 2025, first national); Tunisia (national reviews); Egypt (Elshahidi review + El Tallawy admin-1) | GBD-MENA for DZ/LY/SD |
| **Sub-Saharan Africa** | Nigeria (Indianapolis-Ibadan); CAR & Congo (EPIDEMCA); Cameroon (Ntui); Ghana (national); Senegal (IPRES); Tanzania (Hai); South Africa (HAALSI/Agincourt); Kenya/Uganda/Rwanda/Zambia (sub-national) | GBD for the remaining ~30 |
| **West / North Europe** | Austria, Denmark, Finland, Switzerland (national reports/registries); Greece (HELIAD); Norway (HUNT4); Iceland (AGES); Luxembourg; Portugal (10/66); Greenland (Nielsen Arctic) | Alzheimer Europe Yearbook for BE/NL/SE |
| **East / SE Europe** | Albania (nationwide 2024); Russia (EVKALIPT national) | Alzheimer Europe Yearbook (EU + non-EU); GBD 2019 for BY/MD/ME; CEE meta-analysis for XK |
| **Americas & Caribbean** | El Salvador (Hernández, national); Costa Rica (CRELES); Trinidad (national survey); Jamaica (Kingston); Cuba/DR/PR/Peru/Venezuela (10/66); Argentina (Matanza-Riachuelo); Chile & Colombia (national syntheses); Ecuador (Atahualpa) | Ribeiro 2022 LAC review for BS/BZ/HN/NI; GBD for GY/HT/PY/SR/UY |
| **Oceania** | — | Western-Pacific GBD; national stats offices for aging only |

## Status legend (as rendered in the table)

`live` ✅ wired into the tool · `seed` ◐ partial estimate · `identified` ○ source found, not yet
wired (almost all audit rows) · `none` — no data yet. The audit rows are `identified`: the source is
located, but the numeric value still has to be fetched by the local session before it goes `live`.

## Files

- `public/data/data-provenance.json` — regenerated shipped table data (27 → 171 overrides).
- `scripts/gen_provenance.py` — the committed generator (types + 27 hand-authored + audit merges + exposome factors + factor-URL map).
- `scripts/provenance-audit.json` — the 146-country aging/prevalence audit findings, per-country, with `note` annotations.
- `scripts/provenance-audit-cognitive.json` — the MCI/SCD deep-audit findings (100 countries), the authority for those two tabs.
