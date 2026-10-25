# Auditoría independiente Codex — 24-10-2026

## Dictamen

**DEVUELTA PARA CORRECCIONES.** Hay un núcleo real de aplicación, pero el estado actual no acredita la aceptación de PR00B ni el cumplimiento del producto Premium completo. Comercio, BI y asistente ya existen y exceden el inventario de la entrega registrada. La autorización documental posterior del documento 07 permite empezar con núcleo y PostgreSQL: no se considera defecto haber omitido el PR00 extenso.

Codex sólo auditó y escribió documentación; no corrigió aplicación, pruebas ni datos. La prioridad inmediata es reparar integridad, privacidad y reglas de agenda, documentar el código real y presentar una nueva entrega revisable. Las funciones futuras ausentes son alcance pendiente, no automáticamente defectos de una primera fase.

## Alcance y límites de comprobación

Lectura de AGENTS, PLAN, ESTADO, MAPA, expediente 00–07, entrega PR00B, esquema/migraciones, ocho archivos test y código de web, identidad, organización, contactos, agenda, comercio, BI y asistente. Revisión de existencia de archivos; no recorrido visual independiente del navegador en esta auditoría.

Ejecutado: 10 pruebas de tiempo con pytest sin conftest y sin caché; todas pasaron. Reproducciones aisladas con Flask test client y mocks, política horaria pura y agregado SQL en SQLite en memoria. No se leyó .env, no hubo login real ni conexión PostgreSQL, llamadas externas, migraciones o escritura en bases. SQLite sólo se usó para demostrar aritmética CASE del SQL extraído; no valida semántica/concurrencia de PostgreSQL.

Inventario AST: 70 funciones test_ en 8 archivos. No es un resultado de 70 pruebas ejecutadas ni cuenta de parametrizaciones. El resumen almacenado de 47 pasadas es evidencia anterior de GLM, sin revalidación de Codex para el código adicional.

## Hallazgos para corregir

### R01 — P1 — Credencial administrativa expuesta en documentación

ESTADO.md y docs/entregas/PR00B/ENTREGA.md contienen una contraseña descrita como temporal del administrador. No se reproduce en este reporte ni se probó su vigencia. Es información de acceso operativo, no un fixture sintético. La afirmación «sin contraseña predeterminada» no resuelve publicar la credencial.

Solicitar al propietario rotación por vía local segura e invalidación de sesiones; el implementador debe facilitar un procedimiento sin imprimir el secreto. Eliminar valores de acceso de documentación y evidencias mediante redacción explícita; conservar constancia del incidente y revisar historial de versiones si existe, sin asumir push. No borrar pruebas históricas legítimas. No dar por rotada la contraseña sólo por limpiar Markdown.

### R02 — P1 — Ventas anuladas producen neto negativo y alteran el período original

src/crm_premium/modules/analytics/service.py:96–103 sustituye las líneas originales por importes negativos cuando sales.status es reversed. modules/assistant/service.py:56–57 hace lo mismo con total. commerce/service.py:396 actualiza estado de una venta; no crea un evento compensatorio independiente que conserve el positivo.

Una única venta de 100 totalmente anulada devuelve -100 en el agregado del asistente; el neto acumulado esperado es 0. BI sigue la misma fórmula. Al reconstruir, se cambia el período de creación original en vez de registrar la reversión en su fecha. tests/test_analytics.py:44–52 exige diferencia de 350, pero con sustitución +350 → -350 la diferencia es 700; la expectativa y la implementación divergen. No se ejecutó esa prueba contra PostgreSQL.

Corregir mediante movimientos positivos/compensatorios con fecha y referencia, sin destruir el original. Unificar ventas netas entre BI y asistente. Probar venta única, reversión total, mezcla de ventas y reversión en período posterior con valores absolutos calculados a mano.

### R03 — P1 — Política horaria acepta intervalos fuera de horario

modules/organization/service.py:112 en adelante sólo comprueba inicio y «último minuto» truncado. Con horario lunes–viernes 09:00–17:00 UTC, acepta lunes 26-10 10:00 → martes 27-10 11:00, atravesando toda la noche cerrada. También acepta 16:00 → 17:00:30. Ambos resultados reproducidos: None (permitido), cuando deben rechazarse.

Restituir validación del intervalo completo por instantes, cada fecha atravesada y límite exacto al segundo, con zona IANA/DST. Mantener intervalo semiabierto y cierre exacto permitido. No arreglar sólo estos ejemplos mediante condiciones especiales.

### R04 — P1 — Historial del asistente compartido entre usuarios

