from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re
from typing import Any

from ..utils import ensure_inside, sha256_text


SECRET_MARKERS = (
    "OPENAI_API_KEY",
    "Authorization: Bearer",
    "BEGIN RSA PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "password=",
    "sk-proj-",
)

BLOCKED_PATH_PARTS = (
    ".git",
    "__pycache__",
    "node_modules",
    "dist",
    "target",
)

FRONTEND_INTERNAL_MARKERS = (
    "Validaciones",
    "Actividad reciente",
    "screen.records",
    "traceability",
    "trazabilidad",
)

FRONTEND_REQUIREMENT_PREFIXES = ("CU_", "FUN_", "FT_", "RN_", "CH_", "EX_", "ACT_", "REQ_")


@dataclass(frozen=True)
class FileActionResult:
    action: str
    path: str
    status: str
    reason: str
    bytes_written: int = 0
    output_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SafeFileWriter:
    def __init__(self, *, repo_root: Path, run_dir: Path, max_file_bytes: int = 120000, max_patch_bytes: int = 60000) -> None:
        self.repo_root = repo_root.resolve()
        self.run_dir = run_dir.resolve()
        self.max_file_bytes = max_file_bytes
        self.max_patch_bytes = max_patch_bytes
        self.allowed_roots = (
            (self.repo_root / "app-generada").resolve(),
            (self.run_dir / "ai-generated").resolve(),
            (self.run_dir / "docs" / "generated").resolve(),
        )

    def write_file(self, *, relative_path: str, content: str) -> FileActionResult:
        validation = self._validate(relative_path, content, check_frontend_markers=True)
        if validation.status != "complete":
            return validation
        target = (self.repo_root / relative_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return FileActionResult(
            action="write_file",
            path=relative_path,
            status="complete",
            reason="file written inside allowed factory sandbox",
            bytes_written=len(content.encode("utf-8")),
            output_hash=sha256_text(content),
        )

    def patch_file(self, *, relative_path: str, content: str) -> FileActionResult:
        if len(content.encode("utf-8")) > self.max_patch_bytes:
            return FileActionResult("patch_file", relative_path, "error", "patch content exceeds max_patch_bytes")
        validation = self._validate(relative_path, content, check_frontend_markers=False)
        if validation.status != "complete":
            return validation
        target = (self.repo_root / relative_path).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        previous = target.read_text(encoding="utf-8") if target.exists() else ""
        try:
            patch_result = self._apply_search_replace_patch(previous=previous, patch=content)
        except ValueError as exc:
            return FileActionResult("patch_file", relative_path, "error", str(exc))
        if patch_result is None:
            new_content = previous + ("\n" if previous and not previous.endswith("\n") else "") + content
            reason = "patch appended inside allowed factory sandbox"
        else:
            new_content = patch_result
            reason = "search/replace patch applied inside allowed factory sandbox"
        if len(new_content.encode("utf-8")) > self.max_file_bytes:
            return FileActionResult("patch_file", relative_path, "error", "patched file exceeds max_file_bytes")
        final_validation = self._validate(relative_path, new_content, check_frontend_markers=True)
        if final_validation.status != "complete":
            return FileActionResult("patch_file", relative_path, "error", f"patched result invalid: {final_validation.reason}")
        target.write_text(new_content, encoding="utf-8")
        return FileActionResult(
            action="patch_file",
            path=relative_path,
            status="complete",
            reason=reason,
            bytes_written=len(content.encode("utf-8")),
            output_hash=sha256_text(new_content),
        )

    def _apply_search_replace_patch(self, *, previous: str, patch: str) -> str | None:
        pattern = re.compile(r"<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE", re.DOTALL)
        matches = list(pattern.finditer(patch))
        if not matches:
            return None
        updated = previous
        for match in matches:
            before = match.group(1)
            after = match.group(2)
            if before not in updated:
                raise ValueError("search block not found in target file")
            updated = updated.replace(before, after, 1)
        return updated

    def _validate(self, relative_path: str, content: str, *, check_frontend_markers: bool) -> FileActionResult:
        if not relative_path or Path(relative_path).is_absolute():
            return FileActionResult("file_action", relative_path, "error", "path must be relative")
        normalized = relative_path.replace("\\", "/")
        lowered = normalized.lower()
        if ".." in Path(normalized).parts:
            return FileActionResult("file_action", relative_path, "error", "path traversal is not allowed")
        lowered_parts = [part.lower() for part in Path(normalized).parts]
        if any(part in BLOCKED_PATH_PARTS or part.startswith(".env") for part in lowered_parts) or "project/secrets" in lowered:
            return FileActionResult("file_action", relative_path, "error", "path targets a blocked area")
        target = (self.repo_root / relative_path).resolve()
        if not any(ensure_inside(target, root) for root in self.allowed_roots):
            return FileActionResult("file_action", relative_path, "error", "path is outside allowed write roots")
        if "\x00" in content:
            return FileActionResult("file_action", relative_path, "error", "binary-like content is not allowed")
        if len(content.encode("utf-8")) > self.max_file_bytes:
            return FileActionResult("file_action", relative_path, "error", "content exceeds max_file_bytes")
        if any(marker in content for marker in SECRET_MARKERS):
            return FileActionResult("file_action", relative_path, "error", "content contains secret-like marker")
        if check_frontend_markers and "/frontend/" in lowered:
            if any(marker.lower() in content.lower() for marker in FRONTEND_INTERNAL_MARKERS):
                return FileActionResult("file_action", relative_path, "error", "frontend content exposes internal factory markers")
            if any(prefix in content for prefix in FRONTEND_REQUIREMENT_PREFIXES):
                return FileActionResult("file_action", relative_path, "error", "frontend content exposes internal requirement ids")
        return FileActionResult("file_action", relative_path, "complete", "validated")
