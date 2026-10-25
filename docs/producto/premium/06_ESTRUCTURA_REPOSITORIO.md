# Estructura del repositorio y arranque para GLM

## Traslado a V4 — instrucción vigente del 24-10-2026

Trabajo y entregas: H:\git\Agente de reserva V4. Fuente histórica V3, sólo lectura: H:\git\chat-clinica-dental - copia\chat-reserva-V3. La aplicación aún no se ha copiado a V4. Las referencias a código/pruebas/arranques «existentes» se refieren a V3 hasta que GLM los reutilice y verifique en V4. PR00 debe inventariar ambos lugares; PR00B crea la base mínima en V4 y documenta reutilización. Preservar comportamiento mediante pruebas en V4, sin modificar V3. No exigir que código aún no trasladado ya arranque en V4; reportar su estado real y demostrar arranque de lo efectivamente incorporado. Los documentos de continuidad de V4 están en esta raíz; historial y evidencias V3 se consultan en la fuente. No copiar secretos, datos ni entornos.

Fecha: 23-10-2026. Actualización solicitada: construir Premium empezando por un repositorio ordenado. Este documento define la estructura futura; Codex no crea código, mueve módulos ni modifica la aplicación en esta entrega.

## Decisión

Usar un monolito modular Python con un paquete principal `crm_premium` dentro de `src/`. Web, API/webhooks y trabajador son puntos de entrada del mismo producto y comparten servicios. Cada módulo tiene responsabilidad y dependencias explícitas. Conservar Flask/Jinja y las reglas útiles de la base actual mediante una transición gradual.

La nueva raíz de trabajo es `H:\git\Agente de reserva V4`. V3 permanece como fuente externa de lectura, sin cambios. Construir V4 aquí por reutilización controlada; no copiar todo V3 ni su Git. No inicializar Git como parte del traslado documental. La estructura siguiente es destino, no inventario de archivos ya disponibles.

## Árbol de destino

```text
Agente de reserva V4/
├── AGENTS.md
├── README.md
├── MAPA.md
├── pyproject.toml                 # Metadatos, dependencias y herramientas
├── .env.example                  # Nombres y ejemplos sin secretos
├── .gitignore
├── src/
│   └── crm_premium/
│       ├── bootstrap/            # Creación de app, configuración y composición
│       ├── entrypoints/
│       │   ├── web/              # Rutas web y API autenticada
│       │   ├── webhooks/         # Recepción por proveedor y normalización
│       │   ├── worker/           # Colas, tareas y ETL programado
│       │   └── cli/              # Administración y mantenimiento
│       ├── shared/               # Tiempo, dinero, errores e IDs; mínimo común
│       ├── modules/
│       │   ├── identity/         # Usuarios, sesiones, roles y autorizaciones
│       │   ├── organization/     # Negocio, sedes, equipos y perfiles
│       │   ├── contacts/         # Contactos, identidades y consentimiento
│       │   ├── opportunities/    # Embudo, tareas y señales de leads
│       │   ├── scheduling/       # Agenda, recursos y reservas
│       │   ├── conversations/    # Hilos, mensajes y transferencia humana
│       │   ├── templates/        # Versiones y aprobaciones de mensajes
│       │   ├── campaigns/        # Segmentos, campañas y experimentos
│       │   ├── automations/      # Reglas y ejecuciones controladas
│       │   ├── commerce/         # Cotizaciones, ventas y pagos
│       │   ├── inventory/        # Productos, ubicaciones y movimientos
│       │   ├── knowledge/        # Archivos, publicación y permisos de RAG
│       │   ├── analytics/        # Modelo semántico, ETL e indicadores
│       │   ├── market/           # Observaciones, fuentes y comparativas
│       │   └── assistant/        # Orquestación y herramientas autorizadas
│       ├── infrastructure/
│       │   ├── persistence/      # Conexiones/repositorios PostgreSQL
│       │   ├── messaging/        # Outbox, trabajos y arrendamientos
│       │   ├── storage/          # Almacenamiento privado de archivos
│       │   ├── observability/    # Logs redactados, salud y auditoría técnica
│       │   └── integrations/
│       │       ├── whatsapp/
│       │       ├── telegram/
│       │       ├── messenger/
│       │       ├── instagram/
│       │       ├── email/
│       │       ├── google_calendar/
│       │       ├── external_crm/
│       │       ├── erp/
│       │       └── ai_provider/
│       └── presentation/
│           ├── templates/        # Jinja: base, componentes y módulos
│           └── static/           # CSS, JS e imágenes propios
├── migrations/
│   ├── operational/              # Esquema operativo e integración
│   └── analytics/                # Estrellas y vistas analíticas
├── config/
│   ├── profiles/                 # Clínica, tienda, colegio e inmobiliaria
│   └── examples/                 # Configuración ilustrativa sin credenciales
├── prompts/
│   ├── runtime/                  # Versiones R01–R06 del producto
│   └── evaluations/              # Casos sintéticos y respuestas esperadas
├── tests/
│   ├── unit/
│   ├── integration/              # PostgreSQL temporal y servicios internos
│   ├── contracts/                # Contratos de adaptadores y capacidades
│   ├── e2e/                      # Recorridos web
│   ├── security/                 # Permisos, sesiones, archivos e inyección
│   ├── migration/                # Ensayos SQLite → PostgreSQL
│   ├── fixtures/                 # Datos exclusivamente sintéticos
│   └── performance/              # Carga y mediciones reproducibles
├── scripts/
│   ├── dev/                      # Preparación local
│   ├── maintenance/              # Respaldo, restauración y diagnóstico
│   └── migration/                # Herramientas del corte entre bases
├── deploy/
│   ├── vps/                      # Servicios, proxy HTTPS y guía de operación
│   └── local/                    # Configuración de desarrollo/pruebas
└── docs/
    ├── producto/                 # Expediente, estado, entregas y evidencia
    ├── architecture/             # Decisiones y contratos técnicos
    ├── operations/               # Instalación, actualización y recuperación
    └── user/                     # Guías de administrador y usuarios
```

