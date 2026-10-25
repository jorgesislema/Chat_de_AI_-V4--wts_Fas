/* Inventario: cambio de precio y ajuste de stock con motivo auditado. */
(function () {
  'use strict';
  var priceDialog = document.getElementById('priceDialog');
  var stockDialog = document.getElementById('stockDialog');
  var historyDialog = document.getElementById('historyDialog');
  if (!priceDialog) return;

  function csrfField() {
    var form = priceDialog.querySelector('form');
    var input = form.querySelector('input[name="csrf_token"]');
    if (!input) {
      input = document.createElement('input');
      input.type = 'hidden';
      input.name = 'csrf_token';
      form.prepend(input);
    }
    var meta = document.querySelector('meta[name="csrf-token"]');
    input.value = meta ? meta.getAttribute('content') : '';
    return input.value;
  }

  var priceProductId = null;
  window.showPrice = function (id, name, current) {
    priceProductId = id;
    document.getElementById('priceTitle').textContent =
      'Cambiar precio — ' + name + ' (actual: ' + current.toFixed(2) + ')';
    document.getElementById('newPrice').value = current;
    document.getElementById('priceReason').value = '';
    priceDialog.showModal();
  };

  document.getElementById('priceForm').addEventListener('submit', function (event) {
    event.preventDefault();
    fetch('/inventory/products/' + priceProductId + '/price', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({
        csrf_token: csrfField(),
        price: document.getElementById('newPrice').value,
        reason: document.getElementById('priceReason').value
      })
    }).then(function (response) {
      if (response.ok) location.reload();
      else response.json().then(function (data) { alert(data.message || 'Error'); });
    });
  });

  var stockProductId = null;
  window.showStock = function (id, name, current) {
    stockProductId = id;
    document.getElementById('stockTitle').textContent = 'Ajustar stock — ' + name;
    document.getElementById('stockCurrent').textContent = 'Stock actual: ' + current;
    document.getElementById('stockDelta').value = '';
    document.getElementById('stockNote').value = '';
    stockDialog.showModal();
  };

  document.getElementById('stockForm').addEventListener('submit', function (event) {
    event.preventDefault();
    fetch('/inventory/products/' + stockProductId + '/stock', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: new URLSearchParams({
        csrf_token: csrfField(),
        delta: document.getElementById('stockDelta').value,
        note: document.getElementById('stockNote').value
      })
    }).then(function (response) {
      if (response.ok) location.reload();
      else response.json().then(function (data) { alert(data.message || 'Error'); });
    });
  });

  window.toggleProduct = function (id) {
    var meta = document.querySelector('meta[name="csrf-token"]');
    var form = document.createElement('form');
    form.method = 'post';
    form.action = '/inventory/products/' + id + '/toggle';
    form.innerHTML = '<input type="hidden" name="csrf_token" value="' +
      (meta ? meta.getAttribute('content') : '') + '">';
    document.body.appendChild(form);
    form.submit();
  };

  window.showHistory = function (id) {
    fetch('/inventory/products/' + id + '/history', {credentials: 'same-origin'})
      .then(function (response) { return response.json(); })
      .then(function (data) {
        var body = document.getElementById('historyBody');
        body.innerHTML = '';
        function section(title, rows, renderer) {
          var heading = document.createElement('h4');
          heading.textContent = title;
          body.appendChild(heading);
          if (!rows.length) {
            var empty = document.createElement('p');
            empty.className = 'muted';
            empty.textContent = 'Sin registros.';
            body.appendChild(empty);
            return;
          }
          rows.forEach(function (item) {
            var line = document.createElement('div');
            line.className = 'history-item';
            line.textContent = renderer(item);
            body.appendChild(line);
          });
        }
        section('Precios', data.prices, function (p) {
          return (p.created_at || '').slice(0, 16).replace('T', ' ') + ' — ' +
            p.old_price + ' → ' + p.new_price +
            (p.reason ? ' · ' + p.reason : '') +
            ' · por ' + (p.actor_name || 'sistema');
        });
        section('Stock', data.stock, function (m) {
          return (m.created_at || '').slice(0, 16).replace('T', ' ') + ' — ' +
            (m.delta > 0 ? '+' : '') + m.delta + ' (queda ' + m.resulting_stock +
            ') · ' + m.cause + (m.sale_id ? ' · venta V' + m.sale_id : '') +
            ' · por ' + (m.actor_name || 'sistema');
        });
        historyDialog.showModal();
      });
  };
})();
