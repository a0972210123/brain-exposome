#!/usr/bin/env python3
"""
build_data.py — offline data pipeline for the Brain-Health Exposome Check-in
(/projects/dementia-exposome).

Produces the static assets consumed by the page, under public/data/:
  pm25/tw-county-pm25.json      county x year mean PM2.5 (1998-2024)  -> calculator
  pm25/tw-district-pm25.json    per-town recent PM2.5                 -> map layer
  geo/tw-districts.topo.json    368 town (鄉鎮市區) boundaries         -> map geometry
  dementia/tw-dementia-modelled.json   modelled prevalence            -> map layer
  manifest.json                 provenance / citation / licence

Data sources (all open):
  - PM2.5:  ACAG / WashU global surface PM2.5, V6.GL.03 (CNN), 0.1deg annual,
            AWS Open Data bucket s3://satpmdata/ (CC BY 4.0).
            Cite: Shen et al. 2024 (ACS ES&T Air); van Donkelaar et al. 2021 (ES&T).
  - Boundaries: taiwan-atlas (dkaoster) TopoJSON redistribution of MOI 鄉鎮市區界線
            (data.gov.tw #7441), OGDL-Taiwan-1.0 (~= CC BY 4.0). NLSC / 內政部.
  - Population for modelled prevalence: official source is MOI 內政部戶政司
            #77132 (single-year age by 村里). That API is not reachable from every
            build environment; this script tries it and falls back to a committed,
            cited COUNTY-level snapshot (see EMBEDDED_COUNTY_POP) — in which case the
            prevalence map is a COUNTY-level estimate. Re-run with gov access to
            regenerate the authoritative 鄉鎮市區-level version.
  - Dementia rates: NHRI national community survey 2020-2023 (age-band prevalence).

Deps (pip wheels, no system GDAL): netCDF4 numpy shapely requests.
Usage:  python3 scripts/build_data.py   (run from repo root)
"""
import io
import json
import os
import sys
import tarfile
import tempfile
import time

import numpy as np
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "data")
BUILD_DATE = time.strftime("%Y-%m-%d")

# ---- config ----
YEAR0, YEAR1 = 1998, 2024
S3 = ("https://satpmdata.s3.us-east-1.amazonaws.com/V6GL03/CoarseResolution/GL/"
      "Annual/V6GL03.CNNPM25.0p10.GL.{y}01-{y}12.nc")
TW_BBOX = dict(lon_min=118.0, lon_max=122.5, lat_min=21.4, lat_max=26.5)  # incl. offshore
TATLAS_TGZ = "https://registry.npmjs.org/taiwan-atlas/-/taiwan-atlas-2021.9.20.tgz"

# NHRI 2020-2023 age-band dementia prevalence (share of that age band)
NHRI_RATES = {"65-69": 0.0240, "70-74": 0.0516, "75-79": 0.0910,
              "80-84": 0.1600, "85-89": 0.2004, "90+": 0.2945}
# National distribution of the 65+ population across the six bands (approx, MOI ~2023).
# Used only when we lack per-area age structure (county fallback).
NAT_65_DIST = {"65-69": 0.30, "70-74": 0.24, "75-79": 0.17,
               "80-84": 0.13, "85-89": 0.09, "90+": 0.07}
# Weighted mean dementia rate among 65+ (national age structure) ~ 0.095.
RBAR = sum(NHRI_RATES[b] * NAT_65_DIST[b] for b in NHRI_RATES)

# Committed county snapshot fallback: (total population, share aged 65+), approx MOI 2023
# year-end. Keyed by COUNTYNAME as it appears in the taiwan-atlas boundary data (台 forms).
# Clearly a snapshot/estimate — the map is labelled accordingly.
EMBEDDED_COUNTY_POP = {
    "台北市": (2494000, 0.215), "新北市": (4004000, 0.170), "桃園市": (2320000, 0.140),
    "台中市": (2856000, 0.150), "台南市": (1862000, 0.180), "高雄市": (2738000, 0.180),
    "基隆市": (361000, 0.190), "新竹市": (452000, 0.135), "嘉義市": (261000, 0.175),
    "新竹縣": (585000, 0.140), "苗栗縣": (530000, 0.190), "彰化縣": (1247000, 0.180),
    "南投縣": (476000, 0.200), "雲林縣": (660000, 0.210), "嘉義縣": (484000, 0.220),
    "屏東縣": (795000, 0.195), "宜蘭縣": (449000, 0.185), "花蓮縣": (316000, 0.185),
    "台東縣": (211000, 0.190), "澎湖縣": (107000, 0.170), "金門縣": (143000, 0.130),
    "連江縣": (13900, 0.140),
}


def log(*a):
    print(*a, flush=True)


