#!/usr/bin/env python3
"""Literature radar for the brain-exposome map.

For each watch-topic in ``scripts/literature-watch.json`` it queries the
**Europe PMC** REST API (free, no key; indexes PubMed + PMC + preprints) for
papers published in the last ``days_window`` days, and lists them as *candidates*
for a human to judge — never auto-ingests. TITLE-scoped queries keep the noise
down (a naive "dementia prevalence" search returns hundreds/month; the tuned
title queries return a handful).

Optional ``--triage``: if any LLM provider key is set (see scripts/llm_triage.py —
NVIDIA NIM → Groq → Cloudflare fallback, ported from the dreamcatcher ai-worker),
each candidate is scored keep/drop and the drops are collapsed. Fail-open: with no
keys, or on any error, everything is kept (identical to the keyless behaviour).

Stdlib only. Robust: a topic whose query fails is reported as "could not check".

Usage:
  python scripts/literature_watch.py --out report.md --append           # keyless
  python scripts/literature_watch.py --out report.md --append --triage   # + LLM filter
"""
import argparse
import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import llm_triage

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, "literature-watch.json")
UA = {"User-Agent": "brain-exposome-litwatch/1.1 (mailto:a0972210123@gmail.com)"}
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
TIMEOUT = 30


def epmc_search(query, since_iso, until_iso, page_size):
    full = f"({query}) AND (FIRST_PDATE:[{since_iso} TO {until_iso}])"
    params = urllib.parse.urlencode({
        "query": full, "format": "json", "pageSize": str(page_size),
        "sort": "P_PDATE_D desc", "resultType": "core",   # core → includes abstractText for triage
    })
    req = urllib.request.Request(f"{EPMC}?{params}", headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    return d.get("hitCount", 0), d.get("resultList", {}).get("result", [])


def journal_of(rec):
    return (rec.get("journalTitle")
            or (rec.get("journalInfo") or {}).get("journal", {}).get("title")
            or (rec.get("bookOrReportDetails") or {}).get("publisher")
            or "preprint/other")


def link_for(rec):
    if rec.get("doi"):
        return f"https://doi.org/{rec['doi']}"
    src, rid = rec.get("source"), rec.get("id")
    return f"https://europepmc.org/article/{src}/{rid}" if src and rid else ""


def line_for(rec, verdict=None):
    title = (rec.get("title") or "").rstrip(".")
    url = link_for(rec)
    cite = f"[{title}]({url})" if url else title
    tag = f" — _{verdict['reason']}_" if verdict and verdict.get("reason") else ""
    return f"- {rec.get('firstPublicationDate', '?')} · *{journal_of(rec)}* — {cite}{tag}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--triage", action="store_true", help="LLM keep/drop filter if provider keys are set")
    args = ap.parse_args()

    cfg = json.load(open(CONFIG, encoding="utf-8"))
    window = int(cfg.get("days_window", 45))
    per_topic = int(cfg.get("max_per_topic", 6))
    until = datetime.date.today()
    since = until - datetime.timedelta(days=window)
    since_iso, until_iso = since.isoformat(), until.isoformat()

    do_triage = args.triage and llm_triage.available()

    L = [f"## 📚 New literature — last {window} days ({since_iso} → {until_iso})\n"]
    L.append("Candidate papers for the figures the map uses (Europe PMC, TITLE-scoped). "
             "**For review, not auto-ingested** — if one updates a number we use, follow "
             "extract→review→register.")
    # Filled in after the loop — the header has to name the model that actually
    # answered, and that is not known until the first verdict comes back. Claiming
    # "LLM-triaged" when every tier silently failed is the failure mode worth
    # designing against: the run still succeeds and filters nothing.
    triage_line = len(L)
    L.append("")
    triaged_by = set()
    triage_tried = 0      # a quiet month has nothing to score — not the same as a broken chain

    total_keep = 0
    for t in cfg["topics"]:
        label = t["label"]
        try:
            hits, results = epmc_search(t["query"], since_iso, until_iso, per_topic)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError) as e:
            L.append(f"### {label}\n- ⚠️ could not check ({type(e).__name__})\n")
            continue

        keeps, drops = [], []
        for r in results:
            v = None
            if do_triage:
                triage_tried += 1
                v = llm_triage.triage(r.get("title", ""), r.get("abstractText", ""))
                if v:
                    triaged_by.add(f"{v.get('tier', '?')}/`{v.get('model', '?')}`")
                time.sleep(1)                      # gentle pacing for free-tier TPM
            if v and v.get("verdict") == "drop":
                drops.append(line_for(r, v))
            else:
                keeps.append(line_for(r, v))
        total_keep += len(keeps)

        if keeps:
            L.append(f"### {label} — {hits} new" + (f", {len(keeps)} kept" if do_triage else ""))
            L.extend(keeps)
            if drops:
                L.append(f"\n<details><summary>{len(drops)} filtered out by triage</summary>\n")
                L.extend(drops)
                L.append("\n</details>")
            L.append("")
        elif drops:
            L.append(f"### {label} — {hits} new, 0 kept")
            L.append(f"<details><summary>{len(drops)} filtered out by triage</summary>\n")
            L.extend(drops)
            L.append("\n</details>\n")
        else:
            L.append(f"### {label}\n- none in the last {window} days\n")

        if t.get("manual_also"):
            L.append(f"  <sub>↳ {t.get('note', '')}</sub>")
            for m in t["manual_also"]:
                L.append(f"  - 🔎 manual: {m}")
            L.append("")

    if not do_triage:
        L[triage_line] = "_Keyless: all candidates listed (set provider secrets + `--triage` to filter)._\n"
    elif triaged_by:
        L[triage_line] = f"_🤖 LLM-triaged by {', '.join(sorted(triaged_by))}; drops are collapsed._\n"
    elif not triage_tried:
        L[triage_line] = "_🤖 Triage is on, but there was nothing to score this month._\n"
    else:
        L[triage_line] = ("_⚠️ **Triage was requested but every provider failed** — nothing was "
                          "filtered and every candidate below is listed. Check the provider keys "
                          "and `scripts/llm_triage.py`._\n")

    L.append(f"> {total_keep} candidate(s) to review across {len(cfg['topics'])} topics. "
             "Queries live in `scripts/literature-watch.json`.")

    report = "\n".join(L)
    if args.out:
        with open(args.out, "a" if args.append else "w", encoding="utf-8") as f:
            if args.append:
                f.write("\n\n---\n\n")
            f.write(report)
    else:
        sys.stdout.buffer.write(report.encode("utf-8"))
    print(f"\n[litwatch] {total_keep} kept across {len(cfg['topics'])} topics "
          f"({since_iso}→{until_iso}) triage={'on' if do_triage else 'off'}", file=sys.stderr)


if __name__ == "__main__":
    main()
