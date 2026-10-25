# Contrato cerrado de Lead Scoring configurable por empresa
24-10-2026. Codex diseña/documenta; GLM implementa. Alcance confirmado por el propietario: UNA instalación y base privada por cliente, varias sucursales/usuarios. No SaaS multiempresa ni migración tenant_id universal por copiar un ejemplo. organization_id identifica el negocio local; branch_id/ámbito y service_line_id siguen siendo obligatorios donde corresponda.

## 1. Referencias verificadas y decisión
Consulta oficial 24-10-2026:
- HubSpot permite fit, engagement y combinado, reglas por propiedades/eventos, puntos positivos/negativos, límites, decaimiento, umbrales, probar un registro y previsualizar distribución antes de activar. https://knowledge.hubspot.com/scoring/build-lead-scores
- HubSpot mantiene vista publicada y edición/revisión separadas. https://knowledge.hubspot.com/scoring/manage-lead-scores
- Zoho permite múltiples reglas y muestra componentes positivos/negativos y total en ficha. https://help.zoho.com/portal/en/kb/crm/automate-business-processes/scoring-rules/articles/multiple-scoring-rule

No son normas universales de industria ni justifican que75 siempre prediga compra. Adoptamos UI guiada y cálculo explicable; los pesos son decisión del negocio probada por simulación. Catálogo cerrado/typed es nuestra decisión de producto para evitar señales imposibles, no una restricción atribuida a todos los CRM.

## 2. Pantallas exactas, sin editar JSON
Navegación Comercial → Reglas de leads.
Pantalla A: lista de métodos con línea/sede, versión publicada, borrador, autor y última evaluación. Pestañas por línea de servicio; nunca un umbral único obligado para todos.
Pantalla B: asistente de configuración:
1. Objetivo: reservar / cotizar / venta asistida / compra directa. Rubro y línea del catálogo existente, sedes y horario de atención.
2. Preset Conservador/Balanceado/Atención rápida: clona borrador versionado, no sobrescribe publicación.
3. Señales: tabla «Activa [casilla] | Nombre y explicación | Fuente | Tipo | Condición | Puntos | Vigencia | Tope». Columnas Ajuste/Intención/Negativas separadas. Código interno visible sólo en información avanzada.
4. Pesos Fit/Intención: controles numéricos+slider enlazados, suma100%; límites de categoría y máximo alcanzable visibles.
5. Frío/Tibio/Caliente: sliders+inputs con límites legibles; sin huecos/solapamientos. Elegibilidad y atención clínica en panel separado.
6. Preguntas: elegir desde banco preguntas ligado a señales activas; ordenar, opcional/obligatoria según flujo, respuesta tipada, permiso de ver. No inventar nueva señal libre ni pregunta de IA que cambie el contrato.
7. Acciones: tarea, asignación y alerta internas permitidas; seguimiento externo sólo si su canal/consentimiento/plantilla lo permite.
8. Simular: ficha de ejemplo y muestra de leads autorizados; resultado y desglose antes/después, faltantes, conteos de buckets y acciones simuladas. No persiste score real, envía, asigna ni crea tareas.
9. Revisar/publicar: resumen de cambios/impacto, fecha de vigencia, decisión sobre existentes, permiso y motivo. Publicada inmutable; edición crea nueva versión.

La distribución usa población/fecha/filtros/cobertura visibles. Cambio de slider actualiza preview mediante backend con espera breve y cancelación de petición antigua; no cientos de llamados por arrastrar. Sin leads suficientes: ejemplos sintéticos etiquetados, no distribución inventada.

Ficha de lead: score total y Fit/Intención/penalización, estado de datos, versión, señales activadas con fuente/fecha/cita, acción sugerida y motivos de no contactar. Botón «Simular otra configuración» no altera historial. Corrección humana de una señal exige motivo y autor; no edición directa arbitraria del número.

## 3. Catálogo de señales v1
Registro mantenido por desarrollador mediante cambios revisados; el cliente activa/pondera/selecciona condiciones permitidas. Cada código define categoría, tipo/valores, extractor, datos requeridos, vigencia, repetición/tope, condición, visibilidad, posibilidad de puntuar y ejemplo. No aceptar código desconocido en API ni etiqueta inventada por LLM.

