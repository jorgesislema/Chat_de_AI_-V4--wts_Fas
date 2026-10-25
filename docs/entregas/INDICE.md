# Índice de entregas Premium

Estado inicial: estructura documental preparada. La evidencia histórica de
P01/P02/P03/G01 permanece en la carpeta docs/producto de la fuente V3 y no
representa una ejecución nueva de Premium.

| Entrega | Alcance | Estado GLM | Documento | Última ejecución | Dictamen Codex |
|---|---|---|---|---|---|
| PR00B | Núcleo funcional local: identidad, organización, contactos, agenda sobre PostgreSQL + frontend profesional | Lista para revisión (47/47 pytest, servidor y navegador verificados) | [ENTREGA.md](PR00B/ENTREGA.md) | 24-10-2026 | Devuelta para correcciones (auditoría 24-10) |
| CORR01 | Correcciones R01–R11 de la auditoría + absorbe comercio/analítica/asistente con pruebas (90/90) y empaquetado verificado | Lista para revisión independiente | [ENTREGA.md](CORR01/ENTREGA.md) | 24-10-2026 | Pendiente |
| CORR01B | Cierre técnico: DSN con parámetros, rupturas migración/ETL con rollback, rotación interactiva, evidencia reproducible (96/96 verbose + wheel) | Lista para revisión | [ENTREGA.md](CORR01B/ENTREGA.md) | 24-10-2026 | Pendiente |
| E00 | Paridad V3→V4 + matriz F01–F34 + contratos E01–E08 + bocetos (sólo documentación) | Preparada (documental) | [ENTREGA.md](E00/ENTREGA.md) | 24-10-2026 | Pendiente |
| CORR01C | Cierre B1–B4: lista blanca DSN + guardas de base efectiva, ruptura con escritura válida + huella bi completa, redacción de evidencia, manifiesto + wheel externo real (104/104) | Lista para revisión | [ENTREGA.md](CORR01C/ENTREGA.md) | 24-10-2026 | Pendiente |
| E00B | Ajuste documental D1–D4: oportunidad mínima (E03-O), E06/E09/E10-IA divididos, mapa individual F01–F34 y T01–T58, contrato E01 ejecutable | **ACEPTADA** como base documental de E01 (con 5 precisiones vinculantes) | [ENTREGA.md](E00B/ENTREGA.md) · dictamen en revision/ | 24-10-2026 | Aceptada (24-10-2026) |
| CORR01D | Cierre C1/C2: huella de las 9 tablas bi corregida + derivación URI única temporal_dsn; repro rojo conservado; 110/110 · wheel externo OK | **ACEPTADA** (cierre C1/C2) | [ENTREGA.md](CORR01D/ENTREGA.md) | 24-10-2026 | Aceptada (24-10-2026) |
| E01 | Sedes, roles de ámbito con denegación por defecto, backfill a sede Principal, BI/IA por sede, buscador de contactos, agenda con franjas horarias y multidiaria | Lista para revisión (120/120 + navegador) | [ENTREGA.md](E01/ENTREGA.md) | 24-10-2026 | Pendiente |

Nota de procedencia: los módulos commerce/analytics/assistant se iniciaron a
petición directa del propietario entre PR00B y la auditoría, sin entrega
registrada en su momento; CORR01 los documenta, corrige y prueba (ver
ENTREGA §Contexto). GLM añade una fila por entrega real y enlaces relativos a sus documentos. Usar «no ejecutado» cuando corresponda; no rellenar con resultados supuestos.

## Revisión independiente vigente — 24-10-2026

PR00B: DEVUELTA PARA CORRECCIONES. Dictamen [revisión 01](PR00B/revision/REVISION_CODEX_01.md). Informe [auditoría](AUDITORIA_CODEX_20261024/REVISION_CODEX.md), [evidencia actual](AUDITORIA_CODEX_20261024/EVIDENCIA.md) y [prompt CORR01](AUDITORIA_CODEX_20261024/PROMPT_CORRECCIONES_GLM.md). La fila anterior describe el envío histórico de GLM; no equivale a aceptación. CORR01 aún no implementada.

## Revisión CORR01 — 24-10-2026

[Dictamen Codex](CORR01/revision/REVISION_CODEX_01.md): parcialmente verificada, cierre pendiente. 10 pruebas de tiempo y reproducciones aisladas repetidas por Codex, no suite PostgreSQL. Las 90 pasadas son evidencia reportada de GLM. Siguiente CORR01B; alcance empresarial 08–10 sólo diseñado.

## Dictámenes vigentes CORR01B/E00 — 24-10-2026

CORR01B: [devuelta para CORR01C](CORR01B/revision/REVISION_CODEX_01.md). E00: [devuelta para E00B](E00/revision/REVISION_CODEX_01.md). E01 aún no habilitada. Prompt de cierre en docs/producto/premium/11_PROMPT_CORR01C_E00B.md. Evidencia anterior se conserva con redacción explícita de credencial en un registro; ninguna rotación ejecutada por Codex.

## Revisión CORR01C/E00B — 24-10-2026

CORR01C: [devuelta sólo por C1/C2](CORR01C/revision/REVISION_CODEX_01.md). E00B: [aceptada como base documental E01](E00B/revision/REVISION_CODEX_01.md). Cinco pruebas puras y diez de tiempo comprobadas por Codex, manifiesto 69 archivos correcto; 104 pasadas PostgreSQL reportadas por GLM. Próxima CORR01D acotada; E01 al aceptar ese cierre.

## CORR01D — dictamen 24-10-2026

[ACEPTADA cierre C1/C2](CORR01D/revision/REVISION_CODEX_01.md). E00B continúa aceptada; E01 habilitada. Cuatro pruebas puras y helper de nueve huellas comprobados por Codex; manifiesto 69 entradas correcto. Las 110 pasadas PostgreSQL son evidencia GLM. Documentos 13/14 y T59–T70 definen recorridos visibles por construir.

## E01 — dictamen independiente 24-10-2026

[DEVUELTA E01-R](E01/revision/REVISION_CODEX_01.md): rutas de cita/BI y permisos de ámbito incompletos, UI inventario/CSP y agenda a corregir. Reproducciones aisladas Codex, no suite PostgreSQL ni guardado real navegador independiente. Prompt15 fija reparación;17 catálogo azul/rojo;16/18 scoring por catálogo tipado. Las120 pasadas son reporte GLM sin log íntegro encontrado en entrega E01. Instalación privada por cliente confirmada.

## Reconfirmación E01 y nuevos contratos19–21

[Reproducción aislada02](E01/revision/EVIDENCIA_RECONFIRMACION_02.md) conserva dictamen E01-R. Documentos19/20 especifican handoff/alarma y UI accionable;21 es entrada única para GLM. Ningún módulo implementado por esta actualización. H01–H15/UIA01–12 pendientes.
