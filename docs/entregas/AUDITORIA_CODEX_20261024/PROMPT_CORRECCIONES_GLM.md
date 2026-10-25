# Prompt GLM — CORR01 de Agente de reserva V4

Eres GLM, implementador. Codex ha auditado el árbol actual y devuelve el alcance revisado por defectos de integridad, privacidad y trazabilidad. Lee AGENTS.md, docs/producto/PLAN.md, ESTADO.md, MAPA.md, expediente Premium 00–07 y docs/entregas/AUDITORIA_CODEX_20261024/REVISION_CODEX.md con su EVIDENCIA.md.

Trabaja en H:\git\Agente de reserva V4. Conserva cambios previos. La decisión del propietario de empezar con núcleo funcional y PostgreSQL prevalece sobre el PR00 extenso antiguo. Codex especifica/revisa; tú corriges código y ejecutas pruebas. Esta entrega es CORR01: corregir lo existente, no construir todos los módulos pendientes.

## Antes de modificar

Inventaría el árbol y relación de commerce, analytics y assistant con la entrega PR00B. Registra autorizaciones disponibles sin inventarlas. Identifica código probado, esquema y entorno. Crea docs/entregas/CORR01/ENTREGA.md y pruebas/PLAN.md. No uses .env ni servidor operativo como fallback de pruebas. Usa credenciales de pruebas suministradas por vía segura, base temporal PostgreSQL y proveedores simulados; si no hay servidor aislado, deja esa prueba pendiente con razón sin declarar éxito.

## Correcciones requeridas por orden

1. R01: redacta credencial operativa expuesta en documentación, conservando aviso del incidente sin el valor. Da procedimiento seguro para que el propietario rote y revoque sesiones. No inventes ni imprimas otra contraseña, no pruebes la publicada y no declares rotación hasta tener evidencia autorizada. No suprimas historial de fallos de pruebas.
2. R02: corrige el modelo de venta/reversión para conservar operación positiva y compensación fechada. Migración nueva, transaccional y documentada: nunca editar migraciones ya aplicadas ni inferir cobros/reembolsos históricos. BI y asistente deben cuadrar con 100 → anulación → neto acumulado 0; devolución posterior aparece en su fecha sin reescribir venta histórica. Conserva stock compensatorio e idempotencia.
3. R03: valida intervalo completo del horario por fechas e instantes, no sólo extremos/minutos. Rechaza 26-oct-2026 10:00 → 27-oct 11:00 con 09–17 UTC y 16:00 → 17:00:30; permite terminar exactamente 17:00. Incluye fines de semana, varios días, DST/hora ambigua y citas 24/49 horas bajo perfil 24×7.
4. R04/R05: historial de asistente por propietario del registro/ámbito autorizado y permiso explícito para vista global. Restringe ajustes globales a administrador. Herramientas y rutas aplican permisos del usuario; no basta pasar su ID al log. Añade dos usuarios con contenidos distintos y prueba ausencia de datos ajenos en HTML/API/asistente. Matriz honesta de permisos aún pendientes para Premium.
5. R06/R07: revoca sesiones atómicamente al cambiar rol y repara par CSRF cookie/formulario después de login fallido o token caducado. Incorrecta → correcta debe funcionar sin recargar manualmente; token ajeno debe fallar.
6. R08: excluye demos por defecto en BI, vistas y asistente, con opción permitida visible; conserva costo desconocido y costo histórico donde exista. No recalcular costos pasados con precio/costo actual. Separa top de productos/servicios y ventas de cobros. Para funciones financieras no disponibles responde no disponible y documenta el límite; no inventes abonos/pagos.
7. R09: actualiza entrega/inventario/estado e índice sin borrar resultados históricos. Pruebas con URL separada obligatoria, composición de DSN robusta y limpieza en finally; opt-in explícito para cualquier servidor compartido. Ningún acceso al servidor del propietario por el simple import del conftest.
8. R10: prueba instalación distribuida en entorno limpio fuera del checkout, incluyendo plantillas/estáticos y migraciones. Corrige empaquetado si falla. Ordena adquisición de locks de productos y prueba concurrencia A,B/B,A además de última unidad. Reporta resultados y límites reales.
9. R11: corrige las afirmaciones del documento 07 usando documentación oficial fechada; expresa franquicias/excepciones y separa estimación de costo real. No añadas un motor tarifario universal fijo. No anuncies superioridad absoluta sin comparación demostrada.

## Pruebas de regresión obligatorias

Cada R tiene reproducción previa que falla y prueba posterior que pasa; resultados reales en PostgreSQL temporal para integridad/concurrencia/ETL. Incluye:
- Reversión absoluta neto 0, períodos distintos y mezcla de ventas; no sólo diferencia entre snapshots.
- Dos usuarios, permisos negativos de ajuste/historial/herramientas y revocación al cambiar rol.
- Fronteras horarias al segundo, DST y jornadas completas.
- Reintento de login sin recarga y token CSRF inválido.
- Demo excluido, costo NULL, costos históricos, consulta de cobros sin convertirla en ventas.
- Fallo de migración/ETL sin publicación parcial y recuperación de última versión válida.
- Paquete instalado sin checkout y concurrencia comercial en orden inverso.

Ejecuta regresión del conjunto afectado; no cuentes 47 históricas ni 70 funciones AST como pruebas pasadas nuevas. No elimines aserciones o cambies datos sólo para obtener verde. Si el esquema financiero exige dos subentregas, documenta dependencias y presenta la primera sin autoaceptar el resto.

## Evidencia y cierre

Guarda docs/entregas/CORR01/ENTREGA.md, matriz R01–R11, diseno/, cambios/, pendientes/ y pruebas/ejecuciones/<UTC-ID>/ con entorno, código probado/huella, comandos depurados, códigos de salida, conteos, duración, logs y capturas pertinentes. Conserva ejecución fallida y añade la corregida. Actualiza INDICE.md y ESTADO.md.

No edites REVISION_CODEX.md ni escribas dictamen por Codex. No despliegues, cambies credenciales operativas, migres base real, envíes mensajes ni hagas push por inferencia. Indica cada R como resuelto con evidencia o pendiente con causa. Detente y presenta CORR01 para revisión independiente antes de avanzar a conversaciones o nuevas funciones.
