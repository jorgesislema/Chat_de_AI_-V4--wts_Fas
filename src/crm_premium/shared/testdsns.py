"""Utilidades de DSN para pruebas y smokes (CORR01C/B1).

Viven en el paquete para que la verificación de aislamiento esté disponible
también en instalaciones wheel fuera del checkout (scripts/dev/smoke_packaging).
tests/conftest.py re-exporta estas definiciones.
"""
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


class DSNConfigError(ValueError):
    """DSN de pruebas no soportado. El mensaje nunca incluye el secreto."""


#: CORR01C/B1: claves de identidad/destino prohibidas en la query — libpq
#: permitiría que sustituyan el destino derivado del path y la suite podría
#: operar una base ajena. Se rechazan siempre.
FORBIDDEN_QUERY_KEYS = {'dbname', 'database', 'host', 'hostaddr', 'port',
                        'user', 'password', 'passfile', 'service', 'options'}

#: CORR01C/B1: únicas opciones de query admitidas (TLS, timeouts, telemetría).
ALLOWED_QUERY_KEYS = {'sslmode', 'sslcert', 'sslkey', 'sslrootcert', 'sslcrl',
                      'sslpassword', 'sslnegotiation', 'gssencmode',
                      'connect_timeout', 'tcp_user_timeout', 'keepalives',
                      'keepalives_idle', 'keepalives_interval',
                      'keepalives_count', 'application_name',
                      'target_session_attrs'}


def parse_test_dsn(raw):
    """Valida la URL de pruebas y deriva (admin, partes, opciones).

    - Sólo formato URL ``postgresql://user:pass@host:puerto/base``; conninfo
      «palabra=valor» se rechaza explícitamente.
    - La query admite ÚNICAMENTE claves de la lista blanca (TLS, timeouts,
      application_name, target_session_attrs). Cualquier clave de identidad o
      destino (dbname/host/user/password/service/options…) o desconocida se
      rechaza ANTES de abrir conexión. Claves duplicadas se rechazan.
    - Devuelve (dsn_admin_con_mismas_opciones, urlsplit_parts, opciones).
    """
    parts = urlsplit(raw)
    if parts.scheme not in ('postgresql', 'postgres') or not parts.netloc:
        raise DSNConfigError(
            'CRM_PREMIUM_TEST_URL debe ser una URL postgresql://user:pass@host'
            ':puerto/base. El formato conninfo palabra=valor no está soportado.')
    if not parts.username or parts.password is None:
        raise DSNConfigError(
            'CRM_PREMIUM_TEST_URL debe incluir usuario y contraseña de prueba '
            'en la propia URL (user:pass@host).')
    if not parts.path or parts.path == '/':
        raise DSNConfigError(
            'CRM_PREMIUM_TEST_URL debe indicar una base (p. ej. /postgres).')

    seen = {}
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key = key.lower()
        if key in seen:
            raise DSNConfigError(
                f'Parámetro de query duplicado: {key!r}. Corrija la URL.')
        if key in FORBIDDEN_QUERY_KEYS:
            raise DSNConfigError(
                f'Parámetro de query no permitido: {key!r} puede sustituir la '
                'identidad/destino derivada del path y romper el aislamiento.')
        if key not in ALLOWED_QUERY_KEYS:
            raise DSNConfigError(
                f'Parámetro de query no reconocido: {key!r}. Sólo se admiten '
                'opciones TLS/timeout/application_name/target_session_attrs.')
        seen[key] = value
    # quote_via=quote → %20 (libpq URL decodifica %XX, no '+' de form-urlencode).
    admin = temporal_dsn(parts, seen, 'postgres')
    return admin, parts, seen


def temporal_dsn(parts, options, dbname):
    """CORR01C/C2: derivación ÚNICA de DSN temporal/admin con codificación
    URI consistente (%XX vía quote; nunca '+' de form-urlencode, que libpq
    interpreta literal). Fixture, pruebas y smoke usan este mismo camino."""
    clean_query = urlencode(options, quote_via=quote)
    return urlunsplit((parts.scheme, parts.netloc, f'/{dbname}', clean_query, ''))


def verify_target_database(conn, expected_name):
    """Guarda anti-destino-erróneo antes de operaciones destructivas:
    compara current_database() con el nombre temporal EXACTO esperado
    (ambos son nombres de base, sin secretos)."""
    with conn.cursor() as cur:
        cur.execute('SELECT current_database() AS db')
        actual = cur.fetchone()['db']
    if actual != expected_name:
        raise RuntimeError(
            f'Aislamiento violado: la conexión apunta a {actual!r}, se '
            f'esperaba {expected_name!r}. Operación destructiva abortada.')
