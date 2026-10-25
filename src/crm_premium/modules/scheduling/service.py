"""Agenda: citas, estados operativos, conflictos e historial.

Puerto controlado de crm/reservation_service.py (V3) a PostgreSQL. Reglas
conservadas:
- Normalización a UTC con zona IANA explícita; horas locales inexistentes o
  ambiguas por DST se rechazan sin offset.
- Fin posterior a inicio; nada en el pasado.
- El recurso debe existir y estar activo; el contacto es opcional.
- Conflictos por intervalos semiabiertos [inicio, fin); el bloqueo consultivo
  por recurso dentro de la transacción impide dos reservas simultáneas.
- Reprogramar conserva ``event_id`` y exige versión (concurrencia optimista).
- Estados: pending/confirmed/attended/no_show/cancelled con transiciones
  validadas e idempotencia en confirmar/cancelar/asistencia.
- Historial y auditoría en la misma transacción del cambio.
"""
import uuid
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Json

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row
from ...shared.timeutil import (AmbiguousLocalTime, InvalidZone,
                                NonexistentLocalTime, to_utc)

INVALID_DATETIME = 'invalid_datetime'
INVALID_RANGE = 'invalid_range'
INVALID_ZONE = 'invalid_zone'
NONEXISTENT_LOCAL_TIME = 'nonexistent_local_time'
AMBIGUOUS_LOCAL_TIME = 'ambiguous_local_time'
PAST_DATETIME = 'past_datetime'
MISSING_RESOURCE = 'missing_resource'
INACTIVE_RESOURCE = 'inactive_resource'
INVALID_TITLE = 'invalid_title'
NOT_FOUND = 'not_found'
RESOURCE_MISMATCH = 'resource_mismatch'
CANCELLED_APPOINTMENT = 'cancelled_appointment'
OVERLAP = 'overlap'
VERSION_CONFLICT = 'version_conflict'
INVALID_TRANSITION = 'invalid_transition'
TOO_LATE = 'too_late'
TOO_EARLY = 'too_early'
REASON_REQUIRED = 'reason_required'
FORBIDDEN = 'forbidden'
ALREADY_CLOSED = 'already_closed'
NO_RESURRECTION = 'no_resurrection'
NOTE_REQUIRED = 'note_required'
OUTSIDE_BUSINESS_HOURS = 'outside_business_hours'

CREATION_CHANNELS = ('web', 'bot', 'google')
OPERATIONAL_STATES = ('pending', 'confirmed', 'attended', 'no_show', 'cancelled')
OPEN_STATES = ('pending', 'confirmed')
CLOSED_STATES = ('attended', 'no_show')

STATUS_LABELS = {
    'pending': 'Pendiente',
    'confirmed': 'Confirmada',
    'attended': 'Atendida',
    'no_show': 'No asistió',
    'cancelled': 'Cancelada',
}
ACTION_LABELS = {
    'creacion': 'Creación',
    'confirmacion': 'Confirmación',
    'reprogramacion': 'Reprogramación',
    'cancelacion': 'Cancelación',
    'asistencia': 'Asistencia',
    'no_asistio': 'No asistió',
    'correccion': 'Corrección administrativa',
    'nota': 'Observación interna',
}

#: Espacio de claves del bloqueo consultivo por recurso.
ADVISORY_NAMESPACE = 94001


def _result(code, message, **extra):
    return {'ok': False, 'code': code, 'message': message, 'appointment': None, **extra}


def _clock(clock=None):
    current = clock or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current


def _actor_reference(actor):
    if isinstance(actor, bool):
        return None, 'system'
    if isinstance(actor, int):
        return actor, None
    return None, (actor or 'system').strip()[:40] or 'system'


def _serialize(appt):
    data = row(appt)
    return data


