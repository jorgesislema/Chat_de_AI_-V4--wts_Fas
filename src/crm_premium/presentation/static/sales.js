/* Ventas: diálogo de nueva venta con líneas dinámicas y cobro por API.
   El catálogo llega en la isla JSON #catalogData (CSP-safe, sin scraping). */
(function () {
  'use strict';
  var dialog = document.getElementById('saleDialog');
  var catalogNode = document.getElementById('catalogData');
  if (!dialog || !catalogNode) return;
  var products = JSON.parse(catalogNode.textContent);

  function fillSelect(select) {
    select.innerHTML = '';
    products.forEach(function (p, index) {
      var option = document.createElement('option');
      option.value = p.id;
      option.textContent = p.name + ' — ' + Number(p.price).toFixed(2);
      select.appendChild(option);
    });
    select.addEventListener('change', recalc);
  }

  function recalc() {
    var total = 0;
    document.querySelectorAll('.sale-line').forEach(function (line) {
      var id = parseInt(line.querySelector('.product-select').value, 10);
      var qty = parseInt(line.querySelector('.qty-input').value, 10) || 0;
      var product = products.find(function (p) { return p.id === id; });
      if (!product) return;
      var lineTotal = Number(product.price) * qty;
      line.querySelector('.line-total').textContent = lineTotal.toFixed(2);
      total += lineTotal;
    });
    document.getElementById('saleTotal').textContent = total.toFixed(2);
  }

  function bindLine(line) {
    line.querySelector('.qty-input').addEventListener('input', recalc);
    line.querySelector('.remove-line').addEventListener('click', function () {
      if (document.querySelectorAll('.sale-line').length > 1) {
        line.remove();
        recalc();
      }
    });
    fillSelect(line.querySelector('.product-select'));
  }

  document.getElementById('newSaleBtn').addEventListener('click', function () {
    document.getElementById('saleError').classList.add('hidden');
    dialog.showModal();
    recalc();
  });

  bindLine(document.querySelector('.sale-line'));

  document.getElementById('addLine').addEventListener('click', function () {
    var clone = document.querySelector('.sale-line').cloneNode(true);
    clone.querySelector('.qty-input').value = 1;
    document.getElementById('saleLines').appendChild(clone);
    bindLine(clone);
    recalc();
  });

  var contactTimer = null;
  document.getElementById('saleContact').addEventListener('input', function (e) {
    clearTimeout(contactTimer);
    var q = e.target.value.trim();
    if (q.length < 2) { window.saleContactId = null; return; }
    contactTimer = setTimeout(function () {
      fetch('/api/contacts/search?q=' + encodeURIComponent(q),
            {credentials: 'same-origin'})
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (!data.ok) return;
          var list = document.getElementById('saleContactOptions');
          list.innerHTML = '';
          data.items.forEach(function (c) {
            var option = document.createElement('option');
            option.value = c.name;
            option.label = c.name + (c.phone ? ' · ' + c.phone : '');
            option.dataset.id = c.id;
            list.appendChild(option);
          });
        });
    }, 250);
  });
  document.getElementById('saleContact').addEventListener('change', function (e) {
    var text = e.target.value.trim();
    var match = Array.from(
      document.getElementById('saleContactOptions').options)
      .find(function (o) { return o.value === text; });
    window.saleContactId = match ? parseInt(match.dataset.id, 10) : null;
  });

  document.getElementById('saleClose').addEventListener('click', function () { dialog.close(); });
  document.getElementById('saleCancel').addEventListener('click', function () { dialog.close(); });

  document.getElementById('saleConfirm').addEventListener('click', function () {
    var lines = [];
    document.querySelectorAll('.sale-line').forEach(function (line) {
      var qty = parseInt(line.querySelector('.qty-input').value, 10) || 0;
      var id = parseInt(line.querySelector('.product-select').value, 10);
      if (qty > 0 && id) lines.push({product_id: id, qty: qty});
    });
    var error = document.getElementById('saleError');
    if (!lines.length) {
      error.textContent = 'Añada al menos un artículo con cantidad.';
      error.classList.remove('hidden');
      return;
    }
    var branchSel = document.getElementById('saleBranch');
    window.crmApi('/api/sales', {
      method: 'POST',
      body: JSON.stringify({
        lines: lines,
        payment_method: document.getElementById('paymentMethod').value,
        contact_id: window.saleContactId || null,
        branch_id: branchSel ? parseInt(branchSel.value, 10) : null,
        note: document.getElementById('saleNote').value || null
      })
    }).then(function (res) {
      if (res.ok) {
        dialog.close();
        location.reload();
      } else {
        error.textContent = res.data.message || 'No se pudo registrar la venta';
        error.classList.remove('hidden');
      }
    });
  });

  window.reverseSale = function (saleId) {
    var reason = prompt('Motivo de la reversión (auditado):');
    if (reason === null) return;
    window.crmApi('/api/sales/' + saleId + '/reverse', {
      method: 'POST',
      body: JSON.stringify({reason: reason})
    }).then(function (res) {
      if (res.ok) location.reload();
      else alert(res.data.message || 'No se pudo revertir');
    });
  };
})();
