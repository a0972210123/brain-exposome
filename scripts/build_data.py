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
DATA_IN = os.path.join(ROOT, "scripts", "_data_in")  # owner-downloaded inputs (gitignored)
BUILD_DATE = time.strftime("%Y-%m-%d")

# ---- config ----
YEAR0, YEAR1 = 1998, 2024
S3 = ("https://satpmdata.s3.us-east-1.amazonaws.com/V6GL03/CoarseResolution/GL/"
      "Annual/V6GL03.CNNPM25.0p10.GL.{y}01-{y}12.nc")
TW_BBOX = dict(lon_min=118.0, lon_max=122.5, lat_min=21.4, lat_max=26.5)  # incl. offshore
# Union bbox covering Taiwan + Japan + Korea, so the ACAG grid is loaded once and
# re-used (each unit is matched by point-in-polygon, so a wider grid is harmless).
ALL_BBOX = dict(lon_min=118.0, lon_max=154.0, lat_min=21.0, lat_max=46.5)
TATLAS_TGZ = "https://registry.npmjs.org/taiwan-atlas/-/taiwan-atlas-2021.9.20.tgz"
NE_ADMIN1 = ("https://raw.githubusercontent.com/nvkelso/natural-earth-vector/"
             "master/geojson/ne_10m_admin_1_states_provinces.geojson")
# Other-country sub-national PM2.5 maps (boundaries: Natural Earth admin-1).
COUNTRY_MAPS = {
    "jp": {"admin": "Japan", "name": "Japan", "nameZh": "日本"},
    "kr": {"admin": "South Korea", "name": "South Korea", "nameZh": "南韓"},
}

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
                la = np.where((lat >= ALL_BBOX["lat_min"]) & (lat <= ALL_BBOX["lat_max"]))[0]
                lo = np.where((lon >= ALL_BBOX["lon_min"]) & (lon <= ALL_BBOX["lon_max"]))[0]
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
    log(f"  loaded {len(stack)} years, grid {stack[0].shape} (TW+JP+KR bbox)")
    return years, sub_lat, sub_lon, np.stack(stack)  # [year, lat, lon]


def load_ne_admin1():
    log("Fetching Natural Earth admin-1 (JP/KR provinces)…")
    return json.loads(http_get(NE_ADMIN1).decode("utf-8", "replace"))


