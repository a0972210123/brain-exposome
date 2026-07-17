# Literature candidates — papers to review for possible ingestion

Seeded 2026-07-18 from the first literature-radar sweep (see `scripts/literature_watch.py`).
These are **candidates only** — a human decides whether any of them updates a figure the map
uses. When one is adopted, follow extract → review → register (bump `scripts/data-versions.json`)
and move it to "adopted" below. Going forward the monthly Action appends fresh candidates to its
issue; this file is the curated backlog.

## To review

| Paper | Date | Journal | Which figure it might touch | DOI |
|---|---|---|---|---|
| Differences in the prevalence and patterns of dementia risk factors across **14 countries and regions**: a harmonised cross-national analysis | 2026-07 | Lancet Healthy Longev | **Risk-factor prevalence / PAF layer** — cross-national, harmonised; most directly relevant | [10.1016/j.lanhl.2026.100867](https://doi.org/10.1016/j.lanhl.2026.100867) |
| Long-Term Exposure to PM2.5 and Risk of Incident Dementia: A Systematic Review and Meta-Analysis | 2026-05 | (systematic review) | **PM2.5 → dementia HR** (we use ≈ HR 1.08 per +5 µg/m³) | search: EuropePMC "PM2.5 incident dementia meta-analysis 2026" |
| Global burden of young-onset dementia and the forecast for 2050 (GBD update) | 2026-03 | (GBD analysis) | **Dementia prevalence / burden** context (young-onset) | search: EuropePMC "young-onset dementia 2050 forecast" |
| Estimates of Incidence and Prevalence of Conversions to MCI and Dementia … | 2026-07 | Neurology | **MCI** — conversion rates (niche: essential tremor cohort) | [10.1212/wnl.0000000000218283](https://doi.org/10.1212/wnl.0000000000218283) |
| Reassessing / Broadening the 2024 Lancet Commission dementia-risk model (several 2025 papers) | 2025 | various | **Lancet Commission RRs / risk model** — heads-up, not a new Commission | search: EuropePMC TITLE:"Lancet Commission" AND TITLE:dementia |

## Adopted

_(none yet)_

## Notes
- The PAF layer's backbone is still Livingston 2024; a new **Lancet Commission** (not just papers *about* it) would be the trigger to revise RRs.
- Taiwan-specific studies land under the `taiwan_cognitive` watch topic because Taiwan is excluded from GBD/WHO/World Bank — see `scripts/literature-watch.json`.
