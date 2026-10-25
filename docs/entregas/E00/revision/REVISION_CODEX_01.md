# Dictamen independiente E00 — revisión 01
Fecha: 24-10-2026. **DEVUELTA PARA AJUSTE DOCUMENTAL E00B.**

## Reconocido
Matriz identifica paridad aún abierta, F17 obligatorio y alcance pendiente sin fingir implementación. Bocetos son destino, no pantallas ejecutadas. Fases/entidades/permisos son un avance válido. No se exige código en esta entrega.

## D1 — dependencia circular o invertida
E04 requiere lead_scores/señales y T46–T48, pero opportunities sólo se crea en E05. E03 menciona contactos/interés sin definir un modelo mínimo de oportunidad que E04 pueda puntuar. Mover contrato mínimo de oportunidad/interés/etapa/responsable/consentimiento a E01 o E03 y declarar dependencia E04; E05 amplía circuito comercial. Esta inconsistencia procede también de los prompts anteriores de Codex; se corrige el plan, sin atribuirla exclusivamente a GLM.

E06 sólo declara elección del proveedor/E00, pero sincroniza stock/pedidos/pagos de E02/E05. Separar contrato/adaptador simulado temprano y activación después de entidades locales. E07 atribuye cobros a campañas sin dependencia verificable de campañas/eventos; no habilitar métrica hasta contar con sus datos.

## D2 — requisitos sin fase cerrada
F09/F10 «post-E03» y F22–F27 «dependencias naturales» no definen entrega ni puerta de aceptación. Asignar cada requisito a fase/subentrega, dependencias, pruebas y condición de habilitación. No basta nombrarlos. Declarar cuáles ampliaciones requieren contrato y cuáles son obligatorias según 07/08.

## D3 — trazabilidad individual pendiente
Se citan T01–T38/T39–T58 en conjuntos; falta mapa individual requisito→caso→fase→evidencia prevista, con no aplicable motivado. Separar diseñado/implementado/simulado/externo y no afirmar criterio probado por sumar 96 pruebas. «CI local» requiere configuración/evidencia o redactar como suite local.

## D4 — contrato E01 insuficiente para que GLM implemente sin adivinar
Concretar acciones por rol y ámbito, migración de datos globales actuales a sede inicial sin pérdidas ni apertura de acceso, contactos compartidos frente a oportunidades asignadas, backfill de recursos/ventas/stock/BI y permisos del asistente. Declarar cómo preservar historial/precio/costo y tratamiento de entidades aún no implementadas. Definir MFA/recuperación: cuándo se entrega y requisito antes de publicar VPS. Añadir criterios negativos que validen denegación por defecto.

## Siguiente paso
Sólo actualizar documentación en E00B conforme a 11_PROMPT_CORR01C_E00B.md. Revisión de E00B y cierre CORR01C antes de E01. No implementar el resto del producto en este ajuste. Los flujos básicos siguen abiertos hasta E03 y eso no se confunde con fallo de esta entrega documental.
