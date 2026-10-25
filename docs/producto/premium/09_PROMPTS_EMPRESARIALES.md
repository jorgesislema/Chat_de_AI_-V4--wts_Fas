# GLM: cierre técnico y construcción empresarial por entregas

## Precisión vigente del propietario — 24-10-2026

Prompts15/17/18 y contrato16 concretan y prevalecen en reserva/agenda, variantes/inventario y scoring. E01 está devuelta, cerrar E01-R antes de ampliar implementación. El cliente configura señales de catálogo tipado y preguntas/ponderaciones desde UI; no scripts ni códigos de señal inventados. Sólo instalación privada por cliente. No interpretar «RAG» como autoridad de stock/precio ni normalización como garantía de mantener clasificación tras añadir reglas.
24-10-2026. Codex especifica/revisa; GLM implementa y prueba. Leer 08_ALCANCE_EMPRESARIAL y revisión de CORR01. Trabajar en H:\git\Agente de reserva V4.

## Instrucciones comunes
Conservar código/evidencia previa, una entrega a la vez y aceptación de dependencias. Multisucursal y equipos de más de cinco personas son requisitos del núcleo; no imponer cinco cuentas como tope. Una organización por instalación, código para cliente, PostgreSQL privado y sin suscripción propia.

Contrato antes de modificar, migraciones nuevas, permisos en servidor y servicios compartidos. Base PostgreSQL temporal con conexión explícita; no leer .env ni usar servidor operativo por fallback. Proveedores simulados por defecto. No mensajes externos/despliegue/cambio de credenciales/push por inferencia.

En cada entrega guardar docs/entregas/<ID>/ENTREGA.md, diseño, cambios y pruebas por ejecución con huella del código probado, entorno, comando depurado, fecha, duración, salida íntegra y código de salida. Capturas y pruebas de uso desde UI; casos negativos de permiso. Actualizar estado/índice. No autoaceptarse ni editar dictamen de Codex.

## CORR01B — cierre de correcciones antes de ampliar código
Lee docs/entregas/CORR01/revision/REVISION_CODEX_01.md.
1. Corrige DSN de pruebas: preservar parámetros admitidos al cambiar dbname en conexión admin/temporal, incluyendo TLS/timeout; validar formato soportado sin imprimir secreto. No prometer soporte conninfo si sólo se admite URL.
2. Añade fallos inyectados de migración/ETL que demuestren rollback y lote válido anterior conservado. Una transacción escrita no sustituye prueba de ruptura.
3. Repara procedimiento R01: mecanismo interactivo seguro, sin contraseña en argumento/historial ni SQL mal formado; no rotar producción por tu cuenta. Redacción documental y rotación real son estados separados; ésta queda pendiente hasta confirmación autorizada.
4. Suite PostgreSQL y wheel externo con evidencia reproducible completa; no sólo una línea 90 passed/SMOKE OK. Conserva resultados previos. Reporta pendientes de permisos por documento/sede con honestidad.
Entrega CORR01B para revisión; no implementar módulos nuevos antes del cierre técnico. E00 documental sí puede prepararse.

## E00 — paridad y contrato empresarial; sólo documentación
Inventaría V3→V4 por flujo básico: información, catálogo, contacto, reservas, calendario, canal, humano/pausa, notas y seguimiento. No asumir que V3 estaba completo. Matriz F01–F34 y T01–T58 con implementado/probado/simulado/pendiente. Define contratos/datos/permisos/dependencias de E01–E08 y bocetos de pantallas. No rehacer PR00 extenso ni crear otra app. La finalidad es construir los recorridos de 08 con una base auditable.

## E01 — sedes, equipos, permisos y configuración
Implementa sucursales/almacenes/recursos/horarios/equipos/ausencias y asignaciones; rol independiente de ámbito. UI configura campos tipados y pipelines. Migra núcleo de dos roles sin exponer datos. Director consolidado, gerente sede, asesor asignados, almacén/finanzas/analista con acciones distintas. Servidor filtra API/HTML/IA/BI/exportaciones. No sólo branch_id. Fixture tres sedes/quince cuentas. Criterios T39–T40 y regresión de acceso/agenda.

