# GLM — siguiente entrega: E01 y recorridos visibles
24-10-2026. Codex especifica/revisa; GLM implementa/prueba. Raíz H:\git\Agente de reserva V4.
Leer AGENTS, ESTADO, PLAN, MAPA, E00B con dictamen y 13_RECORRIDOS_AGENDA_VENTAS_CATALOGO.md. CORR01D está aceptada para cierre C1/C2; E00B aceptada como base. Inicia E01 por entregas, sin otro ciclo técnico genérico.

## Secuencia concreta
- E01: sedes, roles/ámbitos, backfill seguro, recursos/horarios y selección usable de clientes, conforme E00B. Ámbito también en BI/IA existentes.
- E01-UI: agenda click celda/cita, panel editar/cancelar/reagendar, Día/Semana/Mes, hora/recurso exactos y citas multidiarias. Motivo sólo al solicitar cancelación, no al abrir detalle. Sin 09:00 fija ni IDs manuales. Mantener historia/versiones/horario y permisos. Referencia a servicio tipada; ficha completa con E02.
- E02: catálogo visual producto/servicio/tratamiento con detalles/fotos/variantes/precios, edición frontend y stock por ubicación. E02-ETA para llegadas previstas/recepciones parciales sin sumarlas a stock disponible.
- E03: conocimiento publicado/RAG híbrido, canal, humano, calendario y herramientas de ficha/stock/precio/ETA vivos. Precio/stock no se extraen de un índice desactualizado.
- E05: nombres de productos/tratamientos en ventas, detalle de líneas, retiro/entrega y pago separados; cobros/abonos/saldos y parcialidades. Columna de nombres puede ser mejora UI previa acotada si no depende de esquema nuevo; no anunciar estados/cobros como completos por mostrarla.
Conservar dependencias de reglas E04, ERP E06 y análisis E07; estas prioridades no eliminan el valor empresarial restante.

## Contrato antes de implementar
Declara brecha real, archivos/esquema, permisos, migración y criterios T59–T70 de 13. Backfill no infiere pagos o entregas reales del antiguo confirmed. Mantener IDs/snapshots/historial y señalar dato histórico desconocido. Estados por línea: producto retirado no significa tratamiento realizado. Archivo no elimina operaciones.
No reescribir framework por estilo. Entregar navegación y densidad útil, no tarjetas decorativas.

## Verificación
Pruebas PostgreSQL temporal explícito; proveedores simulados y datos sintéticos por defecto. Navegador real: celda→panel→editar/reagendar/cancelar; Día/Semana/Mes; producto→foto/detalle/precio/stock/ETA; venta→retiro y abono separados; pregunta antes/después de editar precio/descripción.
Capturas 360/768/1440, estado antes/después, resultado persistido tras recarga e historial. Negativos de permiso, concurrencia de stock, conflicto de versión y PII. Seleccionar personas/productos mediante búsqueda, no IDs.
Registrar docs/entregas/<ID>/ENTREGA.md, diseño, código probado/huella, comando depurado, salidas y límites. Las 110 históricas no son ejecución nueva. Rutas 200 no sustituyen recorrido UI.
No producción, mensajes reales, credenciales operativas ni push por inferencia. Una entrega a la vez y dictamen antes de siguiente. Empieza sólo E01, incluyendo el contrato de E01-UI; no intentes implementar todos los puntos a la vez.
