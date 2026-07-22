// Tier-2 aging: United Kingdom admin-1 65+ % from ONS via Nomis (NM_2002_1, c_age 209=65+ / 200=All Ages).
// The gb geojson uses an older ISO-3166-2:GB vintage (~2015, incl. pre-2015 NI districts); current Nomis
// LADs are matched to it BY NAME. The resulting crosswalk is SAVED to scripts/_ref/gb-lad-to-iso.json for
// reuse by any future UK dataset. Units that changed boundary (NI 26->11, merged English unitaries) stay
// unmatched and fall back to the Tier-0 national shade.
//   node scripts/build_aging_gb.mjs
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const ROOT = path.resolve(HERE, '..');
const OUT = path.join(ROOT, 'public', 'data');
const REF = path.join(ROOT, 'scripts', '_ref');
const CACHE = path.join(ROOT, 'scripts', '_data_in', 'nomis');
const NOMIS_URL = 'https://www.nomisweb.co.uk/api/v01/dataset/NM_2002_1.data.json?geography=TYPE432&date=latest&gender=0&c_age=200,209&measures=20100&select=geography_code,geography_name,c_age,obs_value';

const norm = (s) => (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/&/g, 'and').replace(/,?\s*(city|county|county borough) of\b/g, '').replace(/\bborough of\b/g, '')
  .replace(/[^a-z0-9]+/g, '').replace(/^the/, '').trim();

// Overrides: normalised-Nomis-name -> geojson ISO code (for name variants that don't normalise equal)
const OVERRIDE = {
  kingstonuponhull: 'GB-KHL', herefordshire: 'GB-HEF', bristol: 'GB-BST',
  cityoflondon: 'GB-LND', westnorthamptonshire: 'GB-NTH', northnorthamptonshire: 'GB-NTH',
  'stalbans': 'GB-STA',
};

async function main() {
  fs.mkdirSync(CACHE, { recursive: true });
  const fp = path.join(CACHE, 'gb_65plus.json');
  if (!(fs.existsSync(fp) && fs.statSync(fp).size > 0)) {
    const r = await fetch(NOMIS_URL, { headers: { 'User-Agent': 'brain-exposome/aging' } });
    fs.writeFileSync(fp, await r.text());
  }
  const obs = JSON.parse(fs.readFileSync(fp, 'utf8')).obs;
  const lad = {};   // gss -> {name, all, o65}
  for (const o of obs) {
    const g = o.geography, gss = g.geogcode, d = lad[gss] = lad[gss] || { name: g.description };
    if (o.c_age.value === 200) d.all = o.obs_value.value; else if (o.c_age.value === 209) d.o65 = o.obs_value.value;
  }
  const feats = JSON.parse(fs.readFileSync(path.join(OUT, 'geo', 'gb-admin1.geojson'), 'utf8')).features;
  const nameToIso = {};
  for (const f of feats) for (const nm of [f.properties.name, f.properties.nameLocal]) if (nm) nameToIso[norm(nm)] = f.properties.code;

  const byUnit = {}, crosswalk = [];
  for (const [gss, d] of Object.entries(lad)) {
    if (!d.all || d.o65 == null) continue;
    const key = norm(d.name);
    const iso = OVERRIDE[key] || nameToIso[key];
    const share = +(100 * d.o65 / d.all).toFixed(1);
    if (iso) { byUnit[iso] = share; crosswalk.push({ iso, gss, nomis_name: d.name }); }
  }
  // save the reusable crosswalk (sorted by ISO)
  fs.mkdirSync(REF, { recursive: true });
  crosswalk.sort((a, b) => a.iso.localeCompare(b.iso));
  fs.writeFileSync(path.join(REF, 'gb-lad-to-iso.json'), JSON.stringify({
    _note: 'ONS/Nomis LAD (GSS code + name) -> ISO-3166-2:GB geojson code. Built by build_aging_gb.mjs; reuse for any UK admin-1 dataset. Unmatched = boundary-changed units (NI pre-2015, merged English unitaries).',
    crosswalk,
  }, null, 1));

  const isoMatched = new Set(Object.keys(byUnit));
  const unmatchedGeo = feats.map((f) => f.properties.code).filter((c) => !isoMatched.has(c));
  const vals = Object.values(byUnit);
  const nat = +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
  fs.mkdirSync(path.join(OUT, 'aging'), { recursive: true });
  fs.writeFileSync(path.join(OUT, 'aging', 'gb-admin1.json'), JSON.stringify({
    meta: { metric: 'share of population aged 65+ (%)', age_group: '65+', year: 2024, source: 'ONS mid-year population estimates via Nomis (NM_2002_1)', resolution: 'admin-1', method: '65+ / all-ages per local authority; matched to ISO-3166-2:GB by name (see scripts/_ref/gb-lad-to-iso.json)', national_pct_unweighted: nat },
    byUnit,
  }));
  console.log(`gb: matched ${isoMatched.size}/${feats.length} geojson units, range ${Math.min(...vals)}-${Math.max(...vals)}%  WROTE`);
  console.log(`crosswalk saved: scripts/_ref/gb-lad-to-iso.json (${crosswalk.length} rows)`);
  console.log(`unmatched geojson units (fall back to national, ${unmatchedGeo.length}): ${unmatchedGeo.slice(0, 30).join(' ')}${unmatchedGeo.length > 30 ? ' …' : ''}`);
}
main();
