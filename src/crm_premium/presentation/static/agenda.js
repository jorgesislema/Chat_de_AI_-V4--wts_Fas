/* Agenda visual: día/semana/mes sobre la API propia. Sin librerías externas.
   El servidor fija zona horaria y rangos; el cliente sólo pinta y pide. */
(function () {
  'use strict';

  var root = document.getElementById('agendaRoot');
  if (!root) return;

  var state = {
    view: 'week',
    date: localToday(),
    resource: 'all',
    cancelled: false,
    events: [],
    range: null,
    editId: null
  };
  var WEEKDAYS = ['lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom'];

  function localToday() {
    var now = new Date();
    var offset = now.getTimezoneOffset() * 60000;
    return new Date(now - offset).toISOString().slice(0, 10);
  }

  function fmtTime(hhmm) {
    return hhmm;
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

  function eventsFor(day) {
    // CORR01-E01: la cita aparece cada día que atraviesa (24/49 h, medianoche).
    return state.events.filter(function (e) {
      return e.start_date <= day && day <= e.end_date;
    }).sort(function (a, b) { return a.start_time < b.start_time ? -1 : 1; });
  }

  function chip(event) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'event-chip st-' + event.operational_status;
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
    head.className = 'agenda-day-head' + (day === localToday() ? ' is-today' : '');
    head.innerHTML = WEEKDAYS[weekday] + '<strong>' + day.slice(8, 10) + '</strong>';
    return head;
  }

  var HOUR_FIRST = 7;
  var HOUR_LAST = 20;

  function slotButton(day, hour) {
    var hh = String(hour).padStart(2, '0');
    var free = document.createElement('button');
    free.type = 'button';
    free.className = 'slot-btn';
    free.title = 'Nueva cita ' + day + ' ' + hh + ':00';
    free.setAttribute('aria-label', 'Nueva cita el ' + day + ' a las ' + hh + ':00');
    free.addEventListener('click', function () {
      openNew(day, hh + ':00');   // CORR01-E01: nunca 09:00 fija
    });
    return free;
  }

  function hourCell(day, hour, events) {
    var holder = document.createElement('div');
    holder.className = 'slot-cell';
    holder.appendChild(slotButton(day, hour));
    events.forEach(function (event) {
      var startH = parseInt(event.start_time, 10);
      if (event.start_date === day && startH === hour) {
        holder.appendChild(chip(event));
      } else if (event.start_date < day && day <= event.end_date &&
                 startH < HOUR_FIRST) {
        holder.appendChild(chip(event));  // continúa de otro día
      }
    });
    return holder;
  }

  function renderWeek() {
    root.innerHTML = '';
    var grid = document.createElement('div');
    grid.className = 'grid-cols';
    grid.style.gridTemplateColumns = 'repeat(7, 1fr)';
    state.range.days.forEach(function (day) {
      var col = document.createElement('div');
      col.appendChild(dayHead(day.date, day.weekday));
      var list = document.createElement('div');
      list.className = 'day-col';
      var events = eventsFor(day.date);
      for (var hour = HOUR_FIRST; hour <= HOUR_LAST; hour++) {
        list.appendChild(hourCell(day.date, hour, events));
      }
      col.appendChild(list);
      grid.appendChild(col);
    });
    root.appendChild(grid);
  }

  function renderDay() {
    root.innerHTML = '';
    var day = state.range.days[0];
    var grid = document.createElement('div');
    grid.className = 'grid-cols';
    grid.style.gridTemplateColumns = '1fr';
    var col = document.createElement('div');
    col.appendChild(dayHead(day.date, day.weekday));
    var list = document.createElement('div');
    list.className = 'day-col';
    list.style.minHeight = '520px';
    var events = eventsFor(day.date);
    for (var hour = HOUR_FIRST; hour <= HOUR_LAST; hour++) {
      list.appendChild(hourCell(day.date, hour, events));
    }
    col.appendChild(list);
    grid.appendChild(col);
    root.appendChild(grid);
  }

  function renderMonth() {
    root.innerHTML = '';
    var grid = document.createElement('div');
    grid.className = 'grid-cols';
    grid.style.gridTemplateColumns = 'repeat(7, 1fr)';
    state.range.days.forEach(function (day) {
      var cell = document.createElement('div');
      cell.className = 'month-cell' +
        (day.date === localToday() ? ' is-today' : '') +
        (day.date < state.range.start_date || day.date > state.range.end_date
         ? '' : '');
      if (monthOf(day.date) !== monthOf(state.range.days[20].date)) {
        cell.classList.add('is-out');
      }
      var num = document.createElement('div');
      num.className = 'month-daynum';
      num.textContent = day.date.slice(8, 10);
      cell.appendChild(num);
      var events = eventsFor(day.date);
      events.slice(0, 3).forEach(function (event) {
        var mini = chip(event);
        mini.innerHTML = '<strong>' + esc(event.start_time) + '</strong> ' +
          esc(event.title);
        cell.appendChild(mini);
      });
      if (events.length > 3) {
        var more = document.createElement('div');
        more.className = 'month-daynum';
        more.textContent = '+' + (events.length - 3) + ' más';
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
          if (!res.ok) { alert(res.data.message || 'No se pudo completar'); }
          eventDialog.close();
          fetchAgenda();
        });
    });
    return btn;
  }

  function openDetail(id) {
    window.crmApi('/api/appointments/' + id).then(function (res) {
      if (!res.ok) { alert(res.data.message || 'Error'); return; }
      var a = res.data.appointment;
      document.getElementById('eventDialogTitle').textContent = a.title;
      dialogBody.innerHTML = '';

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
      actions.style.cssText = 'display:flex;flex-wrap:wrap;gap:6px;margin:10px 0;';
      res.data.allowed_actions.forEach(function (action) {
        if (action === 'confirm') {
          actions.appendChild(actionButton('Confirmar', 'btn-primary', {
            appointment_id: id, body: {action: 'confirm',
              expected_version: a.row_version}}));
        } else if (action === 'cancel') {
          actions.appendChild(actionButton('Cancelar', 'btn-danger', {
            appointment_id: id, body: {action: 'cancel',
              expected_version: a.row_version,
              reason: prompt('Motivo de la cancelación (opcional):') || ''}}));
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
      document.getElementById('newReason').value = '';
      document.getElementById('newError').classList.add('hidden');
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
      var target = prompt('Estado destino (pending/confirmed/attended/no_show/cancelled):');
      if (!target) return;
      var reason = prompt('Motivo obligatorio de la corrección:') || '';
      window.crmApi('/api/appointments/' + a.id + '/transition', {
        method: 'POST',
        body: JSON.stringify({action: 'correct', target: target,
          reason: reason, expected_version: a.row_version})
      }).then(function (res) {
        if (!res.ok) alert(res.data.message);
        eventDialog.close();
        fetchAgenda();
      });
    });
    return btn;
  }

  /* -------------------------------------------------------------- nueva */
  var newDialog = document.getElementById('newDialog');
  var newForm = document.getElementById('newForm');
  var newError = document.getElementById('newError');

  function openNew(day, time) {
    state.editId = null;
    newForm.reset();
    document.getElementById('newStart').value = time ? day + 'T' + time : '';
    document.getElementById('newEnd').value = '';
    newError.classList.add('hidden');
    newDialog.showModal();
  }

  function padHour(value) {
    return String(value).padStart(2, '0');
  }

  document.getElementById('newCancel').addEventListener('click', function () {
    newDialog.close();
  });
  document.getElementById('eventDialogClose').addEventListener('click', function () {
    eventDialog.close();
  });

  function resolveContact() {
    var input = document.getElementById('newContact');
    var text = input.value.trim();
    if (!text) return Promise.resolve(null);
    return window.crmApi('/api/contacts/search?q=' + encodeURIComponent(text))
      .then(function (res) {
        if (!res.ok) return null;
        var match = res.data.items.find(function (c) { return c.name === text; });
        return match ? match.id : 'notfound';
      });
  }

  newForm.addEventListener('submit', function (event) {
    event.preventDefault();
    resolveContact().then(function (contactId) {
      if (contactId === 'notfound') {
        newError.textContent = 'Seleccione un cliente de la lista de resultados.';
        newError.classList.remove('hidden');
        return;
      }
      submitAppointment(contactId);
    });
  });

  function submitAppointment(contactId) {
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
      if (res.ok) {
        newDialog.close();
        fetchAgenda();
      } else {
        newError.textContent = res.data.message || 'No se pudo guardar';
        newError.classList.remove('hidden');
      }
    });
  }
  // fin submitAppointment

  /* -------------------------------------------------------------- barra */
  function shift(days) {
    var d = new Date(state.date + 'T12:00:00');
    if (state.view === 'day') d.setDate(d.getDate() + days);
    else if (state.view === 'week') d.setDate(d.getDate() + days * 7);
    else d.setMonth(d.getMonth() + days, 1);
    state.date = d.toISOString().slice(0, 10);
    fetchAgenda();
  }
  document.getElementById('prevBtn').addEventListener('click', function () { shift(-1); });
  document.getElementById('nextBtn').addEventListener('click', function () { shift(1); });
  document.getElementById('todayBtn').addEventListener('click', function () {
    state.date = localToday();
    fetchAgenda();
  });
  document.querySelectorAll('.view-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.view-btn').forEach(function (other) {
        other.classList.remove('active');
      });
      btn.classList.add('active');
      state.view = btn.dataset.view;
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
          list.innerHTML = '';
          res.data.items.forEach(function (c) {
            var option = document.createElement('option');
            option.value = c.name;
            option.label = c.name + (c.phone ? ' · ' + c.phone : '');
            list.appendChild(option);
          });
        });
    }, 250);
  });

  fetchAgenda();
})();