entrypoints/web/app.py:566–570 invoca assistant.history(db(), limit=10) para cualquier usuario autenticado. modules/assistant/service.py:history con user_id=None devuelve historial global, incluyendo pregunta, respuesta y data.

Reproducción de ruta con usuario sintético role=user confirmó llamada sin user_id y respuesta 200. Es comprobación del flujo/autorización con mock, no consulta a conversaciones reales. Un usuario ordinario puede ver preguntas/respuestas ajenas. La búsqueda de conocimiento tampoco tiene permisos/publicación en knowledge_docs.

Filtrar por usuario/ámbito desde servidor; vista global sólo con permiso independiente. Las herramientas del asistente deben heredar el alcance del usuario; user_id como dato de auditoría no es autorización.

### R05 — P1 — Usuario ordinario modifica ajustes globales; permisos Premium incompletos

entrypoints/web/app.py:340–363 protege POST /settings únicamente con login_required. Cualquier usuario puede cambiar nombre, zona, moneda y horario del negocio. No hay distinción admin para esta acción; influye en nuevas reservas y representación financiera. identity/service.py sólo permite admin/user. Contactos, ventas, agenda y BI no filtran por responsable/sede.

Restringir ajustes globales inmediatamente. Documentar el alcance del núcleo de dos roles; diseñar e implementar permisos granulares por fases antes de presentar F01 completo. Cubrir rutas directas y herramientas, no sólo menú.

### R06 — P2 — Cambio de rol no revoca sesiones

identity/service.py:209–219 cambia role sin revocar sessions. user_for_session vuelve a leer el rol, lo cual reduce persistencia de privilegios antiguos, pero no cumple la exigencia explícita de invalidar sesiones al cambiar rol. No confundir refresco de rol con revocación.

Revocar en la misma transacción y probar que un token anterior deja de autenticar después de promoción/degradación.

### R07 — P2 — Login deja inválido el formulario tras un intento incorrecto

entrypoints/web/app.py:149–154 genera token nuevo, elimina cookie csrf_login y devuelve formulario. Reenviar ese formulario obtiene 400 por CSRF en lugar de intentar autenticar. Reproducción: GET → fallo de credenciales 401 → segundo intento 400.

Regenerar par cookie/formulario coherente también tras error y tras token caducado. Probar incorrecta → correcta sin recarga manual y conservar rechazo de token ajeno.

### R08 — P1 antes de aceptar analítica — Demo, costos e identidad de métricas

BI guarda es_demo, pero overview y las vistas no lo excluyen por defecto. rebuild_bi convierte costo desconocido en cero y usa products.cost actual, no costo histórico de línea. Top global limitado a ocho mezcla servicios/productos antes de separarlos: una categoría puede desaparecer aunque tenga ventas.

assistant._detect interpreta «recaudacion de hoy» como ventas y «cobros de hoy» como precio. create_sale fija paid=total automáticamente sin movimientos de cobro independientes. No hay abonos, cartera ni devolución parcial y no debe afirmarse que se soportan.

Excluir demo por defecto con modo visible, preservar NULL/cobertura y costo histórico para operaciones nuevas con migración explícita de desconocidos. Separar métricas de ventas/cobros y responder «no disponible» donde aún no exista dato. No inventar pagos reales a partir de venta confirmada.

### R09 — P2 — Entregas, estado y pruebas no corresponden al árbol actual

PR00B declara dos migraciones, cinco suites/47 pruebas y núcleo sin BI/asistente; el árbol contiene cuatro migraciones y módulos commerce/analytics/assistant, ocho archivos y 70 funciones de prueba. Sólo hay una fila PR00B y su dictamen estaba pendiente. No hay reportes de entregas adicionales ni evidencia actual suficiente de esos módulos.

No se puede determinar por el árbol si el trabajo adicional fue autorizado en otro diálogo; documentar procedencia y alcance, sin acusar una acción no demostrada. Actualizar el inventario y separar evidencia histórica de ejecución nueva. Mantener fallos y guardar código probado/entorno/salidas, no sólo un resumen manuscrito.

La fixture tests/conftest.py carga .env, usa DATABASE_URL como fallback y crea/elimina bases en ese servidor. No se ejecutó la suite completa para evitar acceso automático al servidor operativo. Requerir conexión de pruebas separada y opt-in explícito para servidor compartido; URL compuesta con rsplit es frágil ante parámetros/formatos. Limpieza en finally, incluso si falla la migración.

### R10 — P2 — Calidad de empaquetado y concurrencia pendiente de acreditar

