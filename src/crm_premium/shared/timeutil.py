"""Tiempo compartido: zona IANA, DST y rangos visibles de la agenda.

Puerto controlado de crm/agenda_time.py y de la resolución de horas locales de
crm/reservation_service.py (V3). Funciones puras sin Flask ni SQL: el servidor
decide zona y rangos; el navegador nunca elige zona horaria.
"""
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

MAX_DAYS = 62


class InvalidZone(ValueError):
    """La zona IANA indicada no existe."""


class NonexistentLocalTime(ValueError):
    """Hora local que no existe por el salto estacional (DST)."""


class AmbiguousLocalTime(ValueError):
    """Hora local que ocurre dos veces por el cambio estacional (DST)."""


def resolve_zone(zone):
    try:
        return ZoneInfo(zone)
    except Exception as exc:
        raise InvalidZone(f'Zona horaria no válida: {zone}. Use una zona IANA.') from exc


def _resolve_local(dt, tz):
    """Resuelve una hora local sin offset detectando huecos y ambigüedades.

    - Ninguna de las dos lecturas (fold 0/1) vuelve a la misma hora de pared:
      la hora no existe por el salto de primavera.
    - Ambas lecturas válidas con offsets distintos: hora ambigua; exige offset.
    """
    first = dt.replace(tzinfo=tz, fold=0)
    second = dt.replace(tzinfo=tz, fold=1)

    def round_trip_ok(candidate):
        return (candidate.astimezone(timezone.utc).astimezone(tz)
                .replace(tzinfo=None) == dt)

    first_ok = round_trip_ok(first)
    second_ok = round_trip_ok(second)
    if not first_ok and not second_ok:
        raise NonexistentLocalTime(
            'La hora local no existe por el cambio estacional; elija otra hora '
            'o indique un offset explícito (por ejemplo -05:00).')
    if first_ok and second_ok and first.utcoffset() != second.utcoffset():
        raise AmbiguousLocalTime(
            'La hora local es ambigua por el cambio estacional; indique un offset '
            'explícito (por ejemplo +01:00) para elegir la ocurrencia.')
    return first if first_ok else second


def to_utc(value, zone):
    """Convierte un ISO string o datetime a UTC usando la zona IANA indicada.

    Acepta cadenas sin offset (se interpretan en ``zone``) y con offset o ``Z``
    (se respeta y se normaliza a UTC). Rechaza horas locales inexistentes o
    ambiguas por DST cuando no traen offset explícito.
    """
    tz = resolve_zone(zone)
    if isinstance(value, datetime):
        dt = value
    else:
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Fecha no válida')
        dt = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    return _resolve_local(dt, tz).astimezone(timezone.utc)


def parse_date(value):
    try:
        return date.fromisoformat((value or '').strip())
    except (TypeError, ValueError) as exc:
        raise ValueError('Indique una fecha válida (AAAA-MM-DD)') from exc


def _midnight(day, tz):
    return datetime.combine(day, time(0, 0), tzinfo=tz)


def _range(first, last, tz, view):
    if last < first:
        raise ValueError('Rango de agenda no válido')
    if (last - first).days + 1 > MAX_DAYS:
        raise ValueError('El rango solicitado es demasiado amplio')
    start = _midnight(first, tz)
    end = _midnight(last + timedelta(days=1), tz)
    days = []
    cursor = first
    while cursor <= last:
        days.append({
            'date': cursor.isoformat(),
            'weekday': cursor.weekday(),
            'start_utc': _midnight(cursor, tz).astimezone(timezone.utc).isoformat(),
            'end_utc': (_midnight(cursor + timedelta(days=1), tz)
                        .astimezone(timezone.utc)).isoformat(),
        })
        cursor += timedelta(days=1)
    return {
        'view': view,
        'start_date': first.isoformat(),
        'end_date': last.isoformat(),
        'start_utc': start.astimezone(timezone.utc).isoformat(),
        'end_utc': end.astimezone(timezone.utc).isoformat(),
        'days': days,
    }


def view_range(view, value, zone):
    """Devuelve el rango UTC y días para ``day``/``week``/``month``."""
    tz = resolve_zone(zone)
    day = parse_date(value)
    if view == 'day':
        return _range(day, day, tz, view)
    if view == 'week':
        first = day - timedelta(days=day.weekday())
        return _range(first, first + timedelta(days=6), tz, view)
    if view == 'month':
        first_month = day.replace(day=1)
        grid_start = first_month - timedelta(days=first_month.weekday())
        next_month = (first_month.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day = next_month - timedelta(days=1)
        grid_end = last_day + timedelta(days=(6 - last_day.weekday()))
        # Rejilla estable de 6 semanas para evitar saltos de altura al navegar.
        if (grid_end - grid_start).days + 1 < 42:
            grid_end = grid_start + timedelta(days=41)
        return _range(grid_start, grid_end, tz, view)
    raise ValueError('Vista no válida: use day, week o month')


def local_parts(value, zone):
    """Descompone un instante UTC en fecha/hora locales (respuestas API)."""
    if isinstance(value, str):
        dt = datetime.fromisoformat(value)
    else:
        dt = value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    local = dt.astimezone(resolve_zone(zone))
    return {
        'date': local.date().isoformat(),
        'time': local.strftime('%H:%M'),
        'iso': local.isoformat(),
    }


SPANISH_MONTHS = ('ene', 'feb', 'mar', 'abr', 'may', 'jun',
                  'jul', 'ago', 'sep', 'oct', 'nov', 'dic')
WEEKDAY_LABELS = ('lun', 'mar', 'mié', 'jue', 'vie', 'sáb', 'dom')


def period_label(rng):
    """Etiqueta legible del período visible (sin depender del navegador)."""
    start = date.fromisoformat(rng['start_date'])
    end = date.fromisoformat(rng['end_date'])
    if rng['view'] == 'month':
        # La rejilla de 6 semanas arranca en el mes anterior: el mes mostrado
        # es el del ancla, ~2 semanas dentro de la rejilla.
        anchor = start + timedelta(days=14)
        return f"{SPANISH_MONTHS[anchor.month - 1]} {anchor.year}"
    if rng['view'] == 'day':
        return f"{start.day} {SPANISH_MONTHS[start.month - 1]} {start.year}"
    if start.month == end.month:
        return f"{start.day}–{end.day} {SPANISH_MONTHS[start.month - 1]} {start.year}"
    return (f"{start.day} {SPANISH_MONTHS[start.month - 1]} – "
            f"{end.day} {SPANISH_MONTHS[end.month - 1]} {end.year}")
