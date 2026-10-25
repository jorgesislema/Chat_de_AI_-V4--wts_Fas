"""Migraciones versionadas de PostgreSQL.

Cada archivo ``NNNN_nombre.sql`` se aplica una sola vez dentro de su propia
transacción y queda registrado en ``app_migrations``. El runner es
idempotente: re-ejecutar no re-aplica nada.

CORR01/R10: las migraciones viven DENTRO del paquete
(``crm_premium/migrations/operational``) para que una instalación wheel
funcione fuera del checkout. ``CRM_PREMIUM_MIGRATIONS_DIR`` permite apuntar a
un directorio externo si una instalación lo requiere. El registro usa el
nombre de archivo, por lo que la reubicación no re-aplica nada.
"""
import os
from pathlib import Path

from .db import connect

_DEFAULT_DIR = Path(__file__).resolve().parents[2] / 'migrations' / 'operational'
MIGRATIONS_DIR = Path(os.environ.get('CRM_PREMIUM_MIGRATIONS_DIR')
                      or _DEFAULT_DIR)


def _ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_migrations (
                version    integer PRIMARY KEY,
                name       text    NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
        """)


def applied(url):
    with connect(url) as conn:
        _ensure_table(conn)
        with conn.cursor() as cur:
            cur.execute('SELECT version FROM app_migrations ORDER BY version')
            rows = cur.fetchall()
        conn.commit()
    return {row['version'] for row in rows}


def pending_files(url, directory=None):
    done = applied(url)
    files = sorted((directory or MIGRATIONS_DIR).glob('*.sql'))
    result = []
    for path in files:
        try:
            version = int(path.name.split('_', 1)[0])
        except ValueError as exc:
            raise RuntimeError(f'Migración con nombre inválido: {path.name}') from exc
        if version not in done:
            result.append((version, path))
    return result


def apply_all(url, directory=None):
    """Aplica las migraciones pendientes y devuelve la lista aplicada.

    ``directory`` permite a las pruebas apuntar a un lote alterado (CORR01B:
    prueba de ruptura) sin tocar el paquete instalado.
    """
    applied_now = []
    for version, path in pending_files(url, directory):
        sql = path.read_text(encoding='utf-8')
        with connect(url) as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(
                        'INSERT INTO app_migrations(version, name) VALUES (%s, %s)',
                        (version, path.name))
            conn.commit()
        applied_now.append(path.name)
    return applied_now
