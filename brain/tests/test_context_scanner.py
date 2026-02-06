"""
Tests for the Context Scanner module.

Validates workspace scanning, file tree building, and manifest detection.
"""

from __future__ import annotations

import os
import tempfile
import pytest
from context_scanner import scan_workspace, ProjectContext


class TestScanWorkspace:
    """Test workspace scanning functionality."""

    def test_nonexistent_path_returns_empty_context(self) -> None:
        ctx = scan_workspace("/nonexistent/path/that/does/not/exist")
        assert ctx.total_files == 0
        assert len(ctx.file_tree) == 0

    def test_empty_directory(self, tmp_path) -> None:
        ctx = scan_workspace(str(tmp_path))
        assert ctx.total_files == 0
        assert ctx.root == str(tmp_path)

    def test_detects_python_project(self, tmp_path) -> None:
        (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (tmp_path / "main.py").write_text("print('hello')")
        ctx = scan_workspace(str(tmp_path))
        assert ctx.language_hint == "python"
        assert ctx.manifest_name == "requirements.txt"

    def test_detects_node_project(self, tmp_path) -> None:
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "index.js").write_text("console.log('hi')")
        ctx = scan_workspace(str(tmp_path))
        assert ctx.language_hint == "javascript/typescript"
        assert ctx.manifest_name == "package.json"

    def test_ignores_node_modules(self, tmp_path) -> None:
        nm = tmp_path / "node_modules" / "pkg"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("module.exports = {}")
        (tmp_path / "app.js").write_text("const x = 1;")
        ctx = scan_workspace(str(tmp_path))
        assert not any("node_modules" in f for f in ctx.file_tree)

    def test_ignores_hidden_files(self, tmp_path) -> None:
        (tmp_path / ".secret").write_text("hidden")
        (tmp_path / "visible.txt").write_text("public")
        ctx = scan_workspace(str(tmp_path))
        assert not any(".secret" in f for f in ctx.file_tree)
        assert any("visible.txt" in f for f in ctx.file_tree)

    def test_respects_max_file_size(self, tmp_path) -> None:
        # Create a file larger than MAX_FILE_SIZE_KB (32KB default)
        large = tmp_path / "large.py"
        large.write_text("x = 1\n" * 10000)  # ~60KB
        small = tmp_path / "small.py"
        small.write_text("y = 2\n")
        ctx = scan_workspace(str(tmp_path))
        # large file should be in tree but not have content
        large_entry = next((f for f in ctx.files if "large.py" in f.relative_path), None)
        assert large_entry is not None
        assert large_entry.content is None

    def test_reads_small_files(self, tmp_path) -> None:
        (tmp_path / "hello.py").write_text("print('hello')")
        ctx = scan_workspace(str(tmp_path))
        entry = next((f for f in ctx.files if "hello.py" in f.relative_path), None)
        assert entry is not None
        assert entry.content == "print('hello')"


class TestProjectContextXml:
    """Test XML serialization of project context."""

    def test_xml_contains_root(self) -> None:
        ctx = ProjectContext(root="/test", total_files=0)
        xml = ctx.to_xml()
        assert "<project_context>" in xml
        assert "</project_context>" in xml

    def test_xml_contains_manifest(self) -> None:
        ctx = ProjectContext(
            root="/test",
            manifest_name="package.json",
            manifest_content='{"name": "test"}',
            total_files=0,
        )
        xml = ctx.to_xml()
        assert "package.json" in xml
        assert "CDATA" in xml