| Código | Tipo | Fuente | Uso permitido |
|---|---|---|---|
| service_matches_interest | bool/null | catálogo+formulario confirmado | Fit; servicio ofrecido coincide con interés |
| service_area_match | bool/null | sede/zona declarada; geocoding opt-in | Fit; no inferir ubicación de IP |
| preferred_modality_available | bool/null | formulario+catálogo | Fit; modalidad/horario solicitado se ofrece |
| requested_appointment | bool/null | formulario o extracción con evidencia | Intención, solicitud explícita |
| asked_quote | bool/null | formulario/LLM con evidencia | Intención, cotización solicitada |
| asked_price | bool/null | LLM con evidencia | Intención, pregunta de precio; no negativo |
| asked_financing | bool/null | LLM/formulario | Intención opcional; no inferir ingreso/solvencia |
| specific_service_interest | enum catálogo/null | formulario/LLM con referencia válida | Elegir línea/señal; no duplicar puntos por nombrar servicio |
| purchase_horizon_days | entero>=0/null | declaración explícita | Intención con bandas permitidas |
| responded_within_5min | bool/null | timestamps del sistema | Intención; emparejar pregunta-respuesta, no reloj del LLM |
| next_step_agreed | bool/null | confirmación registrada | Intención; vigencia del compromiso |
| no_response_7d | bool/null | sistema con salida entregada y sin respuesta | Penalización comercial; respuesta nueva la elimina |
| verified_invalid_contact | bool/null | validación determinista | Penalización o revisión, según configuración |
| outside_service_area | bool/null | zona confirmada+política negocio | No ofrecer servicio local; revisión/alternativa remota si existe |
| requested_no_contact | bool/null | evidencia literal+confirmación de alcance | BLOQUEO de contacto aplicable; no puntos |
| marketing_consent | sí/no/desconocido | registro explícito por canal/finalidad | Elegibilidad; jamás inferido de puntaje |
| verified_spam_or_abuse | bool/null | proveedor/regla revisada | Revisión y bloqueo justificado; no sentimiento del LLM |

Extensión B2B por perfil revisado: industria, tamaño empresa, cargo/autoridad/presupuesto declarados. No habilitarlas automáticamente en dental/colegio/retail. Datos no observados son desconocidos.

Señales propuestas en el ejemplo que NO van al score comercial dental:
- mentions_pain: atención/triage humano según protocolo aprobado, independiente de score/ingreso. No subir prioridad comercial por sufrimiento.
- sent_photos: hecho de adjunto privado, no mérito de compra ni análisis clínico automático.
- age_group/seguro: información operativa restringida cuando necesaria; no mayor prioridad de ventas por edad/salud/seguro ni perfiles comerciales de menores.
- has_current_dentist: no penalización automática por tener proveedor.
- price_shopper_only: no etiquetar intenciones por preguntar tres veces. Puede registrarse conteo objetivo con fuente, sin conclusión despectiva.
- Gmail/.edu/dominio competidor no son descalificadores universales; no default negativo por correo personal/educativo. Criterio B2B específico requiere perfil/justificación y revisión.
No registrar diagnóstico ni fotos clínicas en índice comercial/BI ni usarlos para inferir solvencia.

## 4. Fórmula única de la primera versión
Modo elegido: NORMALIZADO por categoría, no suma y normalización simultáneas configurables.
Fmax = suma de máximos positivos de reglas Fit activas, por grupo mutuamente exclusivo.
Imax = suma de máximos positivos de reglas Intención activas por grupo.
Fobs/Iobs = contribuciones verificadas, con límites y vigencia; desconocido aporta0 y se informa.
Fn =100×Fobs/Fmax; In=100×Iobs/Imax.
Penalización P = suma de magnitudes no negativas de reglas negativas aplicadas una vez.
Total sin redondear = wFit×Fn + wIntent×In − P.
Score = limitar0–100 y redondear HALF_UP al entero sólo al final.
Categoría de cada señal se obtiene del registro, no de un campo libre del cliente. La entrada negativa se captura como «restar15», se almacena magnitud15 y nunca se resta dos veces.

