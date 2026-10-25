# GLM — E02-A: ficha editable y variante «cepillo azul»
24-10-2026. Codex especifica/revisa; GLM implementa/prueba. Ejecutar después de E01-R aceptada. No implementar scoring aquí. Leer13 y16; una instalación privada por cliente confirmada.

## Resultado cerrado
Un administrador crea «Cepillo dental suave», añade azul y rojo como variantes reales con SKU/atributos/foto/precio y stock por sede. Edita desde la ficha, guarda, recarga y el asistente puede consultar la variante exacta con datos autorizados. Cambiar precio/stock no exige editar código ni reindexar texto.

## Modelo mínimo y migración (sin fijar número antes de ver versiones)
Product: identificador estable, tipo producto/servicio, nombre, categoría, descripción pública e interna separadas, activo, versión.
Variant: product_id, SKU único, atributos tipados (color/talla/presentación), nombre corto, foto/medios, activo, versión. Color en atributo consultable, NO sólo escribir «azul» en notas.
Precio/lista/moneda por variante y vigencia; costo separado con permiso. Balance por variante/ubicación con físico/reservado; movimientos firmados/motivo/actor/idempotencia. Próximas llegadas separadas del balance.
Tratamiento: servicio sin color/stock artificiales; detalle, duración/precio/condiciones/sedes/profesionales. Consumibles opcionales referenciados explícitamente.
Las entidades pueden extender lo existente; no duplicar tabla producto por cada pantalla. Documentar contrato de campos y FK antes de cambio.

Migración de catálogo actual: conservar IDs/precios/costos/historial y crear variante estándar sin inferir color de nombre libre. Stock histórico queda a esa variante/ubicación de origen con conciliación; nunca asignar automáticamente unidades a azul sólo por editar color. Líneas históricas guardan snapshot y referencias válidas, no se reescriben. Transformación de stock se demuestra en fixture poblado previo y transacción/rollback.

## Pantallas y campos
Listado Catálogo: búsqueda por nombre/SKU/atributo; filtros tipo/sede/activo/publicado/stock bajo; botones Nuevo producto/Nuevo servicio. Fila/galería muestra foto y nombre, variantes, precio desde sólo si corresponde y disponibilidad; abrir ficha.
Ficha con pestañas:
1. Información: nombre, categoría, descripción pública, instrucciones/compatibilidades aprobadas, detalle interno restringido.
2. Variantes: filas azul/rojo, SKU, atributos editables tipados, foto, precio/moneda, activo. Crear variante, no borrar historial.
3. Existencias: sede/almacén, físico/reservado/disponible, botón Movimiento con tipo/cantidad/motivo/fecha. Disponible calculado; no modificarlo directamente.
4. Próximas llegadas: proveedor/referencia, variante/cantidad/destino, fecha/rango, estimada/confirmada/en tránsito/parcial/recibida/cancelada, historial y retraso.
5. Publicación: público/interno/enviable/RAG, versión/estado/última indexación y errores.
6. Historial: autor/campo anterior/nuevo/motivo, precio y stock con referencia.

Guardar verifica permisos/versiones y conserva campos ante error. No enlaces decorativos, no onclick inline bajo CSP. Código JS externo y eventos. Etiquetas/casos vacíos/móvil/teclado. Almacén ajusta cantidades en sedes asignadas sin ver costo ni editar precio si no tiene permiso. Director gestiona campos/publicación según matriz.
«Quitar» archiva con aviso de pedidos/reservas; no DELETE de ventas/movimientos. Ningún guardado silencioso ni mensaje de éxito antes de commit.

## Datos exactos de aceptación (sintéticos)
Reloj de pruebas2030-06-10.
Producto Cepillo dental suave, descripción «Cerdas suaves, mango antideslizante», campo interno «Costo de compra» no público.
Variante AZUL: SKU CEP-SUAVE-AZ, color=azul, foto azul fixture local, precio4.50USD; Principal físico3 reservado0, Norte físico1 reservado0.
Variante ROJO: SKU CEP-SUAVE-RO, color=rojo, foto roja, precio5.00USD; Principal físico0.
Llegada prevista azul Principal10 unidades2030-06-20 estimada; hoy sigue disponible3, no13.
Servicio Limpieza dental: duración45min, precio35USD o condiciones configuradas, incluye revisión informativa aprobada, sin diagnóstico automatizado y sin stock ficticio.

## Recorridos obligatorios
CATA01 crear producto+azul+rojo desde UI y consultar tras recarga; no seed directo como sustituto.
CATA02 editar detalle azul y precio4.50→4.80 con historia; rojo sigue5.00 y venta previa sigue4.50.
CATA03 ajuste físico azul Principal3→2 (delta−1, motivo Conteo); Norte sigue1, nadie puede retirar tercera unidad disponible inexistente.
CATA04 archivar rojo: desaparece oferta nueva, referencias históricas persisten.
CATA05 próxima llegada10 no altera físico; recibir4 mueve físico2→6 y remanente6, reintento no suma dos veces.
CATA06 cliente pregunta «¿Tienes cepillo azul?» sin sede: aclarar/usar sede explícita válida; con Principal responder azul, foto azul, cantidad autorizada,4.80 y ETA estimada separada. Nunca ofrecer rojo como azul ni sumar sedes.
CATA07 cliente pregunta «¿Es suave?» → ficha publicada con fuente; consulta de costo interno → no revelar.
CATA08 cambiar stock/precio desde UI y preguntar inmediatamente: nueva herramienta ve valor sin reindexar. Detalle cambia por flujo de publicación y muestra estado real.
CATA09 usuario de Norte no edita ni obtiene stock privado de Principal por ID/API/asistente; prueba negativa.
CATA10 evidencia en360/768/1440, guardar/error/conflicto/recarga y estado persistido.

## RAG y asistente de esta subentrega
Implementar contratos de herramientas de búsqueda tipada y consulta variante/sede. Si el canal/LLM todavía está pendiente, probar con adaptador simulado etiquetado y no anunciar bot externo conectado. E03 conecta motor real después.
Índice contiene texto público/versionado y referencia producto/variante; no autoridad de precio/stock. Adjuntos privados nunca se publican al subir. No agregar un servicio nuevo costoso sólo para una búsqueda básica; decidir mecanismo con dependencia existente y reportar su estado.
Fuentes/ACL antes del retrieval y después en lectura de detalle; inyección en descripción no cambia permisos.
Vender producto retail puede saltar scoring, pero no reserva física/cobro/despacho autorizado.

## Entrega
Tabla requisito→archivo→prueba antes de modificar. E02-A/ENTREGA.md con migración/concilio, salida de pruebas PostgreSQL temporal, manifiesto, capturas y rutas exactas del flujo. Una ejecución por cambio/fallo relevante; no regenerar evidencia antigua. No0 secretos por afirmación sin detector y límites. No producción, .env, mensajes reales, push o cambios de credenciales por inferencia.
Detener al terminar esta subentrega; pendientes de movimientos avanzados/ETA se separan sólo si contrato explícito y no se anuncia completado lo omitido.
