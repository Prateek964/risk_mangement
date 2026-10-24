/* Risk Hub carousel runtime. Builds one paused GSAP timeline per slide and exposes
 * deterministic seek hooks for export/QA. Text is never a tween target: a guard rejects
 * any target that is, contains, or sits inside text. */
(function () {
  'use strict';
  var DATA = window.__CAROUSEL__;
  var params = new URLSearchParams(location.search);
  var timelines = {};
  var guardErrors = [];
  var fitErrors = [];

  function slideEl(i) { return document.querySelector('.slide[data-index="' + i + '"]'); }

  // ---- Fit text before the first frame (final size is fixed before any animation) ----
  function fitHeadline(el) {
    var size = parseFloat(getComputedStyle(el).fontSize), min = 48;
    while (el.scrollWidth > el.clientWidth + 1 && size > min) { size -= 2; el.style.fontSize = size + 'px'; }
    if (el.scrollWidth > el.clientWidth + 1) fitErrors.push({ slide: +el.closest('.slide').dataset.index, el: 'headline', msg: 'headline does not fit on one line' });
  }
  function fitColumn(col) {
    var size = parseFloat(getComputedStyle(col).fontSize), min = 22;
    while (col.scrollHeight > col.clientHeight + 1 && size > min) { size -= 1; col.style.fontSize = size + 'px'; }
    if (col.scrollHeight > col.clientHeight + 1) fitErrors.push({ slide: +col.closest('.slide').dataset.index, el: 'column', msg: 'text column overflows its region at minimum size' });
  }

  // ---- Animation presets (non-text SVG only) ----
  var maskSeq = 0;
  function prepDraw(el) {
    var len = el.getTotalLength() + 1;
    if (!el.hasAttribute('stroke-dasharray')) { el.__drawTarget = el; el.__len = len; return el; }
    // Dashed strokes: draw a solid white copy inside a mask so the dash pattern is preserved.
    var svg = el.ownerSVGElement, ns = 'http://www.w3.org/2000/svg';
    var defs = svg.querySelector('defs') || svg.insertBefore(document.createElementNS(ns, 'defs'), svg.firstChild);
    var mask = document.createElementNS(ns, 'mask');
    var id = 'm' + (++maskSeq) + '-' + svg.closest('.slide').dataset.index;
    mask.setAttribute('id', id);
    mask.setAttribute('maskUnits', 'userSpaceOnUse');
    var vb = svg.viewBox.baseVal;
    mask.setAttribute('x', 0); mask.setAttribute('y', 0); mask.setAttribute('width', vb.width); mask.setAttribute('height', vb.height);
    var copy = el.cloneNode(false);
    copy.removeAttribute('class'); copy.removeAttribute('stroke-dasharray'); copy.removeAttribute('mask');
    copy.setAttribute('stroke', '#fff'); copy.setAttribute('fill', 'none');
    copy.setAttribute('stroke-width', (parseFloat(el.getAttribute('stroke-width')) || 2) + 4);
    mask.appendChild(copy); defs.appendChild(mask);
    el.setAttribute('mask', 'url(#' + id + ')');
    copy.__len = len;
    return copy;
  }

  var PRESETS = {
    draw: function (tl, els, s) {
      var targets = els.map(prepDraw);
      tl.fromTo(targets,
        { strokeDasharray: function (i, t) { return t.__len + ' ' + t.__len; }, strokeDashoffset: function (i, t) { return t.__len; } },
        { strokeDashoffset: 0, duration: s.dur, ease: s.ease || 'power2.inOut', stagger: s.stagger || 0 }, s.at);
    },
    fade: function (tl, els, s) {
      tl.fromTo(els, { opacity: 0 }, { opacity: 1, duration: s.dur, ease: s.ease || 'power1.out', stagger: s.stagger || 0 }, s.at);
    },
    scale: function (tl, els, s) {
      tl.fromTo(els,
        { scale: 0, transformOrigin: function (i, el) { return el.getAttribute('data-origin') || '50% 50%'; } },
        { scale: 1, duration: s.dur, ease: s.ease || 'power2.out', stagger: s.stagger || 0 }, s.at);
    },
    rotate: function (tl, els, s) {
      tl.fromTo(els, { rotation: s.from || 0, transformOrigin: '50% 50%' }, { rotation: s.to || 360, duration: s.dur, ease: s.ease || 'none' }, s.at);
    },
  };

  function guard(el, slideIdx) {
    var problem = null;
    if (el.closest('.text-layer')) problem = 'target is inside the text layer';
    else if (!el.closest('.art-layer')) problem = 'target is outside the art layer';
    else if (/^(text|tspan|textPath|foreignObject)$/i.test(el.tagName)) problem = 'target is a text element';
    else if (el.querySelector && el.querySelector('text,tspan,foreignObject')) problem = 'target contains text';
    else if ((el.textContent || '').trim()) problem = 'target has text content';
    if (problem) guardErrors.push({ slide: slideIdx, target: el.getAttribute('class') || el.tagName, problem: problem });
    return !problem;
  }

  function build(slide) {
    var tl = gsap.timeline({ paused: true });
    var root = slideEl(slide.index);
    var illus = root.querySelector('.illus');
    if (illus) {
      if (illus.querySelector('text,tspan,foreignObject') || illus.textContent.trim()) guardErrors.push({ slide: slide.index, problem: 'art layer contains text' });
      (slide.timeline || []).forEach(function (step) {
        var els = Array.prototype.slice.call(illus.querySelectorAll(step.sel)).filter(function (el) { return guard(el, slide.index); });
        if (!els.length) { guardErrors.push({ slide: slide.index, target: step.sel, problem: 'selector matched nothing' }); return; }
        var preset = PRESETS[step.preset];
        if (!preset) { guardErrors.push({ slide: slide.index, target: step.sel, problem: 'unknown preset ' + step.preset }); return; }
        preset(tl, els, step);
      });
    }
    // Hold the final frame so the slide's timeline length equals its configured on-screen time.
    var hold = Math.max(slide.seconds - tl.duration(), 0);
    if (hold > 0) tl.to({}, { duration: hold });
    timelines[slide.index] = tl;
  }

  function show(which) {
    document.querySelectorAll('.slide').forEach(function (s) { s.style.display = which === 'all' || +s.dataset.index === which ? '' : 'none'; });
  }

  // ---- QA hooks ----
  function effectiveOpacity(el) {
    var o = 1;
    for (var n = el; n && n.nodeType === 1; n = n.parentElement) o *= parseFloat(getComputedStyle(n).opacity);
    return Math.round(o * 1000) / 1000;
  }
  function textSnapshot(i) {
    var out = [];
    var walker = document.createTreeWalker(slideEl(i), NodeFilter.SHOW_TEXT, null);
    var seen = new Set();
    for (var node = walker.nextNode(); node; node = walker.nextNode()) {
      if (!node.nodeValue.trim()) continue;
      var el = node.parentElement;
      if (seen.has(el)) continue;
      seen.add(el);
      var cs = getComputedStyle(el), r = el.getBoundingClientRect();
      out.push({
        text: el.textContent.trim().slice(0, 80),
        rect: [r.x, r.y, r.width, r.height].map(function (v) { return Math.round(v * 100) / 100; }).join(','),
        style: [cs.color, effectiveOpacity(el), cs.visibility, cs.fontSize, cs.fontWeight, cs.fontFamily, cs.letterSpacing, cs.lineHeight, cs.transform, cs.filter].join('|'),
      });
    }
    return out;
  }
  function layoutReport(i) {
    var root = slideEl(i), base = root.getBoundingClientRect();
    var rect = function (el) { var r = el.getBoundingClientRect(); return { x: r.x - base.x, y: r.y - base.y, w: r.width, h: r.height }; };
    var blocks = Array.prototype.slice.call(root.querySelectorAll('.tb')).filter(function (el) { return el.textContent.trim(); }).map(function (el) {
      return { kind: el.dataset.kind, text: el.textContent.trim().slice(0, 60), rect: rect(el) };
    });
    var illus = root.querySelector('.illus');
    return {
      blocks: blocks,
      illustration: illus ? rect(illus) : null,
      fullBleed: illus ? illus.dataset.fullBleed === '1' : false,
      katexErrors: root.querySelectorAll('.katex-error').length,
      katexCount: root.querySelectorAll('.katex').length,
      innerText: root.querySelector('.text-layer').innerText,
    };
  }

  window.__seek = function (i, t) {
    var tl = timelines[i];
    if (!tl) return 0;
    tl.seek(t === 'end' ? tl.duration() : Math.min(t, tl.duration()), false);
    return tl.time();
  };
  window.__duration = function (i) { return timelines[i] ? timelines[i].duration() : 0; };
  window.__textSnapshot = textSnapshot;
  window.__layoutReport = layoutReport;

  function init() {
    var loads = (DATA.fonts || []).map(function (f) { return document.fonts.load(f); });
    Promise.all(loads).then(function () { return document.fonts.ready; }).then(function () {
      document.querySelectorAll('.fit-line').forEach(fitHeadline);
      document.querySelectorAll('.fit-col').forEach(fitColumn);
      gsap.config({ force3D: false });
      gsap.ticker.sleep(); // never advance on wall-clock time: frames come only from __seek
      DATA.slides.forEach(build);
      var slideParam = params.get('slide');
      show(params.get('all') ? 'all' : slideParam ? +slideParam : 'all');
      var state = params.get('state') || 'final';
      DATA.slides.forEach(function (s) { window.__seek(s.index, state === 'start' ? 0 : 'end'); });
      window.__fonts = Array.prototype.slice.call(document.fonts).filter(function (f) { return f.status === 'loaded'; }).map(function (f) { return f.family.replace(/"/g, '') + ':' + f.weight; });
      window.__guardErrors = guardErrors;
      window.__fitErrors = fitErrors;
      window.__ready = true;
    }).catch(function (e) { window.__initError = String(e); window.__ready = true; });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
