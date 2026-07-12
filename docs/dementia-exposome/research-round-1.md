# 🧠 Dementia-Exposome Calculator — Research Report (Round 1)

*Prepared July 2026 · Matt Ye / mattye.dev side project · Scope: feasibility scan + resource/API/dataset/reference inventory · Coverage: global, with Taiwan & Asia depth*

> **Reading note.** Numbers below are drawn from peer-reviewed sources and official data portals, but several were verified from search-index snippets because publisher sites blocked automated fetching. Anything to double-check against the primary source before it's hard-coded into a real tool is marked **⚠️verify**. Nothing here is medical or legal advice.

> **Status:** research only — no application code has been written. This document is internal working notes (lives under `docs/`, outside `src/`, so Astro does not build or deploy it).

---

## 0. TL;DR — is this worth building?

**Yes, as a free, client-side, educational brain-health tool — not as a business, and not as a medical device.** The specifics:

- **Real white space in framing, not in science.** Credible free risk tools already exist (ANU-ADRI, CogDrisk, McCance Brain Care Score, Alzheimer's Research UK "Check-in"). **None** packages the *life-course "exposome accumulation"* narrative — cumulative PM2.5 across the places you've lived + the Lancet risk factors → an intuitive "brain-age acceleration" readout. That framing + UX + the Taiwan/Asia focus is your genuine differentiator. The underlying epidemiology is well-trodden; you are **not** inventing science, you're productizing an academic concept (the "dementia exposome") that nobody has built for consumers yet.
- **The core is a perfect fit for your site.** A user-editable table of past residences/life-periods → an accumulated exposome score computed **entirely in the browser** is the exact pattern of your existing `diet-calculator.astro` ("nothing is uploaded or stored"). No backend needed for the MVP.
- **The safe regulatory lane is well-marked and copyable.** Stay *population-level, educational, non-diagnostic* (like Alzheimer's Research UK, which states outright it "isn't an assessment or diagnostic test"). The moment you output an *individualized personal risk probability*, you risk becoming a regulated medical device — that's exactly why **Five Lives had to CE-mark** its ML dementia-risk product. As a solo dev in Taiwan you do **not** want to be a device manufacturer.
- **Monetization is genuinely hard — treat it as a portfolio/credibility asset, not income.** Realistic path: keep it free, add donations + a light honest resource layer, and optionally pursue a nonprofit/academic partnership for credibility. Consumer-health monetization for solo builders rarely clears meaningful revenue.
- **Two features are harder than they look:** (1) *historical* PM2.5 going back decades has **no free live API** — you must pre-bake a satellite-derived annual grid into a static asset; (2) *wearables* (Apple Health, Google Health Connect) are **native-only and unreachable from a website** — manual entry is the pragmatic MVP path.

**Recommended MVP:** a free, bilingual, client-side "Brain-Health Exposome Check-in" grounded in the 2024 Lancet Commission — residence/life-period table + Lancet factors → a categorical risk profile and an educational "brain-age gap" estimate + protective suggestions and a Taiwan/Asia prevalence map. Everything in the browser, nothing uploaded, rigorous non-diagnostic disclaimer.

---

## 1. Your idea, de-messified

You captured a lot of overlapping thoughts (notes 14–20 + the app description). Here they are consolidated into one coherent product concept.

### The one-sentence concept
> A free, educational web tool that lets someone reconstruct their **life-course "exposome"** — where they've lived, the air they breathed, their chronic-disease / sensory / mental-health history — and see, in plain terms, **how those accumulated exposures relate to brain-health and dementia risk**, plus what's modifiable and where to get help.

### The mental model behind it (this is what your slides + notes describe)
`Lifelong exposome (air, chronic disease, sensory, mental health, social, lifestyle)` → `becomes biologically embedded via whole-body pathways (vascular, metabolic, immune, stress)` → `accelerates the "brain clock" (brain-age gap widens)` → `earlier crossing of the dementia threshold`. This is exactly the **"From Exposome to Brain Ageing"** slide (IMG_3736) and the **brain-clocks** literature (§2.3).

### Two input modes you sketched (keep both, phase them)
1. **Life-history table (the core, and the differentiator).** Rows = life periods / places lived, each with: location, years, local PM2.5 (auto-filled from data), and toggles/values for chronic disease, hearing/vision, mental health, education, smoking/alcohol/TBI, etc. → compute *cumulative* exposome.
2. **"Detect me now" (a lighter, viral hook).** GPS (or coarse IP fallback) → current local PM2.5/AQI → "here's your snapshot + nearby protective options."

### The factor taxonomy you referenced ("see Lancet commission")
Your notes map almost 1:1 onto the **2024 Lancet Commission's 14 modifiable factors** (§2.2), grouped the way you intuitively described them:

| Your wording | Maps to |
|---|---|
| "PM2.5 exposure across years" | Air pollution (exposome) — the anchor feature |
| "chronic disease exposure" | Hypertension, diabetes, obesity, physical inactivity, high LDL |
| "mental health issues" | Depression |
| "visual/hearing problems" | Vision loss, hearing loss |
| "demographics" | Age, sex, education (cognitive reserve) |
| "lived area / change route of living areas" | Residential history → PM2.5 + regional prevalence |

### Notes 14–20 decoded
- **14 ("Y cap / K cap, odds ratio, demographics, Lancet 14 factors")** → use demographics + the Lancet factors as model inputs; express output as relative risk / odds-ratio-style, not a diagnosis.
- **15–17 ("brain aged differently… brain age gap… brain clocks & compound exposome")** → the **brain-age-gap** concept (§2.3): accumulated exposome ages the brain faster; "brain clocks" quantify it. This is your headline output metaphor.
- **18–19 ("how to prevent / precision brain health / needs exposome science")** → the "what now" layer: personalized-feeling but population-level protective suggestions.
- **20 ("design an app… fixed vs dynamic factors, accumulation, GPS→PM2.5 API, wearables, recommend local protective places, map district/prevalence")** → the full feature wishlist; feasibility triaged in §4.

### The 5 slides you photographed (the scientific/framing anchors)
| Slide | What it gives your project |
|---|---|
| **Spider-Web Model of AD** (Novotni 2026, unpublished) | Visual metaphor: exposome feeds 7 biological pathways converging on "network resilience," modulated by genes (APOE, TREM2…). Good design inspiration for the results screen; ⚠️unpublished, cite carefully. |
| **"Defining brain health: a concept analysis"** (Chen et al.) | Your definition line: *"brain health is the lifelong capacity to think, feel and function, shaped by biological, psychological, social and environmental factors."* ⚠️slide says 2025; research found a 2022 paper w/ same authors (DOI 10.1002/gps.5564) — verify which. |
| **WHO Brain health determinants** | The 5-domain taxonomy (physical health · healthy environments · safety & security · learning & social connection · access to services) — a clean way to organize protective recommendations. |
| **Brain Health Exposome vs WHO Determinants** | The causal spine of your whole app (exposome → determinants → whole-body pathways → brain outcomes). |
| **EAN Brain Health Roadmap (2024)** | The "why now": shift from disease-centered to *holistic, lifelong prevention*. Your tool is exactly this ethos. ⚠️the "one brain, one life, one approach" tagline could not be verified in the primary paper. |

---

## 2. The science backbone (how inputs become a score)

### 2.1 Frameworks to cite
- **Exposome** (origin): Wild CP, 2005 — the totality of non-genetic, life-course environmental exposures. DOI 10.1158/1055-9965.EPI-05-0456.
- **WHO** *Optimizing brain health across the life course* (position paper, 2022, ISBN 9789240054561) — the 5-domain determinants model.
- **EAN Brain Health Roadmap**: Boon P et al., *Eur J Neurol* 2025, DOI 10.1111/ene.16589.
- **Brain-health concept analysis**: Chen Y et al., *Int J Geriatr Psychiatry* 2022, DOI 10.1002/gps.5564 (⚠️year vs. your 2025 slide).
- **Brain clocks / exposome & ageing**: Moguilner/Ibáñez et al., *Nat Med* 2024 (DOI 10.1038/s41591-024-03209-x); Ibáñez et al., *Nat Med* 2025 (DOI 10.1038/s41591-025-03808-2); *Nat Med* 2026 (DOI 10.1038/s41591-026-04302-z).

### 2.2 The 2024 Lancet Commission — 14 modifiable factors (the scoring model)

**Livingston G, et al. *The Lancet* 2024;404:572–628. DOI 10.1016/S0140-6736(24)01296-0.** Headline: **~45% of dementia is potentially preventable** by addressing 14 factors (up from 40% / 12 factors in 2020). Two new 2024 factors: **high LDL cholesterol** (PAF 7%) and **vision loss** (PAF 2%).

| # | Factor | Life-course period | Approx. RR ⚠️verify | Weighted PAF % | Group |
|---|--------|--------------------|------|----------------|-------|
| 1 | Less education | Early life | ~1.6 | 5% | Social/cognitive |
| 2 | Hearing loss | Midlife | ~1.9 | 7% | Sensory |
| 3 | High LDL cholesterol *(new)* | Midlife | ~1.08 per mmol/L | 7% | Cardiometabolic |
| 4 | Depression | Midlife | ~1.9 | 3% | Mental health |
| 5 | Traumatic brain injury | Midlife | ~1.8 | 3% | Lifestyle/injury |
| 6 | Physical inactivity | Midlife | ~1.4 | 2% | Cardiometabolic |
| 7 | Diabetes | Midlife | ~1.5 | 2% | Cardiometabolic |
| 8 | Smoking | Midlife | ~1.6 | 2% | Lifestyle |
| 9 | Hypertension | Midlife | ~1.6 | 2% | Cardiometabolic |
| 10 | Obesity | Midlife | ~1.6 | 1% | Cardiometabolic |
| 11 | Excessive alcohol | Midlife | ~1.2 | 1% | Lifestyle |
| 12 | Social isolation | Later life | ~1.6 | 5% | Social/cognitive |
| 13 | **Air pollution (PM2.5)** | Later life | ~1.1 | 3% | **Exposome** |
| 14 | Vision loss *(new)* | Later life | ~1.47 | 2% | Sensory |
|   | **TOTAL** |  |  | **≈45%** |  |

> **Critical modelling note:** the Commission's PAFs are **already overlap-adjusted** ("communality" weighting) because risk factors co-occur. **Do not naively add or multiply raw relative risks** — that double-counts. The PAF column (sums to exactly 45%) is high-confidence and multi-source corroborated; the RR column is approximate — confirm each against the primary 2024 table before hard-coding.

### 2.3 Brain age / brain-age gap (your headline output metaphor)
- **Brain-age gap (BrainAGE)** = predicted brain age − chronological age. Positive = accelerated ageing; larger gaps associate with dementia, decline, mortality. Origin: Franke et al., *NeuroImage* 2010.
- **Brain clocks** (Moguilner/Ibáñez, *Nat Med* 2024): deep-learning models on EEG/fMRI from 5,306 people across 15 countries show **air pollution + socioeconomic inequality + health disparities each widen the brain-age gap** — the flagship "exposome accelerates the brain clock" evidence. Follow-ups scale to 40 (2025) and 34 (2026) countries.
- **How to use it honestly:** convert the user's factor+PM2.5 profile into a *relative* score, and express it intuitively as an **"estimated brain-age acceleration" (years older than chronological)** — but label it clearly as an **educational analogue**, not an imaging-derived BrainAGE. A questionnaire cannot reproduce an MRI/EEG brain clock; say so.

### 2.4 PM2.5 → dementia dose-response (the anchor exposure)
- **Wilker et al., *BMJ* 2023;381:e071620** (DOI 10.1136/bmj-2022-071620): pooled **HR 1.04 (0.99–1.09) per 2 µg/m³** annual PM2.5; higher-quality subgroup **HR 1.42 (1.00–2.02) per 2 µg/m³**.
- **Lancet Planetary Health 2025** (DOI 10.1016/S2542-5196(25)00118-4): 21 studies, ~24M people, **HR 1.08 (1.02–1.14) per 5 µg/m³**.
- **Nature Aging 2025** (DOI 10.1038/s43587-025-00844-y): conservative "burden-of-proof" PM2.5→dementia function.
- **For the app:** an educational **~HR 1.15–1.25 per 10 µg/m³** (extrapolated, label it as such). Model cumulative exposure as **Σ(years-of-residence × local annual-mean PM2.5)** in µg/m³·years — scientifically appropriate, but note the evidence is strongest for *long-term average*, not literal lifetime-integrated dose. Standard regulatory reference: US EPA Integrated Science Assessment for Particulate Matter.

### 2.5 Validated risk models you can borrow algorithms from (all free, published)
| Model | Inputs | Output | Notes | Ref |
|---|---|---|---|---|
| **CogDrisk** | ~17 modern risk/protective factors | RR-weighted online report | Best discrimination in head-to-head (AUC ~0.76); closest to Lancet set | cogdrisk.com.au |
| **ANU-ADRI** | 11 risk + 4 protective, self-report | Weighted points | No clinical data needed; validated 3 cohorts | nceph.anu.edu.au |
| **LIBRA** | 12 modifiable factors | Weighted sum | "Lifestyle for brain health"; online calc (Evidencio #1041) | Vos 2017 |
| **CAIDE** | Age, sex, education, BP, BMI, cholesterol, activity | Points 0–15 → 20-yr risk | Midlife; simple | Kivipelto 2006 |
| **Brain Care Score** | 12 items (physical/lifestyle/social) | 21-point scale | UK Biobank n≈399k; +5 pts → ~27% lower composite risk | Singh 2023 |
| **UKBDRS** | 11 vars incl. family history | 14-yr risk | AUC 0.80; beat ANU-ADRI/CAIDE/DRS | Anatürk 2023 |

> **Sobering benchmark:** in a head-to-head (HUNT cohort), **no index beat "age + education" by much.** Lean on the tool's *behavior-change / awareness* value, not precise individual prediction.

---

## 3. Data sources, APIs & datasets (the resource inventory)

### 3.1 Air quality — CURRENT (for the GPS feature)
| API | Coverage | Free | Key? | lat/lon | Best for |
|---|---|---|---|---|---|
| **Open-Meteo Air Quality** | Global (CAMS) | Yes (non-commercial) | **No** | Yes | **Default** — no key, CORS-friendly, returns PM2.5 + `us_aqi`/`european_aqi` directly. ⚠️verify commercial threshold + `us_aqi` field name |
| **OpenAQ v3** | 134 countries, ~20.7k stations | Yes | Yes (`X-API-Key`) | Yes | Raw station measurements; has history (gov monitors since ~2015) |
| **WAQI / AQICN** | 11k+ stations, all Asia in one token | Yes (non-comm. only) | Yes (token) | Yes (`geo:`) | Widest Asian coverage; ⚠️license forbids resale/redistribution |
| **Google Air Quality** | 100+ countries, 500m | Paid (free cap) | Yes + billing | Yes | Highest resolution; only if you need 500m |
| **IQAir AirVisual** | Global city/station | Free tier (5/min, 500/day) | Yes | Yes (`nearest_city`) | Simple GPS nearest-city |
| **OpenWeatherMap Air Pollution** | Global (CAMS) | Free tier | Yes | Yes | Has history back to 27 Nov 2020 |

### 3.2 Air quality — HISTORICAL / multi-decade (for the accumulation feature)
**No free live API goes back decades.** Use satellite-derived annual grids, pre-baked into a static asset:
| Dataset | Resolution | Years | Access | The point |
|---|---|---|---|---|
| **ACAG / WashU global surface PM2.5** (van Donkelaar/Shen; V6.GL.02.04) | 0.01° (~1km) & 0.1° | **Annual, 1998–2023** | WUSTL Box / AWS S3 `v6.gl.02.04` / CloudFront | **The workhorse.** Index (lat,lon,year) → µg/m³ for any past residence globally |
| **NASA SEDAC** (same ACAG product, V5.GL.04) | 0.01° | 1998–2022 | Earthdata login (GeoTIFF/NetCDF) | Convenient repackaging |
| **Copernicus CAMS reanalysis (EAC4)** | ~0.75° | 2003–2024, 3-hourly | ADS API (`cdsapi`) | Physically-based cross-check; seasonal patterns |
| **TAP / CHAP (China)** | 1–10 km, daily | ~2000– | Register | China residences; ⚠️academic license |

- **Pre-1998 gap:** ACAG starts 1998 → earlier years need extrapolation (CAMS trends / national station trends). Document the assumption.
- **Open-Meteo caveat (verified):** only ~92 `past_days` — **not** usable for past-year reconstruction.

### 3.3 Taiwan air quality (detailed — regulator is now 環境部 / MOENV since Aug 2023)
- **環境資料開放平臺 `data.moenv.gov.tw`** (REST v2, free API key). Base: `https://data.moenv.gov.tw/api/v2/{DATASET_ID}?format=JSON&limit=1000&api_key={KEY}`
  - **`aqx_p_432`** — hourly AQI, all stations (real-time), *already includes lat/lon per station*.
  - **`aqx_p_488`** — historical AQI archive.
  - **`AQX_P_322`** — daily PM2.5 average.
  - **`AQX_P_07`** — station metadata (locations) for nearest-station matching.
- **`data.gov.tw` #40448** — AQI mirror (CSV/JSON/XML).
- **AirTW `airtw.moenv.gov.tw`** — bulk historical downloads (歷年監測資料).
- **History depth:** network built 1993–94; hourly archives ~1994+ for PM10/SO₂/NO₂/O₃/CO, but **automated PM2.5 only from ~mid-2000s–2010s** → for older Taiwan residences fall back to the ACAG grid or PM10→PM2.5 ratios. ⚠️confirm earliest PM2.5 year on AirTW.

### 3.4 Other Asia air quality
Japan **SORAMAME/AEROS** (bulk history, no clean official REST API ⚠️); South Korea **AirKorea** via `data.go.kr` (key); China **CNEMC** (no official public API — prefer gridded TAP/CHAP); India **CPCB** via `data.gov.in` (key). **WAQI** covers all of them in one `geo:` query (non-commercial license).

### 3.5 Dementia prevalence datasets
> ⚠️Two headline pairs circulate — **WHO/ADI 55M (2021)→139M (2050)** vs **GBD 57.4M (2019)→152.8M (2050)**. Never blend them; label whichever you use.

| Dataset | Granularity | Access | License |
|---|---|---|---|
| **GBD 2021 (IHME)** | 204 countries + some subnational, by age/sex 1990–2021 | GBD Results Tool / API / GHDx | Free non-commercial, attribution |
| **WHO Global Dementia Observatory** | Country-level, 35 indicators | Web portal | WHO open |
| **ADI World Alzheimer Reports** | Global/regional projections | PDF/web | Free, attribution |
| **Nichols et al. 2022, *Lancet Public Health*** | 204 countries, 2019 & 2050 | Open access + appendix tables | CC BY |

**Regional growth to 2050 (Nichols 2022):** N. Africa/Middle East **+367%**, E. Sub-Saharan Africa +357% vs High-income Asia Pacific **+53%**, Western Europe +74% — a strong story for an **Asia-focused** tool.

### 3.6 Taiwan & Asia prevalence (the map data)
**Taiwan — newest official survey (NHRI, 2020–2023, released 2024-03-21):** overall **65+ prevalence 7.99%** (women 9.36% > men 6.35%); Alzheimer's = 56.9% of cases.
| Age band | Prevalence % (2020–23) |
|---|---|
| 65–69 | 2.40 |
| 70–74 | 5.16 |
| 75–79 | 9.10 |
| 80–84 | 16.00 |
| 85–89 | 20.04 |
| 90+ | 29.45 |

**National counts:** ~320k (end-2023) → ~350k (2024) → >470k (2031) → ~680k (2041).
**Asia:** China 15.07M (60+, Jia 2020 ⚠️verify) · Japan 4.71M (2025)→5.84M (2040) · South Korea ~970k, 9.25% (2023).
**Sources:** 衛福部 press release `mohw.gov.tw/cp-16-78102-1.html`; NHRI `projects.nhri.edu.tw/spdc/`; TADA `tada2002.org.tw`; earlier TADA rates in Sun Y et al., *PLoS ONE* 2014 (PMC4062510).

> **Important for the map:** **No official sub-national (縣市/鄉鎮市區) prevalence is published in Taiwan.** The defensible method is **national age-band rates × local population age structure** → *modelled* district estimates (label clearly as estimates). NHIRD gives *diagnosed* prevalence (under-counts) — keep on a separate layer.

### 3.7 Admin boundaries / population / GIS (for choropleth)
- **Taiwan:** population by 鄉鎮市區/村里 from 內政部 (`ris.gov.tw`, `data.gov.tw/dataset/32973`, SEGIS); boundary Shapefiles from NLSC 國土測繪中心 (`data.gov.tw` #7442 county / #7441 district / #7438 village). License: **Open Government Data License TW v1.0** (CC-BY-compatible, commercial OK).
- **Global:** **geoBoundaries** (CC BY, commercial OK — best) or **Natural Earth** (public domain). Avoid **GADM** for anything public (non-commercial only).

### 3.8 Wearables (feature d) — the hard reality
| Platform | Web-accessible? | How | Notes |
|---|---|---|---|
| **Apple HealthKit** | ❌ No | — | Native iOS only; a web page cannot read it |
| **Google Fit REST** | ⚠️ Dying | — | No new signups since May 2024; EOL end-2026. Don't build on it |
| **Google Health Connect** | ❌ No | — | Android on-device only |
| **Fitbit Web API** | ✅ Yes | Cloud OAuth2 (PKCE) | Token exchange via a Cloudflare Worker |
| **Oura / Withings / Garmin / Polar** | ✅ Yes | Cloud OAuth2 | Withings covers BP/weight; Garmin needs program approval |
| **Web Bluetooth** | ⚠️ Partial | `navigator.bluetooth` | Reads BLE HR/glucose directly — **Chromium desktop/Android only, NOT Safari/iOS** |
| **LDL cholesterol** | — | Manual only | A lab value; no consumer feed |

**Verdict:** **manual numeric entry for the MVP** (HR, BP, fasting glucose/CGM avg, LDL). Add one cloud OAuth (Fitbit/Oura/Withings) via a Worker later; Web Bluetooth as a progressive-enhancement "read now" button that hides on Safari/iOS.

---

## 4. Technical feasibility on your static Astro / Cloudflare site

Your `diet-calculator.astro` (single file, inline vanilla `<script>`, "nothing uploaded") is the exact template. Cloudflare Pages gives you **Pages Functions/Workers** for free (100k req/day, 10ms CPU) — use them **only as a stateless proxy** (hide keys, CORS shim, free `request.cf` geolocation), **never to store health data**.

| Feature | Client-only? | Needs Worker? | Verdict |
|---|---|---|---|
| (a) Residence/risk table → accumulated score | ✅ | No | **Do it fully client-side** (diet-calculator pattern) |
| (a-hist) Multi-decade PM2.5 per residence | ✅ (from bundled static grid) | Build-time prep only | **Ship a pre-baked annual PM2.5 JSON** (shard by region, lazy-load) |
| (b) GPS → current PM2.5/AQI | ✅ mostly | Optional cache | Geolocation + Open-Meteo (no key, CORS) in-browser |
| (c) IP/DNS fallback location | ⚠️ partial | Recommended | Best via free `request.cf`; coarse, city-level, VPN-unreliable — say so |
| (d) Wearable vitals | ⚠️ partial | Yes (OAuth) | **Manual entry MVP**; OAuth later |
| (e) District choropleth | ✅ | No | **Leaflet or MapLibre + static GeoJSON**; mind OSM tile attribution (use OpenFreeMap) |

**Recommended MVP architecture:** one `/projects/dementia-exposome` `.astro` page; residence table + scoring engine + brain-age readout all in inline JS; historical PM2.5 from a static `public/data/pm25-annual.json`; "detect me now" via Geolocation → Open-Meteo; vitals via manual fields; map via Leaflet + static Taiwan district GeoJSON + modelled-prevalence JSON. **Build order:** (1) client-only table + scoring + static PM2.5 + map → ships as pure static; (2) add GPS + live AQI; (3) add `request.cf` fallback; (4) optional wearable OAuth.

---

## 5. Prior art & competitive landscape

**The tools to emulate (free, credible, educational lane):**
| Product | What | Maker |
|---|---|---|
| **Think Brain Health "Check-in"** | ~10-min habits questionnaire; *explicitly not diagnostic*; 340k+ users — **closest model to yours** | Alzheimer's Research UK |
| **CogDrisk** | 17-factor self-assessment + report | NeuRA / UNSW |
| **ANU-ADRI** | Risk index self-assessment | ANU |
| **McCance Brain Care Score** | 21-point "care" score | Mass General |

**Commercial (mostly B2B or brain-training, not your model):** Five Lives (DTC, **CE-marked device** — the cautionary example), CogniFit (paid training), Linus Health / Neurotrack / BrainCheck (B2B clinical).

**Exposome angle:** an **active research concept** (Gateway Exposome Coordinating Center; low-cost exposome ML dementia model on medRxiv; Nature Communications social-exposome-and-dementia in Latin America) but **not productized for consumers**. Personal air-pollution exposure is served only by generic AQI apps (AirNow, IQAir).

**Answer to "is anyone doing this exact thing?" → No.** Nobody packages *life-course exposome accumulation → brain-health risk → protective recommendations* under an exposome banner. Your novelty is **framing + UX + Taiwan/Asia focus**, on top of well-established scoring.

---

## 6. Monetization (honest)

Consumer-health monetization is brutal for solo builders (free→paid conversion ~2–5%, health underperforms; ~5% of health apps reach even $10k in 2 years ⚠️directional stats).

| Model | Fit for indie | Upside | Note |
|---|---|---|---|
| Free + donations (BMC / GitHub Sponsors) | High | Very low | Frictionless, non-compromising — **do this** |
| Honest affiliate (hearing checks, air purifiers, books) | Medium | Low | Contextual only; disclose; reputational risk with supplements |
| Freemium (paid detailed PDF) | Medium | Low–modest | A "personal report" risks drifting toward individualized/device territory — keep educational |
| Grant / nonprofit / academic partnership | Med–High | Low cash, **high credibility** | **Best non-revenue upside** — aligns with free+educational |
| B2B2C (insurers/employers) | Low (needs a company) | High *if* it lands | Where the real money is, but not an indie path |
| Display ads / subscription / clinic lead-gen | Low | Low | Erode trust or raise regulatory risk — avoid early |

**Recommendation:** free + client-side; donations + a light honest resource layer; pursue a partnership for credibility. Treat it as a **portfolio + public-good asset**; any revenue is a bonus.

---

## 7. Regulatory & privacy (the part that decides if it's safe to ship)

**The line:** a risk calculator becomes a **regulated medical device (SaMD)** when it **diagnoses/predicts/drives treatment for an individual**. It stays **general-wellness/educational** when it's **population-level, informational, non-diagnostic**. All three relevant regimes agree on this principle:
- **US FDA** General Wellness policy (revised Jan 2026) — explicitly allows claims relating healthy lifestyle to *reducing the risk of chronic disease* where "well understood and accepted." A Lancet-Commission-based tool fits.
- **EU MDR / MDCG 2019-11 (Rev.1, 2025)** — individualized disease *prediction/prognosis* → Medical Device Software (Rule 11). **Five Lives CE-marked** for exactly this.
- **Taiwan TFDA** 醫用軟體分類分級參考指引 — non-diagnostic, no medical claim → outside 醫療器材.

**DO:** frame as educational/wellness; report *which* factors matter and roughly how much *in populations* (cite Lancet); give general protective tips; keep output **categorical/qualitative** ("several modifiable factors present"), not a personal %; repeatedly point to a clinician; cite sources.
**DON'T:** diagnose/predict an individual's dementia; give individualized medical advice; output a personal risk probability presented as *their* outcome (the device trigger); imply it replaces professional evaluation; target symptomatic users.

**Privacy — the architecture dissolves most of it:** health answers are **GDPR Art. 9 special-category** / **Taiwan PDPA Art. 6 特種個資**. **Compute everything client-side and upload nothing** → you're not "collecting/processing" in the regulated sense. Two site-specific cautions: (1) your **GA4** must **never** receive health answers/results — page-level metrics only; (2) any "email me my report"/payments/server PDF re-enters data-controller territory — keep the free tool fully client-side.

**A disclaimer bundle (bilingual, shown before results) should assert:** educational only / not a medical device / not diagnostic; population-level not personal prediction; not medical advice, see a professional; estimates uncertain; **processed entirely in your browser, nothing uploaded.** ⚠️Have a Taiwan-qualified lawyer review before public launch.

---

## 8. Feasibility verdict & recommendation

**Build it — scoped as a free, client-side, educational "Brain-Health Exposome Check-in."** It's technically a great fit for your site, scientifically groundable (2024 Lancet Commission + brain-clock framing), legally safe if kept non-diagnostic, and genuinely novel in framing. Don't count on revenue; count on it as a strong portfolio/public-good piece with a credible partnership as the upside.

**Suggested MVP scope (round-1 build, if you proceed):**
1. Residence/life-period table → cumulative PM2.5 (from a pre-baked ACAG grid) + Lancet-factor toggles.
2. A categorical brain-health profile + an educational **"brain-age gap"** readout (clearly labelled non-clinical).
3. Protective suggestions organized by the **WHO 5 determinants**.
4. A **Taiwan district prevalence map** (modelled from national age-rates × local population).
5. "Detect me now" GPS → live AQI hook.
6. Rigorous bilingual non-diagnostic disclaimer; everything client-side.

**Defer:** wearable integrations, IP fallback, multi-country maps, any paid/report features.

---

## 9. Open questions / what to resolve before building

**⚠️ Verify-before-shipping (from the research flags):**
- Exact per-factor **relative risks** in the 2024 Lancet primary table (PAFs are solid; RRs approximate).
- **PM2.5 per-10 µg/m³** hazard — use published increments (per-2 Wilker, per-5 Lancet Planetary Health), not the older ~1.40 figure.
- **Chen et al.** year (2022 vs your 2025 slide) and the **EAN "one brain, one life, one approach"** tagline.
- **ACAG** grid resolution (0.01° vs 0.1°) and license/attribution before bundling; earliest **Taiwan PM2.5** year on AirTW.
- **Open-Meteo** commercial threshold + `us_aqi` field name; **Web Bluetooth** support %; **China 15.07M** figure.

**Product decisions for you:**
- Output style: categorical profile only, or the "brain-age acceleration" number? (Affects regulatory framing.)
- Geographic scope of v1: Taiwan-only map, or global from the start?
- How ambitious is v1: lean informational check-in, or the full life-history + map + GPS build?

---

## 10. Next research rounds (pick to steer round 2)

- **A. Scoring-engine deep dive** — turn the Lancet PAFs + validated-model weights into a concrete, defensible client-side algorithm (inputs → score → brain-age-gap readout), with the exact numbers verified against primary tables.
- **B. Data-pipeline prototype spec** — exactly how to fetch, downsample and pre-bake the ACAG PM2.5 grid + Taiwan district GeoJSON + modelled prevalence into static assets, with sizes and a build script design.
- **C. UX / product design** — wireframe the life-history table, results screen (Spider-Web-inspired), and map; define the bilingual copy and the disclaimer.
- **D. Regulatory/partnership** — draft the disclaimer for a Taiwan lawyer, and shortlist nonprofit/academic partners (TADA, Gateway Exposome, GBHI).
- **E. Go straight to a build MVP** — if you've seen enough, greenlight the scoped MVP in §8.

---

## Consolidated references
1. Livingston G, et al. 2024 Lancet Commission. *Lancet* 2024;404:572–628. DOI 10.1016/S0140-6736(24)01296-0
2. Livingston G, et al. 2020 Commission. *Lancet* 2020;396:413–446. DOI 10.1016/S0140-6736(20)30367-6
3. Wild CP. Exposome. *Cancer Epidemiol Biomarkers Prev* 2005;14:1847–50. DOI 10.1158/1055-9965.EPI-05-0456
4. WHO. Optimizing brain health across the life course, 2022. ISBN 9789240054561
5. Boon P, et al. EAN Brain Health Roadmap. *Eur J Neurol* 2025. DOI 10.1111/ene.16589
6. Chen Y, et al. Defining brain health: a concept analysis. *Int J Geriatr Psychiatry* 2022;37(1). DOI 10.1002/gps.5564
7. Moguilner S, Ibáñez A, et al. Brain clocks. *Nat Med* 2024;30:3646–57. DOI 10.1038/s41591-024-03209-x
8. Ibáñez A, et al. Exposome of ageing across 40 countries. *Nat Med* 2025;31:3089–3100. DOI 10.1038/s41591-025-03808-2
9. Exposome of brain aging across 34 countries. *Nat Med* 2026. DOI 10.1038/s41591-026-04302-z
10. Franke K, et al. BrainAGE. *NeuroImage* 2010;50:883–892. DOI 10.1016/j.neuroimage.2010.01.005
11. Wilker EH, et al. Air pollution & clinical dementia. *BMJ* 2023;381:e071620. DOI 10.1136/bmj-2022-071620
12. Long-term air pollution & incident dementia. *Lancet Planet Health* 2025. DOI 10.1016/S2542-5196(25)00118-4
13. Burden-of-proof PM2.5 & dementia. *Nature Aging* 2025. DOI 10.1038/s43587-025-00844-y
14. Kivipelto M, et al. CAIDE. *Lancet Neurol* 2006;5:735–741. DOI 10.1016/S1474-4422(06)70537-3
15. Vos SJB, et al. LIBRA. *J Alzheimers Dis* 2017;58:537–547. DOI 10.3233/JAD-161208
16. Walters K, et al. Dementia Risk Score. *BMC Medicine* 2016;14:6. DOI 10.1186/s12916-016-0549-y
17. Anatürk M, et al. UKBDRS, 2023. PMC10577770
18. Singh S, et al. Brain Care Score. *Front Neurol* 2023;14:1291020. DOI 10.3389/fneur.2023.1291020
19. Nichols E, et al. GBD dementia forecast. *Lancet Public Health* 2022. DOI 10.1016/S2468-2667(21)00249-8
20. Sun Y, et al. Taiwan MCI/dementia survey. *PLoS ONE* 2014;9(6):e100303. PMC4062510
21. Jia L, et al. China dementia. *Lancet Public Health* 2020;5:e661–71. DOI 10.1016/S2468-2667(20)30185-7
22. van Donkelaar/Shen et al. ACAG surface PM2.5 (V6.GL.02.04). sites.wustl.edu/acag/datasets/surface-pm2-5/

**Data portals:** Open-Meteo Air Quality · OpenAQ v3 · WAQI/AQICN · Taiwan MOENV `data.moenv.gov.tw` (aqx_p_432/488, AQX_P_07/322) · AirTW · GBD Results Tool (IHME) · WHO GDO · ADI · NLSC boundaries (`data.gov.tw` #7441/7442/7438) · geoBoundaries · Leaflet / MapLibre / OpenFreeMap · Cloudflare Pages Functions.

*Regulatory/privacy sources: FDA General Wellness (rev. Jan 2026); EU MDCG 2019-11 Rev.1; Taiwan 醫療器材分類分級管理辦法 + TFDA 醫用軟體指引; GDPR Art. 9; Taiwan PDPA Art. 6.*
