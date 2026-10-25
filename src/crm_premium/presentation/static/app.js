/* Utilidades comunes: menú móvil, token CSRF y fetch JSON. */
(function () {
  'use strict';

  var toggle = document.getElementById('menuToggle');
  var sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) {
    toggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
    });
    document.addEventListener('click', function (event) {
      if (sidebar.classList.contains('open') &&
          !sidebar.contains(event.target) && event.target !== toggle) {
        sidebar.classList.remove('open');
      }
    });
  }

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
  }

  window.crmApi = function (url, options) {
    options = options || {};
    options.headers = Object.assign({
      'Content-Type': 'application/json',
      'X-CSRF-Token': csrfToken()
    }, options.headers || {});
    options.credentials = 'same-origin';
    return fetch(url, options).then(function (response) {
      return response.json().then(function (data) {
        return {ok: response.ok, status: response.status, data: data};
      });
    });
  };

  // E01-R/A4: gráficos de barras vía data-* + CSSOM tipado. El atributo
  // style="height/width:...%" renderizado por la plantilla viola
  // style-src 'self' y dejaba las barras a altura cero.
  function applyBars() {
    document.querySelectorAll('[data-bar-h]').forEach(function (el) {
      el.style.height = el.getAttribute('data-bar-h') + '%';
    });
    document.querySelectorAll('[data-bar-w]').forEach(function (el) {
      el.style.width = el.getAttribute('data-bar-w') + '%';
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyBars);
  } else {
    applyBars();
  }

  window.crmFormat = {
    localInput: function (isoDate, time) {
      return isoDate + 'T' + time;
    },
    parseLocalInput: function (value) {
      return value; // datetime-local ⇒ AAAA-MM-DDTHH:MM (zona del negocio)
    }
  };
})();
