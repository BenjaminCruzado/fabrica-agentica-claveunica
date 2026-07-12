# Generacion Agentica Controlada

La fabrica usa IA real como copiloto de agentes especializados, pero no le entrega control libre del sistema.

## Modos

- `enabled=false`: la fabrica opera en modo determinista local.
- `enabled=true`: los agentes llaman al modelo configurado mediante Responses API.
- `execution-mode.local.json` con `mode=codex_direct`: Codex trabaja como agente externo, la OpenAI API queda bloqueada por defecto y la validacion se sostiene con Docker, smoke tests, Playwright y evidencia local.
- `execute_tools=false`: el modelo puede pedir herramientas, pero el runtime no las ejecuta.
- `apply_model_writes=false`: el modelo puede proponer archivos, pero el runtime no los escribe.
- `apply_model_writes=true`: el runtime aplica acciones `write_file` y `patch_file` solo si pasan `SafeFileWriter`.

## Modo Codex directo sin gasto API

Para trabajar con Codex como agente externo sin consumir saldo API, usar:

- `project/secrets/execution-mode.local.json` con `mode: "codex_direct"`.
- `allow_openai_api_calls: false`.
- `project/secrets/model-provider.local.json` conservado, pero con `enabled: false`.

Este modo no borra la integracion OpenAI API. Solo la deja bloqueada hasta que el usuario decida activarla explicitamente. Es el modo recomendado para iterar localmente con Codex: revisar codigo, corregir app, levantar Docker, ejecutar smoke tests y Playwright, sin push ni despliegue.

Para volver a una corrida agentic con API, el usuario debe cambiar manualmente:

1. `execution-mode.local.json`: quitar `codex_direct` o cambiar el modo.
2. `model-provider.local.json`: `enabled=true`.
3. Confirmar `OPENAI_API_KEY`.
4. Definir presupuesto y limite de llamadas antes de ejecutar.

## IA que codifica con control

En modo `agentic`, cada agente crea primero un plan IA estructurado. Los agentes codificadores (`implementacion_doc_code`, `database_builder`, `backend_builder`, `frontend_builder`, `test_builder` y `docker_packaging`) tienen ademas el gate `ai_code_writer`.

Eso significa:

- La IA puede escribir codigo solo con acciones JSON `write_file` o `patch_file`.
- El runtime nunca aplica texto libre ni comandos inventados.
- Cada escritura pasa por `SafeFileWriter`.
- Cada agente deja bitacora en `project/runs/<run_id>/ai-code-writer-ledger/`.
- Si una escritura es bloqueada por policy, el agente queda con `model_file_policy_failed`.
- En modo agentic, un agente critico sin plan IA valido queda bloqueado con `critical_agentic_fallback`.
- `patch_file` soporta parches exactos `SEARCH/REPLACE`; si el texto buscado no existe, el runtime devuelve error en vez de duplicar codigo silenciosamente.

## Bordes fuertes

- No se permite escribir fuera de `app-generada/` o artefactos del run.
- No se permite tocar `.git` ni `project/secrets`.
- No se permite tocar `.env`, `node_modules`, `dist`, `target` ni `__pycache__`.
- No se permite contenido con marcadores de secretos.
- No se permiten rutas absolutas.
- No se permiten archivos mayores al limite local.
- No se permite que el frontend exponga IDs de requisitos, trazabilidad, paneles de validacion, actividad generica del generador ni `screen.records`.
- Las herramientas pasan por allowlist y `PolicyEngine`.
- GitHub y EC2 siguen congelados por configuracion local.

## Estaciones de implementacion

La fase `implement` queda dividida en:

- `agent.implementacion_doc_code`: base full-stack y fallback determinista.
- `agent.database_builder`: PostgreSQL, Flyway, seed e invariantes.
- `agent.backend_builder`: Spring Boot, DTOs, servicios, controllers y tests.
- `agent.frontend_builder`: Angular, rutas, services, features y UI.
- `agent.test_builder`: smoke, contratos, integracion y runtime local preparado.

Cada estacion recibe contrato, contexto, policy, plan de IA, preflight de tools, validadores y logs de sesion.

## Ciclo esperado

