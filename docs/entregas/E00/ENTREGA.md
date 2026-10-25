# ENTREGA E00 — paridad básica V3→V4 y contrato empresarial (sólo documentación)

Implementador: GLM/ZCode. Base: `08_ALCANCE_EMPRESARIAL.md`, `10_ACEPTACION_
EMPRESARIAL.md` (T39–T58), `05_ACEPTACION.md` (T01–T38) y el árbol real
post-CORR01B. **No afirma cierre técnico de CORR01B ni implementa módulos.**

## 1. Paridad V3→V4 por flujo básico

Leyenda de estado: ✔ implementado y probado en V4 · ◐ parcial · ✖ pendiente.
V3 se cita por su último estado documentado (su docs/producto/ESTADO.md); su
aceptación histórica NO vale como prueba V4.

| Flujo básico (08 §Paridad) | V3 (estado real de referencia) | V4 actual | Brecha → fase |
|---|---|---|---|
| Información publicada al cliente | Bot con prompts fijos; RAG sin publicación gestionada | ✖ sin canal/agente | E03 |
| Precio/disponibilidad estructurados | ✖ (sin catálogo) | ◐ productos/precios con historial y stock simple; sin publicación ni disponibilidad por sede | E02/E03 |
| Contacto e interés | Leads CRM SQLite (etapa «Cita agendada») | ◐ contacts sin oportunidades/etapas | E03/E05 |
| Reservar/consultar/confirmar/cancelar/reprogramar | reservation_service aceptado (P01B/P02C) | ✔ portado a PostgreSQL con las mismas reglas (47→96 pruebas) | — |
| Horario/zona/recurso/concurrencia | G01B perfil + check_window | ✔ política por intervalo completo (CORR01/R03) + concurrencia probada | — |
| Calendario con reintentos/conflictos | Google con outbox (P03 condicionada a prueba real) | ✖ sin calendario externo | E03 |
| Historial y seguimiento | Historial de citas + auditoría | ✔ en citas/ventas/precios/stock; ✖ tareas/SLA | E03/E05 |
| Canal contratado con plantillas | WhatsApp webhook sin verificar; plantillas doc | ✖ | E03 |
| Humano con pausa durable | ✖ (P04 nunca iniciada) | ✖ | E03 |
| Notas privadas | ✔ notas de cita | ✔ en citas; ✖ por conversación | E03 |
| Acceso individual | Roles admin/usuario | ✔ sesiones/CSRF/roles dos; ✖ por sede/documento (R04 residual) | E01 |
| Adaptación por negocio | Perfiles V3 (zona/horario/nombre) | ◐ organización editable; sin perfiles multirrubro completos | E01/E02 |

Conclusión honesta: V4 supera a V3 en agenda/comercio/analítica básica, pero
**la paridad básica aún no cierra**: canal, plantillas, humano/pausa, tareas y
calendario externo dependen de E03. Un flujo ausente bloquea los recorridos
de 08 que lo usan (T55 lo exigirá completo).

## 2. Matriz F01–F34 (estado del árbol post-CORR01B)

| F | Estado | Evidencia/límite |
|---|---|---|
| F01 acceso/equipo | ◐ | Sesiones/CSRF/roles dos, bloqueo, revocación por rol/rotación. Sin MFA, recuperación, sedes ni permisos granulares → E01 |
| F02 inicio ejecutivo | ◐ | Dashboard KPIs reales (no certificado como cuadro financiero) |
| F03 clientes 360 | ◐ | Contacts+historial de citas; sin consentimiento/fusión/identidades |
| F04 embudo | ✖ | E03/E05 |
| F05 análisis de leads | ✖ | E04 (R1 como plantilla editable) |
| F06 agenda | ✔ núcleo | Reglas V3 portadas; conectores → E03 |
| F07 conversaciones | ✖ | E03 |
| F08 plantillas Meta | ✖ | E03 |
| F09/F10 campañas/automatizaciones | ✖ | post-E03 |
| F11 ventas/stock | ◐ | Venta atómica, reversión compensatoria, stock por movimientos, costo snapshot; sin cotizaciones/abonos/cartera → E05 |
| F12 conocimiento | ◐ | Tabla+búsqueda por palabras; sin versiones/permisos/publicación |
| F13 análisis de datos | ◐ | Estrella bi (citas+ventas) con demo excluido; sin SCD2/incremental/sede → E07 |
| F14 mercado | ✖ | E07 |
| F15 asistente | ◐ | Determinista por herramientas, auditado, ámbito propio; sin LLM/RAG real |
| F16 operación local | ◐ | CLI (migrate/seed/run/rotate-password/rebuild-bi); sin VPS/respaldo ensayado → E08 |
| F17 multisucursal | ✖ | **Ahora requisito del núcleo** (08) → E01 |
| F18–F21 canales/mercado/predicción/integraciones | ✖ | E03/E06/E07 |
| F22 failover IA | ✖ | dependencia: proveedores IA |
| F23 telemetría tokens | ✖ | dependencia: primer proveedor |
| F24 evals prompts | ✖ | dependencia: primer prompt runtime |
| F25 seguridad continua | ◐ | suite seguridad en CI local; sin pentest/MFA |
| F26 semáforo por número | ✖ | dependencia: WhatsApp |
| F27 fábrica | ✖ | segunda instalación (E08) |
| F28 reglas editables | ✖ | E04 |
| F29 catálogo visual/fichas | ◐ | E02 (sin fotos/variantes/publicación) |
| F30 inventario por almacén | ◐ | stock único global sin ubicaciones → E02 |
| F31 campos/pipelines configurables | ✖ | E01 |
| F32 cotización/pedido/cobro/postventa | ✖ | E05 |
| F33 dirección por sede/equipo/metas | ✖ | E01/E07 |
| F34 centro de integraciones | ✖ | E06 |

