# Dictamen independiente CORR01B — revisión 01
Fecha: 24-10-2026. Codex. **DEVUELTA PARA CORRECCIÓN ACOTADA CORR01C. E01 todavía no habilitada.**

## Avance reconocido
El código conserva TLS/timeout, añade rotación interactiva y pruebas de fallo de ETL/migración. Hay ahora salida verbosa de 96 casos y registros de empaquetado con códigos de salida. No se reabren defectos que la evidencia ya resuelve.

## Comprobación propia
1. Diez pruebas de tests/test_timeutil.py pasaron con --noconftest y sin caché.
2. Invocación directa de tres funciones puras de test_corr01b.py: preservación de parámetros, rechazo de conninfo sin secreto y rechazo de URL sin credenciales/base: PASS. No es corrida pytest completa ni usa fixtures.
3. CLI cmd_rotate_password con getpass/_db_url/admin_reset_password simulados: llama una vez al servicio y salida sin contraseña sintética. No se rotó ninguna credencial real.
4. Inspección de servicio confirma hash y revocación de sesiones; no ejecución PostgreSQL independiente.
5. CRM_PREMIUM_TEST_URL no disponible en entorno de esta revisión. No se leyó .env ni se usó credencial hallada en documentos. Las 96 pasadas siguen siendo evidencia de GLM, no repetida por Codex.

## B1 — P1 — query dbname rompe aislamiento de pruebas (reproducido)
tests/conftest.py: parse_test_dsn devuelve parts.query sin controlar claves; db_url cambia path pero conserva query. libpq permite que dbname de query prevalezca.

Reproducción sin conexión, credenciales exclusivamente sintéticas:
URL: postgresql://fixture:fixture@invalid:5433/postgres?sslmode=verify-full&dbname=synthetic_wrong_targetlmode=verify-full&dbname=synthetic_wrong_target
Se deriva path /crm_premium_test_synthetic manteniendo query.
psycopg.conninfo.conninfo_to_dict(derived)['dbname'] devuelve synthetic_wrong_target.
Esperado: crm_premium_test_synthetic o rechazo explícito antes de conexión.

La fixture aplica migraciones y después TRUNCATE de tablas de negocio/BI; con este override puede operar otra base en lugar de la recién creada. No se realizó ninguna conexión para probarlo. Es bloqueante aunque el DSN usado por GLM en su corrida no tuviera ese parámetro.

Corregir validación de opciones: rechazar sustitución de identidad/destino (dbname, host/hostaddr/port, user/password, service u otras equivalentes) en query; conservar opciones permitidas TLS/timeout/application_name sin aceptar «todos los parámetros» indiscriminadamente. Verificar destino efectivo con parser libpq y base actual antes de operaciones destructivas. Probar guardas también para query duplicada/escapada, sin acceder a servidor operativo.

## B2 — P1 documental — credencial en evidencia
pruebas/ejecuciones/20261024T214438Z/entorno_y_comando.txt incluía una URL con usuario y contraseña de la conexión descrita como pruebas. Contradice «comando depurado» y política de no credenciales en reportes. No se reproduce el valor ni se utilizó.

Codex redacta únicamente la parte de autenticación de esa URL en el archivo, dejando constancia visible; conserva el resto de evidencia. GLM debe usar un mecanismo que redacte antes de persistir y revisar archivos de evidencia sin imprimir coincidencias. No afirmar rotación por redacción. El propietario debe gestionar también esa credencial si continúa vigente, según exposición. La rotación del admin R01 original permanece pendiente aparte.

## B3 — P2 — ruptura de migración no demuestra rollback de cambios ya ejecutados
test_migracion_rota_hace_rollback_y_conserva_lote_anterior usa un archivo cuya primera instrucción es SQL sintácticamente inválido. Demuestra rechazo sin registrar versión y preservación del lote anterior; no demuestra reversión de una escritura exitosa anterior al fallo dentro de esa migración.

Añadir caso con escritura/DDL válida seguida de error de ejecución controlado (por ejemplo violación de restricción), comprobando desaparición de efecto parcial y ausencia de registro de versión. Reintentar corregida con éxito. No usar syntax error de lote completo como única inyección: puede rechazarse antes de ejecutar la primera sentencia.
ETL sí falla tras pasos previos y verifica hechos/productos/meta; fortalecer comparación con contenido/hashes de las tablas afectadas para sustentar «lote completo», no sólo conteos de dos tablas. No volver a afirmar todas las dimensiones iguales si no se comprueban.

## B4 — P2 — trazabilidad pendiente de completar
El registro de wheel contiene build y hash del wheel, pero remite a /tmp/smoke_packaging.py sin guardar su fuente/comando exacto completo de instalación/smoke. No hay manifiesto de la revisión fuente probada. Añadir script reproducible sin secretos, comandos reales y manifest/hash del código y tests. No generar retrospectivamente una huella como si fuera la de la corrida antigua: nueva ejecución identificada.

## Resolución
GLM entrega CORR01C según docs/producto/premium/11_PROMPT_CORR01C_E00B.md. Mantener las mejoras ya verificadas, revisión anterior y corridas existentes. No ampliar producto ni usar credenciales de documentos para completar revisión. E01 requiere cierre técnico y E00B aceptadas.
