# SEO / AEO 結構化資料規劃 — brain-exposome

> 規劃文件（2026-09-01）。**尚未改任何程式碼**，供之後 `/refresh` 時逐項落地。
> 目標：把本站已有的公共衛生資料，變成搜尋引擎與**答案引擎（AEO：ChatGPT / Perplexity / Google AI Overviews）**能抓、能引用、能標註出處的形式。

## 0. 一句話結論

本站是「資料密集 + 出處完整」的公衛工具 —— 這正是 AEO 最愛引用的素材。**唯一問題：數字現在只活在 SVG/Leaflet 地圖與 JS 注入的表格裡，爬蟲與 LLM 看不到。** 解法＝把同一批數字，額外輸出成（a）語意化 HTML `<table>` 與（b）`schema.org` **Dataset** JSON-LD。基礎建設（canonical、OG、sitemap、Person/WebSite JSON-LD）都已就緒，只缺這兩層。

## 1. 現況盤點（已查證）

| 已有 ✅ | 缺口 ❌ |
|---|---|
| `BaseLayout.astro`：JSON-LD `@graph`（Person 葉淨維 + WebSite） | 沒有 **Dataset** 結構化資料（最大缺口） |
| `@astrojs/sitemap` 自動產 sitemap-index；`robots.txt` 放行全部 | 沒有 **WebApplication / MedicalWebPage** 型別 |
| canonical、OG、Twitter card、`<meta description>`、author 齊全 | 地圖數字只在 SVG/Leaflet → 不可爬 |
| 資料齊全度表（`#dp-table-wrap`）| 該表是 **JS 注入**，HTML 原始碼裡沒有列 → 爬蟲/LLM 看不到 |
| 逐層資料檔 `public/data/**/*.json`（含 `meta.source`、年份） | 這些 meta 尚未被輸出成頁面上的表格或 JSON-LD |

## 2. 硬前提（不先解，其餘白做）

- **Cloudflare 邊緣預設擋 AI 爬蟲**（見既有研究：CF 的 "Block AI Scrapers and Crawlers" / Bot Fight Mode）。`robots.txt` 放行是**必要但不充分**——CF 在邊緣就把 GPTBot / ClaudeBot / PerplexityBot / Google-Extended 擋掉，AEO 直接歸零。
  - **動作**：CF Dashboard 確認並**放行**這些 AI crawler UA；若用 "AI Audit" 功能，設為允許索引。
  - 驗證：部署後看伺服器/CF log 是否有 GPTBot、ClaudeBot 實際取得 200。
- sitemap、canonical 已有，維持即可。

## 3. 資料 → 表格（本站現有資料逐層對應）

原則：每層輸出一張**語意化 `<table>`**（`<caption>` + `<th scope>`），且在 **Astro build 時就渲染進 HTML**（SSG，不靠 JS 注入），這樣爬蟲與答案引擎才看得到。列＝國家或 admin-1 單元；每個數字都帶年份與出處（meta 已有）。

| 圖層 | 列 | 欄 | 資料真源 |
|---|---|---|---|
| 高齡化 65+（國家級） | 26+ 國 | 國家、65+ %、UN 高齡分級、年份、來源 | `aging/*.json` meta ＋ World Bank |
| 高齡化 65+（admin-1） | 逐國（如 TR 81、TW 370） | 行政區、65+ % | `aging/<cc>-admin1.json` |
| 失智盛行率 | 國家＋admin-1 | 單元、盛行率 %、年齡層、來源 | `dementia/*.json` |
| PM2.5 | admin-1 | 單元、µg/m³、年 | `pm25/*.json` |
| 可調控風險 / PAF | 國家 | 因子、盛行率、RR、PAF % | exposome 資料 |

落地位置：放在「資料與文獻」分頁下，新增可折疊的「**資料表 / Data tables**」區。**最省做法**＝把現有 `#dp-table-wrap` 從 JS 注入改成 build 時 SSR（同一份資料，改渲染時機）。逐國錨點（`#aging-tr` 等）方便深連與被引用。

## 4. schema.org JSON-LD（加在既有 `@graph`）

在 `BaseLayout.astro` 的 `jsonLd['@graph']` 陣列**追加**下列型別（沿用既有機制，不新開檔）：

- **`Dataset`（每層一個，最關鍵）**——`name` / `description` / `creator`（指向既有 Person）/ `license` / `temporalCoverage` / `spatialCoverage`（國家清單 `Place`）/ `variableMeasured`（`PropertyValue`：如「share of population aged 65+」）/ `distribution`（指向 `public/data/**` 的 JSON URL）/ `isBasedOn`（Eurostat、WorldPop、各國統計處…）/ `citation`（§⑤ 參考文獻）。→ 進 **Google Dataset Search**，並成為 AI 引用時的「出處」。
- **`WebApplication`**——本工具本身（`applicationCategory: HealthApplication`、`isAccessibleForFree: true`、`featureList`：腦齡估算、全球地圖、資料下鑽）。
- **`MedicalWebPage`**——`about` = `MedicalCondition`「Dementia」（附 ICD-10 F03）、`lastReviewed`、`audience`；**務必保留「教育用途、非診斷」聲明**（`MedicalWebPage` 提升健康主題權威，但別過度宣稱醫療效力）。
- Person / WebSite 已有；可補 `Person` 的 `sameAs`、資歷以強化 E-E-A-T（作者身分是答案引擎信任訊號）。

實作方式：用各 `*.json` 的 `meta` 在 build 時**自動生成** Dataset 節點（資料變、schema 跟著變，零手維護，和 registry／freshness 同哲學）。

## 5. AEO 內容形態（讓事實可被「抬走」）

- 每張地圖旁，同一批數字也給**一句定義句 + 一張表**（LLM 抬句子與表格，不抬 SVG）。例：「土耳其 Sinop 省 65 歲以上人口占 20.8%（TÜİK ADNKS 2024）。」
- 逐國深連結（`?country=tr` 類）確保：渲染該國的表格 + 國別 `<title>`/`<meta>` + `Place` JSON-LD，讓「dementia aging Türkiye」這類查詢能落地且被引用。
- 單位一致、年份明示、每個數字帶出處（meta 已具備）——這正是答案引擎會照抄的「according to X (year)」。

## 6. 落地順序（之後 /refresh 時）

1. **CF 放行 AI 爬蟲** + 確認 sitemap（基礎設施，最優先）。
2. **SSR 資料齊全度表**（`dp-table` 資料改 build 時渲染成 HTML）。
3. **每層 Dataset JSON-LD**（由 `*.json` meta 自動生成）。
4. **WebApplication + MedicalWebPage + 強化 author** JSON-LD。
5. **驗證**：Google Rich Results Test、Schema Markup Validator、CF log 確認 GPTBot/ClaudeBot 取得 200。

## 7. 明確不做（依既有 SEO/AEO 研究裁決）

- ❌ **FAQ schema**——Google 已收掉 FAQ rich result，投報比為零。
- ❌ **llms.txt**——不做。
- ❌ **拆站／每國一個子網域**——維持單站 + 錨點/深連結即可。

---

### 附：一頁摘要
「基礎 SEO 已滿分；AEO 的錢在 **Dataset schema + 可爬表格**。先過 CF AI 爬蟲閘門，再把地圖背後那批已帶出處的 `*.json` meta，一路輸出成 SSR 表格 + 自動生成的 Dataset JSON-LD——資料一變、表格與 schema 全自動跟上。」