No hay evidencia de instalación wheel fuera del checkout: migraciones se localizan mediante parents[4] y assets/SQL no tienen declaración explícita de empaquetado en pyproject. Una instalación editable no demuestra instalación distribuida. Hipótesis pendiente de prueba de wheel, no fallo de instalación reproducido.

create_sale toma advisory locks en orden de líneas recibido y reverse_sale según orden SQL sin orden explícito. Ventas concurrentes A,B / B,A pueden adquirir locks en orden inverso; falta prueba de deadlock y tratamiento documentado. Riesgo estático, no reproducido en PostgreSQL en esta auditoría. Ordenar claves y probar antes de certificar concurrencia comercial completa.

### R11 — P2 — Tarifas y afirmaciones comerciales sin precisión suficiente

Documento 07 dice que Meta cobra por mensajes de servicio desde octubre sin expresar franquicia. La FAQ oficial consultada confirma la franquicia de 1.000 mensajes de servicio por número/mes y cobro desde el 1.001; no equivale a «todos cobran desde el primero». Fuente: https://whatsappbusiness.com/resources/faq/ (consulta 24-10-2026). La página comercial general devolvió información no coincidente sobre ventana gratuita: no usar un texto comercial antiguo para fijar el motor de costos.

El tarifario requiere categoría, mercado, vigencia, franquicias/excepciones y distinción costo real/estimado/BSP. No se validaron todas las tarifas ni se promete ninguna cifra. «Supera a todas» y «ninguna entrega código» son afirmaciones universales no demostradas; convertirlas en objetivo o comparación con muestra y fuentes específicas.

## Cumplimiento funcional observado

| Alcance | Estado auditado |
|---|---|
| Repositorio src, paquete Python, Flask/Jinja, migraciones PostgreSQL | Existe; instalación independiente, permisos de BD y recuperación no acreditados |
| F01 acceso multiusuario | Parcial: hashes/sesiones/CSRF; faltan permisos completos/MFA/recuperación y hay R01/R04/R05/R06 |
| F02 panel | Existe; no certificado como cuadro financiero completo |
| F03 clientes | Parcial: contactos/nota; faltan consentimientos, fusión, identidades y oportunidades completas |
| F04/F05 embudo y análisis de leads | Sin módulo/calificación R1 ni evidencia de cumplimiento |
| F06 agenda | Existe; R03 bloquea aceptación de reglas horarias; conectores de calendario no implementados aquí |
| F07 conversaciones y toma humana | Ausentes; no se observa bandeja/outbox de mensajería |
| F08 editor de plantillas Meta | Ausente |
| F09/F10 campañas/automatizaciones | Ausentes |
| F11 ventas/stock | Parcial; no pagos por movimientos/abonos/cotizaciones/devoluciones parciales; R02/R08/R10 |
| F12 conocimiento | Tabla y búsqueda básicas; no gestión segura de versiones/publicación/archivos |
| F13 análisis de datos | Estrella inicial de citas y líneas; no modelo completo/incremental/SCD2; R02/R08 |
| F14 mercado | Documentación; sin módulo de observaciones/competidores implementado |
| F15 asistente | Herramientas deterministas y búsqueda por palabras; no LLM/RAG completo, permisos insuficientes |
| F16 operación/respaldos/VPS | CLI local; sin prueba de instalación VPS/restauración |
| F17 multisucursal | No implementado |
| F18–F21 canales/mercado automático/predicción/integraciones | No implementados; pueden ser ampliaciones por contrato |
| F22 failover IA | Ausente |
| F23 telemetría tokens/costos | Ausente |
| F24 evals de prompts | Sin prompts/runtime ni evaluación versionada |
| F25 seguridad continua | Hay test_security.py, cobertura parcial; no demuestra toda la suite exigida |
| F26 semáforo por número | Ausente |
| F27 fábrica por cliente | Documentación; sin kit ejecutable comprobado |

La falta de módulos futuros no requiere construirlos en una sola corrección. Primero cerrar defectos del código existente; luego planificar entregas con aceptación.

## Puerta de aceptación

No iniciar otra fase sobre la premisa de que PR00B está aceptada. GLM debe entregar CORR01 siguiendo PROMPT_CORRECCIONES_GLM.md, sin sobreescribir esta revisión. Revisión posterior debe ejecutar suite PostgreSQL en base de pruebas separada y probar números absolutos, permisos cruzados y fronteras temporales. Probar todos los módulos que se pretenda aceptar y documentar pendientes reales.
