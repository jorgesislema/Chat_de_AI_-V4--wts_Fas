# INFORME DE PRUEBAS — PR00B (núcleo funcional)

Fecha: 24-10-2026. Entorno: Windows 10, Python 3.13.1, PostgreSQL 18.6 nativo
(puerto 5432, base `crm_premium`). Ejecutor: GLM en venv propio del proyecto
(`.venv`). Todas las pruebas usan una base PostgreSQL temporal creada y
destruida por corrida (`crm_premium_test_<hex>`), sin datos reales.

## Resultado actual (no histórico)

```
47 passed in 37.70s
```

Comando: `./.venv/Scripts/python.exe -m pytest tests/` (reproducible; ver
PROMPTS_USADOS.md). Resumen en `evidencias/pytest_resumen.txt`.

## Cobertura por suite

| Suite | Pruebas | Qué cubre |
|---|---:|---|
| test_timeutil.py | 9 | Zona IANA, DST (hora inexistente y ambigua Madrid), rangos día/semana/mes (rejilla 42 días), etiquetas en español |
| test_identity.py | 8 | Alta/duplicados, contraseña débil, bloqueo a los 5 intentos, sesiones y revocación, cambio de contraseña, expiración, desactivación |
| test_scheduling.py | 12 | Alta/detalle, solape y borde semiabierto, concurrencia real del mismo hueco (2 hilos, 1 ganador por bloqueo consultivo), pasado/rango/título, recurso inactivo, reprogramación con versión, confirmar/cancelar/asistencia/corrección, notas, ventana de horario con excepción admin, listado por rango |
| test_security.py | 9 | Rutas protegidas, API 401, CSP/X-Frame/nosniff, cookie HttpOnly+SameSite, CSRF en escrituras y en login, credenciales inválidas, usuario no-admin sin acceso a usuarios, logout revoca, open-redirect bloqueado |
| test_web_flow.py | 6 | Dashboard con KPIs, ciclo agenda API (crear→listar→detalle→confirmar→nota), solape→409, contactos ciclo completo, ajustes con zona válida/inválida, gestión de usuarios por admin |

## Iteraciones registradas (trazabilidad de fallos corregidos)

1. **Corrida 1**: 12 failed / 15 errors / 20 passed. Causas: columna `note_id`
   faltante en `appointment_history` (migración 0002 añadida, 0001 no se tocó
   por estar aplicada), imports de paquete en vez de servicio, `set_user_active`
   con `fetchone` tras UPDATE sin `RETURNING`, etiqueta de mes de la rejilla.
2. **Corrida 2**: 4 failed / 15 errors — servicio dashboard mal importado,
   pruebas con expectativas contradictorias con el diseño (cancelar cita
   confirmada antes del inicio es válido; listado necesitaba fecha aislada).
3. **Corrida 3**: 6 failed — restos de `organization.service`/`contacts_module.service`,
   `/api/agenda` sin fecha (ahora usa hoy por defecto), `Location` relativo del
   redirect, `contacts.items` resolvía al método dict de Jinja (renombrado a
   `listing`).
4. **Corrida 4**: 2 failed — `reason` pasada a `confirm_appointment`; corregido
   el reparto de argumentos por acción.
5. **Corrida 5**: 47/47 en verde.
6. **Servidor real**: el arranque manual reveló el mismo defecto de import de
   `scheduling` (en pytest pasaba por acoplamiento oculto: otra prueba ya
   había importado el submódulo). Corregido de raíz; servidor re-verificado.
7. **Navegador real (Chromium del entorno)**: detectado y corregido un defecto
   de UI (botón invisible de hueco libre tapaba los chips de cita; z-index).
   Tras corregirlo: apertura de detalle, historial, notas y **creación de cita
   desde la interfaz** verificadas con capturas.

## Verificación de servidor real (curl, misma sesión)

- `POST /login` → 302; `GET /` → 200 con KPIs; `POST /api/appointments` → 201;
  `GET /api/agenda?view=month` → 200 con 426 eventos del demo;
  contactos/usuarios/ajustes → 200.

## Evidencia visual

`evidencias/dashboard_inicio.png`, `evidencias/agenda_semana.png`,
`evidencias/agenda_mes_cita_creada.png` (la cita «Cita creada desde el
navegador» del 27-oct visible en el mes).

## Límites de esta corrida

- Sin pruebas de carga ni de producción (es núcleo local).
- Conectores (WhatsApp/Telegram/etc.) no existen todavía: nada que probar ahí.
- No se modificaron secretos ni datos reales; `.env` local permanece fuera de Git.
