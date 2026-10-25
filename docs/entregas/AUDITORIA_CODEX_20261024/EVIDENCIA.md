# Evidencia independiente de auditoría — 24-10-2026

No contiene credenciales reales ni datos de clientes. Código de aplicación sin modificaciones durante la auditoría.

## E01 — pruebas de tiempo

Comando desde raíz V4:
.\.venv\Scripts\python.exe -B -m pytest --noconftest -p no:cacheprovider tests/test_timeutil.py -q

Código de salida: 0.
Salida: .......... [100%]
Resultado: 10 pruebas pasaron. Se deshabilitó conftest para evitar carga de .env; no es suite integral de PostgreSQL.

## E02 — reproducciones en memoria

Ejecutadas mediante python -B por entrada estándar. Flask create_app con load_dotenv sustituido por mock y URL sintética, identity.authenticate/user_for_session y assistant.history simulados. No conexión a PostgreSQL ni login real.

Login retry repro: first failure=401; cookie removed=True; retry=400.
Expected retry should reach auth; actual CSRF rejection=True.

Assistant history repro status=200; history call=call('postgresql://invalid/audit_no_connection', limit=10).
Usuario sintético role=user, ID 22; no parámetro user_id en llamada.

SQL extraído mediante AST de _tool_resumen_ventas y evaluado en SQLite en memoria con una fila sintética status=reversed, total=100:
Financial aggregate from actual SQL, one fully reversed sale=(-100, 0); expected net=0.
Sólo valida aritmética del agregado; no ejecuta función completa ni certifica PostgreSQL.

## E03 — horario puro e intenciones

build_window_policy con zone=UTC, days=[0,1,2,3,4], start=09:00, end=17:00.
overnight_closed: 2026-10-26T10:00:00+00:00 → 2026-10-27T11:00:00+00:00; result=None; expected rejection.
seconds_after_close: 2026-10-26T16:00:00+00:00 → 2026-10-26T17:00:30+00:00; result=None; expected rejection.

_detect('cobros de hoy') = ('precio', 'cobros de hoy').
_detect('recaudacion de hoy') = ('ventas', 'hoy').
_detect('ventas de hoy') = ('ventas', 'hoy').

## E04 — inventario estático, no ejecución

AST de funciones test_:
test_analytics.py 3; test_assistant.py 8; test_commerce.py 9; test_identity.py 9;
test_scheduling.py 12; test_security.py 10; test_timeutil.py 10; test_web_flow.py 9.
Total 70 funciones en 8 archivos. Parametrizaciones no contadas.

Migraciones presentes: 0001_core.sql, 0002_history_note_id.sql, 0003_comercio.sql, 0004_bi.sql.
Resumen previo PR00B/evidencias/pytest_resumen.txt: 47 passed in 37.70s (GLM histórico).
No verificación independiente de ese conteo para el árbol actual.

## E05 — referencia tarifaria

Consulta oficial https://whatsappbusiness.com/resources/faq/ el 24-10-2026: sección de facturación indica cambio desde octubre, primeros 1.000 mensajes de servicio por número/mes gratuitos y cobro desde 1.001. Página comercial general consultada no coincide plenamente; documentación técnica directa no accesible con la herramienta de consulta. No se certificó un tarifario completo.
