# GLM — cierre acotado CORR01C y ajuste documental E00B
Fecha: 24-10-2026. Codex dirige/revisa; GLM implementa/prueba. Trabaja en H:\git\Agente de reserva V4. Lee AGENTS, ESTADO, PLAN, MAPA, expediente 08–10 y dictámenes:
docs/entregas/CORR01B/revision/REVISION_CODEX_01.md
docs/entregas/E00/revision/REVISION_CODEX_01.md

Conserva código, mejoras verificadas, evidencia e historial. No autoaceptación ni nuevas funciones empresariales en esta corrección.

## CORR01C — primero, cerrar aislamiento y evidencia
1. Reproduce B1 sin conectar: DSN sintético con query dbname distinto del path. Con conninfo_to_dict muestra el destino efectivo sin imprimir credenciales. Evita que opciones query sustituyan identidad/destino: valida claves y duplicados/escapes, conserva opciones TLS/timeout/application_name admitidas. DSN inválida se rechaza antes de abrir conexión. Verifica base efectiva/identidad esperada antes de migrar/TRUNCATE/DROP; jamás operar una base cuyo nombre no sea exactamente el temporal recién generado.
2. Probar dbname override, host/user/service u opciones de destino, duplicados, opciones escapadas y error sin secreto; todos deben fallar seguros antes de operaciones. La URL válida debe preservar TLS/timeout.
3. B2: evidencia sin contraseñas/token. Redacción de URL detectada aplicada por Codex; no restaurarla. Pipeline de captura debe depurar antes de guardar, conservando comando útil con referencias de variables privadas. Verificar documentos por conteos/rutas, nunca mostrar coincidencias. No afirmar rotación del admin ni de credencial de pruebas; ninguna rotación operativa autorizada por este prompt.
4. B3: migración nueva temporal con DDL/DML exitoso antes de error de ejecución; demostrar que efecto parcial y registro se revierten, lote previo intacto y reintento corregido funciona. ETL: comparar todas las tablas del lote y meta afectadas por contenido reproducible, no sólo dos conteos. Todo sobre PostgreSQL de pruebas explícito.
5. B4: guardar fuente del smoke de wheel, comandos exactos depurados de build/install/smoke desde fuera del checkout, entorno y salidas reales. Manifest SHA256 de código/tests/configuración no secreta probado, y hash del wheel. Si el árbol cambia después, identificar nueva revisión. No atribuir manifiesto nuevo a corrida histórica.
6. Ejecutar regresión en PostgreSQL temporal aislado con nuevas carpetas UTC y comando seguro. Si falta conexión explícita de pruebas, reportar pendiente; no usar credencial encontrada ni .env para pasar suites.

Entrega docs/entregas/CORR01C/ENTREGA.md, matriz B1–B4, fallos previos/nuevos y ejecuciones reproducibles. Conservar dictámenes de Codex y no reescribirlos.

## E00B — sólo documentación, puede elaborarse en paralelo
1. Resolver modelo mínimo de oportunidad/etapas/interés/consentimiento antes de reglas E04. Definir fase concreta, datos y contrato; E05 amplía cotización/pedido/pago.
2. Dependencias E06: contrato/simulación temprano, sincronización después de datos E02/E05. E07 no calcula atribución de campañas/cobros sin eventos y entidad disponibles.
3. Asignar todos F01–F34 y T01–T58 individualmente a fase/subentrega, condición de habilitación y evidencia prevista. Incluir F09/F10/F22–F27, MFA/recuperación y permisos de documentos. Ampliación contractual o núcleo se declara expresamente.
4. Contrato E01 ejecutable por GLM: matriz acción×rol×ámbito, denegación por defecto, sede inicial y migración de datos actuales, política de contactos compartidos/oportunidades asignadas, permisos IA/BI/exportación y preservación de historial. No completar entidades aún inexistentes con datos ficticios en migraciones.
5. Corregir «CI local» si sólo hay pytest local. Mantener paridad básica abierta y métricas sin fuente como no disponibles.
6. Entregar E00B/ENTREGA.md con enlaces/tabla de respuesta D1–D4, contratos y bocetos; no implementar E01. No prometer superioridad comercial universal.

## Cierre
Actualizar índice y continuidad con estados separados. R01 operativo sigue pendiente del propietario y no se considera reparado por redacción. Presentar CORR01C y E00B a Codex. E01 sólo empieza tras ambos dictámenes favorables de alcance técnico/documental; no prometer lanzamiento mientras falten flujos empresariales.
