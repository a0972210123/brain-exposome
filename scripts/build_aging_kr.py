#!/usr/bin/env python3
"""Tier-2 aging: Korea admin-1 65+ % from KOSIS DT_1YL20631 (고령인구비율, latest month, sido level).
Maps Korean sido name -> ISO-3166-2:KR. The KOSIS extract merges Gwangju+Jeonnam into one
'전남광주통합특별시' row; applying that to Gwangju would badly overstate it, so KR-29/KR-46 are left
for the Tier-0 national fallback. Writes public/data/aging/kr-admin1.json."""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'public', 'data'))
SRC = os.path.join(HERE, '_data_in', 'kr', '고령인구비율_시도_시_군_구__20260831201805.csv')

# Korean sido name -> ISO-3166-2:KR
ISO = {
    '서울특별시': 'KR-11', '부산광역시': 'KR-26', '대구광역시': 'KR-27', '인천광역시': 'KR-28',
    '대전광역시': 'KR-30', '울산광역시': 'KR-31', '세종특별자치시': 'KR-50', '경기도': 'KR-41',
    '강원특별자치도': 'KR-42', '충청북도': 'KR-43', '충청남도': 'KR-44', '전북특별자치도': 'KR-45',
    '경상북도': 'KR-47', '경상남도': 'KR-48', '제주특별자치도': 'KR-49',
    # '전남광주통합특별시' -> Gwangju+Jeonnam merged; skip (Tier-0 fallback for KR-29 / KR-46)
}

rows = list(csv.reader(open(SRC, encoding='euc-kr')))
sido = [r for r in rows[2:] if len(r) > 15 and r[1].strip() == '소계']
by_unit = {}
for r in sido:
    name = r[0].split(' ', 1)[1].strip() if ' ' in r[0] else r[0].strip()   # strip 'NN ' code prefix
    iso = ISO.get(name)
    if not iso:
        continue
    try:
        by_unit[iso] = float(r[15])   # col 15 = latest month (2026.07) 고령인구비율 %
    except ValueError:
        pass

vals = list(by_unit.values())
nat = round(sum(vals) / len(vals), 1)
os.makedirs(os.path.join(OUT, 'aging'), exist_ok=True)
json.dump({'meta': {'metric': 'share of population aged 65+ (%)', 'age_group': '65+', 'year': 2026,
                    'source': 'KOSIS 고령인구비율 (DT_1YL20631), 2026-07', 'resolution': 'admin-1',
                    'method': '65+ ratio published by sido; Korean name -> ISO-3166-2:KR', 'national_pct_unweighted': nat},
           'byUnit': by_unit},
          open(os.path.join(OUT, 'aging', 'kr-admin1.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print(f'kr: {len(by_unit)} sido, range {min(vals)}-{max(vals)}%, nat {nat}')
