from __future__ import annotations

import pytest

from src.config import _env_bool


def test_env_bool_accepts_common_true_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FEATURE_ENABLED", "yes")

    assert _env_bool("FEATURE_ENABLED", False) is True


def test_env_bool_uses_default_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FEATURE_ENABLED", raising=False)

    assert _env_bool("FEATURE_ENABLED", True) is True
