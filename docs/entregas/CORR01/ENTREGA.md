# ENTREGA CORR01 — correcciones de la auditoría Codex 24-10-2026

Implementador: GLM/ZCode. Origen: `docs/entregas/AUDITORIA_CODEX_20261024/`
(REVISION_CODEX.md + EVIDENCIA.md + PROMPT_CORRECCIONES_GLM.md, no editados
por GLM). Estado: **lista para revisión independiente**. Sin autoaceptación.

## Contexto y procedencia del árbol

El árbol contenía, además de PR00B, los módulos commerce/analytics/assistant
construidos a petición directa del propietario en el mismo día («podemos
poner ventana con análisis de datos… inventario… precios… chat interno…»),
sin entrega registrada y con la suite en rojo (7 fallos) al iniciarse CORR01.
Ese trabajo queda absorbido y corregido por esta entrega; no había autorización
documental previa de esa expansión y se registra aquí su procedencia real.

## Matriz R01–R11

| R | Estado | Resumen con evidencia |
|---|---|---|
| R01 | **Resuelto en docs; rotación PENDIENTE del propietario** | Valor de la contraseña temporal eliminado de ESTADO.md y PR00B/ENTREGA.md (grep final: 0 apariciones en Markdown; el valor existió también en el chat de la sesión). Incidente y procedimiento: ver §R01 abajo. No se declara rotada: no hay evidencia autorizada. |
| R02 | **Resuelto** | ETL: la venta revertida conserva fila POSITIVA en su fecha y añade COMPENSATORIA en `reversed_at` (UNION ALL). Asistente: neto por momentos (venta@created_at, reversión@reversed_at). Pruebas: `test_r02_*` (neto 0, +100/-100 en fechas propias, -100 hoy con venta antigua) y `test_reversion_conserva_positivo_y_compensa` (350→0). Sin migración nueva: `sales.reversed_at` ya existía; el cambio es de ETL/consulta, documentado aquí. |
| R03 | **Resuelto** | `build_window_policy` valida el intervalo completo: por cada fecha local tocada, el fragmento debe caber en [apertura, cierre] en día permitido; cierre exacto permitido (≤ al segundo). Pruebas: cruce de noche rechazado, 17:00:30 rechazado, 17:00 exacto permitido, fin de semana rechazado, 23:59:00 permitido / 23:59:30 rechazado, 24×7 sin política (49 h permitidas). DST ya cubierto en test_timeutil (inexistente/ambigua Madrid). |
| R04 | **Resuelto (con límites declarados)** | `/assistant` muestra por defecto SOLO el historial propio; `?scope=global` es exclusivo de admin. Pruebas con dos usuarios y marca única (ausencia de datos ajenos verificado). Pendiente Premium: knowledge_docs sin permisos por documento/publicación; herramientas leen agregados sin permisos por sede (no hay sedes aún). |
| R05 | **Resuelto** | `POST /settings` ahora exige admin (prueba: usuario ordinario no cambia nombre/zona/moneda). Matriz honesta de permisos del núcleo en §matriz. |
| R06 | **Resuelto** | `set_user_role` revoca todas las sesiones en la misma transacción; prueba: token muere tras promoción. |
| R07 | **Resuelto** | Tras login fallido se reemite el PAR cookie+formulario coherente; prueba: incorrecta→correcta sin recarga da 302; token ajeno sigue dando 400. |
| R08 | **Resuelto** | BI/asistente excluyen `es_demo`/`origin='demo'` por defecto con opt-in visible (`?demo=1` en analítica; `include_demo` sólo admin en asistente). Migración **0005** añade `sale_lines.unit_cost` (snapshot; NULL=desconocido, sin backfill). ETL usa el snapshot, nunca el costo actual (prueba: venta con costo 10, producto cambia a 99, BI sigue 20). Tops separados por tipo (prueba con 9 servicios + 1 producto). «cobros/abonos/pagos/recaudación» → herramienta `no_disponible` honesta; ventas≠cobros documentado. |
| R09 | **Resuelto** | conftest reescrito: opt-in explícito `CRM_PREMIUM_TEST_URL` (sin leer .env ni usar DATABASE_URL), DSN compuesto con `urllib.parse`, limpieza en `finally`. Entregas/estado actualizados sin borrar historia; corrida roja conservada junto a la verde. Conteo nuevo: **90 pruebas ejecutadas** (no se cuentan los 47 históricos ni funciones AST). |
| R10 | **Resuelto** | Migraciones movidas al paquete (`src/crm_premium/migrations/operational`; registro por nombre de archivo ⇒ sin re-aplicación). pyproject empaqueta plantillas/estáticos/migraciones. Prueba real: wheel instalado en venv FUERA del checkout, smoke OK (migraciones + login renderizado + estáticos). Locks ordenados por id ascendente en venta y reversión; prueba A,B/B,A concurrente sin deadlock y stock exacto. |
| R11 | **Resuelto** | Documento 07 corregido: franquicia oficial de 1.000 mensajes de servicio/número/mes (FAQ oficial, 24-10-2026), tarifas por categoría/mercado con vigencia, costo real vs estimación, sin motor tarifario fijo; «supera a todas» convertido en objetivo declarado con comparación por demostrar. |

## R01 — incidente de credencial y procedimiento de rotación

**Incidente**: la contraseña temporal del usuario `admin` quedó escrita en
docs/producto/ESTADO.md y docs/entregas/PR00B/ENTREGA.md, y fue mostrada en el
chat de construcción. No hubo git, commit ni push (sin historial de versiones
que depurar). El valor fue redactado; la constancia del incidente es esta
sección. GLM no probó la contraseña publicada ni puede declarar su rotación.

