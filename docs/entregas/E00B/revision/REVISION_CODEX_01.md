# Dictamen E00B — revisión independiente 01
Fecha: 24-10-2026. Codex. **ACEPTADA COMO BASE DOCUMENTAL PARA E01.**

## Fundamento
D1: E03-O define oportunidad/etapas/interés/consentimiento antes de E04; E05 amplía venta/cobro. E06-A/B separa simulación y activación con sus dependencias. Atribución sin campañas queda no disponible hasta E09.
D2: F01–F34 tiene fase/condición; E09 y E10-IA hacen explícitos requisitos antes difusos.
D3: T01–T58 tiene fase prevista, con límites/estados; ya no se afirma CI inexistente.
D4: E01 incluye sede Principal, preservación de IDs/historial/precios/costos, matriz por acción/rol/ámbito, denegación por defecto, separación de cliente y datos privados, revocación, recuperación y MFA antes de VPS.

Esta aceptación es documental, no implementación ni validación de pruebas empresariales. No demuestra paridad básica ni autoriza producción.

## Precisiones vinculantes al implementar
1. Corrección de alcance comercial: F09/F10 estaban marcadas núcleo N en el catálogo original y E00B las convierte a A. Su entrega puede ir en E09, pero no se elimina silenciosamente la obligación del producto completo. Una reducción comercial requeriría decisión explícita del propietario. Mismo criterio para F34: configurar/probar la integración acordada sigue siendo requisito de la oferta empresarial; proveedor concreto, costos y conectores adicionales dependen del contrato, no de compatibilidad universal.
2. No fijar 0006_opportunities.sql antes de E01: numerar la migración al implementarla según versiones reales pendientes, sin colisión ni editar migraciones aplicadas.
3. T02 condicionado a migración V3 no elimina pruebas de backfill PostgreSQL→sede Principal. Esas pruebas sí son obligatorias en E01-M.
4. La fila «Stock ajustar Director —» puede ser una separación de funciones deliberada: documentar quién recibe permiso y el procedimiento de administración, sin crear excepciones ocultas de superusuario. Permiso independiente no debe contradecir denegación por defecto.
5. Datos actuales sin responsable no se abren a todos los asesores: cola restringida al supervisor hasta asignación. Restricciones por sede deben cubrir también herramientas BI/IA ya existentes, no sólo tablas nuevas.

## Avance
E00B no requiere otra ronda documental para empezar su alcance E01. La condición técnica CORR01C no está aceptada por dos fallos acotados C1/C2, descritos en su dictamen. Una vez aceptado CORR01D podrá iniciar E01, con este contrato y precisiones. No bloquear planificación por la rotación operativa pendiente, pero no publicar VPS hasta cerrar credenciales y seguridad.
