# Entregas de GLM y revisión de Codex

Carpeta oficial para conservar toda la documentación generada durante la construcción de Premium y la evidencia de cada entrega. GLM escribe código y ejecuta pruebas; Codex revisa alcance, cambios y evidencia. Creada como documentación; todavía no contiene entregas implementadas ni resultados de pruebas.

## Organización obligatoria

```text
docs/entregas/
├── README.md
├── INDICE.md
├── PLANTILLA_ENTREGA.md
└── PRxx/
    ├── ENTREGA.md
    ├── diseno/                   # Decisiones, contratos, mapas y diagramas
    ├── cambios/                  # Archivos afectados y explicación de cambios
    ├── pruebas/
    │   ├── PLAN.md               # Casos, requisitos y entorno esperado
    │   └── ejecuciones/
    │       └── AAAAMMDD-HHMMSSZ-01/
    │           ├── RESULTADO.md  # Comandos, versión probada, tiempos y resultado
    │           ├── logs/         # Salidas reales depuradas de secretos
    │           ├── reportes/     # JUnit, cobertura u otros, si se generan
    │           └── capturas/     # Evidencia visual sin datos personales
    ├── pendientes/               # Fallos, límites, bloqueos y reproducción
    └── revision/
        ├── REVISION_CODEX_01.md
        └── RESPUESTA_GLM_01.md
```

PRxx es el ID real de la fase: PR00, PR00B, PR01, etc. Los conectores PR09 se separan, por ejemplo PR09_TELEGRAM. El árbol es una convención: GLM crea las subcarpetas al necesitar contenido; no debe crear reportes ficticios para rellenarlas. El ID de ejecución usa UTC y sufijo si hace falta evitar colisión.

## Reglas para cada entrega

1. Crear `PRxx/ENTREGA.md` desde la plantilla y mantener el índice general actualizado. Registrar el prompt recibido, su versión/ruta y cualquier aclaración que cambie el alcance.
2. Guardar diseño, contratos, mapas, decisiones y documentación de cambios dentro de la entrega o enlazar su archivo autoritativo en el repositorio. No duplicar código fuente completo: listar archivos modificados y, si se adjunta un diff, revisarlo para eliminar secretos.
3. Para cada ejecución conservar fecha UTC, zona de presentación, entorno y versiones, identificación del código probado, comando exacto sin credenciales, salida real, código de salida, duración y totales. Si no hay commit del trabajo actual, describir cambios pendientes y una huella reproducible de archivos probados; no presentar HEAD como si incluyera esos cambios.
4. Registrar pasadas, fallidas, omitidas y no ejecutadas por separado. Identificar proveedor simulado o externo real y base temporal usada. No reusar conteos históricos como resultado actual. PR00 documental puede indicar «no ejecutado: fase de documentación».
5. Cada corrección conserva la ejecución fallida y añade una nueva; nunca sobrescribir evidencia para que sólo queden resultados verdes. Vincular hallazgo → corrección → nueva evidencia.
6. GLM marca «lista para revisión», «parcial» o «bloqueada» y detiene la fase. Sólo Codex escribe su dictamen en `revision/REVISION_CODEX_nn.md`; GLM responde en archivo separado y no modifica el dictamen. Una decisión posterior se añade, conservando la anterior.
7. Actualizar `docs/producto/ESTADO.md` con ruta de entrega, resultado real, pendientes y siguiente paso. La siguiente fase depende de aceptación documentada de la anterior.
8. No guardar .env, tokens, contraseñas, bases de clientes, backups de producción ni datos personales en evidencia. Si un log los contiene, no adjuntarlo sin depuración; documentar la depuración sin inventar contenido. Usar fixtures sintéticos.
9. Guardar evidencia textual depurada y capturas necesarias en el repositorio. Si un archivo excepcionalmente grande se mantiene fuera, dejar manifiesto con ruta privada accesible al revisor, tamaño, huella y motivo; no incluirlo como evidencia disponible hasta comprobar acceso.

Los reportes ya solicitados con nombres `REPORTE_PRxx.md` se guardan como `docs/entregas/PRxx/ENTREGA.md`. Esta ruta es la autoritativa para nuevas entregas Premium. No mover evidencias históricas existentes sin necesidad; enlazarlas y distinguirlas de una ejecución nueva.

## Instrucción para GLM

En toda entrega, incluida PR00, guarda documentación y evidencia bajo docs/entregas/<ID> conforme a este README y PLANTILLA_ENTREGA.md. Actualiza INDICE.md y ESTADO.md. Al terminar, indica la ruta exacta de ENTREGA.md y las ejecuciones que sustentan tu resultado. No afirmes aceptación de Codex ni avances de fase sin dictamen. Si no ejecutaste pruebas, dilo expresamente.
