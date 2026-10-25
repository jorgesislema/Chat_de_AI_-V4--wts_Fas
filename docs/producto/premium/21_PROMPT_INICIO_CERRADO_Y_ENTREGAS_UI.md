# GLM — entrada única y orden de entregas específicas
24-10-2026. Copiar este prompt para iniciar la siguiente entrega.
Codex define y revisa; GLM hace código/pruebas. Raíz H:\git\Agente de reserva V4.

## Primera entrega AHORA: E01-R, sin scoring/catálogo nuevo
E01 está DEVUELTA, no aceptada. Leer AGENTS, inicio vigente de ESTADO/PLAN y:
docs/entregas/E01/revision/REVISION_CODEX_01.md
docs/producto/premium/15_PROMPT_GLM_E01R_AGENDA.md
No releer toda investigación ni reescribir arquitectura para esta corrección. Sólo código relacionado con A1–A6. No crear otra app ni instalar otro frontend.

Antes de editar presenta tabla de máximo una página A1–A6→archivo/causa→cambio→caso esperado. Después implementa y verifica; no emplees la entrega en volver a proponer opciones ya resueltas.
1. Guardar cita desde navegador: fixture2030-06-10,14:00–14:30, sede/recurso autorizados, sin cliente/servicio; repetir con cliente elegido por ID interno y tratamiento válido. Si fecha reloj/horario no admite fixture, configurar sólo entorno sintético correctamente y explicar. Capturar formulario/payload/resultado/recarga; no sustituir por POST manual.
2. Gerente sedeA no lee detalle/notas/historial ni cancela citaB por URL/API. Mismo para contacto→citas, inventario/historial/BI/IA. Permisos por acción+sede+asignación; caso gerenteA/almacénB no ve ventasB. Actor/sede no confiados del JSON.
3. Revocar último ámbito y repetir login/GET no debe reasignar permisos. Backfill una vez, no concesión de permisos en lectura de perfil. Desconocido/sin ámbito denegado.
4. Botones inventario Precio/Stock/Historial/Activar funcionan con JS externo y CSP actual; no unsafe-inline/eval ni cambiar pruebas para permitir fuga. Almacén ajusta sólo cantidad de su sede, no precio/costo ajenos.
5. Día/Semana/Mes y click hora exacta; fin válido propuesto pero editable. Cita10-jun10:00→12-jun11:00 visible tres días bajo perfil24×7;23:00→00:00 no cuenta siguiente. Ampliar rango para05:00; Hoy zona negocio. Reagendar conserva cliente/servicio e intervalo, cancelar sólo al pulsar; error conserva formulario.
6. Ensayo desde esquema anterior E01 poblado, no sólo datos creados tras migrar: conservar IDs/historial/precio/costo y backfill seguro. Evidencia actual completa.

Salida: docs/entregas/E01-R/ENTREGA.md con matriz A1–A6, rojo si corresponde, corrección, comando depurado/entorno/manifest/salida real, y capturas360/768/1440 del flujo guardado/recarga, no página estática. Pruebas PostgreSQL temporal explícito y proveedores simulados. Sin .env, datos de producción, credenciales del chat ni cambios operativos. No mensajes reales ni push por inferencia.
Una ejecución por cambio/fallo relevante; finalizar con regresión afectada. No repetir suite estable sin razón ni generar reportes duplicados. No afirmar éxito por cantidad de pruebas: enlazar cada caso y evidencia. Detener para revisión.

## Después de E01-R aceptada: próximos prompts, uno por entrega
A. E02-A catálogo «cepillo azul»: ejecutar exactamente17_PROMPT_GLM_CATALOGO_VARIANTES.md. No scoring aquí. Crear/editar por UI producto y variantes color/SKU/foto/precio/stock por sede y próximas llegadas. Pregunta de variante exacta no se responde desde notas ambiguas; foto/stock del rojo no responde azul. Costo interno privado. Fuente viva de stock/precio/ETA y detalles publicados para recuperación.
B. E03-H transferencia humana: contrato19. Si catálogo E02 retrasa, H1 puede hacerse tras E01-R sin depender de catálogo, con alcance mínimo de hilos/control/outbox/alarmas y canal simulado. No declarar todo E03 completo por H1.
C. E03-O oportunidades/consentimiento/señales, luego E04-A/B/C del prompt18 y contrato16. Motor, panel y extracción por entregas. No inventar catálogo abierto o usar LLM como calculador. UI20 añade tabla/Kanban/Cliente360 y badges reales cuando exista motor.
D. E05 venta/retiro/pago y E07 informes según13/20 y dependencias de E00B. No retrasar básico por decorar cuadros ni mostrar métricas IA inexistentes.

## Subentregas cerradas para E03-H (al elegir esa fase)
H1: modelo mínimo de conversaciones/mensajes/control y solicitud de atención; disparadores humanos/reclamo/especialista, pausa durable y outbox. Entregable probatorio H01/H02/H06/H07/H08/H09, API simulada sin canal real.
H2: bandeja y campana superior en todas las pantallas autorizadas. Abrir/leer/Tomar NO quita la alarma; primera respuesta humana aceptada por proveedor con ID o atención externa registrada sí marca en atención. Fallo conserva/reabre; nota interna no cuenta. Pruebas H04/H05/H10/H11/H14/H15 en navegador.
H3: configuración de equipos/especialidades/sede/horarios/SLA/escalamiento y protocolo aprobado para posible emergencia. Probar H03/H12/H13, reinicio y ninguna reactivación automática. Prueba real sólo con canal/cuenta de pruebas autorizados; no prometer médico conectado si no lo está.
Cada H conserva motivo/eventos/versión y recibos externos separados. IA no responde comercialmente después del handoff. Una confirmación operacional única no es atención humana. Sonido opcional no afecta contador.

## Reglas de producto que NO quedan a criterio del implementador
- Scoring16: sólo normalizado, Fit35%/Intent65% y umbrales50/75 como preset editable; señales cerradas, negativas restadas una vez, desconocido null, evidencia/decay/versiones/coverage y simulación sin efectos.
- Dolor/foto clínica/edad no son puntaje comercial: activar atención por protocolo. Baja/consentimiento no se compensan con score. No descalificar Gmail/.edu de forma universal.
- RAG recupera ficha; herramientas responden precio/stock/ETA y permisos. LLM extrae candidatos con evidencia y esquema; motor calcula. No entrevista obligatoria para reservar.
- Retail compra directa no significa auto-cobro ni auto-despacho. Precios/financiación aprobados; sin estimar solvencia ni modificar precio autónomamente.
- Instalación/base privada por cliente y sucursales; no SaaS multiempresa nuevo por ejemplo pegado.
- 120 pruebas históricas no son nueva verificación ni evidencian UI. E01-R debe cerrar guardar y permisos antes de nuevas funciones.