def _write_history(cur, appointment_id, action, actor, detail=None, reason=None,
                   note_id=None):
    user_id, label = _actor_reference(actor)
    cur.execute(
        """INSERT INTO appointment_history
           (appointment_id, action, actor_user_id, actor_label, detail, reason, note_id)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (appointment_id, action, user_id, label,
         Json(detail) if detail is not None else None,
         (reason or '').strip()[:300] or None, note_id))


def _audit(cur, actor, action):
    user_id, label = _actor_reference(actor)
    text = action if label is None else f'{action} [{label}]'
    cur.execute(
        'INSERT INTO audit_log (actor_user_id, actor_label, action) VALUES (%s, %s, %s)',
        (user_id, label, text[:500] if label else action[:500]))


def _conflict(cur, resource_id, start_utc, end_utc, exclude_id):
    cur.execute(
        """SELECT id FROM appointments
           WHERE resource_id = %s AND operational_status <> 'cancelled'
             AND start_utc < %s AND end_utc > %s
             AND (%s::bigint IS NULL OR id <> %s)
           LIMIT 1""",
        (resource_id, end_utc, start_utc, exclude_id, exclude_id))
    return cur.fetchone()


def _load(cur, appointment_id):
    cur.execute('SELECT * FROM appointments WHERE id = %s', (appointment_id,))
    return cur.fetchone()


def _version_conflict(old, expected_version):
    if expected_version is None:
        return _result(VERSION_CONFLICT,
                       'Falta la versión de la cita; recargue la agenda')
    try:
        expected = int(expected_version)
    except (TypeError, ValueError):
        return _result(VERSION_CONFLICT,
                       'La versión de la cita no es válida; recargue e intente de nuevo')
    if old['row_version'] != expected:
        return _result(VERSION_CONFLICT,
                       'La cita cambió mientras editaba. Recargue para no sobrescribir cambios.')
    return None


def save_appointment(url, *, resource_id, start, end, title, zone,
                     appointment_id=None, contact_id=None, actor=None, clock=None,
                     expected_version=None, reason=None, role='user',
                     channel=None, window_policy=None, origin='local',
                     service_id=None):
    """Crea o reprograma una cita aplicando las reglas comunes."""
    if channel is not None and channel not in CREATION_CHANNELS:
        return _result(INVALID_TITLE, 'El canal de creación no es válido')
    if not isinstance(title, str) or not title.strip():
        return _result(INVALID_TITLE, 'El título de la cita es obligatorio')

    try:
        start_utc = to_utc(start, zone)
        end_utc = to_utc(end, zone)
    except InvalidZone as exc:
        return _result(INVALID_ZONE, str(exc))
    except NonexistentLocalTime as exc:
        return _result(NONEXISTENT_LOCAL_TIME, str(exc))
    except AmbiguousLocalTime as exc:
        return _result(AMBIGUOUS_LOCAL_TIME, str(exc))
    except (ValueError, TypeError):
        return _result(INVALID_DATETIME, 'La fecha u hora indicada no es válida')

    if end_utc <= start_utc:
        return _result(INVALID_RANGE, 'El fin debe ser posterior al inicio')
    current = _clock(clock)
    if start_utc < current:
        return _result(PAST_DATETIME, 'Seleccione una fecha futura')

    outside_reason = None
    if window_policy is not None:
        window_reason = window_policy(start_utc, end_utc)
        if window_reason:
            if role != 'admin' or not (reason or '').strip():
                return _result(OUTSIDE_BUSINESS_HOURS, window_reason)
            outside_reason = 'Excepción fuera de horario: ' + reason.strip()

    contact_value = None
    if contact_id not in (None, ''):
        try:
            contact_value = int(contact_id)
        except (TypeError, ValueError):
            return _result(INVALID_TITLE, 'El contacto indicado no es válido')

    try:
        resource_id = int(resource_id)
    except (TypeError, ValueError):
        return _result(MISSING_RESOURCE, 'Recurso no válido')

    with transaction(url) as conn:
        with conn.cursor() as cur:
            # Bloqueo consultivo: serializa reservas simultáneas del recurso.
            cur.execute('SELECT pg_advisory_xact_lock(%s, %s)',
                        (ADVISORY_NAMESPACE, resource_id))
            cur.execute('SELECT id, name, is_active, branch_id '
                        'FROM resources WHERE id = %s', (resource_id,))
            resource = cur.fetchone()
            if not resource:
                return _result(MISSING_RESOURCE, 'Recurso no encontrado')
            if not resource['is_active']:
                return _result(INACTIVE_RESOURCE, 'Seleccione un recurso activo')

            old = None
            if appointment_id is not None:
                old = _load(cur, appointment_id)
                if not old:
                    return _result(NOT_FOUND, 'Cita no encontrada')
                if old['resource_id'] != resource_id:
                    return _result(RESOURCE_MISMATCH,
                                   'Para cambiar de recurso, cancele la cita y cree una nueva')
                if old['operational_status'] == 'cancelled':
                    return _result(CANCELLED_APPOINTMENT,
                                   'Cree una cita nueva para reemplazar una cancelada')
                if old['operational_status'] not in OPEN_STATES:
                    return _result(INVALID_TRANSITION,
                                   'Una cita cerrada no puede reprogramarse')
                conflict = _version_conflict(old, expected_version)
                if conflict:
                    return conflict
                if _clock(clock) >= old['start_utc']:
                    return _result(TOO_LATE,
                                   'La cita ya comenzó; use una corrección administrativa')
                if old['operational_status'] == 'confirmed' and not (reason or '').strip():
                    return _result(REASON_REQUIRED,
                                   'Indique el motivo de la reprogramación de una cita confirmada')

            if _conflict(cur, resource_id, start_utc, end_utc, appointment_id):
                return _result(OVERLAP, 'Ese horario ya está ocupado')

            if old is not None:
                cur.execute(
                    """UPDATE appointments
                       SET title=%s, start_utc=%s, end_utc=%s, contact_id=%s,
                           operational_status='pending', row_version=row_version+1,
                           updated_at=now()
                       WHERE id=%s""",
                    (title.strip()[:200], start_utc, end_utc, contact_value,
                     appointment_id))
                shown_id = appointment_id
                _write_history(cur, shown_id, 'reprogramacion', actor,
                               {'before': {'start': row(old)['start_utc'],
                                           'end': row(old)['end_utc'],
                                           'status': old['operational_status']},
                                'after': {'start': start_utc.isoformat(),
                                          'end': end_utc.isoformat(),
                                          'status': 'pending'}},
                               outside_reason or reason)
            else:
                service_value = None
                if service_id not in (None, ''):
                    try:
                        service_value = int(service_id)
                    except (TypeError, ValueError):
                        return _result(INVALID_TITLE, 'Servicio no válido')
                    cur.execute("SELECT 1 FROM products WHERE id=%s AND kind='servicio'",
                                (service_value,))
                    if not cur.fetchone():
                        return _result(INVALID_TITLE,
                                       'El servicio indicado no existe')
                event_id = uuid.uuid4().hex
                cur.execute(
                    """INSERT INTO appointments
                       (resource_id, contact_id, title, start_utc, end_utc, event_id,
                        origin, channel, operational_status, row_version,
                        branch_id, service_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', 1,
                               %s, %s)
                       RETURNING id""",
                    (resource_id, contact_value, title.strip()[:200], start_utc,
                     end_utc, event_id, origin, channel,
                     resource['branch_id'], service_value))
                shown_id = cur.fetchone()['id']
                _write_history(cur, shown_id, 'creacion', actor,
                               {'start': start_utc.isoformat(),
                                'end': end_utc.isoformat(),
                                'status': 'pending'}, outside_reason)

            _audit(cur, actor,
                   f"{'Reprogramación' if old is not None else 'Creación'} de cita {shown_id}")
            saved = _load(cur, shown_id)
    return {'ok': True, 'code': 'saved', 'message': 'Cita guardada',
            'appointment': _serialize(saved)}


def reprogram_appointment(url, *, appointment_id, start, end, title, zone,
                          expected_version, reason=None, actor=None, role='user',
                          clock=None, window_policy=None):
    """Reprograma cargando recurso/contacto actuales; la versión evita carreras."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            old = _load(cur, appointment_id)
    if not old:
        return _result(NOT_FOUND, 'Cita no encontrada')
    return save_appointment(
        url, resource_id=old['resource_id'], start=start, end=end,
        title=(title or old['title']), zone=zone, appointment_id=appointment_id,
        contact_id=old['contact_id'], actor=actor, clock=clock,
        expected_version=expected_version, reason=reason, role=role,
        channel=old['channel'], window_policy=window_policy,
        origin=old['origin'])


def cancel_appointment(url, *, appointment_id, actor=None, expected_version=None,
                       reason=None, clock=None):
    """Cancela una cita. Cancelar dos veces no duplica efectos."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            old = _load(cur, appointment_id)
            if not old:
                return _result(NOT_FOUND, 'Cita no encontrada')
            if old['operational_status'] == 'cancelled':
                return {'ok': True, 'code': 'cancelled',
                        'message': 'La cita ya estaba cancelada',
                        'appointment': _serialize(old), 'idempotent': True}
            if old['operational_status'] in CLOSED_STATES:
                return _result(ALREADY_CLOSED,
                               'Una cita ya cerrada no puede cancelarse; use una corrección administrativa')
            conflict = _version_conflict(old, expected_version)
            if conflict:
                return conflict
            if _clock(clock) >= old['start_utc']:
                return _result(TOO_LATE,
                               'La cita ya comenzó; use una corrección administrativa')
            cur.execute(
                """UPDATE appointments SET operational_status='cancelled',
                   row_version=row_version+1, updated_at=now() WHERE id=%s""",
                (appointment_id,))
            _write_history(cur, appointment_id, 'cancelacion', actor,
                           {'before': {'status': old['operational_status']},
                            'after': {'status': 'cancelled'}}, reason)
            _audit(cur, actor, f'Cancelación de cita {appointment_id}')
            saved = _load(cur, appointment_id)
    return {'ok': True, 'code': 'cancelled', 'message': 'Cita cancelada',
            'appointment': _serialize(saved), 'idempotent': False}


def confirm_appointment(url, *, appointment_id, expected_version, actor=None, clock=None):
    """Confirma una cita pendiente antes de su inicio (idempotente)."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            old = _load(cur, appointment_id)
            if not old:
                return _result(NOT_FOUND, 'Cita no encontrada')
            if old['operational_status'] == 'confirmed':
                return {'ok': True, 'code': 'confirmed',
                        'message': 'La cita ya estaba confirmada',
                        'appointment': _serialize(old), 'idempotent': True}
            if old['operational_status'] != 'pending':
                return _result(INVALID_TRANSITION,
                               'Sólo se puede confirmar una cita pendiente')
            conflict = _version_conflict(old, expected_version)
            if conflict:
                return conflict
            if _clock(clock) >= old['start_utc']:
                return _result(TOO_LATE, 'La cita ya comenzó; no puede confirmarse')
            cur.execute(
                """UPDATE appointments SET operational_status='confirmed',
                   row_version=row_version+1, updated_at=now() WHERE id=%s""",
                (appointment_id,))
            _write_history(cur, appointment_id, 'confirmacion', actor,
                           {'before': {'status': 'pending'},
                            'after': {'status': 'confirmed'}})
            _audit(cur, actor, f'Confirmación de cita {appointment_id}')
            saved = _load(cur, appointment_id)
    return {'ok': True, 'code': 'confirmed', 'message': 'Cita confirmada',
            'appointment': _serialize(saved), 'idempotent': False}


def mark_attendance(url, *, appointment_id, outcome, expected_version, actor=None,
                    clock=None):
    """Marca Atendida o No asistió desde el fin de la cita."""
    if outcome not in CLOSED_STATES:
        return _result(INVALID_TRANSITION, 'Resultado de asistencia no válido')
    with transaction(url) as conn:
        with conn.cursor() as cur:
            old = _load(cur, appointment_id)
            if not old:
                return _result(NOT_FOUND, 'Cita no encontrada')
            if old['operational_status'] == outcome:
                return {'ok': True, 'code': outcome,
                        'message': 'La asistencia ya estaba registrada',
                        'appointment': _serialize(old), 'idempotent': True}
            if old['operational_status'] == 'cancelled':
                return _result(INVALID_TRANSITION,
                               'Una cita cancelada no puede marcarse como asistida')
            if old['operational_status'] in CLOSED_STATES:
                return _result(INVALID_TRANSITION,
                               'La asistencia ya está cerrada; use una corrección administrativa')
            conflict = _version_conflict(old, expected_version)
            if conflict:
                return conflict
            if _clock(clock) < old['end_utc']:
                return _result(TOO_EARLY,
                               'Sólo se puede cerrar la asistencia cuando la cita terminó')
            cur.execute(
                """UPDATE appointments SET operational_status=%s,
                   row_version=row_version+1, updated_at=now() WHERE id=%s""",
                (outcome, appointment_id))
            action = 'asistencia' if outcome == 'attended' else 'no_asistio'
            _write_history(cur, appointment_id, action, actor,
                           {'before': {'status': old['operational_status']},
                            'after': {'status': outcome}})
            _audit(cur, actor,
                   f"{'Asistencia' if outcome == 'attended' else 'No asistió'} de cita {appointment_id}")
            saved = _load(cur, appointment_id)
    return {'ok': True, 'code': outcome, 'message': 'Asistencia registrada',
            'appointment': _serialize(saved), 'idempotent': False}


def admin_correct_status(url, *, appointment_id, target, reason, expected_version,
                         actor=None, role='user', clock=None):
    """Corrección excepcional de estado, sólo administrador y con motivo."""
    if role != 'admin':
        return _result(FORBIDDEN, 'Sólo un administrador puede corregir estados')
    if target not in OPERATIONAL_STATES:
        return _result(INVALID_TRANSITION, 'Estado de destino no válido')
    if not (reason or '').strip():
        return _result(REASON_REQUIRED, 'Indique el motivo de la corrección')
    with transaction(url) as conn:
        with conn.cursor() as cur:
            old = _load(cur, appointment_id)
            if not old:
                return _result(NOT_FOUND, 'Cita no encontrada')
            if old['operational_status'] == target:
                return {'ok': True, 'code': 'unchanged',
                        'message': 'La cita ya tenía ese estado',
                        'appointment': _serialize(old), 'idempotent': True}
            if old['operational_status'] == 'cancelled' and target != 'cancelled':
                return _result(NO_RESURRECTION,
                               'Una cita cancelada no se reactiva; cree una cita nueva')
            conflict = _version_conflict(old, expected_version)
            if conflict:
                return conflict
            cur.execute(
                """UPDATE appointments SET operational_status=%s,
                   row_version=row_version+1, updated_at=now() WHERE id=%s""",
                (target, appointment_id))
            _write_history(cur, appointment_id, 'correccion', actor,
                           {'before': {'status': old['operational_status']},
                            'after': {'status': target}}, reason)
            _audit(cur, actor, f'Corrección de cita {appointment_id} a {target}')
            saved = _load(cur, appointment_id)
    return {'ok': True, 'code': 'corrected', 'message': 'Estado corregido con historial',
            'appointment': _serialize(saved), 'idempotent': False}


def add_note(url, *, appointment_id, body, author):
    """Añade una observación interna con autor y entrada de historial."""
    if not isinstance(author, int) or isinstance(author, bool):
        return _result(FORBIDDEN, 'Sólo un usuario autenticado puede añadir observaciones')
    text = (body or '').strip()
    if not text:
        return _result(NOTE_REQUIRED, 'La observación no puede estar vacía')
    if len(text) > 2000:
        return _result(NOTE_REQUIRED, 'La observación no puede superar 2000 caracteres')
    with transaction(url) as conn:
        with conn.cursor() as cur:
            if not _load(cur, appointment_id):
                return _result(NOT_FOUND, 'Cita no encontrada')
            cur.execute(
                """INSERT INTO appointment_notes (appointment_id, author_user_id, body)
                   VALUES (%s, %s, %s) RETURNING *""",
                (appointment_id, author, text))
            note = cur.fetchone()
            _write_history(cur, appointment_id, 'nota', author, None, None,
                           note['id'])
            _audit(cur, author, f'Observación en cita {appointment_id}')
    return {'ok': True, 'code': 'note_created', 'message': 'Observación guardada',
            'note': row(note)}


def list_appointments(url, *, start_utc, end_utc, resource=None, status=None,
                      include_cancelled=False, branch_ids=None):
    """Citas que atraviesan [start_utc, end_utc), sin notas ni historial."""
    start = to_utc(start_utc, 'UTC') if isinstance(start_utc, str) else start_utc
    end = to_utc(end_utc, 'UTC') if isinstance(end_utc, str) else end_utc
    if end <= start:
        raise ValueError('Rango de agenda no válido')
    if (end - start) > timedelta(days=62):
        raise ValueError('El rango solicitado es demasiado amplio')
    if status and status not in OPERATIONAL_STATES:
        raise ValueError('Estado de filtro no válido')
    sql = ["""SELECT a.*, r.name AS resource_name, r.specialty AS resource_specialty,
                     c.full_name AS contact_name, c.phone AS contact_phone,
                     p.name AS service_name,
                     EXISTS(SELECT 1 FROM appointment_notes n
                            WHERE n.appointment_id = a.id) AS has_notes
              FROM appointments a
              JOIN resources r ON r.id = a.resource_id
              LEFT JOIN contacts c ON c.id = a.contact_id
              LEFT JOIN products p ON p.id = a.service_id
              WHERE a.start_utc < %s AND a.end_utc > %s"""]
    params = [end, start]
    if branch_ids is not None:
        if not branch_ids:
            return []
        marks = ', '.join(['%s'] * len(branch_ids))
        sql.append(f'AND a.branch_id IN ({marks})')
        params.extend(sorted(set(int(b) for b in branch_ids)))
    if resource not in (None, '', 'all'):
        sql.append('AND a.resource_id = %s')
        params.append(int(resource))
    if status:
        sql.append('AND a.operational_status = %s')
        params.append(status)
    if not include_cancelled and status != 'cancelled':
        sql.append("AND a.operational_status <> 'cancelled'")
    sql.append('ORDER BY a.start_utc, r.name LIMIT 1000')
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(' '.join(sql), params)
            rows = cur.fetchall()
    return [row(r) for r in rows]


def appointments_for_contact(url, *, contact_id, limit=50, branch_ids=None):
    """Historial de citas de un contacto (incluye canceladas).

    E01-R/A1: ``branch_ids`` acota a las sedes agenda.view del usuario; el
    perfil del contacto no revela citas de sedes ajenas (None = todas,
    director; lista vacía = ninguna).
    """
    sede = ''
    sede_params = []
    if branch_ids is not None:
        if not branch_ids:
            return []
        marks = ', '.join(['%s'] * len(branch_ids))
        sede = f' AND a.branch_id IN ({marks})'
        sede_params.extend(sorted(set(int(b) for b in branch_ids)))
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT a.*, r.name AS resource_name
                   FROM appointments a JOIN resources r ON r.id = a.resource_id
                   WHERE a.contact_id = %s{sede}
                   ORDER BY a.start_utc DESC LIMIT %s""",
                (contact_id, *sede_params, max(1, min(int(limit), 200))))
            return [row(r) for r in cur.fetchall()]


def list_resources(url, *, only_active=True):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM resources %s ORDER BY name' %
                        ('WHERE is_active' if only_active else ''))
            return [row(r) for r in cur.fetchall()]


def create_resource(url, *, name, specialty=None, is_active=True,
                    branch_id=1):
    """E01: todo recurso nace en una sede (Principal=1 por defecto)."""
    clean = (name or '').strip()[:120]
    if not clean:
        return {'ok': False, 'code': INVALID_TITLE, 'message': 'El nombre es obligatorio'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO resources (name, specialty, is_active, branch_id)
                   VALUES (%s, %s, %s, %s) RETURNING *""",
                (clean, (specialty or '').strip()[:120] or None, is_active,
                 branch_id))
            return {'ok': True, 'code': 'created', 'resource': row(cur.fetchone())}


