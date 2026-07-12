from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .constants import DESIGN_DOCS, EVIDENCE_FALLBACK_DOCS, INDEX_VERSION, RERANKER_VERSION, ROOT
from .utils import read_json, sha256_file, sha256_text, stable_json, utc_now, write_json


class ContextManager:
    def __init__(self, factory_root: Path = ROOT) -> None:
        self.factory_root = factory_root

    def source_manifest(self) -> list[dict[str, Any]]:
        manifest = []
        for index, rel_path in enumerate(DESIGN_DOCS, start=1):
            path = self.factory_root / rel_path
            if path.exists():
                manifest.append(
                    {
                        "source_id": f"SRC-DOC-{index:03d}",
                        "type": "doc",
                        "path": rel_path,
                        "authorized": True,
                        "hash": sha256_file(path),
                        "trust": "trusted",
                    }
                )
        if manifest:
            return manifest

        for index, rel_path in enumerate(EVIDENCE_FALLBACK_DOCS, start=1):
            path = self.factory_root / rel_path
            if path.exists():
                manifest.append(
                    {
                        "source_id": f"SRC-CODE-{index:03d}",
                        "type": "code",
                        "path": rel_path,
                        "authorized": True,
                        "hash": sha256_file(path),
                        "trust": "trusted",
                    }
                )
        return manifest

    def chunk_sources(self) -> list[dict[str, Any]]:
        chunks: list[dict[str, Any]] = []
        for source in self.source_manifest():
            text = (self.factory_root / source["path"]).read_text(encoding="utf-8")
            parts = re.split(r"(?m)^##\s+", text)
            for idx, part in enumerate(parts):
                content = part.strip()
                if not content:
                    continue
                chunk_id = f"{source['source_id']}.chunk.{idx:03d}"
                chunks.append(
                    {
                        "source_id": source["source_id"],
                        "chunk_id": chunk_id,
                        "path": source["path"],
                        "hash": sha256_text(content),
                        "score": 0.0,
                        "rerank_score": 0.0,
                        "reason_included": "TBD",
                        "content": content[:2400],
                    }
                )
        return chunks

    def retrieve(self, query: str, *, limit: int = 10, threshold: float = 0.08) -> dict[str, Any]:
        terms = {term for term in re.findall(r"[a-zA-Z0-9_]+", query.lower()) if len(term) > 2}
        ranked: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for chunk in self.chunk_sources():
            content = chunk["content"].lower()
            hits = sum(1 for term in terms if term in content)
            score = hits / max(len(terms), 1)
            rerank_score = round(score + (0.001 if "arnes" in content or "harness" in content else 0), 6)
            candidate = {**chunk, "score": round(score, 6), "rerank_score": rerank_score}
            if score >= threshold:
                candidate["reason_included"] = "coincidencia keyword deterministica con query y policy"
                ranked.append(candidate)
            else:
                excluded.append({"source_id": chunk["source_id"], "chunk_id": chunk["chunk_id"], "reason": "low_score"})

        ranked.sort(key=lambda item: (-item["rerank_score"], item["source_id"], item["chunk_id"]))
        deduped: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for item in ranked:
            key = (item["source_id"], item["hash"])
            if key in seen:
                excluded.append({"source_id": item["source_id"], "chunk_id": item["chunk_id"], "reason": "duplicate"})
                continue
            seen.add(key)
            deduped.append(item)
            if len(deduped) >= limit:
                break

        if not deduped:
            fallback = self.chunk_sources()[: min(limit, 7)]
            deduped = [{**item, "score": 0.08, "rerank_score": 0.08, "reason_included": "fallback minimo de documentos autorizados"} for item in fallback]

        corpus_hash = sha256_text(stable_json([(item["source_id"], item["hash"]) for item in self.source_manifest()]))
        query_hash = sha256_text(query)
        return {
            "context_pack_id": "CP-" + query_hash.split(":", 1)[1][:16],
            "query_hash": query_hash,
            "created_at": utc_now(),
            "index_version": INDEX_VERSION,
            "corpus_hash": corpus_hash,
            "reranker_version": RERANKER_VERSION,
            "score_threshold": threshold,
            "chunks": deduped,
            "excluded": excluded[:50],
        }

    def write_context_pack(self, run_dir: Path, query: str) -> dict[str, Any]:
        context_pack = self.retrieve(query)
        write_json(run_dir / "context-pack.json", context_pack)
        evidence = []
        for index, chunk in enumerate(context_pack["chunks"], start=1):
            evidence.append(
                {
                    "evidence_id": f"EV-{index:03d}",
                    "source_id": chunk["source_id"],
                    "chunk_id": chunk["chunk_id"],
                    "path": chunk["path"],
                    "hash": chunk["hash"],
                    "claim_supported": chunk["reason_included"],
                    "trust": "trusted",
                }
            )
        write_json(run_dir / "evidence-register.json", {"records": evidence})
        return context_pack

    def write_compact_context(self, project_dir: Path) -> dict[str, Any]:
        input_dir = project_dir / "input"
        source_candidates = [
            input_dir / "caso_claveunica.md",
        ]
        generation_policy_candidates: list[tuple[str, Path]] = []
        work_order_path = input_dir / "work_order.json"
        if work_order_path.exists():
            work_order = read_json(work_order_path)
            inputs = sorted(work_order.get("inputs", []), key=lambda item: 0 if item.get("source_id") == "SRC-PROFESOR-MD" else 1)
            ordered_candidates: list[Path] = []
            for item in inputs:
                rel = item.get("path")
                if rel:
                    resolved = self._input_path_candidates(project_dir, input_dir, rel)
                    ordered_candidates.extend(resolved)
                    if item.get("type") == "generation_policy":
                        generation_policy_candidates.extend((str(item.get("source_id") or "SRC-GENERATION-POLICY"), path) for path in resolved)
            source_candidates = ordered_candidates + source_candidates
        for root in (self.factory_root.parent, project_dir.parent):
            if root.exists():
                source_candidates.extend(sorted(root.glob("**/especificacion_requerimientos_funcionales-2.md")))
        source_candidates.append(self.factory_root / "project" / "input" / "caso_claveunica.md")
        best_text = ""
        best_path = "not_found"
        best_ids: dict[str, list[str]] = {}
        best_score = -1
        for candidate in source_candidates:
            if not candidate.exists() or not candidate.is_file():
                continue
            source_text = candidate.read_text(encoding="utf-8", errors="replace")
            candidate_ids: dict[str, list[str]] = {}
            for prefix in ("CU", "FUN", "FT", "RN", "CH", "EX", "ACT", "OBJ"):
                candidate_ids[prefix] = sorted(set(re.findall(prefix + r"_\d{3}", source_text)))
            score = sum(len(values) for values in candidate_ids.values())
            if score > best_score:
                best_text = source_text
                best_path = str(candidate)
                best_ids = candidate_ids
                best_score = score

        source_text = best_text
        source_path = best_path
        ids = best_ids
        snippets = self._semantic_snippets(source_text, ids)
        requirements_model = self._requirements_model(source_text, ids)
        generation_policy = self._generation_policy_from_candidates(generation_policy_candidates)
        if generation_policy.get("status") == "complete":
            requirements_model["generation_policy"] = generation_policy
            requirements_model["coverage_policy"] = {
                **requirements_model.get("coverage_policy", {}),
                "product_generation_policy_required": True,
                "product_generation_policy_source": generation_policy.get("source_id"),
                "frontend_must_hide_internal_generation_artifacts": True,
            }

        context_dir = project_dir / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        summary = [
            "# Contexto Compacto",
            "",
            f"- source: `{source_path}`",
            f"- generation_policy: `{generation_policy.get('source', 'not_found')}`",
            "- proposito: reducir tokens y entregar contexto operativo minimo por fase.",
            "",
            "| tipo | cantidad |",
            "|---|---:|",
        ]
        for prefix, values in ids.items():
            summary.append(f"| {prefix} | {len(values)} |")
        (context_dir / "00_resumen_operativo.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

        for prefix, values in ids.items():
            label = {
                "CU": "casos_uso",
                "FUN": "funcionalidades",
                "FT": "flujos",
                "RN": "reglas",
                "CH": "validaciones",
                "EX": "restricciones",
                "ACT": "actores",
                "OBJ": "objetivos",
            }[prefix]
            lines = [f"# Resumen {label}", "", "IDs y fragmentos semanticos detectados para uso compacto de agentes.", ""]
            for value in values:
                snippet = snippets.get(value, "")
                lines.append(f"- {value}: {snippet}" if snippet else f"- {value}")
            (context_dir / f"{prefix.lower()}_{label}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        payload = {
            "source": source_path,
            "ids": ids,
            "snippets": snippets,
            "requirements_model": requirements_model,
            "files": sorted(path.name for path in context_dir.glob("*")),
        }
        write_json(context_dir / "matriz_ids.json", payload)
        write_json(context_dir / "requirements-model.json", requirements_model)
        write_json(context_dir / "product-generation-policy.json", generation_policy)
        (context_dir / "product-generation-policy.md").write_text(self._generation_policy_markdown(generation_policy), encoding="utf-8")
        write_json(context_dir / "taint-ledger.json", self._taint_ledger(source_path, ids, requirements_model))
        return payload

    @staticmethod
    def _input_path_candidates(project_dir: Path, input_dir: Path, rel: str) -> list[Path]:
        return [
            (input_dir / rel).resolve(),
            (project_dir / rel).resolve(),
        ]

    @staticmethod
    def _generation_policy_from_candidates(candidates: list[tuple[str, Path]]) -> dict[str, Any]:
        seen: set[Path] = set()
        for source_id, path in candidates:
            if path in seen:
                continue
            seen.add(path)
            if not path.exists() or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            return ContextManager._generation_policy_from_text(text, source_id=source_id, source=str(path))
        return {
            "status": "missing",
            "source_id": "SRC-PRODUCT-GENERATION-BRIEF",
            "source": "not_found",
            "message": "No se encontro product_generation_brief.md como input autorizado.",
        }

    @staticmethod
    def _generation_policy_from_text(text: str, *, source_id: str, source: str) -> dict[str, Any]:
        return {
            "status": "complete",
            "source_id": source_id,
            "source": source,
            "hash": sha256_text(text),
            "role": "generation_contract",
            "relationship_to_functional_spec": "supplements SRC-PROFESOR-MD without replacing it",
            "required_stack": {
                "frontend": "Angular",
                "backend": "Spring Boot",
                "database": "PostgreSQL",
                "containers": "Docker Compose",
                "migrations": ["Flyway", "Liquibase"],
                "e2e": "Playwright",
                "backend_tests": ["JUnit", "equivalent"],
                "api": "REST JSON",
            },
            "forbidden_frontend_content": [
                "validaciones internas de la fabrica",
                "trazabilidad tecnica",
                "IDs de rubrica",
                "checks internos",
                "logs de agentes",
                "ejecutado desde Angular",
                "paneles de debug",
                "actividad reciente artificial",
                "texto generico de plantilla",
                "pantallas que solo listan requerimientos",
            ],
            "real_action_policy": [
                "cada boton importante debe cambiar estado visible",
                "cada boton importante debe llamar backend",
                "cada accion relevante debe leer o escribir PostgreSQL",
                "cada accion relevante debe mostrar feedback",
                "cada accion relevante debe manejar errores",
                "prohibido registrar solo actividad sin efecto de dominio",
            ],
            "required_domain_entities": [
                "ciudadanos",
                "perfil ciudadano",
                "autenticacion simulada ClaveUnica",
                "recuperacion de acceso",
                "MFA y dispositivos",
                "tramites",
                "solicitudes de tramite",
                "notificaciones",
                "mensajes",
                "domicilio digital unico",
                "datos personales",
                "datos de contacto",
                "autorizaciones de uso de datos",
                "sesiones activas",
                "auditoria interna",
            ],
            "database_requirements": [
                "tablas normalizadas",
                "claves primarias",
                "claves foraneas",
                "estados de negocio",
                "fechas de creacion y actualizacion",
                "migraciones versionadas",
                "datos semilla realistas",
                "relaciones entre entidades",
                "prohibido usar datos hardcodeados como fuente principal",
            ],
            "required_backend_behaviors": [
                "login ciudadano simulado",
                "dashboard ciudadano",
                "listar y ver tramites",
                "iniciar tramite",
                "actualizar datos personales y de contacto",
                "configurar domicilio digital",
                "listar y marcar notificaciones",
                "listar y revocar autorizaciones",
                "listar y cerrar sesiones activas",
                "listar y desactivar dispositivos MFA",
            ],
            "required_screens": [
                "Login ClaveUnica simulado",
                "Recuperacion de acceso",
                "Dashboard ciudadano",
                "Catalogo de tramites",
                "Detalle de tramite",
                "Inicio de tramite",
                "Datos personales",
                "Datos de contacto",
                "Domicilio digital",
                "Notificaciones",
                "Detalle de notificacion",
                "Autorizaciones de datos",
                "Solicitud de autorizacion",
                "Sesiones activas",
                "Dispositivos y MFA",
                "Preferencias de privacidad",
            ],
            "docker_requirements": {
                "required_services": ["frontend", "backend", "postgres"],
                "optional_services": ["redis", "pgadmin", "migration-service"],
                "single_command_local_run": True,
            },
            "required_tests": [
                "docker build correcto",
                "docker compose up correcto",
                "healthcheck backend",
                "frontend accesible",
                "login funcional",
                "navegacion principal",
                "botones con efecto real",
                "persistencia en DB",
                "endpoints principales",
                "flujos criticos con Playwright",
            ],
            "rejection_criteria": [
                "parece plantilla generica",
                "muestra validaciones internas al usuario",
                "muestra trazabilidad tecnica en la UI",
                "botones solo registran actividad",
                "no existe base de datos real",
                "no hay migraciones",
                "no hay datos semilla",
                "backend sin logica de dominio",
                "frontend usa datos hardcodeados como fuente principal",
                "docker no levanta",
                "playwright no prueba flujos reales",
                "no representa la especificacion oficial",
            ],
            "required_review_agents": [
                "UX/UI Product Reviewer",
                "Arquitecto de Software",
                "QA E2E",
                "Runtime/Docker",
                "Product Owner funcional",
                "Revisor de cumplimiento de requerimientos",
            ],
            "source_excerpt_chars": len(text),
        }

    @staticmethod
    def _generation_policy_markdown(policy: dict[str, Any]) -> str:
        lines = [
            "# Product Generation Policy",
            "",
            f"- status: `{policy.get('status')}`",
            f"- source_id: `{policy.get('source_id')}`",
            f"- source: `{policy.get('source')}`",
            "",
        ]
        if policy.get("status") != "complete":
            lines.append(str(policy.get("message", "policy unavailable")))
            return "\n".join(lines) + "\n"
        lines.extend(
            [
                "## Required Stack",
                "",
                *[f"- {key}: {value}" for key, value in policy.get("required_stack", {}).items()],
                "",
                "## Forbidden Frontend Content",
                "",
                *[f"- {item}" for item in policy.get("forbidden_frontend_content", [])],
                "",
                "## Real Action Policy",
                "",
                *[f"- {item}" for item in policy.get("real_action_policy", [])],
                "",
                "## Rejection Criteria",
                "",
                *[f"- {item}" for item in policy.get("rejection_criteria", [])],
                "",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _semantic_snippets(source_text: str, ids: dict[str, list[str]]) -> dict[str, str]:
        compact = re.sub(r"\s+", " ", source_text)
        snippets: dict[str, str] = {}
        for values in ids.values():
            for item_id in values:
                match = re.search(rf"(.{{0,80}}{re.escape(item_id)}.{{0,260}})", compact)
                if not match:
                    continue
                snippet = match.group(1).strip(" -|:;")
                snippets[item_id] = snippet[:320]
        return snippets

    @staticmethod
    def _requirements_model(source_text: str, ids: dict[str, list[str]]) -> dict[str, Any]:
        sections = []
        current = {"title": "intro", "content": []}
        for line in source_text.splitlines():
            heading = re.match(r"^(#{1,4})\s+(.+)$", line.strip())
            if heading:
                if current["content"]:
                    sections.append({"title": current["title"], "text": "\n".join(current["content"]).strip()[:1200]})
                current = {"title": heading.group(2).strip(), "content": []}
            else:
                current["content"].append(line)
        if current["content"]:
            sections.append({"title": current["title"], "text": "\n".join(current["content"]).strip()[:1200]})
        compact = source_text.lower()
        domain_terms = {
            "clave_unica": "claveunica" in compact or "clave unica" in compact or "claveunica" in compact,
            "domicilio_digital": "domicilio" in compact,
            "notificaciones": "notificacion" in compact or "notificaciones" in compact,
            "autorizaciones": "autorizacion" in compact or "consentimiento" in compact,
            "auditoria": "auditoria" in compact or "bitacora" in compact,
        }
        actors = sorted(set(re.findall(r"(?i)\b(ciudadano|usuario|administrador|funcionario|institucion|servicio)\b", source_text)))
        artifacts = []
        type_names = {
            "CU": "use_case",
            "FUN": "feature",
            "FT": "flow",
            "RN": "business_rule",
            "CH": "validation_check",
            "EX": "constraint",
            "ACT": "actor",
            "OBJ": "objective",
        }
        snippets = ContextManager._semantic_snippets(source_text, ids)
        for prefix, values in ids.items():
            for item_id in values:
                artifacts.append(
                    {
                        "id": item_id,
                        "type": type_names.get(prefix, prefix.lower()),
                        "source_id": "SRC-PROFESOR-MD",
                        "snippet": snippets.get(item_id, ""),
                        "criticality": "critical" if prefix in {"CU", "FUN", "FT", "RN", "CH"} else "supporting",
                        "ui_visibility": "internal_only",
                    }
                )
        return {
            "section_count": len(sections),
            "sections": sections[:40],
            "actors": actors,
            "ids_by_type": {key: len(value) for key, value in ids.items()},
            "requirements": artifacts,
            "coverage_policy": {
                "source_of_truth": "SRC-PROFESOR-MD",
                "traceability_required": True,
                "frontend_must_not_render_requirement_ids": True,
                "required_chain": "requirement -> screen -> action -> endpoint -> table -> test",
            },
            "domain_terms": domain_terms,
            "quality_bar": "requirements_structured_model",
        }

    @staticmethod
    def _taint_ledger(source_path: str, ids: dict[str, list[str]], requirements_model: dict[str, Any]) -> dict[str, Any]:
        records = []
        for prefix, values in ids.items():
            for item in values:
                records.append(
                    {
                        "source_id": "SRC-PROFESOR-MD" if "especificacion_requerimientos_funcionales" in source_path else "SRC-LOCAL-CONTEXT",
                        "artifact_id": item,
                        "artifact_type": prefix,
                        "trust": "trusted",
                        "taint": "clean",
                        "allowed_uses": ["scope_design", "plan", "implement", "validate"],
                        "must_cite_source": True,
                    }
                )
        return {
            "source": source_path,
            "status": "complete",
            "policy": "trusted inputs can enter planning and generation only through context packs and evidence records",
            "domain_terms": requirements_model.get("domain_terms", {}),
            "records": records,
        }
