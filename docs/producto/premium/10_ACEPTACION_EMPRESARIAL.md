# Aceptación empresarial T39–T58

## Extensión posterior T59–T70

Ver 13_RECORRIDOS_AGENDA_VENTAS_CATALOGO.md: celda/vistas de agenda, nombres y retiro/pago en ventas, tratamientos, catálogo/stock/ETA desde UI y RAG con datos vivos. Casos por ejecutar en E01-UI/E02/E03/E05, no pruebas ya pasadas.
24-10-2026. Complementa T01–T38; casos por implementar/ejecutar, no resultados actuales.

| ID | Recorrido | Resultado exigido |
|---|---|---|
| T39 | Tres sedes/quince cuentas/roles | Director consolidado, gerente sede y asesor asignados; sin fuga en URL/API/BI/exportación |
| T40 | Configuración desde frontend | Alta sede/recurso/horario/campo/pipeline con tipos y auditoría; sin terminal para operación |
| T41 | Catálogo 500 artículos/variantes | Crear/importar/editar/publicar/archivar; galería y foto de variante correctas en PC/móvil |
| T42 | Ficha de servicio/tratamiento | Duración/condiciones/precio desde/sedes aprobados; IA no inventa diagnóstico ni total |
| T43 | Físico/reservado/disponible | Dos compradores última unidad: un ganador; expiración libera sin duplicar |
| T44 | Recepción/traslado/conteo | Origen-tránsito-destino consistente ante reintento; ajuste con motivo y permiso |
| T45 | Agente consulta catálogo vigente | Foto/ficha autorizadas y precio/stock por sede; dato vencido no confirma disponibilidad |
| T46 | Editar regla en frontend | Simulación explica impactos sin escribir/enviar; siguiente lead usa versión publicada |
| T47 | Ausencia/conflicto/reversión de reglas | NULL distinguido, ciclo frenado y orden definido; reversión no borra acciones anteriores |
| T48 | Asignación/SLA | Sólo asesores elegibles por sede/horario/carga; consentimiento no se vence con puntaje |
| T49 | Cotizar→aceptar→reservar→vender→abonar→devolver | Snapshot/moneda/pagos/neto/saldo/stock y permisos correctos |
| T50 | ERP autoridad stock/precio | Mapeo/frescura visibles; sin doble maestro o promesa cuando desconectado |
| T51 | Respuesta externa perdida | Un pedido por clave, reconciliación y revisión; reintento no duplica |
| T52 | Cuadros/metas/desglose | Fórmula/filtro/moneda/lote visibles; registros y exportación cuadran |
| T53 | Cohortes y eficacia de reglas | Etapas/pérdidas/resultado por versión; no causalidad inventada |
| T54 | Inventario/campaña hasta cobro | Rotación/cobertura/quiebre con fuente; atribución explícita y cobro separado |
| T55 | Paridad básica V3→V4 | Información/reservas/humano/pausa/canal/calendario/notas privados con estado real por flujo |
| T56 | Mercado/fuente vencida/muestra pequeña | Evidencia/fecha/comparabilidad/cobertura; no estudio ficticio |
| T57 | Medios/conocimiento por permisos | Publicado/interno/enviable/RAG separados; URL temporal no expone privado |
| T58 | Demo empresarial y recuperación | Tres sedes/quince cuentas/dos rubros; UI→operación→ERP→BI y restauración limpia |

Objetivo inicial de carga: diez simultáneos sobre fixture de 08. Medir recursos, P95 y errores contra VPS identificada; no prometer capacidad sin ensayo. Cada aceptación enlaza Fxx, código/huella, fixture, ejecución y captura pertinente. Una prueba API no demuestra que el administrador pueda hacerlo desde frontend.
