# Dictamen CORR01C — revisión independiente 01
Fecha: 24-10-2026. Codex. **DEVUELTA PARA DOS CORRECCIONES ACOTADAS (CORR01D).**

## Comprobación y avances aceptados
- Reejecutadas 10 pruebas de tiempo: --noconftest -p no:cacheprovider, salida 0.
- Invocadas directamente cinco pruebas puras B1 de test_corr01c.py, sin fixtures: todas pasan. Rechazo de dbname/identidad/destino, duplicados y desconocidas reconocido. El bloqueo principal de aislamiento del dictamen anterior queda resuelto para los casos revisados; no se vuelve a exigir su implementación.
- Manifiesto final 20261024T224408Z: 69 rutas comprobadas por SHA256, cero diferencias y cero ausentes en el árbol actual. No se alteró código durante esta revisión.
- Evidencia verbosa conserva fallo intermedio y 104 pasadas de GLM; nuevo wheel indica instalación site-packages fuera del checkout. Se reconoce mejora de trazabilidad.
- Lectura confirma migración con CREATE+INSERT válidos antes de UniqueViolation y recuperación; avance B3 reconocido.
- Guarda de current_database y lista blanca revisadas. CLI y redacción mantienen pendientes de rotación operativa separados.
- Sin CRM_PREMIUM_TEST_URL disponible; no se leyó .env ni hubo conexión PostgreSQL. Las 104 pruebas son ejecución reportada por GLM, no corrida integral repetida por Codex. No se efectuó rotación ni login real.

## C1 — P2 — la huella de nueve tablas sólo contiene bi.meta
tests/test_corr01c.py::_fingerprint_bi coloca payload=... y out[table]=... FUERA del bucle for table in BI_TABLES. Lee las nueve tablas, pero calcula/guarda únicamente la última: bi.meta.

Reproducción aislada con conexión/cursor simulados devolviendo contenido por tabla:
Fingerprint table count: 1; keys: bi.meta.
La igualdad before==after no demuestra preservación de hechos y dimensiones. Esto invalida la afirmación de «contenido de las nueve tablas» aunque pytest esté verde. No es evidencia de corrupción de datos ni se afirma que ETL real esté roto.

Corregir indentación y exigir conjunto EXACTO de nueve claves. Ordenar filas de forma estable para que la huella compare contenido y no orden incidental. Añadir comprobación del propio helper: cambiar contenido de una tabla que no sea meta debe cambiar esa huella; orden distinto de las mismas filas no debe producir falso cambio. Reejecutar prueba PostgreSQL de ruptura y recuperación.

## C2 — P2 — derivación temporal pierde valor de parámetros escapados
parse_test_dsn construye admin con quote_via=quote (correcto), pero tests/conftest.py::db_url y test_corr01c.py::_derived vuelven a urlencode(options) sin quote_via. libpq URI interpreta '+' literalmente, no como espacio de formulario.

Reproducción sin conexión:
Entrada sintética application_name=crm%20tests.
conninfo_to_dict(DSN_temporal)['application_name'] == 'crm tests' → False.
El test actual verifica 'crm tests' en admin, pero no en temporal, así que no detecta la pérdida. Lo mismo puede afectar rutas/cadenas permitidas con espacios; no afecta el rechazo de dbname ya corregido.

Centralizar derivación o usar codificación URI consistente en fixture/smoke/pruebas. Probar valores efectivos en admin Y temporal con espacios, '+', '%' y caracteres escapados. No volver a abrir claves prohibidas.

## Alcance del siguiente cierre
CORR01D corrige C1/C2 y actualiza manifiesto/evidencia de la nueva revisión. No se exige reescribir B1 ni ampliar producto. E00B se revisó por separado y quedó aceptada como base documental de E01; todavía no comenzar E01 hasta aceptar este cierre.

Observaciones no bloqueantes: --in-place sanea archivos existentes y no demuestra por sí solo un filtro previo a toda persistencia; mantener descripción precisa y captura segura. Coincidencias cero sólo significa cero para patrones del detector, no ausencia universal de secretos. Rotación original admin y credencial de pruebas siguen pendientes del propietario, fuera de esta corrección de código.
