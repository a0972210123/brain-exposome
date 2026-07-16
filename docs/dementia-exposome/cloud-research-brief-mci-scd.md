# 雲端 Deep-Research 任務書：全球 MCI／SCD 盛行率徹底檢索

> **給雲端 session（claude.ai/code）執行。** 目標：為**每一個國家**找出最新、最權威的
> **MCI（輕度認知障礙）**與 **SCD（主觀認知衰退）**盛行率來源，附完整出處，讓本地 session
> 能把它們接進 dementia-exposome 地圖。完成後開一個 PR 記錄檢索結果（**不 self-merge**）。
> 建立：2026-07-16（local session）。

---

## 0. 任務一句話
把目前 MCI 的「區域統合底色 + 5 國全國覆寫」升級成**盡可能多國的全國實測值**，並**首次**為 SCD
建立可用的國家別資料集；每一筆都要有可驗證出處、年份、年齡層、診斷準則、取用狀態（OA／付費牆）。

---

## 1. 現況（你不用重做的部分）

**地圖**：`mattye.dev/projects/dementia-exposome`（Astro 靜態站）。地球儀圖層：高齡化、失智盛行率
（GBD 2023）、PM2.5、綜合 PAF、**MCI**。SCD 尚未上圖。

**MCI 現況**（`public/data/mci/mci-national.json`）：
- 底色 = **Bai et al. 2022《Age & Ageing》**依世界銀行區域的 MCI 統合盛行率（50+、社區）：
  EAS 19.0／ECS 10.9／LCN 18.3／MEA 13.0／NAC 15.5／SAS 13.9／SSF 3.8（%）。
- 全國覆寫 5 國：TW 18.7（Sun 2014/2017）、JP 15.5（MHLW 2024）、KR 22.7（KDO 2020）、
  IN 17.6（LASI-DAD）、CN 15.4（Xue 2021）。
- 已佐證（不用再找）：Song 2023 全球 19.7%、Salari 2025 老年 23.7%、拉美專屬 14.95%（T&F 2021）、
  China Lu 2021 12.2%。

**SCD 現況**：**未上圖**。目前只找到中國資料（Hao 2017 clinical 14–19%、Frontiers 2023 自述 46.4%），
無全球／區域一致來源。**這是本任務的重點缺口之一。**

**資料 schema**（每國一筆，本地會用）：`{prev_pct, ci, age, criteria, year, source_type, citation, doi_url, access, subnational, representative, n, confidence}`。

**國家範圍**：~200 國（ISO alpha-2/3；沿用世界銀行國家清單）。台灣須含（多數資料庫排除，需另找內政部/NHRI/學術）。

---

## 2. 每個國家要交出什麼（MCI 與 SCD 各一筆，能找到就填）

| 欄位 | 說明 |
|---|---|
| `prev_pct` | 點估計（%）；有 95% CI 就填 `ci` |
| `age` | 年齡層/母體（65+／60+／50+／其他） |
| `criteria` | 診斷準則/工具：MCI→Petersen／DSM-5 mild NCD／MoCA／MMSE；SCD→SCD-I framework／單題自述／結構化問卷 |
| `year` | 資料/調查年（**優先 2021–2026**；較舊則註明為該國最新可得） |
| `source_type` | `govt-database`／`national-survey`／`national-cohort`／`registry`／`meta-analysis`／`regional-study` |
| `citation` | 作者、期刊/資料庫、年 |
| `doi_url` | DOI 或穩定 URL |
| `access` | `OA`（附連結）／`paywalled`（註明出版社）／`govt`（政府頁） |
| `subnational` | 有無 admin-1/省/縣/州別細分（**有就標明層級與單位數** → 未來做次國家層） |
| `representative` | 是否全國代表性；community vs clinic；樣本數 `n` |
| `confidence` | high／medium／low（代表性 + 準則品質） |

**不要硬正規化**：地圖保留各國出處與「模型估計、異質」註記；你只要**忠實記錄 + 標註準則**，讓本地判斷。

