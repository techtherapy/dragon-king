/* Dragon King Sutra — shared behaviour */
(function () {
  document.documentElement.classList.remove('no-js');

  var header = document.querySelector('.site-header');
  var navToggle = document.querySelector('.nav-toggle');
  var nav = document.querySelector('.site-nav');

  if (navToggle && nav) {
    /* body.nav-open lets the page stop painting whatever sits behind the
       panel — on the home page that is five animated SVGs behind a blurred
       header, which is what made the menu stutter on older phones. */
    var setNav = function (open) {
      nav.classList.toggle('open', open);
      document.body.classList.toggle('nav-open', open);
      navToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      navToggle.textContent = open ? '✕' : '☰';
    };
    navToggle.addEventListener('click', function () {
      setNav(!nav.classList.contains('open'));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') setNav(false);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) setNav(false);
    });
  }

  var onScroll = function () {
    if (header) header.classList.toggle('scrolled', window.scrollY > 30);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* reveal on scroll */
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduced) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('visible'); });
  }

  /* hero parallax layers: [data-parallax="rate"] */
  /* Scroll parallax writes a transform to five layers every frame. That is
     cheap on a desktop GPU and expensive on an old mobile one, for an effect
     barely visible on a small screen — so it is desktop-only. */
  var layers = document.querySelectorAll('[data-parallax]');
  var bigScreen = window.matchMedia('(min-width: 1081px)').matches &&
                  window.matchMedia('(hover: hover)').matches;
  if (layers.length && !reduced && bigScreen) {
    var ticking = false;
    var update = function () {
      var y = window.scrollY;
      layers.forEach(function (el) {
        var rate = parseFloat(el.getAttribute('data-parallax')) || 0;
        el.style.transform = 'translate3d(0,' + (y * rate).toFixed(1) + 'px,0)';
      });
      ticking = false;
    };
    window.addEventListener('scroll', function () {
      if (!ticking) { requestAnimationFrame(update); ticking = true; }
    }, { passive: true });
  }

  /* --- offer another language, once, to a browser that asks for one ---
     Never redirects: the reader stays where they landed unless they choose
     otherwise. The switcher in the header carries a link to each of the other
     two languages; if the browser's preferred language is one of them, that
     one is offered in its own words, and never again once dismissed or once a
     language has been chosen. */
  var OFFERS = {
    en: { text: 'This site is also available in English.', cta: 'View in English', close: 'Close' },
    es: { text: 'Este sitio también está disponible en español.', cta: 'Ver en español', close: 'Cerrar' },
    fr: { text: 'Ce site est également disponible en français.', cta: 'Voir en français', close: 'Fermer' }
  };
  var switcher = document.querySelector('.site-nav .lang-switch');
  var altLinks = switcher ? switcher.querySelectorAll('a[hreflang]') : [];

  function remember(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* private mode */ }
  }
  function recall(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  /* choosing a language is a preference; it also settles the banner */
  Array.prototype.forEach.call(altLinks, function (a) {
    a.addEventListener('click', function () {
      remember('dks-lang', a.getAttribute('hreflang'));
    });
  });

  var settled = recall('dks-lang') || recall('dks-lang-dismissed');
  if (altLinks.length && !settled) {
    /* the browser's languages in order of preference, most wanted first */
    var wanted = (navigator.languages || [navigator.language || ''])
      .map(function (l) { return String(l).toLowerCase().slice(0, 2); });
    var offer = null;
    for (var i = 0; i < wanted.length && !offer; i++) {
      for (var j = 0; j < altLinks.length && !offer; j++) {
        if (altLinks[j].getAttribute('hreflang') === wanted[i]) offer = altLinks[j];
      }
    }
    var words = offer && OFFERS[offer.getAttribute('hreflang')];
    if (words) {
      var lang = offer.getAttribute('hreflang');
      var bar = document.createElement('div');
      bar.className = 'lang-banner';
      bar.setAttribute('lang', lang);
      bar.innerHTML = '<span></span><a></a><button class="close" type="button"></button>';
      bar.querySelector('span').textContent = words.text;
      var cta = bar.querySelector('a');
      cta.textContent = words.cta;
      cta.setAttribute('href', offer.getAttribute('href'));
      var closer = bar.querySelector('.close');
      closer.textContent = '\u00d7';
      closer.setAttribute('aria-label', words.close);
      var hdr = document.querySelector('.site-header');
      if (hdr && hdr.parentNode) {
        hdr.parentNode.insertBefore(bar, hdr.nextSibling);
        requestAnimationFrame(function () { bar.classList.add('show'); });
        cta.addEventListener('click', function () { remember('dks-lang', lang); });
        closer.addEventListener('click', function () {
          bar.remove();
          remember('dks-lang-dismissed', '1');
        });
      }
    }
  }
})();
