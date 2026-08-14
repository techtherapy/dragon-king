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
})();
