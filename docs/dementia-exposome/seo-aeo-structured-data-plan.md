# SEO / AEO 結構化資料規劃 — brain-exposome

> 規劃文件（2026-09-01）。**尚未改任何程式碼**，供之後 `/refresh` 時逐項落地。
> 目標：把本站已有的公共衛生資料，變成搜尋引擎與**答案引擎（AEO：ChatGPT / Perplexity / Google AI Overviews）**能抓、能引用、能標註出處的形式。

## 0. 一句話結論

本站是「資料密集 + 出處完整」的公衛工具 —— 這正是 AEO 最愛引用的素材。**唯一問題：數字現在只活在 SVG/Leaflet 地圖與 JS 注入的表格裡，爬蟲與 LLM 看不到。**

**兩條槓桿要分清（依既有 SEO/AEO 研究，已查證）：**
- **被 AI 引用（AEO）的真槓桿＝內容，不是 schema。** Ahrefs 實測：schema 對 AI 引用**無直接效**。GEO 論文實證前三：原話引言 +42.8%、**統計數據 +32.7%**、流暢化 +28.7%。本站每個 admin-1 數字都帶年份與出處 —— 只要**變成可爬的表格 + 可引用的統計句**，就正中「統計數據」這條。前提是先過 Cloudflare AI 爬蟲閘門。
- **`schema.org` 的用途是「還活著的 rich results」與 Google Dataset Search 的發現性，不是 AI 引用。** 因此 **Dataset** JSON-LD 值得做（進 Google Dataset Search），但別期待它讓 LLM 引用我們 —— 那是內容的事。

基礎建設（canonical、OG、sitemap、Person/WebSite JSON-LD）都已就緒。缺的是：**(a) 可爬的 SSR 表格 + 可引用統計句（AEO 主力）**、**(b) Dataset schema（Dataset Search 發現性）**。
（研究正本：`D:\Claude_Project_Space\ShanLinSays\research\`，尤其 `00-...總覽.md` 第五節 CF 六項檢查與統一寫作清單。）

## 1. 現況盤點（已查證）

| 已有 ✅ | 缺口 ❌ |
|---|---|
| `BaseLayout.astro`：JSON-LD `@graph`（Person 葉淨維 + WebSite） | 沒有 **Dataset** 結構化資料（最大缺口） |
| `@astrojs/sitemap` 自動產 sitemap-index；`robots.txt` 放行全部 | 沒有 **WebApplication / MedicalWebPage** 型別 |
| canonical、OG、Twitter card、`<meta description>`、author 齊全 | 地圖數字只在 SVG/Leaflet → 不可爬 |
| 資料齊全度表（`#dp-table-wrap`）| 該表是 **JS 注入**，HTML 原始碼裡沒有列 → 爬蟲/LLM 看不到 |
| 逐層資料檔 `public/data/**/*.json`（含 `meta.source`、年份） | 這些 meta 尚未被輸出成頁面上的表格或 JSON-LD |

## 2. 硬前提（不先解，其餘白做）

- **Cloudflare 邊緣預設擋 AI 爬蟲**（2025-07 起新網域預設封鎖）。`robots.txt` 放行是**必要但不充分**——CF 在邊緣就把爬蟲擋掉，AEO 直接歸零。
  - **動作**：跑研究總覽 `00-...總覽.md` **第五節的六項檢查**；重點把**答案引擎的 Search/Agent bot 設為 don't block**（OAI-SearchBot、PerplexityBot、Claude-SearchBot、Google-Extended、GPTBot、ClaudeBot）。注意 GEO 引用走的是 *Search* bot，不是訓練爬蟲，兩者都要放行。
  - 驗證：部署後看 CF/伺服器 log 是否有這些 UA 實際取得 200。
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

> ⚠️ 定位：schema **不是** AI 引用槓桿（Ahrefs 實測無直接效）。做它的理由是**還活著的 rich results 與 Google Dataset Search 的發現性**。別把它排在 §3/§5（可爬表格＋統計句）前面。

在 `BaseLayout.astro` 的 `jsonLd['@graph']` 陣列**追加**下列型別（沿用既有機制，不新開檔）：

