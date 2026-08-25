/*!
 * Rockers 502 MG Guatemala — interacción del sitio
 * Sin dependencias. El sitio funciona completo si este archivo no carga.
 */
(function () {
  'use strict';

  document.documentElement.classList.remove('no-js');

  /* --- Menú móvil --------------------------------------------------------- */
  var burger = document.querySelector('[data-burger]');
  var menu = document.querySelector('[data-menu]');

  if (burger && menu) {
    burger.addEventListener('click', function () {
      var open = menu.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    menu.addEventListener('click', function (e) {
      if (e.target.tagName === 'A') {
        menu.classList.remove('is-open');
        burger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* --- Sombra de la barra al hacer scroll --------------------------------- */
  var header = document.querySelector('[data-header]');
  if (header) {
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 20);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  var hasIO = 'IntersectionObserver' in window;

  /* --- Aparición de secciones --------------------------------------------- */
  var revealables = document.querySelectorAll('.rv');
  if (hasIO) {
    var revealObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -12% 0px', threshold: 0.08 });

    Array.prototype.forEach.call(revealables, function (el, i) {
      el.style.transitionDelay = (i % 6) * 60 + 'ms';
      revealObserver.observe(el);
    });
  } else {
    Array.prototype.forEach.call(revealables, function (el) {
      el.classList.add('is-in');
    });
  }

  /* --- Sección activa en la navegación ------------------------------------ */
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('[data-menu] a'));
  if (hasIO && navLinks.length) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        navLinks.forEach(function (a) {
          a.classList.toggle('is-active', a.getAttribute('href') === '#' + entry.target.id);
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });

    navLinks.forEach(function (a) {
      var id = a.getAttribute('href');
      if (id && id.charAt(0) === '#') {
        var section = document.querySelector(id);
        if (section) spy.observe(section);
      }
    });
  }

  /* --- Carrusel ----------------------------------------------------------- */
  var track = document.querySelector('[data-carousel-track]');
  if (track) {
    var slides = Array.prototype.slice.call(track.children);
    var dots = document.querySelector('[data-carousel-dots]');
    var prev = document.querySelector('[data-carousel-prev]');
    var next = document.querySelector('[data-carousel-next]');
    var current = 0;

    var goTo = function (i) {
      var slide = slides[Math.max(0, Math.min(slides.length - 1, i))];
      track.scrollTo({
        left: slide.offsetLeft - (track.clientWidth - slide.clientWidth) / 2,
        behavior: 'smooth'
      });
    };

    var sync = function (i) {
      current = i;
      if (dots) {
        Array.prototype.forEach.call(dots.children, function (dot, k) {
          dot.setAttribute('aria-current', k === i ? 'true' : 'false');
        });
      }
      if (prev) prev.disabled = i === 0;
      if (next) next.disabled = i === slides.length - 1;
    };

    if (dots) {
      slides.forEach(function (slide, i) {
        var dot = document.createElement('button');
        dot.type = 'button';
        dot.setAttribute('role', 'tab');
        dot.setAttribute('aria-label', 'Foto ' + (i + 1) + ' de ' + slides.length);
        dot.addEventListener('click', function () { goTo(i); });
        dots.appendChild(dot);
      });
    }

    if (prev) prev.addEventListener('click', function () { goTo(current - 1); });
    if (next) next.addEventListener('click', function () { goTo(current + 1); });

    track.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowRight') { e.preventDefault(); goTo(current + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); goTo(current - 1); }
    });

    if (hasIO) {
      var slideObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) sync(slides.indexOf(entry.target));
        });
      }, { root: track, threshold: 0.6 });
      slides.forEach(function (slide) { slideObserver.observe(slide); });
    }

    sync(0);
  }

  /* --- Año del pie de página ---------------------------------------------- */
  var year = document.querySelector('[data-year]');
  if (year) year.textContent = new Date().getFullYear();
})();
