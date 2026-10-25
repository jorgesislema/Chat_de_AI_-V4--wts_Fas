"""Contactos: personas y organizaciones del negocio (Clientes 360, fase núcleo)."""
from ...infrastructure.persistence.db import transaction
from ...shared.serialize import row

INVALID_NAME = 'invalid_name'
NOT_FOUND = 'not_found'


def _clean(value, limit=None):
    text = (value or '').strip()
    return text[:limit] if limit else text


def create(url, *, full_name, phone=None, email=None, notes=None, channel=None):
    name = _clean(full_name, 160)
    if not name:
        return {'ok': False, 'code': INVALID_NAME, 'message': 'El nombre es obligatorio'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO contacts (full_name, phone, email, notes, channel)
                   VALUES (%s, %s, %s, %s, %s) RETURNING *""",
                (name, _clean(phone, 40) or None, _clean(email, 120) or None,
                 _clean(notes, 2000) or None, _clean(channel, 20) or None))
            return {'ok': True, 'code': 'created', 'contact': row(cur.fetchone())}


def update(url, *, contact_id, full_name, phone=None, email=None, notes=None):
    name = _clean(full_name, 160)
    if not name:
        return {'ok': False, 'code': INVALID_NAME, 'message': 'El nombre es obligatorio'}
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE contacts SET full_name=%s, phone=%s, email=%s, notes=%s,
                   updated_at=now() WHERE id=%s RETURNING *""",
                (name, _clean(phone, 40) or None, _clean(email, 120) or None,
                 _clean(notes, 2000) or None, contact_id))
            saved = cur.fetchone()
            if not saved:
                return {'ok': False, 'code': NOT_FOUND, 'message': 'Contacto no encontrado'}
            return {'ok': True, 'code': 'updated', 'contact': row(saved)}


def get(url, contact_id):
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT * FROM contacts WHERE id = %s', (contact_id,))
            return row(cur.fetchone())


def list_contacts(url, *, q='', limit=50, offset=0):
    """Búsqueda por nombre/teléfono/correo con paginación."""
    limit = max(1, min(int(limit or 50), 200))
    offset = max(0, int(offset or 0))
    pattern = f'%{_clean(q, 80).lower()}%'
    with transaction(url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.*, (
                       SELECT count(*) FROM appointments a
                       WHERE a.contact_id = c.id AND a.operational_status <> 'cancelled'
                   ) AS appointment_count
                   FROM contacts c
                   WHERE (%s = '%%' OR lower(c.full_name) LIKE %s
                          OR lower(coalesce(c.phone,'')) LIKE %s
                          OR lower(coalesce(c.email,'')) LIKE %s)
                   ORDER BY c.full_name LIMIT %s OFFSET %s""",
                (pattern, pattern, pattern, pattern, limit, offset))
            rows = cur.fetchall()
            cur.execute('SELECT count(*) AS total FROM contacts '
                        'WHERE (%s = %s OR lower(full_name) LIKE %s)',
                        (pattern, pattern, pattern))
            total = cur.fetchone()['total']
    return {'items': [row(r) for r in rows], 'total': total,
            'limit': limit, 'offset': offset}
