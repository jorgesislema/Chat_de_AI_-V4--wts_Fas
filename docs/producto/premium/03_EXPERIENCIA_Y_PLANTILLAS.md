# Experiencia, pantallas y plantillas

Especificación para GLM; no prototipo implementado. 23-10-2026.

## Decisión visual

Conservar la identidad verde/blanco, tarjetas, barra lateral y agenda existentes. La captura revisada es clara para pocas funciones; Premium requiere mayor densidad útil, navegación agrupada y filtros persistentes. No cambiar de framework sólo para aparentar mayor valor.

Menú: Inicio; Atención (conversaciones, tareas); Comercial (clientes, oportunidades, cotizaciones, ventas/cobros); Agenda; Marketing (campañas, plantillas); Inteligencia (datos, leads, mercado); Conocimiento; Ajustes. Ocultar módulos desactivados y acciones no permitidas, manteniendo autorización en servidor. Buscador global respeta permisos.

Encabezado: negocio/sede, período donde aplique, estado de conexión, alertas y usuario. Asistente lateral disponible desde contexto autorizado. No usar «IA» como sustituto de nombres de acciones concretas.

## Contrato de pantallas

| Pantalla | Contenido | Acción principal | Estados obligatorios |
|---|---|---|---|
| Inicio | 4–6 KPI seleccionables, pendientes, alertas, evolución y acciones | Abrir registros que explican un indicador | Vacío, sin permiso, dato viejo, carga y error |
| Cliente 360 | Identidades, permisos de contacto, oportunidades, tareas, citas y actividad | Crear oportunidad/siguiente paso | Duplicado potencial, datos incompletos, baja de comunicaciones |
| Oportunidades | Tabla/Kanban, responsable, etapa, valor, antigüedad, puntaje explicable | Actualizar etapa con motivo | Conflicto concurrente, pérdida, reapertura |
| Conversaciones | Lista izquierda, hilo central, contexto y acciones derecha | Responder o tomar conversación | IA activa/humana, envío incierto, error, canal desconectado |
| Agenda | Día/semana/mes, recurso, sede, servicio y bloqueos | Reservar o reprogramar | Solapamiento, cierre pendiente, conflicto Google |
| Ventas/cobros | Cotización, líneas, aceptación, pagos, saldo y movimientos | Registrar operación permitida | Abono, devolución, costo desconocido |
| Campañas | Segmento, exclusiones, contenido/versiones, presupuesto, horario | Simular y después aprobar/programar | Sin consentimiento, cuota agotada, plantilla retirada |
| Análisis de datos | Filtros, KPI con fórmula, detalle, comparación y exportación | Investigar desviación | Fuente/lote/moneda/alcance siempre visibles |
| Análisis de leads | Prioridad, señales, evidencia, faltantes y próxima acción | Crear tarea propuesta | Sin evidencia, corrección humana, modelo/regla usada |
| Mercado | Competidores, observaciones, comparativas, fuentes e hipótesis | Añadir evidencia o plan de prueba | Sin fuentes, fuente vencida, estimación y muestra limitada |
| Conocimiento | Documentos, vigencia, permisos, versiones y prueba de respuestas | Revisar/publicar | Rechazo, expiración, reversión |
| Integraciones | Capacidades, estado, última prueba, cola y errores redactados | Configurar/probar conexión | Preparado no conectado, degradado, revocado |
| Administración | Usuarios, roles, auditoría, respaldos, consumos y perfiles | Gestionar permisos o recuperación | Impacto visible, confirmación de acción sensible |

Tabla de datos: columnas configurables, filtros guardados, orden, paginación servidor y exportación con mismo alcance. Exportación grande como trabajo con enlace privado caducable. Evitar descargar todo el CRM para filtrar en navegador. Importación con previsualización, errores por fila, duplicados y resumen antes de confirmar.

Cada gráfico permite ver tabla accesible y su definición. Seleccionar barra/segmento abre los registros filtrados; no mostrar cifras decorativas. Diferenciar «0» de «sin datos». Fecha de actualización visible, con aviso si ETL falla.

## Ventana de modificación de plantillas aprobadas