def http_get(url, tries=4, timeout=120):
    for i in range(tries):
        try:
            r = requests.get(url, timeout=timeout,
                             headers={"User-Agent": "mattye-exposome-build/1.0"})
            if r.status_code == 200:
                return r.content
            log(f"  HTTP {r.status_code} for {url}")
        except Exception as e:
            log(f"  attempt {i+1} failed: {e}")
        time.sleep(2 ** i)
    raise RuntimeError(f"GET failed: {url}")


# ---------- TopoJSON decode (transform + delta arcs -> shapely) ----------
from shapely.geometry import Point, Polygon, MultiPolygon, shape  # noqa: E402
from shapely.ops import unary_union  # noqa: E402


def _decode_arc(topo, i):
    rev = i < 0
    if rev:
        i = ~i
    x = y = 0
    pts = []
    for dx, dy in topo["arcs"][i]:
        x += dx
        y += dy
        pts.append((x, y))
    return pts[::-1] if rev else pts


def _ring(topo, arc_idxs):
    coords = []
    for k, ai in enumerate(arc_idxs):
        seg = _decode_arc(topo, ai)
        coords.extend(seg[1:] if k else seg)
    s = topo["transform"]["scale"]
    t = topo["transform"]["translate"]
    return [(x * s[0] + t[0], y * s[1] + t[1]) for x, y in coords]


def _geom(topo, g):
    ty = g["type"]
    if ty == "Polygon":
        rings = [_ring(topo, r) for r in g["arcs"]]
        return Polygon(rings[0], rings[1:]) if rings else None
    if ty == "MultiPolygon":
        polys = []
        for poly in g["arcs"]:
            rings = [_ring(topo, r) for r in poly]
            if rings:
                polys.append(Polygon(rings[0], rings[1:]))
        return MultiPolygon(polys) if polys else None
    return None


def load_boundaries():
    """Return (topo_dict, towns[list of {props, geom}], counties[{name:geom}])."""
    log("Fetching taiwan-atlas boundaries (npm tarball)…")
    raw = http_get(TATLAS_TGZ)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tf:
        towns_topo = json.load(tf.extractfile("package/towns-10t.json"))
    towns, counties = [], {}
    for g in towns_topo["objects"]["towns"]["geometries"]:
        geom = _geom(towns_topo, g)
        if geom and not geom.is_valid:
            geom = geom.buffer(0)
        towns.append({"props": g["properties"], "geom": geom})
    for g in towns_topo["objects"]["counties"]["geometries"]:
        geom = _geom(towns_topo, g)
        if geom and not geom.is_valid:
            geom = geom.buffer(0)
        counties[g["properties"]["COUNTYNAME"]] = {
            "props": g["properties"], "geom": geom}
    log(f"  {len(towns)} towns, {len(counties)} counties decoded")
    return towns_topo, towns, counties


# ---------- ACAG PM2.5 ----------
def load_pm25_years():
    """Stream each annual ACAG file, crop Taiwan bbox, return
       (years, lat[sub], lon[sub], grid[year][lat][lon])."""
    import netCDF4
    years = list(range(YEAR0, YEAR1 + 1))
    sub_lat = sub_lon = None
    li = None
    stack = []
    tmpdir = tempfile.mkdtemp(prefix="acag_")
    try:
        for y in years:
            url = S3.format(y=y)
            path = os.path.join(tmpdir, f"{y}.nc")
            log(f"  ACAG {y} …")
            with open(path, "wb") as fh:
                fh.write(http_get(url))
            ds = netCDF4.Dataset(path)
            lat = ds.variables["lat"][:]
            lon = ds.variables["lon"][:]
            if li is None:
                la = np.where((lat >= TW_BBOX["lat_min"]) & (lat <= TW_BBOX["lat_max"]))[0]
                lo = np.where((lon >= TW_BBOX["lon_min"]) & (lon <= TW_BBOX["lon_max"]))[0]
                li = (la.min(), la.max() + 1, lo.min(), lo.max() + 1)
                sub_lat = np.asarray(lat[li[0]:li[1]])
                sub_lon = np.asarray(lon[li[2]:li[3]])
            pm = ds.variables["PM25"][li[0]:li[1], li[2]:li[3]]
            arr = np.ma.filled(np.ma.masked_invalid(pm).astype("float64"), np.nan)
            stack.append(arr)
            ds.close()
            os.remove(path)  # keep peak disk tiny
    finally:
        try:
            os.rmdir(tmpdir)
        except OSError:
            pass
    log(f"  loaded {len(stack)} years, Taiwan grid {stack[0].shape}")
    return years, sub_lat, sub_lon, np.stack(stack)  # [year, lat, lon]


