/* Build-time schema.org nodes for the data layers.
   Everything here is read from each data file's own `meta`, so the schema follows the
   data instead of being hand-maintained. Fields that a layer does not record (licence,
   citation, units) are omitted rather than guessed.

   Scope note: this is for Google Dataset Search discoverability and the rich results
   that still exist. It is NOT an AI-citation lever — that comes from the crawlable
   tables and quotable sentences, see docs/dementia-exposome/seo-aeo-structured-data-plan.md */

import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const ROOT = process.cwd();
const DATA = join(ROOT, 'public', 'data');
const SITE = 'https://brain-exposome.mattye.dev';
const PERSON_ID = 'https://mattye.dev/#person';

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));
const uniq = (xs) => [...new Set(xs.filter(Boolean))];

let _regions = null;
function countryName(cc) {
  if (!_regions) {
    try { _regions = new Intl.DisplayNames(['en'], { type: 'region' }); } catch (e) { _regions = null; }
  }
  const iso = cc.toUpperCase();
  try {
    const n = _regions && _regions.of(iso);
    return n && n !== iso ? n : null;
  } catch (e) { return null; }
}

/* One entry per layer. `match` picks the files that carry this layer's numbers; the
   descriptions are the only prose here, everything else comes from the files. */
const LAYERS = [
  {
    key: 'aging',
    variable: 'Share of population aged 65 and over',
    dir: 'aging',
    match: (f) => f.endsWith('-admin1.json'),
    name: 'Sub-national population aged 65+ (admin-1)',
    description: 'Share of the population aged 65 and over for first-level administrative units, compiled per country from official statistics offices and WorldPop, each unit carrying its own source and reference year.',
  },
  {
    key: 'dementia',
    variable: 'Modelled dementia prevalence, residents aged 60 and over',
    dir: 'dementia',
    match: (f) => f.endsWith('.json'),
    name: 'Modelled sub-national dementia prevalence',
    description: 'Modelled dementia prevalence among residents aged 60 and over for sub-national units, derived from GBD age-specific rates applied to gridded population.',
  },
  {
    key: 'pm25',
    variable: 'Annual mean PM2.5 concentration',
    dir: 'pm25',
    match: (f) => f.endsWith('.json'),
    name: 'Sub-national fine particulate matter (PM2.5)',
    description: 'Annual mean fine particulate matter concentration aggregated to administrative units from satellite-derived surface estimates.',
  },
  {
    key: 'exposome',
    variable: 'Prevalence and population attributable fraction of modifiable dementia risk factors',
    dir: 'exposome',
    match: (f) => f.endsWith('.json'),
    name: 'Modifiable dementia risk factors and population attributable fractions',
    description: 'National adult prevalence of modifiable dementia risk factors from the Lancet 2024 Commission, with the population attributable fraction computed for each factor.',
  },
  {
    key: 'mci',
    variable: 'Mild cognitive impairment prevalence',
    dir: 'mci',
    match: (f) => f.endsWith('.json'),
    name: 'National mild cognitive impairment (MCI) prevalence',
    description: 'National MCI prevalence estimates built on a World Bank region baseline, with country values where published.',
  },
  {
    key: 'scd',
    variable: 'Subjective cognitive decline prevalence',
    dir: 'scd',
    match: (f) => f.endsWith('.json'),
    name: 'National subjective cognitive decline (SCD) prevalence',
    description: 'National subjective cognitive decline estimates. Self-reported and not harmonised across countries — see the file note before reuse.',
  },
];

/* Data vintage comes from `year` or `period` only. `built` is when the file was
   generated, which is not what the data covers — folding it in here would claim
   coverage the numbers do not have, so a layer that records only `built` gets no
   temporalCoverage at all. */
function temporalCoverage(metas) {
  const years = [];
  for (const m of metas) {
    for (const v of [m.year, m.period]) {
      if (v == null) continue;
      for (const y of String(v).match(/\d{4}/g) || []) years.push(Number(y));
    }
  }
  if (!years.length) return null;
  const lo = Math.min(...years), hi = Math.max(...years);
  return lo === hi ? String(lo) : `${lo}/${hi}`;
}

