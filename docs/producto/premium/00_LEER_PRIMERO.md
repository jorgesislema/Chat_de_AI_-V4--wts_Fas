# CRM Premium — expediente para construir con GLM

## Entrada vigente para GLM: documento21

Leer21_PROMPT_INICIO_CERRADO_Y_ENTREGAS_UI.md para la próxima tarea cerrada E01-R; no implementar todo el expediente de una vez. Se conservan15–18;19 define bandeja/humano/alarma y20 los recorridos de UI accionable. Todo pendiente de código/pruebas por GLM. El dictamen E01 devuelto sigue vigente; sus120 declaradas no acreditan guardar desde navegador ni aislamiento completo.

## Lectura actual para GLM — prompts precisos 15–18

Primero15_PROMPT_GLM_E01R_AGENDA.md (E01 devuelta; reproducción de reserva/permisos/UI). Después17_PROMPT_GLM_CATALOGO_VARIANTES.md (cepillo azul como variante tipada, foto/detalle/stock/precio/ETA por UI). Diseño de leads en16_CONTRATO_LEAD_SCORING.md y ejecución por etapas en18_PROMPT_GLM_SCORING_POR_ENTREGAS.md, sin saltar E03-O. No implementar todos a la vez. Instalación privada por cliente confirmada; sin SaaS multiempresa.

## Última instrucción: operaciones visibles e inicio E01

CORR01D cierra C1/C2 y E00B aceptada: iniciar E01 según contrato. Leer 13_RECORRIDOS_AGENDA_VENTAS_CATALOGO.md y 14_PROMPT_GLM_RECORRIDOS_VISIBLES.md: agenda, ventas/retiro/pago/tratamientos, inventario/fotos/detalles/ETA y RAG híbrido. T59–T70 pendientes de implementar/probar; no reemplazan reglas/ERP/análisis empresarial.

## Lectura vigente — alcance empresarial

Leer también 08_ALCANCE_EMPRESARIAL.md, 09_PROMPTS_EMPRESARIALES.md y 10_ACEPTACION_EMPRESARIAL.md. Varias sucursales y más de cinco personas son el objetivo; F17 obligatorio, reglas editables desde UI y catálogo con fotos/fichas/stock por sede. No aplicar antiguos límites comerciales de una sede/cinco cuentas. CORR01 sigue pendiente de cierre; nuevos módulos sólo diseñados.

## Traslado a V4 — instrucción vigente del 24-10-2026

Trabajo y entregas: H:\git\Agente de reserva V4. Fuente histórica V3, sólo lectura: H:\git\chat-clinica-dental - copia\chat-reserva-V3. La aplicación aún no se ha copiado a V4. Las referencias a código/pruebas/arranques «existentes» se refieren a V3 hasta que GLM los reutilice y verifique en V4. PR00 debe inventariar ambos lugares; PR00B crea la base mínima en V4 y documenta reutilización. Preservar comportamiento mediante pruebas en V4, sin modificar V3. No exigir que código aún no trasladado ya arranque en V4; reportar su estado real y demostrar arranque de lo efectivamente incorporado. Los documentos de continuidad de V4 están en esta raíz; historial y evidencias V3 se consultan en la fuente. No copiar secretos, datos ni entornos.

Fecha: 23-10-2026. Estado: diseño propuesto, sin implementación ni pruebas ejecutadas.
Origen: petición del propietario de diseñar la edición superior, por encima de USD 1.500, tomando como base chat-reserva-V3, con PostgreSQL local, contraseña, análisis de datos/mercado/leads y edición de plantillas aprobadas. No escribir código en esta entrega.

## Decisiones y preguntas

Confirmado: usar esta base; PostgreSQL local; modelo estrella para análisis; acceso con contraseña; especificación, lógica, prompts y plan de pruebas para GLM; ninguna implementación ahora. Codex dirige y revisa; GLM implementa y ejecuta pruebas. El propietario lo identifica como «glm 3 flas»; no se presupone una versión técnica distinta ni se cambia el modelo de ninguna herramienta.

Decisiones comerciales confirmadas y supuestos explícitos:

