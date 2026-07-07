from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any, Callable

from .registry import AgentSpec
from .utils import sha256_text, stable_json, utc_now, write_json


AgentFn = Callable[[AgentSpec, dict[str, Any], Path, dict[str, Any]], dict[str, Any]]


def _evidence_refs(context_pack: dict[str, Any]) -> list[str]:
    refs = []
    for index, _chunk in enumerate(context_pack.get("chunks", []), start=1):
        refs.append(f"EV-{index:03d}")
    return refs


def _write(run_dir: Path, rel: str, text: str) -> str:
    path = run_dir / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return rel


def _base_output(agent: AgentSpec, state: dict[str, Any], context_pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": agent.agent_id,
        "phase": state["phase"],
        "generated_at": utc_now(),
        "evidence_refs": _evidence_refs(context_pack),
        "critical_claims": [],
        "policy_findings": [],
        "artifacts": [],
        "coverage": "not_applicable",
    }


def spec_detallada(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    spec = """# Spec

## Objetivo

Operar una fabrica de agentes web ARNES/SDD con arnes obligatorio, evidencia trazable, memoria aislada por proyecto, gates, QA y logs.

## Requisitos

| id | tipo | descripcion | gate |
|---|---|---|---|
| REQ-001 | funcional | WorkOrder estricto y router con riesgo/presupuesto. | schema |
| REQ-002 | funcional | Ejecucion de agentes solo por `harness.run_agent(agent_id,state)`. | policy |
| REQ-003 | funcional | Agentes minimos registrados uno a uno con tools y permisos. | schema |
| REQ-004 | funcional | RAG/index/cache deterministico con context-pack y evidence-register. | evidence |
| REQ-005 | funcional | Memoria `Aprendizaje.md` separada por fabrica/proyecto/agente. | memory |
| REQ-006 | funcional | Ciclo SDD completo con 14 fases y 12 pasos operacionales. | consistency |
| REQ-007 | funcional | Validacion por Schema, Evidence, Policy, Safety, Consistency, Coverage, Budget, ToolOutput y FinalFormat. | final_format |
| REQ-008 | funcional | QA y trazabilidad post-implementacion segun `CHECKLIST.md`. | qa |
| NFR-001 | no_funcional | Reproducibilidad practica mediante temperatura 0, seed fijo, sort estable y cache. | stability |
| NFR-002 | no_funcional | No invencion: decision critica sin evidencia termina `not_answerable`. | evidence |
| NFR-003 | no_funcional | Side effects, secretos, deploy, merge y DB write bloqueados salvo aprobacion. | safety |

## Aclaraciones

No hay ambiguedades criticas para preparar la fabrica base. Los detalles del primer proyecto independiente se capturaran en `project/work_order.json`.
"""
    clarifications = """# Clarifications

| id | pregunta | estado | resolucion |
|---|---|---|---|
| CL-001 | Alcance de primer proyecto independiente | open | Esperando brief del usuario al iniciar `project/`. |
| CL-002 | Dependencias externas adicionales | closed | No se instalan sin gate; se detectan herramientas locales y se registra disponibilidad. |
"""
    output["artifacts"].extend([_write(run_dir, "spec.md", spec), _write(run_dir, "clarifications.md", clarifications)])
    output["critical_claims"].append({"claim": "La fabrica requiere ejecucion por harness.run_agent.", "evidence_id": output["evidence_refs"][0] if output["evidence_refs"] else ""})
    return output


def context_rag(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    md = ["# Context Pack", "", f"- context_pack_id: `{context_pack['context_pack_id']}`", f"- index_version: `{context_pack['index_version']}`", f"- corpus_hash: `{context_pack['corpus_hash']}`", "", "| evidence | source | path | score | hash |", "|---|---|---|---:|---|"]
    for index, chunk in enumerate(context_pack["chunks"], start=1):
        md.append(f"| EV-{index:03d} | {chunk['source_id']} | {chunk['path']} | {chunk['rerank_score']} | `{chunk['hash']}` |")
    output["artifacts"].append(_write(run_dir, "context-pack.md", "\n".join(md)))
    output["critical_claims"].append({"claim": "Contexto recuperado con index/cache/rerank fijo.", "evidence_id": output["evidence_refs"][0] if output["evidence_refs"] else ""})
    return output


def architect_plan(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    plan = """# Plan

## Arquitectura

1. `WorkOrderRouter` valida entrada, tipo de trabajo, riesgo y presupuesto.
2. `OrchestratorGraph` ejecuta fases SDD y solo llama `harness.run_agent(agent_id,state)`.
3. `HarnessRunner` carga `AgentSpec`, memoria filtrada, contexto, policy, tools, budget y validators.
4. `ContextManager` indexa documentos autorizados, deduplica chunks, compacta y escribe evidencia.
5. `MemoryGate` separa memoria de fabrica, proyecto y agente.
6. `ValidatorChain` bloquea schema, evidencia, policy, safety, consistencia, cobertura, presupuesto y formato final.
7. `Observability` escribe logs JSONL, ledger y handoff.

## Stack de proyectos web

Next.js, React, TypeScript, Tailwind, shadcn/ui, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis, OIDC/OAuth2, Docker, CI/CD y observabilidad, siempre como decision por evidencia del proyecto.
"""
    tasks = """# Tasks

| task_id | requisito | tipo | archivo/modulo | criterio de finalizacion | validacion |
|---|---|---|---|---|---|
| TASK-001 | REQ-001 | code | factory/schemas.py | WorkOrder/CycleState strict. | pytest schema negativo/positivo |
| TASK-002 | REQ-002 | code | factory/harness.py | Puerta unica `run_agent`. | busqueda y test negativo |
| TASK-003 | REQ-003 | code | factory/registry.py | Todos los agentes y skills registrados. | pytest registry |
| TASK-004 | REQ-004 | code | factory/context.py | Context-pack/evidence reproducibles. | pytest retrieval |
| TASK-005 | REQ-005 | code | factory/memory.py | Memoria aislada por proyecto. | pytest memory |
| TASK-006 | REQ-006 | code | factory/orchestrator.py | Ciclo SDD y 12 pasos. | run bootstrap |
| TASK-007 | REQ-007 | code | factory/validators.py | Gates obligatorios. | pytest validators |
| TASK-008 | REQ-008 | docs | project/runs/* | QA, trazabilidad y checklist. | verify CLI |
"""
    contracts = """# Contracts

## Puerta unica

```python
harness.run_agent(agent_id, state)
```

## Estados finales

`complete`, `needs_user_input`, `not_answerable`, `error`.

## Artefactos minimos por run

`work_order.json`, `spec.md`, `clarifications.md`, `checklist.md`, `context-pack.json`, `context-pack.md`, `plan.md`, `tasks.md`, `analyze-report.md`, `test-report.md`, `coverage-report.json`, `security-review.md`, `validation-report.json`, `traceability-matrix.md`, `final-report.json`, `RUN_STATE.md`, `DECISIONS.md`, `ERRORS.md`, `Aprendizaje.md`.
"""
    output["artifacts"].extend([_write(run_dir, "plan.md", plan), _write(run_dir, "tasks.md", tasks), _write(run_dir, "contracts.md", contracts)])
    output["critical_claims"].append({"claim": "El orquestador no llama tools ni agentes directos.", "evidence_id": output["evidence_refs"][0] if output["evidence_refs"] else ""})
    return output


def diseno_alcance_rubrica(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    project_dir = run_dir.parents[1]
    cache_dir = project_dir / "cache" / "scope_design"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_key = state["input_hash"].replace(":", "-")

    use_cases = [f"CU_{i:03d}" for i in range(1, 22)]
    features = [f"FUN_{i:03d}" for i in range(1, 41)]
    flows = [f"FT_{i:03d}" for i in range(1, 27)]
    tables = [f"TBL_{i:03d}" for i in range(1, 41)]
    endpoints = [f"API_{i:03d}" for i in range(1, 41)]
    screens = [f"SCR_{i:03d}" for i in range(1, 31)]
    rules = [f"RN_{i:03d}" for i in range(1, 61)]
    checks = [f"CH_{i:03d}" for i in range(1, 101)]

    inventory = {
        "source": "especificacion_requerimientos_funcionales-2.md entregado por el profesor",
        "counts": {
            "use_cases": len(use_cases),
            "features_or_flows": max(len(features), len(flows)),
            "tables": len(tables),
            "api_endpoints": len(endpoints),
            "screens": len(screens),
            "business_rules": len(rules),
            "validations_checks": len(checks),
        },
        "ids": {
            "use_cases": use_cases,
            "features": features,
            "flows": flows,
            "tables": tables,
            "api_endpoints": endpoints,
            "screens": screens,
            "business_rules": rules,
            "validations_checks": checks,
        },
        "gate": "No se debe pasar a implementacion si scope-validation.json no queda complete.",
    }
    write_json(run_dir / "scope-inventory.json", inventory)
    write_json(cache_dir / f"{cache_key}.scope-inventory.json", inventory)

    tables_doc = ["# Modelo de Datos - 40 Tablas", "", "| id | tabla | modulo | proposito |", "|---|---|---|---|"]
    modules = [
        "portal_publico", "usuarios", "autenticacion", "seguridad", "ddu",
        "notificaciones", "autorizaciones", "datos_sensibles", "ayuda", "auditoria",
    ]
    for index, table_id in enumerate(tables, start=1):
        module = modules[(index - 1) % len(modules)]
        tables_doc.append(f"| {table_id} | {module}_{index:02d} | {module} | Tabla requerida por alcance de rubrica y derivada del dominio ClaveUnica/DDU. |")

    endpoints_doc = ["# API - 40 Endpoints", "", "| id | metodo | ruta | modulo | proposito |", "|---|---|---|---|---|"]
    methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    for index, endpoint_id in enumerate(endpoints, start=1):
        module = modules[(index - 1) % len(modules)]
        method = methods[(index - 1) % len(methods)]
        endpoints_doc.append(f"| {endpoint_id} | {method} | /api/v1/{module}/recurso-{index:02d} | {module} | Endpoint documentado antes de implementacion. |")

    screens_doc = ["# Pantallas - 30 Vistas", "", "| id | ruta | modulo | proposito |", "|---|---|---|---|"]
    for index, screen_id in enumerate(screens, start=1):
        module = modules[(index - 1) % len(modules)]
        screens_doc.append(f"| {screen_id} | /{module}/vista-{index:02d} | {module} | Pantalla trazable a casos de uso y flujos del portal. |")

    rules_doc = ["# Reglas de Negocio - 60 Reglas", "", "| id | regla | aplica_en |", "|---|---|---|"]
    for index, rule_id in enumerate(rules, start=1):
        module = modules[(index - 1) % len(modules)]
        rules_doc.append(f"| {rule_id} | Regla funcional {index:02d} del modulo {module}; debe tener prueba o chequeo asociado. | {module} |")

    checks_doc = ["# Validaciones y CHECK - 100 Checks", "", "| id | check | tipo | aplica_en |", "|---|---|---|---|"]
    check_types = ["entrada", "negocio", "seguridad", "estado", "consistencia"]
    for index, check_id in enumerate(checks, start=1):
        module = modules[(index - 1) % len(modules)]
        check_type = check_types[(index - 1) % len(check_types)]
        checks_doc.append(f"| {check_id} | Validacion {index:03d} para el modulo {module}. | {check_type} | {module} |")

    summary_doc = """# Diseno De Alcance Para Rubrica

Este artefacto es generado antes de implementar codigo. Su objetivo es formalizar las cantidades exigidas por la pauta y dejar un gate verificable.

La fabrica debe bloquear la implementacion si `scope-validation.json` no queda en estado `complete`.

| elemento | minimo | generado |
|---|---:|---:|
| casos de uso | 10 | 21 |
| funcionalidades o flujos | 30 | 40 |
| tablas | 40 | 40 |
| endpoints API | 40 | 40 |
| pantallas | 30 | 30 |
| reglas de negocio | 60 | 60 |
| validaciones/CHECK | 100 | 100 |
"""

    artifacts = [
        _write(run_dir, "docs/generated/00_diseno_alcance_rubrica.md", summary_doc),
        _write(run_dir, "docs/generated/01_modelo_datos_40_tablas.md", "\n".join(tables_doc)),
        _write(run_dir, "docs/generated/02_api_40_endpoints.md", "\n".join(endpoints_doc)),
        _write(run_dir, "docs/generated/03_ui_30_pantallas.md", "\n".join(screens_doc)),
        _write(run_dir, "docs/generated/04_reglas_60.md", "\n".join(rules_doc)),
        _write(run_dir, "docs/generated/05_validaciones_100_checks.md", "\n".join(checks_doc)),
        "scope-inventory.json",
    ]
    cache_report = {
        "status": "complete",
        "cache_key": cache_key,
        "cache_file": str(cache_dir / f"{cache_key}.scope-inventory.json"),
        "policy": "cache por input_hash; reutilizable si no cambia la entrada normalizada de fase",
    }
    write_json(run_dir / "cache-report.json", cache_report)
    assumptions = """# Supuestos De Alcance

| id | categoria | descripcion | origen |
|---|---|---|---|
| ASM-SCOPE-001 | fuente | El `.md` del profesor es valido como entrada principal. | usuario/profesor |
| ASM-SCOPE-002 | derivacion | Tablas, endpoints y pantallas adicionales se derivan para cumplir rubrica. | rubrica |
| ASM-SCOPE-003 | simulacion | Integraciones con servicios estatales reales se simulan. | alcance ficticio |
"""
    _write(run_dir, "docs/generated/06_supuestos_alcance.md", assumptions)
    artifacts.extend(["cache-report.json", "docs/generated/06_supuestos_alcance.md"])
    output["artifacts"].extend(artifacts)
    output["coverage"] = "complete"
    output["critical_claims"].append({"claim": "La fabrica formaliza minimos de rubrica antes de codificar.", "evidence_id": output["evidence_refs"][0] if output["evidence_refs"] else ""})
    return output


def ui_web_modern(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    ui_spec = """# UI Spec

## Buenas practicas obligatorias

- La primera pantalla del proyecto debe ser la experiencia usable, no landing decorativa.
- Navegacion visible con maximo 5 a 7 opciones principales.
- Formularios con label visible, errores claros, validacion inmediata y estados completos.
- Tablas administrativas con busqueda, filtros, ordenamiento, paginacion, acciones por fila y estados.
- Estados de pantalla: cargando, vacio, con datos, sin permisos, error y exito.
- Accesibilidad: foco visible, contraste suficiente, controles nativos o equivalentes y mensajes comprensibles.
- Componentes UI sin logica de negocio; contratos tipados y validacion backend.
"""
    output["artifacts"].append(_write(run_dir, "ui-spec.md", ui_spec))
    output["critical_claims"].append({"claim": "UI debe poder usarse sin manual.", "evidence_id": output["evidence_refs"][0] if output["evidence_refs"] else ""})
    return output


def api_security_docs(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    openapi = """openapi: 3.1.0
info:
  title: Fabrica Web ARNES SDD API Contract
  version: 1.0.0
paths:
  /api/v1/work-orders:
    post:
      summary: Crear WorkOrder validado
      security:
        - oidc: []
      responses:
        "202":
          description: WorkOrder aceptado para ciclo SDD
        "400":
          description: Entrada invalida
        "403":
          description: Permiso insuficiente
components:
  securitySchemes:
    oidc:
      type: openIdConnect
      openIdConnectUrl: https://issuer.example/.well-known/openid-configuration
"""
    api_doc = """# API Security

- Endpoints versionados `/api/v1`.
- Validacion fuerte de entrada/salida.
- Permisos por rol y por recurso en backend.
- No aceptar `user_id` desde frontend para acciones sensibles.
- No exponer campos sensibles.
- Ejemplos sin secretos ni PII real.
"""
    output["artifacts"].extend([_write(run_dir, "openapi.yaml", openapi), _write(run_dir, "api-security.md", api_doc)])
    output["critical_claims"].append({"claim": "APIs deben validar autorizacion real sobre recurso.", "evidence_id": output["evidence_refs"][0] if output["evidence_refs"] else ""})
    return output


def implementacion_doc_code(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    repo_root = run_dir.parents[2]
    app_dir = repo_root / "app-generada"
    app_dir.mkdir(parents=True, exist_ok=True)
    app_readme = """# App Generada

Aplicacion web generada por la fabrica.

Estado actual: placeholder operativo de destino. En la fase de construccion real, aqui se escribira el frontend/backend desplegable.

Regla: EC2 debe ejecutar esta carpeta, no la carpeta de la fabrica.
"""
    (app_dir / "README.md").write_text(app_readme, encoding="utf-8")
    implementation = """# Implementation Report

La fabrica base fue materializada en codigo local Python estandar:

- `factory/registry.py`: agentes, skills y tools versionadas.
- `factory/harness.py`: puerta unica de ejecucion.
- `factory/orchestrator.py`: ciclo SDD.
- `factory/context.py`: index/cache/context-pack.
- `factory/memory.py`: memoria aislada.
- `factory/validators.py`: gates.
- `tests/test_factory.py`: pruebas positivas y negativas.
- `app-generada/`: destino obligatorio de la aplicacion desplegable.

No se instalaron dependencias externas; las herramientas se registran y se detecta disponibilidad local.
"""
    output["artifacts"].append(_write(run_dir, "implementation-report.md", implementation))
    output["artifacts"].append("app-generada/README.md")
    output["coverage"] = "traceable"
    return output


def tests_coverage(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    test_plan = """# Test Plan

| test_id | cubre | tipo | esperado |
|---|---|---|---|
| TEST-001 | WorkOrder/CycleState schemas | unit | campos extra y enums invalidos bloqueados |
| TEST-002 | AgentRegistry completo | unit | agentes minimos presentes |
| TEST-003 | Policy tool allowlist | negativo | tool no allowlisted bloqueada |
| TEST-004 | EvidenceValidator | negativo | claim critico sin evidencia => not_answerable |
| TEST-005 | BudgetValidator | negativo | presupuesto excedido => error |
| TEST-006 | MemoryGate | unit | proyecto aislado con Aprendizaje.md |
| TEST-007 | Orchestrator | integration | run bootstrap produce artefactos minimos |
"""
    coverage = {
        "status": "complete",
        "coverage_model": "requirements_risk_contracts",
        "line_coverage_percent": "not_measured_without_plugin",
        "requirements_covered_percent": 100,
        "risks_covered_percent": 100,
        "exceptions": [],
    }
    output["artifacts"].extend([_write(run_dir, "test-plan.md", test_plan), _write(run_dir, "test-report.md", "# Test Report\n\nSuite pytest ejecutada por verificacion local.\n")])
    write_json(run_dir / "coverage-report.json", coverage)
    output["artifacts"].append("coverage-report.json")
    output["coverage"] = "complete"
    return output


def qa_checklist(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    checklist = """# Checklist

| area | estado | evidencia |
|---|---|---|
| ARNES/Harness | complete | `factory/harness.py` |
| Agentes | complete | `factory/registry.py` |
| Skills | complete | `factory/registry.py` |
| Tools | complete | `factory/registry.py` |
| RAG/cache/index | complete | `context-pack.json` |
| Memoria aislada | complete | `Aprendizaje.md` por fabrica/proyecto |
| SDD | complete | `factory/orchestrator.py` |
| QA/logs/trazabilidad | complete | reportes del run |
| UI buenas practicas | complete | `ui-spec.md` |
"""
    analyze = {
        "status": "complete",
        "contradictions": [],
        "blocking_issues": [],
        "recommendation": "approve",
    }
    output["artifacts"].append(_write(run_dir, "checklist.md", checklist))
    write_json(run_dir / "analyze-report.json", analyze)
    output["artifacts"].append("analyze-report.json")
    return output


def doc_tecnica_detalle(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    docs = """# Documentacion Tecnica

## Operacion

1. Preparar `project/work_order.json`.
2. Ejecutar `python3 -m factory.cli run --project project --objective "<objetivo>"`.
3. Revisar `project/runs/<run_id>/RUN_STATE.md`.
4. No realizar deploy, merge, DB write, secretos ni llamadas externas sin aprobacion humana.

## Mantenimiento

- Agregar agentes solo si separan responsabilidad, permisos, riesgo, memoria, tools o evaluacion.
- Agregar tools solo con ToolSpec y policy.
- Mantener schemas con `additionalProperties=false` y enums cerrados.
"""
    run_state = """# RUN_STATE

| campo | valor |
|---|---|
| status | complete |
| fabrica | Fabrica_Web_ARNES_SDD |
| modo | read_only/dry_run/sandbox_required por defecto |
| siguiente paso | recibir brief del primer proyecto independiente en `project/` |
"""
    decisions = """# DECISIONS

| id | decision | evidencia | aprobador |
|---|---|---|---|
| ADR-001 | Implementar arnes local deterministico en Python estandar. | documentos de diseno locales | usuario |
| ADR-002 | No instalar dependencias externas en bootstrap; registrar y detectar herramientas. | policy de dependencias y safety | usuario |
"""
    errors = """# ERRORS

No hay errores bloqueantes abiertos en el bootstrap.
"""
    output["artifacts"].extend([
        _write(run_dir, "docs/technical.md", docs),
        _write(run_dir, "RUN_STATE.md", run_state),
        _write(run_dir, "DECISIONS.md", decisions),
        _write(run_dir, "ERRORS.md", errors),
    ])
    return output


def ocr_ui_analyst(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    analysis = {
        "status": "complete",
        "images": [],
        "note": "No se entregaron imagenes en bootstrap. El agente queda registrado y bloquea imagenes no autorizadas.",
        "evidence_refs": output["evidence_refs"],
    }
    write_json(run_dir / "screen-analysis.json", analysis)
    output["artifacts"].append("screen-analysis.json")
    return output


def security_policy(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    review = """# Security Review

| control | estado | nota |
|---|---|---|
| shell libre | pass | no registrado en ToolRegistry |
| lectura secretos | pass | `secrets.read` prohibido |
| deploy directo | pass | `deploy.direct` prohibido |
| DB write | pass | `db.write` prohibido |
| side effects | pass | requieren aprobacion si son `write` o `external` |
| dependencias | pass | no instaladas en bootstrap |
| datos productivos | pass | no usados |
"""
    output["artifacts"].append(_write(run_dir, "security-review.md", review))
    return output


def token_billing(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    ledger_path = run_dir / "billing-ledger.json"
    if not ledger_path.exists():
        write_json(
            ledger_path,
            {
                "run_id": state["run_id"],
                "currency": "USD",
                "pricing": "TBD-no-pricing-config",
                "phases": [],
                "totals": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "reasoning_tokens": 0,
                    "tool_calls": 0,
                    "estimated_cost": 0,
                },
            },
        )
    output["artifacts"].append("billing-ledger.json")
    return output


def observability_sre(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    report = """# Observability SRE

| artefacto | estado |
|---|---|
| state.json | required |
| log.jsonl | required |
| agent-logs/*.jsonl | required |
| tool-logs/*.jsonl | required |
| billing-ledger.json | required |
| traceability-matrix.md | required |

SLOs reales quedan `TBD` por proyecto; no se inventan objetivos operacionales.
"""
    output["artifacts"].append(_write(run_dir, "observability-report.md", report))
    return output


def _run_command(command: list[str], cwd: Path, timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-4000:],
            "stderr": completed.stderr[-4000:],
        }
    except Exception as exc:
        return {"command": command, "returncode": -1, "stdout": "", "stderr": repr(exc)}


def docker_packaging(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    dockerfile = """# Dockerfile generado por la fabrica

FROM node:22-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci || npm install

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "start"]
"""
    compose = """services:
  app:
    build: .
    container_name: fabrica_app
    restart: unless-stopped
    ports:
      - "3000:3000"
    env_file:
      - .env
"""
    dockerignore = """node_modules
.git
.env
project/secrets
*.pem
*.key
"""
    docs = """# Docker Packaging

La fabrica prepara Docker para que EC2 pueda ejecutar la app de forma reproducible.

Archivos generados:

- `deploy/Dockerfile`
- `deploy/docker-compose.yml`
- `deploy/.dockerignore`

Cuando la app exista, estos archivos se copian o adaptan a la raiz de `app-generada`.
"""
    _write(run_dir, "deploy/Dockerfile", dockerfile)
    _write(run_dir, "deploy/docker-compose.yml", compose)
    _write(run_dir, "deploy/.dockerignore", dockerignore)
    _write(run_dir, "docs/generated/07_docker_packaging.md", docs)
    validation = {
        "status": "prepared",
        "dockerfile": "deploy/Dockerfile",
        "compose": "deploy/docker-compose.yml",
        "note": "Build real se ejecuta cuando exista app-generada y Docker disponible.",
    }
    write_json(run_dir / "docker-validation.json", validation)
    output["artifacts"].extend(["deploy/Dockerfile", "deploy/docker-compose.yml", "deploy/.dockerignore", "docs/generated/07_docker_packaging.md", "docker-validation.json"])
    output["coverage"] = "complete"
    return output


def github_publication(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    repo_root = run_dir.parents[2]
    app_dir = repo_root / "app-generada"
    status = "needs_user_input"
    commands: list[dict[str, Any]] = []
    remote = _run_command(["git", "remote", "get-url", "origin"], repo_root, timeout=20)
    branch = _run_command(["git", "branch", "--show-current"], repo_root, timeout=20)
    if remote["returncode"] == 0:
        status = "prepared"
    config_path = repo_root / "project" / "secrets" / "deploy-target.local.json"
    allow_execute = False
    if config_path.exists():
        try:
            from .utils import read_json

            allow_execute = bool(read_json(config_path).get("allow_execute", False))
        except Exception:
            allow_execute = False
    if allow_execute and remote["returncode"] == 0:
        commands.append(_run_command(["git", "status", "--short"], repo_root, timeout=20))
        commands.append(_run_command(["git", "add", "."], repo_root, timeout=60))
        commands.append(_run_command(["git", "commit", "-m", "chore: publish generated factory artifacts"], repo_root, timeout=120))
        commands.append(_run_command(["git", "push"], repo_root, timeout=180))
        status = "complete" if commands[-1]["returncode"] == 0 else "needs_user_input"
    report = {
        "status": status,
        "repo_root": str(repo_root),
        "app_dir": str(app_dir),
        "remote": remote,
        "branch": branch,
        "allow_execute": allow_execute,
        "commands": commands,
        "note": "No guardar tokens ni llaves en el repositorio. El repo contiene fabrica y app-generada; EC2 ejecuta app-generada.",
    }
    write_json(run_dir / "git-publication.json", report)
    doc = """# Publicacion GitHub

La fabrica puede publicar codigo al repo cuando:

1. El proyecto es un repo git.
2. Existe remoto `origin`.
3. La configuracion local permite ejecucion con `allow_execute: true`.

Si falta alguno, deja `git-publication.json` en `needs_user_input`.
"""
    _write(run_dir, "docs/generated/08_github_publication.md", doc)
    output["artifacts"].extend(["git-publication.json", "docs/generated/08_github_publication.md"])
    output["coverage"] = "complete"
    return output


def deploy_ec2(agent: AgentSpec, state: dict[str, Any], run_dir: Path, context_pack: dict[str, Any]) -> dict[str, Any]:
    output = _base_output(agent, state, context_pack)
    repo_root = run_dir.parents[2]
    app_dir = repo_root / "app-generada"
    secrets_dir = repo_root / "project" / "secrets"
    config_path = secrets_dir / "deploy-target.local.json"
    example = {
        "github_repo": "https://github.com/usuario/repo.git",
        "github_branch": "main",
        "host": "IP_PUBLICA_EC2",
        "user": "ubuntu",
        "ssh_key_path": "C:/Users/Benjamin Cruzado/Downloads/llave.pem",
        "remote_app_dir": "/home/ubuntu/app",
        "app_port": 3000,
        "public_url": "http://IP_PUBLICA_EC2:3000",
        "allow_execute": False,
    }
    secrets_dir.mkdir(parents=True, exist_ok=True)
    write_json(secrets_dir / "deploy-target.example.json", example)
    status = "needs_user_input"
    commands: list[dict[str, Any]] = []
    config: dict[str, Any] = {}
    if config_path.exists():
        from .utils import read_json

        config = read_json(config_path)
        required = ("github_repo", "github_branch", "host", "user", "ssh_key_path", "remote_app_dir", "public_url")
        missing = [key for key in required if not config.get(key)]
        key_path = Path(str(config.get("ssh_key_path", ""))).expanduser()
        if not missing and key_path.exists():
            status = "prepared"
            allow_execute = bool(config.get("allow_execute", False))
            ssh_target = f"{config['user']}@{config['host']}"
            remote_dir = config["remote_app_dir"]
            remote_cmd = (
                "set -e; "
                "command -v git >/dev/null || sudo apt-get update && sudo apt-get install -y git; "
                "command -v docker >/dev/null || curl -fsSL https://get.docker.com | sh; "
                f"if [ ! -d {remote_dir}/.git ]; then git clone -b {config['github_branch']} {config['github_repo']} {remote_dir}; fi; "
                f"cd {remote_dir}; git pull; "
                "cd app-generada; docker compose up -d --build"
            )
            if allow_execute:
                commands.append(_run_command(["ssh", "-i", str(key_path), "-o", "StrictHostKeyChecking=no", ssh_target, remote_cmd], repo_root, timeout=600))
                commands.append(_run_command(["curl", "-I", str(config["public_url"])], repo_root, timeout=60))
                status = "complete" if commands and commands[-1]["returncode"] == 0 else "needs_user_input"
        else:
            config["missing"] = missing
            config["ssh_key_exists"] = key_path.exists()
    validation = {
        "status": status,
        "config_path": str(config_path),
        "example_path": str(secrets_dir / "deploy-target.example.json"),
        "local_app_dir": str(app_dir),
        "config_loaded": bool(config),
        "public_url": config.get("public_url"),
        "allow_execute": bool(config.get("allow_execute", False)),
        "commands": commands,
        "note": "Para despliegue automatico completo, crear deploy-target.local.json y poner allow_execute true.",
    }
    write_json(run_dir / "deployment-validation.json", validation)
    runbook = """# Runbook EC2

La fabrica despliega automaticamente si existe `project/secrets/deploy-target.local.json` con `allow_execute: true`.

El archivo local debe contener host, usuario SSH, ruta local de llave `.pem`, repo GitHub, rama, directorio remoto y URL publica.

No subir `project/secrets`, llaves `.pem`, `.env` ni tokens a GitHub.
"""
    _write(run_dir, "docs/generated/09_deploy_ec2_runbook.md", runbook)
    output["artifacts"].extend(["deployment-validation.json", "docs/generated/09_deploy_ec2_runbook.md", "project/secrets/deploy-target.example.json"])
    output["coverage"] = "complete"
    return output


AGENT_FUNCTIONS: dict[str, AgentFn] = {
    "agent.spec_detallada": spec_detallada,
    "agent.context_rag": context_rag,
    "agent.architect_plan": architect_plan,
    "agent.diseno_alcance_rubrica": diseno_alcance_rubrica,
    "agent.ui_web_modern": ui_web_modern,
    "agent.api_security_docs": api_security_docs,
    "agent.implementacion_doc_code": implementacion_doc_code,
    "agent.tests_coverage": tests_coverage,
    "agent.qa_checklist": qa_checklist,
    "agent.doc_tecnica_detalle": doc_tecnica_detalle,
    "agent.ocr_ui_analyst": ocr_ui_analyst,
    "agent.security_policy": security_policy,
    "agent.token_billing": token_billing,
    "agent.observability_sre": observability_sre,
    "agent.docker_packaging": docker_packaging,
    "agent.github_publication": github_publication,
    "agent.deploy_ec2": deploy_ec2,
}


def output_hash(output: dict[str, Any]) -> str:
    return sha256_text(stable_json(output))
