# Agentic Quality Plan

La fabrica debe cerrar solo cuando los artefactos pasen alcance realista, app_realism, build/runtime cuando el entorno lo permita, y trazabilidad pantalla-endpoint-tabla-test.

## Ciclo esperado

1. Planner deriva dominio y contrato desde requisitos.
2. Builder genera frontend, backend, base y migraciones.
3. Reviewer ejecuta gates estaticos y, si hay runtime disponible, builds y smoke.
4. Builder corrige hasta que no queden fallas bloqueantes.
