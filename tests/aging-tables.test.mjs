/* Guards the build-time table data: the numbers must survive the JSON → row → sentence
   path with their unit names and sources intact. Run: node tests/aging-tables.test.mjs */

import assert from 'node:assert/strict';
import { agingTables, agingSentence } from '../src/lib/aging-tables.mjs';
import { dpTableHtml, makeRegionNamer } from '../src/lib/dp-table.mjs';
import { readFileSync } from 'node:fs';

const aging = agingTables('zh');

assert.equal(aging.length, 26, 'expected 26 countries with an admin-1 aging file');

const total = aging.reduce((n, c) => n + c.units.length, 0);
assert.ok(total > 1400, `expected >1400 admin-1 units, got ${total}`);

for (const c of aging) {
  assert.ok(c.meta.source, `${c.cc}: missing meta.source`);
  assert.ok(c.meta.year, `${c.cc}: missing meta.year`);
  // Descending sort is what makes the visible top-N the interesting end.
  for (let i = 1; i < c.units.length; i++) {
    assert.ok(c.units[i - 1].pct >= c.units[i].pct, `${c.cc}: units not sorted desc`);
  }
  assert.equal(c.unnamed, c.units.filter(u => !u.named).length, `${c.cc}: unnamed count out of sync`);
}

/* Only Taiwan's 4 MOI household-registration sub-districts (三民/鳳山 split codes) lack a
   name; the registry already records "366/370 match map". Everything else must be named —
   if this number grows, a geo file changed and rows silently became uncitable. */
const unnamedByCc = Object.fromEntries(aging.filter(c => c.unnamed).map(c => [c.cc, c.unnamed]));
assert.deepEqual(unnamedByCc, { tw: 4 }, `unexpected unnamed units: ${JSON.stringify(unnamedByCc)}`);

// Türkiye is the case the source registry warns about — check it end to end.
const tr = aging.find(c => c.cc === 'tr');
assert.equal(tr.units.length, 81, 'TR should have 81 provinces');
const trZh = agingSentence(tr, 'zh');
assert.ok(trZh.includes('TÜİK'), 'zh sentence should carry the source');
assert.ok(/\d+(\.\d+)?%/.test(trZh), 'zh sentence should carry a percentage');
assert.ok(agingSentence(tr, 'en').startsWith('In '), 'en sentence should read as English prose');

// Taiwan comes from a topojson, not a geojson — the one shape exception.
const tw = aging.find(c => c.cc === 'tw');
assert.ok(tw.units[0].nameLocal.length > 1 && !/^\d+$/.test(tw.units[0].nameLocal), 'TW units should be named, not numeric codes');

// Provenance table renders every country and escapes nothing away.
const provenance = JSON.parse(readFileSync(new URL('../public/data/data-provenance.json', import.meta.url), 'utf8'));
const namer = makeRegionNamer();
const dp = dpTableHtml(provenance, { type: 'aging', lang: 'zh', name: (iso) => namer(iso, 'zh') });
assert.equal(dp.count, provenance.iso.length, 'unfiltered dp table should list every ISO entry');
assert.equal((dp.html.match(/<tr>/g) || []).length, dp.count + 1, 'dp table rows should equal countries + header');

// Filtering and onlyData still narrow the same way the UI expects.
const filtered = dpTableHtml(provenance, { type: 'aging', lang: 'zh', name: (iso) => namer(iso, 'zh'), filter: 'TW' });
assert.ok(filtered.count >= 1 && filtered.count < dp.count, 'filter should narrow the row set');

console.log(`ok — ${aging.length} countries, ${total} admin-1 units, ${dp.count} provenance rows`);