En PR00B se crean sólo las carpetas y archivos necesarios para una base ejecutable mínima, no cientos de archivos vacíos. Cada conector futuro se documenta como reservado hasta tener implementación; un directorio o archivo vacío nunca equivale a una integración. No añadir directorios `services`, `utils` o `helpers` gigantes que concentren todo el producto.

## Organización interna de un módulo

Cada módulo suficientemente complejo puede contener `domain/` (entidades y reglas), `application/` (casos de uso y contratos de repositorios), y un archivo público de interfaz. Los módulos pequeños pueden empezar con archivos claros, sin multiplicar capas artificialmente. La persistencia concreta queda en infraestructura; rutas y formularios en puntos de entrada/presentación.

Las rutas validan identidad y entradas, llaman un caso de uso y presentan resultado; no contienen SQL ni reglas comerciales. Dominio no importa Flask, SDK de proveedores, configuración global ni conexiones. Casos de uso dependen de contratos; infraestructura implementa esos contratos. Bootstrap conecta implementaciones. Referencia a otro módulo mediante interfaz pública, no acceso a sus tablas o archivos privados.

`shared/` contiene únicamente conceptos realmente compartidos y estables. El asistente usa herramientas autorizadas de módulos; no lee toda la base ni calcula cifras por su cuenta. ETL lee fuentes bajo contrato y sólo escribe BI. Migraciones operativas y analíticas pueden separarse por carpetas, pero deben tener orden/dependencias y una versión global coherente de despliegue.

## Correspondencia con la base actual

PR00 entregará inventario completo; este mapa inicial no autoriza movimientos ciegos.

| Origen actual | Destino conceptual | Condición de transición |
|---|---|---|
| `crm/app.py` y `run_crm.py` | bootstrap y entrypoint web/CLI | Mantener arranque actual con delegación durante transición |
| `crm/store.py`, `database/` | persistencia y migraciones | Inventariar SQL/SQLite antes; PostgreSQL se introduce en PR01 |
| `crm/reservation_service.py`, `agenda_time.py` | módulo scheduling y tiempo compartido | Preservar reglas aceptadas y pruebas temporales/DST |
| `crm/calendar.py` | integración google_calendar y scheduling | Conservar outbox y política de conflictos |
| `api/main.py`, `api/procesamiento.py` | webhooks, conversations y worker | Preservar autenticidad, idempotencia y pausa humana |
| `api/agent.py`, `tools/` | assistant, adaptadores y scripts según responsabilidad | Clasificar antes de mover; no convertir todos los tools en SDK externos |
| `crm/analytics.py` | analytics, persistencia BI y migraciones analíticas | Conservar definiciones y cambiar almacenamiento en la fase correspondiente |
| `crm/business_profile.py`, `perfiles/` | organization y config/profiles | Compatibilidad validada, sin perder precedencia de zona |
| `crm/templates/`, `crm/static/` | presentation | Conservar rutas estáticas, accesibilidad e identidad visual |
| `ui/`, `app_corporativa.py` | Legado identificado en documentación | No borrar ni mover hasta inventariar consumidores |
| Pruebas existentes | tests, clasificación progresiva | No borrar cobertura ni contar pruebas movidas como cobertura nueva |

