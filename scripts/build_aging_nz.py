#!/usr/bin/env python3
"""Tier-2 aging: New Zealand admin-1 65+ % from Stats NZ Subnational population estimates (Table 3:
regional council areas by broad age group, 30 June 2025). 65+ / Total per region. Maps region name ->
ISO-3166-2:NZ. Writes public/data/aging/nz-admin1.json."""
import json
import os
import unicodedata
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'public', 'data'))
SRC = os.path.join(HERE, '_data_in', 'nz', 'subnational-population-estimates-at-30-june-2025-provisional.xlsx')
YEAR = '2025 P'   # col2; latest provisional
C_65, C_TOTAL = 6, 7

def norm(s):
    s = unicodedata.normalize('NFD', str(s)).encode('ascii', 'ignore').decode().lower()
    s = s.replace('region', '')
    return ''.join(c for c in s if c.isalnum())

ISO = {norm(k): v for k, v in {
    'Northland': 'NZ-NTL', 'Auckland': 'NZ-AUK', 'Waikato': 'NZ-WKO', 'Bay of Plenty': 'NZ-BOP',
    'Gisborne': 'NZ-GIS', "Hawke's Bay": 'NZ-HKB', 'Taranaki': 'NZ-TKI', 'Manawatu-Whanganui': 'NZ-MWT',
    'Wellington': 'NZ-WGN', 'Tasman': 'NZ-TAS', 'Nelson': 'NZ-NSN', 'Marlborough': 'NZ-MBH',
    'West Coast': 'NZ-WTC', 'Canterbury': 'NZ-CAN', 'Otago': 'NZ-OTA', 'Southland': 'NZ-STL',
}.items()}

ws = openpyxl.load_workbook(SRC, read_only=True, data_only=True)['Table 3']
by_unit, miss = {}, []
for r in ws.iter_rows(values_only=True):
    if len(r) <= C_TOTAL or str(r[2]).strip() != YEAR:
        continue
    iso = ISO.get(norm(r[0]))
    o65, tot = r[C_65], r[C_TOTAL]
    if iso and isinstance(o65, (int, float)) and isinstance(tot, (int, float)) and tot:
        by_unit[iso] = round(100 * o65 / tot, 1)
    elif r[0] and norm(r[0]) not in ('totalnewzealand', 'areaoutsidenz', 'newzealand') and not iso and isinstance(o65, (int, float)):
        miss.append(str(r[0]))

vals = list(by_unit.values())
nat = round(sum(vals) / len(vals), 1)
os.makedirs(os.path.join(OUT, 'aging'), exist_ok=True)
json.dump({'meta': {'metric': 'share of population aged 65+ (%)', 'age_group': '65+', 'year': 2025,
                    'source': 'Stats NZ subnational population estimates, 30 June 2025 (Table 3)', 'resolution': 'admin-1',
                    'method': '65+ / total ERP per regional council area; name -> ISO-3166-2:NZ', 'national_pct_unweighted': nat},
           'byUnit': by_unit},
          open(os.path.join(OUT, 'aging', 'nz-admin1.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(f'nz: {len(by_unit)} regions, range {min(vals)}-{max(vals)}%, nat {nat}' + (f' | MISS {set(miss)}' if miss else ''))