**Procedimiento seguro para el propietario (rotación obligatoria):**
1. Usuarios de la aplicación (vía interactiva CORR01B): desde la raíz del
   proyecto, `python -m crm_premium rotate-password admin` (o sin argumento
   para que pregunte). La contraseña se lee dos veces con getpass — nunca en
   argumentos/historial ni impresa —, valida ≥12 caracteres y revoca TODAS
   las sesiones del usuario. Alternativa con sesión abierta: Ajustes →
   «Mi contraseña» (mismo efecto).
2. Alternativa sin entrar: desde la raíz del proyecto,
   `python -m crm_premium create-admin <nuevo-usuario>` y desactivar `admin`
   desde Usuarios.
3. Verificar en la tabla `sessions` que no queden sesiones activas del admin.
4. Credencial de PostgreSQL (sólo si se considera comprometida; no fue
   publicada en documentos): abrir `psql -U postgres -h localhost` y usar
   `\password postgres` — pide la nueva contraseña de forma interactiva, sin
   historial ni argumentos. Después actualizar `.env`. Nunca usar `psql -c`
   con la contraseña en la línea de comandos. (CORR01B repara aquí el SQL
   defectuoso y la contraseña en línea del texto anterior.)
5. Confirmar la rotación al revisor para cerrar R01 con evidencia.

## Matriz de permisos del núcleo (honesta)

| Acción | admin | usuario |
|---|---|---|
| Agenda: ver/crear/reprogramar/cancelar/confirmar/asistencia/notas | ✔ | ✔ |
| Corrección administrativa de citas | ✔ | ✖ |
| Contactos: ver/crear | ✔ | ✔ |
| Ventas: registrar | ✔ | ✔ |
| Ventas: revertir | ✔ | ✖ |
| Inventario: ver | ✔ | ✔ |
| Inventario: crear/precio/stock/activar | ✔ | ✖ |
| Analítica: ver | ✔ | ✔ |
| Analítica: reconstruir BI | ✔ | ✖ |
| Asistente: preguntar y ver SU historial | ✔ | ✔ |
| Asistente: historial global (`?scope=global`) y `include_demo` | ✔ | ✖ |
| Ajustes del negocio (nombre/zona/moneda/horario) | ✔ | ✖ |
| Usuarios: gestión | ✔ | ✖ |

Pendientes Premium (no fingidos): permisos por sede/responsable, MFA,
recuperación de cuenta, permisos por documento de conocimiento, exportaciones.

## Cambios de código

- `modules/organization/service.py`: política de intervalo completo (R03).
- `modules/identity/service.py`: revocación al cambiar rol (R06).
- `modules/commerce/service.py`: locks ordenados + snapshot unit_cost (R08/R10).
- `modules/analytics/service.py`: ETL positivo+compensatorio fechado, costo
  snapshot, overview con `include_demo`, series llenadas en Python, tops por
  tipo (R02/R08/R09-estabilidad).
- `modules/assistant/service.py`: neto por momentos, demo excluido,
  `no_disponible` para cobros, precio por regex corregida, conocimiento
  por-palabra content|title (R02/R08 + defectos previos).
- `entrypoints/web/app.py`: cookie CSRF reemitida tras fallo, settings
  admin-only, historial por ámbito, demo visible (R04/R05/R07/R08).
- `migrations → src/crm_premium/migrations/operational` + `0005_venta_linea_costo.sql`.
- `pyproject.toml`: package-data (R10).
- `tests/conftest.py`: opt-in explícito + finally + aislamiento comercio/BI (R09).
- `tests/test_corr01.py` nuevo (18 pruebas); ajustes en suites previas.

## Pruebas (reales, PostgreSQL temporal en servidor aislado 5433)

- Corrida roja previa: `pruebas/ejecuciones/red_corrida1.txt` — 13 fallos
  que reproducen R02/R03/R04/R05/R06/R07/R08/R10 (los ítems ya conformes y
  las correcciones documentales R01/R11 no generan prueba de código).
- Corrida final: `pruebas/ejecuciones/green_corrida_final.txt` —
  **90 passed in 61.42s**. Comando reproducible:
  `CRM_PREMIUM_TEST_URL=postgresql://<credenciales de prueba>@<servidor aislado>/postgres .venv/Scripts/python -m pytest tests/`
- Empaquetado: `pruebas/ejecuciones/smoke_packaging.txt` — wheel instalado
  fuera del checkout, migraciones/render/estáticos OK.
- ETL atómico verificado en verde (rebuild completo en una transacción; la
  corrida roja inicial documentó el estado previo). Pendiente específico:
  prueba dirigida de fallo de migración a mitad (la cobertura actual es por
  transacción única, ver §pendientes).
- Servidor real reiniciado: las 10 rutas responden 200 (log de la sesión).

## Pendientes declarados

1. **R01**: rotación real de la contraseña por el propietario (procedimiento
   arriba). Mientras tanto, tratar la credencial como comprometida.
2. Prueba dirigida de fallo de migración/ETL a mitad de lote (rollback y
   conservación del último lote bueno) — la transacción única lo garantiza
   en diseño, falta la prueba de ruptura inyectada.
3. knowledge_docs sin permisos/publicación por documento (R04 residual).
4. Permisos por sede/responsable, MFA y recuperación (F01 completo).
5. Cobros/abonos/cartera como fase propia (F11 completa); hoy «no disponible».
6. Recorrido visual independiente del navegador por Codex (no cubierto aquí).
7. Git: sin commit/push (decisión pendiente del propietario); el redactado
   R01 quedó aplicado sobre los archivos, sin historial que depurar.

## Detente aquí

CORR01 se presenta para revisión independiente. No se avanza a
conversaciones/conectores ni nuevas funciones hasta el dictamen.
