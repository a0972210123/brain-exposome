# 資料更新流程（Data-Refresh Workflow）— dementia-exposome map

> 目的：把「**驗證最新版 → 抓取 → 清理 → 填入 → 揭露**」的完整流程釐清並固化，
> 作為日後用 **GitHub Actions 定期自動更新**的依據。每一層都標註**各國特異性、
> 資料源特異性、以及自動化的可行性/困難度**。
> 建立：2026-07-16（葉淨維 / Claude）。所有數值皆為 modelled / latest-available estimate，非醫療診斷。

---

## 0. TL;DR — 自動化分級結論

| 分級 | 意義 | 資料源 | 建議 Action 行為 |
|---|---|---|---|
| **A（全自動）** | 公開 API、無金鑰、GitHub runner 可直連 | World Bank 65+、WHO GHO（吸菸/身體活動不足） | 排程重抓 → rebuild → 若有 diff **自動開 PR**（人工 review 後 merge） |
| **B（自動偵測、人工抓取）** | URL 穩定但需下載大檔／或有版本字串 | NCD-RisC（3 檔）、ACAG PM2.5、GBD 版次 | Action 偵測「有新版」→ **開 issue 提醒**，不自動改資料 |
| **C（純人工）** | 授權點擊、超大 raster、CJK PDF、被 IP 封鎖的政府入口 | IHME GBD 匯出、WorldPop rasters、台灣 NHIS/內政部 PDF | 手動 runbook（見 §6）；Action 不碰 |

**核心原則**：Action **永不 auto-merge**（沿用 CLAUDE.md：owner 說「可以 merge」才 merge）；
**只 commit 衍生資產**，raw 一律留在 gitignored `scripts/_data_in/`；每次更新都保留「modelled estimate」與各國分母註記。

---

## 1. 地圖的資料層與來源清單

| 層 | 指標 | 資料源 | 資料集 / 指標代碼 | 目前版次（2026-07） | 分母 / 定義 | 解析度 | 自動化 |
|---|---|---|---|---|---|---|---|
| 高齡化 | 65+ 人口占比 % | **World Bank** | `SP.POP.65UP.TO.ZS` | **2025** | 占總人口 % | 國家（台灣：內政部） | **A** |
| 失智盛行率 | 失智 % 60+ | **IHME GBD 2023** | Prevalence · 60+ years · Percent | 2023（最新 round） | 60+ 族群內 % | 國家＋部分次國家 | **C** |
| 空汙 | PM2.5 µg/m³ | **ACAG（WUSTL）** | SatPM2.5 `V6.GL.03` | 年均至 2024 | 年均濃度 | 國家＋admin-1 zonal | **B** |
| 高血壓 | 高血壓盛行率 % | **NCD-RisC** | Lancet 2017 BP age-std countries | **資料 2015**（最新可下載版） | 成人、年齡標準化、**實測** | 國家 | **B** |
| 糖尿病 | 糖尿病 % 18+ | **NCD-RisC** | Lancet 2024 Diabetes age-std | **資料 2022** | 成人 18+、年齡標準化、實測 | 國家 | **B** |
| 肥胖 | BMI≥30 % | **NCD-RisC** | Nature 2026 BMI age-std | **資料 2024** | 成人、年齡標準化、實測 | 國家 | **B** |
| 吸菸 | 目前吸菸率 % | **WHO GHO** | `M_Est_tob_curr` | 最新觀測年（過濾 2030 推估） | 年齡標準化 | 國家（台灣：NHIS 2021） | **A** |
| 身體活動不足 | 不足比例 % | **WHO GHO** | `NCD_PAC` | 2022 | 年齡標準化 | 國家（台灣：NHIS 2021） | **A** |
| 綜合 PAF | 可歸因 % | **推導**（Livingston 2024 RRs） | — | — | 5 因子下限估計 | 國家 | 隨上游 |
| MCI / SCD | 盛行率 % | **（規劃中）** | 各國別來源 | — | 依來源 | 目前僅 TW/JP/KR | **C** |

> 2026-07-16 已核對：World Bank 65+ 釋出到 **2025**；NCD-RisC 三檔皆為官網**目前最新可下載版**
> （BP 2017/資料2015、DM 2024/資料2022、BMI 2026/資料2024，各 200 國）；GBD 2023 為最新 round。

---

## 2. 四階段管線（generic）

