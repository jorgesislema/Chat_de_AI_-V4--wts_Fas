# Plan de pruebas CORR01

Objetivo: cada R con reproducción previa que falla y prueba posterior que
pasa, sobre PostgreSQL temporal real (servidor aislado, opt-in explícito).

## Secuencia ejecutada

1. **Corrida roja** (`ejecuciones/red_corrida1.txt`): `tests/test_corr01.py`
   contra el código auditado → 13 fallos que reproducen R02, R03(×2),
   R04, R05, R06, R07, R08(×5) y R10-locks. R01/R11 son documentales (sin
   prueba de código); R09 se verifica por el propio conftest (rechaza
   ejecutarse sin opt-in explícito).
2. **Correcciones** por R (ver ENTREGA.md §Cambios).
3. **Corrida verde** (`ejecuciones/green_corrida_final.txt`): suite completa
   **90 passed** (incluye las 18 de test_corr01 + suites previas corregidas).
4. **Empaquetado** (`ejecuciones/smoke_packaging.txt`): wheel instalado en
   venv externo; migraciones/render/estáticos verificados fuera del checkout.
5. **Servidor real**: reinicio y 10 rutas en 200 (registro en la sesión).

## Cobertura por R

- R02: test_r02_reversion_total_neto_cero_y_fechas_propias;
  test_r02_asistente_cuenta_reversion_en_su_momento;
  test_reversion_conserva_positivo_y_compensa (mezcla con 350).
- R03: 6 pruebas de frontera (noche cerrada, 17:00:30, cierre exacto, fin de
  semana, 23:59:00/23:59:30, 24×7).
- R04/R05: dos usuarios reales; ausencia de datos ajenos con marca única;
  ajustes globales bloqueados a usuario ordinario.
- R06/R07: token muerto tras cambio de rol; incorrecta→correcta sin recarga;
  token ajeno 400.
- R08: demo excluido/incluido por opt-in; costo snapshot vs recalculado;
  NULL preservado; cobros→no_disponible; tops por tipo.
- R10: A,B/B,A concurrente sin deadlock, stock exacto; instalación wheel.
- Regresión de las previas: cubierta dentro de las 90 (ninguna eliminada; se
  ajustaron expectativas cambiadas por diseño: reversión con valores absolutos).

## Pendientes de prueba (declarados en ENTREGA §pendientes)

- Fallo de migración/ETL a mitad de lote con conservación del lote bueno.
- Recorrido visual independiente del navegador (Codex).
- Rotación real de credencial (acción del propietario).
