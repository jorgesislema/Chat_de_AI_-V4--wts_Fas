# GLM — CORR01D, dos correcciones y cierre
Fecha: 24-10-2026. Codex especifica/revisa; GLM implementa/prueba.
Raíz: H:\git\Agente de reserva V4.

Leer dictámenes:
- docs/entregas/CORR01C/revision/REVISION_CODEX_01.md
- docs/entregas/E00B/revision/REVISION_CODEX_01.md

E00B ya está aceptada como base documental con precisiones vinculantes. No rehacerla ni ampliar producto. El aislamiento dbname corregido se reconoce; conservar lista blanca/guardas. Sólo quedan C1/C2 de CORR01C.

## C1 — huella de las nueve tablas
Corregir _fingerprint_bi: cálculo y asignación dentro de bucle, conjunto exacto de nueve claves, serialización estable de contenido sin depender del orden de SELECT. Afirmar explícitamente todas las claves, no sólo before['bi.meta'] != 'empty'. Añadir prueba del helper: cambio de contenido en tabla no-meta debe cambiar huella correspondiente; reordenar las mismas filas no debe cambiarla. Conservar prueba real de ruptura ETL y recuperación; comparar todas las tablas declaradas.

## C2 — parámetros URI efectivos en temporal
Eliminar divergencia entre parse_test_dsn (quote_via=quote) y derivación temporal de conftest/_derived. Preferir helper común de derivación con nombre validado o codificación consistente. Comprobar conninfo_to_dict sobre admin Y temporal: application_name con espacios/+/porcentaje/escapes conserva valor; opciones TLS admitidas no pierden valor y claves de identidad/destino continúan rechazadas antes de conectar. Smoke debe usar la misma derivación probada.

## Verificación y entrega
Reproducir ambos fallos antes de corregir y conservar salida. Pruebas puras sin conexión primero; luego ruptura ETL/migración y regresión PostgreSQL sobre base temporal con URL explícita. No leer .env ni credenciales de reportes/chat. No cambiar contraseñas, datos operativos ni servicios externos.
Registrar docs/entregas/CORR01D/ENTREGA.md con respuesta C1/C2, código probado, manifiesto nuevo, entorno/comandos depurados/salida/exit/duración, casos omitidos y nueva ejecución identificada. No atribuir hashes nuevos a corridas anteriores.
Actualizar descripción de redacción con precisión: --in-place limpia lo ya escrito; filtro previo a persistir requiere flujo de captura real. No afirmar «cero secretos» por sólo cero patrones.
Conservar dictámenes de Codex sin modificarlos. No reconstruir otra fase técnica ni añadir funciones. Presentar CORR01D para revisión; E01 comienza sólo tras su dictamen favorable y usa E00B más las precisiones aceptadas. La rotación operativa pendiente del propietario se informa aparte.
