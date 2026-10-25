"""Fixtures de pruebas — PostgreSQL temporal por sesión (CORR01/R09).

Reglas:
- Opt-in explícito: sólo se ejecuta contra ``CRM_PREMIUM_TEST_URL``. Nunca
  lee ``.env`` ni usa ``DATABASE_URL`` del entorno como fallback: importar
  conftest no puede tocar el servidor operativo del propietario.
- DSN compuesto con ``urllib.parse`` (tolera parámetros y formatos).
- Limpieza en ``finally`` aunque fallen las migraciones.
- Datos exclusivamente sintéticos.
"""
import os
import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import psycopg
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'src'))

TEST_DSN_ENV = 'CRM_PREMIUM_TEST_URL'

# CORR01C/B1: las utilidades de DSN viven en el paquete para estar
# disponibles también en instalaciones wheel fuera del checkout.
from crm_premium.shared.testdsns import (  # noqa: E402,F401
    ALLOWED_QUERY_KEYS, DSNConfigError, FORBIDDEN_QUERY_KEYS,
    parse_test_dsn, temporal_dsn, verify_target_database)


def _admin_and_base_urls():
    raw = os.environ.get(TEST_DSN_ENV)
    if not raw:
        pytest.exit(
            f'[R09] Defina {TEST_DSN_ENV} apuntando a un servidor de pruebas '
            f'aislado (p. ej. el contenedor dedicado). Por seguridad, la suite '
            f'no usa .env ni DATABASE_URL, y no ejecuta contra el servidor '
            f'operativo sin opt-in explícito.', returncode=4)
    try:
        admin, parts, options = parse_test_dsn(raw)
    except DSNConfigError as exc:
        pytest.exit(f'[R09/CORR01C] {exc}', returncode=4)
    return admin, parts, options


@pytest.fixture(scope='session')
def db_url():
    admin_url, parts, options = _admin_and_base_urls()
    name = f'crm_premium_test_{secrets.token_hex(6)}'
    admin = psycopg.connect(admin_url, autocommit=True)
    with admin.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{name}"')
    admin.close()

    # CORR01C/C2: misma derivación probada (codificación %XX consistente).
    test_dsn = temporal_dsn(parts, options, name)
    from crm_premium.infrastructure.persistence.migrations import apply_all
    try:
        guard = psycopg.connect(test_dsn, autocommit=True,
                                row_factory=psycopg.rows.dict_row)
        verify_target_database(guard, name)
        guard.close()
        apply_all(test_dsn)
        yield test_dsn
    finally:
        admin = psycopg.connect(admin_url, autocommit=True)
        try:
            with admin.cursor() as cur:
                cur.execute(
                    """SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                       WHERE datname = %s AND pid <> pg_backend_pid()""", (name,))
                cur.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        finally:
            admin.close()


@pytest.fixture(autouse=True)
def _clean_commerce_between_tests(db_url):
    """Aislamiento (CORR01): las tablas de comercio/BI/asistente se limpian
    tras cada prueba. CORR01C/B1: verifica la base efectiva ANTES del
    TRUNCATE en una conexión autocommit propia (un SELECT previo sobre una
    conexión autocommit=False abriría una transacción externa y convertiría
    el transaction() en savepoint: el TRUNCATE se revertiría al cerrar)."""
    yield
    expected = urlsplit(db_url).path.lstrip('/')
    guard = psycopg.connect(db_url, autocommit=True,
                            row_factory=psycopg.rows.dict_row)
    try:
        verify_target_database(guard, expected)
    finally:
        guard.close()
    from crm_premium.infrastructure.persistence.db import transaction
    with transaction(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """TRUNCATE bi.fact_venta_linea, bi.fact_cita, bi.dim_contacto,
                       bi.dim_producto, bi.dim_recurso, bi.dim_estado, bi.dim_hora,
                       bi.dim_fecha, bi.meta,
                       sale_lines, sales, stock_movements, product_price_history,
                       products, assistant_log, knowledge_docs
                   RESTART IDENTITY CASCADE""")


@pytest.fixture(scope='session')
def org(db_url):
    from crm_premium.modules.organization import service as organization
    return organization.ensure(db_url, name='Negocio de prueba', zone='UTC')


@pytest.fixture(scope='session')
def admin_user(db_url):
    from crm_premium.modules.identity import service as identity
    result = identity.create_user(db_url, username='admin_test',
                                  password='ClaveLarga.2026',
                                  full_name='Admin de prueba', role='admin')
    assert result['ok'], result
    return result['user']


@pytest.fixture()
def plain_user(db_url):
    """Usuario sin privilegios de administración (CORR01/R04/R05)."""
    from crm_premium.modules.identity import service as identity
    import secrets as _secrets
    result = identity.create_user(db_url,
                                  username=f'user_{_secrets.token_hex(4)}',
                                  password='ClaveLarga.2026',
                                  full_name='Usuario de prueba', role='user')
    assert result['ok'], result
    return result['user']


@pytest.fixture()
def client(db_url, org, admin_user):
    """Cliente web autenticado como administrador con CSRF resuelto."""
    from crm_premium.entrypoints.web.app import create_app
    app = create_app(db_url=db_url)
    app.config['testing'] = True
    with app.test_client() as test_client:
        login_page = test_client.get('/login')
        assert login_page.status_code == 200
        token = login_page.data.decode('utf-8').split('name="csrf_token" value="')[1] \
            .split('"')[0]
        response = test_client.post('/login', data={
            'username': 'admin_test', 'password': 'ClaveLarga.2026',
            'csrf_token': token})
        assert response.status_code == 302, response.data
        page = test_client.get('/').data.decode('utf-8')
        csrf = page.split('name="csrf-token" content="')[1].split('"')[0]
        test_client.csrf = csrf
        yield test_client


def login_as(db_url, test_client, username, password='ClaveLarga.2026'):
    """Login de un usuario arbitrario sobre un cliente limpio (CORR01)."""
    page = test_client.get('/login')
    token = page.data.decode('utf-8').split('name="csrf_token" value="')[1] \
        .split('"')[0]
    response = test_client.post('/login', data={
        'username': username, 'password': password, 'csrf_token': token})
    assert response.status_code == 302, response.data
    html = test_client.get('/').data.decode('utf-8')
    csrf = html.split('name="csrf-token" content="')[1].split('"')[0]
    test_client.csrf = csrf
    return test_client


@pytest.fixture()
def resource(db_url):
    from crm_premium.modules.scheduling import service as scheduling
    result = scheduling.create_resource(db_url, name='Profesional Uno',
                                        specialty='General')
    assert result['ok']
    return result['resource']


@pytest.fixture()
def contact(db_url):
    from crm_premium.modules.contacts import service as contacts
    result = contacts.create(db_url, full_name='Cliente Prueba',
                             phone='+593900000000')
    assert result['ok']
    return result['contact']
