/* Agenda visual: día/semana/mes sobre la API propia. Sin librerías externas.
   El servidor fija zona horaria y rangos; el cliente sólo pinta y pide.

   E01-R/A5:
   - Rango horario dinámico: se amplía para no ocultar citas fuera de 07–20.
   - La continuación se pinta en cada día ocupado (no depende de startH<7).
   - Un fin exactamente a las 00:00 cierra el día anterior: no cuenta el
     día siguiente sin ocupación.
   - «Hoy» es la fecha del negocio (data-zone), no la del navegador.
   - El fin se propone (+30 min, editable) y el cliente se elige por su ID
     interno con etiqueta única (nombres repetidos no seleccionan por texto).
   - Reprogramar precarga cliente/servicio/recurso/versión; doble envío
     bloqueado; el error conserva el formulario. */
(function () {
  'use strict';

  var root = document.getElementById('agendaRoot');
  if (!root) return;
  var ZONE = root.getAttribute('data-zone') || 'UTC';

  var state = {
    view: 'week',
    date: businessToday(),
    resource: 'all',
    cancelled: false,
    events: [],
    range: null,
    editId: null,
    submitting: false
  };
  var WEEKDAYS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];
  var HOUR_FIRST_DEFAULT = 7;
  var HOUR_LAST_DEFAULT = 20;

  function businessToday() {
    // Fecha del negocio: el servidor entrega la zona; el navegador nunca
    // decide el día con su reloj local.
    try {
      return new Intl.DateTimeFormat('en-CA', {
        timeZone: ZONE, year: 'numeric', month: '2-digit', day: '2-digit'
      }).format(new Date());
    } catch (error) {
      return new Date().toISOString().slice(0, 10);
    }
  }

  function fetchAgenda() {
    var params = new URLSearchParams({
      view: state.view, date: state.date,
      resource: state.resource, cancelled: state.cancelled ? '1' : '0'
    });
    window.crmApi('/api/agenda?' + params).then(function (res) {
      if (!res.ok) { root.textContent = res.data.message || 'Error'; return; }
      state.events = res.data.events;
      state.range = res.data.range;
      document.getElementById('periodLabel').textContent = res.data.label;
      render();
    });
  }

  /* Días ocupados por una cita: [start_date, end_date) salvo que el fin sea
     distinto de 00:00, en cuyo caso el día final también cuenta. */
  function occupies(event, day) {
    if (day < event.start_date) return false;
    if (day < event.end_date) return true;
    return day === event.end_date && event.end_time !== '00:00';
  }

  function eventsFor(day) {
    return state.events.filter(function (e) {
      return occupies(e, day);
    }).sort(function (a, b) { return a.start_time < b.start_time ? -1 : 1; });
  }

  /* Rango horario dinámico: nunca ocultar una reserva visible. */
  function hourBounds() {
    var first = HOUR_FIRST_DEFAULT;
    var last = HOUR_LAST_DEFAULT;
    state.events.forEach(function (e) {
      if (!occupiesCurrentView(e)) return;
      first = Math.min(first, parseInt(e.start_time, 10));
      var endH = e.end_time === '00:00' ? 24 : parseInt(e.end_time, 10);
      last = Math.max(last, endH);
    });
    first = Math.max(0, Math.min(first, 23));
    last = Math.max(first + 1, Math.min(last, 24));
    return {first: first, last: last};
  }

  function occupiesCurrentView(event) {
    // Citas del rango visible actual (state.range.days).
    var days = (state.range && state.range.days) || [];
    return days.some(function (d) { return occupies(event, d.date); });
  }

  function chip(event, isContinuation) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'event-chip st-' + event.operational_status +
      (isContinuation ? ' is-continuation' : '');
    btn.innerHTML = '<strong>' + esc(event.start_time) + '</strong> ' +
      esc(event.title) +
      '<small>' + esc(event.resource_name) +
      (event.contact_name ? ' · ' + esc(event.contact_name) : '') + '</small>';
    btn.addEventListener('click', function () { openDetail(event.id); });
    return btn;
  }

  function esc(value) {
    var div = document.createElement('div');
    div.textContent = value == null ? '' : String(value);
    return div.innerHTML;
  }

  function dayHead(day, weekday) {
    var head = document.createElement('div');
    head.className = 'agenda-day-head' + (day === businessToday() ? ' is-today' : '');
    head.innerHTML = WEEKDAYS[weekday] + '<strong>' + day.slice(8, 10) + '</strong>';
    return head;
  }

  function slotButton(day, hour) {
    var hh = String(hour).padStart(2, '0');
    var free = document.createElement('button');
    free.type = 'button';
    free.className = 'slot-btn';
    free.title = 'Nueva cita ' + day + ' ' + hh + ':00';
    free.setAttribute('aria-label', 'Nueva cita el ' + day + ' a las ' + hh + ':00');
    free.addEventListener('click', function () {
      openNew(day, hh + ':00');   // hora exacta del hueco pulsado
    });
    return free;
  }

  function hourCell(day, hour, events, gridFirst) {
    var holder = document.createElement('div');
    holder.className = 'slot-cell';
    holder.appendChild(slotButton(day, hour));
    events.forEach(function (event) {
      var startH = parseInt(event.start_time, 10);
      if (event.start_date === day && startH === hour) {
        holder.appendChild(chip(event, false));
      } else if (event.start_date < day && hour === gridFirst) {
        // Continuación de otro día: primer hueco del día, sin depender de
        // la hora de inicio original (A5).
        holder.appendChild(chip(event, true));
      }
    });
    return holder;
  }

  function buildDayColumn(day, gridFirst, gridLast, tall) {
    var col = document.createElement('div');
    col.appendChild(dayHead(day.date, day.weekday));
    var list = document.createElement('div');
    list.className = 'day-col';
    if (tall) list.style.minHeight = '520px';
    var events = eventsFor(day.date);
    for (var hour = gridFirst; hour <= gridLast; hour++) {
      list.appendChild(hourCell(day.date, hour, events, gridFirst));
    }
    col.appendChild(list);
    return col;
  }

  function renderWeek() {
    root.textContent = '';
    var bounds = hourBounds();
    var grid = document.createElement('div');
    grid.className = 'grid-cols';
    grid.style.gridTemplateColumns = 'repeat(7, 1fr)';
    state.range.days.forEach(function (day) {
      grid.appendChild(buildDayColumn(day, bounds.first, bounds.last, false));
    });
    root.appendChild(grid);
  }

  function renderDay() {
    root.textContent = '';
    // E01-R/A5: el día mostrado es el seleccionado (state.date), no el
    // lunes de su semana: days[0] hacía crear citas en días pasados.
    var bounds = hourBounds();
    var day = state.range.days.find(function (d) {
      return d.date === state.date;
    }) || state.range.days[0];
    var grid = document.createElement('div');
    grid.className = 'grid-cols';
    grid.style.gridTemplateColumns = '1fr';
    grid.appendChild(buildDayColumn(day, bounds.first, bounds.last, true));
    root.appendChild(grid);
  }

  function renderMonth() {
    root.textContent = '';
    var grid = document.createElement('div');
    grid.className = 'grid-cols';
    grid.style.gridTemplateColumns = 'repeat(7, 1fr)';
    var midMonth = monthOf(state.range.days[20].date);
    state.range.days.forEach(function (day) {
      var cell = document.createElement('div');
      cell.className = 'month-cell' +
        (day.date === businessToday() ? ' is-today' : '');
      if (monthOf(day.date) !== midMonth) {
        cell.classList.add('is-out');
      }
      var num = document.createElement('div');
      num.className = 'month-daynum';
      num.textContent = day.date.slice(8, 10);
      cell.appendChild(num);
      var events = eventsFor(day.date);
      events.slice(0, 3).forEach(function (event) {
        var mini = chip(event, event.start_date < day.date);
        mini.innerHTML = '<strong>' + esc(event.start_time) + '</strong> ' +
          esc(event.title);
        cell.appendChild(mini);
      });
      if (events.length > 3) {
        // E01-R/A5: «Ver más» abre la vista Día de ESA fecha.
        var more = document.createElement('button');
        more.type = 'button';
        more.className = 'month-daynum month-more';
        more.textContent = '+' + (events.length - 3) + ' más';
        more.setAttribute('aria-label', 'Ver las ' + events.length +
          ' citas del ' + day.date);
        more.addEventListener('click', function () {
          state.view = 'day';
          state.date = day.date;
          syncViewButtons();
          fetchAgenda();
        });
        cell.appendChild(more);
      }
      var add = document.createElement('button');
      add.type = 'button';
      add.className = 'month-add';
      add.textContent = '+';
      add.setAttribute('aria-label', 'Nueva cita el ' + day.date);
      add.addEventListener('click', function () { openNew(day.date, ''); });
      cell.appendChild(add);
      grid.appendChild(cell);
    });
    root.appendChild(grid);
  }

  function monthOf(day) { return day.slice(0, 7); }

  function render() {
    if (state.view === 'month') renderMonth();
    else if (state.view === 'day') renderDay();
    else renderWeek();
  }

  /* ------------------------------------------------------------ detalle */
  var eventDialog = document.getElementById('eventDialog');
  var dialogBody = document.getElementById('eventDialogBody');

  function actionButton(label, className, payload) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn ' + className + ' btn-sm';
    btn.textContent = label;
    btn.addEventListener('click', function () {
      btn.disabled = true;
      window.crmApi('/api/appointments/' + payload.appointment_id + '/transition',
        {method: 'POST', body: JSON.stringify(payload.body)})
        .then(function (res) {
          btn.disabled = false;
          if (!res.ok) { alert(res.data.message || 'No se pudo completar'); return; }
          eventDialog.close();
          fetchAgenda();
        });
    });
    return btn;
  }

  /* Cancelar al pulsar el botón, sin popup al abrir el detalle: se muestra
     un campo de motivo en el propio diálogo (E01-R/A5). */
  function cancelButton(a) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-danger btn-sm';
    btn.textContent = 'Cancelar cita';
    btn.addEventListener('click', function () {
      var old = document.getElementById('cancelReasonRow');
      if (old) old.remove();
      var row = document.createElement('div');
      row.id = 'cancelReasonRow';
      // E01-R/A4: propiedades tipadas (CSSOM); style="..." y atributos style
      // violan style-src 'self'.
      row.style.display = 'flex';
      row.style.gap = '6px';
      row.style.margin = '6px 0';
      var input = document.createElement('input');
      input.className = 'input';
      input.maxLength = 300;
      input.placeholder = 'Motivo de la cancelación (opcional)';
      var confirm = document.createElement('button');
      confirm.type = 'button';
      confirm.className = 'btn btn-danger btn-sm';
      confirm.textContent = 'Confirmar cancelación';
      confirm.addEventListener('click', function () {
        confirm.disabled = true;
        window.crmApi('/api/appointments/' + a.id + '/transition', {
          method: 'POST',
          body: JSON.stringify({action: 'cancel',
            expected_version: a.row_version, reason: input.value})
        }).then(function (res) {
          if (!res.ok) { alert(res.data.message || 'No se pudo cancelar'); return; }
          eventDialog.close();
          fetchAgenda();
        });
      });
      row.appendChild(input);
      row.appendChild(confirm);
      dialogBody.insertBefore(row, btn.parentNode);
      btn.disabled = true;
    });
    return btn;
  }

  function openDetail(id) {
    window.crmApi('/api/appointments/' + id).then(function (res) {
      if (!res.ok) { alert(res.data.message || 'Error'); return; }
      var a = res.data.appointment;
      document.getElementById('eventDialogTitle').textContent = a.title;
      dialogBody.textContent = '';

      var info = document.createElement('dl');
      info.className = 'detail-list-inline';
      var rows = [
        ['Estado', a.operational_status],
        ['Inicio', a.start_local.date + ' ' + a.start_local.time],
        ['Fin', a.end_local.date + ' ' + a.end_local.time],
        ['Recurso', a.resource_name],
        ['Contacto', a.contact_name || '—'],
        ['Teléfono', a.contact_phone || '—'],
        ['Canal', a.channel || '—']
      ];
      rows.forEach(function (pair) {
        var dt = document.createElement('dt');
        dt.textContent = pair[0];
        var dd = document.createElement('dd');
        dd.textContent = pair[1];
        info.appendChild(dt);
        info.appendChild(dd);
      });
      dialogBody.appendChild(info);

      var actions = document.createElement('div');
      actions.style.display = 'flex';
      actions.style.flexWrap = 'wrap';
      actions.style.gap = '6px';
      actions.style.margin = '10px 0';
      res.data.allowed_actions.forEach(function (action) {
        if (action === 'confirm') {
          actions.appendChild(actionButton('Confirmar', 'btn-primary', {
            appointment_id: id, body: {action: 'confirm',
              expected_version: a.row_version}}));
        } else if (action === 'cancel') {
          actions.appendChild(cancelButton(a));
        } else if (action === 'attend') {
          actions.appendChild(actionButton('Atendida', 'btn-primary', {
            appointment_id: id, body: {action: 'attend',
              expected_version: a.row_version}}));
        } else if (action === 'no_show') {
          actions.appendChild(actionButton('No asistió', 'btn-ghost', {
            appointment_id: id, body: {action: 'no_show',
              expected_version: a.row_version}}));
        } else if (action === 'reprogram') {
          actions.appendChild(reprogramButton(a));
        } else if (action === 'admin_correct') {
          actions.appendChild(correctButton(a));
        }
      });
      dialogBody.appendChild(actions);

      if (res.data.pending_closure) {
        var warn = document.createElement('p');
        warn.className = 'alert alert-error';
        warn.textContent = 'Pendiente de cierre: la cita terminó sin registrar asistencia.';
        dialogBody.insertBefore(warn, actions);
      }

      var notesTitle = document.createElement('h4');
      notesTitle.textContent = 'Observaciones internas';
      dialogBody.appendChild(notesTitle);
      res.data.notes.forEach(function (note) {
        var box = document.createElement('div');
        box.className = 'note-box';
        box.textContent = note.body + ' — ' + note.author;
        dialogBody.appendChild(box);
      });
      var noteForm = document.createElement('form');
      var noteInput = document.createElement('input');
      noteInput.className = 'input';
      noteInput.maxLength = 2000;
      noteInput.placeholder = 'Añadir observación interna…';
      noteInput.required = true;
      noteForm.appendChild(noteInput);
      noteForm.addEventListener('submit', function (submitEvent) {
        submitEvent.preventDefault();
        window.crmApi('/api/appointments/' + id + '/transition', {
          method: 'POST',
          body: JSON.stringify({action: 'note', body: noteInput.value})
        }).then(function (res2) {
          if (res2.ok) openDetail(id); else alert(res2.data.message);
        });
      });
      dialogBody.appendChild(noteForm);

      var historyTitle = document.createElement('h4');
      historyTitle.textContent = 'Historial';
      historyTitle.style.marginTop = '14px';
      dialogBody.appendChild(historyTitle);
      res.data.history.slice().reverse().forEach(function (item) {
        var line = document.createElement('div');
        line.className = 'history-item';
        line.textContent = item.action_label + ' · ' + item.actor + ' · ' +
          item.created_at.slice(0, 16).replace('T', ' ') +
          (item.reason ? ' — ' + item.reason : '');
        dialogBody.appendChild(line);
      });

      eventDialog.showModal();
    });
  }

  /* Reprogramar precarga inicio/fin/cliente/servicio/recurso/versión:
     cambiar sólo la hora conserva los vínculos (E01-R/A5). */
  function reprogramButton(a) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-ghost btn-sm';
    btn.textContent = 'Reprogramar';
    btn.addEventListener('click', function () {
      state.editId = a.id;
      state.editVersion = a.row_version;
      document.getElementById('newTitle').value = a.title;
      document.getElementById('newStart').value =
        a.start_local.date + 'T' + a.start_local.time;
      document.getElementById('newEnd').value =
        a.end_local.date + 'T' + a.end_local.time;
      document.getElementById('newResource').value = a.resource_id;
      document.getElementById('newService').value = a.service_id || '';
      var contactInput = document.getElementById('newContact');
      if (a.contact_name) {
        contactInput.value = contactLabel(a.contact_id, a.contact_name,
                                          a.contact_phone);
        knownContacts[contactInput.value] = a.contact_id;
      } else {
        contactInput.value = '';
      }
      document.getElementById('newReason').value = '';
      newError.classList.add('hidden');
      document.getElementById('newDialog').showModal();
    });
    return btn;
  }

  function correctButton(a) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn btn-ghost btn-sm';
    btn.textContent = 'Corrección admin';
    btn.addEventListener('click', function () {
      var old = document.getElementById('correctRow');
      if (old) old.remove();
      var row = document.createElement('div');
      row.id = 'correctRow';
      // E01-R/A4: propiedades tipadas (CSSOM); style="..." y atributos style
      // violan style-src 'self'.
      row.style.display = 'flex';
      row.style.gap = '6px';
      row.style.margin = '6px 0';
      var select = document.createElement('select');
      select.className = 'input';
      ['pending', 'confirmed', 'attended', 'no_show', 'cancelled'].forEach(
        function (status) {
          var option = document.createElement('option');
          option.value = status;
          option.textContent = status;
          select.appendChild(option);
        });
      var reason = document.createElement('input');
      reason.className = 'input';
      reason.maxLength = 300;
      reason.placeholder = 'Motivo obligatorio';
      var confirm = document.createElement('button');
      confirm.type = 'button';
      confirm.className = 'btn btn-primary btn-sm';
      confirm.textContent = 'Aplicar';
      confirm.addEventListener('click', function () {
        if (!reason.value.trim()) { alert('Indique el motivo de la corrección'); return; }
        confirm.disabled = true;
        window.crmApi('/api/appointments/' + a.id + '/transition', {
          method: 'POST',
          body: JSON.stringify({action: 'correct', target: select.value,
            reason: reason.value, expected_version: a.row_version})
        }).then(function (res) {
          confirm.disabled = false;
          if (!res.ok) { alert(res.data.message); return; }
          eventDialog.close();
          fetchAgenda();
        });
      });
      row.appendChild(select);
      row.appendChild(reason);
      row.appendChild(confirm);
      dialogBody.insertBefore(row, btn.parentNode);
      btn.disabled = true;
    });
    return btn;
  }

  /* -------------------------------------------------------------- nueva */
  var newDialog = document.getElementById('newDialog');
  var newForm = document.getElementById('newForm');
  var newError = document.getElementById('newError');
  var knownContacts = {};   // etiqueta única → id interno (E01-R/A5)

  function contactLabel(id, name, phone) {
    return name + (phone ? ' · ' + phone : ' (#' + id + ')');
  }

  function openNew(day, time) {
    state.editId = null;
    newForm.reset();
    document.getElementById('newStart').value = time ? day + 'T' + time : '';
    proposeEnd();
    newError.classList.add('hidden');
    newDialog.showModal();
  }

  /* Fin propuesto: +30 min desde el inicio (editable por el usuario). */
  function proposeEnd() {
    var startValue = document.getElementById('newStart').value;
    if (!startValue) return;
    var start = new Date(startValue);
    if (isNaN(start.getTime())) return;
    var end = new Date(start.getTime() + 30 * 60000);
    document.getElementById('newEnd').value =
      end.getFullYear() + '-' + String(end.getMonth() + 1).padStart(2, '0') +
      '-' + String(end.getDate()).padStart(2, '0') + 'T' +
      String(end.getHours()).padStart(2, '0') + ':' +
      String(end.getMinutes()).padStart(2, '0');
  }

  var newCancel = document.getElementById('newCancel');
  if (newCancel) newCancel.addEventListener('click', function () {
    newDialog.close();
  });
  document.getElementById('eventDialogClose').addEventListener('click', function () {
    eventDialog.close();
  });

  document.getElementById('newStart').addEventListener('change', function () {
    var end = document.getElementById('newEnd');
    if (!end.value) proposeEnd();
  });
  document.getElementById('newEnd').addEventListener('change', function () {
    state.endTouched = document.getElementById('newEnd').value !== '';
  });

  newForm.addEventListener('submit', function (event) {
    event.preventDefault();
    // E01-R/A5: error visible sin cerrar ni perder el formulario; el fin
    // vacío no falla en silencio.
    if (!document.getElementById('newStart').value ||
        !document.getElementById('newEnd').value) {
      newError.textContent = 'Indique fecha y hora de inicio y de fin';
      newError.classList.remove('hidden');
      return;
    }
    var contactValue = document.getElementById('newContact').value.trim();
    var contactId = null;
    if (contactValue) {
      if (!(contactValue in knownContacts)) {
        // Nombre ambiguo o no seleccionado de la lista: error explícito.
        newError.textContent = 'Seleccione un cliente de la lista de resultados.';
        newError.classList.remove('hidden');
        return;
      }
      contactId = knownContacts[contactValue];
    }
    submitAppointment(contactId);
  });

  function submitAppointment(contactId) {
    if (state.submitting) return;   // doble click no duplica
    state.submitting = true;
    var submitBtn = newForm.querySelector('button[type="submit"]');
    if (submitBtn) submitBtn.disabled = true;
    var payload = {
      resource_id: parseInt(document.getElementById('newResource').value, 10),
      title: document.getElementById('newTitle').value,
      start: document.getElementById('newStart').value,
      end: document.getElementById('newEnd').value,
      contact_id: contactId,
      service_id: document.getElementById('newService').value || null,
      reason: document.getElementById('newReason').value || null
    };
    var request;
    if (state.editId) {
      payload.action = 'reprogram';
      payload.expected_version = state.editVersion;
      request = window.crmApi('/api/appointments/' + state.editId + '/transition',
        {method: 'POST', body: JSON.stringify(payload)});
    } else {
      request = window.crmApi('/api/appointments', {
        method: 'POST', body: JSON.stringify(payload)});
    }
    request.then(function (res) {
      state.submitting = false;
      if (submitBtn) submitBtn.disabled = false;
      if (res.ok) {
        newDialog.close();
        fetchAgenda();
      } else {
        newError.textContent = res.data.message || 'No se pudo guardar';
        newError.classList.remove('hidden');
      }
    });
  }

  /* -------------------------------------------------------------- barra */
  function shift(days) {
    var d = new Date(state.date + 'T12:00:00Z');
    if (state.view === 'day') d.setUTCDate(d.getUTCDate() + days);
    else if (state.view === 'week') d.setUTCDate(d.getUTCDate() + days * 7);
    else d.setUTCMonth(d.getUTCMonth() + days, 1);
    state.date = d.toISOString().slice(0, 10);
    fetchAgenda();
  }
  document.getElementById('prevBtn').addEventListener('click', function () { shift(-1); });
  document.getElementById('nextBtn').addEventListener('click', function () { shift(1); });
  document.getElementById('todayBtn').addEventListener('click', function () {
    state.date = businessToday();   // hoy en zona del negocio
    fetchAgenda();
  });
  function syncViewButtons() {
    document.querySelectorAll('.view-btn').forEach(function (other) {
      other.classList.toggle('active', other.dataset.view === state.view);
    });
  }
  document.querySelectorAll('.view-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      state.view = btn.dataset.view;
      syncViewButtons();
      fetchAgenda();
    });
  });
  document.getElementById('resourceFilter').addEventListener('change', function (e) {
    state.resource = e.target.value;
    fetchAgenda();
  });
  document.getElementById('showCancelled').addEventListener('change', function (e) {
    state.cancelled = e.target.checked;
    fetchAgenda();
  });

  /* Búsqueda de cliente: resultados con etiqueta única; la selección guarda
     el ID interno; el texto libre que no coincide da error visible. */
  var contactTimer = null;
  document.getElementById('newContact').addEventListener('input', function (e) {
    clearTimeout(contactTimer);
    var q = e.target.value.trim();
    if (q.length < 2) return;
    contactTimer = setTimeout(function () {
      window.crmApi('/api/contacts/search?q=' + encodeURIComponent(q))
        .then(function (res) {
          if (!res.ok) return;
          var list = document.getElementById('contactOptions');
          list.textContent = '';
          res.data.items.forEach(function (c) {
            var label = contactLabel(c.id, c.name, c.phone);
            knownContacts[label] = c.id;
            var option = document.createElement('option');
            option.value = label;
            option.label = label;
            list.appendChild(option);
          });
        });
    }, 250);
  });

  fetchAgenda();
})();
