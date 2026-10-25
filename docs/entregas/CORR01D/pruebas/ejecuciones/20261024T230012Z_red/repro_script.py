"""Reproducción sin conexión de C1 (huella trunca a bi.meta) y C2 (temporal
pierde valor escapado). Credenciales exclusivamente sintéticas."""
import sys, json, hashlib
sys.path.insert(0, 'src')
sys.path.insert(0, 'tests')

print('=== C2: derivación temporal ===')
from conftest import parse_test_dsn
raw = ('postgresql://fixture:fixture@db.example:5433/postgres'
       '?sslmode=verify-full&connect_timeout=2&application_name=crm%20tests')
admin, parts, options = parse_test_dsn(raw)
from urllib.parse import urlencode, urlunsplit
temporal = urlunsplit((parts.scheme, parts.netloc, '/temporal_name',
                       urlencode(options), ''))
from psycopg.conninfo import conninfo_to_dict
adm = conninfo_to_dict(admin); tmp = conninfo_to_dict(temporal)
print('admin application_name:', repr(adm.get('application_name')))
print('temporal application_name:', repr(tmp.get('application_name')))
print('C2 FALLO (esperado igual a "crm tests" en temporal):',
      tmp.get('application_name') != 'crm tests')

print()
print('=== C1: _fingerprint_bi truncada ===')
import inspect
from test_corr01c import _fingerprint_bi
src = inspect.getsource(_fingerprint_bi)
inside = [line for line in src.splitlines()
          if 'out[table]' in line or 'payload = ' in line]
indent = min(len(l) - len(l.lstrip()) for l in inside)
loop_indent = min(len(l) - len(l.lstrip()) for l in src.splitlines()
                  if 'for table in BI_TABLES' in l)
print('asignación de huella indentada DENTRO del bucle:', indent > loop_indent)
print('C1 FALLO (asignación fuera del bucle => sólo última tabla):',
      indent <= loop_indent)
