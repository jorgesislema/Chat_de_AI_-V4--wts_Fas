"""Indicadores del panel ejecutivo (núcleo).

Consultas agregadas directas sobre el operacional PostgreSQL, en la zona del
negocio. La capa estrella/ETL del expediente sustituirá estas consultas en su
fase; por ahora alimentan los gráficos del dashboard con datos reales.
"""
from datetime import date, datetime, timedelta, timezone

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row
from ...shared.timeutil import SPANISH_MONTHS, resolve_zone, to_utc

STATUS_LABELS = {
    'pending': 'Pendiente',
    'confirmed': 'Confirmada',
    'attended': 'Atendida',
    'no_show': 'No asistió',
    'cancelled': 'Cancelada',
}


def _clock(clock=None):
    current = clock or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current


def _local_day_bounds(zone, day):
    """[inicio, fin) del día local en UTC (tolera DST con to_utc)."""
    start = to_utc(f'{day.isoformat()}T00:00:00', zone)
    end = to_utc(f'{(day + timedelta(days=1)).isoformat()}T00:00:00', zone)
    return start, end


def summary(url, *, zone, clock=None, appointment_branch_ids=None):
    """KPIs del día, semana y 30 días + series para los gráficos.

    E01-R/A2: ``appointment_branch_ids`` acota TODAS las consultas de citas a
    las sedes autorizadas para agenda.view (None = todas, director; lista
    vacía = cero datos, nunca el agregado global).
    """
    tz = resolve_zone(zone)
    now = _clock(clock)
    today = now.astimezone(tz).date()
    day_start, day_end = _local_day_bounds(zone, today)
    week_monday = today - timedelta(days=today.weekday())
    week_start, week_end = _local_day_bounds(zone, week_monday + timedelta(days=7))
    range30_start, _ = _local_day_bounds(zone, today - timedelta(days=29))
    series_start, _ = _local_day_bounds(zone, today - timedelta(days=13))
    range30_end = day_end

    sede = ''
    sede_params = []
    if appointment_branch_ids is not None:
        if not appointment_branch_ids:
            appointment_branch_ids = [-1]
        marks = ', '.join(['%s'] * len(appointment_branch_ids))
        sede = (f' AND branch_id IN ({marks})')
        sede_params.extend(sorted(set(int(b) for b in appointment_branch_ids)))

    def _sede(table_alias=''):
        return sede.replace('branch_id', f'{table_alias}branch_id') if table_alias \
            else sede

    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT operational_status, count(*) AS n FROM appointments
                   WHERE start_utc >= %s AND start_utc < %s{sede}
                   GROUP BY operational_status""",
                (day_start, day_end, *sede_params))
            today_counts = {r['operational_status']: r['n'] for r in cur.fetchall()}

            cur.execute(
                f"""SELECT count(*) AS n FROM appointments
                   WHERE start_utc >= %s AND start_utc < %s
                     AND operational_status <> 'cancelled'{sede}""",
                (week_start, week_end, *sede_params))
            week_total = cur.fetchone()['n']

            cur.execute(
                f"""SELECT ((start_utc AT TIME ZONE %s)::date) AS day, count(*) AS n
                   FROM appointments
                   WHERE start_utc >= %s AND start_utc < %s
                     AND operational_status <> 'cancelled'{sede}
                   GROUP BY 1""",
                (zone, series_start, day_end, *sede_params))
            per_day_raw = {r['day']: r['n'] for r in cur.fetchall()}

            cur.execute(
                f"""SELECT r.name, count(*) AS n
                   FROM appointments a JOIN resources r ON r.id = a.resource_id
                   WHERE a.start_utc >= %s AND a.start_utc < %s
                     AND a.operational_status <> 'cancelled'{_sede('a.')}
                   GROUP BY r.name ORDER BY n DESC, r.name LIMIT 8""",
                (week_start, week_end, *sede_params))
            by_resource = [{'label': r['name'], 'value': r['n']} for r in cur.fetchall()]

            cur.execute(
                f"""SELECT operational_status, count(*) AS n FROM appointments
                   WHERE start_utc >= %s AND start_utc < %s{sede}
                   GROUP BY operational_status""",
                (range30_start, day_end, *sede_params))
            by_status_raw = {r['operational_status']: r['n'] for r in cur.fetchall()}

            cur.execute(
                f"""SELECT a.id, a.title, a.start_utc, a.end_utc, a.operational_status,
                          r.name AS resource_name, c.full_name AS contact_name
                   FROM appointments a
                   JOIN resources r ON r.id = a.resource_id
                   LEFT JOIN contacts c ON c.id = a.contact_id
                   WHERE a.start_utc >= %s AND a.operational_status IN ('pending','confirmed')
                     {_sede('a.')}
                   ORDER BY a.start_utc LIMIT 8""",
                (now, *sede_params))
            upcoming = []
            for r in cur.fetchall():
                data = row(r)
                local_start = r['start_utc'].astimezone(tz)
                data['start_local'] = (f"{local_start.day} "
                                       f"{SPANISH_MONTHS[local_start.month - 1]} "
                                       f"{local_start.hour:02d}:{local_start.minute:02d}")
                upcoming.append(data)

            cur.execute(
                f"""SELECT count(*) AS total,
                          count(*) FILTER (WHERE operational_status = 'pending'
                               AND end_utc < %s) AS pending_closure
                   FROM appointments WHERE operational_status <> 'cancelled'{sede}""",
                (now, *sede_params))
            totals = cur.fetchone()

            cur.execute('SELECT count(*) AS n FROM contacts')
            contacts_total = cur.fetchone()['n']

            cur.execute(
                f"""SELECT count(*) FILTER (WHERE operational_status='attended') AS attended,
                          count(*) FILTER (WHERE operational_status='no_show') AS no_show
                   FROM appointments WHERE start_utc >= %s AND start_utc < %s{sede}""",
                (range30_start, range30_end, *sede_params))
            att = cur.fetchone()

    days = []
    cursor_day = today - timedelta(days=13)
    while cursor_day <= today:
        days.append({'day': cursor_day.isoformat(),
                     'value': int(per_day_raw.get(cursor_day, 0))})
        cursor_day += timedelta(days=1)

    attended = att['attended']
    closed = attended + att['no_show']
    return {
        'generated_at': now.isoformat(),
        'zone': zone,
        'today': today.isoformat(),
        'today_counts': {status: int(today_counts.get(status, 0))
                         for status in STATUS_LABELS},
        'week_total': week_total,
        'per_day': days,
        'by_resource': by_resource,
        'by_status_30d': [{'label': STATUS_LABELS[status], 'key': status,
                           'value': int(by_status_raw.get(status, 0))}
                          for status in STATUS_LABELS],
        'upcoming': upcoming,
        'open_total': totals['total'],
        'pending_closure': totals['pending_closure'],
        'contacts_total': contacts_total,
        'attendance_rate': round(attended / closed, 4) if closed else None,
    }
