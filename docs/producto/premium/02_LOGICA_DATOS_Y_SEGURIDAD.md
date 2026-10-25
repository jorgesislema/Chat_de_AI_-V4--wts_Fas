# Lógica, PostgreSQL y seguridad

Diseño, no código. 23-10-2026. Una organización por instalación en VPS del cliente; varios usuarios desde navegador HTTPS. PostgreSQL privado en esa VPS.

## Arquitectura

Conservar Python y Flask/Jinja y separar servicios de contactos, oportunidades, reservas, mensajes, ventas, plantillas y permisos. Bot, web e integraciones utilizan las mismas reglas. No introducir microservicios sin necesidad medida.

Componentes: servidor web de producción detrás de proxy HTTPS, trabajador de colas/ETL, PostgreSQL y archivos privados. Nunca publicar el servidor de desarrollo ni el puerto PostgreSQL a los usuarios. Secretos fuera del repositorio y diagnósticos redactados. Sin dependencia de una plataforma central del freelancer.

Una base por instalación, con esquemas conceptuales operación, integración, auditoría y BI. Operación normalizada; BI dimensional. Esquemas solos no aíslan: roles de base separados para migración, aplicación, trabajador, informes y respaldo. La aplicación no es superusuario. Consultas BI también aplican permisos por usuario/sede; una cuenta de lectura sin filtros podría exponer datos igualmente.

Cambio y evento outbox se guardan en una transacción. Llamadas externas fuera de transacciones de escritura. Trabajador con arrendamiento, idempotencia, reintentos acotados, retirada y cola de revisión. Si un proveedor recibió un envío pero se perdió su respuesta, reconciliar o marcar resultado desconocido; no reenviar ciegamente ni prometer exactamente una entrega sin soporte del proveedor.

## Modelo multirrubro

Contacto = persona/organización; oportunidad = intención comercial; puede haber varias por contacto. Identidad de canal = proveedor, cuenta e identificador externo. No fusionar por nombre; coincidencia de teléfono/correo propone revisión. Fusión con historial, IDs anteriores y consentimiento preservado; reversión o reparación controlada según operaciones posteriores.

Perfiles versionados definen vocabulario, módulos, campos tipados, etapas y permisos. No ejecutan código arbitrario. Cambiar etiqueta no cambia ID histórico; desactivar módulo no borra datos.

| Perfil | Interés | Flujo | Datos específicos |
|---|---|---|---|
| Clínica | Servicio/cita | Consulta, valoración, presupuesto, aceptación | Profesional y agenda; sin diagnóstico ni historia clínica |
| Tienda | Producto/pedido | Consulta, cotización, pedido, pago, entrega | Variantes, unidad, costo, stock reservado, devoluciones |
| Colegio | Admisión | Consulta, visita, solicitud, matrícula | Representante y alumno separados; datos de menores restringidos; matrícula no equivale a cobro |
| Inmobiliaria | Inmueble/visita | Consulta, calificación, visita, oferta, cierre | Disponibilidad, múltiples interesados; comisión distinta del precio del inmueble |

Relación oportunidad/recurso de interés explícita. Campos específicos validados, no sólo notas libres. Colegio no implica sistema académico completo; inmobiliaria no implica contabilidad fiduciaria.

## Reglas transversales

- Oportunidad: nueva → contactada → calificada → propuesta/visita → ganada/perdida. Etapas adaptables; cierre requiere motivo y referencia comercial cuando existe. Reabrir conserva cierre anterior. Cita no significa venta ni pago.
- Tarea: pendiente → en curso → completada/cancelada; responsable, plazo y recordatorio. SLA hábil y tiempo calendario separados.
- Conversación: IA activa → esperando humano → humana → cerrada/devuelta a IA. Toma humana incrementa versión, revoca trabajos pendientes y persiste al reiniciar. Validar versión justo antes del envío; mostrar si el proveedor ya recibió un mensaje anterior.
- Reserva: preservar P02/G01B y reglas UTC/zona IANA. La base impide solapamientos concurrentes por recurso de capacidad uno. Capacidad múltiple requiere unidades reservadas transaccionalmente. Google es sistema externo, no autoridad silenciosa sobre asistencia.
- Cotización: borrador → enviada → aceptada/rechazada/vencida. Guardar versión aceptada, moneda, impuestos, descuentos y líneas.
- Venta/pago: entidades distintas; abonos, devolución y anulación por movimientos compensatorios auditados. Stock y venta se confirman atómicamente. Dos compras no consumen la última unidad dos veces. Dinero decimal, moneda explícita.
- Automatización: borrador → simulada → publicada → pausada/archivada. Evento, condición y acción permitida; límites de profundidad, frecuencia, gasto y reintentos. Ninguna secuencia vuelve a contactar a alguien que pidió baja.

