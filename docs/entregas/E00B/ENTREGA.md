# ENTREGA E00B — ajuste documental del contrato empresarial

Origen: `docs/entregas/E00/revision/REVISION_CODEX_01.md` (DEVUELTA PARA
AJUSTE DOCUMENTAL — no editado). Sólo documentación; **no se implementa E01**.
E00 permanece como entrega histórica; este documento prevalece donde difiere.

## Tabla de respuesta D1–D4

| Punto | Respuesta en este documento |
|---|---|
| D1 dependencia circular/invertida | §2: modelo mínimo de oportunidad/etapas/interés/consentimiento asignado a **E03-O** (subentrega de E03); E04 depende de E03-O; E05 amplía. E06 dividido en **E06-A contrato+simulador** (tras E02) y **E06-B activación** (tras E05 + proveedor elegido). E07: atribución de campañas/cobros marcada **no disponible** mientras no existan las entidades de campañas/eventos (E09). |
| D2 requisitos sin fase | §3: cada F01–F34 con fase/subentrega, condición de habilitación, evidencia prevista y carácter (núcleo o ampliación contractual). F09/F10 → **E09** (ampliación contractual, tras E05). F22–F24 → **E10-IA** (tras E03; evals desde el primer prompt). F25 continuo; F26 → **E03-C** (tras WhatsApp aceptado); F27 → E08. |
| D3 trazabilidad individual | §4: mapa individual T01–T58 → fase, condición y evidencia prevista; separación diseñado/implementado/probado-simulado/probado-externo; «CI local» corregido a **«suite pytest local»** (no hay CI configurado). |
| D4 contrato E01 insuficiente | §5: contrato ejecutable E01 (matriz acción×rol×ámbito con denegación por defecto, migración a sede inicial sin pérdidas ni apertura de acceso, contactos compartidos vs oportunidades asignadas, backfill, permisos IA/BI/exportación, preservación de historial, MFA/recuperación con plazos y criterios negativos). |

## §2. Modelo mínimo de oportunidad (contrato E03-O; habilita E04)

**Fase**: E03-O (subentrega de E03, antes de E04). **E05** lo amplía con
cotización/pedido/pago. **Datos (migración `0006_opportunities.sql`)**:

```
opportunities: id, contact_id→contacts, branch_id (E01; NULL→sede única hasta E01),
  stage (lead/consultada/calificada/propuesta/ganada/perdida; configurable por
  pipeline en E01-F31), responsible_user_id→users, interest_product_id→products
  (opcional), consent_marketing boolean NULL (NULL=desconocido: nunca tratado
  como falso ni verdadero), origin, channel, row_version, created_at, updated_at
opportunity_history: id, opportunity_id, action, actor_user_id/label, reason,
  detail jsonb, created_at   (regla V3: auditoría en la transacción del cambio)
```

**Reglas del contrato**: etapa cambia sólo por transición registrada con
historial; cierre (ganada/perdida) exige motivo; reabrir conserva el cierre
anterior (regla 02 del expediente). **Consentimiento es elegibilidad
independiente del puntaje**: NULL o baja ⇒ ninguna acción de campaña aunque
la regla dé 100 (T48). Sin atributos sensibles. Interés = referencia a
producto/servicio del catálogo (E02) + fecha; el «interés declarado» que usan
las reglas E04 se guarda como señal con evidencia y versión (§E04 de E00).

**Estado tras E03-O**: diseñado; implementación y pruebas en su fase.
E04 queda **condicionada** a E03-O aceptada.

## E06 dividido (respuesta D1)

- **E06-A (contrato + simulador)**: entidades `integration_configs`,
  `entity_mappings`, `sync_runs`, `reconciliation_queue` y adaptador
  **simulado**. Habilitación: E02 (catálogo/stock local) aceptada.
- **E06-B (activación real)**: proveedor elegido con el cliente, credenciales
  privadas, prueba externa autorizada. Habilitación: E05 aceptada (pedidos/
  cobros locales existen) + acuerdo documentado del proveedor.
- E07: la métrica «campaña → cobro» y su atribución **no se implementan ni se
  muestran** hasta que existan eventos de campaña (E09); mientras tanto, «no
  disponible» con motivo (T54 parcial).

## §3. Matriz individual F01–F34

Carácter: **N**=núcleo obligatorio (07/08), **A**=ampliación contractual.
Estado: D=diseñado, I=implementado (núcleo), P=parcial, ✖=no iniciado.

