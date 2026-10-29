"""Synthetic credential tests isolated from the developer's real .env."""

import os
from pathlib import Path

import pytest

from receipttrace.credentials import api_key


def isolate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_reads_local_file_without_mutating_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolate(tmp_path, monkeypatch)
    (tmp_path / ".env").write_text('GEMINI_API_KEY="synthetic-value"\n', encoding="utf-8-sig")
    assert api_key("GEMINI_API_KEY") == "synthetic-value"
    assert "GEMINI_API_KEY" not in os.environ


def test_process_environment_has_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolate(tmp_path, monkeypatch)
    (tmp_path / ".env").write_text("GEMINI_API_KEY=synthetic-file-value")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-environment-value")
    assert api_key("GEMINI_API_KEY") == "synthetic-environment-value"


def test_does_not_expand_variable_references(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolate(tmp_path, monkeypatch)
    monkeypatch.setenv("OTHER_SECRET", "must-not-be-read")
    (tmp_path / ".env").write_text("GEMINI_API_KEY=synthetic-${OTHER_SECRET}")
    assert api_key("GEMINI_API_KEY") == "synthetic-${OTHER_SECRET}"


def test_does_not_search_parent_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / ".env").write_text("GEMINI_API_KEY=synthetic-parent-value")
    child = tmp_path / "child"
    child.mkdir()
    isolate(child, monkeypatch)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        api_key("GEMINI_API_KEY")


def test_missing_key_error_does_not_reveal_other_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    isolate(tmp_path, monkeypatch)
    (tmp_path / ".env").write_text("OTHER_KEY=synthetic-private-value\nGEMINI_API_KEY=\n")
    with pytest.raises(ValueError) as error:
        api_key("GEMINI_API_KEY")
    assert "synthetic-private-value" not in str(error.value)


def test_rejects_other_credential_names() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        api_key("OTHER_KEY")
