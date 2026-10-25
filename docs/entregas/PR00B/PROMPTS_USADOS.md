# PROMPTS USADOS — trazabilidad de construcción (PR00B)

Registro de los prompts/instrucciones que produjeron esta entrega, para
auditarla y recrearla. Sesión del 24-10-2026 con el propietario; agente:
ZCode/GLM (modelo subyacente: GLM). Este archivo se actualizará en cada fase.

## Cadena de instrucciones del propietario

1. «Vas a crear un nuevo proyecto, analízalo, pregunta lo que necesites; debe
   quedar funcional para correrlo en local.»
2. Aclaración de línea de producto: «Es una versión más avanzada de V3 con
   esteroides: reservas y respuesta de información como núcleo; análisis de
   leads, de datos y de mercado; editor de plantillas Meta; chat interno RAG+BD;
   evals por prompt; seguridad; telemetría de tokens; failover entre IAs;
   semáforo por número de teléfono (servicio/publicidad); redes sociales;
   multirrubro; fábrica de instalaciones por prompts y skills.»
3. «Haslo; recuerda frontend profesional con gráficos que cubra lo que vale y
   más; todo testeado; guardar informes y prompts para auditarlo y recrearlo.»
4. Credenciales del servidor: probar contraseñas dadas oralmente y crear una
   sola base de datos para el proyecto (ver ENTREGA.md, decisión D2).
5. «Continúa; cumple los más altos estándares de gobernanza europea y
   latinoamericana; mantén el testeo y la trazabilidad.»

## Respuestas del cuestionario (AskUserQuestion)

- Ubicación: **H:\git\Agente de reserva V4**.
- Arranque: **núcleo funcional ya** (sustituye PR00 documental extenso).
- Primer corazón: **agenda/citas**.
- Base de datos: **PostgreSQL desde el inicio**.

## Prompt operativo efectivo (recreable)

> Construye en H:\git\Agente de reserva V4 el núcleo funcional del CRM Premium
> (edición 2000+) siguiendo docs/producto/premium/06_ESTRUCTURA_REPOSITORIO.md:
> paquete `src/crm_premium` con módulos identity, organization, contacts,
> scheduling y dashboard; PostgreSQL como única base (una base por proyecto);
> frontend Flask/Jinja profesional sin CDN (CSP estricta) con login, panel con
> KPIs y gráficos, agenda día/semana/mes, contactos, ajustes y usuarios;
> reutiliza de V3 sólo las reglas probadas de agenda (zona IANA, DST, conflictos
> por intervalo, versión optimista, estados operativos, historial y auditoría)
> portándolas a PostgreSQL; todo testeado (unit + integración + seguridad +
> flujo web) con base temporal; datos demo sintéticos; registra ENTREGA.md,
> INFORME_PRUEBAS.md, PROMPTS_USADOS.md y evidencias; documenta protección de
> datos (RGPD/LODPD). No leer secretos; no datos reales; sin commit ni push.

## Técnicas y material de referencia usado por el agente

- Lectura de V3: `crm/reservation_service.py`, `crm/agenda_time.py`
  (puerto de reglas), documentos del expediente V4 (00–06) y VISION 07.
- Investigación web (24-10-2026): GoHighLevel (precios agencia),
  WhatsApp Business Platform (cobro por mensaje desde 01-10-2026),
  Telegram Bot API, Instagram/Messenger (App Review), Google/Outlook/CalDAV
  (sincronización), Odoo Community. Fuentes citadas en
  `docs/producto/premium/07_VISION_EDICION_2000.md`.
- Sin generación por plantillas externas: todo el código fue escrito en la
  sesión y verificado con pytest + navegador real.

## Reconstrucción del entorno (comandos reales de la sesión)

```bash
python -m venv .venv
unset CURL_CA_BUNDLE   # el sistema hereda un CA bundle inválido de PostgreSQL 18
./.venv/Scripts/python.exe -m pip install -e ".[test]"
python -m crm_premium migrate
python -m crm_premium seed-demo --yes
python -m crm_premium run --port 8055
./.venv/Scripts/python.exe -m pytest tests/
```
