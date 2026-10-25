# Recorridos visibles: agenda, ventas y catálogo conectado
24-10-2026. Instrucción del propietario. Codex especifica; GLM implementa y prueba. Complementa 08–10 y E00B.

## Estado observado por lectura de código
Agenda ya declara Día/Semana/Mes, click de cita a detalle y acciones de cancelar/reprogramar. Eso no demuestra un recorrido UI aceptado. agenda.js propone 09:00 en celda vacía y eventsFor filtra sólo fecha de inicio: revisar precisión horaria y citas multidiarias. El prompt del motivo de cancelar se construye al abrir detalle, antes de pulsar la acción: corregir en su fase.
Ventas lista número de líneas sin nombres, método de pago y confirmed/reversed; no estados independientes de retiro/entrega/pago. Inventario tiene alta, tipo servicio y precio/stock/activación básicos; falta ficha completa, fotos, edición detallada y próximas llegadas. Son observaciones de fuente, no recorrido de navegador independiente.

## Agenda desde celda
- Día/Semana: celda vacía abre alta con fecha/hora/recurso exactos, nunca 09:00 fija al seleccionar otra hora. Celda ocupada abre cita seleccionada sin disparar cancelación ni pedir motivos antes de elegir acción.
- Mes: día vacío permite alta con fecha y hora explícita; varias citas se eligen por chip/lista, «ver más» abre día/lista completa.
- Panel lateral escritorio y pantalla completa móvil: cliente con buscador, teléfono autorizado, tratamiento/servicio, sede/profesional/recurso, inicio/fin completos, estado, notas privadas e historial.
- Acciones según estado/permiso: editar, confirmar, reagendar, cancelar cita; atendida/no asistió después del fin y corrección administrativa con motivo. «Cerrar formulario» y «Cancelar cita» son acciones distintas.
- Reagendar conserva intervalo/versión, valida horario/solape/recurso, muestra antes/después y persiste al recargar. Cancelar pide confirmación/motivo al pulsar y conserva historial; no borrar reserva ni resucitar cancelada silenciosamente.
- Día/Semana/Mes con Hoy/anterior/siguiente, fecha y filtros de sede/profesional/servicio/estado. Zona visible, vista recordada; móvil inicia Día y permite otras.
- Citas 24/49 h y medianoche visibles cada día que atraviesan, intervalo semiabierto; no perder fecha final. Teclado/zoom 200%, sin depender de arrastrar.
- Error/conflicto conserva formulario; permiso/versionado en servidor. Sincronización externa separada del estado operativo.

## Ventas legibles
Columnas: venta, fecha, cliente, sede, «Productos / tratamientos» con nombres (primeros + más y detalle), cantidades, total/moneda, cobrado, saldo, entrega/retiro y pago separados. Filtros por sede/tipo/fecha/responsable/retiro/saldo. Nombre/SKU/precio como snapshot: cambiar catálogo no reescribe ventas. Totales de cabecera no se duplican al desglosar líneas.

Estados independientes:
- Pago: pendiente, parcial, pagado; reembolso por movimientos auditados. Saldo se calcula desde exigible/pagos/notas de crédito, no desde una etiqueta.
- Producto: pendiente preparación, listo para retirar, parcialmente entregado, entregado o cancelado. Método retiro/entrega y sucursal de retiro explícitos.
- Tratamiento/servicio: pendiente agendar, agendado, realizado o cancelado; no simular entrega de stock para una sesión.
Ejemplos válidos: pagado + pendiente retiro; listo retirar + pendiente pago; retiro con saldo sólo si política/permiso/motivo lo permiten; tratamiento agendado + abono. No marcar entrega y pago juntos por defecto.
Registrar desde UI cobros con importe/método/fecha/referencia/actor/sede e idempotencia; retiro/entrega por cantidad pendiente y referencia permitida. Devolución total/parcial y reembolso explícitos. Venta mixta por línea: retirar producto no realiza tratamiento.

