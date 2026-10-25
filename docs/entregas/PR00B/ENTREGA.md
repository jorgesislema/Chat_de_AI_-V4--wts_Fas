# ENTREGA PR00B — Núcleo funcional ejecutable (edición 2000+)

Fecha: 24-10-2026. Responsable: GLM/ZCode. Revisión: pendiente del propietario.
Estado: **lista para revisión**. Alcance: arranque por núcleo funcional autorizado
por el propietario en `docs/producto/premium/07_VISION_EDICION_2000.md`
(sustituye el PR00 documental extenso como primer paso).

## Objetivo

Dejar corriendo en local el corazón del producto 2000+ (V3 «con esteroides»):
identidad con roles, organización, contactos y agenda de citas sobre PostgreSQL,
con frontend profesional responsive y gráficos, todo testeado y trazable.

## Cambios (inventario real)

```
pyproject.toml, .env.example, .gitignore
migrations/operational/0001_core.sql, 0002_history_note_id.sql
src/crm_premium/
  shared/timeutil.py, shared/serialize.py
  infrastructure/persistence/db.py, migrations.py
  modules/identity/service.py, organization/service.py,
          contacts/service.py, scheduling/service.py, dashboard/service.py
  entrypoints/web/app.py
  presentation/templates/*.html (7), presentation/static/app.css, app.js,
          agenda.js, favicon.svg
  __main__.py (CLI: migrate, create-admin, seed-demo, run)
tests/ (5 suites, 47 pruebas)
docs/operations/PROTECCION_DATOS.md
docs/entregas/PR00B/ (este informe, INFORME_PRUEBAS, PROMPTS_USADOS, evidencias/)
README.md, MAPA.md, docs/producto/ESTADO.md (actualizados)
```

## Decisiones y desviaciones del plan

- **D1. Base de datos**: el propietario indicó que hay PostgreSQL en su PC y dio
  credenciales; se verificaron y la base única del proyecto es `crm_premium`
  en el **PostgreSQL 18.6 nativo** (puerto 5432). El contenedor Docker
  `crm_premium_pg` (5433) quedó como respaldo y puede eliminarse.
- **D2. `.env` local** creado con `DATABASE_URL` y `SECRET_KEY` generada;
  fuera de Git. `.env.example` documenta los nombres.
- **D3. Migración 0002** añade `appointment_history.note_id` (falta detectada
  por pruebas); 0001 ya aplicada no se editó — corrección versionada.
- **D4. Administrador inicial** `admin` con contraseña temporal
  ~~redactada por CORR01/R01~~ *(valor eliminado de la documentación;
  ver incidente y procedimiento de rotación en
  `docs/entregas/CORR01/ENTREGA.md`)*. **El propietario debe rotarla** en
  Ajustes al primer inicio (política: sin contraseñas predeterminadas).
- **D5. Puerto** de desarrollo: 8055.
- **D6. Sin Git**: no se hizo commit ni push (decisión pendiente del propietario).

## Cómo correrlo (verificado en esta máquina)

```bash
cd "H:\git\Agente de reserva V4"
./.venv/Scripts/python.exe -m crm_premium run --port 8055
# → http://127.0.0.1:8055  (admin / <contraseña rotada por el propietario>)
```

Reinstalación limpia en otra PC: crear `.env` desde `.env.example`, apuntar a
un PostgreSQL con la base creada, `pip install -e ".[test]"`,
`python -m crm_premium migrate`, `create-admin`, opcional `seed-demo`.

## Pruebas y verificación

- **47/47 pytest** (unit + integración PostgreSQL temporal + seguridad + flujo
  web). Detalle e iteraciones de corrección: `INFORME_PRUEBAS.md`.
- **Servidor real verificado con curl**: login, dashboard, API de agenda
  (426 eventos demo), creación de cita (201), páginas protegidas.
- **Navegador real**: login, dashboard con KPIs, agenda semana/mes, detalle de
  cita con historial, y creación de cita desde la UI (capturas en `evidencias/`).
- Defecto de UI encontrado y corregido durante la prueba visual (z-index del
  hueco libre); defecto latente de imports detectado por el arranque real.

## Pendientes / siguiente fase

1. Propietario: cambiar la contraseña de `admin`; decidir commit inicial.
2. Fase siguiente sugerida: **comercio/inventario** (cientos de artículos,
   cotización/venta/pago con movimientos de stock atómicos, F11) — es el
   requisito original del propietario («guardar cientos de artículos para venta»).
3. Después: conversations con WhatsApp simulado + telemetría F23; failover F22.
4. La capa estrella/ETL reemplazará las consultas del dashboard en su fase.

## Reversión

No hay código previo de V4 que revertir: la raíz sólo contenía documentación.
La base `crm_premium` puede eliminarse sin impacto (`DROP DATABASE`); los
contenedores Docker `crm_premium_pg`/`reservas-*` no son del proyecto.