| F | Fase | Condición de habilitación | Evidencia prevista | Carácter | Estado |
|---|---|---|---|---|---|
| F01 | E01 (+E01-B MFA) | CORR01C aceptada | T06/T07/T39 + negativos | N | P |
| F02 | E07 (base ya en V4) | E01/E05 | T27 | N | P |
| F03 | E03 (360, fusión) | E01 | T15, T55 | N | P |
| F04 | E03-O/E05 | E03-O | T49 parcial, T53 | N | ✖ |
| F05 | E04 | E03-O | T28, T46–T48 | N | ✖ |
| F06 | núcleo ✔ + E03 (calendario externo) | prueba externa autorizada | T05, T22 parcial | N | P |
| F07 | E03 | E01/E02 | T10–T12 | N | ✖ |
| F08 | E03 | E01 | T16–T17 | N | ✖ |
| F09 | E09 | E03 (plantillas) + E05 + contrato | T19 | A | ✖ |
| F10 | E09 | F09 | T19 | A | ✖ |
| F11 | E05 (+E02 stock) | E02/E03 | T13/T14/T21, T49 | N | P |
| F12 | E03 (versiones/permisos) | E01 | T18, T57 | N | P |
| F13 | E07 | E01–E05 | T20–T22, T27 | N | P |
| F14 | E07 | carga manual utilizable | T56 | N | ✖ |
| F15 | E03 (RAG) + E07 (métricas) + E10-IA | fases previas | T29, T31 | N | P |
| F16 | E08 | fases previas | T34, T58 | N | P |
| F17 | E01 | CORR01C | T39 | N | ✖ |
| F18 | E03-C (canales contratados) | prueba externa autorizada | T12, T23 parcial | N(1º)/A(resto) | ✖ |
| F19 | E07-B | contrato de fuentes | evidencia de fuente/fecha | A | ✖ |
| F20 | E07-C | dataset+validación previa | comparación vs regla base | A | ✖ |
| F21 | E06 | contrato por cliente | T50–T51 | A | ✖ |
| F22 | E10-IA | ≥1 proveedor contratado | conmutación real simulada→externa | N (07) | ✖ |
| F23 | E10-IA | F22 | registros reales vs estimados | N (07) | ✖ |
| F24 | E10-IA | primer prompt runtime | ≥60 casos, 10/prompt | N (07) | ✖ |
| F25 | continuo (cada entrega) + E08 (revisión previa a VPS) | — | suites + negativos | N | P |
| F26 | E03-C | WhatsApp aceptado (T12) | semáforo por número con métricas | N (07) | ✖ |
| F27 | E08 | segunda instalación real | recrear instalación en horas | N (07) | ✖ |
| F28 | E04 | E03-O | T46–T48 | N | ✖ |
| F29 | E02 | E01 | T41–T42, T45 | N | P |
| F30 | E02 | E01 | T43–T44 | N | P |
| F31 | E01 | — | T40 | N | ✖ |
| F32 | E05 | E02/E03 | T49 | N | ✖ |
| F33 | E01/E07 | E01 | T52–T53 | N | ✖ |
| F34 | E06 | E06-A | T50–T51 | A | ✖ |

## §4. Mapa individual T01–T58

Fase de ejecución formal; «regresión» = re-ejecución en esa fase. Evidencia:
suite pytest + recorrido/captura cuando el criterio lo exige.

| T | Fase | T | Fase | T | Fase | T | Fase | T | Fase | T | Fase |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | E01 | T02¹ | E01-M | T03 | E01-M | T04 | E01 | T05 | E01-R | T06 | E01 |
| T07 | E01 | T08 | E01 | T09 | E02 | T10 | E03 | T11 | E03 | T12 | E03-C |
| T13 | E02-R | T14 | E05 | T15 | E03 | T16 | E03 | T17 | E03-C | T18 | E03 |
| T19 | E09 | T20 | E07 | T21 | E07 | T22 | E07 | T23 | E06-A | T24 | E06-B |
| T25 | E03 | T26 | E08 | T27 | E07 | T28 | E04 | T29 | E07 | T30 | E07 |
| T31 | E07 | T32 | E03/E08 | T33 | E03/E08 | T34 | E08 | T35 | E08 | T36 | E01-R |
| T37 | E01-R | T38 | E01-R | T39 | E01 | T40 | E01 | T41 | E02 | T42 | E02 |
| T43 | E02 | T44 | E02 | T45 | E03 | T46 | E04 | T47 | E04 | T48 | E04 |
| T49 | E05 | T50 | E06-B | T51 | E06-B | T52 | E07 | T53 | E07 | T54 | E07² |
| T55 | E03 | T56 | E07 | T57 | E03 | T58 | E08 | | | | |

¹ T02 (fixture SQLite de V3): **no aplicable salvo contrato de migración V3**;
E01-M ejecuta su equivalente sobre los datos actuales PostgreSQL (consolidación
a sede inicial). ² T54 sólo la parte sin campañas; atribución campaña→cobro
queda **no disponible** hasta E09 (D1).

Condición transversal: cada fase requiere las anteriores aceptadas. Estados
actuales honestos: probado-simulado (agenda/concurrencia/seguridad, suite 104),
diseñado (todo lo ✖/✖-fase); **ningún T del 05/10 está aceptado formalmente**.

## §5. Contrato ejecutable E01 (nivel de detalle para implementar sin adivinar)

