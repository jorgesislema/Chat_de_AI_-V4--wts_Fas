# ENTREGA E01 — sedes, ámbitos y agenda con franjas horarias

Implementador: GLM/ZCode. Base: E00B **aceptada** (con 5 precisiones
vinculantes) y CORR01D **aceptada** (cierre C1/C2). Estado: **lista para
revisión**. Alcance: SOLO E01 + contrato de E01-UI; E02/E03/E05 quedan en su
fase según 13_RECORRIDOS_AGENDA_VENTAS_CATALOGO.md.

## Contrato implementado (según E00B §5 y precisiones)

- **Sedes**: tabla `branches`; sede «Principal» id=1 garantizada por
  `ensure_principal` (idempotente, invocado desde organization.ensure) y
  migración **0007_branch_backfill.sql** para bases ya creadas (0006 podía
  correr con organization vacía en bases nuevas — precisión: numeración real
  al implementar, sin editar aplicadas).
- **Roles de ámbito** (`user_branch_roles`, NULL branch = global sólo
  director): director/gerente/asesor/almacén/finanzas/analista. Rol de cuenta
  (admin/user) preservado; admin ⇒ director global (compatibilidad).
  **Denegación por defecto** con matriz `ACTION_ROLES` en
  `modules/scope/service.py` y aplicación en servidor (rutas, no menú).
- **Backfill** transaccional a sede 1 preservando IDs/historial/precios/
  costos; **sin inferir pagos/entregas** de datos históricos (sólo etiqueta
  `branch_id`). Probado: 0 filas con sede NULL tras backfill.
- **Contactos compartidos**: contactos son de la organización (sin sede);
  notas privadas y asignaciones conservan ámbito. Oportunidades: aún no
  existen (E03-O), sin datos ficticios.
- **MFA/recuperación**: recuperación por códigos y MFA TOTP → **E01-B**
  (siguiente subentrega; MFA bloqueante de E08/VPS). Declarado pendiente.

## Cambios de código

- `migrations` → `0006_branches.sql`, `0007_branch_backfill.sql`.
- `modules/scope/service.py` (nuevo): ScopeContext, matriz, assign/revoke
  (revoca sesiones), ensure_principal, list_branches/assignments.
- `modules/scheduling/service.py`: recursos con sede (default 1), citas
  heredan sede del recurso, `service_id` tipado validado contra catálogo,
  listado con filtro `branch_ids`.
- `modules/commerce/service.py`: ventas con sede; listados de
  ventas/productos con filtro por sede; **columna de nombres snapshot**
  (`item_names` desde sale_lines — mejora UI acotada sin esquema nuevo; NO
  introduce estados de entrega/pago de E05).
- `modules/analytics/service.py`: `bi.dim_sede` + `sede_key` en hechos;
  `overview(branch_ids=…)` filtra KPIs/tops/series por sede.
- `modules/assistant/service.py`: herramientas ventas/top/stock respetan el
  ámbito (sin sedes ⇒ «sin datos en su ámbito»).
- `entrypoints/web/app.py`: carga de `g.scope` por sesión; `require(acción,
  sede)` con denegación por defecto en ventas/inventario/análisis/agenda/
  asistente/sedes; rutas nuevas `/branches` (crear sede, asignar/quitar
  ámbito — quitar revoca sesiones) y `/api/contacts/search` (buscador; sin
  IDs manuales).
- UI: `branches.html` nuevo; `agenda.js` — **franjas horarias 07–20 con hora
  exacta al crear (nunca 09:00 fija)**, **citas multidiarias visibles cada
  día que atraviesan** (24/49 h, medianoche), selector de cliente con
  buscador (datalist), selector de tratamiento/servicio tipado en el alta;
  `sales.html/js` — cliente buscado y sede explícita; menú con Sedes.

## Pruebas (PostgreSQL temporal, conexión explícita)

Suite íntegra: **120 passed** (`CRM_PREMIUM_TEST_URL` → servidor de pruebas
aislado 5433; el proyecto usa 0006+0007 sobre la base operativa). Nuevas en
`tests/test_e01.py` (10):

- Backfill E01-M: sin filas NULL por tabla, IDs preservados, etiqueta sin
  inferencia (precisión 3 de E00B).
- Denegación por defecto sin asignación; gerente ve sólo su sede (agenda por
  API); matriz web negativa: asesor vende pero no edita precio ni ve sedes;
  almacén no ve ventas y sí inventario; gerente ve agenda de su sede.
- Quitar ámbito revoca sesiones (R06 consistente).
- BI por sede (150 global → 100/50 por sede; sin sedes ⇒ 0).
- Asistente por ámbito (otra sede ⇒ 0; sin sedes ⇒ 0; director ve todo).
- Buscador de contactos (búsqueda y vacío).
- Referencia tipada a servicio (válida e inválida) y cita multidiaria que
  aparece en ambos días.

Durante la corrida se detectó y corrigió: subconsulta de sede correlacionada
(`sd.sede_key` → PK real `branch_key`), secuencia de `branches` desfasada tras
INSERT con id explícito (`setval` en ensure_principal), `create_product/
create_sale/create_resource` sin sede por defecto, y un test con bloques
duplicados por parches (reescrito limpio). Quedó instrumentación de depuración
eliminada del código entregado (verificado por grep).

## Verificación de servidor y navegador

- Servidor real: las 9 rutas en 200 con sesión admin (incluida `/branches`).
- API web: cita multidiaria visible en Día/Semana del segundo día; creación
  desde celda respeta 09:00 exacta (201, `start_utc=2027-09-02T09:00`).
- Navegador Chromium real: agenda Semana con franjas horarias y menú E01
  (captura `evidencias/agenda_franjas_horarias.png`; 85 chips, 98 huecos).

## Pendientes honestos (no implementado en esta fase)

- **E01-UI completo** (T59–T61): panel lateral con ficha completa del cliente,
  «ver más» del Mes → día, vista recordada, conflicto sin pérdida de
  formulario, capturas 360/768/1440 antes/después y persistencia tras recarga
  de cada acción — recorrido de navegador completo pendiente para la entrega
  E01-UI; lo verificado aquí: franjas/hora exacta, multidiaria (API+render),
  sede en menú y captura de agenda.
- Horarios por recurso (`resource_schedules` creada, sin UI ni validación).
- MFA/recuperación (E01-B); permiso de «Stock ajustar» para Director por
  decidirse (precisión 4 de E00B) — hoy director ✓/almacén ✓.
- Página de sedes no filtra aún usuarios por sede en /users.
- Rotaciones operativas (admin y credencial de pruebas): del propietario.