function layerDataset(layer) {
  const dir = join(DATA, layer.dir);
  if (!existsSync(dir)) return null;
  const files = readdirSync(dir).filter(layer.match).sort();
  if (!files.length) return null;

  const metas = [];
  const countries = [];
  for (const f of files) {
    let j;
    try { j = read(join(dir, f)); } catch (e) { continue; }
    if (j && j.meta) metas.push(j.meta);
    const cc = f.slice(0, 2);
    if (/^[a-z]{2}$/.test(cc) && f[2] === '-') {
      const n = countryName(cc);
      if (n) countries.push(n);
    }
  }
  if (!metas.length) return null;

  const node = {
    '@type': 'Dataset',
    '@id': `${SITE}/#dataset-${layer.key}`,
    name: layer.name,
    description: layer.description,
    creator: { '@id': PERSON_ID },
    isAccessibleForFree: true,
    includedInDataCatalog: { '@type': 'DataCatalog', name: 'Brain Exposome', url: SITE },
    distribution: files.map((f) => ({
      '@type': 'DataDownload',
      encodingFormat: 'application/json',
      contentUrl: `${SITE}/data/${layer.dir}/${f}`,
    })),
  };

  const temporal = temporalCoverage(metas);
  if (temporal) node.temporalCoverage = temporal;

  const places = uniq(countries);
  if (places.length) node.spatialCoverage = places.map((name) => ({ '@type': 'Place', name }));

  /* The measured variable is named per layer rather than taken from `meta.metric`:
     several layers put method prose and file references in that field, which reads
     badly as a schema value. Units still come from the data. */
  const units = uniq(metas.map((m) => m.units))[0];
  const variable = { '@type': 'PropertyValue', name: layer.variable };
  if (units) variable.unitText = units;
  node.variableMeasured = variable;

  const sources = uniq(metas.flatMap((m) => [m.source, m.rr_source]));
  if (sources.length) node.isBasedOn = sources;

  const citations = uniq(metas.map((m) => m.citation));
  if (citations.length) node.citation = citations;

  /* A licence is only claimed when EVERY file in the layer records one and they agree.
     One file's licence is not the layer's: the dementia layer has a single Taiwan file
     carrying OGDL-Taiwan-1.0 for its boundaries, which says nothing about the rest.
     The repo has no LICENSE file, so an unstated licence stays unstated. */
  const licenses = metas.map((m) => m.license);
  const stated = uniq(licenses);
  if (stated.length === 1 && licenses.every(Boolean)) node.license = stated[0];

  return node;
}

/* Newest `built` date across every layer — a fact we can state, unlike a human
   "last reviewed" claim, which is why `lastReviewed` is deliberately absent below. */
export function dataLastBuilt() {
  const dates = [];
  for (const layer of LAYERS) {
    const dir = join(DATA, layer.dir);
    if (!existsSync(dir)) continue;
    for (const f of readdirSync(dir).filter(layer.match)) {
      try {
        const m = read(join(dir, f)).meta;
        if (m && m.built) dates.push(m.built);
      } catch (e) { /* a file without meta simply does not contribute a date */ }
    }
  }
  return dates.length ? dates.sort().at(-1) : null;
}

export function datasetNodes() {
  return LAYERS.map(layerDataset).filter(Boolean);
}

export function appNode() {
  return {
    '@type': 'WebApplication',
    '@id': `${SITE}/#webapp`,
    name: 'Brain Exposome Check-in',
    url: SITE,
    applicationCategory: 'HealthApplication',
    operatingSystem: 'Any modern web browser',
    isAccessibleForFree: true,
    browserRequirements: 'Requires JavaScript. All calculation runs in the browser; no data is uploaded.',
    author: { '@id': PERSON_ID },
    featureList: [
      'Brain-age acceleration estimate from the Lancet 2024 modifiable risk factors',
      'Cumulative PM2.5 exposure from residence history',
      'Global map of aging, dementia prevalence and risk factors',
      'Sub-national (admin-1) drill-down for 26 countries',
      'Per-country data provenance and coverage table',
    ],
  };
}

export function medicalPageNode(lastBuilt) {
  const node = {
    '@type': 'MedicalWebPage',
    '@id': `${SITE}/#medicalwebpage`,
    url: SITE,
    inLanguage: 'zh-TW',
    about: {
      '@type': 'MedicalCondition',
      name: 'Dementia',
      alternateName: '失智症',
      code: { '@type': 'MedicalCode', codeValue: 'F03', codingSystem: 'ICD-10' },
    },
    audience: { '@type': 'Audience', audienceType: 'General public' },
    /* Kept verbatim from the page's own disclaimer — MedicalWebPage raises the bar on
       health claims, so the educational framing has to travel with the markup. */
    disambiguatingDescription: 'Educational self-assessment tool. The brain-age figure is a modelled educational reference value, not a medical diagnosis or individual medical advice.',
    author: { '@id': PERSON_ID },
  };
  if (lastBuilt) node.dateModified = lastBuilt;
  return node;
}

/* Everything this page adds to BaseLayout's @graph. */
export function structuredData() {
  const lastBuilt = dataLastBuilt();
  return [appNode(), medicalPageNode(lastBuilt), ...datasetNodes()];
}