### Migración a sede inicial (E01-M, sin pérdidas ni apertura de acceso)
1. Migración `0006_organizations_branches.sql`: `branches` (id, name, timezone,
   is_active), `user_branch_roles` (user_id, branch_id, role_scope, UNIQUE),
   `resource_branches`/`product_branches` N:M con sede habilitada,
   `branch_id` en appointments/sales/stock_movements/opportunities.
2. Backfill transaccional: sede **«Principal» id=1** creada; TODAS las filas
   existentes (recursos, contactos, citas, productos, ventas, movimientos)
   quedan asignadas a sede 1 **preservando IDs, historial, precios y costos**;
   BI recibe `dim_sede` y los hechos se re-etiquetan (sede 1). Sin datos
   ficticios para entidades inexistentes (las que falten se crean vacías).
3. Usuarios actuales: admin→rol **director** (ámbito global); usuarios→
   **asesor** (sede 1). Ningún acceso nuevo se abre: la denegación por defecto
   restringe, nunca expande. MFA/recovery: recuperación por códigos de un solo
   uso en E01; **MFA TOTP del admin es requisito bloqueante de E08** (VPS
   público) y se entrega en E01-B.

### Matriz acción × rol × ámbito (denegación por defecto)

Ámbitos: G=global/todas las sedes, S=sede(s) asignada(s), P=propios
(asignados/creados). «—» = denegado (403 sin datos; ocultar menú no basta).

| Acción | Director | Gerente sede | Asesor | Almacén | Finanzas | Analista |
|---|---|---|---|---|---|---|
| Ver clientes | G | S | P+S(consulta) | — | S(consulta) | agregado |
| Crear/editar cliente | G | S | S | — | — | — |
| Ver oportunidad ajena | G | S | P | — | S(cifras) | agregado |
| Agenda: ver/crear | G | S | S | — | — | — |
| Cita: confirmar/cancelar/reprogramar ajena | G | S | P | — | — | — |
| Corrección administrativa de cita | G | S | — | — | — | — |
| Notas privadas: ver/crear | G+S | S | P | — | — | — |
| Venta: crear | G | S | S | — | S | — |
| Venta: revertir | G | — | — | — | S | — |
| Catálogo: ver / crear-editar-precio | G / G | S / — | S / — | S / — | — / — | — / — |
| Stock: ajustar / trasladar / contar | — / G / G | S / S / S | — / — / — | S / S / S | — / — / — | — / — / — |
| Exportar datos (personales) | G | S | — | — | S(cobros) | — (agregados anon.) |
| BI: ver consolidado / por sede | G | S | — | — | S | G(agregado sin PII) |
| BI: reconstruir | G | — | — | — | — | — |
| Asistente: preguntar / historial global | G / G | S / — | P / — | P / — | P / — | P / — |
| Reglas: ver / editar-publicar | G / G | S / — | — | — | — | — / — |
| Usuarios y sedes: gestionar | G | — | — | — | — | — |

Permisos atómicos independientes (exportar, reembolsar, publicar, ajustar
stock) se modelan como permisos, no derivados del rol. El servidor aplica el
ámbito en rutas, búsquedas, herramientas del asistente, BI y exportaciones.

### Contactos compartidos vs oportunidades asignadas
- Contacto: registro compartido de la organización (visible según matriz);
  sus notas privadas de cita conservan ámbito de sede.
- Oportunidad: SIEMPRE asignada (responsable + sede de origen); compartirla a
  otra sede no expone notas privadas ni documentos privados del contacto.
- Regla transversal (08): compartir cliente ≠ exponer lo privado.

### Preservación de historial/precio/costo
Ningún backfill reescribe precios/costos/historiales; las migraciones son
aditivas y versionadas; reversión documentada por entrega (regla CORR01).

### Criterios negativos de E01 (denegación por defecto)
1. Asesor: URL/API/exportación de otra sede → 403 sin datos ni filtrado.
2. Gerente de sede A: no ve sede B en API, BI ni exportación.
3. Analista: ninguna consulta devuelve PII; exportación agregada/anónima.
4. Almacén: sin acceso a ventas/finanzas; Finanzas: sin ajustar stock.
5. Asistente: pregunta sobre otra sede → «no disponible en su ámbito».
6. Usuario sin permiso explícito: toda acción de la matriz fuera de su celda
   → denegada y auditada.
7. Tras cambiar rol/ámbito: sesiones revocadas (regla CORR01/R06).

## Correcciones menores (D3)
- «CI local» de E00 se corrige: **suite pytest local** (no hay CI configurado;
  si se configura, será otra entrega con evidencia).
- Métricas sin fuente: se presentan «no disponible» con motivo (T54²).
- Sin afirmaciones de superioridad comercial universal (objetivo declarado,
  comparación por demostrar — 07 corregido).

## Límites
Documento de diseño: nada de lo aquí asignado está implementado salvo lo
marcado P/✔ en §3 con su evidencia de fase previa. E01 sólo inicia tras
dictámenes favorables de CORR01C y E00B.
