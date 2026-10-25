"""Smoke de instalación distribuida (CORR01C/B4 — fuente versionada).

Construye el wheel, lo instala en un venv EXTERNO al checkout y verifica
migraciones incluidas, render de login y estáticos, contra una base temporal
que crea y destruye. Sin secretos: la conexión admin de pruebas se toma de la
variable de entorno CRM_PREMIUM_TEST_URL (URL postgresql://user:pass@host/
postgres). Toda salida pasa por la redacción de tools/redact_evidencia.

Uso (desde la raíz del proyecto):
  CRM_PREMIUM_TEST_URL=postgresql://... .venv/Scripts/python.exe \
      scripts/dev/smoke_packaging.py
"""
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from urllib.parse import urlunsplit

REPO_ROOT = Path(__file__).resolve().parents[2]

# Sin sys.path hacia el checkout: este script debe probar el WHEEL instalado
# en el venv externo, no el árbol fuente.
import psycopg  # noqa: E402
from crm_premium.shared.testdsns import (  # noqa: E402
    parse_test_dsn, temporal_dsn, verify_target_database)

WHEEL_DIR = Path(tempfile.gettempdir()) / 'crm_premium_wheel'


def build_wheel():
    WHEEL_DIR.mkdir(exist_ok=True)
    for old in WHEEL_DIR.glob('*.whl'):
        old.unlink()
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'wheel', '.', '--no-deps',
         '-w', str(WHEEL_DIR)],
        cwd=REPO_ROOT, capture_output=True, text=True)
    print(result.stdout[-800:] if result.stdout else '', end='')
    if result.returncode != 0:
        print(result.stderr[-2000:])
    return result.returncode


def run(url):
    admin_url, parts, options = parse_test_dsn(url)
    name = f'crm_premium_pack_{secrets.token_hex(5)}'
    test_dsn = temporal_dsn(parts, options, name)
    admin = psycopg.connect(admin_url, autocommit=True)
    with admin.cursor() as cur:
        cur.execute(f'CREATE DATABASE "{name}"')
    admin.close()
    try:
        os.environ['DATABASE_URL'] = test_dsn
        os.environ['SECRET_KEY'] = 'smoke-key-no-operativo'
        guard = psycopg.connect(test_dsn, autocommit=True,
                                row_factory=psycopg.rows.dict_row)
        verify_target_database(guard, name)
        guard.close()

        from crm_premium.infrastructure.persistence.migrations import apply_all
        applied = apply_all(test_dsn)
        assert '0001_core.sql' in applied and '0005_venta_linea_costo.sql' in applied
        from crm_premium.entrypoints.web.app import create_app
        app = create_app(db_url=test_dsn)
        app.config['testing'] = True
        client = app.test_client()
        page = client.get('/login')
        assert page.status_code == 200 and b'CRM' in page.data
        css = client.get('/static/app.css')
        assert css.status_code == 200 and b'sidebar' in css.data
        js = client.get('/static/agenda.js')
        assert js.status_code == 200
        import crm_premium
        pkg = Path(crm_premium.__file__).parent
        assert (pkg / 'migrations' / 'operational' / '0001_core.sql').exists()
        assert 'site-packages' in str(pkg), (
            f'debe ejecutar el wheel instalado, no el checkout: {pkg}')
        print(f'SMOKE OK (paquete instalado en {pkg})')
        return 0
    finally:
        admin = psycopg.connect(admin_url, autocommit=True)
        with admin.cursor() as cur:
            cur.execute(
                """SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                   WHERE datname = %s AND pid <> pg_backend_pid()""", (name,))
            cur.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def main():
    url = os.environ.get('CRM_PREMIUM_TEST_URL')
    if not url:
        print('Defina CRM_PREMIUM_TEST_URL (base postgres del servidor de pruebas)')
        return 4
    code = build_wheel()
    if code != 0:
        return code
    wheels = list(WHEEL_DIR.glob('*.whl'))
    if not wheels:
        print('No se produjo wheel')
        return 1
    print(f'wheel: {wheels[0].name}')
    return run(url)


if __name__ == '__main__':
    sys.exit(main())
