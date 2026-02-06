"""
Aether-IDE Brain — Context-Aware Workspace Scanner

Walks the user's project directory to build a structured snapshot that is
injected into the XML Master Prompt.  The snapshot includes:

  • File tree (respecting ignore rules)
  • Manifest / dependency metadata (package.json, pubspec.yaml, etc.)
  • Targeted file contents for small, relevant source files

Design goals:
  - Fast: never reads files larger than MAX_FILE_SIZE_KB.
  - Safe: never traverses symlinks or hidden OS directories.
  - Deterministic: output is sorted alphabetically.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from config import settings


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class FileEntry:
    """Lightweight descriptor for a single file discovered during scanning."""
    relative_path: str
    size_bytes: int
    extension: str
    content: Optional[str] = None  # Populated only for small, text files


@dataclass
class ProjectContext:
    """Aggregated snapshot of the workspace."""
    root: str
    file_tree: list[str] = field(default_factory=list)
    files: list[FileEntry] = field(default_factory=list)
    manifest_content: Optional[str] = None
    manifest_name: Optional[str] = None
    language_hint: Optional[str] = None
    total_files: int = 0

    def to_xml(self) -> str:
        """Serialise the context into an XML fragment for prompt injection."""
        lines: list[str] = ['<project_context>']

        # Root & language
        lines.append(f'  <workspace root="{self.root}" language_hint="{self.language_hint or "unknown"}" />')
        lines.append(f'  <total_files>{self.total_files}</total_files>')

        # File tree
        lines.append('  <file_tree>')
        for fp in self.file_tree:
            lines.append(f'    <file>{fp}</file>')
        lines.append('  </file_tree>')

        # Manifest
        if self.manifest_content:
            lines.append(f'  <manifest name="{self.manifest_name}">')
            lines.append(f'    <![CDATA[{self.manifest_content}]]>')
            lines.append('  </manifest>')

        # Sampled file contents
        sampled = [f for f in self.files if f.content]
        if sampled:
            lines.append('  <sampled_files>')
            for f in sampled:
                lines.append(f'    <file path="{f.relative_path}">')
                lines.append(f'      <![CDATA[{f.content}]]>')
                lines.append('    </file>')
            lines.append('  </sampled_files>')

        lines.append('</project_context>')
        return '\n'.join(lines)


# ── Known manifests → language hints ─────────────────────────────────────

_MANIFESTS: dict[str, str] = {
    "package.json":    "javascript/typescript",
    "pubspec.yaml":    "dart/flutter",
    "Cargo.toml":      "rust",
    "go.mod":          "go",
    "pyproject.toml":  "python",
    "setup.py":        "python",
    "requirements.txt": "python",
    "pom.xml":         "java",
    "build.gradle":    "java/kotlin",
    "Gemfile":         "ruby",
    "composer.json":   "php",
}


# ── Scanner ──────────────────────────────────────────────────────────────

def scan_workspace(workspace_path: str) -> ProjectContext:
    """
    Walk *workspace_path* and return a ``ProjectContext`` snapshot.

    The scanner:
      1. Builds a file tree (respecting ignore rules).
      2. Detects the primary manifest and reads it.
      3. Reads small source files (≤ MAX_FILE_SIZE_KB) up to MAX_CONTEXT_FILES.
    """
    root = Path(workspace_path).resolve()
    if not root.is_dir():
        return ProjectContext(root=str(root))

    ctx = ProjectContext(root=str(root))
    file_entries: list[FileEntry] = []

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        # Prune ignored directories in-place
        dirnames[:] = sorted(
            d for d in dirnames
            if d not in settings.IGNORED_DIRS and not d.startswith(".")
        )

        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        for fname in sorted(filenames):
            if fname.startswith("."):
                continue
            ext = _ext(fname)
            if ext in settings.IGNORED_EXTENSIONS:
                continue

            rel_path = os.path.join(rel_dir, fname) if rel_dir else fname
            full_path = os.path.join(dirpath, fname)

            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue

            ctx.file_tree.append(rel_path.replace("\\", "/"))

            entry = FileEntry(
                relative_path=rel_path.replace("\\", "/"),
                size_bytes=size,
                extension=ext,
            )
            file_entries.append(entry)

    ctx.total_files = len(file_entries)

    # ── Detect manifest ──────────────────────────────────────────────
    for manifest_name, lang in _MANIFESTS.items():
        manifest_path = root / manifest_name
        if manifest_path.is_file():
            ctx.manifest_name = manifest_name
            ctx.language_hint = lang
            try:
                ctx.manifest_content = manifest_path.read_text(encoding="utf-8", errors="replace")[:8192]
            except OSError:
                pass
            break  # Use the first match (highest priority)

    # ── Read small files for context ─────────────────────────────────
    max_bytes = settings.MAX_FILE_SIZE_KB * 1024
    count = 0
    for entry in file_entries:
        if count >= settings.MAX_CONTEXT_FILES:
            break
        if entry.size_bytes > max_bytes:
            continue
        if not _is_text_extension(entry.extension):
            continue
        full = root / entry.relative_path
        try:
            entry.content = full.read_text(encoding="utf-8", errors="replace")
            count += 1
        except OSError:
            pass

    ctx.files = file_entries
    return ctx


# ── Helpers ──────────────────────────────────────────────────────────────

_TEXT_EXTS = frozenset({
    ".py", ".js", ".ts", ".tsx", ".jsx", ".dart", ".rs", ".go",
    ".java", ".kt", ".rb", ".php", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".swift", ".m", ".sql", ".sh", ".bash", ".zsh",
    ".html", ".css", ".scss", ".less", ".json", ".yaml", ".yml",
    ".toml", ".xml", ".md", ".txt", ".env", ".ini", ".cfg",
    ".graphql", ".proto", ".vue", ".svelte", ".astro",
})


def _ext(filename: str) -> str:
    """Return the lowercased file extension (e.g. '.py')."""
    _, e = os.path.splitext(filename)
    return e.lower()


def _is_text_extension(ext: str) -> bool:
    """Heuristic: is this extension likely a text/source file?"""
    return ext in _TEXT_EXTS
