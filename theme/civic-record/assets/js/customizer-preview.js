/**
 * Civic Record — customizer-preview.js
 * Live preview bindings for postMessage transport settings.
 */

(function ($) {
  'use strict';

  // Accent color → CSS custom property
  wp.customize('civic_accent_color', function (value) {
    value.bind(function (newVal) {
      document.documentElement.style.setProperty('--accent-color', newVal);
    });
  });

  // City name → hero section header
  wp.customize('civic_city_name', function (value) {
    value.bind(function (newVal) {
      document.querySelectorAll('.js-city-name').forEach(function (el) {
        el.textContent = newVal;
      });
    });
  });

  // Publication name → site name elements
  wp.customize('civic_publication_name', function (value) {
    value.bind(function (newVal) {
      document.querySelectorAll('.site-name, .footer-name, .about-widget__name').forEach(function (el) {
        el.textContent = newVal;
      });
    });
  });

})(jQuery);
