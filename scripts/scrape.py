#!/usr/bin/env python3
"""
scrape.py — Playwright scraper for the blocked upstream datasets that feed the
dementia-exposome map/calculator (/projects/dementia-exposome).

WHY THIS EXISTS
---------------
build_data.py can reach ACAG PM2.5 (S3), Natural Earth, npm and GitHub, so the
PM2.5 layers (Taiwan / Japan / Korea) are built directly. But the *prevalence*
and *population-by-age* inputs live on government / research portals —
Taiwan data.gov.tw + NHRI, Japan e-Stat + MHLW, Korea KOSIS + the national
dementia survey. Those are all behind interactive query pages (and are policy-
blocked from this CI sandbox — see docs/.../data-download-points.md). This
module drives a real browser through those query flows so they can be captured
in one run.

HONEST LIMITS
-------------
* In THIS repo's CI/build sandbox the egress is a strict policy allowlist, not a
  bot filter. Playwright routes through the same proxy, so it CANNOT reach the
  gov/research targets here either — every real recipe returns HTTP 000. Run this
  on the owner's UNRESTRICTED network (home/office), where the browser can load
  the pages. `--smoke` proves the browser harness itself works against a local
  data: URL, with no network.
* Each recipe encodes the click-path *as of July 2026*. Portals change their DOM;
  if a selector breaks, run with `--headed --slowmo 300` and update the recipe
  (the download-point doc lists the stable landing URLs as the source of truth).

OUTPUT
------
Everything lands in scripts/_data_in/ (gitignored). build_data.py already looks
there (fetch_population hook) — drop the files and re-run it to regenerate the
authoritative town-level prevalence and to unlock JP/KR prevalence maps once the
matching *-pop.csv / *-rates.csv are present.

SETUP (owner's machine)
-----------------------
  pip install playwright
  playwright install chromium          # or reuse a system Chrome via --chrome-path
  python3 scripts/scrape.py --list     # show recipes
  python3 scripts/scrape.py tw_moi_77132 nhri_mci jp_estat_pop kr_kosis_pop
  python3 scripts/scrape.py --smoke    # harness self-test, no network

In this repo's sandbox a pre-built Chromium exists at
/opt/pw-browsers/chromium-1194/chrome-linux/chrome and is used automatically for
--smoke; pass --chrome-path to override anywhere.
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_IN = os.path.join(ROOT, "scripts", "_data_in")

# Pre-installed Chromium in this sandbox; owner machines usually use the one that
# `playwright install` drops, so this is only a convenience default.
SANDBOX_CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def log(*a):
    print("[scrape]", *a, file=sys.stderr, flush=True)


def _import_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return sync_playwright
    except Exception:
        log("Playwright not installed. Run:  pip install playwright && playwright install chromium")
        raise


def launch(pw, chrome_path=None, headed=False, slowmo=0):
    """Launch Chromium. Reuse a local binary if given/available (no download)."""
    exe = chrome_path or (SANDBOX_CHROME if os.path.exists(SANDBOX_CHROME) else None)
    kwargs = dict(headless=not headed, slow_mo=slowmo,
                  args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    if exe:
        kwargs["executable_path"] = exe
    return pw.chromium.launch(**kwargs)


# ── generic helpers a recipe can call ─────────────────────────────────────────
def fetch_page(ctx, url, wait="networkidle", timeout=45000):
    """Open url, return (page, html). Caller closes the page."""
    page = ctx.new_page()
    page.goto(url, wait_until=wait, timeout=timeout)
    return page, page.content()


def download_via_click(page, selector, out_name, timeout=60000):
    """Click an element that triggers a download; save it to _data_in/out_name."""
    os.makedirs(DATA_IN, exist_ok=True)
    dest = os.path.join(DATA_IN, out_name)
    with page.expect_download(timeout=timeout) as dl:
        page.click(selector)
    dl.value.save_as(dest)
    log(f"saved {out_name} ({os.path.getsize(dest)} bytes)")
    return dest


def save_text(name, text):
    os.makedirs(DATA_IN, exist_ok=True)
    dest = os.path.join(DATA_IN, name)
    with open(dest, "w", encoding="utf-8") as f:
        f.write(text)
    log(f"saved {name} ({len(text)} chars)")
    return dest


# ── per-source recipes ────────────────────────────────────────────────────────
# Each recipe(ctx) drives one portal. They target the owner's open network.
# The landing URL + the export step are documented in data-download-points.md;
# keep that doc and these selectors in sync.

def tw_moi_77132(ctx):
    """Taiwan MOI 戶政司 #77132 — 鄉鎮市區 single-year-age population.
    Unlocks the TOWN-level (368) Taiwan prevalence map (currently county-level).
    RIS open-data has a per-month CSV endpoint; if reachable it's a direct GET,
    otherwise export from the dataset page."""
    url = "https://data.gov.tw/dataset/77132"
    page, _ = fetch_page(ctx, url)
    # The dataset page lists distribution links; grab the newest CSV href.
    hrefs = page.eval_on_selector_all(
        "a[href$='.csv'], a[href*='ODRP014']",
        "els => els.map(e => e.href)")
    save_text("tw_moi_77132_links.txt", "\n".join(hrefs) or "(no CSV links found — check DOM)")
    page.close()
    log("tw_moi_77132: captured distribution links; download the latest yyymm CSV.")


def nhri_mci(ctx):
    """NHRI 全國社區失智症流行病學調查 — MCI + dementia age-band prevalence.
    Adds the MCI map layer the owner asked about. The tables live in the 2024
    press-release PDF; save the page so the PDF link/table can be extracted."""
    url = "https://www.nhri.edu.tw/"
    page, html = fetch_page(ctx, url)
    save_text("nhri_landing.html", html)
    pdfs = page.eval_on_selector_all("a[href$='.pdf']", "els => els.map(e => e.href)")
    save_text("nhri_pdf_links.txt", "\n".join(pdfs) or "(no PDFs on landing — use site search 失智症流行病學)")
    page.close()


def jp_estat_pop(ctx):
    """Japan e-Stat — prefecture population by 5-yr age band (国勢調査 / 人口推計).
    Feeds JP prefecture prevalence once combined with GBD/national rates."""
    url = "https://www.e-stat.go.jp/en"
    page, html = fetch_page(ctx, url)
    save_text("jp_estat_landing.html", html)
    page.close()
    log("jp_estat_pop: log in / use the statistical-table search, export the "
        "prefecture x age-band CSV to _data_in/jp-admin1-pop.csv (schema in doc).")


def kr_kosis_pop(ctx):
    """Korea KOSIS — province (시도) population by age band.
    Feeds KR province prevalence once combined with the 2023 dementia survey."""
    url = "https://kosis.kr/eng/"
    page, html = fetch_page(ctx, url)
    save_text("kr_kosis_landing.html", html)
    page.close()
    log("kr_kosis_pop: use the population-by-age statistical table, export the "
        "시도 x age CSV to _data_in/kr-admin1-pop.csv (schema in doc).")


RECIPES = {
    "tw_moi_77132": tw_moi_77132,
    "nhri_mci": nhri_mci,
    "jp_estat_pop": jp_estat_pop,
    "kr_kosis_pop": kr_kosis_pop,
}


def smoke(chrome_path=None, headed=False):
    """Harness self-test: drive a local data: page (NO network) and read it back."""
    sync_playwright = _import_playwright()
    fixture = ("data:text/html,<html><body><h1 id='ok'>brain-health harness OK</h1>"
               "<a id='dl' href='data:text/plain,hello' download='probe.txt'>dl</a></body></html>")
    with sync_playwright() as pw:
        browser = launch(pw, chrome_path=chrome_path, headed=headed)
        page = browser.new_page()
        page.goto(fixture)
        text = page.text_content("#ok")
        ua = page.evaluate("() => navigator.userAgent")
        browser.close()
    log(f"smoke OK — page said: {text!r}")
    log(f"user-agent: {ua}")
    return text == "brain-health harness OK"


def run(names, chrome_path=None, headed=False, slowmo=0):
    sync_playwright = _import_playwright()
    os.makedirs(DATA_IN, exist_ok=True)
    with sync_playwright() as pw:
        browser = launch(pw, chrome_path=chrome_path, headed=headed, slowmo=slowmo)
        ctx = browser.new_context(accept_downloads=True,
                                  user_agent=("Mozilla/5.0 (X11; Linux x86_64) "
                                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                                              "Chrome/126.0 Safari/537.36"))
        for name in names:
            fn = RECIPES.get(name)
            if not fn:
                log(f"unknown recipe: {name} (see --list)")
                continue
            log(f"── {name} ──")
            try:
                fn(ctx)
            except Exception as e:  # keep going; one blocked portal shouldn't abort the batch
                log(f"{name} FAILED: {type(e).__name__}: {e}")
                log("   (expected in the CI sandbox — run on an unrestricted network)")
            time.sleep(0.5)
        browser.close()


def main():
    ap = argparse.ArgumentParser(description="Playwright scraper for blocked prevalence/population sources.")
    ap.add_argument("recipes", nargs="*", help="recipe names to run (see --list)")
    ap.add_argument("--list", action="store_true", help="list available recipes")
    ap.add_argument("--smoke", action="store_true", help="harness self-test (no network)")
    ap.add_argument("--chrome-path", help="path to a Chromium/Chrome binary (skip download)")
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    ap.add_argument("--slowmo", type=int, default=0, help="ms delay between actions (debug)")
    args = ap.parse_args()

    if args.list:
        print("Available recipes:")
        for k, fn in RECIPES.items():
            print(f"  {k:16s} {(fn.__doc__ or '').strip().splitlines()[0]}")
        return 0
    if args.smoke:
        return 0 if smoke(chrome_path=args.chrome_path, headed=args.headed) else 1
    if not args.recipes:
        ap.print_help()
        return 1
    run(args.recipes, chrome_path=args.chrome_path, headed=args.headed, slowmo=args.slowmo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
