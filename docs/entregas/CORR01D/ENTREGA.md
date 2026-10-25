# ENTREGA CORR01D — dos correcciones acotadas (C1/C2) y cierre

Implementador: GLM/ZCode. Origen: `docs/entregas/CORR01C/revision/REVISION_CODEX_01.md`
(DEVUELTA PARA DOS CORRECCIONES ACOTADAS — no editado). E00B: **ACEPTADA**
(`docs/entregas/E00B/revision/REVISION_CODEX_01.md`) con precisiones
vinculantes registradas para E01. Estado: **lista para revisión**. Sin
funciones nuevas.

## Reproducción previa (conservada)

`pruebas/ejecuciones/20261024T230012Z_red/` (repro_script.py + salida):
- **C2 reproducido**: temporal devolvía `'crm+tests'` en lugar de `'crm tests'`
  para `application_name=crm%20tests` (urlencode de formulario en la
  derivación temporal vs quote en admin).
- **C1 reproducido**: la asignación de la huella estaba FUERA del bucle —
  `_fingerprint_bi` leía las 9 tablas pero sólo guardaba la última (`bi.meta`).

## C1 — huella de las nueve tablas (resuelto)

- `_fingerprint_bi` (tests/test_corr01c.py): cálculo y asignación **dentro
  del bucle**; `BI_TABLES` constante con las **nueve claves exactas** y
  `assert set(out) == set(BI_TABLES)` en cada llamada; serialización estable
  `_stable_payload` (filas ordenadas, claves ordenadas) → el orden del SELECT
  no afecta la comparación.
- Pruebas nuevas del propio helper:
  - `test_c1_huella_cubre_exactamente_nueve_claves` (9 claves, formato hex16).
  - `test_c1_cambio_de_contenido_cambia_su_huella` (UPDATE en `bi.dim_hora`
    cambia SU huella y sólo esa; siembra necesaria porque la limpieza entre
    pruebas TRUNCATEa bi).
  - `test_c1_serializacion_estable_ante_reordenamiento` (filas reordenadas y
    diccionarios con claves en otro orden → misma huella).
- La prueba real de ruptura ETL/recuperación se conserva y ahora compara las
  **nueve claves explícitamente** en bucle (`after[table] == before[table]`
  por tabla), no un dict completo ni sólo meta.

## C2 — parámetros URI efectivos en temporal (resuelto)

- Derivación **centralizada** en el paquete: `shared/testdsns.py::temporal_dsn
  (parts, options, dbname)` con codificación `%XX` (`quote_via=quote`);
  `parse_test_dsn` (admin), el fixture `db_url`, `_derived` de pruebas y
  `scripts/dev/smoke_packaging.py` usan **el mismo camino**.
- Pruebas puras nuevas: `test_c2_temporal_conserva_valores_escapados_como_
  admin` (application_name con `%20`, TLS y timeouts iguales en admin Y
  temporal; dbname temporal = nombre esperado vía `conninfo_to_dict`) y
  `test_c2_temporal_con_mas_signo_y_porcentaje` (`crm+tests%one` literal).
  Los rechazos de identidad/destino se re-verifican con la derivación común
  (`test_c2_rechazos_sigue_antes_de_conectar_con_derivacion_comun`).

## Verificación (nueva ejecución identificada)

Carpeta: `pruebas/ejecuciones/20261024T230648Z/` — manifiesto SHA256 del
árbol final, comandos con variables privadas, suite íntegra verbosa
(**110 passed · exit 0 · duración 61 s · UTC 23:07:55** — 104 + 6 nuevas),
wheel_externo.txt (SMOKE OK en site-packages del venv externo, exit 0),
wheel_sha256.txt (6e3ae09b…), revision_evidencia.txt (0 coincidencias, por
conteos). Reproducción roja previa conservada en 20261024T230012Z_red.

Incidentes registrados durante la corrida (todos resueltos, sin ocultar):
1. La guarda anti-checkout **abortó correctamente** una pasada ejecutada con
   el venv del proyecto (editable) — comportamiento esperado.
2. Un `pip install --quiet --force-reinstall` dejó el paquete viejo en el
   venv externo; resuelto con uninstall+install y verificación del contenido
   instalado antes de re-ejecutar.
3. El build de wheel en el venv externo falló por la CA inválida heredada;
   resuelto con `unset CURL_CA_BUNDLE` en la invocación (el comando queda
   documentado en comandos.txt).

## Precisión sobre redacción (observación no bloqueante del dictamen)

`--in-place` **limpia archivos ya escritos**; el filtro previo a persistir
exige que el flujo de captura lo invoque antes de guardar (así se usó en las
nuevas ejecuciones). «0 coincidencias» significa **cero para los patrones del
detector** (URLs postgres con credenciales, Bearer, KEY=valor), no ausencia
universal de secretos. Sin afirmaciones de rotación: admin y credencial de
pruebas siguen **pendientes del propietario**.

## Pendientes / siguiente paso
- Revisión de CORR01D; **E01 inicia sólo tras dictamen favorable**, usando
  E00B aceptada + sus 5 precisiones (F09/F10 siguen obligación de producto
  completo; numerar migración de oportunidades al implementarla; backfill
  PostgreSQL→sede Principal obligatorio en E01-M; documentar quién recibe
  «Stock ajustar» para Director; datos sin responsable a cola restringida del
  supervisor y restricciones por sede también en BI/IA existentes).
- Rotaciones operativas: propietario, fuera de esta corrección.

## Cambios de código
- `shared/testdsns.py` (+`temporal_dsn`), `tests/conftest.py` (usa helper),
  `tests/test_corr01c.py` (huella corregida + 6 pruebas nuevas),
  `scripts/dev/smoke_packaging.py` (derivación común). Suite total: **110**.
