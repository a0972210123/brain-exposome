// Tier-2 aging: China admin-1 65+ % — 2020 Seventh National Census (per-province 公报), fallback for the
// geoblocked data.stats.gov.cn portal. Values verified against each provincial bureau's census communiqué
// (see docs/dementia-exposome/aging-fetch-guide.md). Maps English province name -> ISO-3166-2:CN geojson code.
//   node scripts/build_aging_cn.mjs
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const OUT = path.resolve(HERE, '..', 'public', 'data');

// 2020 census 65+ % per province (national anchor 13.50%). Subagent-verified vs provincial communiqués.
const CN = [
  ['Beijing', 13.30], ['Shanghai', 16.28], ['Tianjin', 14.75], ['Chongqing', 17.08], ['Hebei', 13.92],
  ['Shanxi', 12.90], ['Inner Mongolia', 13.05], ['Liaoning', 17.42], ['Jilin', 15.61], ['Heilongjiang', 15.61],
  ['Jiangsu', 16.20], ['Zhejiang', 13.27], ['Anhui', 15.01], ['Fujian', 11.10], ['Jiangxi', 11.89],
  ['Shandong', 15.13], ['Henan', 13.49], ['Hubei', 14.59], ['Hunan', 14.81], ['Guangdong', 8.58],
  ['Guangxi', 12.20], ['Hainan', 10.43], ['Sichuan', 16.93], ['Guizhou', 11.56], ['Yunnan', 10.75],
  ['Tibet', 5.67], ['Shaanxi', 13.32], ['Gansu', 12.58], ['Qinghai', 8.68], ['Ningxia', 9.62], ['Xinjiang', 7.76],
];
const OVERRIDE = { tibet: 'CN-XZ', xizang: 'CN-XZ', innermongolia: 'CN-NM' };  // name-variant safety net

const norm = (s) => (s || '').toLowerCase().replace(/[^a-z0-9]+/g, '');
const feats = JSON.parse(fs.readFileSync(path.join(OUT, 'geo', 'cn-admin1.geojson'), 'utf8')).features;
const nameToIso = {};
for (const f of feats) for (const nm of [f.properties.name, f.properties.nameLocal]) if (nm) nameToIso[norm(nm)] = f.properties.code;

const byUnit = {}, missing = [];
for (const [en, pct] of CN) {
  const iso = nameToIso[norm(en)] || OVERRIDE[norm(en)];
  if (iso) byUnit[iso] = pct; else missing.push(en);
}
const vals = Object.values(byUnit);
const nat = +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);
fs.writeFileSync(path.join(OUT, 'aging', 'cn-admin1.json'), JSON.stringify({
  meta: { metric: 'share of population aged 65+ (%)', age_group: '65+', year: 2020,
    source: 'China 2020 Seventh National Population Census (provincial communiqués / NBS)', resolution: 'admin-1',
    method: 'per-province 65+ share from the 2020 census; matched to ISO-3166-2:CN by name', national_pct_unweighted: nat },
  byUnit,
}));
console.log(`cn: ${Object.keys(byUnit).length}/${feats.length} matched, range ${Math.min(...vals)}-${Math.max(...vals)}%`);
if (missing.length) console.log('UNMATCHED:', missing.join(', '));