## Fichas de productos y tratamientos
Alta/editar/importar con previsualización/buscar/filtrar/publicar/archivar desde UI. Lista/galería/ficha con fotos por variante, nombre, SKU, categoría, descripción, atributos, unidad, precio/moneda/lista, costo sólo autorizado y sedes.
Tratamiento/servicio: detalle aprobado, duración, precio fijo/desde con condiciones, profesional/recurso/sedes, preparación e inclusiones/exclusiones. Vincular cita, servicio y venta; sesiones cuando corresponda. Bot informa y reserva, no diagnostica/prescribe ni cierra precio desde sin condiciones.
Fotos: portada/reordenar/miniaturas/texto accesible, tipo/peso/dimensiones validados y archivo privado. Permisos publicar/enviar/RAG separados. URL temporal sólo si canal requiere, nunca ruta de disco o archivo ajeno.
No pedir ID manual de cliente/artículo en flujo normal; usar buscador/selector.

## Stock, altas y bajas desde frontend
Stock físico/reservado/disponible/tránsito por variante y ubicación. Cambiar mediante entrada/salida/ajuste/conteo/traslado con cantidad/motivo/fecha/actor, no sobrescritura sin movimientos. Precio/detalle/minimos/fotos se editan con permiso y versión.
«Quitar producto» archiva; no borra historial, ventas ni devoluciones. Si tiene pedidos/reservas, mostrar impacto y resolver antes de retirar de venta. Consumibles del tratamiento se descuentan por operación configurada/autorizada, no por una consulta informativa.

## Próximas llegadas
Desde ficha: proveedor/referencia, variante, cantidad esperada, sede destino, fecha/rango ETA, estado estimada/confirmada/en tránsito/recibida parcial/recibida/cancelada, fuente y responsable.
Atraso/reprogramación con historial. ETA no suma físico/disponible; recepción real por cantidades sí, parcial conserva remanente. Prepedido sólo con condiciones explícitas. Asistente distingue «no disponible hoy; llegada estimada» de compromiso confirmado; no garantiza ETA.

## Inventario y RAG híbrido
Publicar ficha alimenta índice para búsqueda semántica de detalles aprobados con ID/variante/sede/versión/vigencia. Archivar retira recomendaciones públicas preservando historia.
RAG recupera descripción y condiciones; herramientas estructuradas consultan precio/stock/saldo/ETA/disponibilidad vivos con permisos y frescura. Un precio vectorizado no es autoridad después de editarlo. Cambiar stock/precio/ETA debe verse sin esperar reindexación; cambiar detalle actualiza publicación/índice con estado visible.
Fallo de índice mantiene última versión buena o excluye según política, nunca publica borradores/internos. Cliente externo no ve costo/margen/notas; asistente interno hereda permisos.
Pregunta → identificar variante/sede o aclarar → ficha aprobada → datos vivos → respuesta con foto/condiciones/fecha. ERP autoridad prevalece según configuración; desconectado o vencido muestra por confirmar, no disponibilidad inventada.

## Mejora visible y aceptación T59–T70
No aceptar por más colores/tarjetas/rutas 200. Recorrido real de navegador con datos sintéticos y captura antes/después en 360/768/1440 px, recarga e historial. UI más integridad/permiso, no sólo pruebas API.

| ID | Caso exigido |
|---|---|
| T59 | Celda Día/Semana respeta hora/recurso; Mes pide hora y selecciona cita correcta |
| T60 | Editar/reagendar/cancelar desde cita; motivo al pulsar, historial y persistencia |
| T61 | Vistas completas y citas 24/49 h/medianoche; teclado/móvil/zoom y conflicto sin pérdida |
| T62 | Nombres/SKU/tipo/cantidades legibles y snapshots históricos |
| T63 | Pago/entrega separados, retiro pendiente y parcialidades por línea |
| T64 | Venta mixta distingue tratamiento agendado/realizado y producto entregado |
| T65 | Alta/editar detalle/foto/precio/stock por UI; permisos y concurrencia |
| T66 | Archivo con pedidos/reservas conserva referencias y comunica impacto |
| T67 | ETA/reprogramación/recepción parcial; stock sólo aumenta al recibir |
| T68 | RAG ficha aprobada + valores vivos; cambio de precio/stock sin reindexar |
| T69 | Ambigüedad/ERP caído/ETA estimada no causan falsa confirmación ni fuga de costo |
| T70 | UI consulta→ficha→lead→cita/venta→retiro/pago→cuadro por sede |

Son pruebas por construir y ejecutar, no resultados actuales. E01-UI/E02/E03/E05 son fases dependientes; no todo se implementa de una sola vez.
