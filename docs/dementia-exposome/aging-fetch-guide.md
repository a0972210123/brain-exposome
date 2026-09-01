# Aging layer — fetch guide (COMPLETE — historical)

> ✅ **2026-09-01 — all countries fetched.** tr (TÜİK ADNKS 2024, embedded), in (Census 2011 C-14), ir
> (SCI 2016 via UN OCHA/HDX) were the last three; all built and shipped. Kept as a record of how each source
> was obtained. Live per-source registry: [`scripts/aging-sources.json`](../../scripts/aging-sources.json).

Step-by-step for the 9 countries I can't fetch unattended. **Two kinds of action:** (A) get a free **API key**
and give it to me, or (B) **download a file** and drop it in `scripts/_data_in/<cc>/`, then tell me the filename —
I write the parser + the region→ISO code mapping and generate `public/data/aging/<cc>-admin1.json`.

General rule for downloads: whatever format the site gives (XLSX / CSV / PDF) is fine — save it under
`scripts/_data_in/<cc>/` and tell me the exact filename. Aim for a table of **region + (65+ count and total)**
or **region + 65+ %**. `scripts/_data_in/` is gitignored, so the raw files stay local.

> ⚠️ **`_data_in` is NOT protected by version control — 0 files tracked** (`.gitignore:32`). The raw inputs for
> the five `access: download` countries (**tw / kr / mx / nz / in**) exist as a *single local copy*; the owner
> keeps a Google Drive backup (confirmed 2026-09-01). The other countries are safe by construction: **cn** and
> **tr** have their figures embedded in the (version-controlled) build scripts, and **ir** re-fetches from a
> keyless URL each run — which is why `_data_in/cn`, `_data_in/ir` are empty and `_data_in/tr` holds only a
> superseded bulletin PDF. That is by design, not a missing-file bug; see the `access` field in
> [`scripts/aging-sources.json`](../../scripts/aging-sources.json) for the authoritative per-country answer.
> If a raw file is ever lost, every source URL is recorded there and can be re-downloaded.

---

## A. Free API keys (give me the key; ~2 min each)

### 🇺🇸 US — US Census Bureau
- **Get key:** https://api.census.gov/data/key_signup.html → enter name + email + organisation → key arrives by email instantly.
- **What I do with it:** fetch ACS 5-year subject table **`S0101_C02_030E`** (= "% 65 years and over") for every
  state **and county** in one call, map FIPS → `US-xx`. State + county gradient.
