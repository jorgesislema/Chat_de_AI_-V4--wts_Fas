# Mapa del proyecto Agente de reserva V4

## Actualización documental empresarial — 24-10-2026

Expediente 08, prompts 09 y aceptación 10 describen sucursales/equipos, reglas frontend, catálogo visual/inventario, CRM/ERP y análisis. No son módulos implementados. CORR01 tiene revisión en docs/entregas/CORR01/revision/REVISION_CODEX_01.md: cierre pendiente. GLM actualizará inventario real en CORR01B/E00; no tratar conteos históricos como prueba actual.

Raíz: H:\git\Agente de reserva V4.
Estado al 24-10-2026 (tarde): **núcleo funcional PR00B implementado y probado**.

## Código (real, probado)

- `src/crm_premium/` — paquete Python: `shared` (tiempo/serialización),
  `infrastructure/persistence` (PostgreSQL + migraciones), `modules`
  (identity, organization, contacts, scheduling, dashboard),
  `entrypoints/web` (Flask), `presentation` (plantillas y estáticos propios).
- `migrations/operational/0001_core.sql`, `0002_history_note_id.sql`.
- `tests/` — 5 suites, 47 pruebas; base PostgreSQL temporal por corrida.
- `pyproject.toml` (instalable, CLI `python -m crm_premium`).

## Documentación

- docs/producto/premium/00–07: expediente del producto (07 = visión de la
  edición 2000+ con requisitos del propietario, F22–F27 e investigación).
- docs/entregas/PR00B/: ENTREGA, INFORME_PRUEBAS, PROMPTS_USADOS, evidencias/.
- docs/operations/PROTECCION_DATOS.md: gobernanza RGPD/LODPD.

## Base de datos

Una única base `crm_premium` en PostgreSQL 18 nativo del propietario (5432),
credenciales en `.env` local (fuera de Git). Las pruebas crean bases temporales
`crm_premium_test_*` y las destruyen. Contenedor Docker `crm_premium_pg` (5433)
queda como respaldo, no en uso.

## Fuente de referencia V3

H:\git\chat-clinica-dental - copia\chat-reserva-V3 — sólo lectura. Reglas
portadas a V4 con pruebas propias: zona IANA/DST, conflictos por intervalo,
versión optimista, estados operativos, historial y auditoría.

## Destino (pendiente)

commerce/inventory (F11, artículos y ventas), conversations + conectores
(F07/F18), telemetría (F23), failover IA (F22), evals (F24), seguridad
continua (F25), semáforo por número (F26), fábrica (F27), capa estrella/ETL
y empaquetado VPS según expediente 01–06.