Validación al publicar: pesos>=0 y suma1 exacta; umbrales enteros0<=warm<hot<=100; cada categoría con peso>0 tiene máximo positivo>0; códigos/tipos/operadores/vigencias/tope válidos; bandas numéricas/enum sin doble conteo; alcance y línea existentes; no señales clínicas prohibidas.
Si una categoría no aplica, peso0; no renormalizar pesos silenciosamente. Si todas las señales son desconocidas, score=null/«datos insuficientes», no frío definitivo. Si hay hechos conocidos falsos puede dar0; mostrar cobertura.
La normalización mantiene escala0–100, NO garantiza misma clasificación al añadir reglas: cambia denominador. Toda modificación debe simular impacto y generar versión.

Ejemplo Balanceado v1, sólo para pruebas/punto de partida:
Fit: interés compatible20 + área compatible15 + modalidad compatible15 → Fmax50.
Intención: precio10 + cotización20 + cita30 + horizonte<=30d15 + respondió<=5min15 + siguiente paso10 → Imax100.
Pesos35%/65%, warm50, hot75. asked_financing queda disponible pero inactiva en este preset; activarla cambia configuración y denominador, no altera v1.
Frío0–49; tibio50–74; caliente75–100. No hay huecos y se usa score entero final.
Casos cerrados:
- Fit30/50, Intención70/100, P0 →21+45,5=66,5→67 tibio.
- Fit50/50, Intención100/100, P15 →85 caliente.
- Fit0/50, Intención0/100 conocidos, P0 →0 frío.
- Todas desconocidas →null, datos insuficientes.
- Score85 y baja marketing →85 con envío marketing bloqueado, sin borrar razón del interés.
Umbrales no son probabilidades ni rangos estadísticos universales.

## 5. Vigencia y determinismo
Motor recibe hechos, config_version y as_of UTC explícitos; no consulta al LLM ni reloj global oculto para calcular. Idéntica entrada+versión+as_of produce mismo resultado.
Preset inicial de señales de intención: hasta7d100%; >7 y <=30d50%; >30d0. Cada regla puede tener vigencia/reducción permitida propia. Fit se revalida cuando cambia catálogo/zona declarada; no caduca como un click.
no_response_7d se calcula de mensaje saliente entregado y ausencia de entrada7×24h; no aplicar si no existe salida entregada. Al responder cesa. No sumar infinito por repetir mensajes; deduplicar ID de evento y tope por señal/ventana. Una señal puede tener varias evidencias, una contribución según política registrada.

## 6. Datos y extracción
Entidades conceptuales: SignalDefinition(versionada); ScoringConfig+versions; ScoringRule; QuestionDefinition/selección; LeadSignalObservation; LeadScoreSnapshot; SimulationRun; RoutingDecision/outbox.
Config contiene organization_id local, línea, ámbito, estado/versión/fechas, pesos/umbrales/reglas/acciones y registry_version. Observación contiene oportunidad, código/tipo/valor nullable, fuente/id externo, occurred_at, received_at, evidence_ref/cita mínima, extractor/prompt/model version y confianza declarada. No bool=False por ausencia.
Score snapshot guarda versión, IDs/huella de observaciones, as_of, Fn/In/P/total/desglose/cobertura y elegibilidad separada. No modificar observación anterior: corrección auditada.

LLM sólo propone observaciones tipadas con evidencia verificable. Preguntas del paciente y RAG son datos no confiables, no permisos. Validar JSON/códigos/tipos y que evidencia pertenece al mensaje autorizado; desestimar señal sin evidencia. Confianza del LLM no es probabilidad calibrada: guardar como metadato, no sumar score.
Sistema calcula tiempos/stock/precio/área con herramientas; no aceptar timestamp o disponibilidad inventados por LLM.
Fallback extracción fallida: extraction_status=failed, conservar datos de formulario/sistema y score con cobertura, no bloquear reserva/atención. Una llamada puede devolver borrador de respuesta+señales si se valida; nunca imponer que el score dependa de respuesta generada.

