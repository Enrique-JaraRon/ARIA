"""Tests for ARIA runtime configuration."""

from pathlib import Path

from app.app_config import (
    DATA_DIR,
    PORTFOLIOS_DIR,
    PROJECT_ROOT,
    TMP_DIR,
    ensure_runtime_directories,
    get_runtime_setting,
    relative_to_project,
    resolve_project_path,
)


def test_resolve_project_path_keeps_absolute_path(tmp_path):
    absolute_path = tmp_path / "file.csv"

    assert resolve_project_path(absolute_path) == absolute_path


def test_resolve_project_path_anchors_relative_path_to_project_root():
    resolved = resolve_project_path("data/example.csv")

    assert resolved == PROJECT_ROOT / "data" / "example.csv"


def test_relative_to_project_returns_portable_path():
    assert relative_to_project(PROJECT_ROOT / "data" / "file.csv") == "data/file.csv"


def test_ensure_runtime_directories_creates_required_folders():
    ensure_runtime_directories()

    for directory in (
        DATA_DIR,
        PORTFOLIOS_DIR,
        TMP_DIR,
    ):
        assert directory.exists()
        assert directory.is_dir()


def test_get_runtime_setting_falls_back_to_environment(monkeypatch):
    monkeypatch.setenv(
        "ARIA_TEST_SETTING",
        "local-value",
    )

    assert get_runtime_setting("ARIA_TEST_SETTING") == "local-value"


def test_runtime_paths_are_inside_project():
    for path in (
        DATA_DIR,
        PORTFOLIOS_DIR,
        TMP_DIR,
    ):
        assert Path(path).is_relative_to(PROJECT_ROOT)
