#!/usr/bin/env python3
"""Literature radar for the brain-exposome map (keyless, v1).

For each watch-topic in ``scripts/literature-watch.json`` it queries the
**Europe PMC** REST API (free, no key; indexes PubMed + PMC + preprints) for
papers published in the last ``days_window`` days, and lists them as *candidates*
for a human to judge — never auto-ingests. TITLE-scoped queries keep the noise
down (a naive "dementia prevalence" search returns hundreds/month; the tuned
title queries return a handful).

Stdlib only. Robust: a topic whose query fails is reported as "could not check".

Usage:
  python scripts/literature_watch.py --out report.md            # write section
  python scripts/literature_watch.py --out report.md --append   # append section
"""
import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "literature-watch.json")
UA = {"User-Agent": "brain-exposome-litwatch/1.0 (mailto:a0972210123@gmail.com)"}
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TIMEOUT = 30


def epmc_search(query, since_iso, until_iso, page_size):
    date_clause = f'(FIRST_PDATE:[{since_iso} TO {until_iso}])'
    full = f"({query}) AND {date_clause}"
    params = urllib.parse.urlencode({
        "query": full, "format": "json", "pageSize": str(page_size),
        "sort": "P_PDATE_D desc", "resultType": "lite",
    })
    req = urllib.request.Request(f"{EPMC}?{params}", headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    return d.get("hitCount", 0), d.get("resultList", {}).get("result", [])


def link_for(rec):
    doi = rec.get("doi")
    if doi:
        return f"https://doi.org/{doi}"
    src, rid = rec.get("source"), rec.get("id")
    if src and rid:
        return f"https://europepmc.org/article/{src}/{rid}"
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="", help="write report here (else stdout)")
    ap.add_argument("--append", action="store_true", help="append instead of overwrite")
    args = ap.parse_args()

    cfg = json.load(open(CONFIG, encoding="utf-8"))
    window = int(cfg.get("days_window", 45))
    per_topic = int(cfg.get("max_per_topic", 6))
    until = datetime.date.today()
    since = until - datetime.timedelta(days=window)
    since_iso, until_iso = since.isoformat(), until.isoformat()

    L = [f"## 📚 New literature — last {window} days ({since_iso} → {until_iso})\n"]
    L.append("Candidate papers for the figures the map uses (Europe PMC, TITLE-scoped). "
             "These are **for review, not auto-ingested** — skim, and if one updates a number "
             "we use, follow the extract→review→register flow.\n")

    total_new = 0
    for t in cfg["topics"]:
        label = t["label"]
        try:
            hits, results = epmc_search(t["query"], since_iso, until_iso, per_topic)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
            L.append(f"### {label}\n- ⚠️ could not check ({type(e).__name__})\n")
            continue
        total_new += len(results)
        if results:
            L.append(f"### {label} — {hits} new")
            for r in results:
                title = (r.get("title") or "").rstrip(".")
                date = r.get("firstPublicationDate", "?")
                journal = r.get("journalTitle") or r.get("bookOrReportDetails", {}).get("publisher", "") or "preprint/other"
                url = link_for(r)
                cite = f"[{title}]({url})" if url else title
                L.append(f"- {date} · *{journal}* — {cite}")
            L.append("")
        else:
            L.append(f"### {label}\n- none in the last {window} days\n")
        if t.get("manual_also"):
            L.append(f"  <sub>↳ {t.get('note','')}</sub>")
            for m in t["manual_also"]:
                L.append(f"  - 🔎 manual: {m}")
            L.append("")

    L.append(f"> {total_new} candidate(s) across {len(cfg['topics'])} topics. "
             "Queries live in `scripts/literature-watch.json` — tune them there.")

    report = "\n".join(L)
    if args.out:
        mode = "a" if args.append else "w"
        with open(args.out, mode, encoding="utf-8") as f:
            if args.append:
                f.write("\n\n---\n\n")
            f.write(report)
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))
    print(f"\n[litwatch] {total_new} candidates across {len(cfg['topics'])} topics "
          f"({since_iso}→{until_iso})", file=sys.stderr)


if __name__ == "__main__":
    main()