def county_year_series(counties, years, lat, lon, grid):
    """Mean of grid cells whose centre falls inside each county polygon."""
    LON, LAT = np.meshgrid(lon, lat)
    out = {}
    for name, c in counties.items():
        geom = c["geom"]
        minx, miny, maxx, maxy = geom.bounds
        m = (LON >= minx) & (LON <= maxx) & (LAT >= miny) & (LAT <= maxy)
        idx = np.argwhere(m)
        inside = [(r, cc) for r, cc in idx if geom.contains(Point(LON[r, cc], LAT[r, cc]))]
        if not inside:  # county smaller than a 0.1deg cell -> nearest to centroid
            cen = geom.centroid
            r = int(np.abs(lat - cen.y).argmin())
            cc = int(np.abs(lon - cen.x).argmin())
            inside = [(r, cc)]
        rows = [r for r, _ in inside]
        cols = [cc for _, cc in inside]
        series = []
        for yi in range(len(years)):
            vals = grid[yi, rows, cols]
            vals = vals[~np.isnan(vals)]
            series.append(round(float(vals.mean()), 1) if len(vals) else None)
        out[c["props"]["COUNTYCODE"]] = {
            "name": name, "nameEn": c["props"]["COUNTYENG"], "values": series}
    return out


def town_recent_pm(towns, years, lat, lon, grid, recent=3):
    """Per-town PM2.5 = nearest grid cell to town centroid, mean of last `recent` years."""
    yi0 = len(years) - recent
    recent_mean = np.nanmean(grid[yi0:], axis=0)  # [lat, lon]
    out = {}
    for t in towns:
        cen = t["geom"].centroid
        r = int(np.abs(lat - cen.y).argmin())
        cc = int(np.abs(lon - cen.x).argmin())
        v = recent_mean[r, cc]
        out[t["props"]["TOWNCODE"]] = {
            "name": t["props"]["TOWNNAME"],
            "pm25": round(float(v), 1) if not np.isnan(v) else None}
    return out, f"{years[yi0]}-{years[-1]} mean"


# ---------- population -> modelled prevalence ----------
def fetch_population():
    """Try the official MOI #77132 API; on failure use the committed county snapshot.
       Returns (granularity, pop_by_county{name:(total, share65)})."""
    api = "https://www.ris.gov.tw/rs-opendata/api/v1/datastore/ODRP014/11305"
    try:
        r = requests.get(api, timeout=30,
                         headers={"User-Agent": "mattye-exposome-build/1.0"})
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("application/json"):
            # NOTE: parsing/rollup to the six age bands would go here for the
            # authoritative 鄉鎮市區-level version. Left as the gov-access path.
            log("  MOI #77132 reachable — implement village->town age rollup here.")
    except Exception as e:
        log(f"  MOI population API not reachable ({e}); using committed county snapshot.")
    return "county", EMBEDDED_COUNTY_POP


def modelled_prevalence(towns, granularity, pop):
    """County crude dementia rate per 1,000 residents = share65 * RBAR * 1000.
       Every town in a county inherits its county rate (county-level estimate)."""
    county_rate, county_rows = {}, []
    for name, (total, share65) in pop.items():
        pop65 = total * share65
        cases = int(round(pop65 * RBAR))
        rate_per_1000 = round(share65 * RBAR * 1000, 1)
        county_rate[name] = rate_per_1000
        county_rows.append({"countyName": name, "pop_total": total,
                            "pop_65plus": int(round(pop65)),
                            "modelled_cases": cases,
                            "rate_per_1000": rate_per_1000})
    by_town = {}
    for t in towns:
        p = t["props"]
        by_town[p["TOWNCODE"]] = county_rate.get(p["COUNTYNAME"])
    return county_rows, by_town


# ---------- world country-level PM2.5 (for the residence country dropdown) ----------
WORLD_CSV = ("https://satpmdata.s3.us-east-1.amazonaws.com/V6GL03/RegionSummaries/"
             "GlobalPM25-V6GL03-Annual-1998-2024-wThresFrac.csv")


def build_world_country_pm25():
    """Parse ACAG global country summary CSV -> {country: {values:[YEAR0..YEAR1]}}
       using the Population-Weighted PM2.5 column."""
    import csv
    log("Fetching ACAG global country PM2.5 summary…")
    raw = http_get(WORLD_CSV).decode("utf-8", "replace")
    rd = csv.reader(io.StringIO(raw))
    header = next(rd)  # Region, Year, Population-Weighted PM2.5 [ug/m3], ...
    ri, yi, pi = 0, 1, 2
    tmp = {}
    for row in rd:
        if len(row) <= pi:
            continue
        region = row[ri].strip()
        try:
            year, pm = int(row[yi]), float(row[pi])
        except ValueError:
            continue
        if YEAR0 <= year <= YEAR1:
            tmp.setdefault(region, {})[year] = round(pm, 1)
    out = {}
    for region, ys in tmp.items():
        vals = [ys.get(y) for y in range(YEAR0, YEAR1 + 1)]
        if any(v is not None for v in vals):
            out[region] = {"values": vals}
    log(f"  {len(out)} countries")
    return out