- **Hand-off:** paste me the key (it's a low-sensitivity public-data key), or put it in the repo env and I run the script.

### 🇯🇵 JP — Statistics Bureau e-Stat
- **Get appId:** https://www.e-stat.go.jp/en → register a free account (email) → log in → "API" → **issue an application ID**.
- **What I do:** fetch **statsDataId `0003448225`** (Population Estimates, prefecture × 3 age groups) → 65+ share
  per prefecture, map JIS code → `JP-xx`. 47 prefectures (Akita ~40% → Okinawa ~23%).
- **Hand-off:** give me the appId.

### 🇳🇿 NZ — Stats NZ (optional — or use the manual XLSX in §B)
- **Get key:** https://portal.apis.stats.govt.nz/ → register → subscribe to the **Aotearoa Data Explorer** API → copy the subscription key.
- **What I do:** fetch subnational population estimates by age × region → 65+ share per region (16 regions).
- **Simpler alternative (no key):** download the release XLSX — see §B.

---

## B. Manual downloads (drop the file in `scripts/_data_in/<cc>/`, tell me the filename)

### 🇰🇷 KR — KOSIS (Statistics Korea)
- **Site (English):** https://kosis.kr/eng
- **Find:** search table **`DT_1YL20631`** "고령인구비율 / Ratio of elderly population" (65+ share by 시도/시군구).
- **Download:** CSV or XLSX (65+ ratio by sido, latest year). *(The OpenAPI key needs a Korean ID, so use the portal download.)*
- **Save:** `scripts/_data_in/kr/`

### 🇹🇷 TR — TÜİK (TurkStat)  ⚠️ needs re-grab (next round)
- The elderly-stats **bulletin PDF** (`ist_yasli2024.pdf`) is INSUFFICIENT — national totals + charts only, no clean per-province 65+ table. Superseded.
- **Real province data — use one of:**
  - **Nüfus İstatistikleri Portalı** https://nip.tuik.gov.tr → "Population by age group and province" (ADNKS 2024) → export Excel (province × age group → 65+ / total).
  - **veriportali press page** https://veriportali.tuik.gov.tr/tr/press/53783 → the bulletin's İstatistiksel Tablolar (statistical-tables) Excel, which has the by-province table.
- Sources it cites: TÜİK ADNKS 2024; TÜİK Nüfus Projeksiyonları 2030–2100.
- **Get:** 65+ share by province (il), 81 provinces. **Save:** `scripts/_data_in/tr/`

### 🇨🇳 CN — ✅ DONE (2020 census fallback, no VPN)
- The live annual portal `data.stats.gov.cn` **geoblocks foreign IPs (403 UrlACL)** — needs a China ("回国") VPN.
- **Fallback used instead:** 2020 Seventh National Census 65+ % per province (verified vs each provincial bureau's
  第七次人口普查公报; national anchor 13.50%, range Tibet 5.67% → Liaoning 17.42%). Written by `build_aging_cn.mjs`
  → `public/data/aging/cn-admin1.json` (31/31 provinces). vintage 2020 (matches WorldPop).
- To refresh to the newer annual value (2023) later: use a 回国 VPN → `data.stats.gov.cn` 分省年度数据 → 人口 → 65岁及以上人口比重.

### 🇮🇳 IN — Census of India
- **Site:** https://censusindia.gov.in/census.website/data/census-tables → table **C-13** (single-year age) or **C-14** (5-year age group by sex), by state.
- **Download:** the state-level XLSX (Census 2011 — still the latest; 2021 delayed). Compute 65+ by summing 65+ bands.
- **Alt (60+, newer):** MoSPI "Elderly in India 2021" PDF: https://mospi.gov.in/sites/default/files/publication_reports/Elderly%20in%20India%202021.pdf
- **Save:** `scripts/_data_in/in/`

### 🇲🇽 MX — INEGI
- **Site (census tabulado, no key):** https://www.inegi.org.mx/app/tabulados/interactivos/?pxq=Poblacion_Poblacion_01_e60cd8cf-927f-4b94-823e-972457a12d4b — "Población por entidad federativa y grupo quinquenal de edad".
- **Download:** XLSX/CSV, by entidad × 5-year age group → sum 65+ / total. 32 states.
- **Save:** `scripts/_data_in/mx/`

### 🇮🇷 IR — Statistical Centre of Iran  *(hardest — 2016, PDF)*
- **Verified English PDF:** https://irandataportal.syr.edu/wp-content/uploads/Iran_Census_2016_Selected_Results.pdf (province × age tables).
- **Get:** 65+ share by province (ostan), 31 provinces, 2016. If you can transcribe the province age table into a small CSV that's easiest; otherwise save the PDF and I'll try to parse it.
- **Save:** `scripts/_data_in/ir/`

### 🇳🇿 NZ — (no-key alternative to §A)
- **Site:** https://www.stats.govt.nz/information-releases/subnational-population-estimates-at-30-june-2025/ → "Download data" XLSX (population by age × region).
- **Save:** `scripts/_data_in/nz/`

---

## C. Local file (Taiwan town-level upgrade)

### 🇹🇼 TW — MOI #77132
- **What:** 內政部戶政司 dataset **#77132** — single-year-age population by 村里/鄉鎮市區 (the file the dementia-prevalence
  pipeline already used; currently not on this machine).
- **Site:** data.gov.tw dataset 77132, or your local copy.
- **Save:** `scripts/_data_in/tw/` — then I compute 65+ / total per township → the finest-resolution aging layer.

---

## Priority suggestion
1. **US + JP keys** (biggest, easy) → I do them immediately.
2. **TR, MX, CN, KR** downloads (clean tables, good gradients).
3. **IN** (Census 2011 XLSX), **TW** (MOI file).
4. **IR** last (PDF, 2016).
