#!/usr/bin/env python3
"""Monthly data-freshness check for the brain-exposome map.

Compares the live *API* upstream sources (World Bank, WHO GHO) against the
recorded baselines in ``scripts/data-versions.json`` and lists the *manual*
sources (NCD-RisC / GBD / ACAG / papers) for a human glance. Emits a Markdown
report the GitHub Action turns into an issue.

Stdlib only (urllib/json) so CI needs no pip install. Never hard-fails on a
network hiccup — a source that can't be reached is reported as "could not check".

Usage:  python scripts/check_data_freshness.py --out report.md
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
VERSIONS = os.path.join(HERE, "data-versions.json")
UA = {"User-Agent": "brain-exposome-data-refresh/1.0 (+https://brain-exposome.mattye.dev)"}
TIMEOUT = 30


def _get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def wb_latest_year(indicator):
    """World Bank: most-recent value year for the World (WLD) aggregate."""
    url = f"https://api.worldbank.org/v2/country/WLD/indicator/{indicator}?format=json&mrv=1"
    d = _get_json(url)
    if isinstance(d, list) and len(d) > 1 and d[1]:
        return int(d[1][0]["date"])
    return None


def gho_latest_year(indicator, this_year):
    """WHO GHO OData: latest OBSERVED year (drop future projections above this year)."""
    d = _get_json(f"https://ghoapi.azureedge.net/api/{indicator}")
    years = [v.get("TimeDim") for v in d.get("value", []) if isinstance(v.get("TimeDim"), int)]
    years = [y for y in years if y <= this_year]
    return max(years) if years else None


def check_api(key, src, this_year):
    """Return (status, latest, note). status ∈ {'update','ok','error'}."""
    cur = src.get("current_year")
    try:
        if src["api"] == "worldbank":
            latest = wb_latest_year(src["indicator"])
        elif src["api"] == "gho":
            latest = gho_latest_year(src["indicator"], this_year)
        else:
            return "error", None, f"unknown api '{src['api']}'"
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, KeyError, TimeoutError) as e:
        return "error", None, f"could not check ({type(e).__name__})"
    if latest is None:
        return "error", None, "no year returned"
    if cur is None or latest > cur:
        return "update", latest, ""
    return "ok", latest, ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="", help="write the Markdown report here (else stdout)")
    args = ap.parse_args()

    reg = json.load(open(VERSIONS, encoding="utf-8"))
    sources = reg["sources"]
    this_year = datetime.date.today().year
    today = datetime.date.today().isoformat()

    updates, oks, errors, manual = [], [], [], []
    for key, src in sources.items():
        if src.get("mode") == "api":
            status, latest, note = check_api(key, src, this_year)
            row = (src["label"], src.get("current_year"), latest, src["url"], note)
            (updates if status == "update" else oks if status == "ok" else errors).append(row)
        else:
            manual.append((src["label"], src.get("current_version") or src.get("current_year"), src["url"]))

    L = []
    L.append(f"## 🔄 Monthly data-freshness check — {today}\n")
    L.append("Automated check of the upstream sources behind the brain-exposome map. "
             "API sources (World Bank, WHO GHO) are compared to `scripts/data-versions.json`; "
             "the manual sources are listed for a human glance.\n")

    if updates:
        L.append(f"### 🔔 {len(updates)} API source(s) have NEWER data\n")
        L.append("| Source | Recorded | Live latest | Link |")
        L.append("|---|---|---|---|")
        for label, cur, latest, url, _ in updates:
            L.append(f"| {label} | {cur} | **{latest}** | [source]({url}) |")
        L.append("")
    else:
        L.append("### ✅ No API source has newer data than what's recorded.\n")

    if oks:
        L.append("<details><summary>✅ API sources up to date</summary>\n")
        for label, cur, latest, url, _ in oks:
            L.append(f"- {label} — latest {latest} (recorded {cur})")
        L.append("\n</details>\n")

    if errors:
        L.append("### ⚠️ Could not check (network / API)\n")
        for label, cur, latest, url, note in errors:
            L.append(f"- {label} — {note} · [source]({url})")
        L.append("")

    L.append("### 🔍 Manual sources — check these pages for a new release\n")
    L.append("These have no version API; skim each once (releases are infrequent):\n")
    for label, cur, url in manual:
        L.append(f"- {label} — currently `{cur}` · [check for updates]({url})")
    L.append("")

    L.append("### ▶️ If something is new — the flow\n")
    L.append("1. **Extract & consolidate** — download / fetch the new source into "
             "`scripts/_data_in/` (local, gitignored for the manual ones), then run "
             "`python scripts/build_data.py` to regenerate `public/data/`.")
    L.append("2. **Review** — open a PR with the regenerated derived assets; check the "
             "method boxes / references still read correctly.")
    L.append("3. **Register** — bump the matching `current_year` / `current_version` in "
             "`scripts/data-versions.json` **in that same PR** so this check goes quiet again.")
    L.append("\n> API layers (World Bank aging, WHO GHO smoking/inactivity) fetch directly and "
             "can be regenerated in CI; the manual layers (NCD-RisC, GBD, ACAG, papers) still "
             "need a human download step — see `docs/dementia-exposome/data-refresh-workflow.md`.")
    L.append("\ncc @a0972210123")

    report = "\n".join(L)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))

    # machine-readable signal for the workflow
    has_updates = "true" if updates else "false"
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a", encoding="utf-8") as f:
            f.write(f"has_updates={has_updates}\n")
            f.write(f"n_updates={len(updates)}\n")
    print(f"\n[freshness] api-updates={len(updates)} ok={len(oks)} errors={len(errors)} manual={len(manual)}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
