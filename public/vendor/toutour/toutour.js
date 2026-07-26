/*!
 * Toutour v0.2 — zero-dependency spotlight onboarding tour engine (MIT)
 * https://github.com/a0972210123/Toutour
 *
 * Usage:
 *   Toutour.start(steps, opts)
 *   step: {
 *     target: '#sel' | () => Element,   // required
 *     text:   'string' | {en, zh, ...}, // per-locale copy (plain text or HTML via opts.allowHTML)
 *     icon:   '🌀',                     // shown on the card, outside the spotlight
 *     place:  'right'|'left'|'top'|'bottom',  // placement hint (auto-flips if it doesn't fit)
 *     when:   () => boolean,            // filtered out at start when falsy
 *     before: () => void,               // reveal the target first (switch tab, open drawer…)
 *     widen:  true,                     // default true: bare inputs widen to closest label/wrapper
 *     timeout: 4000,                    // ms to wait for the target to mount (SPA lazy content);
 *                                       //   if it never appears the step is skipped at runtime
 *   }
 *   opts: {
 *     lang: 'en' | () => 'en',          // key into step.text objects
 *     mask: true, ring: true,           // dark overlay / accent spotlight ring
 *     block: true,                      // block page interaction during the tour
 *     storageKey: 'toutour_seen',       // set on end; Toutour.seen(opts) reads it
 *     zIndex: 9000,                     // base layer; audit your site's max z-index first
 *     labels: { next:'Next', prev:'Back', done:'Done', skip:'Skip tour' },  // or per-locale objects
 *     allowHTML: false,                 // treat step.text as HTML (only with trusted copy)
 *     onEvent: (name, data) => {},      // tour_start | tour_step | tour_done | tour_skip
 *                                       //   tour_step fires per step — use it for funnel analysis
 *   }
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.Toutour = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
  const S = { steps: [], i: 0, active: false, raf: 0, lastRect: null, fresh: false, waitUntil: 0, opts: {} };
  let els = null;

  function ensureEls() {
    if (els) return els;
    const mk = (tag, id, parent) => { const e = document.createElement(tag); e.id = id; (parent || document.body).appendChild(e); return e; };
    const block = mk('div', 'ttBlock');
    const spot  = mk('div', 'ttSpot');
    const tip   = mk('div', 'ttTip');
    tip.setAttribute('role', 'dialog');
    tip.setAttribute('aria-label', 'Tour step');
    tip.setAttribute('aria-live', 'polite');
    tip.innerHTML =
      '<div class="tt-head"><span class="tt-ico" id="ttIco"></span><span class="tt-count" id="ttCount"></span></div>' +
      '<div class="tt-body" id="ttBody"></div>' +
      '<div class="tt-foot"><button type="button" class="tt-btn" id="ttPrev"></button>' +
      '<button type="button" class="tt-btn tt-btn-primary" id="ttNext"></button></div>' +
      '<button type="button" class="tt-skip" id="ttSkip"></button>';
    els = { block, spot, tip,
      ico: tip.querySelector('#ttIco'), count: tip.querySelector('#ttCount'),
      body: tip.querySelector('#ttBody'), prev: tip.querySelector('#ttPrev'),
      next: tip.querySelector('#ttNext'), skip: tip.querySelector('#ttSkip') };
    els.prev.addEventListener('click', prev);
    els.next.addEventListener('click', next);
    els.skip.addEventListener('click', () => end(false));
    return els;
  }

  const lang = () => {
    const l = S.opts.lang;
    return typeof l === 'function' ? l() : (l || 'en');
  };
  const copy = v => (v && typeof v === 'object') ? (v[lang()] ?? Object.values(v)[0] ?? '') : (v ?? '');
  const label = k => {
    const defaults = { next: 'Next', prev: 'Back', done: 'Done', skip: 'Skip tour' };
    return copy((S.opts.labels || {})[k]) || defaults[k];
  };
  const emit = (name, data) => { try { (S.opts.onEvent || function(){})(name, data || {}); } catch (e) {} };

  function resolveTarget(st) {
    const sel = typeof st.target === 'function' ? st.target() : st.target;
    let el = typeof sel === 'string' ? document.querySelector(sel) : sel;
    if (!el) return null;
    // A bare input is too small a spotlight — widen to the wrapper carrying its label.
    if (st.widen !== false && el.tagName === 'INPUT') {
      el = el.closest('label') || el.closest('[class*="field"],[class*="row"],[class*="block"]') || el;
    }
    return el;
  }

  function start(steps, opts) {
    if (S.active) end(false);
    S.opts = opts || {};
    ensureEls();
    S.steps = (steps || []).filter(st => (!st.when || st.when()) && !!resolveTarget(st));
    if (!S.steps.length) return false;
    S.active = true;
    S.fresh = true;
    const z = S.opts.zIndex || 9000;
    els.block.style.zIndex = z - 1; els.spot.style.zIndex = z; els.tip.style.zIndex = z + 10;
    els.block.classList.toggle('show', S.opts.block !== false);
    els.spot.classList.add('show');
    els.spot.classList.toggle('tt-mask-off', S.opts.mask === false);
    els.spot.classList.toggle('tt-ring-off', S.opts.ring === false);
    els.tip.classList.add('show');
    document.addEventListener('keydown', onKey, true);
    emit('tour_start', { steps: S.steps.length });
    show(0);
    return true;
  }

  function show(i) {
    S.i = i;
    S.lastRect = null;
    const st = S.steps[i];
    // SPA budget: before() may trigger async mounting — tick() waits this long
    // for the target to appear before skipping the step at runtime.
    S.waitUntil = performance.now() + (st.timeout || 4000);
    try { if (st.before) st.before(); } catch (e) {}
    render(st, i);
    emit('tour_step', { step: i + 1, total: S.steps.length });
    setTimeout(() => {
      const el = resolveTarget(st);
      if (el && S.active) { try { el.scrollIntoView({ block: 'center', behavior: 'auto' }); } catch (e) {} }
    }, 60);
    if (!S.raf) tick();
  }

  function render(st, i) {
    els.ico.textContent = st.icon || '💡';
    els.count.textContent = (i + 1) + '/' + S.steps.length;
    if (S.opts.allowHTML) els.body.innerHTML = copy(st.text);
    else els.body.textContent = copy(st.text);
    els.prev.style.visibility = i === 0 ? 'hidden' : 'visible';
    els.prev.textContent = '‹ ' + label('prev');
    els.next.textContent = (i === S.steps.length - 1) ? label('done') + ' ✓' : label('next') + ' ›';
    els.skip.textContent = label('skip');
    try { els.next.focus({ preventScroll: true }); } catch (e) {}
  }

  // rAF loop: follows the target through scroll, resize, drawer animations and
  // i18n reflow with one mechanism. Updates only on >0.5px movement.
  function tick() {
    if (!S.active) { S.raf = 0; return; }
    S.raf = requestAnimationFrame(tick);
    const el = resolveTarget(S.steps[S.i]);
    const r = el && el.getBoundingClientRect();
    if (!el || (!r.width && !r.height)) {
      if (performance.now() > S.waitUntil) {   // target never mounted — don't point at nothing
        S.i < S.steps.length - 1 ? show(S.i + 1) : end(true);
      }
      return;
    }
    const pad = 6;
    const rect = { top: r.top - pad, left: r.left - pad, w: r.width + pad * 2, h: r.height + pad * 2 };
    const p = S.lastRect;
    if (p && Math.abs(p.top - rect.top) < .5 && Math.abs(p.left - rect.left) < .5 &&
        Math.abs(p.w - rect.w) < .5 && Math.abs(p.h - rect.h) < .5) return;
    S.lastRect = rect;
    positionSpot(el, rect);
    placeTip(rect, S.steps[S.i]);
  }

  function positionSpot(el, rect) {
    const s = els.spot.style;
    if (S.fresh) els.spot.classList.add('no-anim');      // no fly-in on first placement
    s.top = rect.top + 'px'; s.left = rect.left + 'px';
    s.width = rect.w + 'px'; s.height = rect.h + 'px';
    let br = '';
    try { br = getComputedStyle(el).borderRadius; } catch (e) {}
    s.borderRadius = (br && br !== '0px') ? br : '10px';
    if (S.fresh) { S.fresh = false; requestAnimationFrame(() => els.spot.classList.remove('no-anim')); }
  }

  // Card never overlaps the spotlight, so the icon + counter are guaranteed to
  // sit outside the lit area. Arrow aims at the target center.
  function placeTip(rect, st) {
    const tip = els.tip, vw = innerWidth, vh = innerHeight, gap = 14, m = 8;
    const tw = tip.offsetWidth, th = tip.offsetHeight;
    const spaces = {
      right:  vw - (rect.left + rect.w) - gap - m,
      left:   rect.left - gap - m,
      bottom: vh - (rect.top + rect.h) - gap - m,
      top:    rect.top - gap - m,
    };
    const mobile = vw <= 768;
    let order = mobile ? ['bottom', 'top', 'right', 'left'] : ['right', 'left', 'bottom', 'top'];
    if (st.place) order = [st.place].concat(order.filter(s => s !== st.place));
    let side = null;
    for (const s of order) {
      if (spaces[s] >= ((s === 'left' || s === 'right') ? tw : th)) { side = s; break; }
    }
    tip.classList.remove('tip-left', 'tip-right', 'tip-top', 'tip-bottom');
    let x, y;
    if (!side) {  // target dominates the screen — pin to the freer edge, no arrow
      x = clamp((vw - tw) / 2, m, Math.max(m, vw - tw - m));
      y = (rect.top + rect.h / 2 > vh / 2) ? m : vh - th - m;
      tip.style.left = x + 'px'; tip.style.top = y + 'px';
      return;
    }
    const cx = rect.left + rect.w / 2, cy = rect.top + rect.h / 2;
    if (side === 'right')  { x = rect.left + rect.w + gap; y = clamp(cy - th / 2, m, vh - th - m); }
    if (side === 'left')   { x = rect.left - gap - tw;     y = clamp(cy - th / 2, m, vh - th - m); }
    if (side === 'bottom') { y = rect.top + rect.h + gap;  x = clamp(cx - tw / 2, m, vw - tw - m); }
    if (side === 'top')    { y = rect.top - gap - th;      x = clamp(cx - tw / 2, m, vw - tw - m); }
    tip.classList.add('tip-' + side);
    const off = (side === 'left' || side === 'right')
      ? clamp(cy - y - 6, 14, th - 26) : clamp(cx - x - 6, 14, tw - 26);
    tip.style.setProperty('--tt-arrow-off', off + 'px');
    tip.style.left = x + 'px'; tip.style.top = y + 'px';
  }

  function next() { S.i < S.steps.length - 1 ? show(S.i + 1) : end(true); }
  function prev() { if (S.i > 0) show(S.i - 1); }

  function end(done) {
    if (!S.active) return;
    S.active = false;
    cancelAnimationFrame(S.raf); S.raf = 0; S.lastRect = null;
    els.block.classList.remove('show');
    els.spot.classList.remove('show');
    els.tip.classList.remove('show');
    document.removeEventListener('keydown', onKey, true);
    markSeen(S.opts);
    emit(done ? 'tour_done' : 'tour_skip', { step: S.i + 1, total: S.steps.length });
  }

  function onKey(e) {
    if (!S.active) return;
    if (e.key === 'Escape') { e.preventDefault(); end(false); }
    else if (e.key === 'ArrowRight' || e.key === 'Enter') { e.preventDefault(); next(); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); prev(); }
  }

  function key(opts) { return (opts && opts.storageKey) || 'toutour_seen'; }
  function seen(opts) { try { return !!localStorage.getItem(key(opts)); } catch (e) { return false; } }
  function markSeen(opts) { try { localStorage.setItem(key(opts), '1'); } catch (e) {} }

  return { start, end: () => end(false), seen, markSeen, get active() { return S.active; } };
}));
