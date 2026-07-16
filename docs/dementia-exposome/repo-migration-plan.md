# 遷移計畫：把 dementia-exposome 拆成獨立 repo，仍部署到 mattye.dev

> 需求（owner）：專案越來越大，想**獨立開一個 repo 管理**，但**仍部署到目前網域 mattye.dev**。
> 本文提供選項比較、建議做法、分階段步驟、風險與回滾。建立：2026-07-16。
> ⚠ 這是**計畫**；實際遷移（開新 repo、改 Cloudflare 設定）屬結構性/對外動作，**需 owner 明確同意後才執行**。

---

## 1. 現況與耦合盤點

| 項目 | 現況 | 遷移難度 |
|---|---|---|
| 頁面 | 單一檔 `src/pages/projects/dementia-exposome.astro` | 低 |
| 共用相依 | 只 import **`BaseLayout.astro`** + **`T.astro`**（i18n） | 低（複製精簡版即可） |
| 資料資產 | `public/data/`（geo/exposome/pm25/dementia/data-provenance/manifest）≈ **4.1 MB** | 低（整包搬） |
| 資料管線 | `scripts/build_data.py`、`gen_provenance.py`、`scrape.py` | 低（整包搬） |
| raw 輸入 | `scripts/_data_in/` ≈ **1.5 GB**（gitignored：GBD/WorldPop rasters/PDF） | 特殊（見 §5） |
| 文件 | `docs/side-projects/dementia-exposome/`（14 檔） | 低 |
| 部署 | Cloudflare Pages 連 GitHub `main`，build = `npm run build`（**純 Astro，無需 Python**） | 中（要新開 Pages 專案 + 網域路由） |
| 網址 | `https://mattye.dev/projects/dementia-exposome/` | **關鍵決策點**（見 §2） |

**重要**：Cloudflare Pages 的 build 只跑 Astro；Python 管線是**另外**在本機/GitHub Action 跑、把衍生 JSON commit 進 repo。
所以新 repo 的 Pages build **不需要 Python 環境**，很單純。`.git` 目前僅 ~58 MB（1.5 GB 是 gitignored，不在版控內）。

---

## 2. 關鍵決策：要不要保留「原網址路徑」？

「同樣部署到 mattye.dev」有兩種解讀，決定架構：

- **(甲) 可接受子網域** → 如 `brain.mattye.dev` 或 `dementia.mattye.dev`。**最乾淨、最好維護。**
- **(乙) 必須維持原路徑** `mattye.dev/projects/dementia-exposome/` → 需要 **Cloudflare Worker 反向代理**把該路徑轉到第二個 Pages 專案。可行但多一層基礎設施。

> 這是唯一需要 owner 拍板的點。以下三個選項對應不同答案。

---

## 3. 選項比較

### 選項 A —— 子網域 + 獨立 Cloudflare Pages（**推薦，若可接受子網域**）
- 新 repo `dementia-exposome` → 新 Pages 專案 → 自訂網域 `brain.mattye.dev`（CNAME）。
- 舊路徑 `mattye.dev/projects/dementia-exposome/` 在**主站**留一條 **301 轉址**到新子網域（保留 SEO/舊連結）。
- **優點**：完全獨立 build/CI/issues；主站瘦身；互不影響。
- **缺點**：網址變子網域（301 可保留大部分 SEO 權重）；跨子網域 analytics 要各自設定。

### 選項 B —— 維持原路徑 + Cloudflare Worker 反向代理（**若路徑必須不變**）
- 新 repo → 新 Pages 專案（產生 `xxx.pages.dev` origin）。
- 主站前面掛一支 **Worker**：`/projects/dementia-exposome/*` → fetch 第二專案 origin；其餘 → 主站。
- Astro 設 `base: '/projects/dementia-exposome/'`，資產路徑才正確。
- **優點**：網址完全不變（SEO/連結零損失）。
- **缺點**：多一層 Worker（維護 + 極小延遲）；兩個 origin；`base` 設定要小心。

### 選項 C —— Git submodule / subtree（單一部署，原始碼分 repo）
- 主 repo 保留單一 Pages 部署，但子專案原始碼放獨立 repo，以 **submodule/subtree** 掛回 `src/pages/projects/` 等路徑。
- **優點**：網址不變、單一部署。
- **缺點**：submodule 在 Cloudflare Pages checkout 需額外設定（`git clone --recursive`）；build 仍與主站耦合（共用 Astro config/BaseLayout）→ **不是真正的獨立部署**，與 owner「獨立管理」的意圖有落差。

**建議**：優先 **A**（若可接受 `brain.mattye.dev`）；若堅持原路徑則走 **B**。C 只在「想拆版控但不想動部署」時用。

---

## 4. 遷移步驟（以 A / B 為例，分階段、可回滾）

