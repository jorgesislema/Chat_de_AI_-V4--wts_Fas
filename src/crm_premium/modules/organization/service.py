"""Organización: perfil único del negocio (nombre, zona, horario).

El perfil gobierna la zona IANA y la ventana de horario compartida por la web
y los canales (regla G01 de V3 conservada). ``opening_json`` vacío significa
atención 24×7 (sin restricción).
"""
from psycopg.types.json import Json

from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row
from ...shared.timeutil import InvalidZone, resolve_zone

INVALID_ZONE = 'invalid_zone'
INVALID_OPENING = 'invalid_opening'
NOT_FOUND = 'not_found'


def ensure(url, *, name='Mi Negocio', zone='UTC'):
    """Crea la fila única id=1 si no existe y la devuelve."""
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO organization (id, name, zone)
                   VALUES (1, %s, %s) ON CONFLICT (id) DO NOTHING""",
                (name, zone))
            cur.execute('SELECT * FROM organization WHERE id = 1')
            profile = row(cur.fetchone())
            from ..scope import service as scope_service
            scope_service.ensure_principal(url, zone=profile['zone'])
            return profile


def get(url):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM organization WHERE id = 1')
            profile = row(cur.fetchone())
            from ..scope import service as scope_service
            scope_service.ensure_principal(url, zone=profile['zone'])
            return profile


def update(url, *, name=None, zone=None, currency=None, opening=None):
    """Actualiza campos del perfil validando zona y horario."""
    current = get(url)
    if current is None:
        return {'ok': False, 'code': NOT_FOUND, 'message': 'Perfil inexistente'}
    new_zone = zone or current['zone']
    try:
        resolve_zone(new_zone)
    except InvalidZone as exc:
        return {'ok': False, 'code': INVALID_ZONE, 'message': str(exc)}
    if opening is not None and opening and not _opening_valid(opening):
        return {'ok': False, 'code': INVALID_OPENING,
                'message': 'Horario no válido: use días 0-6 y horas HH:MM'}
    # opening == {} limpia el horario (atención 24×7).
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE organization
                   SET name=%s, zone=%s, currency=%s,
                       opening_json=%s, updated_at=now()
                   WHERE id=1 RETURNING *""",
                ((name or current['name']).strip()[:120],
                 new_zone,
                 (currency or current['currency']).strip()[:8],
                 Json(opening) if opening is not None else Json(current['opening_json'])))
            return {'ok': True, 'code': 'updated', 'profile': row(cur.fetchone())}


def _opening_valid(opening):
    if not isinstance(opening, dict):
        return False
    days = opening.get('days')
    start = opening.get('start')
    end = opening.get('end')
    if start is None or end is None or days is None:
        return False
    if not isinstance(days, list) or not days:
        return False
    if not all(isinstance(d, int) and 0 <= d <= 6 for d in days):
        return False
    for value in (start, end):
        parts = str(value).split(':')
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            return False
        if not (0 <= int(parts[0]) <= 23 and 0 <= int(parts[1]) <= 59):
            return False
    return str(end) > str(start)


def build_window_policy(profile):
    """Callable(start_utc, end_utc) -> motivo|None según el horario del perfil.

    CORR01/R03: valida el intervalo completo, no sólo los extremos. Para cada
    fecha local que el intervalo toca, el fragmento de ese día debe estar
    vacío o completamente dentro de [apertura, cierre] en un día permitido.
    El cierre exacto se permite (intervalo semiabierto al segundo); un fin
    aunque sea un segundo después del cierre se rechaza. ``opening`` vacío =
    24×7 (sin política).
    """
    opening = profile.get('opening_json') if profile else None
    if not opening or not isinstance(opening, dict):
        return None
    try:
        zone = resolve_zone(profile['zone'])
    except (InvalidZone, KeyError):
        return None
    days = tuple(opening.get('days') or ())
    open_h, open_m = (int(p) for p in opening['start'].split(':'))
    close_h, close_m = (int(p) for p in opening['end'].split(':'))

    def policy(start_utc, end_utc):
        from datetime import date as _date, timedelta as _td
        from ...shared.timeutil import to_utc as _to_utc

        first_day = start_utc.astimezone(zone).date()
        last_day = end_utc.astimezone(zone).date()
        cursor = first_day
        while cursor <= last_day:
            next_day = cursor + _td(days=1)
            midnight = _to_utc(f'{cursor.isoformat()}T00:00:00', profile['zone'])
            next_midnight = _to_utc(f'{next_day.isoformat()}T00:00:00',
                                    profile['zone'])
            portion_start = max(start_utc, midnight)
            portion_end = min(end_utc, next_midnight)
            if portion_start < portion_end:  # el intervalo toca este día
                if cursor.weekday() not in days:
                    return ('La cita atraviesa el '
                            f'{cursor.isoformat()}, fuera del horario de atención')
                try:
                    day_open = _to_utc(
                        f"{cursor.isoformat()}T{open_h:02d}:{open_m:02d}:00",
                        profile['zone'])
                    day_close = _to_utc(
                        f"{cursor.isoformat()}T{close_h:02d}:{close_m:02d}:00",
                        profile['zone'])
                except ValueError:
                    return ('El horario configurado cae en una hora local '
                            'inexistente por cambio estacional; revise Ajustes')
                if portion_start < day_open or portion_end > day_close:
                    return (f'La cita queda fuera del horario de atención del '
                            f'{cursor.isoformat()}')
            cursor = next_day
        return None

    return policy
