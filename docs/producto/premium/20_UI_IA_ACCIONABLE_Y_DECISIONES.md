# UI empresarial accionable y decisiones sobre scoring
24-10-2026. Diseño detallado para GLM, no pantallas implementadas. Contratos 15–19 vigentes; no abrir una reescritura ni catálogo paralelo.

## Cómo lo hacen las referencias consultadas
HubSpot separa Fit/interacción/combinado, permite probar un registro y previsualizar distribución antes de activar; sus reglas usan propiedades/eventos. Zoho permite componentes positivos/negativos y varias reglas. Salesforce documenta configuración de Fit/Engagement.
Fuentes oficiales:
https://knowledge.hubspot.com/scoring/build-lead-scores
https://help.zoho.com/portal/en/kb/crm/automate-business-processes/scoring-rules/articles/multiple-scoring-rule
https://help.salesforce.com/s/articleView?id=mktg.mktg_data_scoring_setup.htm&language=en_US&type=5
Consulta 24-10-2026. Nuestro catálogo cerrado tipado es decisión de implementación, no una limitación atribuida universalmente a esos proveedores.

## Decisiones para evitar ambigüedad y errores del ejemplo
- Cliente usa casillas, condiciones tipadas, pesos, preguntas y umbrales; no escribe JSON, SQL ni nuevas señales sin extractor/evaluación.
- Contrato16 elige NORMALIZADO por categoría. Mostrar Fit, Intención, penalización, cobertura y total. No implementar simultáneamente suma libre y normalizada ni copiar funciones incompletas del chat.
- Total0–100 no es probabilidad. Agregar reglas cambia denominador y puede cambiar clasificación: siempre simular y versionar. No afirmar que normalización mantiene la misma clasificación.
- Datos ausentes null; observación false conocida es distinta. Registro define categoría/tipo; no puntuar todo enum por ser no vacío. No acumular mensajes repetidos sin tope.
- Dolor/emergencia/adjunto clínico son atención aparte, no puntos para vender. Edad/seguro no determinan prioridad comercial. .edu/Gmail, tener otro dentista o preguntar precio repetidamente no descalifican universalmente.
- No contacto y consentimiento restringen acciones independientemente del score; una categoría fría no significa «se puede enviar publicidad». Iniciativa de servicio y permiso de marketing son distintos.
- RAG recupera contexto; LLM propone señales con evidencia; validador admite hechos y motor determinista calcula. Stock/precio/ETA/timestamps vienen de herramientas, no inferencias del modelo.
- Catálogo de señales por perfil/línea del contrato16. Configurar preguntas sin repetir respondidas, máximo piloto2 por turno, sin bloquear cita por preguntas comerciales opcionales.
- Varias sedes dentro de instalación/base privada por cliente. El ejemplo multi-tenant no autoriza SaaS nuevo. organization_id local y branch/service_line no sustituyen controles de recurso.
- Retail puede ir a compra directa y omitir scoring de venta asistida, pero NO auto-despachar ni auto-cobrar. Nombre de política direct_checkout; evitar que auto_fulfill=true salte pagos/stock/entrega.
- Una llamada respuesta+señales es opción optimizable con outputs validados, no requisito para recibir/guardar cita ni motivo para bloquear fallback.

## 1. Contactos/Oportunidades: centro de trabajo
Lista tabla o Kanban; ambas muestran el mismo filtro autorizado. Filas: inicial/avatar neutro (no inferir género), nombre, sede/responsable, interés, etapa, badge Frío/Tibio/Caliente o Datos insuficientes, score/versión/frescura y siguiente tarea.
Filtros combinables: sede/asesor, línea, clase, etapa, sin respuesta7d, sin siguiente paso, SLA vencido y elegibilidad. Guardar vista y mostrar conteos; no filtros que descargan todo el CRM al navegador.
Kanban por pipeline configurable: Nuevo→Contactado→Cita agendada/Propuesta→Ganado/Perdido según rubro. Mover requiere permiso/versión y motivo cuando cierre; alternativa accesible sin arrastrar. No llamar «tratamiento realizado» a venta ganada.
Click abre drawer Cliente360: datos autorizados; oportunidades separadas por línea, score explicado con Fit/Intent/P y evidencia/fecha; timeline unificado real (humano/IA/correo/reserva/cobro/tarea), adjuntos privados y saldos sólo si existen.
Acciones: Responder/Abrir bandeja, crear tarea, reservar, cotizar, simular regla y proponer seguimiento. «Iniciar secuencia» sólo con motor/canal/plantilla/consentimiento aprobados; antes de eso deshabilitado con causa, nunca éxito ficticio.
Si no hay scoring aún, mostrar Pendiente de evaluar; no pintar caliente inventado para hacer bonita la demo.

## 2. Configurador de método
Contrato16/18 define pantalla completa: selector de línea/sede, preset clonado, tabla de señales activables con tipo/fuente/condición/puntos/vigencia/tope, sliders+inputs Fit/Intent y umbrales, preguntas tipadas y simulador.
Vista previa con población/cobertura/corte y detalle de un lead autorizado. Debounce300ms al cambiar control y no llamada al LLM por movimiento de slider. Cancelar petición antigua para no pintar resultado anterior sobre nuevo.
Conservar borrador al error; validación de campo, publicación por permiso y comparación de cambios. Configuración publicada inmutable, reproceso explícito y sin campañas por simulación.