def pending_closure(appt, clock=None):
    """Condición calculada: cita abierta cuyo fin ya pasó."""
    end = appt['end_utc']
    if isinstance(end, str):
        end = datetime.fromisoformat(end)
    return appt['operational_status'] in OPEN_STATES and _clock(clock) >= end


def allowed_actions(appt, role='user', clock=None):
    start = appt['start_utc']
    if isinstance(start, str):
        start = datetime.fromisoformat(start)
    current = _clock(clock)
    status = appt['operational_status']
    actions = []
    if status == 'cancelled':
        return actions
    if status in OPEN_STATES and current < start:
        actions.extend(['confirm', 'reprogram', 'cancel'])
    if pending_closure(appt, clock):
        actions.extend(['attend', 'no_show'])
    if role == 'admin':
        actions.append('admin_correct')
    return actions


def appointment_detail(url, *, appointment_id, role='user', clock=None):
    """Detalle autenticado con notas, historial y acciones permitidas."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT a.*, r.name AS resource_name,
                          r.specialty AS resource_specialty,
                          c.full_name AS contact_name, c.phone AS contact_phone,
                          c.email AS contact_email
                   FROM appointments a
                   JOIN resources r ON r.id = a.resource_id
                   LEFT JOIN contacts c ON c.id = a.contact_id
                   WHERE a.id = %s""", (appointment_id,))
            appt = cur.fetchone()
            if not appt:
                return _result(NOT_FOUND, 'Cita no encontrada')
            cur.execute(
                """SELECT n.*, u.full_name AS author_name FROM appointment_notes n
                   LEFT JOIN users u ON u.id = n.author_user_id
                   WHERE n.appointment_id = %s ORDER BY n.id""", (appointment_id,))
            notes = cur.fetchall()
            cur.execute(
                """SELECT h.*, u.full_name AS actor_name FROM appointment_history h
                   LEFT JOIN users u ON u.id = h.actor_user_id
                   WHERE h.appointment_id = %s ORDER BY h.id""", (appointment_id,))
            history = cur.fetchall()
    serialized = _serialize(appt)
    return {
        'ok': True,
        'appointment': serialized,
        'pending_closure': pending_closure(appt, clock),
        'allowed_actions': allowed_actions(appt, role, clock),
        'notes': [{'id': n['id'], 'body': n['body'],
                   'created_at': row(n)['created_at'],
                   'author': n['author_name'] or 'Sistema'} for n in notes],
        'history': [{'id': h['id'], 'action': h['action'],
                     'action_label': ACTION_LABELS.get(h['action'], h['action']),
                     'actor': h['actor_name'] or h['actor_label'] or 'Sistema',
                     'created_at': row(h)['created_at'], 'reason': h['reason'],
                     'detail': h['detail']} for h in history],
    }
