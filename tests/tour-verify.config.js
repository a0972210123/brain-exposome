// Tour health check — Toutour Pro verification harness config.
//
// The harness itself (verify/tour-verify.mjs) is part of the commercial Toutour Pro
// bundle and is intentionally NOT vendored into this public repo. Run it from your
// local Pro checkout:
//
//   cd brain-exposome && npm run build
//   npx serve dist -l 8080          # or any static server on :8080
//   node /path/to/Toutour-pro/verify/tour-verify.mjs ./tests/tour-verify.config.js
//
// Re-run after ANY UI change to catch broken selectors and step drift (Phase 6).

export default {
  url: 'http://localhost:8080/',
  chromium: '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',

  spot: '#ttSpot', tip: '#ttTip', next: '#ttNext', count: '#ttCount',

  settle: 1200,     // the page fetches PM2.5 + geo JSON before the wizard is usable
  stepPause: 500,

  start: async (page) => { await page.evaluate(() => window.__startTour && window.__startTour()); },

  viewports: [
    { name: 'desktop', width: 1280, height: 800 },
    { name: 'mobile', width: 390, height: 844, isMobile: true },
  ],

  themes: [
    { name: 'light', apply: async (page) => { await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light')); } },
    { name: 'dark', apply: async (page) => { await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark')); } },
  ],

  // Main tour — mirrors MAIN in src/components/Tour.astro, in order.
  steps: [
    { target: '.intro-tabs' },
    { target: '#main-tabs' },
    { target: '#wizard-steps' },
    { target: '#in-weight' },
    { target: '.res-table' },
    { target: '.res-controls' },
    { target: '.wizard-steps li[data-step="3"]' },
    { target: '.result-brainage' },
    { target: '#out-actions' },
    { target: '.map-section .map-controls', activePanel: '.tab-panel[data-panel="map"]' },
    { target: '.calc-provenance .dp-tabs', activePanel: '.tab-panel[data-panel="refs"]' },
    { target: '#tour-help' },
  ],

  // /cdn-cgi/trace is Cloudflare's edge geo endpoint — it exists in production but 404s on a
  // local static server. The app already treats a failure as "no geo hint" (.catch(() => null)).
  ignoreRequests: [/favicon/i, /cdn-cgi\/trace/],

  reducedMotion: true,

  // Core flows with the tour never opened — expect no console/network errors.
  regression: async (page) => {
    await page.click('.mt-btn[data-tab="map"]').catch(() => {});
    await page.waitForTimeout(400);
    await page.click('.mt-btn[data-tab="refs"]').catch(() => {});
    await page.waitForTimeout(300);
    await page.click('.mt-btn[data-tab="calc"]').catch(() => {});
    await page.click('.wizard-steps li[data-step="2"]').catch(() => {});
    await page.click('#res-add-last').catch(() => {});
    await page.click('.wizard-steps li[data-step="6"]').catch(() => {});
    await page.waitForTimeout(400);
    return true;
  },
};
