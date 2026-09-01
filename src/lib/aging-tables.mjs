/* Build-time reader for the admin-1 "population aged 65+" layer.
   The map already has these numbers, but only inside Leaflet/SVG — invisible to crawlers
   and answer engines. This turns the same JSON into rows the build can render as HTML.
   Node-only (uses node:fs): import from Astro frontmatter, never from a client script. */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = process.cwd();
const AGING_DIR = join(ROOT, 'public', 'data', 'aging');
const GEO_DIR = join(ROOT, 'public', 'data', 'geo');

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));

/* Units that carry a 65+ figure but have no polygon in the geo file, so the map never
   needed a name for them. Names are ISO 3166-2 subdivision names — a row showing only
   "US-AK" cannot be cited, which is the whole point of these tables.
   GB is not listed here: its names come from the repo's own gb-lad-to-iso.json. */
const NO_GEOMETRY_NAMES = {
  'CA-NU': 'Nunavut',
  'ES-CE': 'Ceuta',
  'ES-ML': 'Melilla',
  'US-AK': 'Alaska',
  'US-HI': 'Hawaii',
};

/* Unit code → names, from the same geo files the map draws.
   Taiwan is the one exception: townships in a topojson, not admin-1 in a geojson. */
function unitNames(cc) {
  if (cc === 'tw') {
    const topo = read(join(GEO_DIR, 'tw-districts.topo.json'));
    return Object.fromEntries(topo.objects.towns.geometries.map(g => [
      g.properties.TOWNCODE,
      { name: `${g.properties.TOWNENG}, ${g.properties.COUNTYENG}`, nameLocal: `${g.properties.COUNTYNAME}${g.properties.TOWNNAME}` },
    ]));
  }

  const names = {};
  const p = join(GEO_DIR, `${cc}-admin1.geojson`);
  if (existsSync(p)) {
    for (const f of read(p).features) {
      names[f.properties.code] = { name: f.properties.name, nameLocal: f.properties.nameLocal || f.properties.name };
    }
  }

  /* The GB builder matched local authorities to ISO codes through this table; it names
     the ones the boundary file omits (e.g. GB-STA = St Albans). */
  if (cc === 'gb') {
    const ref = join(ROOT, 'scripts', '_ref', 'gb-lad-to-iso.json');
    if (existsSync(ref)) {
      for (const r of read(ref).crosswalk) {
        if (!names[r.iso] && r.nomis_name) names[r.iso] = { name: r.nomis_name, nameLocal: r.nomis_name };
      }
    }
  }

  for (const [code, name] of Object.entries(NO_GEOMETRY_NAMES)) {
    if (!names[code] && code.startsWith(cc.toUpperCase() + '-')) names[code] = { name, nameLocal: name };
  }
  return names;
}

/* One entry per country that has an admin-1 aging file, sorted by country name.
   `units` is sorted high → low so the visible top-N is the interesting end. */
export function agingTables(lang = 'zh') {
  const region = (() => {
    let dn = null;
    try { dn = new Intl.DisplayNames([lang === 'en' ? 'en' : 'zh-Hant'], { type: 'region' }); } catch (e) { /* falls back to the code */ }
    return (iso) => { try { return (dn && dn.of(iso)) || iso; } catch (e) { return iso; } };
  })();

  const out = readdirSync(AGING_DIR)
    .filter(f => f.endsWith('-admin1.json'))
    .map(f => {
      const cc = f.replace('-admin1.json', '');
      const src = read(join(AGING_DIR, f));
      const names = unitNames(cc);
      /* `named: false` keeps the row but flags it: the figure is real, the label is only
         the source's own code. Never drop the row — a shorter table reads as complete. */
      const units = Object.entries(src.byUnit)
        .map(([code, pct]) => ({
          code,
          name: (names[code] && names[code].name) || code,
          nameLocal: (names[code] && names[code].nameLocal) || code,
          named: Boolean(names[code]),
          pct,
        }))
        .sort((a, b) => b.pct - a.pct);
      return {
        cc,
        iso: cc.toUpperCase(),
        country: region(cc.toUpperCase()),
        meta: src.meta,
        units,
        unnamed: units.filter(u => !u.named).length,
      };
    })
    .filter(c => c.units.length > 0)
    .sort((a, b) => a.country.localeCompare(b.country, lang === 'en' ? 'en' : 'zh-Hant'));

  return out;
}

/* A single quotable sentence per country: highest unit, lowest unit, national figure,
   source and year all in one clause — the shape answer engines lift verbatim. */
export function agingSentence(entry, lang = 'zh') {
  const { country, meta, units } = entry;
  /* Only named units can appear in a quotable sentence — a bare code cites nothing. */
  const usable = units.filter(u => u.named);
  const pool = usable.length ? usable : units;
  const hi = pool[0], lo = pool[pool.length - 1];
  const label = lang === 'en' ? (u) => u.name : (u) => u.nameLocal;
  const nat = meta.national_pct_unweighted;
  const year = meta.year;
  const res = meta.resolution === 'township' ? (lang === 'en' ? 'township' : '鄉鎮市區') : (lang === 'en' ? 'admin-1 unit' : '一級行政區');

  if (lang === 'en') {
    return `In ${country}, the ${res} with the highest share of population aged 65+ is ${label(hi)} at ${hi.pct}%, and the lowest is ${label(lo)} at ${lo.pct}%`
      + (nat != null ? `; the unweighted national figure is ${nat}%` : '')
      + ` (${meta.source}, ${year}).`;
  }
  return `${country} 65 歲以上人口占比最高的${res}是 ${label(hi)}（${hi.pct}%），最低是 ${label(lo)}（${lo.pct}%）`
    + (nat != null ? `；全國未加權平均 ${nat}%` : '')
    + `（${meta.source}，${year} 年）。`;
}