---

## 3. 檢索來源優先序（每國都掃這幾層）

1. **政府統計/衛生機關 + 失智登記**：如 韓國 KDO/NaSDEK、日本 厚労省/JPSC-AD、美國 CDC BRFSS/Alzheimer's Assoc F&F、英國 CFAS、加拿大 PHAC/CCDSS、澳洲 AIHW、台灣 NHRI/HPA、歐盟各國統計局。
2. **大型全國世代/老化研究**：LASI-DAD（印度）、ELSI-Brasil、MHAS/ENASEM（墨西哥）、CLSA（加拿大）、SHARE（歐洲多國）、CHARLS（中國）、KLoSA（韓國）、JAGES（日本）、TILDA（愛爾蘭）、HRS/ADAMS（美國）、ELSA（英國）、SAGE（WHO 6 國）、10/66 Dementia Research Group（多 LMIC）。
3. **全國盛行率調查**（door-to-door／社區）。
4. **系統性回顧/統合分析**：全球、區域（如拉美 14.95%）、單國（中國、印度…）— 用來**補長尾覆蓋**與**三角驗證**。
5. **WHO/OECD/GBD-adjacent**（註：**GBD 不產 MCI/SCD**，別浪費時間找 GBD 的 MCI）。

**SCD 特別注意**：SCD 沒有像失智那樣的成熟全球資料；重點找**區域/多國 SCD 統合**（Röhr、Jessen SCD-I 相關）、
各國大型世代裡的 SCD 題組。若某國只有自述單題 → 標 `criteria: self-report-single-item`、`confidence: low`。

---

## 4. 多 agent 策略（請先評估效益再釋放）

- **分工單位 = 國家**（或小群集）。~200 國 × 2 指標。
- **分層釋放**（避免對沒有全國資料的國家硬燒 agent）：
  - **Tier A（~50–70 國，很可能有全國資料）**：高所得國 + 大型 LMIC（G20＋東亞＋歐盟＋主要拉美/非洲大國）→ **每國一個專責 agent**（MCI＋SCD 一起查）。
  - **Tier B（區域長尾）**：其餘國家 → **每個世界銀行區域一個 agent**，用區域統合 + 少數國家研究覆蓋，不逐國硬找。
  - **Tier C（查無）**：明確記為「僅區域估計可用」。
- **agent 數量**：Tier A 逐國（~50–70）+ Tier B 區域（7–14）+ 交叉驗證/去重（數個）≈ **70–100 個 agent**。
  若某區域資料特別豐富（歐洲、東亞），可再細分到次區域。**上百個 agent 可接受，但每個要 scope 很緊
  （一國、明確產出 schema），並先去重**（很多小國注定只有區域值，不要各派一個 agent 空跑）。
- **每個 agent 產出**：§2 的結構化記錄（MCI + SCD），附「已檢索哪些來源、找到/沒找到」。

---

## 5. PR 產出物（要 commit 的東西）

**只 commit 衍生的檢索結果，不 commit 原始 PDF**（`scripts/_data_in/` 是 gitignored；沿用 repo 慣例）。

1. **`docs/side-projects/dementia-exposome/mci-scd-sources.md`** — 人類可讀總表：每國 MCI/SCD 一列
   （值、年齡、準則、年份、來源、DOI、access、subnational、confidence）。
2. **`scripts/mci-scd-sources.json`**（committed，非 _data_in）— 機器可讀，以 ISO alpha-2 為鍵，schema 同 §2。
   本地會直接吃這份來更新 `build_mci_national()`／新增 `build_scd_national()`。
3. **`docs/side-projects/dementia-exposome/mci-scd-download-worklist.md`** — 下載清單，分三類：
   - **OA 可直接抓**：附 URL（本地用 `fitz` 抓 PDF 萃取值）。
   - **付費牆需 VPN**：出版社 + 精確 URL/DOI（owner 用學校 VPN 下載到 `_data_in/`）。
   - **已足夠、免下載**：摘要即含 pooled/subgroup 數字者。