## Puntaje inicial de leads

Regla R1, determinista y configurable; no es probabilidad de compra:

| Señal comercial comprobable | Puntos |
|---|---:|
| Interés explícito en producto/servicio disponible | 25 |
| Solicita cotización o reserva | 25 |
| Declara horizonte de compra de hasta 30 días | 20 |
| Respondió en últimos 7 días | 15 |
| Siguiente paso vigente acordado | 15 |

Cada señal se cuenta una vez con evidencia, fecha y versión; máximo 100. Desconocida aporta cero y se muestra como falta de datos. Las señales históricas de interés y solicitud se reducen a mitad tras 30 días sin actividad y a cero tras 60. Respuesta reciente caduca a 7 días; horizonte y siguiente paso sólo aportan mientras sigan vigentes.

70–100 alta, 40–69 media, 0–39 inicial. Tres señales desconocidas o más añaden «datos insuficientes». Son hipótesis iniciales que deben validarse por rubro. Ejemplo: interés 25 + solicitud 25 + respuesta 15 = 65; prioridad media, sin probabilidad inventada.

Permiso para contacto es un bloqueo independiente: puntaje alto no habilita campañas. No usar salud, religión, raza, discapacidad, atributos de menores ni riqueza inferida. IA extrae posibles señales citando mensajes; servicio valida y calcula. Usuario autorizado puede corregir con historial.

Predicción futura exige etiquetas suficientes, validación temporal, control de fuga, calibración y comparación con regla base por segmento. Sin ventaja demostrada, mantener reglas; no fijar una cantidad mágica de registros ni presentar puntaje como porcentaje.

## Estrellas analíticas

Dimensiones compartidas: fecha con papeles creación/cierre/cobro, hora, organización, sucursal, contacto seudonimizado, usuario, profesional/recurso, canal, origen comercial, campaña, servicio/producto, etapa, estado, versión de plantilla, moneda y fuente de mercado. Canal técnico no equivale a origen comercial: WhatsApp puede contener un referido. Históricos desconocidos siguen desconocidos.

| Hecho | Grano exacto | Medidas principales |
|---|---|---|
| Oportunidad-evento | Una transición de etapa | Entrada/salida, tiempo en etapa; conservar revisitas |
| Oportunidad-diaria | Una oportunidad por fecha local de corte | Etapa, valor abierto, antigüedad; saldo no sumable entre días |
| Cita | Una cita, estado actual | Duración UTC, asistencia, fecha de servicio; cambios en historial operativo |
| Capacidad-diaria | Un recurso/sede/día | Minutos disponibles netos de bloqueos |
| Venta-línea | Una línea confirmada o compensatoria | Unidades, neto, costo conocido e impuestos separados |
| Pago | Un cobro o reembolso | Importe firmado, moneda, fecha, operación asociada |
| Mensaje | Un mensaje lógico único | Autor, dirección, tiempos y estado reconciliado; recibos no crean nuevos mensajes |
| Conversación | Un episodio de atención hasta cierre | Respuesta humana, espera, resolución y transferencias |
| Campaña-diaria | Campaña/canal/sede/fecha/moneda | Gasto y resultados; conservar granularidad real disponible |
| Stock-movimiento | Un movimiento por producto/ubicación | Cantidad firmada, costo conocido y causa |
| Mercado-observación | Servicio/competidor/fuente/fecha/observación | Precio, unidad y calidad; no es transacción real |

Todos incluyen ID de origen, lote, fecha de carga, versión de transformación y marca demo. Sucursal, responsable y clasificación de producto usan versiones históricas SCD2 cuando cambian el análisis: clave sustituta, vigencia y una versión actual. Hecho apunta a versión vigente al evento. Corrección tipográfica puede sobrescribirse. PII se resuelve con permisos desde operación; no duplicar teléfonos ni documentos sensibles en BI.

ETL incremental por fecha de modificación y clave estable, ventana de solapamiento y upsert; manejar eventos tardíos, bajas y anonimización. Publicación de lote atómica tras controles; conservar último lote bueno ante fallo. Refresco objetivo 15 minutos con antigüedad visible. No escribir operación desde BI.

Agregar hechos por separado antes de combinarlos: unir pagos directamente a líneas multiplica importes. Atribución inicial: último contacto comercial elegible registrado en 30 días previos al cierre, o «sin atribución». Es convención, no causalidad. Si se incorpora reparto, pesos por venta deben sumar uno.

## Indicadores verificables

