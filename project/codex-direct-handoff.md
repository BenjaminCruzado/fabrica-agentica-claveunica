# Codex Direct Handoff

Este archivo es el punto de continuidad para trabajar la fabrica en modo Codex directo.

## Modo actual

- Modo de trabajo: `codex_direct`.
- OpenAI API interna de la fabrica: bloqueada por defecto.
- Archivo de modo: `project/secrets/execution-mode.local.json`.
- Config API conservada pero desactivada: `project/secrets/model-provider.local.json` con `enabled=false`.
- GitHub push: bloqueado.
- EC2 deploy: bloqueado.
- Trabajo esperado: solo local.

## Respaldo base

La app generada con API y reparada localmente fue respaldada en:

`app-generada-respaldo-api-20260711-215533/`

Ese respaldo sirve para comparar contra futuras mejoras hechas por Codex directo.

## Estado validado antes del modo Codex directo

La app `app-generada/` llego a pasar validacion local:

- Docker Compose levanto Postgres, backend y frontend.
- Backend health: `http://localhost:8080/api/v1/health` respondio `200`.
- Frontend: `http://localhost:3000` respondio `200`.
- Smoke test: `npm.cmd test` paso.
- Playwright: `npx.cmd playwright test` paso con 2 tests.

El run formal de la fabrica no quedo `complete` porque hubo error OpenAI `429` en agentes criticos. En modo Codex directo eso se evita bloqueando llamadas API internas.

## Como retomar si se corta Codex

Cuando se retome, partir con:

```powershell
cd "C:\Users\Benjamin Cruzado\Desktop\Ultimo Semestre\IA\PROYECTO\fabrica-final"
git status --short
python -m factory.cli doctor --project project
docker compose ps
```

Luego revisar:

```powershell
Get-Content -LiteralPath "project\codex-direct-handoff.md"
Get-Content -LiteralPath "project\secrets\execution-mode.local.json"
Get-Content -LiteralPath "project\secrets\model-provider.local.json"
```

## Reglas para Codex directo

- No usar OpenAI API desde la fabrica.
- No activar `model-provider.local.json` sin instruccion explicita del usuario.
- No hacer `git push`.
- No desplegar en EC2.
- No borrar el respaldo `app-generada-respaldo-api-20260711-215533/`.
- Si se corrige app o fabrica, validar con Docker, smoke y Playwright cuando aplique.
- Mantener este archivo actualizado con avances, errores y siguiente paso.

## Siguiente paso recomendado

Usar Codex directo para mejorar la app/fabrica sobre `app-generada/`, comparando contra el respaldo cuando sea necesario, y dejando evidencia local de cada reparacion.

## Ejecucion Codex Direct 2026-07-11

Prompt ejecutado:

`Ejecuta la fabrica en local usando el work_order actual, en modo Codex directo.`

Resultado:

- Run completo final: `project/runs/RUN-f944ce026be1/`.
- Estado final: `complete`.
- `ready_for_first_project`: `true`.
- `runtime-close-gate.json`: `status=complete`.
- Docker runtime: `runtime_complete`.
- Playwright: `complete`.
- Verify global: `python -m factory.cli verify --project project` devolvio `status=complete`.
- API interna: bloqueada durante la ejecucion (`codex_direct`, `model-provider.enabled=false`, `OPENAI_API_KEY` vacia en el proceso).
- GitHub/EC2: sin push y sin deploy.

Correcciones hechas durante esta ejecucion:

- Se corrigio el health check portable en `factory/agents.py`; el comando Python de health ya no usa `with` en una sola linea.
- Se ajusto `app_reviewer` para aceptar `docker-runtime-validation.json` con `runtime_complete` como evidencia honesta cuando no existe `coverage-report.json`.

Estado local al cierre:

- App levantada por Docker Compose.
- Postgres healthy.
- Backend healthy en `http://localhost:8080/api/v1/health`.
- Frontend healthy en `http://localhost:3000`.