```
① 驗證最新版 (verify-latest)   ── 每個源怎麼判斷「有沒有更新」→ 記在 manifest
        │
② 抓取 (fetch/scrape)          ── REST API / 靜態 CSV / raster / 手動匯出 / PDF
        │
③ 清理正規化 (clean/normalize) ── 國名→ISO、both-sexes=mean(M,F)、選年齡層/年份、
        │                          單位換算、過濾推估年、most-recent-non-null、加表頭
        │
④ 建置/烘焙/推導 (build/bake)   ── scripts/build_data.py → JSON 資產 + geojson 烘焙 +
                                   scripts/gen_provenance.py 揭露表；**只 commit 衍生檔**
```

管線程式：`scripts/build_data.py`（各 `build_*` / `_load_*` 函式）與 `scripts/gen_provenance.py`。
raw 輸入放 gitignored `scripts/_data_in/`；`manifest.json` 由 build 產生（存在性守衛）。

---

## 3. 各資料源逐一拆解（verify-latest 配方 · 抓取 · 清理雷點 · 可自動化）

### 3.1 World Bank 65+（高齡化）—— 分級 A（全自動）
- **verify-latest**：`GET https://api.worldbank.org/v2/country/all/indicator/SP.POP.65UP.TO.ZS?format=json&date=2020:<今年>&per_page=20000`；
  取每國 **most-recent-non-null**。回傳 JSON 第一段的 `lastupdated` 可判斷是否有新釋出。
- **抓取**：同上一支 API（無金鑰）。**另外**需國家清單 `GET /v2/country?format=json&per_page=400` 以：
  (a) 用 `region.id != "NA"` 濾掉「聚合區」（World、income groups…），(b) 取 iso2。
- **清理雷點**：
  - 寫 `scripts/_data_in/world-65plus.csv` **必須含表頭 `iso2,pct,year,name`**（`_read_csv` 是 `DictReader`；
    無表頭會把第一列當表頭 → `_load_pop65` 靜默 fallback 到 46 筆種子 → US/CN 反而變小，**曾踩過**）。
  - `mrnev=1` 參數會回 **HTTP 400**；改用 `date=<起>:<迄>` 自己挑最新非空。
- **各國特異性**：**台灣不在 World Bank** → 由 `SEED_POP65["TW"]` 覆蓋（現為內政部戶政司 2025 年底 20.06%）。
- **自動化**：★★★ 完全可行。GitHub runner 直連無礙。cadence 建議季度。

### 3.2 WHO GHO 吸菸 / 身體活動不足 —— 分級 A（全自動）
- **verify-latest**：OData `https://ghoapi.azureedge.net/api/<INDICATOR>`；吸菸 `M_Est_tob_curr`、
  身體活動不足 `NCD_PAC`。回傳含多年份，取**最新觀測年**。
- **清理雷點**：`M_Est_tob_curr` 含 **2030 推估**列 → 必須過濾到 `TimeDim ≤ 今年`；both-sexes 取 `Dim1=BTSX`
  或 mean(M,F)；國名→ISO3。
- **各國特異性**：**WHO GHO 無台灣** → 台灣吸菸/身體活動不足採 **2021 NHIS**（吸菸 15.8%、活動不足 54.0%），
  存 `scripts/_data_in/tw-riskfactors.json`（此檔為手動整理，見 §3.7）。
- **自動化**：★★★ 完全可行（keyless OData）。

### 3.3 NCD-RisC 高血壓 / 糖尿病 / 肥胖 —— 分級 B（自動偵測、人工抓取）
- **目前最新版（2026-07-16 核對官網下載頁）**：
  - 高血壓：`downloads/bp/NCD_RisC_Lancet_2017_BP_age_standardised_countries.csv`（Lancet 2017，**資料至 2015**，仍是官網最新可下載的「raised BP prevalence」版）。欄位含 `Prevalence of raised blood pressure`。
  - 糖尿病：`downloads/dm-2024/NCD_RisC_Lancet_2024_Diabetes_age_standardised_countries.csv`（Lancet 2024，資料至 2022）。
  - 肥胖：`downloads/bmi-2026/adult/NCD_RisC_Nature_2026_BMI_age_standardised_country.csv`（Nature 2026，資料至 2024，DOI 10.1038/s41586-026-10383-0）。
- **verify-latest**：抓 3 個下載頁（`data-downloads-blood-pressure.html` / `-diabetes.html` / `-adiposity.html`），
  比對頁面上的**發表字串 / 檔名**；檔名一變（例：出現 `_2028_` 或新 `bmi-2028/`）即代表有新版。
- **清理雷點**：
  - both-sexes = **mean(Men, Women)**（檔案分性別列）。
  - **國名別名**：`Turkey`（BP 檔）vs `Turkiye`（DM/BMI 檔）、`Republic of Korea`、`Viet Nam`、
    `Iran (Islamic Republic of)`、`United States of America`、`Russian Federation`… → 需集中 alias map。
  - 取「age-standardised」而非各年齡層；取最新年份列。
