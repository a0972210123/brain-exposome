// Tier-2 aging: USA admin-1 65+ % from Census ACS 5-year subject table S0101 (C02_030E = % 65 and over),
// by state, mapped FIPS -> ISO-3166-2:US. Needs a free Census API key: CENSUS_KEY=... node scripts/build_aging_us.mjs
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const OUT = path.resolve(HERE, '..', 'public', 'data');
const KEY = process.env.CENSUS_KEY;
if (!KEY) { console.error('set CENSUS_KEY'); process.exit(1); }

const FIPS = { '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA', '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL', '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN', '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME', '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS', '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH', '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND', '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI', '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT', '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI', '56': 'WY' };

async function fetchYear(y) {
  const url = `https://api.census.gov/data/${y}/acs/acs5/subject?get=NAME,S0101_C02_030E&for=state:*&key=${KEY}`;
  const r = await fetch(url);
  if (!r.ok) return null;
  const txt = await r.text();
  if (txt.trim().startsWith('<') || txt.includes('valid key')) return null;
  return { y, rows: JSON.parse(txt) };
}

let res = await fetchYear(2024) || await fetchYear(2023);
if (!res) { console.error('census fetch failed (year/key?)'); process.exit(2); }

const byUnit = {};
for (const row of res.rows.slice(1)) {
  const [, pct, fips] = row;                 // NAME, value, state FIPS
  const p = FIPS[fips]; const v = parseFloat(pct);
  if (p && !isNaN(v)) byUnit[`US-${p}`] = v;
}
const vals = Object.values(byUnit);
const nat = +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
fs.writeFileSync(path.join(OUT, 'aging', 'us-admin1.json'), JSON.stringify({
  meta: { metric: 'share of population aged 65+ (%)', age_group: '65+', year: res.y,
    source: `US Census ACS 5-year ${res.y} (S0101_C02_030E)`, resolution: 'admin-1',
    method: 'published % 65+ by state; FIPS -> ISO-3166-2:US', national_pct_unweighted: nat },
  byUnit,
}));
console.log(`us: ${Object.keys(byUnit).length} states, year ${res.y}, range ${Math.min(...vals)}-${Math.max(...vals)}%`);
