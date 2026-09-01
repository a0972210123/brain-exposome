/* Data-provenance table markup — shared by the build (SSR) and the client script.
   Kept pure (no fs, no DOM) so the same function renders the initial HTML at build
   time and every re-render after a tab / filter / language change. */

const BADGES = {
  live: ['✅', 'dp-live'],
  seed: ['◐', 'dp-seed'],
  identified: ['○', 'dp-id'],
  none: ['—', 'dp-none'],
};

export function dpBadge(status) {
  const [sym, cls] = BADGES[status] || BADGES.none;
  return `<span class="dp-badge ${cls}" title="${status}">${sym}</span>`;
}

function dpCell(o, k) {
  const src = o[k + 'Src'], url = o[k + 'Url'], yr = o[k + 'Year'];
  const s = (!src || src === '—') ? '—' : (url ? `<a href="${url}" target="_blank" rel="noopener">${src}</a>` : src);
  return { src: s, yr: yr || '—' };
}

/* Rows for one data type, filtered and sorted exactly as the table shows them.
   `name` maps an ISO code to a display name (Intl.DisplayNames in both runtimes). */
export function dpRows(DP, { type, lang, name, filter = '', onlyData = false }) {
  const t = DP.types.find(x => x.key === type) || DP.types[0];
  const q = filter.trim().toLowerCase();
  return DP.iso
    .map(iso => ({ iso, name: name(iso), o: (DP.overrides[iso] && DP.overrides[iso][type]) || t.default }))
    .filter(r => !q || r.name.toLowerCase().includes(q) || r.iso.toLowerCase().includes(q))
    .filter(r => !onlyData || r.o.status === 'live' || r.o.status === 'seed')
    .sort((a, b) => a.name.localeCompare(b.name, lang === 'en' ? 'en' : 'zh-Hant'));
}

export function dpTableHtml(DP, opts) {
  const { lang } = opts;
  const L = (zh, en) => (lang === 'en' ? en : zh);
  const rows = dpRows(DP, opts);
  const head = `<tr><th scope="col">${L('國家/地區', 'Country')}</th><th scope="col">${L('國家級來源', 'National source')}</th><th scope="col">${L('年份', 'Year')}</th>`
    + `<th scope="col">${L('省縣級來源', 'Sub-national source')}</th><th scope="col">${L('年份', 'Year')}</th><th scope="col">${L('狀態', 'Status')}</th></tr>`;
  const body = rows.map(r => {
    const n = dpCell(r.o, 'nat'), s = dpCell(r.o, 'sub');
    /* Country stays a <td>: the table's <th> rule is a sticky uppercase header style,
       so a row-header here would change how it looks. */
    return `<tr><td class="dp-country">${r.name}</td><td>${n.src}</td><td class="dp-yr">${n.yr}</td>`
      + `<td>${s.src}</td><td class="dp-yr">${s.yr}</td><td>${dpBadge(r.o.status)}</td></tr>`;
  }).join('');
  const caption = L('各國資料齊全度與來源', 'Data coverage and sources by country');
  return {
    html: `<table class="dp-table"><caption class="visually-hidden">${caption}</caption><thead>${head}</thead><tbody>${body}</tbody></table>`,
    count: rows.length,
  };
}

/* Country display name, memoised per locale. Same call in Node and the browser. */
export function makeRegionNamer() {
  const cache = {};
  return (iso, lang) => {
    const lg = lang === 'en' ? 'en' : 'zh-Hant';
    if (!(lg in cache)) {
      try { cache[lg] = new Intl.DisplayNames([lg], { type: 'region' }); } catch (e) { cache[lg] = null; }
    }
    try { return (cache[lg] && cache[lg].of(iso)) || iso; } catch (e) { return iso; }
  };
}
