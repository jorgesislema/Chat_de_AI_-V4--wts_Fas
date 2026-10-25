"""CORR01C: cierre B1 (aislamiento DSN), B2 (redacción de evidencia) y
B3 (ruptura con escritura válida previa + huella completa de bi)."""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from conftest import DSNConfigError, parse_test_dsn, verify_target_database
from crm_premium.infrastructure.persistence.migrations import (
    MIGRATIONS_DIR, apply_all)
from crm_premium.modules.analytics import service as analytics
from crm_premium.modules.commerce import service as commerce

SECRET = 'CONTRASENA-DE-PRUEBA-NO-REAL'


def _derived(url, temp_name):
    """CORR01D/C2: usa la derivación ÚNICA del paquete (idéntica al fixture
    y al smoke) para que las pruebas midan el camino real."""
    admin, parts, options = parse_test_dsn(url)
    from crm_premium.shared.testdsns import temporal_dsn
    temporal = temporal_dsn(parts, options, temp_name)
    return admin, temporal, options


# ---------------------------------------------------------------- B1: DSN

def test_b1_dbname_en_query_se_rechaza_antes_de_conectar():
    raw = (f'postgresql://fixture:{SECRET}@invalid:5433/postgres'
           '?sslmode=verify-full&dbname=synthetic_wrong_target')
    with pytest.raises(DSNConfigError) as exc:
        parse_test_dsn(raw)
    assert 'dbname' in str(exc.value)
    assert SECRET not in str(exc.value)


def test_b1_host_user_service_options_en_query_se_rechazan():
    for key, value in (('host', 'evil.example'), ('hostaddr', '10.0.0.9'),
                       ('port', '5434'), ('user', 'otro'),
                       ('password', 'otra'), ('service', 'prod'),
                       ('options', '-c search_path=hack')):
        raw = f'postgresql://fixture:{SECRET}@invalid:5433/postgres?{key}={value}'
        with pytest.raises(DSNConfigError) as exc:
            parse_test_dsn(raw)
        assert 'no permitido' in str(exc.value)
        assert SECRET not in str(exc.value)


def test_b1_duplicados_y_clave_desconocida_se_rechazan():
    base = f'postgresql://fixture:{SECRET}@invalid:5433/postgres'
    with pytest.raises(DSNConfigError):
        parse_test_dsn(base + '?sslmode=require&sslmode=verify-full')
    with pytest.raises(DSNConfigError):
        parse_test_dsn(base + '?sslmagic=1')


def test_b1_valida_preserva_tls_timeout_y_destino_efectivo():
    raw = (f'postgresql://fixture:{SECRET}@db.example:5433/postgres'
           '?sslmode=verify-full&connect_timeout=2'
           '&application_name=crm%20tests&keepalives_idle=30')
    admin, temporal, options = _derived(raw, 'crm_premium_test_abc123')
    # Destino efectivo verificado con el parser libpq (sin conexión):
    assert conninfo_to_dict(admin)['dbname'] == 'postgres'
    assert conninfo_to_dict(admin)['host'] == 'db.example'
    assert conninfo_to_dict(admin)['sslmode'] == 'verify-full'
    assert conninfo_to_dict(admin)['connect_timeout'] == '2'
    assert conninfo_to_dict(admin)['application_name'] == 'crm tests'
    effective = conninfo_to_dict(temporal)
    assert effective['dbname'] == 'crm_premium_test_abc123'
    assert effective['sslmode'] == 'verify-full'
    assert effective['keepalives_idle'] == '30'
    # Ninguna clave prohibida sobrevive en el diccionario efectivo.
    for forbidden in ('dbname_override', 'service'):
        assert forbidden not in effective


def test_b1_conninfo_no_soportado_y_sin_credenciales_rechazados():
    with pytest.raises(DSNConfigError) as conninfo_exc:
        parse_test_dsn(f'host=servidor user=u password={SECRET} dbname=db')
    assert SECRET not in str(conninfo_exc.value)
    with pytest.raises(DSNConfigError):
        parse_test_dsn('postgresql://invalid:5433/postgres')  # sin usuario
    with pytest.raises(DSNConfigError):
        parse_test_dsn(f'postgresql://u:{SECRET}@invalid:5433')  # sin base


def test_b1_guarda_de_base_efectiva_antes_de_operaciones(db_url):
    """La guarda compara current_database() con el nombre temporal EXACTO;
    un nombre distinto aborta sin ejecutar nada destructivo."""
    correct = urlsplit_name(db_url)
    conn = psycopg.connect(db_url, autocommit=True, row_factory=dict_row)
    try:
        verify_target_database(conn, correct)  # pasa: es la base exacta
        with pytest.raises(RuntimeError) as exc:
            verify_target_database(conn, 'crm_premium_test_otra')
        assert 'Aislamiento violado' in str(exc.value)
    finally:
        conn.close()


