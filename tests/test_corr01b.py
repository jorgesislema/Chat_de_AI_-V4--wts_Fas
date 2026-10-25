"""CORR01B: cierre técnico — DSN con parámetros, ruptura de migración/ETL
con lote válido conservado, y rotación interactiva."""
import shutil
import tempfile
from pathlib import Path

import psycopg
import pytest
from psycopg.rows import dict_row

from conftest import DSNConfigError, parse_test_dsn
from crm_premium.infrastructure.persistence.migrations import (
    MIGRATIONS_DIR, apply_all)
from crm_premium.modules.analytics import service as analytics
from crm_premium.modules.commerce import service as commerce
from crm_premium.modules.identity import service as identity


# ------------------------------------------------- CORR01B-1: DSN de pruebas

def test_dsn_preserva_parametros_tls_y_timeout():
    raw = ('postgresql://u:secreto@db.example:5433/postgres'
           '?sslmode=verify-full&connect_timeout=2&application_name=pruebas')
    admin, parts, options = parse_test_dsn(raw)
    assert 'sslmode=verify-full' in admin
    assert 'connect_timeout=2' in admin
    assert 'application_name=pruebas' in admin
    assert admin.count('/postgres') == 1
    # La DSN temporal conserva los mismos parámetros (se construye igual).
    from urllib.parse import urlunsplit
    temp = urlunsplit((parts.scheme, parts.netloc, '/mi_base', parts.query, ''))
    assert 'sslmode=verify-full' in temp and 'connect_timeout=2' in temp


def test_dsn_rechaza_conninfo_sin_imprimir_secreto():
    raw = 'host=servidor password=ClaveSecreta123 user=u'
    with pytest.raises(DSNConfigError) as exc:
        parse_test_dsn(raw)
    assert 'ClaveSecreta123' not in str(exc.value)
    assert 'conninfo' in str(exc.value).lower()


def test_dsn_rechaza_url_sin_credenciales_o_sin_base():
    for bad in ('postgresql://host:5432/db',
                'postgresql://u:p@host:5432'):
        with pytest.raises(DSNConfigError):
            parse_test_dsn(bad)


# ---------------------------------------- CORR01B-2: ruptura de migración

def test_migracion_rota_hace_rollback_y_conserva_lote_anterior(db_url):
    """Una migración inválida revierte su propio lote: el registro de
    migraciones y los datos del lote bueno anterior quedan intactos."""
    sentinel = commerce.create_product(db_url, sku='SENTINEL-X',
                                       name='Sentinela', price='1.00')
    assert sentinel['ok']
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT count(*) AS n FROM app_migrations')
            before = cur.fetchone()['n']

    with tempfile.TemporaryDirectory() as tmp:
        batch = Path(tmp)
        for sql in sorted(MIGRATIONS_DIR.glob('*.sql')):
            shutil.copy(sql, batch / sql.name)
        (batch / '9999_rota.sql').write_text(
            'ESTO NO ES SQL VALIDO;', encoding='utf-8')
        with pytest.raises(psycopg.errors.SyntaxError):
            apply_all(db_url, directory=batch)

    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT count(*) AS n FROM app_migrations')
            assert cur.fetchone()['n'] == before
            cur.execute("SELECT count(*) AS n FROM products WHERE sku='SENTINEL-X'")
            assert cur.fetchone()['n'] == 1
    # El paquete real sigue aplicable (la ruptura no tocó su directorio).
    assert apply_all(db_url) == []


# --------------------------------------------- CORR01B-2: ruptura de ETL

def test_etl_roto_hace_rollback_y_conserva_lote_bueno(db_url, org, admin_user):
    product = commerce.create_product(db_url, sku='SRV-ETLX', name='ETL X',
                                      price='10.00')['product']
    commerce.create_sale(db_url, lines=[{'product_id': product['id'], 'qty': 1}],
                         actor=admin_user['id'])
    good = analytics.rebuild_bi(db_url, 'UTC')
    assert good['lineas_venta'] >= 1
    stamp_before = analytics.last_rebuild(db_url)

    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Inyección de ruptura: el INSERT explícito por columnas no
            # encontrará 'neto' a mitad del ETL (las vistas siguen al
            # renombrado, sin dependencias rotas).
            cur.execute('ALTER TABLE bi.fact_venta_linea '
                        'RENAME COLUMN neto TO neto_roto')
    with pytest.raises(psycopg.errors.UndefinedColumn):
        analytics.rebuild_bi(db_url, 'UTC')
    with psycopg.connect(db_url, autocommit=True, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # Restaurar la columna y comprobar que el lote bueno sobrevivió
            # íntegro (el TRUNCATE inicial quedó dentro del rollback).
            cur.execute('ALTER TABLE bi.fact_venta_linea '
                        'RENAME COLUMN neto_roto TO neto')
            cur.execute('SELECT count(*) AS n FROM bi.fact_venta_linea')
            lines = cur.fetchone()['n']
            cur.execute('SELECT count(*) AS n FROM bi.dim_producto')
            dims = cur.fetchone()['n']
    assert lines == good['lineas_venta'] and dims > 0
    assert analytics.last_rebuild(db_url) == stamp_before  # meta no avanzó

    healed = analytics.rebuild_bi(db_url, 'UTC')
    assert healed['lineas_venta'] == good['lineas_venta']


# ------------------------------------------ CORR01B-3: rotación interactiva

def test_admin_reset_password_politica_y_revoca(db_url, admin_user):
    weak = identity.admin_reset_password(db_url, username='admin_test',
                                         new_password='corta')
    assert not weak['ok'] and weak['code'] == 'weak_password'
    missing = identity.admin_reset_password(db_url, username='nadie',
                                            new_password='OtraClaveLarga.7')
    assert not missing['ok'] and missing['code'] == 'not_found'
    auth = identity.authenticate(db_url, username='admin_test',
                                 password='ClaveLarga.2026')
    assert auth['ok']
    rotated = identity.admin_reset_password(db_url, username='admin_test',
                                            new_password='RotadaInteractiva.9')
    assert rotated['ok']
    old_token = identity.user_for_session(db_url, token=auth['token'])
    assert old_token[0] is None, 'las sesiones deben morir al rotar'
    reauth = identity.authenticate(db_url, username='admin_test',
                                   password='RotadaInteractiva.9')
    assert reauth['ok']
    identity.admin_reset_password(db_url, username='admin_test',
                                  new_password='ClaveLarga.2026')
