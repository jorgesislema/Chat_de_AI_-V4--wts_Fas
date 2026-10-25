# Bandeja humana y alarma superior: contrato cerrado para GLM
24-10-2026. Especificación de Codex, no implementación. Complementa 13–18. E01 continúa devuelta a E01-R; no sustituir su reparación por este módulo.

## Resultado observable
El cliente escribe «quiero hablar con una persona/especialista», presenta un reclamo o señala una posible emergencia: se crea solicitud durable, se pausa la respuesta autónoma y aparece una alarma superior para el equipo autorizado. La alarma desaparece del grupo de pendientes cuando hay atención humana efectiva registrada, no al abrir, marcar leída, asignar o pulsar Tomar chat.

Prioridad de atención y score comercial son cosas distintas. Un lead frío, sin puntuar o que no quiere publicidad puede necesitar atención prioritaria. La transferencia no depende de venta, financiación, seguro, edad, foto clínica ni puntaje.

## Dónde y cómo se ve
Cabecera global de toda pantalla autenticada: icono con texto «Atención humana pendiente (N)» y número por prioridad. No mostrar conversaciones de otra sede ni su existencia mediante contadores globales. Texto/forma además de color.
Al pulsar abre lista: cliente autorizado, canal/cuenta, sede, motivo público al equipo, prioridad, tiempo de espera, responsable/cola y botón «Abrir conversación». Orden: atención urgente, reclamo, especialista/humano, resto; dentro, fecha de solicitud. Prioridades son configurables por protocolo y no diagnóstico IA.
Bandeja: filtros Mis chats/Sin asignar/Mi equipo/En espera/En atención, sede/canal/motivo/SLA. Hilo identifica Cliente, IA, Humano y Nota interna con texto/icono. No basta color.
Panel lateral: identidad, contactos autorizados, servicio/producto/interés, tareas, contexto de reserva/venta, y resumen interno con fuentes. Botones Tomar, Reasignar, Responder, Nota interna, Resolver, Devolver a IA; permisos y estados claros.
Sonido opcional configurable por usuario y disponible tras interacción del navegador; por defecto no necesario para operar. Silenciar sonido NO borra alerta. Sin popups intrusivos ni destellos. Aviso «conexión perdida» si no se actualiza; no mostrar 0 pendientes por fallo de red.

## Disparadores y fallback
Tipos cerrados: requested_human, requested_specialist, complaint, possible_emergency, unresolved_request, tool_failure_requiring_human, operator_requested.
Guardar mensaje/acción que lo origina, fecha y regla/versión. Mensaje explícito/botón deriva por regla determinista antes de necesitar LLM. Extracción puede proponer un motivo con evidencia y esquema validado; no decide que un dolor es diagnóstico ni reemplaza protocolo profesional. Si LLM falla y el texto/botón pide humano, la solicitud sigue funcionando.
Un reclamo no es spam por tono negativo. Pedir especialista no exige preguntar presupuesto. Si varias categorías coinciden, un episodio y varios motivos, prioridad mayor aplicable; no varias alarmas iguales.
Posible emergencia usa texto de contingencia aprobado por el negocio y deriva a atención humana/protocolo local. No diagnosticar ni prometer presencia inmediata si no hay profesional. No dejar una respuesta de seguridad urgente esperando al scoring o recuperación documental; su contenido debe revisarse por responsables del negocio antes de activar.
No hay envío de avisos externos a trabajadores por defecto; alarma interna. Email/SMS/llamada requieren configuración y autorización por canal.

## Estados separados
Conversación: IA_ACTIVA → ESPERANDO_HUMANO → HUMANA → CERRADA o DEVUELTA_IA.
Solicitud de atención: PENDIENTE → ASIGNADA → EN_ATENCION → RESUELTA/CERRADA_CON_MOTIVO.
Recibo del mensaje externo: en cola/enviado/entregado/error/resultado desconocido, independiente.

- Abrir hilo: sólo lectura; solicitud permanece pendiente.
- Tomar: reclamar responsable de forma atómica/versionada, cambia a ASIGNADA/HUMANA; IA ya estaba pausada. Alarma pendiente permanece hasta atención efectiva.
- Atención efectiva: primera respuesta humana aceptada por proveedor con ID externo, o registro explícito de atención por llamada/presencial con responsable, fecha, medio y resultado. Borrador, nota interna, clic, mensaje IA y estado «en cola» no cuentan.
- Al registrar atención: retirar del contador «sin atender», mostrar estado En atención y responsable. El recibo «enviado» no se etiqueta como entregado si no hay confirmación.
- Fallo de envío: no atender por un texto que no salió. Si proveedor después notifica fallo definitivo del único intento de atención, reabrir pendiente/alerta y conservar evidencia anterior.
- Nuevo mensaje que vuelve a requerir atención, o reapertura de caso resuelto: nueva condición pendiente según evento/política; nunca borrar solicitud previa. No duplicar por webhook repetido.
- Resolver requiere respuesta/acción registrada o cierre excepcional con permiso/motivo (p.ej. duplicado verificado), auditado. No botón global «borrar todas» ni TTL que quite alarma sin atención.
- Devolver a IA siempre explícito con permiso/motivo; resolver no reactiva IA automáticamente. Para protocolo de reclamo/urgencia, exigir resolución/permiso definidos por negocio antes de devolución.
- Si operador se desconecta antes de atender, arrendamiento vence y vuelve a cola; alarma no desaparece. Sin personal habilitado, queda pendiente y visible a supervisor autorizado con aviso de disponibilidad real.
- Toda condición persiste al reiniciar servidor o navegador.

