#!/usr/bin/env node
// Tier-2 aging: Iran admin-1 (31 ostans) 65+ % from the 2016 national census (Statistical Centre of
// Iran), via the UN OCHA / HDX common-operational-dataset mirror (English province names + 5-year age
// bins). 65+ = sum(T_65_69..T_100Plus) / T_TL per province. Live-fetch (no manual download).
//
// Note on codes: this map's ir geojson labels BOTH Tehran and Alborz as IR-07 (Alborz split from
// Tehran in 2010; the geojson never adopted IR-32). Two polygons can't hold two values, so Tehran+Alborz
// are merged into one population-weighted IR-07 figure. Writes public/data/aging/ir-admin1.json.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '..', 'public', 'data', 'aging');
const CSV = 'https://data.humdata.org/dataset/07f4ec78-42c7-4606-ae62-4f1bff918c45/resource/5e9b5713-9d1a-4d90-90b3-e0861a994e88/download/irn_admpop_adm1_2016_v2.csv';

const norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
// CSV ADM1_EN (normalised) -> ISO-3166-2:IR (matches this map's ir geojson codes)
const ISO = Object.fromEntries(Object.entries({
  'East Azerbaijan': 'IR-01', 'West Azerbaijan': 'IR-02', 'Ardabil': 'IR-03', 'Isfahan': 'IR-04',
  'Ilam': 'IR-05', 'Bushehr': 'IR-06', 'Tehran': 'IR-07', 'Alborz': 'IR-07',
  'Chaharmahal and Bakhtiari': 'IR-08', 'Khuzestan': 'IR-10', 'Zanjan': 'IR-11', 'Semnan': 'IR-12',
  'Sistan and Baluchestan': 'IR-13', 'Fars': 'IR-14', 'Kerman': 'IR-15', 'Kurdistan': 'IR-16',
  'Kermanshah': 'IR-17', 'Kohgiluyeh and Boyer-Ahmad': 'IR-18', 'Gilan': 'IR-19', 'Lorestan': 'IR-20',
  'Mazandaran': 'IR-21', 'Markazi': 'IR-22', 'Hormozgan': 'IR-23', 'Hamadan': 'IR-24', 'Yazd': 'IR-25',
  'Qom': 'IR-26', 'Golestan': 'IR-27', 'Qazvin': 'IR-28', 'South Khorasan': 'IR-29',
  'Razavi Khorasan': 'IR-30', 'North Khorasan': 'IR-31',
}).map(([k, v]) => [norm(k), v]));

const OLD = ['T_65_69', 'T_70_74', 'T_75_79', 'T_80_84', 'T_85_89', 'T_90_94', 'T_95_99', 'T_100Plus'];

const text = await (await fetch(CSV)).text();
const rows = text.split(/\r?\n/).filter(Boolean).map(r => r.split(','));
const H = rows[0];
const iEn = H.indexOf('ADM1_EN'), iTot = H.indexOf('T_TL');
const iOld = OLD.map(c => H.indexOf(c));

const acc = {}, miss = [];           // ISO -> [total, 65plus] (accumulates Tehran+Alborz into IR-07)
for (const r of rows.slice(1)) {
  const iso = ISO[norm(r[iEn])];
  if (!iso) { miss.push(r[iEn]); continue; }
  const tot = +r[iTot], o65 = iOld.reduce((s, i) => s + (+r[i] || 0), 0);
  const a = acc[iso] || (acc[iso] = [0, 0]);
  a[0] += tot; a[1] += o65;
}

const byUnit = {};
for (const [iso, [tot, o65]] of Object.entries(acc)) if (tot) byUnit[iso] = +(100 * o65 / tot).toFixed(1);
const vals = Object.values(byUnit);
const nat = +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);

fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'ir-admin1.json'), JSON.stringify({
  meta: {
    metric: 'share of population aged 65+ (%)', age_group: '65+', year: 2016,
    source: 'Statistical Centre of Iran, 2016 census (via UN OCHA/HDX COD-PS mirror)', resolution: 'admin-1',
    method: 'sum 65+ 5-year groups / total per province; Tehran+Alborz merged into IR-07 (shared geojson code)',
    national_pct_unweighted: nat,
  },
  byUnit,
}, null, 0), 'utf8');
console.log(`ir: ${vals.length} units, range ${Math.min(...vals)}-${Math.max(...vals)}%, nat ${nat}` + (miss.length ? ` | MISS ${miss}` : ''));
