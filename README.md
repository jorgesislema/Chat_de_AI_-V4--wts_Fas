# Agente de reserva V4 — CRM Premium (edición 2000+)

Producto multirrubro de atención, agenda e inteligencia comercial. V3 «con
esteroides»: reservas e información como núcleo, más analítica, multicanal,
telemetría de costos, failover de IA y fábrica de instalaciones. Instalación
freelancer, código para el cliente, PostgreSQL privado, sin suscripción propia.

## Estado

**CORR01 (última entrega, para revisión)**: núcleo PR00B + comercio
(inventario con precios auditados y ventas/reversión atómicas), analítica
con modelo estrella (esquema `bi`, demo excluido por defecto) y asistente
interno auditable. 90/90 pruebas en PostgreSQL temporal, wheel verificado
fuera del checkout. Correcciones R01–R11 de la auditoría Codex aplicadas
(rotación de contraseña del admin PENDIENTE del propietario). Detalle en
`docs/entregas/CORR01/ENTREGA.md`; visión del producto en
`docs/producto/premium/07_VISION_EDICION_2000.md`.

## Correrlo en local

1. PostgreSQL accesible y base creada (una base por proyecto, p. ej. `crm_premium`).
2. Copiar `.env.example` a `.env` y ajustar `DATABASE_URL` y `SECRET_KEY`.
3. `python -m venv .venv && .venv/Scripts/pip install -e ".[test]"`
4. `python -m crm_premium migrate` → `python -m crm_premium create-admin admin`
5. Opcional demo: `python -m crm_premium seed-demo --yes`
6. `python -m crm_premium run --port 8055` → http://127.0.0.1:8055

## Estructura

- `src/crm_premium/` — paquete modular (shared, infrastructure, modules,
  entrypoints/web, presentation).
- `migrations/operational/` — SQL versionado (aplica `python -m crm_premium migrate`).
- `tests/` — pytest con base PostgreSQL temporal por corrida.
- `docs/producto/premium/` — expediente (alcance, lógica, experiencia, prompts,
  aceptación, estructura, visión 07).
- `docs/entregas/` — entregas con evidencia; índice en `INDICE.md`.
- `docs/operations/PROTECCION_DATOS.md` — gobernanza de datos (RGPD/LODPD).

## Reglas

Leer `AGENTS.md` y `docs/producto/ESTADO.md` antes de trabajar. Una fase a la
vez con revisión; datos sintéticos por defecto; nunca subir secretos ni bases.
Fuente de referencia V3 (sólo lectura): `H:\git\chat-clinica-dental - copia\chat-reserva-V3`.
