# ENTREGA CORR01B — cierre técnico de correcciones

Implementador: GLM/ZCode. Origen: `docs/entregas/CORR01/revision/REVISION_CODEX_01.md`
(PARCIALMENTE VERIFICADA; CIERRE PENDIENTE — no editado por GLM). Estado:
**lista para revisión**. Sin autoaceptación. Sin módulos nuevos.

## Respuesta a los pendientes de cierre

### 1) DSN de pruebas — resuelto
- `tests/conftest.py` ahora expone `parse_test_dsn(raw)` validado por pruebas:
  conserva **todos los parámetros de consulta** (sslmode, connect_timeout,
  application_name…) tanto en la conexión admin (CREATE/DROP) como en la DSN
  temporal; rechaza formato conninfo palabra=valor y URLs sin credenciales/base
  con mensaje claro **que nunca incluye el valor recibido** (prueba
  `test_dsn_rechaza_conninfo_sin_imprimir_secreto`).
- Soporte declarado honesto: **sólo URL postgresql://**, no conninfo.
- El servidor de pruebas de esta corrida usó `?connect_timeout=5` efectivo.

### 2) Ruptura de migración/ETL — resuelto con pruebas reales
- `test_migracion_rota_hace_rollback_y_conserva_lote_anterior`: lote copiado a
  directorio temporal + `9999_rota.sql` con SQL inválido; `apply_all` (que
  ahora acepta `directory=` para pruebas) **falla**, `app_migrations` queda en
  el conteo anterior y el dato centinela sobrevive; el directorio real del
  paquete sigue aplicable.
- `test_etl_roto_hace_rollback_y_conserva_lote_bueno`: inyección real en
  PostgreSQL (`RENAME COLUMN neto TO neto_roto` a mitad de esquema), el ETL
  **falla**, y el lote bueno previo queda íntegro (filas de hechos/dimensiones
  y `bi.meta` sin avanzar); tras restaurar, el ETL sana y cuadra.

### 3) R01 — procedimiento reparado; rotación real sigue PENDIENTE
- Nuevo comando CLI **interactivo**: `python -m crm_premium rotate-password
  [usuario]` — getpass doble, validación ≥12, revoca sesiones; la contraseña
  nunca va en argumentos, historial ni salida (respaldo en
  `identity.admin_reset_password`, probado).
- Documento CORR01 §R01 reescrito: eliminada la contraseña en línea y el SQL
  defectuoso (`psql -c "...PASSWORD '...')"`), sustituidos por `\password
  postgres` interactivo en psql. Estados separados explícitos: redacción
  aplicada ≠ rotación ejecutada; **rotación real pendiente de confirmación
  autorizada del propietario**.

### 4) Evidencia reproducible completa — resuelto
- `pruebas/ejecuciones/20261024T214438Z/`: `entorno_y_comando.txt` (fecha UTC,
  SO, Python, versiones de librerías, versión del servidor PostgreSQL de
  pruebas, comando depurado), `suite_completa.txt` (**salida íntegra verbosa
  de 96 pruebas, duración 60 s, exit 0, fecha UTC**) y `wheel_externo.txt`
  (build/install/smoke completos con exit 0 cada paso, venv fuera del
  checkout). Las ejecuciones previas de CORR01 se conservan sin tocar.
- Conteo actual honesto: **96 pruebas** (90 de CORR01 + 6 nuevas de CORR01B).

### 5) Pendientes declarados (sin fingir cierre)
- **R01**: rotación real de credenciales por el propietario.
- **R04 residual**: permisos por documento de conocimiento y por sede NO
  existen; el historial propio del asistente y el opt-in global admin son lo
  único implementado. F01 completo (MFA, recuperación, permisos granulares)
  y F12/F15 quedan pendientes hasta E01/E03.
- Sin recorrido visual independiente de navegador por Codex en esta entrega.
- Sin prueba de fallo de migración sobre bases ya migradas del propietario
  (sólo base temporal, por diseño).

## Cambios de código
- `tests/conftest.py` (DSN), `tests/test_corr01b.py` (6 pruebas nuevas).
- `infrastructure/persistence/migrations.py`: `apply_all(url, directory=None)`.
- `modules/identity/service.py`: `admin_reset_password`.
- `__main__.py`: comando `rotate-password`.
- `docs/entregas/CORR01/ENTREGA.md`: §R01 reparado (historial conservado).

## Pruebas
- Comando reproducible (ver `entorno_y_comando.txt`):
  `CRM_PREMIUM_TEST_URL=postgresql://<credencial de prueba>@<servidor aislado>/postgres?connect_timeout=5 .venv/Scripts/python -m pytest tests/ -o addopts= -v`
- Resultado: **96 passed · exit 0 · 2026-10-24T21:52Z**.

## Siguiente paso
Revisión independiente de CORR01B. E00 (documental) preparado en paralelo;
ningún módulo nuevo antes del cierre.