## E02 — catálogo visual, tratamientos e inventario
UI crea/edita/importa/publica productos/variantes/fotos/precios y servicios con detalle, duración y sedes habilitadas. Lista/galería/ficha y medios privados validados. Stock físico/reservado/disponible por ubicación; recepción, conteo, ajuste, traslado y expiración transaccionales. Foto correcta de variante, costo desconocido NULL y snapshot de precio/costo. No diagnóstico clínico. Fixture 500 artículos, sin descargar medios arbitrarios. Criterios T41–T44.

## E03 — completar básico: atención, catálogo, turnos y plantillas
Bandeja con hilos/identidades/asignación, SLA, tareas, humano y pausa durable probada bajo carrera. Canal/calendario primeros contratados, inicialmente WhatsApp/Google de referencia, simulado hasta prueba externa autorizada. Información usa catálogo publicado con foto/ficha y precio/stock por sede; confirma reserva sólo tras persistencia. Plantillas: edición/versiones/aprobación interna/Meta independientes. Conocimiento publicado/versionado con permisos. Cerrar matriz de paridad sin sacrificar V3. Criterios T10–T18/T45/T55/T57.

## E04 — reglas comerciales editables
Estudio visual con campos tipados, TODOS/ALGUNO, operadores, pesos/topes, decaimiento, umbrales, ámbitos y acciones permitidas. R1 es plantilla editable. Adecuación/intención/urgencia separadas de elegibilidad. Borrador, simulación de impacto sin efectos, aprobación, versión/vigencia, publicación y reversión. Decisión con explicación/evidencia; reglas de asignación por sede/carga/horario y cola sin elegibles. Frenar ciclos. Sin SQL/eval/scripts ni atributos sensibles. Probar administrador cambiando regla desde frontend y efecto real en siguiente lead. Criterios T46–T48.

## E05 — cotización, pedido, cobro y postventa
Oportunidad con artículos/fotos, precio/moneda/impuestos y cotización versionada; aceptación, pedido, reserva/expiración, entrega, abonos/saldo y devolución total/parcial. Descuentos/reembolsos por permiso y aprobación. Portal mínimo con identidad/enlace caducable sin acceso al CRM entero. Tarea de reclamo/recompra. No marcar toda venta pagada sin pago; no añadir fiscalidad/pasarela no contratada. Criterio T49 y regresión T13–T15/T21.

## E06 — primer conector CRM/ERP acordado
Antes de programar adaptador, elegir proveedor con el cliente y documentar API/licencia/permisos/costos. Contratos neutrales y simulación desde E00. Centro de mapeos/entidades/dirección/autoridad/conflictos/frescura y reconciliación. ERP autoridad de catálogo/stock/pedido cuando se configure; V4 conversación/lead. Credenciales privadas, IDs, firma/deduplicación/reintentos y revisión. Respuesta perdida no duplica pedido; revocar no borra datos. Un conector real probado no equivale a cualquier ERP. Criterios T50–T51.

## E07 — análisis gerencial, leads y mercado
BI con sede/equipo/pipeline/regla-versión/inventario/cobros, grano e historia explícitos. UI configura cuadros sobre catálogo de medidas permitidas. Metas/funnel/cohortes/pérdidas/SLA/rotación/quiebre/venta/cobro/margen con cobertura, desglose y exportación coherentes. Alertas producen tareas controladas. Mercado con fuentes cargadas/fecha/comparabilidad, sin inventar estudio. Asistente usa las mismas métricas/permisos y cita fuente; tokens/costos reales vs estimados separados. Evals desde primer prompt. Criterios T52–T54/T56 y R01–R06.

## E08 — recorrido empresarial, VPS y transferencia
Demuestra tres sedes/quince cuentas/500 artículos/dos rubros: cambiar regla e inventario desde UI, consultar foto/ficha, lead explicable, atención/turno/venta/pago, ERP de prueba y cuadro gerencial. Móvil/tablet/PC y teclado, permisos cruzados, carga medida, respaldo externo/restauración y actualización. No sustituir por rutas 200. Entregar código/guías/formación/exportación y límites del proveedor sin dependencia del freelancer. T32–T35/T58 y fases previas aceptadas.

F22–F27 siguen vigentes (IA/failover/costos/evals/seguridad/números/fábrica) y se incorporan con dependencias claras. No posponer seguridad/evals al final. Fábrica se prueba en segunda instalación, no con archivos vacíos. No presentar etapas parciales como la edición empresarial terminada.
