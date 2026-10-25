# Visión de la edición 2000+ y decisiones del propietario

Fecha: 24-10-2026. Sesión con el propietario que define qué es esta edición y cómo se construye.
Este documento consolida sus instrucciones; las fases y criterios de los documentos 01–06 siguen
vigentes salvo lo que aquí se modifica expresamente.

## Qué es esta edición

- **V3 con esteroides**: versión más avanzada de chat-reserva-V3 (agente de reservas de clínica).
  Su función principal sigue siendo **reservar y responder información**; al ser de más valor añade
  inteligencia comercial, multicanal, multiusuario, telemetría y operación multirrubro.
- Línea de 4 productos por segmento de precio: V3 = 80–100 USD (terminado); **esta = 2000+ USD**;
  dos tramos superiores después.
- Meta declarada por el propietario: **superar lo que el mercado ofrece**, dar más de lo que pide.
- El backend debe adaptarse a otras industrias (clínica, ventas, almacén, inmobiliaria, colegio)
  y el producto debe ser **recreable por cliente mediante prompts y skills** (la fábrica).

## Decisiones confirmadas por el propietario en esta sesión

1. Raíz de construcción: `H:\git\Agente de reserva V4` (este repositorio).
2. Arranque: **núcleo funcional ejecutable ya**, documentando por entrega. El propietario sustituye
   la secuencia «PR00 documental extenso primero»; se conserva la disciplina: `docs/entregas/<ID>/ENTREGA.md`
   por fase, pruebas sintéticas, revisión antes de la fase siguiente y actualización de continuidad.
3. Primer corazón funcional: **agenda/citas** con reutilización controlada de V3; después
   comercio/inventario (cientos de artículos) y bandeja de conversaciones.
4. Base de datos: **PostgreSQL desde el inicio**, incluido el entorno local de desarrollo.

## Requisitos declarados por el propietario consolidados

| Requisito del propietario | Dónde vive |
|---|---|
| Reservas y respuesta de información (núcleo) | scheduling + assistant (F06/F15) |
| Análisis de leads | F05 (puntaje explicable) |
| Análisis de datos | F13 (estrellas e indicadores) |
| Análisis de datos de mercado | F14 (observaciones con fuentes) |
| Recoger toda la información que el cliente provea | F03 Clientes 360 + conversaciones |
| Ventana para modificar plantillas aprobadas por Meta | F08 |
| Chat interno que responde del RAG y de la base de datos | F15 (permisos heredados) |
| Todo prompt con evals | **F24 (nuevo)** |
| Pruebas de seguridad | **F25 (nuevo, obligatoria por entrega)** |
| Ventana de telemetría de gastos de tokens | **F23 (nuevo)** |
| Varias IAs con failover: si una cae, otra asume | **F22 (nuevo)** |
| Varios números de teléfono con semáforo; uno para consultas, otros para publicidad | **F26 (nuevo)** |
| Recibir consultas y reservas de redes sociales | F18 (Messenger, Instagram, Telegram, correo) |
| Verse bien en PC, teléfono y tablet | 03_EXPERIENCIA_Y_PLANTILLAS |
| Varias PC, control de contraseñas y administrador | F01 |
| Sincronizarse con distintos calendarios | F06 + adaptadores outlook/caldav (extensión) |
| Adaptarse a clínica, ventas, almacén, inmobiliaria | Perfiles; añadir perfil almacén/mayorista |
| Fábrica: recrear/adaptar instalaciones con prompts y skills | **F27 (nuevo)** |

## Borrador de especificación de los módulos nuevos

- **F22 Conmutación de proveedores de IA.** Registro de proveedores con estado
  (configurado / prueba superada / activo / degradado / caído), orden de preferencia,
  failover automático por error, cuota o latencia, presupuesto heredado y registro auditable
  de cada conmutación. Una caída de proveedor no detiene el producto ni la conversación.
- **F23 Telemetría de costos.** Medición por mensaje, conversación, prompt, proveedor, campaña y
  período: tokens de entrada/salida, costo Meta por categoría de mensaje, presupuesto mensual,
  alertas y ventana administrativa. Valores reales reportados por el proveedor, no estimaciones fijas.
  Desde 01-10-2026 Meta cobra por mensaje entregado incluso en la ventana de servicio 24 h;
  esta ventana pasa de opcional a obligatoria.
- **F24 Evals de prompts.** Cada prompt versionado (`prompts/runtime` R01–R06) con suite de
  evaluación sintética; ejecución local en cada entrega; umbral exigido para publicar la versión;
  resultados archivados con la entrega. Ningún prompt entra en producción sin sus evals.