4. 一段 **coverage 統計**：MCI 幾國有全國值/幾國僅區域；SCD 幾國有資料。

---

## 6. 定義與陷阱（務必內建判斷）

- **MCI**：優先 Petersen／DSM-5 mild NCD、社區、註明年齡層。**MoCA-only 會高估**（~20%+）、MMSE 偏低 → 都要標。
- **SCD**：優先 SCD-I 結構化框架；**單題自述會膨脹到 40–60%** → 標 `self-report-single-item`＋`low`。
- **付費牆會擋自動抓取**（OUP／Karger／Cambridge／Wiley／Elsevier/ScienceDirect／T&F／Sage → 402/403）；
  但**摘要常含 pooled + subgroup 數字**，能抓就抓摘要數字 + 標 access。**BMC 會轉址到 Springer IDP** → 記 DOI 讓本地/VPN 抓。
- **不要捏造 DOI**；抓不到就標「need full text」。
- **台灣**：多數國際資料庫排除 → 找 NHRI 全國調查、內政部、學術（Sun/PLoS、TIGER）。**目前查無公開發表的縣市級 MCI**（全國調查涵蓋 19 縣市但未發布分縣市值）— 若你找到縣市級，特別標出。
- **偏好近 3–5 年**（2021–2026）；若某國最新就是較舊研究，照實記 + 標年份。

---

## 7. Repo 慣例（給雲端）

- 先 `git fetch` + 從**最新 `origin/main`** 開分支（本地 clone 常落後）。
- **一個 PR、不 self-merge**（等 owner 說「可以 merge」）；merge 用 merge-commit。
- **不要 base 在別的未合併 PR 分支上**（本專案曾因 stacked-PR 讓內容漏進 main）。
- `.claude/`、`scripts/_data_in/` 皆 gitignored → **顯式 stage 路徑，勿 `git add -A`**。
- 保留「modelled estimate／異質、跨國比較需謹慎」的框架。

---

## 8. 完成後 → 回傳給本地的交接 md（請雲端一併產出）

在 PR 裡放一份 **`mci-scd-handoff-to-local.md`**，明確告訴本地 session：
1. **可直接接的值**：哪些國家的 MCI/SCD 值可直接寫進 `mci-scd-sources.json`（附 kind=national）。
2. **要本地下載的 OA PDF**：URL 清單（本地 `fitz` 萃取）。
3. **要 owner VPN 下載的付費牆 PDF**：精確清單 + 為什麼（本地抓不到）。
4. **次國家（admin-1）資料**：哪些國家有省/縣/州別 MCI/SCD → 給未來次國家層。
5. **SCD 可行性結論**：是否已足夠做全球/區域 SCD 層，或仍需補哪些。

之後流程：本地 `git pull` 這個 PR → 依 handoff 下載/萃取 → 更新 `build_mci_national()` +
新增 `build_scd_national()` → 烘焙進 `world-globe.geojson` → 開實作 PR。

---

## 9. 起手參考（已知強來源，當作 seed，不要重找）
LASI-DAD（IN）· MHLW/JPSC-AD（JP）· NaSDEK/KDO（KR）· Sun 2014/PLoS（TW）· Xue 2021/Lu 2021（CN）·
Bai 2022（全球區域）· Song 2023／Salari 2025（全球佐證）· 拉美 T&F 2021 · 10/66 DRG（多 LMIC）·
SHARE（歐洲）· HRS-ADAMS/MCSA（US）· CFAS（UK）· MHAS（MX）· ELSI（BR）· CLSA（CA）· AIHW（AU）。

## 相關檔案
- 現況資料：`public/data/mci/mci-national.json`、`scripts/build_data.py`（`BAI_MCI`／`MCI_NATIONAL`／`build_mci_national`）
- 資料流程：[`data-refresh-workflow.md`](./data-refresh-workflow.md)
- 認知障礙來源盤點（第一版，可延伸）：`scripts/provenance-audit-cognitive.json`
