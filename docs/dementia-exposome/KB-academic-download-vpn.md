# KB：學術文獻／資料庫下載 · VPN · PDF 抓取（給未來 session 用）

> 從 dementia-exposome 的 MCI/SCD 檢索累積的可重用知識。任何未來 session 要抓學術論文 PDF、
> 或從期刊/政府資料庫取資料時，先讀這份。建立 2026-07（NTU VPN 實測）。

---

## 0. 最重要的一件事：誰的網路？
- **本地 Claude Code session 跑在使用者的 Windows 機器上** → `Bash`/`curl` 走**使用者的網路 + VPN**。
- **`WebFetch` 不走使用者網路**（從 Anthropic 基礎設施出去）→ 使用者開 VPN 對 WebFetch **無效**；要用 `curl`（Bash）。
- 驗證出口 IP：`curl -s https://ipinfo.io/json`（開 NTU VPN 會看到 `140.112.x.x · National Taiwan University`）。

## 1. VPN 給的是 institutional IP，但**擋你的通常不是付費牆，是 bot 防護**
即使有機構 IP，多數商業出版社用 Cloudflare「are you human」JS 挑戰擋 `curl` → 你拿到的是 HTML（`<!DOC…`），不是 PDF。
- **curl 抓得到**：Springer/BMC、Nature（OA）、MDPI、Frontiers、PLoS、EuropePMC OA。
- **curl 抓不到（要真瀏覽器）**：Wiley、Sage/IOS（JAD `10.3233`）、Karger、OUP、Elsevier/ScienceDirect、Cambridge、Neurology(Wolters Kluwer)、LWW、Taylor&Francis。**連 PMC/PubMed 文章頁也回 HTML 給 curl**（非 OA-subset 的 PMC 尤其）。

## 2. curl 自動抓 PDF 的技巧（依成效排序）
1. **EuropePMC OA render**（PMC 最穩）：`https://europepmc.org/backend/ptpmcrender.fcgi?accid=PMC{id}&blobtype=pdf`（僅 OA subset）。
2. **`citation_pdf_url` meta**：抓 landing HTML → `<meta name="citation_pdf_url" content="…">` → 下載該 URL。多數 OA 出版社有埋（Google Scholar 慣例）。
3. **各出版社 PDF URL pattern**：
   - Springer/BMC：`https://link.springer.com/content/pdf/{doi}.pdf` ✅
   - Nature：`https://www.nature.com/articles/{id}.pdf` ✅（OA）
   - MDPI / Frontiers：`{article_url}/pdf` ✅
   - PLoS：`https://journals.plos.org/plosone/article/file?id={doi}&type=printable` ✅
   - Wiley：`/doi/pdfdirect/{doi}`、Sage：`/doi/pdf/{doi}`、Karger/OUP：article-pdf → **常被 Cloudflare 擋** ❌
4. **DOI→PMCID lookup**（把 doi.org 轉成 OA render）：`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:"{doi}"&format=json` → `pmcid` + `isOpenAccess=="Y"` → 用 render endpoint。
5. **瀏覽器 headers + cookie jar**：`-A "<Chrome UA>" -c/-b cookies.txt -e <referer> -H "Accept: application/pdf"`。小幅提升，贏不了 Cloudflare。

## 3. **一定要驗證下載的 PDF**（踩過雷）
- 用 `fitz`（pymupdf）**開檔驗證**：`d=fitz.open(p); len(d)>=1 and len(text)>150`。不要只看 `%PDF` magic bytes。
- **greedy「同網域任何 `.pdf` href」fallback 會抓錯文件**（曾把 landing page 上連的 *World Alzheimer Report* 當成目標論文抓下來）→ 抓完要做 **title/國名 match** 驗證，不符就丟。
- Windows：`fitz` 開著檔時 `os.remove` 會 `PermissionError` → 先 `d.close()` 再刪。

## 4. 實測成效（MCI/SCD, 2026-07, NTU VPN）
- 90 個 OA 連結：plain curl **1** → per-host+citation_pdf_url **36** → +VPN retry **39**。
- 剩 88（含 38 付費牆）需**真瀏覽器**（Claude in Chrome / 使用者手動）。
- **結論：curl 自動化上限 ~40%。** 其餘靠 (a) 真瀏覽器，或 (b) **直接從摘要抽數值**（付費牆摘要常含 pooled + subgroup 數字，Bai 2022 的世界銀行區域值就是這樣抽到的）。

## 5. PDF 文字萃取
- **fitz (pymupdf)** 對**英文**論文萃取乾淨。**CJK 會亂碼**（字型 CMap 壞，pypdf/fitz 都 garble，只有數字可讀）→ 掃描 CJK PDF（如台灣 NHIS）要 `get_pixmap(200dpi)` render 成圖再視覺讀。
- 本機 `Read` tool 的 PDF 分頁需要 poppler(`pdftoppm`)，**沒裝** → 一律用 fitz 抽文字。

## 6. 認知/流行病學資料源特性（省得重踩）
- **GBD 不產 MCI/SCD**。MCI 全球底色用 **Bai et al. 2022《Age & Ageing》**（afac173）世界銀行區域統合（50+，社區）。佐證：Song 2023(19.7%)、Salari 2025(23.7%)、拉美 14.95%。
- **MCI 準則差異巨大**：MoCA-only 高估（20%+，「any impairment」到 90%+）；clinical(Petersen/DSM-5) 較低。→ 用 **plausibility gate 3–40%**，超出退回區域值。
- **SCD 幾乎全是單題自述** → 30–76%，隨問法變動，**不可跨國比較**；無全球統合。
- Keyless 公開 API（可全自動）：World Bank `api.worldbank.org`、WHO GHO `ghoapi.azureedge.net`、EuropePMC、NCD-RisC 靜態 CSV。

## 7. 檔案落地慣例
- 原始 PDF/raw 放 gitignored `scripts/_data_in/`（**不 commit**）；只 commit 衍生值 + 出處（如 `scripts/mci-scd-sources.json`）。
- 相關：`docs/side-projects/dementia-exposome/data-refresh-workflow.md`、`cloud-research-brief-mci-scd.md`、`mci-scd-download-worklist.md`。
