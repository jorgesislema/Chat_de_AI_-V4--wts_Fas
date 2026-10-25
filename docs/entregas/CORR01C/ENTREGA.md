# ENTREGA CORR01C — cierre de aislamiento, evidencia y trazabilidad

Implementador: GLM/ZCode. Origen: `docs/entregas/CORR01B/revision/REVISION_CODEX_01.md`
(DEVUELTA PARA CORRECCIÓN ACOTADA CORR01C — no editado). Estado: **lista para
revisión**. Sin autoaceptación. Sin funciones empresariales nuevas.

## Matriz B1–B4

### B1 — aislamiento de DSN (resuelto)
- Utilidades movidas al paquete: `src/crm_premium/shared/testdsns.py`
  (`parse_test_dsn`, `verify_target_database`, `DSNConfigError`); conftest
  re-exporta. Así las guardas existen también en instalaciones wheel.
- **Lista blanca estricta de query**: sólo TLS (sslmode/sslcert/sslkey/
  sslrootcert/sslcrl/sslpassword/sslnegotiation), timeouts (connect_timeout,
  tcp_user_timeout, keepalives*), application_name, target_session_attrs y
  gssencmode. Se rechazan siempre: **dbname/database, host, hostaddr, port,
  user, password, passfile, service, options** y cualquier clave desconocida.
  Claves duplicadas se rechazan; escapes se decodifican (`%20` → espacio,
  probado con parser libpq `conninfo_to_dict`).
- **Guarda de destino efectivo** `verify_target_database`: antes de migrar
  (fixture) y antes de cada TRUNCATE compara `current_database()` con el
  nombre temporal EXACTO recién generado; cualquier desviación aborta.
- DSN inválida se rechaza **antes de abrir conexión** (función pura).
- Pruebas (`tests/test_corr01c.py`, sin conexión para los casos de rechazo):
  dbname/host/hostaddr/port/user/password/service/options rechazados sin
  imprimir secreto; duplicados; desconocidas; conninfo rechazado; URL válida
  preserva TLS/timeout y el destino efectivo verificado con
  `conninfo_to_dict` es la base temporal esperada; la guarda rechaza un
  nombre distinto con «Aislamiento violado».
- Nota de consolidación de la revisión: un SELECT de verificación sobre una
  conexión autocommit=False abre transacción externa y convierte el
  `transaction()` siguiente en savepoint (el TRUNCATE se revertía al cerrar).
  Detectado en esta corrida (conservado en 20261024T222323Z: 6 failed) y
  corregido: la guarda usa conexión autocommit propia y el TRUNCATE el helper
  `transaction()` como primera operación.

### B2 — redacción de evidencia (resuelto; sin claims de rotación)
- Pipeline: `tools/redact_evidencia.py` — `--in-place` redacta ANTES de
  persistir; `--check` **revisa por conteos y rutas, nunca muestra
  coincidencias**. Patrones: URLs postgres con credenciales, tokens Bearer,
  KEY=valor de configuración. Exclusión declarada: URLs sintéticas
  `fixture:fixture@` de reproducción (no son secretos).
- Incidente propio registrado: la primera pasada redactó una URL sintética
  DENTRO del dictamen CORR01B; se **restauró byte a byte** (conocida por la
  lectura previa íntegra) y la herramienta se refinó con la exclusión.
  Hashes actuales de los cuatro dictámenes (integridad):
  PR00B 8bfea381…, CORR01 e91f925e…, CORR01B c1f03fd5…, E00 cd9055004749…
- Estado final: `revision_evidencia.txt` = **0 coincidencias** en la carpeta
  de ejecución y en docs/entregas (conteo, sin contenido). La redacción que
  Codex aplicó al entorno_y_comando.txt de CORR01B se respeta (no restaurada).
- **No se afirma rotación del admin ni de la credencial de pruebas.** Ninguna
  rotación operativa fue autorizada; ambas quedan pendientes del propietario.

### B3 — ruptura con escritura válida previa y huella completa (resuelto)
- `test_b3_migracion_escritura_valida_luego_error_revierte_parcial`: migración
  con DDL (CREATE TABLE) + INSERT exitoso + INSERT que viola PK → error de
  ejecución; se comprueba que la tabla del efecto parcial **no existe**, el
  registro de versión no avanza, el centinela sobrevive, y el **reintento
  corregido** de la misma versión se aplica con éxito.
- `test_b3_etl_roto_conserva_contenido_de_todas_las_tablas_bi`: huella SHA256
  por contenido de **las 9 tablas bi** (hechos, 7 dimensiones y bi.meta)
  antes/después del fallo — igualdad bit a bit del lote bueno, no sólo
  conteos; curación posterior cuadra.

### B4 — trazabilidad y manifiesto (resuelto; nueva ejecución identificada)
- Fuente versionada del smoke: `scripts/dev/smoke_packaging.py` (sin
  secretos; toma CRM_PREMIUM_TEST_URL del entorno; **ejecuta el WHEEL
  instalado** — assertion de que el paquete corre desde site-packages, no el
  checkout). Primera pasada descubrió que el script probaba el checkout:
  corregido y vuelto a ejecutar (ambas salidas conservadas).
- Carpeta final `pruebas/ejecuciones/20261024T224408Z/`: manifest_sha256.txt
  (71→72+ archivos fuente/tests/config no secreta), comandos.txt (variables
  privadas, nunca literales), suite_completa.txt (**104 passed · exit 0 ·
  UTC 22:45:14**), wheel_externo.txt (install+smoke exit 0), wheel_sha256.txt
  (9c7b055e08e9c355d390d140a0ef80d07afe01e6f18d4dd2be045b26f0ef81ae),
  revision_evidencia.txt.
- Carpetas previas conservadas como ejecuciones de revisiones ANTERIORES del
  árbol: 20261024T222323Z (6 failed — corrida con el defecto de savepoint)
  y 20261024T223334Z (104 passed, manifiesto previo a testdsns.py). El
  manifiesto definitivo corresponde SOLO a la última.
- Regresión completa en PostgreSQL temporal aislado con conexión explícita
  (`CRM_PREMIUM_TEST_URL`, parámetro connect_timeout preservado).

## Pendientes honestos
- Rotación del admin (R01) y de la credencial de pruebas: del propietario.
- Permisos por documento de conocimiento y por sede: E01/E03 (R04 residual).
- Recorrido visual independiente del navegador: no cubierto aquí.

## Cambios de código
- `shared/testdsns.py` (nuevo), `tests/conftest.py` (lista blanca + guardas +
  limpieza corregida), `tests/test_corr01c.py` (8 pruebas nuevas),
  `scripts/dev/smoke_packaging.py` (nuevo), `tools/redact_evidencia.py`
  (nuevo), `tests/test_corr01b.py` (desempaquetado a 3 valores).
- Total suite: **104 pruebas** (96 + 8).