# ---------- write ----------
def write_json(rel, obj):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))
    log(f"  wrote {rel}  ({os.path.getsize(path)//1024} KB)")


def main():
    log("== BUILD DATA ==  RBAR(65+ dementia rate) = %.4f" % RBAR)
    towns_topo, towns, counties = load_boundaries()

    years, lat, lon, grid = load_pm25_years()

    log("Computing county x year PM2.5 …")
    county_pm = county_year_series(counties, years, lat, lon, grid)
    write_json("pm25/tw-county-pm25.json", {
        "meta": {"source": "ACAG SatPM2.5 V6.GL.03 (0.1deg annual)",
                 "method": "mean of grid cells within each county polygon",
                 "units": "ug/m3", "note": "years < 1998 clamp to 1998 in the app",
                 "citation": "Shen et al. 2024, ACS ES&T Air; van Donkelaar et al. 2021, ES&T",
                 "license": "CC BY 4.0", "built": BUILD_DATE},
        "year0": years[0], "year1": years[-1], "counties": county_pm})

    log("Computing per-town recent PM2.5 …")
    town_pm, pm_period = town_recent_pm(towns, years, lat, lon, grid)
    write_json("pm25/tw-district-pm25.json", {
        "meta": {"source": "ACAG SatPM2.5 V6.GL.03", "period": pm_period,
                 "method": "nearest 0.1deg cell to town centroid",
                 "units": "ug/m3", "citation": "Shen et al. 2024; van Donkelaar et al. 2021",
                 "license": "CC BY 4.0", "built": BUILD_DATE},
        "districts": town_pm})

    log("Modelled prevalence …")
    granularity, pop = fetch_population()
    county_rows, by_town = modelled_prevalence(towns, granularity, pop)
    write_json("dementia/tw-dementia-modelled.json", {
        "meta": {"title": "Modelled dementia prevalence (ESTIMATE)",
                 "granularity": granularity,
                 "method": ("national NHRI 2020-2023 age-band rates x county 65+ population "
                            "(national within-65+ age structure); towns inherit county rate"),
                 "disclaimer": ("MODELLED COUNTY-LEVEL ESTIMATE, not measured. Taiwan publishes no "
                                "sub-national dementia prevalence. Re-run build_data.py with MOI "
                                "#77132 access for the authoritative town-level version."),
                 "rates_source": "NHRI community dementia survey 2020-2023",
                 "population_source": "MOI 2023 county snapshot (approx.)",
                 "metric": "modelled dementia cases per 1,000 residents (all ages)",
                 "license": "OGDL-Taiwan-1.0", "built": BUILD_DATE},
        "counties": county_rows, "byTown": by_town})

    log("World country PM2.5 (residence dropdown) …")
    world_pm = build_world_country_pm25()
    write_json("pm25/world-country-pm25.json", {
        "meta": {"source": "ACAG SatPM2.5 V6.GL.03 global region summary (population-weighted)",
                 "units": "ug/m3", "note": "years < 1998 clamp to 1998 in the app",
                 "citation": "Shen et al. 2024, ACS ES&T Air; van Donkelaar et al. 2021, ES&T",
                 "license": "CC BY 4.0", "built": BUILD_DATE},
        "year0": YEAR0, "year1": YEAR1, "countries": world_pm})

    log("Boundaries -> geo/tw-districts.topo.json …")
    write_json("geo/tw-districts.topo.json", towns_topo)

    write_json("manifest.json", {
        "built": BUILD_DATE,
        "assets": {
            "pm25/tw-county-pm25.json": "ACAG V6.GL.03 county x year PM2.5 (CC BY 4.0)",
            "pm25/tw-district-pm25.json": "ACAG V6.GL.03 per-town recent PM2.5 (CC BY 4.0)",
            "pm25/world-country-pm25.json": "ACAG V6.GL.03 country x year PM2.5, pop-weighted (CC BY 4.0)",
            "geo/tw-districts.topo.json": "taiwan-atlas / MOI #7441 boundaries (OGDL-Taiwan-1.0)",
            "dementia/tw-dementia-modelled.json": "modelled prevalence, NHRI 2020-23 x MOI pop"},
        "attribution": ["PM2.5 © ACAG/WashU (Shen 2024; van Donkelaar 2021), CC BY 4.0",
                        "界線 © 內政部NLSC / taiwan-atlas, OGDL-Taiwan-1.0",
                        "人口 © 內政部 (MOI)", "失智盛行率為模型估計值 (NHRI 2020-2023)"]})
    log("== DONE ==")


if __name__ == "__main__":
    sys.exit(main())
