#!/usr/bin/env python3
"""Tier-2 aging: India admin-1 65+ % from Census 2011 table C-14 (population in five-year age groups by
state, DDW-0000C-14.xls). Per state: (65-69 + 70-74 + 75-79 + 80+) / All ages, Total-Persons column.

The 2011 census predates three boundary changes the map's geojson reflects, so a few census state codes
fan out to two ISO units (same rate applied flat):
  code 01 Jammu & Kashmir  -> IN-JK + IN-LA (Ladakh split 2019)
  code 28 Andhra Pradesh   -> IN-AP + IN-TG (Telangana split 2014)
  codes 25 Daman & Diu + 26 Dadra & Nagar Haveli -> IN-DH (merged UT 2020; pop-weighted)
Writes public/data/aging/in-admin1.json."""
import json
import os
import xlrd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'public', 'data', 'aging'))
SRC = os.path.join(HERE, '_data_in', 'in', 'DDW-0000C-14.xls')

OLD = {'65-69', '70-74', '75-79', '80+'}
CODE2ISO = {
    '01': ['IN-JK', 'IN-LA'], '02': ['IN-HP'], '03': ['IN-PB'], '04': ['IN-CH'], '05': ['IN-UT'],
    '06': ['IN-HR'], '07': ['IN-DL'], '08': ['IN-RJ'], '09': ['IN-UP'], '10': ['IN-BR'],
    '11': ['IN-SK'], '12': ['IN-AR'], '13': ['IN-NL'], '14': ['IN-MN'], '15': ['IN-MZ'],
    '16': ['IN-TR'], '17': ['IN-ML'], '18': ['IN-AS'], '19': ['IN-WB'], '20': ['IN-JH'],
    '21': ['IN-OR'], '22': ['IN-CT'], '23': ['IN-MP'], '24': ['IN-GJ'], '25': ['IN-DH'],
    '26': ['IN-DH'], '27': ['IN-MH'], '28': ['IN-AP', 'IN-TG'], '29': ['IN-KA'], '30': ['IN-GA'],
    '31': ['IN-LD'], '32': ['IN-KL'], '33': ['IN-TN'], '34': ['IN-PY'], '35': ['IN-AN'],
}

s = xlrd.open_workbook(SRC).sheet_by_index(0)
acc = {}   # ISO -> [total, 65plus]  (fan-out targets accumulate independently; IN-DH gets 25+26)
for r in range(7, s.nrows):
    code = str(s.cell_value(r, 1)).strip()
    if code not in CODE2ISO:   # skips '00' India total + any stray rows
        continue
    age = str(s.cell_value(r, 4)).strip()
    val = s.cell_value(r, 5)
    if not isinstance(val, (int, float)):
        continue
    for iso in CODE2ISO[code]:
        a = acc.setdefault(iso, [0, 0])
        if age == 'All ages':
            a[0] += val
        elif age in OLD:
            a[1] += val

by_unit = {iso: round(100 * o65 / tot, 1) for iso, (tot, o65) in acc.items() if tot}
vals = list(by_unit.values())
nat = round(sum(vals) / len(vals), 1)
os.makedirs(OUT, exist_ok=True)
json.dump({'meta': {'metric': 'share of population aged 65+ (%)', 'age_group': '65+', 'year': 2011,
                    'source': 'Census of India 2011, table C-14 (five-year age groups by state)', 'resolution': 'admin-1',
                    'method': '(65-69+70-74+75-79+80+)/all-ages per state; census code -> ISO-3166-2:IN (pre-2014 units fanned out)',
                    'national_pct_unweighted': nat},
           'byUnit': by_unit},
          open(os.path.join(OUT, 'in-admin1.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(f'in: {len(by_unit)} units, range {min(vals)}-{max(vals)}%, nat {nat}')
