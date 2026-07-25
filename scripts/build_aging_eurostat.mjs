// Tier-2 aging (EU): Eurostat demo_r_pjanind3 PC_Y65_MAX (share aged 65+, direct) -> admin-1 65+ %.
// Covers DE/FR/IT/ES/PL in ONE keyless call. Resolves each Eurostat NUTS region to the map's ISO-3166-2
// geojson code via (1) an explicit NUTS->ISO CODEMAP where names don't match, else (2) normalised
// name-match against the geojson name/nameLocal (with bilingual "A/B" splitting). Multiple NUTS units
// mapping to one ISO unit are averaged (e.g. PL91+PL92 -> PL-MZ Mazowieckie).
// Writes public/data/aging/{cc}-admin1.json = {meta, byUnit}. Reports match rate + unmatched.
//   node scripts/build_aging_eurostat.mjs [year]   (default 2023)
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const ROOT = path.resolve(HERE, '..');
const OUT = path.join(ROOT, 'public', 'data');
const CACHE = path.join(ROOT, 'scripts', '_data_in', 'eurostat');
const YEAR = process.argv[2] || '2023';

// cc -> NUTS code length that matches the map's admin-1 units (3=NUTS-1, 4=NUTS-2, 5=NUTS-3)
const EU = { de: 3, pl: 4, fr: 5, it: 5, es: 5 };

// Explicit NUTS-code -> ISO-3166-2 crosswalks where the geojson name won't match the Eurostat label.
const CODEMAP = {
  // Poland: geojson uses English voivodeship names; Eurostat uses Polish. PL91+PL92 both -> PL-MZ (averaged).
  pl: {
    PL21: 'PL-MA', PL22: 'PL-SL', PL41: 'PL-WP', PL42: 'PL-ZP', PL43: 'PL-LB', PL51: 'PL-DS',
    PL52: 'PL-OP', PL61: 'PL-KP', PL62: 'PL-WN', PL63: 'PL-PM', PL71: 'PL-LD', PL72: 'PL-SK',
    PL81: 'PL-LU', PL82: 'PL-PK', PL84: 'PL-PD', PL91: 'PL-MZ', PL92: 'PL-MZ',
  },
  // Spain: Catalan/Galician/Basque vs Spanish naming, and Balearic/Canary structure.
  es: {
    ES111: 'ES-C', ES113: 'ES-OR', ES211: 'ES-VI', ES512: 'ES-GI', ES513: 'ES-L', ES521: 'ES-A',
    ES522: 'ES-CS', ES523: 'ES-V', ES531: 'ES-PM', ES532: 'ES-PM', ES533: 'ES-PM', ES630: 'ES-CE', ES640: 'ES-ML',
  },
};

const norm = (s) => (s || '').toString().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
  .replace(/[^a-z0-9]+/g, '').trim();

async function getEurostat() {
  fs.mkdirSync(CACHE, { recursive: true });
  const fp = path.join(CACHE, `pc_y65_max_${YEAR}.json`);
  if (fs.existsSync(fp) && fs.statSync(fp).size > 0) return JSON.parse(fs.readFileSync(fp, 'utf8'));
  const url = `https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_r_pjanind3?format=JSON&indic_de=PC_Y65_MAX&time=${YEAR}`;
  const j = await (await fetch(url, { headers: { 'User-Agent': 'brain-exposome/aging' } })).json();
  fs.writeFileSync(fp, JSON.stringify(j));
  return j;
}

function decoder(o) {
  const dims = o.id, sizes = o.size, stride = {};
  let s = 1; for (let i = dims.length - 1; i >= 0; i--) { stride[dims[i]] = s; s *= sizes[i]; }
  const geo = o.dimension.geo.category, unit = o.dimension.unit.category, val = o.value;
  const valOf = (code) => {
    const gi = geo.index[code]; if (gi == null) return null;
    for (const ui of Object.values(unit.index)) { const v = val[gi * stride.geo + ui * stride.unit]; if (v != null) return v; }
    return null;
  };
  return { geo, valOf };
}

// try a normalised name and, for bilingual "A/B" labels, each half
function nameKeys(label) {
  const keys = [norm(label)];
  if (label.includes('/')) for (const part of label.split('/')) keys.push(norm(part));
  return keys;
}

function build(cc, len, dec) {
  const feats = JSON.parse(fs.readFileSync(path.join(OUT, 'geo', `${cc}-admin1.geojson`), 'utf8')).features;
  const nameToIso = {};
  for (const f of feats) for (const nm of [f.properties.name, f.properties.nameLocal]) if (nm) nameToIso[norm(nm)] = f.properties.code;
  const CC = cc.toUpperCase();
  const nuts = Object.keys(dec.geo.index).filter((c) => c.startsWith(CC) && c.length === len);
  const map = CODEMAP[cc] || {};
  const acc = {};   // iso -> [values]
  const unmatched = [];
  for (const c of nuts) {
    const label = dec.geo.label[c];
    let iso = map[c];
    if (!iso) for (const k of nameKeys(label)) if (nameToIso[k]) { iso = nameToIso[k]; break; }
    if (!iso) { unmatched.push(`${c}=${label}`); continue; }
    const v = dec.valOf(c);
    if (v != null) (acc[iso] = acc[iso] || []).push(+v);
  }
  const byUnit = {};
  for (const [iso, vs] of Object.entries(acc)) byUnit[iso] = +(vs.reduce((a, b) => a + b, 0) / vs.length).toFixed(1);
  const vals = Object.values(byUnit);
  const nat = vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : null;
  return {
    json: {
      meta: {
        metric: 'share of population aged 65+ (%)', age_group: '65+', year: +YEAR,
        source: `Eurostat demo_r_pjanind3 (PC_Y65_MAX), NUTS-${len - 2}`, resolution: 'admin-1',
        method: '65+ share published directly by Eurostat; matched to admin-1 by NUTS code / region name',
        national_pct_unweighted: nat,
      },
      byUnit,
    },
    report: { total: feats.length, hit: Object.keys(byUnit).length, unmatched, range: vals.length ? `${Math.min(...vals)}-${Math.max(...vals)}` : 'n/a' },
  };
}

const dec = decoder(await getEurostat());
fs.mkdirSync(path.join(OUT, 'aging'), { recursive: true });
for (const [cc, len] of Object.entries(EU)) {
  const { json, report } = build(cc, len, dec);
  const ok = report.hit / report.total >= 0.9;
  if (ok) fs.writeFileSync(path.join(OUT, 'aging', `${cc}-admin1.json`), JSON.stringify(json));
  console.log(`${cc}: matched ${report.hit}/${report.total} (${(100 * report.hit / report.total).toFixed(0)}%) range ${report.range}%  ${ok ? 'WROTE' : 'NOT WRITTEN (<90%)'}`);
  if (report.unmatched.length) console.log(`   unmatched: ${report.unmatched.slice(0, 14).join(' | ')}${report.unmatched.length > 14 ? ' …' : ''}`);
}
