/* Dragon King Sutra — reader behaviour */
(function () {
  /* --- language layer toggles (persisted) --- */
  var LAYERS = ['zh', 'py', 'en', 'es', 'fr'];
  /* The three readers are separate pages with different defaults, so they keep
     separate preferences — otherwise turning Spanish off on /es/read would
     silently turn it off on /read too. Each page opens with 漢字, pinyin and
     its own language showing; the other two are a click away. */
  var PAGE_LANG = { es: 'es', fr: 'fr' }[document.documentElement.lang] || 'en';
  var DEFAULTS = {
    en: { zh: true, py: true, en: true,  es: false, fr: false },
    es: { zh: true, py: true, en: false, es: true,  fr: false },
    fr: { zh: true, py: true, en: false, es: false, fr: true }
  };
  var DEFAULT_ON = DEFAULTS[PAGE_LANG];
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

  /* --- the ribbon: keep a returning reader's place ---
     The verse at the top of the screen is remembered as the reader moves
     through the text — one key for all three readers, since their verses are
     the same. Opening the reader again without a chapter link hangs a ribbon
     at the head of the text that leads back to that verse. The opening lines
     are not worth a ribbon, so scrolling back to the title never moves it;
     reaching the end of the sutra takes it out. */
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var PLACE = 'dks-place';
  var MIN_VERSE = 6;
  var verses = document.querySelectorAll('.sutra .prow');
  var tools = document.querySelector('.reader-tools');
  var finished = false;

  /* the first verse that begins below the toolbar (verses run in order down
     the page, so a binary search reads a dozen of them, not 3,000). A verse
     only peeking out from under the toolbar does not count — otherwise
     following the ribbon, which leaves a little of the verse before in view,
     would keep it one verse earlier on every visit. */
  function topVerse() {
    var edge = (tools ? tools.getBoundingClientRect().bottom : 0) - 1;
    var lo = 0, hi = verses.length - 1;
    while (lo < hi) {
      var mid = (lo + hi) >> 1;
      if (verses[mid].getBoundingClientRect().top >= edge) hi = mid; else lo = mid + 1;
    }
    return lo;
  }
  function keepPlace() {
    if (finished || !verses.length) return;
    var v = topVerse();
    if (v >= MIN_VERSE) {
      try { localStorage.setItem(PLACE, String(v)); } catch (e) { /* private mode */ }
    }
  }
  var keepTimer = null;
  window.addEventListener('scroll', function () {
    clearTimeout(keepTimer);
    keepTimer = setTimeout(keepPlace, 500);
  }, { passive: true });

  var ribbon = document.getElementById('ribbon');
  var kept = NaN;
  try { kept = parseInt(localStorage.getItem(PLACE), 10); } catch (e) { /* private mode */ }
  var arrivedSomewhere = window.location.hash || window.location.search.indexOf('print') !== -1;
  if (ribbon && !arrivedSomewhere && kept >= MIN_VERSE && kept < verses.length) {
    var verse = verses[kept];
    var chapter = verse.closest('.chapter');
    var entry = chapter && document.querySelector('.reader-toc a[href="#' + chapter.id + '"]');
    if (entry) {
      /* the chapter's name as the contents gives it, in this reader's language */
      var own = { es: '.t-en.espanol', fr: '.t-en.francais' }[PAGE_LANG] ||
                '.t-en:not(.espanol):not(.francais)';
      ribbon.querySelector('.ribbon-zh').textContent = entry.querySelector('.t-zh').textContent;
      ribbon.querySelector('.ribbon-name').textContent = entry.querySelector(own).textContent;
      ribbon.setAttribute('href', '#' + chapter.id);
      ribbon.hidden = false;
      ribbon.addEventListener('click', function (e) {
        e.preventDefault();
        /* the ribbon comes out as the book falls open at it */
        ribbon.hidden = true;
        verse.classList.add('ribbon-here');
        verse.setAttribute('tabindex', '-1');
        verse.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' });
        verse.focus({ preventScroll: true });
        var found = function () {
          window.removeEventListener('scrollend', found);
          verse.classList.add('is-found');
        };
        if (reduced) { found(); return; }
        window.addEventListener('scrollend', found);
        setTimeout(found, 1400); // browsers without scrollend
      });
    }
  }

  /* --- the close: the Dragon King's garland ---
     The sutra ends as the Sea Dragon King rains pearl garlands in offering.
     When the garland beneath that line comes into view, its pearls fall onto
     the thread — once. Where motion is reduced it is simply there. */
  var end = document.getElementById('sutraEnd');
  if (end && 'IntersectionObserver' in window) {
    if (!reduced) end.classList.add('is-waiting');
    var offering = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return;
      offering.disconnect();
      finished = true;
      try { localStorage.removeItem(PLACE); } catch (e) { /* private mode */ }
      if (end.classList.contains('is-waiting')) {
        end.classList.remove('is-waiting');
        end.classList.add('is-offered');
      }
    }, { threshold: 0.6 });
    offering.observe(end.querySelector('.garland') || end);
  }

  /* --- print --- */
  var printBtn = document.getElementById('printBtn');
  if (printBtn) printBtn.addEventListener('click', function () { window.print(); });
  if (window.location.search.indexOf('print') !== -1) {
    window.addEventListener('load', function () { setTimeout(function () { window.print(); }, 600); });
  }
})();
