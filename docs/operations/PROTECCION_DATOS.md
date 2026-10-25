# PROTECCIÓN DE DATOS Y GOBERNANZA — CRM Premium

Actualizado: 24-10-2026. Alcance: núcleo funcional PR00B. Este documento declara
cómo el núcleo implementa los principios de protección de datos personales
aplicables en Europa (RGPD) y Latinoamérica (por ejemplo, LOPDP Ecuador,
LGPD Brasil, LPDP Perú/Chile). Es una declaración de diseño del producto para
instalaciones del freelancer, no un dictamen legal por país: cada instalación
final debe revisar la ley local antes de operar con datos reales.

## Principios implementados en el núcleo

| Principio | Implementación verificable |
|---|---|
| Minimización | Contactos guarda sólo nombre, teléfono, correo, notas y canal. No hay campos de salud, religión, ideología ni otra categoría especial; el formulario lo advierte. |
| Finalidad declarada | Los datos se recolectan para agenda y atención comercial; la nota de privacidad del formulario lo indica al usuario final. |
| Exactitud y rectificación | Edición de contactos y perfil con historial de cambios en citas; auditoría con actor e instante. |
| Limitación del plazo | Retención por instalación: la política de borrado/anonimización es responsabilidad de la instalación (documentado; la herramienta de exportación/borrado llega en fases PR05+). |
| Integridad y confidencialidad | PostgreSQL privado, credencial fuera del repositorio (.env), sesiones de servidor revocables, CSRF, CSP `default-src 'self'`, cookies HttpOnly/SameSite, bloqueo por intentos fallidos, contraseñas con hash scrypt + sal (Werkzeug) y mínimo 12 caracteres. |
| Responsabilización (accountability) | `audit_log` registra actor, acción e instante UTC de cada operación de agenda; `appointment_history` conserva antes/después de cada cambio con motivo cuando aplica. |
| Transparencia | El login informa que las sesiones se registran y pueden revocarse; el panel de ajustes permite cambiar contraseña y cierra todas las sesiones al hacerlo. |

## Derechos de las personas (estado actual)

- **Acceso y rectificación**: disponibles hoy (listados, detalle, edición de contactos).
- **Supresión / oposición / portabilidad**: corresponden a fases posteriores
  (exportación y borrado con auditoría, F16/F11 del expediente). No declarar
  portabilidad al cliente hasta implementarla.

## Datos de pruebas

Todas las pruebas y el demo usan datos 100% sintéticos (contactos ficticios,
teléfonos generados, notas «DEMO»). Las bases de prueba se crean y destruyen
por corrida. Prohibido cargar datos de personas reales en el repositorio,
documentación o evidencias.

## Auditoría y trazabilidad

- Cada cambio de cita escribe `appointment_history` (acción, actor, detalle
  JSON antes/después, motivo) y `audit_log` dentro de la misma transacción.
- El fallo de la auditoría revierte el cambio (regla heredada de V3).
- Los servicios externos (IA, canales) se conectarán en fases posteriores con
  registros propios; ninguna integración está activa en este núcleo.

## Retención y respaldo (compromisos de la instalación)

- Respaldo diario cifrado fuera del servidor (objetivo RPO 24 h / RTO 4 h,
  documento 02 del expediente) cuando se despliegue en VPS; en local, el
  respaldo es responsabilidad del operador.
- Ninguna base `.db`/dump entra al repositorio (` .gitignore` lo bloquea).