Dos objetos diferentes: plantilla de mensaje del proveedor y contenido/conocimiento aprobado internamente. Dos aprobaciones distintas: aprobación del negocio y aprobación Meta. El usuario debe ver ambas.

Ventana amplia en PC, pantalla completa móvil. Tres zonas: lista de versiones/estado; editor con encabezado/cuerpo/pie/botones/variables; vista previa con datos ficticios. En móvil, pestañas accesibles. Mostrar cuenta de canal, idioma, categoría, ID externo, versión local, estado proveedor, última sincronización, calidad cuando disponible, uso en campañas y cambios respecto a versión anterior.

Acciones: guardar borrador, validar, probar vista previa, solicitar aprobación interna, aprobar/rechazar según permiso, enviar a revisión del proveedor, sincronizar estado y archivar. «Editar aprobada» crea una revisión local, no sobrescribe la evidencia de la aprobada. No ofrecer botón «forzar aprobación».

Flujo interno: borrador → en revisión interna → aprobada internamente/rechazada → enviada al proveedor. Estado externo independiente: desconocido, pendiente, aprobada, rechazada, pausada, deshabilitada u otro valor documentado. Conservar valor bruto y mapearlo sin inventar equivalencias.

Reglas:

1. Cargar versión base y control de concurrencia. Dos editores no se sobrescriben; comparar y resolver.
2. Validar campos, variables, ejemplos, tipos de botones, medios y límites según canal/API vigente. Vista previa escapa contenido; no permite scripts.
3. Mostrar campañas y automatizaciones afectadas antes de enviar una modificación.
4. Preferir crear variante externa cuando se necesita mantener la anterior en uso. Si se edita el mismo objeto externo, no suponer que la versión previa sigue enviable: consultar estado y suspender envíos afectados cuando no se pueda asegurar validez.
5. Guardar borrador no envía nada a Meta. Envío a revisión requiere permiso; aprobación interna no habilita envío externo.
6. Un webhook repetido no duplica revisión; evento antiguo no revierte un estado reciente. Si el orden no puede determinarse, reconciliar consultando al proveedor.
7. Sólo enviar contenido y variables de la versión externa actualmente utilizable en la cuenta correcta. Si fue pausada/revocada, detener campañas pendientes.
8. Revertir contenido significa restaurar borrador local o seleccionar otra versión aún utilizable; no deshacer remotamente una decisión Meta.
9. Historial conserva autor, motivo, comparación, fechas y respuesta externa redactada. No guardar tokens.
10. Costos y categorías son informativos según fuente/fecha; aprobación y plazo dependen del proveedor.

Para conocimiento interno: borrador → revisión → publicado → retirado. Publicar genera versión e índice asociado; al fallar indexación continúa activa la última versión buena. Cada respuesta cita versión/fuente. Documento «interno» no puede enviarse ni entrar al RAG del cliente por subirlo.

## Campañas y automatizaciones

Preparación: elegir objetivo y segmento; congelar lista de candidatos para auditoría; mostrar exclusiones y costo estimado. Antes de cada envío volver a validar consentimiento, baja, reglas del canal, versión de plantilla y cuota: el consentimiento puede cambiar después de programar.

Simulación muestra destinatarios ficticios o vista previa sin envío. Aprobación separada de edición cuando el equipo tenga revisor; instalación de una sola persona permite autoprobación explícita auditada, sin fingir doble control. Límite de gasto y volumen por campaña/día; botón de pausa global. Reintentos no exceden presupuesto ni duplican entrega.

A/B: asignación estable por contacto, versiones congeladas y objetivo predefinido; no declarar ganador sin muestra y ventana suficientes. Tasas por enviados/entregados se nombran correctamente. Correlación comercial no se presenta como impacto causal.

## Accesibilidad y estados

Validar 360, 768 y 1440 px y zoom 200 %. Teclado, foco visible, Escape/cierre, retorno de foco y etiquetas; ninguna acción sólo por arrastrar, hover o color. Controles táctiles cómodos; tablas con alternativa móvil. Contraste verificable y textos en español.

Los errores conservan el formulario y explican qué hacer. No exponer trazas, secretos o detalles internos. Operaciones largas muestran progreso y resultado real; no simulaciones de «conectado». Pérdida de red no convierte un envío incierto en éxito.