## Transacción y carrera IA/humano
request_handoff registra entrada/episodio/motivos, incrementa versión de control/response_epoch, pausa IA, invalida tareas de salida antiguas y crea evento de alerta/outbox en transacción.
Generación LLM no mantiene transacción abierta. Trabajador de envío revalida control y versión en el punto de despacho y se coordina con toma humana; si no coincide, descarta borrador IA. No basta comprobar sólo al empezar a generar.
Si proveedor ya aceptó un mensaje antes de la toma puede llegar después: mostrarlo como envío previo, no prometer retiro remoto.
Confirmación automática de transferencia, si se usa, es una única respuesta operacional autorizada e idempotente; no sigue conversación comercial ni afirma que un humano ya está conectado. Mensajes siguientes se guardan para operador, sin reactivar IA.
Dos operadores pulsan Tomar: un ganador, otro conflicto claro sin enviar. Webhooks/recibos reordenados no hacen retroceder estado; reconciliar estado incierto. Sin «exactamente una entrega» prometida si proveedor no soporta verificación/idempotencia.

## Datos/servicios mínimos
Reutilizar modelo conversations/messages y outbox del proyecto; si no existen, crearlos en subentrega E03-H1 mínima sin fingir todo E03.
HandoffRequest: conversación/episodio, sede/equipo, motivos, prioridad, fuente/evidencia_ref, creado, asignado, atendido, resuelto, actor, respuesta humana vinculada, row_version.
ConversationControl: modo, responsable, response_epoch y versión. HandoffEvent inmutable para transiciones. Message: autor/tipo/canal/ID externo/estado. Consentimiento, canal y permisos se validan aparte.
Clave única episodio+disparador lógico, deduplicación por ID externo; no un booleano efímero guardado en frontend.
Endpoints conceptuales autorizados: listar cola/contador, solicitar, tomar, reasignar, responder, resolver y devolver; servidor obtiene actor/ámbito, no los acepta confiados del navegador. ACL antes de devolver hilo o nota.
Alarma se actualiza mediante mecanismo existente de eventos o polling inicial cada 5 s; evitar introducir nueva plataforma por una campana. Comprobar recuperación al volver de pérdida de red. No exponer PII en avisos de escritorio fuera de la app.

## Reglas de atención editables desde frontend
Ajustes→Atención humana: motivos activos (solicitud explícita de humano siempre operativa), equipos/especialidades/sedes, horario, SLA interno por tipo, supervisor de escalamiento, texto de fuera de horario aprobado y política de notificación.
Guardar borrador, validar destino, probar sin enviar y publicar versión. Umbral temporal de SLA usa horario/rubro; valores piloto son configurables, no promesa clínica ni SLA contractual.
Escalar vencimiento aumenta prioridad/avisos según configuración, no inventa asesor disponible ni cierra el caso.

## Casos H01–H15, por ejecutar
H01 «Quiero especialista» crea una solicitud/alarma, pausa IA.
H02 «Quiero reclamar» se enruta a responsable de reclamos aunque score0.
H03 Posible emergencia sigue protocolo aprobado y no espera scoring/LLM.
H04 Abrir/leer/Tomar no elimina pendiente; respuesta humana operacional sí.
H05 Nota interna/borrador/mensaje IA no cuentan como atención.
H06 Reinicio conserva solicitud/pausa/contador.
H07 Carrera generación→toma descarta salida IA pendiente; registra envío ya aceptado antes.
H08 Dos operadores toman, uno gana; segundo no puede responder como propietario sin permiso.
H09 Webhook repetido/reordenado no duplica ni revierte.
H10 Error de envío conserva/reabre alerta sin falso atendido.
H11 Gerente A no ve hilo/contador/motivos de B; doble rol filtra por acción/sede.
H12 Fuera de horario y nadie disponible mantienen cola/supervisor; no promesa de conexión inmediata.
H13 Devolver a IA exige acción/motivo; resolver no reactiva sola.
H14 Backend caído muestra desconexión; al volver resincroniza sin falso cero.
H15 UI 360/768/1440: campana en todas las pantallas, contador clicable y evidencia antes/después de atención.

## Referencias de investigación, no implementación
HubSpot permite guías y rutas de transferencia configurables:
https://knowledge.hubspot.com/customer-agent/set-up-and-customize-the-customer-agents-handoff-process
Salesforce documenta supervisar conversaciones y transferir a un representante:
https://help.salesforce.com/s/articleView?id=service.omnichannel_supervisor_ai_agents_tab.htm&language=en_US&type=5
Consulta 24-10-2026. La semántica exacta de nuestra alarma es decisión propia y se prueba con H01–H15.
