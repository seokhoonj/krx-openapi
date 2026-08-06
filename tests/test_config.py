"""Config resolution -- explicit > env > file, and the failure modes."""

import json
from pathlib import Path

import pytest

from krx_openapi._config import credentials_path, resolve_api_key
from krx_openapi.errors import KRXConfigError


def _point_config_at(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("KRX_API_KEY", raising=False)
    return tmp_path / "krx-openapi" / "credentials.json"


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8")


def test_explicit_key_wins(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"KRX_API_KEY": "from-file"}))
    monkeypatch.setenv("KRX_API_KEY", "from-env")
    assert resolve_api_key("from-arg") == "from-arg"


def test_env_beats_file(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"KRX_API_KEY": "from-file"}))
    monkeypatch.setenv("KRX_API_KEY", "from-env")
    assert resolve_api_key(None) == "from-env"


def test_file_is_last_resort(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"KRX_API_KEY": "from-file"}))
    assert resolve_api_key(None) == "from-file"


def test_missing_everywhere_raises(tmp_path, monkeypatch):
    _point_config_at(tmp_path, monkeypatch)  # no file written
    with pytest.raises(KRXConfigError):
        resolve_api_key(None)


def test_whitespace_key_is_not_a_key(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"KRX_API_KEY": "   "}))
    with pytest.raises(KRXConfigError):
        resolve_api_key("   ")


def test_present_but_invalid_json_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, "{not json")
    with pytest.raises(KRXConfigError):
        resolve_api_key(None)


def test_non_object_json_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, "[1, 2, 3]")
    with pytest.raises(KRXConfigError):
        resolve_api_key(None)


def test_present_but_unreadable_raises(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write(path, json.dumps({"KRX_API_KEY": "x"}))

    def boom(self, *args, **kwargs):
        raise PermissionError("locked")

    monkeypatch.setattr(Path, "read_text", boom)  # file exists but cannot be read
    with pytest.raises(KRXConfigError):
        resolve_api_key(None)


def test_credentials_path_honors_xdg(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert credentials_path() == tmp_path / "krx-openapi" / "credentials.json"
