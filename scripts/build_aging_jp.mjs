// Tier-2 aging: Japan admin-1 65+ % from e-Stat Census 2020 (statsDataId 0003448299): tab=105 (割合/ratio),
// cat01=130 (65歳以上), cat02=100 (total), area = prefecture (XX000). Maps prefecture code -> ISO-3166-2:JP.
//   ESTAT_APPID=... node scripts/build_aging_jp.mjs
import fs from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1'));
const OUT = path.resolve(HERE, '..', 'public', 'data');
const K = process.env.ESTAT_APPID;
if (!K) { console.error('set ESTAT_APPID'); process.exit(1); }

const url = `https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData?appId=${K}&statsDataId=0003448299&cdTab=105&cdCat01=130&cdCat02=100`;
const o = await (await fetch(url)).json();
const sd = o.GET_STATS_DATA;
if (sd.RESULT.STATUS !== 0) { console.error('e-Stat error:', sd.RESULT.ERROR_MSG); process.exit(2); }
const vals = sd.STATISTICAL_DATA.DATA_INF.VALUE;

const byUnit = {};
for (const v of vals) {
  const m = /^(\d\d)000$/.exec(v['@area']);          // prefecture only (XX000), skip municipalities + 00000 national
  if (!m || m[1] === '00') continue;
  const pct = parseFloat(v.$);
  if (!isNaN(pct)) byUnit[`JP-${m[1]}`] = +pct.toFixed(1);
}
const arr = Object.values(byUnit);
const nat = +(arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(1);
fs.writeFileSync(path.join(OUT, 'aging', 'jp-admin1.json'), JSON.stringify({
  meta: { metric: 'share of population aged 65+ (%)', age_group: '65+', year: 2020,
    source: 'Japan 2020 Census via e-Stat (0003448299, 年齢別割合)', resolution: 'admin-1',
    method: 'published 65+ share by prefecture; JIS code -> ISO-3166-2:JP', national_pct_unweighted: nat },
  byUnit,
}));
console.log(`jp: ${arr.length} prefectures, range ${Math.min(...arr)}-${Math.max(...arr)}%, nat ${nat}`);
