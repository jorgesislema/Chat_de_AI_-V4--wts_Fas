# V4 empresarial: sucursales, reglas, catálogo e inteligencia
Fecha: 24-10-2026. Diseño de Codex; implementación y pruebas a cargo de GLM.

## Decisión vigente
El comprador objetivo tiene varias sucursales y más de cinco personas. F17 multisucursal pasa a requisito del núcleo, superando el catálogo anterior que lo trataba como ampliación. Una organización por instalación se conserva; no es SaaS multiempresa. Objetivo inicial de ensayo: tres sedes, quince cuentas y diez usuarios simultáneos. No es tope de licencia ni capacidad ya demostrada.

No vender el árbol actual como producto empresarial completo. Las correcciones de CORR01 reparan el núcleo; no implementan por sí solas la oferta Premium. La edición superior debe conservar los flujos utilizables del básico y añadir gestión desde la interfaz.

## Investigación oficial
Consultas del 24-10-2026, sin afirmar equivalencia de productos ni límites de ediciones:
- [HubSpot lead scoring](https://knowledge.hubspot.com/scoring/understand-the-lead-scoring-tool?facet1=word): puntuaciones configurables con acciones/propiedades y uso en segmentos, flujos e informes.
- [Zoho administración](https://help.zoho.com/portal/en/kb/crm/crm-reference/product-architecture-and-reliability/articles/how-zoho-crm-administration-and-configuration-works-for-sales-operations): reglas de asignación y flujos configurables.
- [Zoho inventario](https://help.zoho.com/portal/en/kb/crm/manage-inventory/overview/articles/inventory): productos, listas de precios, cotizaciones y pedidos.
- [Odoo reposición entre almacenes](https://www.odoo.com/documentation/19.0/applications/inventory_and_mrp/inventory/warehouses_storage/replenishment/resupply_warehouses.html): operación entre ubicaciones.
- [Odoo ficha de producto](https://www.odoo.com/documentation/19.0/applications/websites/ecommerce/ecommerce_design/product_page.html): multimedia e imágenes de variantes.
- [HubSpot data sync](https://knowledge.hubspot.com/integrations/connect-and-use-hubspot-data-sync?isappinstalled=0): mapeos de datos y conflictos.
- [Salesforce Revenue Insights](https://help.salesforce.com/apex/HTViewHelpDoc?id=sales.revenue_insights.htm): indicadores de equipo, etapas, producto y previsión.
- [Zoho territorios](https://www.zoho.com/crm/lp/territory-management.html): asignación y acceso por territorio.
- [HubSpot help desk](https://www.hubspot.com/products/service/help-desk?level=2): bandeja y objetivos de atención.

Inferencia de diseño: reglas, equipos, catálogo e inventario son capacidades esperables de la categoría. El valor propuesto es conectarlas con atención, reservas y decisiones, con código y VPS del cliente. No afirmar superioridad universal.

## Paridad básica obligatoria
GLM inventaría V3 en lectura y demuestra cada flujo en V4: información publicada; precio/disponibilidad estructurados; contacto e interés; reservar/consultar/confirmar/cancelar/reprogramar; horario/zona/recurso/concurrencia; calendario con reintentos/conflictos; historial y seguimiento; canal contratado con plantillas; humano con pausa durable; notas privadas; acceso individual y adaptación por negocio.
Estado por flujo: implementado, probado, simulado, pendiente o no aplicable con motivo. V3 tampoco se presume completo ni se reutiliza su aceptación como prueba V4. Un flujo básico ausente bloquea los recorridos que dependen de él.

## Alcance y nuevas referencias
F01–F27 siguen vigentes. Extensiones:
- F28: editor visual de reglas comerciales, scoring, asignación y seguimiento.
- F29: catálogo visual, medios y fichas publicables de servicios/tratamientos.
- F30: inventario por almacén y circuito completo de movimiento/reserva.
- F31: campos, formularios, etapas y vistas configurables por perfil.
- F32: cotizaciones, aceptación, pedidos, cobros y postventa.
- F33: dirección por sede/equipo, metas, análisis y alertas.
- F34: centro de integraciones configurable y reconciliación.
Amplían requisitos previos; no los sustituyen ni los declaran implementados.

## Sedes, equipos y permisos
Administrar desde frontend sucursales, almacenes, ubicaciones, horarios, recursos, ausencias y equipos. Rol y ámbito son independientes; una persona puede trabajar en varias sedes. Propietario/director ve consolidado, gerente su sede, asesor sus asignados, almacén movimientos permitidos, finanzas cobros y analista agregados autorizados. Exportar, ajustar stock, descontar, reembolsar y publicar reglas son permisos distintos.
Compartir cliente entre sedes no expone automáticamente notas/documentos privados. El servidor aplica alcance a rutas, búsquedas, herramientas IA, informes y exportaciones.

## Reglas de negocio editables desde frontend
Pantalla con nombre, objetivo, ámbito, prioridad, versión, autor y vigencia. Constructor TODOS/ALGUNO, campos tipados, operadores permitidos, pesos/topes, decaimiento y acciones autorizadas. Datos ausentes no equivalen a falso. No SQL, eval, Python ni scripts ejecutables configurados por usuario.

Separar adecuación, intención comercial y urgencia operativa. Consentimiento/baja/canal son elegibilidad: ninguna puntuación los anula. El administrador ajusta pesos y umbrales; la R1 anterior es una plantilla editable, no fórmula fija. Clasificación de lead depende de reglas explicables, no de probabilidad inventada. No usar atributos sensibles, salud o perfiles de menores.

Borrador → validar → simular → comparar impacto → aprobar → publicar/programar → supervisar → retirar/revertir. Simular indica quién cambia de prioridad/asignación y qué tareas generaría; no modifica ni envía. Guardar señal/evidencia, versión y decisión. Reprocesar históricos es acción explícita. Revertir cambia política futura; no borra tareas o mensajes ya ejecutados.

Ejemplo editable: interés + cotización solicitada + plazo declarado ≤30 días → prioridad alta; asignar asesor habilitado de sede elegida y tarea a 15 minutos hábiles. No disponible → cola y alerta. Sin consentimiento marketing → ninguna campaña aunque puntúe 100. Asignación por sede/especialidad/horario/carga; reparto sólo entre elegibles. Detectar conflictos/ciclos, prioridades y máximo de acciones.

## Catálogo visual y fichas de servicio
Interfaz para crear/editar/importar con previsualización/buscar/filtrar/archivar/publicar. Lista, galería y ficha. Producto: SKU, variante, categoría, unidad, descripción, fotos de variante, atributos, precio/lista/moneda, impuestos, disponibilidad por sede, entrega y garantía aprobada. Fijar precio y costo al cotizar/vender.

Servicio/tratamiento: descripción pública aprobada, duración, profesional/recurso/sede habilitados, precio fijo o desde con condiciones, preparación, inclusiones/exclusiones y preguntas frecuentes. El agente informa y reserva; no diagnostica ni prescribe. Un precio desde no se convierte en total cerrado sin condiciones cumplidas.

Subida/reordenamiento/portada/miniaturas y texto accesible; validar tipo/peso/dimensiones, guardar privado y separar permiso publicar/enviar/RAG. URL temporal sólo cuando canal/proveedor la necesite; no rutas locales ni archivos privados ajenos. Importación de medios externos valida origen y evita acceso a recursos internos.

Bot consulta versión publicada, precio/stock por sede y frescura, y responde con imagen/ficha cuando canal permita. Revalidar antes de confirmar; no usar PDF antiguo como autoridad de precio.

## Inventario administrado desde interfaz
Stock físico, reservado y disponible separados por variante/ubicación. Disponible = físico − reservado; tránsito aparte. Recepción, salida por venta/consumo, devolución, ajuste con motivo, conteo y traslado origen→tránsito→recepción. Un traslado no duplica stock; fallos/reintentos conservan movimientos.
Reserva transaccional con expiración; última unidad concurrente tiene un ganador. Mínimos/máximos, reposición sugerida, cobertura, rotación y quiebre. Proveedores/compras con aprobación por importe. Lotes/series/caducidad activables según rubro.

Dos modos: inventario nativo V4 o ERP autoridad por campo/almacén. Sin doble maestro. Con ERP desconectado o dato vencido: por confirmar, reserva externa idempotente o humano; nunca promesa automática de stock.

## Venta y postventa
Oportunidad → cotización versionada con artículos/fotos y condiciones → aceptación → pedido/reserva → entrega → abonos/cobro/saldo → devolución total/parcial. Permisos de descuento y reembolso. Portal mínimo de aceptación con identidad/enlace caducable, sin acceso general al CRM. Seguimiento, reclamo, recompra y tarea con responsable. No sustituye contabilidad fiscal integral ni implica pasarela no contratada. Venta confirmada no equivale a pago.

## Inteligencia para decidir
Cuadro director con metas vs resultado por sede/equipo, venta neta/cobro/cartera, margen con cobertura de costo, pérdidas, tiempos de respuesta/asistencia y quiebres.
- Leads: fuente, adecuación/intención, tiempo en etapa, falta de siguiente paso, pérdida y cohortes.
- Equipo: carga, asignación, SLA y objetivos, separando volumen/calidad.
- Inventario: rotación, inmovilizado, cobertura, demanda observada y faltantes.
- Mercado: competidores/precios/promociones con fuente/fecha/muestra/comparabilidad.
- Experimentos: hipótesis, responsable, costo, ventana y resultado; no causalidad inventada.

Cada cifra muestra definición, filtro, moneda, fuente, corte y lote. Abrir filas autorizadas, exportar mismo alcance y guardar vistas/informes configurables sobre medidas permitidas. Alertas pueden crear tareas aprobadas.
Preguntas útiles: qué sede pierde cotizaciones y en qué etapa; qué productos se consultan sin stock; qué campaña genera cobros; qué regla prioriza leads que no avanzan. Si falta evento/pago/costo, informar cobertura y dato no disponible.

## Integración CRM/ERP
No obligar a sustituir un sistema que funciona. Un primer conector concreto por cliente, no promesa de cualquiera. Centro con credenciales privadas, prueba, entidades, mapeo, dirección, autoridad, conflicto, frecuencia/frescura y reconciliación.
Entidades según API: contactos, catálogo/precios, stock, oportunidades/pedidos, cobros. IDs externos, firmas, cuotas, outbox, deduplicación, reintentos y cola de revisión. ERP puede dominar SKU/precio/stock; V4 conversación/lead. Confirmar pedido sólo tras respuesta persistida; resultado incierto se reconcilia por clave, no se repite ciegamente. No escribir ERP por SQL directo.
Proveedor/API/licencia/costos se eligen antes de implementar. Simulado primero y entorno externo autorizado después. CSV es importación, no sincronización bidireccional.

## Pantallas y demostración de valor
Inicio gerencial; Bandeja con contexto; Pipeline; Cliente 360; Catálogo galería/ficha; Almacenes/movimientos; Cotizaciones/ventas/cobros; Reglas comerciales; Análisis; Mercado; Integraciones y Administración.
Cambiar reglas/stock/precios desde frontend; ningún flujo normal requiere terminal o editar código. Identidad visual existente puede conservarse, con mejor navegación y densidad útil.

Demo sintética: 3 sedes, 15 cuentas, 500 artículos/variantes con muestra fotográfica, 2.000 oportunidades y dos perfiles. Es objetivo por construir, no capacidad demostrada.
Recorrido: editar/simular/publicar regla → consulta con foto/stock → lead explicable/asignado → asesor cotiza y reserva → humano toma chat → ERP prueba confirma o maneja conflicto → abono/devolución → director abre desglose BI → cambio de precio/regla se aplica a nuevas consultas. Probar móvil, permisos cruzados, concurrencia y recuperación.

## Alcance comercial sostenible
USD 1.500–10.000 es instalación/adaptación de producto terminado, no desarrollo ilimitado desde cero. Cotizar migración, formación, conector y soporte; consumos/VPS por cuenta del cliente. Código y exportación sin bloqueo por mantenimiento. El valor se acredita con los recorridos anteriores, no con cantidad de módulos, gráficos o pruebas unitarias.