- **各國特異性**：台灣**是原生列**（NCD-RisC 有台灣），不需特例；但注意台灣的 HTN/DM/肥胖採 NCD-RisC
  值（而非 NHIS 的 65+/BMI≥27），以與各國可比。
- **自動化**：★★☆ 半自動。URL 穩定、新版罕見（數年一次），可寫偵測；但因授權宜人工確認後再更新。
  **授權**：NCD-RisC 資料供學術/非商業使用並註明出處。

### 3.4 IHME GBD（失智盛行率）—— 分級 C（純人工）
- **現況**：owner 手動從 GBD Results Tool 匯出 `scripts/_data_in/GBD/*.csv`（794 locations，含次國家）。
- **verify-latest**：GBD 每 1–3 年出新 round（GBD 2021 → **2023**）。只能人工留意 IHME 公告。
- **為何不能自動**：需登入帳號 + 點擊接受**非商業授權**；查詢結果非穩定 REST。**Action 只能偵測「有新 round」→ 開 issue**。
- **清理**：`load_gbd_prev60()` 取 `measure=Prevalence, metric=Percent, age="60+ years"`。**非商業授權 → 只發布衍生的 per-admin 值，永不 commit raw CSV。**

### 3.5 ACAG PM2.5 —— 分級 B
- 版本字串 `V6.GL.03`（年均至 2024）。verify-latest = 看 ACAG 網站有無新版本/新年份。
- 抓取為 raster / zonal，檔案大；annual cadence。可腳本化但偏重 → 半自動、季度以上。

### 3.6 WorldPop（admin-1 人口分母）—— 分級 C
- 1km age/sex rasters（CC BY 4.0），僅用於部分國家 admin-1 分母。**靜態 2020 產品**、檔案巨大 →
  不進定期自動；且部分高所得國套用**全國一致年齡面** → admin-1「% 60+」是平的，需 `build_pop_rate_prev60`
  以**量測散度自動判定** national vs subnational（`max-min < 0.15pp` 收斂為全國值）。

### 3.7 台灣專屬來源 —— 混合
- **內政部戶政司**：65+ 占比（宣告超高齡的官方基礎）；月度登記人口；`data.gov.tw` #77132 單一年齡鄉鎮人口（可 API）。
- **NHIS 國民健康訪問調查**：吸菸/身體活動不足等 → **PDF 且 CJK 為亂碼**（字型 CMap 壞，pypdf/fitz 都garble，
  只有數字可讀）→ 以 `fitz` 定位表格 numeric id、`get_pixmap(200dpi)` 轉圖後**人工/視覺讀取**。純人工。
- **HPA / 體育署**：縣市級危險因子（obesity 有縣市缺口）。

---

## 4. 各國特異性（cross-cutting）
1. **台灣**幾乎每一層都要特例：不在 World Bank、不在 WHO GHO、GBD 次國家常缺 → 需國家別 override。
2. **國名別名**：集中一份 alias（Turkey/Türkiye/Turkiye、Korea Rep./Republic of Korea、Czechia/Czech Republic、
   Viet Nam、Iran、USA、Russia…）；各源命名不一，**同一國在不同檔可能不同拼法**（NCD-RisC BP vs DM 就不同）。
3. **實測 vs 自報**：NCD-RisC = 實測且年齡標準化；許多國家次國家源為自報 → **不同尺度、不可跨源比色**。
4. **分母不一致**：失智盛行率各國分母不同（CN 50+、IN 60+、TW 65+、GBD 60+）→ **各國自帶圖例、不可跨國比色**。
5. **PAF 用成人（非 65+）盛行率**：符合 Livingston 2024 本身的方法；65+ 值會與模型分歧，勿用。
6. **WorldPop 平面年齡面**：部分高所得國 admin-1 收斂為全國值（見 §3.6）。

---

## 5. 自動化：建議的 GitHub Action 設計

### 5.1 新增一支 `scripts/verify_sources.py`（自動化前置）
- 讀一份 `scripts/source-manifest.json`（記錄每源目前版次/檔名/URL/最後檢查日）。
- 對每源跑 verify-latest（§3）：**Tier A** 比對 API `lastupdated`/最新年；**Tier B** 比對下載頁檔名字串；
  **Tier C** 略過（僅列人工待辦）。
- 輸出：`updated=[...]`（有新版的源）。