1. Orquestador selecciona fase y agente.
2. Harness valida schema, policy y contexto.
3. Runtime crea contrato operativo.
4. Modelo propone pasos y acciones estructuradas.
5. Runtime aplica solo acciones permitidas por configuracion y policy.
6. Runtime escribe ledger `ai_code_writer`.
7. Funcion del agente genera o valida artefactos.
8. ValidatorChain bloquea app falsa, secretos, drift, falta de evidencia o escritura IA insegura.
9. Reviewer deja findings para correccion.

## Limpieza de app generada

En una corrida completa nueva, la fabrica no reutiliza la app vieja. Si existe `app-generada/`, la mueve a `project/runs/<run_id>/pre-run-app-generada/` antes de generar otra. Esto evita mezclar residuos de una corrida anterior con el resultado nuevo y mantiene un backup recuperable.

Para casos especiales:

- `--clean-generated-app`: fuerza backup/limpieza antes de generar.
- `--no-clean-generated-app`: conserva `app-generada/` para corridas parciales o diagnostico.

## Verificacion honesta

`python -m factory.cli verify --project project` ya no revisa solo documentos de fabrica. Tambien audita `app-generada/` y falla si detecta:

- UI de generador: `Validaciones`, `Actividad reciente`, `screen.records` o logs globales.
- Endpoints genericos como `/api/v1/actions` para botones de producto.
- Falta de `requirements-model.json`, `traceability-matrix.json`, Playwright o Docker.
- Schema generico con `metadata JSONB`.
- Falta de evidencia `docker-runtime-validation.json` con Docker y Playwright completos.
- Runs antiguos sin `generated-app-cleanup.json` quedan marcados como `legacy`; deben regenerarse para tener evidencia vigente.

## Doctor local

Antes de ejecutar la fabrica se puede correr:

```powershell
python -m factory.cli doctor --project project
```

El doctor revisa Python, pytest, Node/npm, Docker, Docker daemon, Java, Maven, configuracion OpenAI, API key y si `app-generada/` parece contaminada con artefactos viejos.

## Limpieza de requisitos

La fase `context` ejecuta `agent.requirements_cleaner` antes de recuperar contexto. Este agente escribe:

- `project/context/requirements-clean.json`
- `project/context/requirements-clean.md`
- `project/runs/<run_id>/requirements-cleaner-report.json`

Los builders prefieren `requirements-clean.json` cuando existe. El objetivo es que la IA no use fragmentos OCR/markdown rotos ni copie IDs internos en la UI.

## Cierre runtime obligatorio

Una corrida completa no debe cerrar como `complete` si falta:

- `docker compose build`.
- `docker compose up`.
- health backend.
- health frontend.
- smoke test.
- Playwright E2E.

Si el entorno local no permite ejecutar Docker o Playwright, el cierre debe quedar como `needs_user_input` o `error`, no como `complete`.

## Corrida final agentic real

Las fases finales (`implement`, `validate`, `containerize`, `close`) requieren modo agentic real:

- `model-provider.local.json` con `enabled=true`.
- `provider=openai`.
- API key disponible en la variable configurada.
- `apply_model_writes=true`.

Si falta algo, el cierre queda en `needs_user_input` y se registra en `runtime-close-gate.json`.

El objetivo es evitar dos extremos: un template fijo que siempre genera lo mismo, y una IA sin bordes que cambia cualquier cosa.

## Ciclo autonomo de reparacion

Cuando `agent.app_reviewer` no queda en `complete`, el orquestador activa un ciclo interno `repair`:

1. Registra el fallo inicial del reviewer.
2. Ejecuta `database_builder`, `backend_builder`, `frontend_builder` y `test_builder`.
3. Re-ejecuta `agent.app_reviewer`.
4. Repite hasta `max_repair_cycles`.
5. Escribe `repair-ledger.json` con intentos, agentes y resultado.

El ciclo no es infinito. Si un builder falla o el reviewer sigue bloqueando al terminar los intentos, el run cierra como `error` o `needs_user_input`.

## Regla de producto

La IA no debe crear una interfaz que muestre la fabrica por dentro. La trazabilidad y validaciones son internas; el ciudadano solo debe ver flujos de producto: iniciar tramite, actualizar domicilio, marcar notificacion, revocar permiso, revisar sesiones, responder solicitudes y acciones equivalentes del dominio.