- «Leans» significa leads, posibles clientes.
- Producto multirrubro: clínicas, tiendas, colegios e inmobiliarias mediante perfiles; no historia clínica.
- Una organización por instalación. Varias sucursales posibles en Premium; no plataforma SaaS multiempresa.
- WhatsApp y Google Calendar como primeras integraciones; arquitectura preparada para Telegram, Facebook Messenger, Instagram, correo y CRM/ERP externos. Preparado no significa conectado y probado.
- USD 1.500–10.000 corresponde al cobro freelancer por instalación/adaptación en VPS del cliente, con código para el cliente, sin suscripción propia y con mantenimiento opcional. No es presupuesto de desarrollo completo desde cero.
- PostgreSQL «local» se interpreta como instalado en la misma VPS, privado para la aplicación. Varios equipos acceden mediante navegador y HTTPS. Desarrollo y pruebas pueden ejecutarse localmente.

Preguntas pendientes por instalación: usuarios/profesionales/sucursales; volumen de leads/mensajes; presupuesto de proveedores; idiomas y monedas; país de venta; datos históricos y primeros conectores contratados. No pedir contraseñas en el chat: se crearán durante instalación.

## Cómo leer y usar

1. `01_PRODUCTO_Y_MERCADO.md`: catálogo de funciones, investigación y alcance comercial.
2. `02_LOGICA_DATOS_Y_SEGURIDAD.md`: reglas, PostgreSQL, modelo estrella y métricas.
3. `03_EXPERIENCIA_Y_PLANTILLAS.md`: pantallas y edición segura de contenido aprobado.
4. `04_PROMPTS_GLM.md`: instrucciones de construcción por entregas y prompts de IA del producto.
5. `05_ACEPTACION.md`: casos de prueba y criterios de salida.
6. `06_ESTRUCTURA_REPOSITORIO.md`: árbol de destino, responsabilidades, transición y prompt inicial.

Orden de construcción actualizado: PR00 documenta inventario y estructura; PR00B crea la base ejecutable mínima con compatibilidad; PR01 incorpora PostgreSQL. Después continúan las fases funcionales. GLM crea código y ejecuta pruebas; Codex mantiene documentación y revisión. No crear toda la estructura con módulos ficticios ni reorganizar el legado sin regresión.

Esta edición amplía el plan básico; no cambia su límite de tres profesionales. En Premium, PostgreSQL sustituirá SQLite como registro autoritativo una vez validada la migración. Flask/Jinja y Python se conservan inicialmente. No mantener dos registros operativos en escritura simultánea.

## Diagnóstico de la base

Se leyeron AGENTS.md, MAPA.md, PLAN.md, ESTADO.md, README.md, plantilla de navegación y principio de la capa analítica; se inspeccionó `docs/crm-preview.png`. No se ejecutó la aplicación ni se inspeccionaron bases con datos personales.

- Reutilizable: acceso, sesiones, agenda, reglas compartidas web/bot, sincronización con outbox y esquema estrella inicial.
- El estado documentado acepta P01/P02/G01B. P03 conserva pendiente validación externa en calendario exclusivo. No se convierte esa evidencia histórica en pruebas de esta entrega.
- Faltan módulos comerciales completos y la aceptación de bandeja/pausa durable, ventas, conocimiento, reportes y empaquetado.
- Roles actuales administrador/usuario son insuficientes para permisos por sucursal, finanzas, exportaciones y aprobaciones.
- La capa estrella existente usa SQLite y principalmente citas; no demuestra que haya análisis de leads, ventas o mercado completo.
- La imagen muestra una base visual limpia en verde y blanco. Conviene conservar identidad y agenda, y ampliar organización, tablas, filtros y paneles; no justificar una reescritura por el precio.

## Qué significa listo

Documentación generada y evidencia de cada fase: `docs/entregas/README.md`. GLM guarda una carpeta por entrega con reporte, pruebas y capturas; Codex escribe su dictamen en revisión separada. El índice `docs/entregas/INDICE.md` permite retomar la revisión sin depender del chat.

Expediente listo para revisión de alcance y para que GLM empiece la fase documental PR00 cuando el propietario solicite construir. No es producto terminado, cotización contractual ni autorización para enviar campañas reales. Las decisiones pendientes deben cerrarse antes de implementar sus funciones dependientes.
