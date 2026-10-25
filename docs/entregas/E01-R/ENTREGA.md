# Entrega E01-R — Reparación de agenda, permisos por sede, revocación durable y UI bajo CSP

Estado GLM: **lista para revisión** (no autoaceptada).
Fecha: 25-10-2026. Implementación GLM conforme a `docs/producto/premium/15_PROMPT_GLM_E01R_AGENDA.md`; dictamen de origen: `docs/entregas/E01/revision/REVISION_CODEX_01.md` (hallazgos A1–A6). Dictamen Codex de esta entrega: pendiente.

## Alcance recibido

Corrección acotada de A1–A6 de la revisión de E01. CORR01D/E00B permanecen
aceptadas y no se reabren. Sin scoring, catálogo de variantes (E02-A),
transferencia humana (E03-H) u otros módulos: sólo código relacionado con
A1–A6. Entorno: PostgreSQL **temporal y explícito** (clúster local de pruebas
puerto 5439 iniciado para esta entrega; el servidor 5432 del propietario no
se tocó), datos 100 % sintéticos, proveedores simulados, sin `.env`, sin
mensajes reales, sin despliegue.

## Resultado y cambios (matriz A1–A6)

| # | Archivo / causa | Cambio | Caso esperado (evidencia) |
|---|---|---|---|
| **A1** | `entrypoints/web/app.py`: detalle/transición sólo exigían login, sin sede; `appointments_for_contact` sin filtro | `_appointment_branch()` carga identidad mínima; `TRANSITION_ACTIONS` mapea acción→permiso; `require(permiso, sede)` **antes** de leer notas o mutar; acciones desconocidas 400; contacto→citas filtra por `agenda.view`; `scheduling.appointments_for_contact(branch_ids=…)` | Gerente sede A: detalle/cancel/nota/corrección de cita B → 403, cero marca privada, `row_version` intacto (test_a1_gerente_ajeno…) |
| **A2** | `scope.ScopeContext.branches_for(action)` nuevo; BI API sin guardia ni filtro; dashboard global; historial inventario sin guardia; contactos sin guardia; herramientas IA mezclaban sedes | Filtro **por acción** (`branches_for`) en agenda/ventas/BI/inventario/dashboard; `require` en contactos/historial; `assistant.ask(branches={'sales','agenda','inventory'})` y cada herramienta filtra por la suya; `commerce.find_product_by_text(branch_ids)` | Doble rol gerente A/almacén B: ve ventas A (V-formateada) no B; BI filtrada `[A]`; `precio`/`stock` sólo en su ámbito (test_a2_*) |
| **A3** | `scope.ensure_principal` insertaba `user_branch_roles` en **cada GET** de perfil → reponía ámbitos revocados | Los dos INSERT de ámbitos eliminados de `ensure_principal`; el backfill de permisos vive **sólo** en migraciones 0006/0007 (una vez); alta de ámbitos sólo por `/branches` | Revocar última membresía → 3 ciclos login/GET → **cero** filas; usuario nuevo sin ámbito denegado (test_a3 + test_security 403) |
| **A4** | `inventory.html`/`sales.html` usaban `onclick=` inline (CSP `script-src 'self'` los bloqueaba); `require('inventory.manage')` sin sede; `role='admin'` de cuenta | Plantillas con `data-*`; `inventory.js` reescrito con delegación; rutas cargan `_product_branch` y `require(..., sede)`; `_matrix_role()` traduce matriz→rol de servicio; `can_price`/`can_manage` por producto; sede en alta de artículo; `sales.js` reversión por delegación | Botones Historial/Precio/Stock/Activar **ejecutados** en navegador con CSP intacta; almacén ajusta stock de su sede (movimiento auditado), no precio ni sede ajena (test_a4_* + capturas) |
| **A5** | `agenda.js`: rango fijo 07–20; continuación sólo si `startH<7`; día final a medianoche contado; «Hoy» zona navegador; fin vacío; contacto por texto; reagendar sin precarga; `days[0]` pintaba el lunes | Rango dinámico `hourBounds()`; continuación en primer hueco del día; fin 00:00 excluye el día siguiente; `businessToday()` con `data-zone`; fin propuesto +30 editable con error «Indique fecha y hora de fin»; contacto por **ID interno** con etiqueta única `nombre · teléfono`; reagendar precarga cliente/servicio/recurso/versión; cancelar con motivo al pulsar (no popup al abrir); doble envío bloqueado; «+N más» abre el día; `renderDay` usa el día seleccionado (defecto real encontrado por la evidencia: creaba en lunes de la semana) | Guardado desde celda 14:00→14:30 sin y con cliente (Ana duplicada elegida por ID) + servicio; fixture 2030-06-10 14:00–14:30 con UTC persistido 19:00Z; 49 h (13→15 jun) y 23:00→00:00 verificados por API; recarga conserva las citas |
| **A5+** (extra, misma clase CSP) | `agenda.js` `style.cssText`, barras `style="height:…%"` de `dashboard/analytics.html`, márgenes inline de `branches.html` violaban `style-src 'self'` (gráficos a cero) | CSSOM tipado en JS; barras vía `data-bar-h/w` + `applyBars()` en `app.js`; clases `.mt-16/.mt-14/.kpi-range` | Consola del navegador: **0** errores CSP en el recorrido completo (antes 39) |
| **A6** | `test_e01m` creaba datos tras migrar; no probaba base poblada pre-E01 | `test_a6_migracion_preserva_base_poblada_pre_e01`: base sintética en esquema 0001–0005 **poblada** (cita confirmada con historial+nota, producto con precio histórico y costo, venta con línea y movimiento), aplica 0006+0007, compara snapshots exactos | IDs/historial/motivos/precios/costos idénticos antes/después; `branch_id=1` en 5 tablas; 1 ámbito inicial (admin→director); `organization.get` repetido **no** añade ámbitos |