T01–T38 (05) y T39–T58 (10) se ejecutarán por fase según la tabla siguiente;
hoy no hay criterio T empresarial ejecutado.

## 3. Contratos de fase E01–E08

| Fase | Objetivo | Datos/entidades nuevas (migraciones) | Permisos | Dependencias | Criterios |
|---|---|---|---|---|---|
| E01 | Sedes, equipos, permisos, configuración frontend | `branches`, `locations`(almacén/consultorio), `team_members`(usuario↔sede↔rol de ámbito), `absences`, `assignments`, `resource_schedules`, `field_defs`(campos tipados), `pipelines` | rol+ámbito independientes: director/gerente-sede/asesor/almacén/finanzas/analista; permisos atómicos (exportar, ajustar stock, descontar, reembolsar, publicar) | CORR01B aceptada | T39–T40 + regresión acceso/agenda |
| E02 | Catálogo visual + inventario por ubicación | `variants`, `media`(privado), `catalog_publications`, `stock_by_location`(físico/reservado), `stock_transfers`(tránsito), `counts`, `reservations`(expiración) | publicar/ajustar/descontar por permiso; medios: subir≠publicar≠RAG | E01 (ubicaciones) | T41–T44 |
| E03 | Paridad básica: bandeja, canal, plantillas, conocimiento, calendario | `conversations`, `messages`, `conversation_events`(pausa durable), `tasks`(SLA), `templates`(versiones+aprobación), `knowledge_versions`, `calendar_links` | bandeja por asignación; pausa revoca envíos; publicar conocimiento por permiso | E01/E02; WhatsApp/Google simulados primero | T10–T18, T45, T55, T57 |
| E04 | Reglas comerciales editables | `rules`(versión, vigencia, constructor JSON tipado), `rule_simulations`, `lead_scores`(señal+evidencia+versión), `assignment_rules` | editar/simular/publicar/revertir por permiso; sin SQL/eval/scripts | E01; señales de E03 | T46–T48 |
| E05 | Cotización→cobro→postventa | `opportunities`, `quotes`(versionadas, snapshot precio/costo), `orders`, `payments/abonos`, `refunds`, `portal_tokens`(caducables) | descuento/reembolso por permiso+aprobación; venta≠pago | E02 (stock/reserva), E03 | T49 + regresión T13–T15/T21 |
| E06 | Primer conector CRM/ERP acordado | `integration_configs`(credenciales privadas), `entity_mappings`, `sync_runs`(outbox, firma, dedup), `reconciliation_queue` | ERP autoridad por campo cuando configurado; nunca SQL directo | E00 contratos + elección documentada de proveedor con el cliente | T50–T51 |
| E07 | Análisis gerencial + mercado | bi: dims sede/equipo/regla-versión; facts cobros/inventario/pipeline; `market_observations`(fuente/fecha/muestra); `assistant_metrics`(misma fuente) | cuadros sobre medidas permitidas; exportación con ámbito | E01–E05; evals desde primer prompt (F24) | T52–T54, T56 |
| E08 | Recorrido empresarial + VPS + transferencia | deploy/ (servicios, proxy HTTPS), guías, respaldo/restauración ensayados | demo 3 sedes/15 cuentas/500 artículos/2 rubros; permisos cruzados | fases previas aceptadas | T32–T35, T58 |

F22–F27 se incorporan en sus dependencias naturales (E03→F26; E07→F23/F24;
proveedores→F22; E08→F27), sin posponer seguridad/evals.

## 4. Bocetos de pantallas (destino; no implementadas)

```
INICIO GERENCIAL          BANDEJA (E03)             CATÁLOGO GALERÍA (E02)
┌────────────────────┐    ┌───────────────────┐    ┌─────────────────────┐
│ Sede: [Todas ▼]    │    │ Filtro: abiertos  │    │ [Buscar…] [Rubro ▼] │
│ ▣ Metas vs real    │    │ ┌───────────────┐ │    │ ┌────┐ ┌────┐ ┌────┐│
│ ▣ Venta/cobro/cartera│  │ │ Cliente X     │ │    │ │foto│ │foto│ │foto││
│ ▣ Leads por regla  │    │ │ ⏸ IA │ Asignar│ │    │ └────┘ └────┘ └────┘│
│ ▣ Quiebres de stock│    │ └───────────────┘ │    │  Variante ▸ ficha   │
│ [Desglose→BI]      │    │  …hilos…          │    │  precio/stock/sede  │
└────────────────────┘    └───────────────────┘    └─────────────────────┘

REGLAS (E04)              COTIZACIÓN (E05)          ANÁLISIS (E07)
┌────────────────────┐    ┌───────────────────┐    ┌─────────────────────┐
│ Regla: prioridad   │    │ Oportunidad #12   │    │ Medida:[Venta neta▼]│
│ TODOS:[▼señal…]    │    │ ┌───────────────┐ │    │ Por:[Sede/Equipo▼]  │
│ ▣ peso:25 tope:100 │    │ │artícfoto cant.│ │    │ ▣ fórmula ▣ fuente  │
│ [Simular impactos] │    │ └───────────────┘ │    │ ▣ lote ▣ cobertura  │
│ [Publicar v2]      │    │ Total $ → Aceptar │    │ [Exportar(mi ámbito)]│
└────────────────────┘    └───────────────────┘    └─────────────────────┘
```

## 5. Límites de E00

Documento de diseño; nada aquí declara implementado lo pendiente. La matriz
se re-valida al cerrar cada fase. No rehace PR00 ni crea otra aplicación.