Preguntas guiadas: línea/interés, sede/modalidad, quiere cita/cotización, cuándo desea y cómo prefiere contacto. Banco configurable por perfil; máximo inicial dos preguntas por turno, no repetir respondidas ni impedir servicio porque no dio información comercial opcional. Bot no realiza entrevista clínica para vender.

## 7. RAG y productos
RAG encuentra ficha publicada y condiciones; herramientas consultan precio/stock/variante/ETA actuales. Extracción estructurada proviene del mensaje/formulario; retrieval da contexto, NO es por sí mismo un extractor ni calculador.
No meter la config completa cada turno: enviar sólo códigos activos permitidos/tipos y fuentes necesarias. Medir tokens/latencia; no reextraer mensajes sin cambios. Fuera de alcance/poca evidencia: aclaración breve o humano.
Un cepillo azul corresponde a product_id+variant_id con color azul, foto/precio/stock por sede. Si el cliente pide azul no responder sobre rojo o stock agregado. Compra retail directa puede omitir scoring si perfil lo define; auto_checkout/ruta directa NO es enviar, cobrar o despachar sin aprobación y comprobación.

## 8. Elegibilidad y acciones
Bloqueos no son negativos que se compensen con puntos. No contactar: alcance por canal/finalidad, inmediata supresión de campañas pendientes, auditoría y reactivación sólo explícita. Responder solicitud de servicio y marketing son permisos distintos. Estado dudoso se revisa; no simular consentimiento.
Caliente: tarea/alerta interna inmediata, SLA inicial60min hábiles configurable y asignación elegible. Tibio: tarea24h hábiles; secuencia externa sólo con consentimiento/canal permitido. Frío: sin presión comercial automática, sin negar servicio.
Necesidad de atención clínica se enruta fuera del motor comercial con protocolo aprobado y humano; nunca se retrasa por score bajo.
Acción al cruzar umbral con clave idempotente oportunidad/config_version/transición; no repetir por cada recálculo. Reentrada/cooldown24h configurables, publicación/re-score masivo no dispara campañas sin aprobación.
Simulation no produce outbox ejecutable. Colas durables reutilizan infraestructura del proyecto; no añadir Redis/Celery/ARQ y otro stack sin necesidad. Explicar fallback/no asesor y conservar decisión.

## 9. Versiones, publicación y permisos
draft→preview→published→retired. preview guarda configuración/simulaciones autorizadas, no cambia leads reales. Publicación atómica, una activa por línea/ámbito/instante y precedence sede específica→regla general explícita. Revertir clona versión en nueva publicación, no borra historia.
Leads nuevos usan vigente; existentes mantienen versión fijada y recalculan observaciones con ella hasta reproceso explícito. Re-score bajo demanda conserva snapshot anterior y muestra impacto antes; acciones externas desactivadas por defecto para lote.
Director o permiso scoring.publish publica; analista puede simular agregados autorizados y no editar; asesor ve explicaciones de asignados. No filtrar PII en distribución ni permitir simular lead ajeno por ID.

## 10. Criterios de aceptación específicos S01–S16
S01 algoritmo casos numéricos exactos; S02 rechazo de config inválida/señal desconocida; S03 false vs null y denominador0; S04 enum/bandas sin duplicados; S05 caducidad exacta y eventos tardíos; S06 mensajes duplicados no suman; S07 modelo/prompt/evidencia inválida y fallback; S08 no contacto bloquea acción con score100; S09 dolor/foto/edad no alteran score comercial; S10 simulación sin escrituras/acciones; S11 publicar/concurrencia/reversión/históricos; S12 permisos de sede/lead/distribución; S13 threshold cruzado crea una tarea, no diez; S14 formularios/presets/sliders usables y desglose; S15 cepillo azul sin sugerir rojo/stock agregado; S16 misma entrada/versión/as_of idéntica salida.
Son contratos por implementar/probar en E03-O/E04 y dependencias, no ejecución actual. Ninguna nueva señal sin definición/extractor/eval y revisión.