def ne_units(ne_geojson, admin_name):
    """Return [{code, name, nameLocal, geom}] for one country's admin-1 units."""
    out = []
    for f in ne_geojson["features"]:
        p = f["properties"]
        if p.get("admin") != admin_name:
            continue
        geom = shape(f["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        code = p.get("iso_3166_2") or p.get("adm1_code") or p.get("name")
        out.append({"code": code, "name": p.get("name"),
                    "nameLocal": p.get("name_local") or p.get("name"), "geom": geom})
    return out


def admin1_recent_pm(units, years, lat, lon, grid, recent=3):
    """Per admin-1 unit: mean of grid cells inside the polygon (recent-N-yr mean);
       tiny units fall back to the nearest cell to the centroid."""
    yi0 = len(years) - recent
    recent_mean = np.nanmean(grid[yi0:], axis=0)
    LON, LAT = np.meshgrid(lon, lat)
    out = {}
    for u in units:
        geom = u["geom"]
        minx, miny, maxx, maxy = geom.bounds
        m = (LON >= minx) & (LON <= maxx) & (LAT >= miny) & (LAT <= maxy)
        vals = []
        for r, c in np.argwhere(m):
            if geom.contains(Point(LON[r, c], LAT[r, c])):
                v = recent_mean[r, c]
                if not np.isnan(v):
                    vals.append(v)
        if not vals:
            cen = geom.centroid
            r = int(np.abs(lat - cen.y).argmin())
            c = int(np.abs(lon - cen.x).argmin())
            v = recent_mean[r, c]
            if not np.isnan(v):
                vals = [v]
        out[u["code"]] = round(float(np.mean(vals)), 1) if vals else None
    return out, f"{years[yi0]}-{years[-1]} mean"


def units_geojson(units, tol=0.01):
    from shapely.geometry import mapping
    feats = []
    for u in units:
        g = u["geom"].simplify(tol, preserve_topology=True)
        feats.append({"type": "Feature",
                      "properties": {"code": u["code"], "name": u["name"], "nameLocal": u["nameLocal"]},
                      "geometry": mapping(g)})
    return {"type": "FeatureCollection", "features": feats}


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


# ---------- generic modelled prevalence from owner-downloaded CSVs (_data_in) ----------
# Lets any country's prevalence layer be built once the owner drops the two CSVs
# documented in docs/.../data-download-points.md. Schema:
#   {cc}-admin1-pop.csv     unit_code,pop_total[,pop_65_69,pop_70_74,pop_75_79,pop_80_84,pop_85p]
#   {cc}-rates.csv          age_band,prevalence_pct        (age_band in POP_BANDS)
POP_BANDS = ["65_69", "70_74", "75_79", "80_84", "85p"]  # 00_64 contributes ~0 dementia


def _read_csv(path):
    import csv
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def load_admin_pop(cc):
    """_data_in/{cc}-admin1-pop.csv -> {unit_code: {band: n, ..., 'total': n}} or None."""
    path = os.path.join(DATA_IN, f"{cc}-admin1-pop.csv")
    if not os.path.exists(path):
        return None
    out = {}
    for row in _read_csv(path):
        code = (row.get("unit_code") or "").strip()
        if not code:
            continue
        rec = {}
        for b in POP_BANDS:
            v = row.get(f"pop_{b}")
            if v not in (None, ""):
                rec[b] = float(v)
        total = row.get("pop_total")
        rec["total"] = (float(total) if total not in (None, "")
                        else sum(rec.get(b, 0.0) for b in POP_BANDS))
        out[code] = rec
    return out or None


def load_rates(cc):
    """_data_in/{cc}-rates.csv (or {cc}-dementia-rates.csv): age_band,prevalence_pct
       -> {band: fraction} or None."""
    for fn in (f"{cc}-rates.csv", f"{cc}-dementia-rates.csv"):
        path = os.path.join(DATA_IN, fn)
        if not os.path.exists(path):
            continue
        out = {}
        for row in _read_csv(path):
            band = (row.get("age_band") or "").strip()
            pct = row.get("prevalence_pct")
            if band and pct not in (None, ""):
                out[band] = float(pct) / 100.0
        return out or None
    return None


def modelled_from_csv(pop, rates):
    """cases = Σ_band pop_band × rate_band (or 65+ × RBAR fallback);
       rate_per_1000 = cases / pop_total × 1000. -> (by_unit{code: rate}, rows)."""
    by_unit, rows = {}, []
    have_bandrates = bool(rates) and any(b in rates for b in POP_BANDS)
    for code, rec in pop.items():
        total = rec.get("total", 0.0)
        if not total:
            continue
        pop65 = sum(rec.get(b, 0.0) for b in POP_BANDS)
        if have_bandrates and any(b in rec for b in POP_BANDS):
            cases = sum(rec.get(b, 0.0) * rates.get(b, 0.0) for b in POP_BANDS)
        else:
            cases = pop65 * RBAR  # only 65+ known, or no age-band rates: single crude rate
        rate = round(cases / total * 1000, 1)
        by_unit[code] = rate
        rows.append({"code": code, "pop_total": int(round(total)),
                     "pop_65plus": int(round(pop65)),
                     "modelled_cases": int(round(cases)), "rate_per_1000": rate})
    return by_unit, rows


def build_admin_prevalence(cc, name):
    """If the owner dropped {cc}-admin1-pop.csv (+ optional rates) in _data_in/,
       emit dementia/{cc}-modelled.json and return True; else False (layer pending)."""
    pop = load_admin_pop(cc)
    if not pop:
        return False
    rates = load_rates(cc)
    by_unit, rows = modelled_from_csv(pop, rates)
    write_json(f"dementia/{cc}-modelled.json", {
        "meta": {"metric": "modelled dementia cases per 1,000 residents (all ages)",
                 "method": ("Σ age-band population × age-band prevalence"
                            if rates else "65+ population × crude 65+ rate (RBAR)"),
                 "note": "MODELLED estimate, not measured",
                 "rates_source": "downloaded" if rates else "RBAR fallback",
                 "built": BUILD_DATE},
        "byTown": by_unit, "rows": rows})
    log(f"  {name}: modelled prevalence for {len(by_unit)} units "
        f"({'age-band rates' if rates else 'RBAR fallback'})")
    return True


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

    log("Japan & Korea sub-national PM2.5 (Natural Earth admin-1 + ACAG zonal) …")
    ne = load_ne_admin1()
    for key, cfg in COUNTRY_MAPS.items():
        units = ne_units(ne, cfg["admin"])
        pm, period = admin1_recent_pm(units, years, lat, lon, grid)
        write_json(f"pm25/{key}-admin1-pm25.json", {
            "meta": {"source": "ACAG SatPM2.5 V6.GL.03 (0.1deg annual)", "period": period,
                     "method": "mean of grid cells within each admin-1 polygon",
                     "units": "ug/m3", "country": cfg["name"],
                     "citation": "Shen et al. 2024; van Donkelaar et al. 2021",
                     "license": "CC BY 4.0", "built": BUILD_DATE},
            "units": pm})
        write_json(f"geo/{key}-admin1.geojson", units_geojson(units))
        vv = [v for v in pm.values() if v is not None]
        log(f"  {cfg['name']}: {len(units)} units, PM2.5 {min(vv):.1f}–{max(vv):.1f} ug/m3")
        # Prevalence layer builds only if the owner dropped population (+rates) CSVs.
        if not build_admin_prevalence(key, cfg["name"]):
            log(f"  {cfg['name']}: no _data_in/{key}-admin1-pop.csv -> prevalence layer pending "
                f"(see data-download-points.md)")

    write_json("manifest.json", {
        "built": BUILD_DATE,
        "assets": {
            "pm25/tw-county-pm25.json": "ACAG V6.GL.03 county x year PM2.5 (CC BY 4.0)",
            "pm25/tw-district-pm25.json": "ACAG V6.GL.03 per-town recent PM2.5 (CC BY 4.0)",
            "pm25/world-country-pm25.json": "ACAG V6.GL.03 country x year PM2.5, pop-weighted (CC BY 4.0)",
            "pm25/jp-admin1-pm25.json": "ACAG V6.GL.03 Japan prefecture PM2.5 (CC BY 4.0)",
            "pm25/kr-admin1-pm25.json": "ACAG V6.GL.03 Korea province PM2.5 (CC BY 4.0)",
            "geo/tw-districts.topo.json": "taiwan-atlas / MOI #7441 boundaries (OGDL-Taiwan-1.0)",
            "geo/jp-admin1.geojson": "Natural Earth admin-1 (Japan), public domain",
            "geo/kr-admin1.geojson": "Natural Earth admin-1 (Korea), public domain",
            "dementia/tw-dementia-modelled.json": "modelled prevalence, NHRI 2020-23 x MOI pop"},
        "attribution": ["PM2.5 © ACAG/WashU (Shen 2024; van Donkelaar 2021), CC BY 4.0",
                        "台灣界線 © 內政部NLSC / taiwan-atlas, OGDL-Taiwan-1.0",
                        "JP/KR 界線: Natural Earth (public domain)",
                        "人口 © 內政部 (MOI)", "失智盛行率為模型估計值 (NHRI 2020-2023)"]})
    log("== DONE ==")


if __name__ == "__main__":
    sys.exit(main())
