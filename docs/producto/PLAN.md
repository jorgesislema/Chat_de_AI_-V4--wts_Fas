# Plan de Agente de reserva V4

## Detalle operativo nuevo — 24-10-2026

Inicio único para GLM: premium/21_PROMPT_INICIO_CERRADO_Y_ENTREGAS_UI.md. E01-R primero según dictamen/prompt15. Documentos16–18 de scoring/catálogo se conservan. Documento19 añade H01–H15 de transferencia humana/alarma persistente;20 concreta UI accionable y UIA01–12. E03-H mínimo puede ir tras E01-R sin catálogo si sólo usa hilos/control/outbox/canal simulado, sin declarar todo E03 completo. Un reclamo/especialista/emergencia no depende del puntaje de venta. Datos reales de precio/stock/ETA se consultan por herramientas y ACL; RAG no es su autoridad. Sólo especificación, todavía no nuevas funciones.

## Prioridad vigente — reparar reserva y catálogo antes de scoring

24-10-2026: E01 requiere E01-R por revisión independiente. Prompt15 define guardar cita en navegador, autorización por acción/sede, revocación durable y CSP. Prompt17 define catálogo/variantes con caso azul/rojo y edición real; contrato16 y prompt18 fijan scoring y panel por etapas. Estos detalles prevalecen sobre interpretaciones genéricas anteriores. Mantener E03-O antes E04 y dependencias de ERP/análisis.

Decisión explícita del propietario: instalación y base privadas por cliente; varias sucursales dentro del negocio. No añadir multiempresa SaaS ni tenant_id universal por el ejemplo del chat. Señales comerciales tipadas y controladas; cliente activa/pondera/define umbrales/preguntas permitidas. Dolor/fotos clínicas/edad no son puntos de prioridad de venta; atención clínica y consentimiento son flujos separados.

## Recorridos visibles vigentes — 24-10-2026

CORR01D y E00B aceptadas en sus alcances; E01 habilitada. Leer premium/13_RECORRIDOS_AGENDA_VENTAS_CATALOGO.md y 14_PROMPT_GLM_RECORRIDOS_VISIBLES.md. Agenda accionable/vistas completas; ventas por nombres con retiro/entrega/pago separados; tratamientos y fichas/stock/precios/ETA editables por UI; RAG híbrido con valores vivos. T59–T70 se ejecutan en E01-UI/E02/E03/E05. No son nuevas funciones implementadas por esta documentación.

## Alcance empresarial vigente — 24-10-2026

Esta edición se dirige a varias sucursales y equipos de más de cinco personas; objetivo de ensayo 3 sedes/15 cuentas. F17 y permisos por sede son núcleo obligatorio, superando tablas anteriores de ampliaciones. Una organización por instalación se conserva.
Leer premium/08_ALCANCE_EMPRESARIAL.md, 09_PROMPTS_EMPRESARIALES.md y 10_ACEPTACION_EMPRESARIAL.md: paridad básica, reglas frontend, catálogo visual, stock por sede, venta/cobro, análisis y ERP. F28–F34/T39–T58 complementan criterios. CORR01B cierra defectos/evidencia antes de nueva implementación; E00–E08 desarrolla producto empresarial por dependencias y revisión.

Actualizado: 24-10-2026. La raíz de construcción es H:\git\Agente de reserva V4; el alcance Premium está en premium/00_LEER_PRIMERO.md y documentos 01–06.

Instalación freelancer en VPS del cliente, entrega del código al cliente, sin suscripción propia y mantenimiento opcional. PostgreSQL privado en VPS, modelo estrella, usuarios/administrador desde varios equipos y perfiles clínica, tienda, colegio e inmobiliaria. Preparación de canales no equivale a conectores activos.

## Secuencia

Actualización 24-10-2026 (propietario): arranque por **núcleo funcional ejecutable** en lugar de
PR00 documental extenso como primer paso. Ver docs/producto/premium/07_VISION_EDICION_2000.md.
Se conserva una fase a la vez, ENTREGA.md por fase y revisión antes de la siguiente.

PR00: inventario documental de V4 y fuente V3, diseño de reutilización y estructura.
PR00B: crear estructura ejecutable mínima en V4; reutilizar desde V3 sólo piezas auditadas necesarias y probarlas aquí.
PR01: PostgreSQL y ensayo temporal de migración, nunca sobre producción por defecto.
PR02–PR10: módulos, conectores y entrega VPS según prompts y aceptación del expediente.

Cada fase requiere revisión de Codex antes de la siguiente. Código y pruebas a cargo de GLM; Codex mantiene especificación y revisión. Guardar evidencia en docs/entregas/<ID>/ENTREGA.md y ejecuciones independientes.

## Relación con V3

La base histórica permanece en H:\git\chat-clinica-dental - copia\chat-reserva-V3. Lectura de referencia, sin modificar el proyecto anterior. No copiar sus secretos, bases, entornos ni Git. No limitar Premium con el alcance de tres profesionales/SQLite de la edición básica. GLM documentará qué código reutiliza y la regresión correspondiente; no trasladar toda la aplicación de forma indiscriminada.

## Aceptación

Criterios F01–F21 y T01–T38 del expediente. Datos sintéticos y servicios simulados por defecto. Pruebas externas sólo con recurso de prueba autorizado. Ninguna función Premium aceptada todavía en esta carpeta; no usar aceptación histórica V3 como validación V4.
