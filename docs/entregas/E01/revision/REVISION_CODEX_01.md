# E01 — revisión independiente 01
Fecha: 24-10-2026. Codex. **DEVUELTA PARA CORRECCIÓN E01-R.**
E01-UI y E02 todavía no se aceptan por esta revisión. Se reconoce avance de sedes, rejilla y nombres de venta; el contrato de aislamiento no está cumplido.

## Verificación
Lectura de entrega, migraciones 0006/0007, scope, rutas, servicios y JS/plantillas. Reproducciones aisladas con Flask test client, identidad/scope/perfil/servicios simulados y URL inválida: no login real, .env, conexión o modificación PostgreSQL. No se reprodujo un guardado real de cita en navegador; el fallo que reporta el propietario debe diagnosticarse con payload/consola/persistencia.
Evidencia encontrada E01: ENTREGA.md y una captura; no logs íntegros/manifiesto de la supuesta corrida 120. Las 120 son resultado declarado de GLM, no ejecución verificada por Codex.

## A1 — P1 — detalle y transición de cita eluden sede
api_appointment_detail sólo pide login y devuelve appointment_detail con notas; api_transition sólo login/CSRF y ejecuta acción sin comprobar agenda.transition sobre sede/cita y propietario. Una prueba con gerente de sede 1 y cita sintética de sede 2 devolvió:
detalle 200 con marca privada de sede 2;
POST cancel llegó al servicio y devolvió 200.
Reproducción con mocks demuestra falta de guardia de ruta, no cancelación real.
Requerir autorización por acción, sede y asignación ANTES de leer notas o mutar, también en contacto→citas y correcciones.

## A2 — P1 — filtros incompletos en API/IA y listas
/api/analytics/overview llama overview sin branch_ids ni permiso específico; reproducción devuelve 200 y argumento branch_ids AUSENTE para gerente de sede 1.
Dashboard agrega global; appointment/stock histories y contacts pueden devolver datos sin permiso de recurso. assistant.ask filtra ventas/top/stock pero citas_hoy/proximas/precio/asistencia/conocimiento no reciben ámbito.
can_any(action) + branch_filter() de todas las sedes mezcla acciones: gerente en sede A y almacén en B puede ver ventas de B mediante filtro que incluye ambas aunque no tenga sales.view allí. Filtrar por acción y recurso en cada consulta/herramienta, no por cualquier membresía. Probar doble rol/sede.

## A3 — P1 — lectura de perfil puede restaurar permisos revocados
organization.get/ensure llama ensure_principal en cada lectura; éste inserta asesor sede 1 a usuarios no admin sin ninguna fila. Tras revocar última asignación, una visita al perfil puede volver a concederla. Backfill debe ser migración/alta explícita una sola vez con procedencia, no reparación de permisos en GET. Comprobar revocación→login/GET repetidos→cero asignaciones, sin usar producción.

## A4 — P2 — inventario UI bloqueado por CSP y permisos incoherentes
inventory.html usa onclick para historial/precio/stock/activar, mientras app devuelve script-src 'self' sin permiso de handlers inline. Fuente de comportamiento: https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP . Sustituir por eventos JS externos; no añadir unsafe-inline para esconderlo.
require('inventory.manage') sin branch_id sólo admite director aunque ACTION_ROLES incluya almacén; g.scope.can sin sede también produce can_manage falso. Productos/price/stock usan aún role admin/user en servicios. Debe comprobarse permiso/ubicación real y mantener compatibilidad explícita, sin habilitar a todos.
La observación CSP es análisis de código y comportamiento documentado, no captura nueva del navegador. El reporte del propietario concuerda con que no funcionan botones; exigir prueba real.

## A5 — P2 — rejilla y guardado requieren prueba de uso, no sólo API
hourCell pinta continuación sólo si la hora inicial es menor que HOUR_FIRST=7; una cita 10:00→día siguiente 11:00 se filtra como existente pero no se pinta en la continuación. Rango fijo 07–20 oculta reservas fuera de ese rango. eventsFor incluye día final aunque termine exactamente a medianoche. Today usa zona navegador en vez de negocio.
No se da por comprobado el fallo concreto de guardar; openNew deja fin vacío y resolveContact busca por texto exacto/nombre, con pérdida potencial de identidad. Probar sin cliente/con cliente/tratamiento, día/semana/mes, hora distinta de09, fin válido, error de red y duplicados de nombre. Reagendar debe precargar cliente/servicio y conservarlos.
No aceptar captura estática o POST directo como prueba del botón Guardar.

## A6 — P2 — backfill y evidencia incompletos
test_e01m crea datos después de migraciones y sólo observa que no hay NULL; no demuestra migración de base previa poblada preservando historial/precios/costos. Ensayar copia sintética anterior a E01 y migrar con comparación.
Guardar salidas íntegras, manifiesto fuente, pasos UI y casos negativos. No borrar pruebas ni rebajar permiso esperado a redirect genérico sin verificar que no hubo cambio/fuga.

## Resolución
Usar premium/15_PROMPT_GLM_E01R_AGENDA.md, después catálogo/variantes de 17 y reglas de16/18 según dependencias. No reabrir CORR01D ya aceptada. Corregir sólo A1–A6, preservar UI útil y demostrar casos. Nuevos módulos por entregas separadas; no fingir cierre empresarial con conteo de tests.
