#!/usr/bin/env python3
"""Tier-1 aging layer: WorldPop 2020 1km age/sex rasters -> admin-1 % aged 65+.

For each country: zonal-sum EVERY WorldPop age/sex band onto {cc}-admin1.geojson,
then pct_65plus = 100 * sum(65,70,75,80 bands, m+f) / sum(all bands, m+f) per unit.
Numerator and denominator come from the SAME age/sex product, so the ratio is
internally consistent. Writes public/data/aging/{cc}-admin1.json = {meta, byUnit:{code: pct}}.

Rasters are cached in _data_in/WorldPop/{ISO3}/ (gitignored) and reused across runs.
Needs rasterstats + rasterio. Usage:
  python scripts/build_aging.py            # all WorldPop countries
  python scripts/build_aging.py th vn      # a subset
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_IN = os.path.join(HERE, "_data_in")
OUT = os.path.normpath(os.path.join(HERE, "..", "public", "data"))
WP_DIR = os.path.join(DATA_IN, "WorldPop")

# Same 18 countries as build_data.py WORLDPOP (GBD-rate x WorldPop-pop set).
WORLDPOP = {
    "th": "THA", "vn": "VNM", "id": "IDN", "ph": "PHL", "my": "MYS", "pk": "PAK",
    "bd": "BGD", "mm": "MMR", "gb": "GBR", "de": "DEU", "fr": "FRA", "it": "ITA",
    "es": "ESP", "pl": "POL", "ca": "CAN", "au": "AUS", "nz": "NZL", "tr": "TUR",
}
AGES = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]  # WorldPop AgeSex codes
OLD = [65, 70, 75, 80]  # 65+ (WorldPop's top band is 80+)
BASE = "https://data.worldpop.org/GIS/AgeSex_structures/Global_2000_2020_1km/unconstrained/2020/{ISO3}"


def fetch(url, fp, tries=4):
    if os.path.exists(fp) and os.path.getsize(fp) > 0:
        return True
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "brain-exposome/aging (mailto:a0972210123@gmail.com)"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            with open(fp, "wb") as f:
                f.write(data)
            time.sleep(0.4)  # politeness — WorldPop resets connections under rapid sequential load
            return True
        except Exception as e:
            if attempt == tries:
                print(f"    fetch FAIL {os.path.basename(fp)} after {tries} tries: {e}", flush=True)
                return False
            time.sleep(2 * attempt)  # backoff
    return False


def build(cc, iso3):
    from rasterstats import zonal_stats
    geo = os.path.join(OUT, "geo", f"{cc}-admin1.geojson")
    if not os.path.exists(geo):
        print(f"  {cc}: no {cc}-admin1.geojson, skip", flush=True)
        return None
    feats = json.load(open(geo, encoding="utf-8"))["features"]
    codes = [f["properties"]["code"] for f in feats]
    wp = os.path.join(WP_DIR, iso3)
    os.makedirs(wp, exist_ok=True)
    tot = {c: 0.0 for c in codes}
    old = {c: 0.0 for c in codes}
    for age in AGES:
        for sex in ("m", "f"):
            fn = f"{iso3.lower()}_{sex}_{age}_2020_1km.tif"
            fp = os.path.join(wp, fn)
            if not fetch(f"{BASE.format(ISO3=iso3)}/{fn}", fp):
                return None
            for c, z in zip(codes, zonal_stats(feats, fp, stats="sum", all_touched=True)):
                s = z["sum"] or 0.0
                tot[c] += s
                if age in OLD:
                    old[c] += s
    by = {c: (round(100 * old[c] / tot[c], 1) if tot[c] else None) for c in codes}
    nat_old, nat_tot = sum(old.values()), sum(tot.values())
    nat = round(100 * nat_old / nat_tot, 1) if nat_tot else None
    return {
        "meta": {
            "metric": "share of population aged 65+ (%)", "age_group": "65+", "year": 2020,
            "source": "WorldPop 2020 1km unconstrained age/sex (CC BY 4.0)", "resolution": "admin-1",
            "method": "zonal sum of 65+ age/sex bands / all bands per admin-1 unit (Natural Earth boundaries)",
            "national_pct": nat,
        },
        "byUnit": by,
    }


def main():
    ccs = [a.lower() for a in sys.argv[1:]] or list(WORLDPOP)
    os.makedirs(os.path.join(OUT, "aging"), exist_ok=True)
    for cc in ccs:
        iso3 = WORLDPOP.get(cc)
        if not iso3:
            print(f"  {cc}: not a WorldPop country, skip", flush=True)
            continue
        t = time.time()
        print(f"{cc} ({iso3}) ...", flush=True)
        r = build(cc, iso3)
        if r:
            json.dump(r, open(os.path.join(OUT, "aging", f"{cc}-admin1.json"), "w", encoding="utf-8"), ensure_ascii=False)
            vals = [v for v in r["byUnit"].values() if v is not None]
            rng = f"{min(vals)}-{max(vals)}%" if vals else "n/a"
            print(f"  {cc}: national {r['meta']['national_pct']}% | units {len(r['byUnit'])} | range {rng} | {time.time() - t:.0f}s", flush=True)
        else:
            print(f"  {cc}: FAILED ({time.time() - t:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
