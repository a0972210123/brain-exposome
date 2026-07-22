// Tier-2 aging (non-EU official APIs): fetch admin-1 65+ % from each country's statistics office
// and map to the map's ISO-3166-2 geojson codes. Writes public/data/aging/{cc}-admin1.json.
//   node scripts/build_aging_tier2.mjs [cc ...]   (default: all implemented)
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const OUT = path.resolve(HERE, '..', 'public', 'data');
const AGE = path.join(OUT, 'aging');

const jget = async (url, headers = {}) => (await fetch(url, { headers: { 'User-Agent': 'brain-exposome/aging', ...headers } })).json();
const tget = async (url, headers = {}) => (await fetch(url, { headers: { 'User-Agent': 'brain-exposome/aging', ...headers } })).text();

function write(cc, byUnit, meta) {
  const vals = Object.values(byUnit).filter((x) => x != null);
  const total = JSON.parse(fs.readFileSync(path.join(OUT, 'geo', `${cc}-admin1.geojson`), 'utf8')).features.length;
  const nat = vals.length ? +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : null;
  fs.mkdirSync(AGE, { recursive: true });
  fs.writeFileSync(path.join(AGE, `${cc}-admin1.json`), JSON.stringify({ meta: { ...meta, national_pct_unweighted: nat }, byUnit }));
  console.log(`${cc}: ${Object.keys(byUnit).length}/${total} units, range ${vals.length ? Math.min(...vals) + '-' + Math.max(...vals) : 'n/a'}%  WROTE`);
}

// ── BR — IBGE SIDRA/agregados table 9514, Census 2022, variable 1000093 (% of total) ──
const BR_UF = { 11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO', 21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA', 31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP', 41: 'PR', 42: 'SC', 43: 'RS', 50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF' };
async function br() {
  const meta = await jget('https://servicodados.ibge.gov.br/api/v3/agregados/9514/metadados');
  const cl = meta.classificacoes.find((c) => c.id === 287);
  const groups = cl.categorias.filter((c) => /^(6[5-9]|[7-9][0-9]) a [0-9]+ anos$/.test(c.nome) || /^100 anos ou mais$/.test(c.nome)).map((c) => c.id);
  const url = `https://servicodados.ibge.gov.br/api/v3/agregados/9514/periodos/2022/variaveis/1000093?localidades=N3[all]&classificacao=287[${groups.join(',')}]`;
  const data = await jget(url);
  const byId = {};
  for (const res of data[0].resultados) {
    for (const s of res.series) {
      const uf = +s.localidade.id, v = parseFloat(s.serie['2022']);
      if (!isNaN(v)) byId[uf] = (byId[uf] || 0) + v;
    }
  }
  const byUnit = {};
  for (const [uf, v] of Object.entries(byId)) { const iso = BR_UF[uf] && `BR-${BR_UF[uf]}`; if (iso) byUnit[iso] = +v.toFixed(1); }
  write('br', byUnit, { metric: 'share of population aged 65+ (%)', age_group: '65+', year: 2022, source: 'IBGE Censo 2022 (SIDRA 9514)', resolution: 'admin-1', method: 'sum of 65+ 5-year-group shares by UF' });
}

const IMPL = { br };
const ccs = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(IMPL);
for (const cc of ccs) {
  if (!IMPL[cc]) { console.log(`${cc}: not implemented`); continue; }
  try { await IMPL[cc](); } catch (e) { console.log(`${cc}: FAILED — ${e.message}`); }
}
