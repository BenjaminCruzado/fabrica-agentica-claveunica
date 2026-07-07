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
        work_order_path = input_dir / "work_order.json"
        if work_order_path.exists():
            work_order = read_json(work_order_path)
            inputs = sorted(work_order.get("inputs", []), key=lambda item: 0 if item.get("source_id") == "SRC-PROFESOR-MD" else 1)
            ordered_candidates: list[Path] = []
            for item in inputs:
                rel = item.get("path")
                if rel:
                    ordered_candidates.append((input_dir / rel).resolve())
                    ordered_candidates.append((project_dir / rel).resolve())
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

        context_dir = project_dir / "context"
        context_dir.mkdir(parents=True, exist_ok=True)
        summary = [
            "# Contexto Compacto",
            "",
            f"- source: `{source_path}`",
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
            lines = [f"# Resumen {label}", "", "IDs detectados para uso compacto de agentes.", ""]
            lines.extend(f"- {value}" for value in values)
            (context_dir / f"{prefix.lower()}_{label}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        payload = {
            "source": source_path,
            "ids": ids,
            "files": sorted(path.name for path in context_dir.glob("*")),
        }
        write_json(context_dir / "matriz_ids.json", payload)
        return payload