- **`Dataset`（每層一個）**——`name` / `description` / `creator`（指向既有 Person）/ `license` / `temporalCoverage` / `spatialCoverage`（國家清單 `Place`）/ `variableMeasured`（`PropertyValue`：如「share of population aged 65+」）/ `distribution`（指向 `public/data/**` 的 JSON URL）/ `isBasedOn`（Eurostat、WorldPop、各國統計處…）/ `citation`（§⑤ 參考文獻）。**價值＝進 Google Dataset Search**（一個還活著的發現面），不是讓 LLM 引用。
- **`WebApplication`**——本工具本身（`applicationCategory: HealthApplication`、`isAccessibleForFree: true`、`featureList`：腦齡估算、全球地圖、資料下鑽）。
- **`MedicalWebPage`**——`about` = `MedicalCondition`「Dementia」（附 ICD-10 F03）、`lastReviewed`、`audience`；**務必保留「教育用途、非診斷」聲明**（`MedicalWebPage` 提升健康主題權威，但別過度宣稱醫療效力）。
- Person / WebSite 已有；可補 `Person` 的 `sameAs`、資歷以強化 E-E-A-T（作者身分是答案引擎信任訊號）。

實作方式：用各 `*.json` 的 `meta` 在 build 時**自動生成** Dataset 節點（資料變、schema 跟著變，零手維護，和 registry／freshness 同哲學）。

## 5. AEO 內容形態（讓事實可被「抬走」）— **這才是引用主力**

依 GEO 論文實證：**統計數據 +32.7%**、原話引言 +42.8%、流暢化 +28.7%（關鍵字堆砌 −8.6%）。本站每個數字都帶出處與年份，天然吃到「統計數據」這條 —— 只要讓它可爬、可引用。

- 每張地圖旁，同一批數字也給**一句可引用的統計句 + 一張表**（LLM 抬句子與表格，不抬 SVG）。例：「土耳其 Sinop 省 65 歲以上人口占 20.8%（TÜİK ADNKS 2024）。」—— 這一句同時滿足「統計數據」與「帶出處原話」兩條槓桿。
- 逐國深連結（`?country=tr` 類）確保：渲染該國的表格 + 國別 `<title>`/`<meta>` + `Place` JSON-LD，讓「dementia aging Türkiye」這類查詢能落地且被引用。
- 單位一致、年份明示、每個數字帶出處（meta 已具備）——這正是答案引擎會照抄的「according to X (year)」。

## 6. 落地順序（之後 /refresh 時）

1. **CF 放行 AI 爬蟲** + 確認 sitemap（基礎設施，最優先）。
2. **SSR 資料齊全度表**（`dp-table` 資料改 build 時渲染成 HTML）。
3. **每層 Dataset JSON-LD**（由 `*.json` meta 自動生成）。
4. **WebApplication + MedicalWebPage + 強化 author** JSON-LD。
5. **驗證**：Google Rich Results Test／Schema Markup Validator（schema）、Google Dataset Search（Dataset 有無被收）、CF log 確認 Search bot 取得 200；**接 Bing Webmaster Tools —— 其 AI Performance 報表是目前唯一給「被 AI 引用次數」的官方後台**。GSC 起量先修「曝光零點擊／排名 8–20」舊頁，別急著先產新內容。

## 7. 明確不做（依既有 SEO/AEO 研究裁決）

- ❌ **FAQ schema**——Google 已收掉 FAQ rich result，投報比為零。
- ❌ **llms.txt**——不做。
- ❌ **拆站／每國一個子網域**——維持單站 + 錨點/深連結即可。

---

### 附：一頁摘要
「基礎 SEO 已滿分。**AEO 被引用的錢在『可爬表格 + 可引用統計句』（schema 對 AI 引用無效）**；schema 另做，只為 Google Dataset Search 的發現性。先過 CF AI 爬蟲閘門，再把地圖背後那批已帶出處的 `*.json` meta，一路輸出成 SSR 表格 + 統計句，Dataset JSON-LD 自動生成——資料一變全自動跟上。」
