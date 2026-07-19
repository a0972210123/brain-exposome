# Sub-national (admin-1) "% aged 65+" — source manifest for Tier 2

Companion to the aging layer. **Tier 0** (shipped) shades every admin-1 unit with the country's *national*
65+ % (World Bank; MOI for Taiwan). **Tier 1** = WorldPop 2020 age grids (re-run the pipeline). **Tier 2** (this
doc) = replace with **real official admin-1 figures** where a statistics office publishes them, for a true
within-country gradient. Verified 2026-07-20 (WebSearch + WebFetch against official domains).

**Key finding:** almost no publisher ships a ready-made "65+ share by region." The exceptions that give it
**directly**: Eurostat `PC_Y65_MAX`, Korea KOSIS `DT_1YL20631`, Turkey TÜİK elderly stats, Japan e-Stat 3-group
table. Everyone else = download counts by 5-year age band × region and compute `Σ(65–69…85+) ÷ total`. Taiwan is
already done (MOI #77132, town-level). All countries below have a **genuine** gradient unless noted.

## Coverage table

| ISO2 | Admin-1 | Latest | Publisher / source | Machine-fetch | Key | Gradient |
|---|---|---|---|---|---|---|
| **EU** (DE FR IT ES PL +all) | NUTS-2 / NUTS-3 | 2024–25 | **Eurostat** `demo_r_pjanind3` (`PC_Y65_MAX`, share direct) / `demo_r_pjanaggr3` (counts) | ✅ JSON API | none | strong |
| GB | LAD (~360) | 2024 | ONS via **Nomis** `pestsyoala` (single-year age) | ✅ API/CSV | optional | strong |
| US | state + county | 2024 | **Census ACS 5-yr** `S0101_C02_030E` (% 65+ direct) | ✅ JSON API | free key (effectively required) | strong |
| CA | province (13) | 2025 | **StatCan** table `17-10-0005` (WDS) | ✅ CSV/JSON | none | strong |
| AU | state/SA4/SA2 | 2024 | **ABS** SDMX `ERP_ASGS2021` (host `data.api.abs.gov.au`) | ✅ SDMX | none | strong |
| NZ | region (16)/TA | 2025 | **Stats NZ** Aotearoa Data Explorer (SDMX) or release XLSX | ◐ API needs key; XLSX no key | key for API | strong |
| JP | prefecture (47) | 2024 | **e-Stat** `statsDataId=0003448225` (3-group age → 65+ direct) | ✅ JSON/CSV API | free appId (no nationality bar) | strong (Akita ~40% ↔ Okinawa ~23%) |
| KR | sido/sigungu | 2024–25 | **KOSIS** `DT_1YL20631` 고령인구비율 (share direct) | ◐ API key Korean-ID-gated | use EN portal CSV / SGIS | strong |
| BR | state (27 UF) | 2022 | **IBGE SIDRA** table `9514` (var `1000093` = % direct) | ✅ JSON API ×2 | none | strong (5–13%) |
| MX | entidad (32) | 2020 | **INEGI** census tabulado `pxq=Poblacion_Poblacion_01_…` / Indicadores API | ◐ XLSX no key; API needs free token | token for API | real |
| TR | province (81) | 2024 | **TÜİK** İstatistiklerle Yaşlılar 2024 / ADNKS portal | ◐ PDF/XLSX/portal export | none | very strong (3.7–20.8%) |
| CN | province (31) | 2020 (+annual) | **NBS** 分省年度数据 "65岁及以上人口比重" | ◐ portal XLSX; JSON API fragile (403 to bots) | none | strong |
| IN | state/district | 2011 | **Census** C-13/C-14 XLSX; MoSPI "Elderly in India 2021" | ◐ per-state XLSX (TLS cert quirk) | none | strong |
| IR | province (31) | 2016 | **SCI** Census Selected Results (Persian) | ✗ manual PDF/XLSX (TLS issues) | none | real |
| ID | province (34/38) | 2020 | **BPS** SP2020 tabular / WebAPI | ◐ API free key; XLSX fallback | free key | strong |
| TH | province (77) | 2024 | **DOPA** civil-registration by age (single-year) | ◐ per-year Excel, no API | none | strong |
| VN | province (63) | 2019 | **GSO** 2019 census dashboard/publication | ✗ XLSX/PDF, no API | none | moderate |
| PH | region + province | 2020 (2024 rolling) | **PSA OpenSTAT** PX-Web `0021A6DPAG0.px` | ✅ PX-Web API | none | moderate |
| MY | state (16) | 2025 | **DOSM** OpenDOSM `population_state` (parquet/CSV) | ✅ direct file | none (CC-BY) | moderate |
| BD | division/district | 2022 | **BBS** Census 2022 National Report | ✗ PDF only | none | narrow |
| PK | province/district | 2023 | **PBS** 7th Census `table_*.pdf` | ✗ PDF; Table 13 caps at "60+" → needs single-year | none | weak |

## Quick wins — clean API/CSV, do these first

1. **Eurostat — one call covers DE/FR/IT/ES/PL and all of Europe.** Share directly (NUTS-3):
   `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanind3?format=JSON&indic_de=PC_Y65_MAX&time=2024`
   (or counts at NUTS-2 **and** NUTS-3 via `demo_r_pjanaggr3?age=Y_GE65&age=TOTAL&sex=T&unit=NR&time=2025` → `Y_GE65/TOTAL`). Free, keyless, JSON-stat.
2. **US Census** — `https://api.census.gov/data/2024/acs/acs5/subject?get=NAME,S0101_C02_030E&for=county:*&in=state:*&key=KEY` (state + county; % 65+ direct). Get a free key.
3. **Canada StatCan** — `https://www150.statcan.gc.ca/t1/wds/rest/getFullTableDownloadCSV/17100005/en` → returns a CSV zip URL. No key.
4. **Brazil IBGE** — SIDRA table `9514` (Censo 2022), var `1000093` = % of total; `apisidra.ibge.gov.br` or `servicodados.ibge.gov.br/api/v3/agregados/9514`. No key.
5. **Australia ABS** — SDMX `https://data.api.abs.gov.au/rest/data/ABS,ERP_ASGS2021,1.0.0/…` (note new host). No key.
6. **Philippines PSA** — PX-Web `https://openstat.psa.gov.ph/PXWeb/api/v1/en/DB/DB__1A__PO/0021A6DPAG0.px` (POST query). No key.
7. **Malaysia DOSM** — direct file `https://storage.dosm.gov.my/population/population_state.parquet` (or `.csv`). CC-BY.
8. **Japan e-Stat** — `https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?appId=KEY&statsDataId=0003448225&lang=E` (prefecture × 3-group age → 65+ direct). Free appId, **no nationality restriction** (the most automation-friendly Asian source).

## Key-gated or export-only (second wave)
- **Mexico INEGI** — census XLSX tabulado needs no token; the Indicadores API needs a free token.
- **Indonesia BPS** — WebAPI needs a free key; `sensus.bps.go.id` XLSX is the no-key fallback.
- **New Zealand Stats NZ** — ADE SDMX needs a free subscription key (`Ocp-Apim-Subscription-Key`); each release page has a no-key XLSX.
- **Korea KOSIS** — `DT_1YL20631` gives the share directly, but the OpenAPI key registration requires Korean identity verification → for non-Koreans use the **English portal CSV/XLSX** or **SGIS**.
- **Turkey TÜİK** — no key, but no REST-JSON API either: use the verified PDF (`tuik.gov.tr/media/announcements/ist_yasli2024.pdf`) or the Nüfus İstatistikleri Portalı Excel export.
- **Thailand DOPA** — per-province/year Excel files (single-year age), scriptable by iterating URLs; no API.

## Manual / PDF (third wave, PDF extraction)
- **China NBS** — portal Excel export is the reliable path (the JSON endpoint 403s bots); Chinese UI.
- **India** — Census 2011 C-13/C-14 XLSX per state (2021 census still delayed); `censusindia.gov.in` has a TLS cert-chain quirk to scripted fetch (fine in a browser).
- **Vietnam GSO** — 2019 census XLSX/PDF; JS `.aspx` dashboard; IPUMS-International has harmonized microdata as an alternative.
- **Iran SCI** — 2016 census "Selected Results" (Persian; official site TLS-flaky). English mirror PDF: `irandataportal.syr.edu/wp-content/uploads/Iran_Census_2016_Selected_Results.pdf`.
- **Bangladesh BBS** — Census 2022 National Report Vol 1, PDF tables only.
- **Pakistan PBS** — 7th Census `…/census_tables/tables/table_*.pdf`; note the standard province age table (Table 13) tops out at **"60+"**, so a clean 65+ needs single-year-age tables from the National/Provincial reports (or the CRAN `PakPC2023` package).

## Recommended fetch order
**Wave 1 (keyless clean data):** Eurostat → CA → BR → AU → MY → PH.
**Wave 2 (free key):** US (Census key) → JP (e-Stat appId) → ID (BPS key).
**Wave 3 (export/portal):** TR → TH → KR (EN portal) → NZ (XLSX) → MX (census XLSX).
**Wave 4 (manual/PDF):** CN → IN → VN → IR → BD → PK.

## Caveats to disclose in the UI when Tier 2 lands
- Most values are **computed as Σ(65+ bands) ÷ total** from age-band tables — state the method + band edges per country.
- **Vintages differ** (IN 2011 · IR 2016 · VN 2019 · CN/MX 2020 · BD/JP 2022–24 · EU/US/CA/AU/NZ/TR 2024–25) — show the year per country.
- **Definition:** crude share of population aged 65+ (not age-standardised) — the standard ageing-society metric; keep the UN tiers (≥7 / ≥14 / ≥20%).
- Prefer the official admin-1 figure over the WorldPop/Tier-1 estimate; where neither adds a real gradient (small/uniform states), fall back to the national Tier-0 value and say so.
