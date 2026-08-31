#!/usr/bin/env python3
"""Tier-2 aging: Taiwan admin-1 (township) 65+ % from MOI #77132 single-year-age village data.
Aggregate villages -> township (first 8 digits of 區域別代碼): 65+ = sum(age 65..100+ both sexes) /
total (人口數). Township-level (finest resolution). Writes public/data/aging/tw-admin1.json."""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'public', 'data'))
SRC = os.path.join(HERE, '_data_in', 'tw', 'opendata10703M030.csv')

rows = list(csv.reader(open(SRC, encoding='utf-8-sig')))
H = rows[0]
i_code = H.index('區域別代碼')
i_total = H.index('人口數')
i_65m = H.index('65歲-男')   # 65+ = this col through the last col (100歲以上-女)

town = {}   # 8-digit township code -> [total, 65plus]
for r in rows[1:]:
    if len(r) <= i_65m:
        continue
    code = r[i_code][:8]
    try:
        total = int(r[i_total])
        o65 = sum(int(x) for x in r[i_65m:] if x.strip().lstrip('-').isdigit())
    except (ValueError, IndexError):
        continue
    t = town.setdefault(code, [0, 0])
    t[0] += total
    t[1] += o65

by_unit = {}
for code, (total, o65) in town.items():
    if total:
        by_unit[code] = round(100 * o65 / total, 1)

vals = list(by_unit.values())
nat = round(sum(vals) / len(vals), 1)
os.makedirs(os.path.join(OUT, 'aging'), exist_ok=True)
json.dump({'meta': {'metric': 'share of population aged 65+ (%)', 'age_group': '65+', 'year': 2018,
                    'source': 'MOI 內政部戶政司 #77132 (village single-year age, 107/03)', 'resolution': 'township',
                    'method': '65+ / total per township, villages aggregated by 8-digit code', 'national_pct_unweighted': nat},
           'byUnit': by_unit},
          open(os.path.join(OUT, 'aging', 'tw-admin1.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(f'tw: {len(by_unit)} townships, range {min(vals)}-{max(vals)}%, nat {nat}')
