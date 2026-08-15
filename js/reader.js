/* Dragon King Sutra — reader behaviour */
(function () {
  /* --- language layer toggles (persisted) --- */
  var LAYERS = ['zh', 'py', 'en', 'es'];
  /* The two readers are separate pages with opposite defaults, so they keep
     separate preferences — otherwise turning Spanish off on /es/read would
     silently turn it off on /read too, and vice versa. */
  var PAGE_LANG = document.documentElement.lang === 'es' ? 'es' : 'en';
  var DEFAULT_ON = PAGE_LANG === 'es'
    ? { zh: true, py: true, en: false, es: true }
    : { zh: true, py: true, en: true, es: false };
  var STORE = 'dks-' + PAGE_LANG + '-show-';
  var chips = document.querySelectorAll('.chip[data-layer]');

  function applyLayer(layer, on) {
    document.body.classList.toggle('hide-' + layer, !on);
    chips.forEach(function (c) {
      if (c.getAttribute('data-layer') === layer) c.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  LAYERS.forEach(function (layer) {
    var stored = null;
    try { stored = localStorage.getItem(STORE + layer); } catch (e) { /* private mode */ }
    applyLayer(layer, stored === null ? DEFAULT_ON[layer] : stored === '1');
  });

  chips.forEach(function (chip) {
    chip.addEventListener('click', function () {
      var layer = chip.getAttribute('data-layer');
      var on = chip.getAttribute('aria-pressed') !== 'true';
      var visible = LAYERS.filter(function (l) {
        return l === layer ? on : document.body.classList.contains('hide-' + l) === false;
      });
      if (!visible.length) return; // never hide every layer
      applyLayer(layer, on);
      try { localStorage.setItem(STORE + layer, on ? '1' : '0'); } catch (e) { /* ignore */ }
    });
  });

  /* --- chapter drawer (mobile) --- */
  var toc = document.getElementById('readerToc');
  var tocBtn = document.getElementById('tocBtn');
  var scrim = document.getElementById('tocScrim');
  function closeToc() {
    toc.classList.remove('open');
    scrim.classList.remove('show');
    tocBtn.setAttribute('aria-expanded', 'false');
  }
  if (tocBtn) {
    tocBtn.addEventListener('click', function () {
      var open = toc.classList.toggle('open');
      scrim.classList.toggle('show', open);
      tocBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    scrim.addEventListener('click', closeToc);
    toc.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeToc();
    });
  }

  /* --- reading progress + back-to-top --- */
  var fill = document.getElementById('progressFill');
  var toTop = document.getElementById('toTop');
  function onScroll() {
    var doc = document.documentElement;
    var max = doc.scrollHeight - window.innerHeight;
    if (fill && max > 0) fill.style.width = (window.scrollY / max * 100).toFixed(2) + '%';
    if (toTop) toTop.classList.toggle('show', window.scrollY > 900);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  if (toTop) toTop.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  /* --- scrollspy: highlight current chapter --- */
  var links = Array.prototype.slice.call(document.querySelectorAll('.reader-toc nav a[href^="#"]'));
  var chapters = links.map(function (a) { return document.getElementById(a.getAttribute('href').slice(1)); }).filter(Boolean);
  if ('IntersectionObserver' in window && chapters.length) {
    var current = null;
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) current = entry.target.id;
      });
      if (current) {
        links.forEach(function (a) {
          a.classList.toggle('current', a.getAttribute('href') === '#' + current);
        });
      }
    }, { rootMargin: '-15% 0px -75% 0px' });
    chapters.forEach(function (c) { spy.observe(c); });
  }

  /* --- print --- */
  var printBtn = document.getElementById('printBtn');
  if (printBtn) printBtn.addEventListener('click', function () { window.print(); });
  if (window.location.search.indexOf('print') !== -1) {
    window.addEventListener('load', function () { setTimeout(function () { window.print(); }, 600); });
  }
})();