Archivos: `src/crm_premium/entrypoints/web/app.py`, `modules/scope|dashboard|assistant|commerce|scheduling/service.py`,
`presentation/static/agenda.js|inventory.js|sales.js|app.js|app.css`,
`presentation/templates/inventory|sales|analytics|dashboard|branches.html`,
`tests/test_e01r.py` (nuevo, 10), `tools/evidencia_e01r.py` (nuevo),
`.gitignore` (`.pytest_pg/`).

## Pruebas y evidencia

| Ejecución | Entorno | Casos | Resultado | Evidencia |
|---|---|---|---|---|
| Suite íntegra | `.venv` (Python 3.13.1) + clúster PG 18.6 temporal puerto 5439; `CRM_PREMIUM_TEST_URL=postgresql://postgres:***@127.0.0.1:5439/postgres`; DSN con credencial de pruebas local desechable | 120 previas + 10 nuevas E01-R | **130 passed** (258.79 s, salida 0) | `tools/redact_evidencia.py` aplica a salidas si se publican |
| Regresión de rama restaurada | ídem | test_e01r + web_flow + security | **29/29 passed** (verifica que el diff del PR es exactamente lo probado) | — |
| Evidencia navegador (Tarea 1 del prompt: guardar real, no POST manual) | Playwright/Chromium headless contra Flask real con base temporal `e01r_evidencia_ff2e721f` (destruida al final); negocio sintético 24×7 en `America/Guayaquil` (con esa zona, 14:00 de hoy es futuro al ejecutar; explicado aquí por exigencia del prompt) | 6 casos del prompt | **6/6 ok, 0 fallos, 0 errores de consola** | `evidencias/RESUMEN.json`, `evidencias/red.json` (payloads/respuestas reales de red), capturas 360/768/1440 del **flujo guardado y recargado** |

