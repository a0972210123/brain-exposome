/* Guards the generated schema.org nodes. Most of these assertions exist because the
   first version of the generator over-claimed: it copied one file's licence onto a
   whole layer, and folded build dates into temporal coverage.
   Run: node tests/structured-data.test.mjs */

import assert from 'node:assert/strict';
import { structuredData, datasetNodes, dataLastBuilt } from '../src/lib/dataset-ld.mjs';

const graph = structuredData();
const datasets = datasetNodes();

assert.equal(graph.length, 8, `expected 8 nodes, got ${graph.length}`);
assert.equal(datasets.length, 6, `expected 6 Dataset nodes, got ${datasets.length}`);

// Every node must be addressable and typed, and the whole graph must be real JSON.
const ids = graph.map((n) => n['@id']);
assert.equal(new Set(ids).size, ids.length, `duplicate @id in graph: ${ids.join(', ')}`);
for (const n of graph) {
  assert.ok(n['@type'], 'node without @type');
  assert.ok(n['@id'], `${n['@type']} without @id`);
}
assert.deepEqual(JSON.parse(JSON.stringify(graph)), graph, 'graph must survive a JSON round-trip');

const by = (key) => datasets.find((d) => d['@id'].endsWith(`#dataset-${key}`));

// A licence is only claimed when every file in the layer states the same one.
// The dementia layer has a single Taiwan file carrying OGDL-Taiwan-1.0 for its
// boundaries; an earlier version promoted that to the whole layer.
assert.equal(by('dementia').license, undefined, 'dementia must not inherit one file\'s licence');
assert.equal(by('pm25').license, 'CC BY 4.0', 'pm25 states CC BY 4.0 on every file');

// `built` is a generation date, not data coverage. A layer that records only `built`
// must have no temporalCoverage rather than a misleading one.
assert.equal(by('dementia').temporalCoverage, undefined, 'dementia records no data year');
assert.match(by('pm25').temporalCoverage, /^2022\/20\d\d$/, 'pm25 covers a real observation span');
assert.match(by('aging').temporalCoverage, /^\d{4}\/\d{4}$/, 'aging spans several census years');
for (const d of datasets) {
  if (d.temporalCoverage) {
    assert.ok(!/\/2026$/.test(d.temporalCoverage) || d['@id'].endsWith('#dataset-aging'),
      `${d.name}: temporalCoverage ending 2026 looks like a build date leak`);
  }
}

// Data-driven fields must actually be populated from the files.
assert.equal(by('aging').distribution.length, 26, 'one DataDownload per aging file');
assert.equal(by('aging').spatialCoverage.length, 26, 'one Place per aging country');
assert.ok(by('aging').isBasedOn.length > 10, 'aging cites many national statistics offices');
assert.equal(by('pm25').variableMeasured.unitText, 'ug/m3', 'units come from the data');
for (const d of datasets) {
  assert.ok(d.variableMeasured && d.variableMeasured.name, `${d.name}: missing variableMeasured`);
  assert.ok(!/\.json/.test(d.variableMeasured.name), `${d.name}: variable name leaks a filename`);
  assert.ok(d.distribution.length > 0, `${d.name}: no distribution`);
  for (const dl of d.distribution) {
    assert.match(dl.contentUrl, /^https:\/\/brain-exposome\.mattye\.dev\/data\//, 'absolute data URL');
  }
}

// MedicalWebPage: the educational framing has to travel with the markup, and we do not
// claim a human review date we cannot evidence.
const med = graph.find((n) => n['@type'] === 'MedicalWebPage');
assert.equal(med.lastReviewed, undefined, 'no unevidenced lastReviewed claim');
assert.match(med.disambiguatingDescription, /not a medical diagnosis/i, 'disclaimer must be present');
assert.equal(med.about.code.codeValue, 'F03');
assert.equal(med.dateModified, dataLastBuilt(), 'dateModified tracks the newest data build');

const app = graph.find((n) => n['@type'] === 'WebApplication');
assert.equal(app.applicationCategory, 'HealthApplication');
assert.ok(app.featureList.length >= 4);

console.log(`ok — ${graph.length} nodes, ${datasets.length} datasets, `
  + `${datasets.reduce((n, d) => n + d.distribution.length, 0)} distributions, `
  + `last built ${dataLastBuilt()}`);
