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

  /* --- offer the Spanish site, once, to Spanish-language browsers ---
     Never redirects: the reader stays where they landed unless they choose
     otherwise. Shown only on English pages, only when the browser asks for
     Spanish, and never again once dismissed or once a language is chosen. */
  var langLink = document.querySelector('.site-nav .lang-switch');
  var onSpanishPage = document.documentElement.lang === 'es';

  function remember(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* private mode */ }
  }
  function recall(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }

  if (langLink) {
    // choosing a language is a preference; it also settles the banner
    langLink.addEventListener('click', function () {
      remember('dks-lang', onSpanishPage ? 'en' : 'es');
    });
  }

  if (!onSpanishPage && langLink) {
    var wantsSpanish = (navigator.languages || [navigator.language || ''])
      .some(function (l) { return String(l).toLowerCase().indexOf('es') === 0; });
    var settled = recall('dks-lang') || recall('dks-lang-dismissed');
    if (wantsSpanish && !settled) {
      var bar = document.createElement('div');
      bar.className = 'lang-banner';
      bar.setAttribute('lang', 'es');
      bar.innerHTML = '<span>Este sitio también está disponible en español.</span>' +
        '<a href="' + langLink.getAttribute('href') + '">Ver en español</a>' +
        '<button class="close" type="button" aria-label="Cerrar">×</button>';
      var header = document.querySelector('.site-header');
      if (header && header.parentNode) {
        header.parentNode.insertBefore(bar, header.nextSibling);
        requestAnimationFrame(function () { bar.classList.add('show'); });
        bar.querySelector('a').addEventListener('click', function () {
          remember('dks-lang', 'es');
        });
        bar.querySelector('.close').addEventListener('click', function () {
          bar.remove();
          remember('dks-lang-dismissed', '1');
        });
      }
    }
  }
})();