**階段 0 — 準備（不影響線上）**
1. 決定子網域名（A）或確認走 Worker（B）。
2. 盤點要搬的路徑：`src/pages/projects/dementia-exposome.astro`、`public/data/*`、`scripts/{build_data,gen_provenance,scrape}.py`、`docs/side-projects/dementia-exposome/`、`.gitignore` 中 `_data_in/` 規則。

**階段 1 — 建新 repo（保留 git 歷史）**
3. 用 `git filter-repo`（或 `git subtree split`）把上述路徑的**歷史**抽到新 repo，保留 commit 記錄。
4. 加**精簡 standalone Astro 殼**：複製 `BaseLayout.astro`（含 SEO/OG/JSON-LD）＋ `T.astro`＋必要 `global.css` 片段（去除主站 Header/Footer 或改精簡版）。
5. `astro.config`：`site` 設對（A：`https://brain.mattye.dev`；B：`https://mattye.dev` 且 `base:'/projects/dementia-exposome/'`）。
6. 本機 `npm run build` + preview，確認地圖各層、i18n、方法框、參考文獻、OG/JSON-LD 全部正常。

**階段 2 — 新部署（與線上並行、先不切換）**
7. Cloudflare 新 Pages 專案連新 repo；build `npm run build`、output `dist`。
8. 先用 `*.pages.dev` 預覽網址驗證；再綁自訂網域（A：`brain.mattye.dev` CNAME；B：設 Worker route）。

**階段 3 — 切換網址**
9. A：主站加 `301 /projects/dementia-exposome/* → https://brain.mattye.dev/`（Cloudflare `_redirects` 或 Pages redirect）。
   B：部署 Worker route，實測原路徑已由新 origin 提供。
10. 更新 `sitemap`、`llms.txt`、主站內部連結、canonical。

**階段 4 — 主站清理（驗證新站穩定後才做）**
11. 從 `personal-website` 移除該頁 + `public/data/*` + `scripts/*.py` + 對應 docs（或留一個轉址 stub）。
12. 更新主站 README / CLAUDE.md 指到新 repo。

---

## 5. raw 輸入（`_data_in/` 1.5 GB）怎麼辦
- 這些是 **gitignored** 的原始檔（GBD CSV、WorldPop rasters、NHIS PDF），**不會**隨 git 歷史轉移。
- 選項：(a) owner 本機把 `_data_in/` 整包複製到新 repo 同路徑即可（管線路徑相對 repo root，不需改碼）；
  (b) 或存到一個私有雲端/物件儲存，管線加下載步驟。
- 因授權（GBD 非商業）與體積，**建議維持本機/私有**，新 repo 的 `.gitignore` 沿用同規則。

---

## 6. SEO / 連結不中斷 checklist
- [ ] 舊路徑 301 → 新位置（A）或 Worker 保持原路徑（B）。
- [ ] 新站 `canonical`、`og:url`、JSON-LD `url` 指到最終網址。
- [ ] `sitemap.xml` 更新（主站移除該頁 / 新站加入）。
- [ ] Google Search Console：A 需為子網域新增 property + 提交 sitemap；送出網址變更。
- [ ] `llms.txt`、社群/名片既有連結沿用（靠 301）。
- [ ] GA4：A 為跨網域，設定 measurement 或沿用同 property 的 cross-domain。

---

## 7. 風險與回滾
| 風險 | 緩解 |
|---|---|
| 資產路徑破圖（`base` 設錯） | 階段 1 本機 preview 全站點一遍；B 務必設 `base` |
| BaseLayout 缺 SEO/OG | 複製時逐項比對 `<head>`；build 後檢查 OG/JSON-LD |
| 管線相對路徑失效 | `build_data.py` 用 `ROOT=repo root` 相對路徑，整包搬即可；跑一次驗證 |
| Cloudflare 兩專案設定衝突（B） | 先在 `*.pages.dev` 驗證，Worker route 最後才切 |
| 切換期空窗 | **並行部署**：新站驗證 OK 前，主站頁面不刪（階段 4 才清理） |
| 回滾 | 只要還沒做階段 4，移除 301/Worker route 即完全回到現況 |

---

## 8. 建議與下一步
1. **先確認 §2 決策**：可接受 `brain.mattye.dev`（選 A，較省事）還是必須保留原路徑（選 B）。
2. 決定後，我可以先在**本機**把 standalone 殼 + filter-repo 歷史抽取準備好（不動線上），交付一個可 preview 的新 repo 草稿。
3. Cloudflare 端（新 Pages 專案、網域、Worker）屬 owner 帳號操作，我會提供逐步指引，但**不代為更動 Cloudflare 設定**（CLAUDE.md：不改 Cloudflare 設定除非明確要求）。

---

## 相關文件
- 資料更新流程：[`data-refresh-workflow.md`](./data-refresh-workflow.md)
- 專案規則：`/CLAUDE.md`（部署、PR、禁止事項）
