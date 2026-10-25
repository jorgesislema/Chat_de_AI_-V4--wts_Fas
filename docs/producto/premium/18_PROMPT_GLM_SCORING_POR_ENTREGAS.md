# GLM — E04, motor y panel de scoring sin decisiones abiertas
24-10-2026. Leer16_CONTRATO_LEAD_SCORING.md. Codex especifica/revisa; GLM implementa/prueba. Instalación privada por cliente, varias sedes; no construir SaaS multiempresa.

## Puertas de entrada
E01-R aceptada; E03-O con oportunidad/señales/consentimiento disponible; catálogo/líneas de E02. Si falta dependencia, documentar exactamente entidad/contrato y presentar esa subentrega; no crear entidades paralelas ni mezclar todo en E04. Se puede diseñar panel mientras se cierran dependencias, sin declarar motor conectado.
El objetivo ahora es el contrato16, no copiar el pseudo-código del chat. Contiene errores/ambigüedades que allí se resolvieron: categoría debe venir de registro, desconocido no false, denominador cambia al activar regla y DNC no es un punto que otra señal compense.

## E04-A — registro, cálculo y simulación (sin acciones reales)
1. Catálogo cerrado versionado de16 con tipos/extractores/reglas permitidas y separación de señales de atención/privacidad. Cliente elige/pondera; API rechaza código/categoría/tipo arbitrarios.
2. Configuración por línea/sede con versión, pesos35/65, umbrales50/75 de preset y reglas exactas del ejemplo16. Sólo modo normalizado descrito. Calcular Fit/Intent/P, coverage, score/level y elegibilidad separados, as_of inyectable; HALF_UP sólo final.
3. Observaciones con referencia/evidencia/fecha/versiones y valor nullable. Extracción LLM propone hechos, validador decide admisión, motor calcula número. No inferir edad/riqueza/salud ni puntuar fotos/dolor.
4. Endpoint de catálogo/registro de métodos autorizados; POST /api/scoring/configs/{id}/simulate acepta versión borrador y lead_id autorizado O señales sintéticas marcadas, as_of y scope. No confiar organization_id/branch_id arbitrarios enviados por navegador.
Respuesta exacta semántica: config_version, registry_version, as_of, fit_raw/max/normalized, intent_raw/max/normalized, penalty, score nullable, level, coverage/missing, breakdown por código con puntos/base/decay/evidencia y elegibilidad/acciones PROPUESTAS. No crear snapshot real, tarea, asignación ni envío por simular.
5. Tests con los casos cerrados de16: 67 tibio,85 caliente,0 frío conocido,null desconocido; denominador0 inválido, no dobles negativos, límites enum, dedup y decay en borde. Prueba mismo input/versión/as_of=misma salida.

## E04-B — frontend usable (depende de E04-A)
Ruta Comercial→Reglas de leads. Pantalla lista, pestañas línea y asistente de nueve pasos de16. Casillas activar/desactivar, campos numéricos puntos/condición/vigencia/tope, pesos y umbrales slider+input con validación accesible, presets como borradores.
Banco de preguntas tipadas ligado a señales; no textarea de «inventa tus reglas». Reordenar preguntas sin código; respuestas capturan hechos y no bloquean reserva por opcionales.
Vista previa con distribución de cohorte autorizada y fecha; sin datos muestra ejemplos sintéticos etiquetados. Control de solicitudes mientras se mueve slider, no llamada a LLM en cada cambio. Desglose y faltantes visibles.
Flujo Guardar borrador→Simular→Revisar→Publicar con permisos y concurrencia. Publicación atómica única por ámbito/vigencia. Históricos fijan configversion; re-score explícito conserva antes/después.
Ficha del lead explica puntos con citas, fuente/fecha/versión y por qué acción está bloqueada. No editar score manualmente.

## E04-C — extracción, recálculo y acciones (sólo con dependencias aceptadas)
Pipeline de mensaje/formulario a observaciones/outbox; retries deduplicados. Extraer sólo señales activas con JSON validado y evidencia que pertenece al mensaje autorizado. Formulario/sistema pueden funcionar sin LLM. Si falla extracción, extraction_status=failed, procesar señales válidas y mostrar cobertura; nunca bloquear guardar cita.
RAG ficha aprobada+herramientas de precio/stock/ETA según17; no retrieval como calculador de score ni precio vectorizado.
Trabajador durable del proyecto, sin introducir varias colas nuevas. Recálculo por nuevo hecho/decay con clock conocido y config fijada; no cada request GET.
Cruce caliente genera una tarea interna y alerta, idempotencia por oportunidad/versión/transición. Marketing bloqueado por baja/ausencia de consentimiento aunque score100. Clínico solicita atención según protocolo fuera del score. Sin asesor disponible cola supervisada.
Nurturing/SMS/voz no conectados se muestran propuestos o pendientes; no inventar envío. Compra directa retail no significa auto-despacho ni auto-cobro.

## Límite de iteraciones y evidencia
Cada A/B/C es una entrega revisable con tabla requisito→contrato/archivo→caso esperado. No iniciar siguiente sin revisión. Ejecutar tests por reglas y negativos reales, no tests que repliquen exactamente una implementación equivocada.
Guardar docs/entregas/E04-A (o B/C)/ENTREGA.md, fixture versionado, pruebas S01–S16, comando/entorno/huella, casos rojos y verdes y capturas reales. Una UI con tablas vacías o JSON pegado no satisface B. No usar conteo histórico como corrida nueva.
No código por Codex; GLM hace todo el código/test. No .env/producción/mensajes reales/push por inferencia ni tenant SaaS añadido. Primero E01-R y catálogo; este prompt no autoriza saltarse los defectos de reserva actuales.