| Indicador | Definición |
|---|---|
| Conversión de cohorte | Oportunidades creadas en período y ganadas hasta corte / creadas en ese período; mostrar madurez de cohorte |
| Tasa de cierre | Ganadas / (ganadas + perdidas), cierres del período |
| Ventas netas | Líneas confirmadas menos devoluciones/descuentos, excluidos impuestos |
| Cobros netos | Cobros menos reembolsos por fecha del movimiento |
| Cartera | Total exigible menos pagos aplicados y notas de crédito a fecha; impuestos explícitos |
| Ticket medio | Neto / ventas válidas del período; definir tratamiento de anuladas/devoluciones |
| No asistencia | No asistió / (atendida + no asistió); canceladas y pendientes aparte |
| Ocupación | Unión de minutos reservados válidos dentro de disponibilidad / minutos disponibles por recurso |
| Primera respuesta | Mediana y P90 hasta primera respuesta humana; bot separado; sin respuesta no es cero |
| Costo por lead | Gasto atribuible / leads nuevos atribuidos en ámbito comparable |
| ROAS | Ventas netas atribuidas / gasto; no beneficio ni prueba causal |
| Margen | Neto menos costo conocido; informar cobertura si faltan costos |
| Recurrencia | Clientes con segunda compra / elegibles de cohorte y ventana declaradas |

Denominador cero: «sin datos». Períodos parciales señalados. Monedas separadas salvo conversión con fuente/fecha/tipo. Datos demo excluidos. Previsión ponderada etiquetada estimación; ningún gráfico la llama cobro.

## Acceso, seguridad y recuperación

Contraseñas individuales de administrador y usuarios; alta inicial sin contraseña predeterminada ni cuenta oculta. Hash adaptativo con sal mediante biblioteca mantenida. Mínimo inicial 12 caracteres, admitir gestores y frases; limitación de intentos. MFA administrador para producción VPS. Recuperación con códigos de un solo uso o procedimiento autenticado del propietario y auditoría.

Sesiones con cookies Secure/HttpOnly/SameSite, caducidad y revocación por cambio de contraseña/rol/desactivación. CSRF y autorización en cada ruta, exportación y archivo. Credencial de PostgreSQL separada, SCRAM-SHA-256, fuera del repositorio. TLS, copias cifradas, adjuntos privados. Cifrado de disco y respaldo se configuran expresamente, no vienen garantizados por instalar PostgreSQL.

Roles: propietario/admin, supervisor, asesor, recepción, analista y finanzas. Asesor ve asignados; supervisor equipo/sede; analista agregados autorizados; finanzas cobros; admin configura usuarios/conectores. Exportar, ver PII, aprobar campañas, reembolsar y publicar son permisos independientes. Usuario con varias sedes tiene asignaciones explícitas. Bot/IA heredan el mínimo permiso.

Auditoría: actor, instante UTC, acción, recurso, motivo, correlación y cambios redactados. No tokens/contraseñas ni conversación completa innecesaria. No prometer inmutabilidad frente al dueño root de la VPS. Retención/borrado se propagan a BI e índices; documentar caducidad de copias.

Objetivos propuestos, no SLA demostrado: RPO 24 h y RTO 4 h con copia diaria cifrada fuera de VPS, restauración ensayada y retención 7 diarias/4 semanales. Si se necesita menos pérdida, presupuestar y probar WAL/PITR. Copia en el mismo disco no protege pérdida de VPS.

## Migración

Inventario sin secretos → copia verificada → ensayo temporal → cuadre de tablas/IDs/hash/UTC/dinero/outbox/historial → corte con escrituras detenidas → migración final → comprobación → cambio único de origen. No dual-write SQLite/PostgreSQL.

Antes de reabrir escrituras, fallo permite volver al origen intacto. Después de nuevas escrituras, volver a SQLite perdería datos: detener, respaldar y reconciliar con procedimiento explícito. GLM no migra producción sin orden específica. SQLite queda como origen histórico y entorno de edición básica, no autoridad simultánea de Premium.

## Contrato de conectores

Capacidades declaradas por adaptador: recibir/enviar, adjuntos, plantillas, ventanas, estados, firma, cuotas y sincronización. Evento común con proveedor/cuenta/ID externo, UTC, dirección, tipo, contenido privado, correlación y versión. Validar autenticidad según proveedor, deduplicar y rechazar repetición indebida.

Estados: no configurado, configurado, prueba superada, activo, degradado, revocado. Existencia de formulario no significa conexión activa. WhatsApp, Telegram, Messenger, Instagram y correo tienen reglas propias; GLM verifica documentación oficial de cada uno en su fase.

Correo: hilos, remitente, rebotes y bajas. CRM/ERP: propiedad de campos, dirección, mapeo de IDs/estados, política de conflictos y reconciliación; comenzar con importación/exportación si ése es el alcance. No anunciar bidireccionalidad hasta probarla. Credenciales y cuentas pertenecen al cliente.