def urlsplit_name(db_url):
    from urllib.parse import urlsplit
    return urlsplit(db_url).path.lstrip('/')


# ------------------------------------------------- B3: ruptura con escritura

BI_TABLES = ('bi.fact_venta_linea', 'bi.fact_cita', 'bi.dim_fecha',
             'bi.dim_hora', 'bi.dim_producto', 'bi.dim_contacto',
             'bi.dim_recurso', 'bi.dim_estado', 'bi.meta')


def _stable_payload(rows):
    """Serialización estable: orden de filas irrelevante, claves ordenadas."""
    normalized = sorted(json.dumps(r, sort_keys=True, default=str)
                        for r in rows)
    return json.dumps(normalized)


def _fingerprint_bi(url):
    """CORR01D/C1: huella de contenido de las NUEVE tablas afectadas por el
    ETL — cálculo dentro del bucle, conjunto exacto de claves y orden de
    filas irrelevante para la comparación."""
    out = {}
    with psycopg.connect(url, autocommit=True, row_factory=dict_row) as conn:
        for table in BI_TABLES:
            with conn.cursor() as cur:
                cur.execute(f'SELECT * FROM {table}')
                rows = cur.fetchall()
            out[table] = hashlib.sha256(
                _stable_payload(rows).encode('utf-8')).hexdigest()[:16]
    assert set(out) == set(BI_TABLES), 'la huella debe cubrir las 9 tablas'
    return out


def test_b3_migracion_escritura_valida_luego_error_revierte_parcial(
        db_url, admin_user):
    """DDL/DML exitosos ANTES del error de ejecución: el efecto parcial y el
    registro de versión se revierten; reintento corregido funciona."""
    sentinel = commerce.create_product(db_url, sku='SENTINEL-C',
                                       name='Sentinela C', price='1.00')
    assert sentinel['ok']
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT count(*) AS n FROM app_migrations')
            before = cur.fetchone()['n']

    with tempfile.TemporaryDirectory() as tmp:
        batch = Path(tmp)
        for sql in sorted(MIGRATIONS_DIR.glob('*.sql')):
            shutil.copy(sql, batch / sql.name)
        (batch / '9999_valida_luego_falla.sql').write_text(
            'CREATE TABLE corr01c_probe (id integer PRIMARY KEY, note text);\n'
            "INSERT INTO corr01c_probe VALUES (1, 'efecto parcial');\n"
            "INSERT INTO corr01c_probe VALUES (1, 'duplicado viola PK');\n",
            encoding='utf-8')
        with pytest.raises(psycopg.errors.UniqueViolation):
            apply_all(db_url, directory=batch)

    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('corr01c_probe') AS t")
            assert cur.fetchone()['t'] is None, 'el efecto parcial debe revertirse'
            cur.execute('SELECT count(*) AS n FROM app_migrations')
            assert cur.fetchone()['n'] == before
            cur.execute("SELECT count(*) AS n FROM products WHERE sku='SENTINEL-C'")
            assert cur.fetchone()['n'] == 1

    # Reintento corregido: la misma versión sin la violación se aplica.
    with tempfile.TemporaryDirectory() as tmp:
        fixed = Path(tmp)
        for sql in sorted(MIGRATIONS_DIR.glob('*.sql')):
            shutil.copy(sql, fixed / sql.name)
        (fixed / '9999_valida_luego_falla.sql').write_text(
            'CREATE TABLE corr01c_probe_fixed (id integer PRIMARY KEY);\n'
            'INSERT INTO corr01c_probe_fixed VALUES (1);\n', encoding='utf-8')
        assert apply_all(db_url, directory=fixed) == ['9999_valida_luego_falla.sql']
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('corr01c_probe_fixed') AS t")
            assert cur.fetchone()['t'] is not None
            # Limpieza para no contaminar otras pruebas (base temporal).
            cur.execute('DROP TABLE corr01c_probe_fixed')
            cur.execute("DELETE FROM app_migrations WHERE version = 9999")