- **F25 Seguridad como suite fija.** `tests/security` se ejecuta en cada entrega: permisos por rol,
  sesiones y revocación, CSRF, inyección, archivos privados. Cada módulo nuevo agrega su caso
  negativo de permisos.
- **F26 Semáforo por número de teléfono.** Números múltiples con propósito declarado (servicio al
  cliente, marketing), estado de calidad por número (verde/amarillo/rojo según métricas propias y
  del proveedor), reglas de ruteo por tipo de tráfico, límites de volumen por número, pausa
  automática al degradarse y alertas. **Cumplimiento:** la rotación no se usa para evadir medidas
  de Meta; se protege la calidad separando tráfico, respetando ventanas y plantillas aprobadas,
  y un número sancionado se gestiona con el proceso oficial de apelación.
- **F27 Fábrica de instalaciones.** Kit de recreación por cliente: scaffolding CLI, perfiles
  empaquetados, prompts y skills de adaptación, checklist de instalación y pruebas de aceptación
  repetibles. Objetivo: recrear una instalación nueva en horas, no semanas.

## Investigación de mercado (24-10-2026) — base para superar

- **GoHighLevel** (97–497 USD/mes por agencia, precios publicados consultados el
  24-10-2026; sujetos a cambio): CRM multicanal white-label por suscripción.
  **Objetivo declarado del propietario**, no afirmación demostrada: ofrecer con pago único
  y código entregado un valor comparable o superior POR INSTALACIÓN. Cualquier afirmación
  de superioridad exige una comparación con muestra, criterios y fuentes fechadas; no
  se declara «supera a todas» ni «ninguna entrega código» como hechos universales.
- **WhatsApp Business Platform** (FAQ oficial, consulta 24-10-2026): desde octubre de 2026
  cambia el cobro de mensajes: cada número tiene una **franquicia de 1.000 mensajes de
  servicio por mes**; desde el mensaje 1.001 se cobran por mensaje entregado, con tarifa
  variable por **categoría (marketing/utility/servicio/autenticación) y mercado (país del
  destinatario)**, más el margen del BSP si se usa uno. Las plantillas dentro de la ventana
  de 24 h iniciada por el usuario y los puntos de entrada libres (p. ej. anuncios click-to-
  WhatsApp) tienen sus propias reglas y excepciones publicadas. **Cifras exactas**: ver la
  tabla de tarifas vigente de Meta en el momento de cada instalación; no fijar un motor
  tarifario estático en el producto. Esto justifica F23 (telemetría de consumo real por
  número/categoría) y presupuestar cada campaña. Distinción obligatoria: costo real
  reportado por el proveedor ≠ estimación propia.
- **Telegram Bot API**: gratuita, sin aprobación (token por @BotFather); modo negocio desde 7.2.
  **Instagram/Messenger**: API gratuita pero requieren Meta App Review, cuenta profesional y
  ventana de 24 h. Orden de conectores: Telegram → WhatsApp → Messenger/Instagram.
- **Bandejas multicanales** (respond.io, SleekFlow, Trengo; revisión 24-10-2026 basada en
  sus sitios y comparaciones propias de los vendedores — sesgo comercial posible): patrón
  de inbox unificado con asignación, estados y SLA. Sus modelos son suscripción; no se
  verificó que «ninguna» entregue código con pago único: tratarlo como diferenciador
  objetivo a demostrar, no como hecho probado.
- **Calendarios**: Google y Microsoft Graph usan REST; Apple sólo CalDAV; no existe
  bidireccionalidad nativa Google↔Outlook (webhooks/polling + deduplicación propias).
  El contrato de conectores de 02 agrega adaptadores `outlook` y `caldav`.
- **Odoo Community**: ERP gratuito autoalojado (CRM/inventario/ventas/facturación); valida el rol
  del instalador técnico, pero no trae IA conversacional multicanal integrada.

## Camino inmediato

1. Núcleo funcional local en V4: `pyproject.toml` + `src/crm_premium` (bootstrap, identity,
   organization, contacts, scheduling reutilizado de V3) + PostgreSQL local + pruebas.
   Entrega con `docs/entregas/PR00B/ENTREGA.md` adaptada al arranque funcional.
2. Después: commerce/inventory (cientos de artículos), conversations con WhatsApp simulado,
   y F23 telemetría desde el primer proveedor de IA conectado.
3. Los módulos F22–F27 se integran al catálogo de aceptación (05) al llegar su fase.

## Nota de gobernanza

El propietario fijó el arranque por núcleo funcional en esta sesión; queda registrado aquí y en
ESTADO.md. Se conservan: una fase a la vez, evidencia real de pruebas, ENTREGA.md por fase,
revisión antes de la siguiente y actualización de continuidad al detenerse.
