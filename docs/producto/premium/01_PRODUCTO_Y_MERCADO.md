# Producto Premium e investigación

Fecha de consulta: 23-10-2026. Las capacidades del producto propuestas aquí son decisiones de diseño; las fuentes sirven de referencia, no garantizan ventas ni equivalencia con plataformas empresariales completas.

## Referencias verificadas

| Fuente oficial | Hallazgo relevante | Aplicación propuesta |
|---|---|---|
| [Salesforce Sales](https://www.salesforce.com/sales/pricing/) | Venta por ediciones y licencias; configuración y automatización comercial | Definir límites, permisos e integraciones en cada oferta |
| [Salesforce Revenue Intelligence](https://www.salesforce.com/sales/revenue-intelligence/pricing/) | Precio publicado USD 220 por usuario/mes con cobro anual para Revenue Intelligence; USD 250 con Tableau. Incluye análisis de oportunidades y previsión | Referencia del costo de analítica avanzada; no es precio de un CRM local completo |
| [HubSpot Sales](https://www.hubspot.com/pricing/sales?tier=enterprise) | Plataforma de ventas con niveles y consumo adicional mediante créditos en determinadas herramientas | Separar licencia/implantación, consumo y servicios; evitar «IA ilimitada» |
| [Zoho Zia](https://www.zoho.com/crm/sales-assistant.html) | Consulta conversacional, predicción comercial, anomalías y recomendaciones | Prioridad explicable, asistente con datos y seguimiento de calidad |
| [Semrush](https://www.semrush.com/stats/) | Inteligencia competitiva basada, entre otras fuentes, en estimaciones de tráfico | Etiquetar estimaciones externas; nunca confundirlas con ventas reales del competidor |
| [WhatsApp Business](https://whatsappbusiness.com/blog/manage-message-templates-whatsapp-business-api/) | Gestión de plantillas y necesidad de aprobación | Separar borrador local y estado del proveedor; artículo antiguo, no copiar versiones de API |
| [AWS End User Messaging](https://docs.aws.amazon.com/social-messaging/latest/userguide/managing-templates.html) | Su integración documenta creación, edición, revisión y estado de plantillas de WhatsApp | La edición no equivale a autorización inmediata de envío |
| [Microsoft: modelo estrella](https://learn.microsoft.com/power-bi/guidance/star-schema) | Hechos y dimensiones con granularidad definida | Capa analítica separada de transacciones |
| [PostgreSQL: contraseñas](https://www.postgresql.org/docs/current/auth-password.html) y [respaldos](https://www.postgresql.org/docs/current/backup.html) | Autenticación de base y alternativas de respaldo/restauración | Credenciales separadas y restauración probada |

Limitación: el acceso directo a la página de plantillas de Meta devolvió 429 en esta investigación. No se fijan cantidades máximas de edición, plazos garantizados ni una versión de API a partir de fuentes secundarias. GLM deberá comprobar el contrato oficial vigente antes de implementar el conector. AWS documenta su propia integración; no se exige contratar AWS.

Ejemplo comparable de costo, no recomendación de compra: cinco licencias de Revenue Intelligence a USD 220 suman USD 1.100 mensuales y USD 13.200 anuales antes de otros productos y cargos aplicables. Esto no demuestra que un desarrollo local valga lo mismo. El precio depende del resultado, alcance, mantenimiento y costos sostenibles.

## Posicionamiento y precio propuesto

Un solo producto superior: **CRM Premium multirrubro de atención, ventas e inteligencia comercial**. Debe responder quién necesita atención, qué oportunidades se pierden, qué campañas producen cobros y qué acciones están respaldadas por evidencia. Modelo confirmado: instalación freelancer en VPS del cliente, entrega del código y mantenimiento opcional. Sin suscripción propia, bloqueo por falta de mantenimiento ni servidor central de licencias.

Bandas orientativas de implantación, NO precios de mercado verificados ni presupuesto de desarrollo desde cero:

| Banda | Oferta posible cuando el producto esté terminado | Límites de referencia a confirmar |
|---|---|---|
| USD 1.500–3.000 | Instalación estándar del núcleo Premium, capacitación y carga sencilla; analítica interna, leads, plantillas y mercado con fuentes cargadas manualmente | 1 sucursal, 5 cuentas, 3 agendas; sin conectores a medida |
| USD 3.000–6.000 | Mayor migración, configuración de equipos, campañas, reportes y una integración de alcance acordado | Hasta 3 sucursales, 15 cuentas, 10 agendas; validar red y rendimiento |
| USD 6.000–10.000 | Proyecto de implantación avanzado, conectores de mercado contratados, permisos y cuadros por sucursal, restauración ensayada y formación ampliada | Hasta 5 sucursales, 30 cuentas, 20 agendas como objetivo sujeto a prueba |

No son tres calidades de seguridad: contraseñas, respaldos, auditoría y permisos son obligatorios en todas. Son tamaños de trabajo y capacidad a verificar, no límites artificiales de licencia. Mantenimiento, consumo IA/Meta, fuentes de mercado, dominio, VPS y soporte se cotizan aparte; preferentemente el cliente paga directamente a sus proveedores. Definir horario, canal, tiempo de primera respuesta y exclusiones. Entregar repositorio, documentación y acceso administrativo por canal seguro. Detallar titularidad del trabajo y licencias de terceros; no prometer propiedad exclusiva sobre bibliotecas externas.

## Catálogo funcional con prioridad

N = obligatorio para declarar Premium completo; A = ampliación contratada. «Obligatorio» no significa implementado.

| ID | Módulo | Contenido y resultado | Prioridad |
|---|---|---|---|
| F01 | Acceso y equipo | Usuarios propios, roles, permisos por sucursal y acción, sesiones revocables, historial y recuperación local | N |
| F02 | Inicio ejecutivo | Ventas netas, cobros, cartera, leads pendientes, ocupación, alertas y fecha de actualización; filtros compartidos | N |
| F03 | Clientes 360 | Identidades por canal, consentimiento, oportunidades múltiples, actividades y búsqueda; fusión auditada de duplicados | N |
| F04 | Embudo | Kanban y tabla equivalentes, responsables, etapas, antigüedad, motivos de pérdida, tareas y SLA | N |
| F05 | Análisis de leads | Puntaje explicable por reglas, datos faltantes, fuente, fecha y siguiente acción propuesta | N |
| F06 | Agenda | Servicios, duración, recursos/profesionales, horarios, bloqueos, lista de espera, estados e historial; Google confiable | N |
| F07 | Conversaciones | Bandeja WhatsApp, asignación, etiquetas, notas privadas, adjuntos, estados de entrega, pausa persistente de IA y SLA | N |
| F08 | Plantillas | Ventana para crear, editar, comparar versiones, aprobar internamente, enviar a revisión y sincronizar estado Meta | N |
| F09 | Campañas | Segmentos, consentimiento, exclusión, vista previa, presupuesto, programación, pausa y resultados; pruebas A/B con asignación estable | N |
| F10 | Automatizaciones | Evento/condición/acción, simulación, límites, versiones, reintentos, deduplicación y registro de ejecución | N |
| F11 | Ventas y cobros | Cotizaciones versionadas, aceptación, venta, abonos, saldo, devoluciones auditadas y productos/stock por movimientos | N |
| F12 | Conocimiento | Documentos privados, permisos de enviar/RAG/interno, borrador/publicación/reversión, vigencia y fuentes | N |
| F13 | Análisis de datos | Embudo por cohortes, origen/campaña, asistencia, respuesta, productividad, recurrencia, cobros y calidad del dato | N |
| F14 | Análisis de mercado | Competidores, precios comparables, tendencias, fuentes, fecha, geografía, evidencia y oportunidades; carga manual utilizable | N |
| F15 | Asistente interno | Preguntas sobre indicadores y fuentes con permisos heredados, límites de consulta y desglose verificable | N |
| F16 | Operación local | Instalador, actualización, PostgreSQL, salud de colas, respaldo, restauración, importación/exportación y consumos | N |
| F17 | Multisucursal | Permisos por sede, recursos, objetivos, transferencias y consolidación sin duplicar clientes | A |
| F18 | Canales adicionales | Adaptadores preparados para Telegram, Facebook Messenger, Instagram, correo y formularios web; activación con cuentas y pruebas por adaptador | A |
| F19 | Mercado automático | APIs licenciadas, frecuencia, cuota, trazabilidad y renovación de fuentes | A |
| F20 | Predicción estadística | Probabilidad calibrada y previsión validadas frente a una referencia; monitor de deriva | A |
| F21 | Integraciones empresariales | CRM/ERP externos, pasarela, sistema contable/fiscal, telefonía, SSO o BI externo; alcance específico | A |

No incluir por defecto: historia clínica/odontograma, diagnóstico o prescripción, contabilidad integral, facturación fiscal, scraping universal, aplicación móvil nativa, autonomía de gasto de IA, SaaS multiempresa o atención sin Internet mediante WhatsApp. Son productos/proyectos distintos.

## Lógica del análisis de mercado

Entradas: zona geográfica, servicios comparables, competidores definidos, período y fuentes. Cada observación conserva URL o archivo, fecha de captura, fecha del dato si existe, moneda, unidad, condiciones, método y responsable. No copiar datos personales para enriquecer leads sin una base autorizada.

Procesamiento: normalizar servicios equivalentes y rangos; marcar promociones y precios «desde»; separar dato observado de estimación del proveedor y de hipótesis de IA. No mezclar paquetes diferentes ni inventar precios ausentes. Mostrar cobertura, sesgo de selección, número de observaciones y antigüedad.

Salida: tabla de competidores, rango/mediana de precios de la muestra comparable, tendencias con origen, fortalezas/debilidades sustentadas y oportunidades en fichas: evidencia → hipótesis → acción de prueba → costo → indicador → fecha de evaluación. No inferir cuota de mercado, facturación ajena o causalidad a partir del CRM.

Sin fuente externa: mostrar «análisis de cartera interna» y formulario de carga de fuentes; nunca un estudio de mercado ficticio. Fuente caducada: marcar y excluir de comparaciones actuales por defecto. Caducidad inicial configurable de 30 días para precios; no presupone que todos cambien cada mes.