### 5.2 `.github/workflows/data-refresh.yml`（草案）
```yaml
on:
  schedule: [{ cron: "0 3 1 */3 *" }]   # 每季 1 號
  workflow_dispatch: {}
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r scripts/requirements.txt
      - run: python scripts/verify_sources.py --emit changed.json
      # Tier A：有變更 → 重抓+rebuild+開 PR
      - run: python scripts/build_data.py --only worldbank,who_gho   # 需支援 --only
        if: contains(changed, 'A')
      - name: Open PR (Tier A)
        uses: peter-evans/create-pull-request@v6   # 產生 PR，不 auto-merge
      # Tier B/C：只開 issue 提醒
      - name: Notify (Tier B/C new-version)
        uses: actions/github-script@v7
```
- **關鍵限制與風險**：
  - **絕不 auto-merge**（沿用 owner-review 規則）。
  - **runner IP**：GitHub runners 一般不像某些 VPN 被政府入口封鎖，但 **每個 Tier-A/B 源都要先在 runner 上實測可達**
    （曾遇 WorldPop/GitHub 對特定 IP 封鎖）。
  - **schema drift**：欄位改名會讓清理靜默失效 → build 內加 **欄位存在性驗證**、`assert` 國家數/數值範圍。
  - **授權**：GBD 非商業 → 永不自動重發佈 raw；NCD-RisC 註明出處。
  - **determinism**：most-recent-non-null 可能讓某國年份跨序跳動 → 可接受（就是「最新」），但 PR 說明要列出「哪些國家年份變了」。
  - **Windows/Linux**：runner 是 Linux（無 cp950 問題）；本機 Windows 跑務必 `PYTHONUTF8=1`。

### 5.3 可自動化程度總結
- **可全自動並自動開 PR**：World Bank 65+、WHO GHO 吸菸/活動不足（→ 綜合 PAF 亦隨之重算）。
- **可自動偵測、需人工抓取/確認**：NCD-RisC 3 檔、ACAG PM2.5、GBD 新 round。
- **維持人工**：GBD 匯出、WorldPop rasters、台灣 NHIS PDF、任何被封鎖入口。

---

## 6. 手動 refresh runbook（自動化前的暫用流程）
1. `git fetch && git checkout -b claude/data-refresh-YYYYMM origin/main`（**本機 clone 常落後，先 fetch**）。
2. `PYTHONUTF8=1 python scripts/verify_sources.py`（或手動對 §3 各源核對最新版）。
3. Tier A：重抓 World Bank + WHO GHO → 更新 `_data_in/*.csv`（**記得表頭**）。
4. Tier B：若 NCD-RisC/ACAG/GBD 有新版，下載到 `_data_in/`（raw、gitignored）。
5. `PYTHONUTF8=1 python scripts/build_data.py`（產生 JSON + geojson 烘焙）。
6. `PYTHONUTF8=1 python scripts/gen_provenance.py`（更新揭露表 + 版次年份）。
7. `npm run build` → 本機 preview 抽查幾國各層 + 方法框 + 參考文獻。
8. **只 stage 衍生檔**（顯式路徑，勿 `git add -A`；`.claude/`、`_data_in/` 皆 gitignored）→ commit → push → 開 PR（不自 merge）。
9. PR 說明列出：更新了哪些源/年份、哪些國家數值變動、驗證結果。

---

## 7. 工程雷點（延續，務必內建進 Action）
- **cp950/UTF-8**：所有 `open()` 加 `encoding="utf-8"`；本機跑 `PYTHONUTF8=1`。
- **CSV 表頭**：`DictReader` 需表頭（`iso2,pct,...`）；缺表頭會靜默 fallback。
- **gitignored raw**：`_data_in/` 的 GBD/rasters/PDF 永不 commit；只 commit 衍生。
- **stacked-PR / 落後 clone**：merge 後用 `git show origin/main:<file>` 確認內容確實進 main。
- **Astro scoped CSS 套不到 innerHTML**：方法框用 `.parent :global(.child)`。
- **manifest**：`build_data` main() 產生（存在性守衛）；部分跑要把新資產列鏡射進已 commit 的 json。

---

## 相關文件
- 來源盤點：[`all-country-source-audit.md`](./all-country-source-audit.md)、[`data-download-points.md`](./data-download-points.md)
- 27 國 exposome 次國家可得性：`scripts/_data_in/exposome-subnational/00-INDEX.md`（gitignored）
- 揭露表產生器：`scripts/gen_provenance.py` → `public/data/data-provenance.json`
- 遷移計畫：[`repo-migration-plan.md`](./repo-migration-plan.md)