Capturas (flujo, no página estática): `guardar-1440-confirmado.png`,
`recarga-1440-chip.png` (cita visible tras recargar), `recarga-1440-con-cliente.png`,
`semana-1440.png`, `mes-1440.png`, `dia-768.png`, `dia-360.png`,
`inventario-stock-dialog-1440.png`, `inventario-historial-1440.png`,
`inventario-precio-1440.png`.

Comandos depurados:

```bash
# clúster temporal de pruebas (local, trust, puerto 5439; nunca el 5432 real)
"/c/Program Files/PostgreSQL/18/bin/initdb" -D .pytest_pg -U postgres --auth=trust -E UTF8 --locale=C
echo "dynamic_shared_memory_type = windows" >> .pytest_pg/postgresql.conf  # error 487 en PG18/Windows
"/c/Program Files/PostgreSQL/18/bin/pg_ctl" -D .pytest_pg -o "-p 5439 -c listen_addresses=127.0.0.1" -l .pytest_pg/log.txt start

CRM_PREMIUM_TEST_URL="postgresql://postgres:pytest_local@127.0.0.1:5439/postgres" \
  .venv/Scripts/python.exe -m pytest            # 130 passed
CRM_PREMIUM_TEST_URL="postgresql://postgres:pytest_local@127.0.0.1:5439/postgres" \
  .venv/Scripts/python.exe tools/evidencia_e01r.py   # 6/6 ok, consola 0
```

Adaptaciones de pruebas previas (justificadas, sin retirar cobertura):
`test_security.py` ahora espera 403 en `/api/agenda` para usuario sin ámbito
(el 200 dependía de la autoasignación que A3 elimina — denegación por defecto
es el comportamiento exigido); `test_e01.py` usa la firma `branches={…}` de
`assistant.ask` (contrato por acción de A2).

## Hallazgos nuevos detectados durante la evidencia (corregidos aquí)

1. `renderDay` pintaba el lunes de la semana (`days[0]`): crear desde la
   celda en domingo producía `past_datetime` en el lunes pasado. Corregido y
   cubierto por la evidencia (guardado 201 con fecha de hoy).
2. Violaciones de `style-src 'self'` (39 errores de consola): `cssText` en
   `agenda.js` y barras `style="height:…%"` en plantillas dejaban los
   gráficos a altura 0. Corregido con CSSOM/`data-*`; consola quedó en 0.

## Pendientes y límites

- El guardado que reportaba el propietario **se reprodujo, diagnosticó y
  corrigió** por la combinación A4 (botones/CSP) + hallazgo 1 (lunes/DST) +
  carrera de vistas en el harness; la evidencia muestra el flujo completo
  funcionando con persistencia tras recarga.
- La denegación web de rutas de formulario sigue el patrón redirect de la
  app (302 sin cambio en base); los endpoints JSON devuelven 403. Verificado
  sin fuga en ambos.
- `knowledge_docs` no tiene dimensión de sede: accesible con `assistant.ask`
  (guardia de ruta) y devuelve contenido de la organización, no datos de sede.
  Anotado para P06.
- Playwright se instaló **sólo** en `.venv` como herramienta de evidencia
  (requirió `PIP_CERT`/`SSL_CERT_FILE` apuntando a cacert.pem por una ruta CA
  heredada inválida del proceso; registrado, no se tocaron variables del
  sistema). No es dependencia del producto.
- El clúster 5439 es desechable; `.pytest_pg/` ignorado en `.gitignore`.

## Reversión y continuidad

Revertir el merge/commits de la rama `e01-r` restaura el estado E01 sin
tocar datos (los cambios son sólo código/pruebas/documentos; ninguna
migración nueva — la v4 de canal pertenece a V3, no a este repo). `ESTADO.md`
actualizado con E01-R «lista para revisión».

## Revisión

Pendiente. Siguiente paso: Codex contrasta esta matriz contra
`REVISION_CODEX_01.md`, repite las 130 pruebas y/o el recorrido
`tools/evidencia_e01r.py`, y decide aceptación o devolución. No se inicia
E02-A/H1 antes del dictamen.
