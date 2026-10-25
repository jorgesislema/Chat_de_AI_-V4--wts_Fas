# GLM — E01-R: reparar lo básico y demostrarlo, una sola entrega
Fecha: 24-10-2026. Raíz H:\git\Agente de reserva V4. Codex especifica/revisa; GLM implementa/prueba.
Leer AGENTS, ESTADO, PLAN, dictamen docs/entregas/E01/revision/REVISION_CODEX_01.md y documentos13/14. No empezar scoring, ERP o otra reescritura aquí. CORR01D continúa aceptada; sólo reparar E01.

## Resultado obligatorio
Un asesor autorizado guarda una cita desde celda en navegador, la abre, edita/reagenda/cancela y confirma persistencia tras recargar; otro usuario no puede verla/mutarla si está fuera de su acción/sede/asignación. Director y almacén operan sólo lo que la matriz permite. Botones de inventario funcionan con CSP vigente.

## Tarea 1 — demostrar el guardado que falla, antes de reparar
Usa negocio/usuarios sintéticos y PostgreSQL temporal explícito. Reproduce el flujo del usuario, no un POST manual:
- 2030-06-10 14:00–14:30, recurso activo de sede autorizada, título Consulta, sin cliente/servicio.
- Repetir con cliente seleccionado y servicio activo de la misma sede.
- En Día/Semana seleccionar 14:00; Mes seleccionar fecha y pedir hora.
Captura valor real del formulario, consola/red y JSON depurado, HTTP/resultado, registro y recarga. Si falta fin, mostrar error de campo «Indique fecha y hora de fin», no fallo silencioso. Si el error exacto no se reproduce, no inventar causa; documentar combinación probada y completar negativos.
Usa fecha controlada en test y negocio de prueba con horario que incluya intervalo. No parchear validaciones de horario para hacer pasar un caso.

## Tarea 2 — cerrar permiso por recurso y acción
Revisa todas las rutas: agenda listado/detalle/crear/transición/nota/corrección, contactos y sus citas, ventas/reversión, inventario/historial, dashboard/BI HTML/API y cada herramienta del asistente.
Antes de devolver PII/notas o mutar, cargar identidad mínima del recurso y comprobar acción+sede+asignación. Denegar sin devolver contenido. El actor/sede autorizados vienen de sesión, no del JSON.
Filtro de lectura debe ser de sedes autorizadas para ESA acción. Caso obligatorio: usuario gerente A/almacén B puede ver ventas A y stock B, no ventas B. Listado vacío no habilita ID directo.
No devolver agregado global por falta de filtro. No asumir que login basta. Acciones desconocidas se deniegan. Servicios con role admin/user deben adaptarse al contrato de permiso sin pasar admin indiscriminadamente.

## Tarea 3 — no reponer permisos en lecturas
Quitar autoasignación de ensure_principal durante GET del perfil. Backfill una vez en migración/operación explícita; usuario nuevo sin asignación sigue sin acceso. Revocar última membresía, volver a autenticar y abrir dashboard/perfil varias veces: no crea nueva membresía. Cambio de rol/ámbito revoca sesiones.

## Tarea 4 — inventario usable, sin debilitar CSP
Quitar handlers inline onclick de plantillas y usar JS externo con addEventListener/delegación/data-* escapados. No unsafe-inline/eval. Probar Historial, Precio, Stock, Activar/Archivar y cierre de cuadros.
Almacén con permiso de sede puede ajustar stock de esa sede con motivo, no editar precio ni otra sede. Director según matriz explícita. No usar autorización global para acción local.
No construir todavía variantes/fotos de E02: conserva límite visible.

## Tarea 5 — agenda completa en esta corrección
Click celda hora exacta y cita detalle. Inicializar fin razonable según servicio o +30min con fecha completa; usuario puede cambiarlo. Cliente usa ID de selección interna, etiqueta separada; nombres repetidos no seleccionan primera persona, y error de búsqueda no elimina cliente silenciosamente.
Reagendar precarga inicio/fin/cliente/servicio/recurso/version; cambiar sólo hora conserva vínculos. Cancelar sólo al pulsar, no popup al abrir. Mostrar error sin cerrar ni perder formulario; doble click no duplica.
Día/Semana/Mes accesibles y recordados. Rango se amplía si hay citas fuera07–20; 24/49h aparecen por intersección real con cada día, con cierre medianoche excluido del siguiente. Continuación no depende de startH<7. Hoy en zona negocio. No exponer notas privadas en chips.
Mes «Ver más» abre fecha correcta. Selector sede/recurso respeta scope y tratamiento activo/habilitado.

## Pruebas de aceptación con valores cerrados
- Guardado de los tres recorridos anteriores: una fila, datos correctos tras recarga.
- Conflicto mismo recurso/intervalo409 preserva formulario; dos envíos concurrentes un ganador.
- Cliente «Ana» duplicado: selección por ID de la elegida, nunca por primer nombre.
- Cita2030-06-10 10:00→2030-06-12 11:00, perfil24×7: visible tres días; cita23:00→00:00 sólo el día tocado.
- Cita05:00 no desaparece; navegador con zona distinta conserva día del negocio.
- Gerente A intenta detalle/cancelar/notas/BI API de B:403 o404 consistente, cero marca privada/cero cambios.
- Usuario doble rol A/B caso de tarea2; herramientas de citas/precio/conocimiento respetan ámbito.
- Revocación final no reaparece por GET.
- Migración desde fixture anterior a E01 poblado conserva IDs/hashes de historia/precios/costos.
- Capturas y recorrido UI 360/768/1440 con botones ejecutados, no sólo página abierta.

## Entrega y ahorro de iteraciones
Antes de editar, tabla breve «A1–A6→archivo→cambio→prueba». Corrige por causa, no parche por test. Una implementación y una regresión afectada; repetir sólo por fallos/cambios. Si hay bloqueo real, registrar exactamente cuál sin pedir al usuario que repita todo.
Guarda docs/entregas/E01-R/ENTREGA.md, salidas previas/posteriores, manifiesto y evidencia UI con datos sintéticos. Código y tests sólo por GLM. No secretos/.env/producción/mensajes reales/push por inferencia.
No cerrar por «N passed»: lista cada resultado obligatorio y su evidencia. Detener y presentar a Codex; no implementar scoring ni E02 aún.