No mover entornos virtuales, archivos `.db`, backups ni secretos al árbol fuente. No copiar `.env` a ejemplos. Datos y adjuntos de ejecución viven fuera del paquete y del repositorio en rutas configurables; en VPS bajo directorios privados del servicio. Requisitos y empaquetado tendrán una fuente autoritativa; si se conservan archivos requirements por compatibilidad, documentar cómo se mantienen sin divergencia.

## Fases de organización

Carpeta transversal obligatoria: `docs/entregas/`, ya preparada documentalmente con README.md, INDICE.md y PLANTILLA_ENTREGA.md. Cada fase guarda `docs/entregas/<ID>/ENTREGA.md`, diseño, cambios, ejecuciones de pruebas con logs/reportes/capturas, pendientes y revisión separada de Codex. Véase su README para el árbol completo. Esta carpeta también se usa desde PR00; no esperar a PR00B. Toda referencia a REPORTE_PRxx.md en este expediente significa el ENTREGA.md de esa fase. Evidencia histórica permanece en su ubicación, enlazada sin presentarla como prueba nueva.

1. PR00: inventario, árbol de destino ajustado, dependencias y mapa archivo actual → destino; sólo documentación.
2. PR00B: GLM crea base mínima del paquete, configuración, puntos de entrada, pruebas de arranque y guías; adapta una parte pequeña para demostrar delegación. No reubica todo el legado ni cambia base de datos. La aplicación actual debe conservar su comportamiento.
3. PR01–PR08: cada módulo se incorpora al destino al implementar su fase; mover código existente sólo con dependencias y regresión del área cubiertas. No mantener dos copias de una misma regla activa.
4. PR09: conectores por contrato real. PR10: empaquetado y retirada de compatibilidad cuando no queden consumidores y exista evidencia. Documentar lo que siga siendo legado.

## Entregables para aceptar PR00B

- Árbol real y diferencia frente al propuesto, con razones; archivo de responsabilidades y dependencias.
- Instalación del paquete en un entorno limpio y arranque web/trabajador/CLI sin hacks de rutas ni `sys.path` manual.
- Ninguna conexión, migración, creación de admin o envío al importar módulos. Conectores no configurados no impiden arrancar capacidades que no los necesitan.
- Arranque y pruebas existentes compatibles; sin pérdida de rutas, archivos estáticos, reglas o datos. Reportar fallos previos como previos, con reproducción.
- Configuración validada por ambiente, muestra sin secretos, datos temporales sólo en pruebas.
- Informe `REPORTE_PR00B.md` con pruebas realmente ejecutadas y procedimiento de reversión de los cambios estructurales.
- T36–T38 del plan de aceptación. Aceptación de Codex antes de PR01.

## Prompt de inicio para entregar a GLM

Lee AGENTS.md, docs/producto/ESTADO.md, PLAN.md, MAPA.md y todos los documentos de docs/producto/premium, especialmente 06_ESTRUCTURA_REPOSITORIO.md. Tu tarea actual es PR00: auditar y diseñar la estructura ordenada del repositorio antes de construir. Entrega el inventario actual, mapa origen-destino por archivo, árbol propuesto, responsabilidades, dependencias, compatibilidad de arranques/pruebas, riesgos y plan concreto de PR00B. Usa la base existente y conserva las reglas aceptadas. Codex dirige/revisa y tú implementarás. En esta PR00 sólo escribe documentación: no muevas ni borres código, no migres bases, no leas secretos ni despliegues. Termina presentando REPORTE_PR00.md para revisión. PR00B será la creación de la estructura ejecutable mínima después de aceptar este diseño; PR01 empezará sólo cuando PR00B esté aceptada.