def test_b3_etl_roto_conserva_contenido_de_todas_las_tablas_bi(
        db_url, org, admin_user):
    product = commerce.create_product(db_url, sku='SRV-HASH', name='Huella',
                                      price='10.00')['product']
    commerce.create_sale(db_url, lines=[{'product_id': product['id'], 'qty': 2}],
                         actor=admin_user['id'])
    good = analytics.rebuild_bi(db_url, 'UTC')
    before = _fingerprint_bi(db_url)
    assert before['bi.meta'] != 'empty'

    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute('ALTER TABLE bi.fact_venta_linea '
                        'RENAME COLUMN neto TO neto_roto')
    with pytest.raises(psycopg.errors.UndefinedColumn):
        analytics.rebuild_bi(db_url, 'UTC')

    with psycopg.connect(db_url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute('ALTER TABLE bi.fact_venta_linea '
                        'RENAME COLUMN neto_roto TO neto')
    after = _fingerprint_bi(db_url)
    assert set(after) == set(BI_TABLES) == set(before)
    for table in BI_TABLES:  # comparación explícita de las nueve
        assert after[table] == before[table], f'lote bueno alterado: {table}'
    assert before['bi.fact_venta_linea'] != '' and before['bi.meta'] != ''
    healed = analytics.rebuild_bi(db_url, 'UTC')
    assert healed['lineas_venta'] == good['lineas_venta']


# ------------------------------------------------- C1: pruebas del helper

def test_c1_huella_cubre_exactamente_nueve_claves(db_url):
    fp = _fingerprint_bi(db_url)
    assert set(fp) == set(BI_TABLES) and len(fp) == 9
    # Ninguna huella vacía por truncado: cada clave tiene hash de 16 hex.
    assert all(len(v) == 16 and set(v) <= set('0123456789abcdef')
               for v in fp.values())


def test_c1_cambio_de_contenido_cambia_su_huella(db_url):
    """Cambiar contenido de una tabla no-meta cambia SU huella y sólo esa.
    La limpieza entre pruebas TRUNCATEa bi: se siembra la tabla primero."""
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO bi.dim_hora (hora_key, franja) "
                        "VALUES (23, 'noche')")
    before = _fingerprint_bi(db_url)
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE bi.dim_hora SET franja = 'prueba-c1' "
                        "WHERE hora_key = 23")
    after = _fingerprint_bi(db_url)
    assert after['bi.dim_hora'] != before['bi.dim_hora']
    for table in BI_TABLES:
        if table != 'bi.dim_hora':
            assert after[table] == before[table], table
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('DELETE FROM bi.dim_hora WHERE hora_key = 23')


def test_c1_serializacion_estable_ante_reordenamiento():
    """CORR01D/C1: reordenar las mismas filas NO cambia la huella."""
    rows = [{'id': 1, 'a': 'x'}, {'id': 2, 'a': 'y'}, {'id': 3, 'a': 'z'}]
    base = hashlib.sha256(_stable_payload(rows).encode()).hexdigest()
    import random
    shuffled = rows[:]
    random.Random(7).shuffle(shuffled)
    assert hashlib.sha256(_stable_payload(shuffled).encode()).hexdigest() == base
    # Y con claves en distinto orden dentro del dict (json sort_keys).
    reordered_keys = [{'a': 'x', 'id': 1}, {'a': 'y', 'id': 2},
                      {'a': 'z', 'id': 3}]
    assert hashlib.sha256(
        _stable_payload(reordered_keys).encode()).hexdigest() == base


# ------------------------------------------------- C2: temporal efectivo

def test_c2_temporal_conserva_valores_escapados_como_admin():
    raw = (f'postgresql://fixture:{SECRET}@db.example:5433/postgres'
           '?sslmode=verify-full&connect_timeout=2'
           '&application_name=crm%20tests&keepalives_idle=30')
    admin, temporal, options = _derived(raw, 'crm_premium_test_abc123')
    adm = conninfo_to_dict(admin)
    tmp = conninfo_to_dict(temporal)
    assert tmp['dbname'] == 'crm_premium_test_abc123'
    for key in ('sslmode', 'connect_timeout', 'keepalives_idle'):
        assert tmp[key] == adm[key], key
    assert tmp['application_name'] == adm['application_name'] == 'crm tests'
    assert tmp['sslmode'] == 'verify-full'


def test_c2_temporal_con_mas_signo_y_porcentaje():
    raw = (f'postgresql://fixture:{SECRET}@db.example:5433/postgres'
           '?application_name=crm%2Btests%25one')  # 'crm+tests%one'
    admin, temporal, _ = _derived(raw, 'temporal_x')
    adm = conninfo_to_dict(admin)
    tmp = conninfo_to_dict(temporal)
    assert adm['application_name'] == tmp['application_name'] == 'crm+tests%one'


def test_c2_rechazos_sigue_antes_de_conectar_con_derivacion_comun():
    raw = (f'postgresql://fixture:{SECRET}@db.example:5433/postgres'
           '?sslmode=require&dbname=otra')
    with pytest.raises(DSNConfigError):
        _derived(raw, 'temporal_x')