## 3. Agenda y atención
Cumplir primero15: guardar/reabrir/reagendar/cancelar desde UI y aislamiento. Filtros sede, profesional, tratamiento y recurso/equipamiento (p.ej. sillón), que son entidades distintas.
Marca de origen IA/operador/canal basada en campo persistido; no deducir por texto o número.
Lista de espera guarda servicio, sede, recurso compatible, franjas preferidas, consentimiento para avisos, fecha y prioridad operativa. Cancelación propone candidatos elegibles según disponibilidad y orden/justificación; score comercial puede ser dato auxiliar no criterio de triage clínico. Sugerencia no envía por sí sola. Oferta con vencimiento y reserva atómica: dos aceptaciones del mismo hueco no crean dos citas.
No-show: primera versión «pendiente de confirmar» o «seguimiento recomendado» basada en hechos explícitos; no presentarlo como predicción IA calibrada. Modelo estadístico sólo con dataset/validación por tiempo y medición de calidad, sin uso de atributos sensibles como atajo.
Emergencias/reclamos/especialistas usan bandeja/alarma19, no color de cita ni score comercial como único aviso.

## 4. Inicio gerencial
Período/sede/equipo/moneda y hora de datos visibles. Bloques:
A. Pendientes accionables: solicitudes humanas sin atender, SLA vencido, citas sin confirmar, retiros pendientes y stock bajo. Cada tarjeta abre registros autorizados.
B. Funnel por cohorte: nuevos→calificados→cita/propuesta→atendida/ganada según definición; no mezclar tasas de cohortes con conteo de estados.
C. Operación IA: conversaciones/mensajes respondidos, citas creadas por herramienta, transferencias y resultados; origen y denominador explícitos. «No disponible» hasta tener telemetría.
D. Dinero: aceptado/cotizado/proyección separados de venta neta/cobro/cartera y costo conocido. No inventar ingresos por duración de cita.
E. Metas y comparación por sede/producto/línea con desglose/fórmula y exportación de mismo alcance.
Alertas crean o abren tarea/caso real; no panel decorativo ni porcentajes fijos.

## 5. Catálogo e inventario: caso cepillo azul obligatorio
Contrato17 completo: producto Cepillo suave con variantes azul y rojo, atributos color tipados, SKU/foto/precio propios y balance por ubicación. El color no vive sólo en notas.
Buscar «cepillo azul» abre variante exacta; si sede no elegida, aclarar. RAG explica descripción pública, herramienta consulta precio/stock. Editar4.50→4.80 y preguntar debe dar4.80 sin reindexar precio; rojo conserva precio propio.
Mostrar existencias/reservas/disponible/ETA y mínimos, alerta de stock bajo con umbral configurado. Predicción de agotamiento requiere ventas/días/cobertura, si falta fuente sólo mínimo.
Venta cruzada: relación explícita producto/servicio compatible, por ejemplo kit aprobado para servicio. Regla y catálogo determinan sugerencia; no consejo clínico inventado ni envío marketing sin permiso. Registrar aceptación/resultado antes de atribuir aumento de ventas.
Financiación: opciones aprobadas/vigencia/condiciones, cálculo estructurado cuando aplicable y transparencia; bot no garantiza crédito ni inventa cuotas. Precio por lista/sede/fecha versionado; descuentos con permiso. «Precio dinámico» no habilita cambiar precio autónomamente por supuesta capacidad de pago.

## 6. Bandeja nueva y alarma
Contrato19. Bandeja central con cola/responsables, IA/humano, notas privadas y respuesta, transferencias con motivo. Campana superior en toda pantalla y atención efectiva para retirar pendiente. No esconder alerta al clicar/leer.
En móvil hilo a pantalla completa, contexto en pestaña; teclado/escape/foco, contraste, labels y estados accesibles. Íconos locales o biblioteca con licencia verificada, sin CDN innecesario. Color + texto para frío/tibio/caliente; urgencia de atención distinta de prioridad comercial.

## 7. Analítica de tratamientos
Preguntas verificables: consultado→cotizado→aceptado→agendado→realizado→cobrado, pérdida por etapa y versión de regla; margen sólo con costos completos/cobertura; recurrencia y ausencias por ventana.
Una consulta con varias líneas genera intereses separados sin duplicar ingreso de cabecera. Tratamiento «más preguntado pero menos aceptado» requiere eventos de consulta y cohorte/fecha, no contar palabras de un chat sin evidencia.
Desgloses por sede/profesional/línea/origen con permiso. Vincular cada recomendación a hipótesis, tarea/responsable y plazo; no causalidad inventada.

## Casos UIA01–UIA12 (pendientes)
01 tabla/Kanban mismos registros;02 Cliente360 con pruebas de permiso;03 score explicado y faltantes;
04 sliders/simulación/versiones sin acciones reales;05 origen de cita y filtros tratamiento/recurso;
06 lista espera con dos aceptaciones/una reserva;07 riesgo no-show etiquetado regla, no predicción ficticia;
08 funnel y métricas IA con denominadores;09 ventas/cobros/proyección separados;
10 variante azul/precio vivo/privacidad;11 venta cruzada/financiación aprobadas con consentimiento;
12 campana19 y recorrido móvil/teclado con evidencia. No se han ejecutado por esta documentación.
