#!/usr/bin/env node
// Tier-2 aging: Turkey admin-1 (81 provinces) 65+ % from TÜİK ADNKS 2024 (Address Based Population
// Registration System) table "İl, tek yaş ve cinsiyete göre nüfus" (population by province, single age
// and sex), press release pid=53783. 65+ = sum(single ages 65..74) + the 75+ terminal bucket, per
// province's Toplam-Total row, / province total. Province order is Turkish plate code 01..81 = ISO-3166-2:TR.
//
// Values below are the ADNKS 2024 figures captured & validated from the source .xls (national total
// checksummed at 85,664,944; İstanbul 15,701,602; Bayburt 83,676 smallest — all match the bulletin).
// The .xls download endpoint (veriportali.tuik.gov.tr/api/tr/data/downloads?t=i&pid=53783&p=<token>) is
// WAF-gated against plain curl, so figures are embedded rather than live-fetched (same pattern as
// build_aging_cn.mjs). Refresh for the 2025 edition (due Feb 2026): re-capture via a browser-context
// fetch of that endpoint (token is long-lived; drop any client-appended ts= param). Writes
// public/data/aging/tr-admin1.json.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const OUT = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'public', 'data', 'aging');

// [ISO-3166-2:TR (plate), province, total pop 2024, 65+ count]
const D = [
  ['TR-01', 'Adana', 2280484, 228892], ['TR-02', 'Adıyaman', 611037, 54669],
  ['TR-03', 'Afyonkarahisar', 750193, 94864], ['TR-04', 'Ağrı', 499801, 29007],
  ['TR-05', 'Amasya', 342378, 56263], ['TR-06', 'Ankara', 5864049, 610643],
  ['TR-07', 'Antalya', 2722103, 274650], ['TR-08', 'Artvin', 169280, 31550],
  ['TR-09', 'Aydın', 1165943, 181602], ['TR-10', 'Balıkesir', 1276096, 222961],
  ['TR-11', 'Bilecik', 228495, 29750], ['TR-12', 'Bingöl', 283276, 23843],
  ['TR-13', 'Bitlis', 359808, 21784], ['TR-14', 'Bolu', 326409, 49356],
  ['TR-15', 'Burdur', 275826, 46752], ['TR-16', 'Bursa', 3238618, 351288],
  ['TR-17', 'Çanakkale', 568966, 97718], ['TR-18', 'Çankırı', 199981, 35389],
  ['TR-19', 'Çorum', 521335, 89781], ['TR-20', 'Denizli', 1061371, 135904],
  ['TR-21', 'Diyarbakır', 1833684, 99991], ['TR-22', 'Edirne', 421247, 72535],
  ['TR-23', 'Elazığ', 603941, 69638], ['TR-24', 'Erzincan', 241239, 33528],
  ['TR-25', 'Erzurum', 745005, 74436], ['TR-26', 'Eskişehir', 921630, 121047],
  ['TR-27', 'Gaziantep', 2193363, 133975], ['TR-28', 'Giresun', 455922, 86993],
  ['TR-29', 'Gümüşhane', 142617, 21967], ['TR-30', 'Hakkari', 282191, 12186],
  ['TR-31', 'Hatay', 1562185, 139458], ['TR-32', 'Isparta', 446409, 66903],
  ['TR-33', 'Mersin', 1954279, 212680], ['TR-34', 'İstanbul', 15701602, 1302793],
  ['TR-35', 'İzmir', 4493242, 598004], ['TR-36', 'Kars', 272300, 26203],
  ['TR-37', 'Kastamonu', 381991, 77163], ['TR-38', 'Kayseri', 1452458, 151747],
  ['TR-39', 'Kırklareli', 379031, 61600], ['TR-40', 'Kırşehir', 244546, 35086],
  ['TR-41', 'Kocaeli', 2130006, 183578], ['TR-42', 'Konya', 2330024, 251997],
  ['TR-43', 'Kütahya', 571078, 86275], ['TR-44', 'Malatya', 750491, 90554],
  ['TR-45', 'Manisa', 1475353, 194022], ['TR-46', 'Kahramanmaraş', 1134105, 108600],
  ['TR-47', 'Mardin', 895911, 53487], ['TR-48', 'Muğla', 1081867, 153117],
  ['TR-49', 'Muş', 392301, 24502], ['TR-50', 'Nevşehir', 317952, 41726],
  ['TR-51', 'Niğde', 372708, 42625], ['TR-52', 'Ordu', 770711, 127498],
  ['TR-53', 'Rize', 346977, 52124], ['TR-54', 'Sakarya', 1110735, 125987],
  ['TR-55', 'Samsun', 1382376, 189022], ['TR-56', 'Siirt', 336453, 19382],
  ['TR-57', 'Sinop', 226957, 47291], ['TR-58', 'Sivas', 637007, 92316],
  ['TR-59', 'Tekirdağ', 1187162, 121036], ['TR-60', 'Tokat', 612674, 97222],
  ['TR-61', 'Trabzon', 822270, 121714], ['TR-62', 'Tunceli', 86612, 14710],
  ['TR-63', 'Şanlıurfa', 2237745, 97726], ['TR-64', 'Uşak', 375310, 53201],
  ['TR-65', 'Van', 1118087, 56745], ['TR-66', 'Yozgat', 413161, 63630],
  ['TR-67', 'Zonguldak', 586802, 92878], ['TR-68', 'Aksaray', 439474, 46395],
  ['TR-69', 'Bayburt', 83676, 10616], ['TR-70', 'Karaman', 262791, 31998],
  ['TR-71', 'Kırıkkale', 283053, 39581], ['TR-72', 'Batman', 654528, 32940],
  ['TR-73', 'Şırnak', 570826, 21025], ['TR-74', 'Bartın', 206715, 34025],
  ['TR-75', 'Ardahan', 91354, 13598], ['TR-76', 'Iğdır', 206857, 16421],
  ['TR-77', 'Yalova', 307882, 41753], ['TR-78', 'Karabük', 250478, 38335],
  ['TR-79', 'Kilis', 156739, 12735], ['TR-80', 'Osmaniye', 561061, 56376],
  ['TR-81', 'Düzce', 412344, 48936],
];

const CHECKSUM = 85664944;   // national total from the bulletin; guards against transcription slips
const sumTot = D.reduce((s, r) => s + r[2], 0);
if (D.length !== 81) throw new Error(`expected 81 provinces, got ${D.length}`);
if (sumTot !== CHECKSUM) throw new Error(`total ${sumTot} != national ${CHECKSUM} (transcription error)`);

const byUnit = {};
for (const [iso, , tot, o65] of D) {
  if (o65 >= tot) throw new Error(`${iso}: 65+ ${o65} >= total ${tot}`);
  byUnit[iso] = +(100 * o65 / tot).toFixed(1);
}
const vals = Object.values(byUnit);
const nat = +(vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1);

fs.mkdirSync(OUT, { recursive: true });
fs.writeFileSync(path.join(OUT, 'tr-admin1.json'), JSON.stringify({
  meta: {
    metric: 'share of population aged 65+ (%)', age_group: '65+', year: 2024,
    source: 'TÜİK ADNKS 2024 — population by province, single age & sex (press 53783)', resolution: 'admin-1',
    method: '(ages 65-74 + 75+) / total per province; Turkish plate order = ISO-3166-2:TR',
    national_pct_unweighted: nat,
  },
  byUnit,
}, null, 0), 'utf8');
console.log(`tr: ${vals.length} provinces, range ${Math.min(...vals)}-${Math.max(...vals)}%, nat ${nat} | checksum ok`);
