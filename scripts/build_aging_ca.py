#!/usr/bin/env python3
"""Tier-2 aging: Canada admin-1 65+ % from StatCan table 17-10-0005 (population by age).
Downloads the full-table CSV zip, computes 65+ / all-ages share per province for the latest
year, maps StatCan GEO -> ISO-3166-2, writes public/data/aging/ca-admin1.json."""
import csv
import io
import json
import os
import urllib.request
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, '..', 'public', 'data'))
CACHE = os.path.join(HERE, '_data_in', 'statcan')
ZIP_URL = 'https://www150.statcan.gc.ca/n1/tbl/csv/17100005-eng.zip'

GEO_ISO = {
    'newfoundland and labrador': 'CA-NL', 'prince edward island': 'CA-PE', 'nova scotia': 'CA-NS',
    'new brunswick': 'CA-NB', 'quebec': 'CA-QC', 'ontario': 'CA-ON', 'manitoba': 'CA-MB',
    'saskatchewan': 'CA-SK', 'alberta': 'CA-AB', 'british columbia': 'CA-BC', 'yukon': 'CA-YT',
    'northwest territories': 'CA-NT', 'nunavut': 'CA-NU',
}


def fetch_zip():
    os.makedirs(CACHE, exist_ok=True)
    fp = os.path.join(CACHE, '17100005-eng.zip')
    if not (os.path.exists(fp) and os.path.getsize(fp) > 0):
        req = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'brain-exposome/aging'})
        with urllib.request.urlopen(req, timeout=180) as r, open(fp, 'wb') as f:
            f.write(r.read())
    return fp


def main():
    zf = zipfile.ZipFile(fetch_zip())
    name = [n for n in zf.namelist() if n.lower().endswith('.csv') and 'metadata' not in n.lower()][0]
    rdr = csv.DictReader(io.TextIOWrapper(zf.open(name), encoding='utf-8-sig'))
    cols = rdr.fieldnames
    # locate columns (names vary slightly)
    c_year = next(c for c in cols if c.strip().upper() == 'REF_DATE')
    c_geo = next(c for c in cols if c.strip().upper() == 'GEO')
    c_age = next(c for c in cols if 'age' in c.lower() and 'group' in c.lower())
    c_sex = next((c for c in cols if c.strip().lower() in ('gender', 'sex')), None)
    c_val = next(c for c in cols if c.strip().upper() == 'VALUE')

    # keep only the latest year, gender=total, provinces we map; capture 65+ and all-ages
    rows = {}   # geo -> {'all':x, '65':y}
    latest = ''
    ages_seen, sex_seen = set(), set()
    for row in rdr:
        yr = row[c_year].strip()
        if yr > latest:
            latest = yr
    zf2 = zipfile.ZipFile(fetch_zip())
    rdr = csv.DictReader(io.TextIOWrapper(zf2.open(name), encoding='utf-8-sig'))
    for row in rdr:
        if row[c_year].strip() != latest:
            continue
        geo = row[c_geo].strip().lower()
        if geo not in GEO_ISO:
            continue
        sex = (row[c_sex].strip().lower() if c_sex else 'both')
        if not ('both' in sex or 'total' in sex):
            continue
        age = row[c_age].strip().lower()
        ages_seen.add(age); sex_seen.add(sex)
        try:
            v = float(row[c_val])
        except (ValueError, TypeError):
            continue
        d = rows.setdefault(geo, {})
        if age in ('all ages', 'total, all ages', 'all ages, total'):
            d['all'] = v
        elif age in ('65 years and over', '65 years and older'):
            d['65'] = v

    by_unit = {}
    for geo, d in rows.items():
        if d.get('all') and d.get('65') is not None:
            by_unit[GEO_ISO[geo]] = round(100 * d['65'] / d['all'], 1)
    if not by_unit:
        print('No values computed. latest year:', latest)
        print('ages sample:', sorted(a for a in ages_seen if '65' in a or 'all' in a)[:10])
        print('sex sample:', sorted(sex_seen)[:6])
        return
    vals = list(by_unit.values())
    nat = round(sum(vals) / len(vals), 1)
    os.makedirs(os.path.join(OUT, 'aging'), exist_ok=True)
    out = {'meta': {'metric': 'share of population aged 65+ (%)', 'age_group': '65+', 'year': int(latest[:4]),
                    'source': 'Statistics Canada, table 17-10-0005', 'resolution': 'admin-1',
                    'method': '65+ / all-ages population estimate per province', 'national_pct_unweighted': nat},
           'byUnit': by_unit}
    json.dump(out, open(os.path.join(OUT, 'aging', 'ca-admin1.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'ca: {len(by_unit)} units, year {latest}, range {min(vals)}-{max(vals)}%  WROTE')


if __name__ == '__main__':
    main()
