"""Config resolution -- explicit > env > file, the header-safety guard (printable ASCII)
applied to whatever is found, and the secret-safety invariant that the key never rides
along in an error message or its cause chain."""

import json
import os

import pytest

from krx_openapi._config import resolve_api_key
from krx_openapi.errors import KRXConfigError

VALID_API_KEY = "krx-service-key-0123456789"  # a well-formed KRX key (printable ASCII)


def _point_config_at(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    monkeypatch.delenv("KRX_API_KEY", raising=False)
    return tmp_path / "krx-openapi" / "credentials.json"


def _write_credentials_file(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def _assert_secret_safe(error, secret):
    seen = set()
    pending = [error]
    while pending:
        current = pending.pop()
        if current is None or id(current) in seen:
            continue
        seen.add(id(current))
        assert secret not in str(current)
        assert secret not in repr(current)
        pending.extend([current.__cause__, current.__context__])


def test_explicit_key_wins(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, json.dumps({"KRX_API_KEY": "from-file"}))
    monkeypatch.setenv("KRX_API_KEY", "from-env")
    assert resolve_api_key("from-arg") == "from-arg"


def test_env_beats_file(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, json.dumps({"KRX_API_KEY": "from-file"}))
    monkeypatch.setenv("KRX_API_KEY", "from-env")
    assert resolve_api_key(None) == "from-env"


def test_file_is_last_resort(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, json.dumps({"KRX_API_KEY": "from-file"}))
    assert resolve_api_key(None) == "from-file"


def test_missing_everywhere_raises(tmp_path, monkeypatch):
    _point_config_at(tmp_path, monkeypatch)  # no file written
    with pytest.raises(KRXConfigError, match="no KRX API key"):
        resolve_api_key(None)


def test_blank_key_is_not_a_key(tmp_path, monkeypatch):
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, json.dumps({"KRX_API_KEY": "   "}))
    with pytest.raises(KRXConfigError, match="no KRX API key"):
        resolve_api_key("   ")


@pytest.mark.parametrize("blank_source", ["explicit", "environment"])
def test_blank_higher_tier_falls_through_to_the_file(tmp_path, monkeypatch, blank_source):
    # A blank explicit argument or env var is "absent" (credbox trims to empty), so
    # resolution falls through to the file rather than returning empty.
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, json.dumps({"KRX_API_KEY": VALID_API_KEY}))
    explicit = None
    if blank_source == "explicit":
        explicit = "   "
    else:
        monkeypatch.setenv("KRX_API_KEY", "   ")

    assert resolve_api_key(explicit) == VALID_API_KEY


@pytest.mark.parametrize("contents", ["{not json", "[1, 2, 3]", json.dumps({"KRX_API_KEY": 1})])
def test_malformed_credentials_file_is_rejected(tmp_path, monkeypatch, contents):
    # Not-JSON, a non-object, or a non-string value all reach the caller as a config
    # error rather than a silent skip -- credbox validates the store and its fault is
    # translated to KRXConfigError.
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, contents)
    with pytest.raises(KRXConfigError, match="could not read"):
        resolve_api_key(None)


def test_credentials_path_that_is_a_directory_is_rejected(tmp_path, monkeypatch):
    # A present-but-unreadable store (here a directory at the file path) is an error,
    # not a silent "no key here".
    path = _point_config_at(tmp_path, monkeypatch)
    path.mkdir(parents=True)
    with pytest.raises(KRXConfigError, match="could not read"):
        resolve_api_key(None)


@pytest.mark.parametrize("source", ["explicit", "environment", "stored"])
def test_key_is_trimmed_at_every_tier(tmp_path, monkeypatch, source):
    # credbox strips surrounding whitespace at every tier (a pasted trailing newline no
    # longer breaks auth); pinned so a future change cannot silently return padding.
    path = _point_config_at(tmp_path, monkeypatch)
    explicit = None
    if source == "explicit":
        explicit = "  " + VALID_API_KEY + "  "
    elif source == "environment":
        monkeypatch.setenv("KRX_API_KEY", "  " + VALID_API_KEY + "  ")
    else:
        _write_credentials_file(path, json.dumps({"KRX_API_KEY": "  " + VALID_API_KEY + "  "}))

    assert resolve_api_key(explicit) == VALID_API_KEY


@pytest.mark.parametrize("bad_key", ["prefix\nSECRETTAIL", "prefix한SECRETTAIL"])
def test_key_outside_printable_ascii_raises_and_never_echoes_the_key(monkeypatch, bad_key):
    # credbox trims surrounding whitespace but keeps an embedded newline or a non-ASCII
    # character; either makes an invalid HTTP header and lets urllib echo the value (in
    # whole or in part) while encoding it. Reject it as config, echoing nothing -- not in
    # the message, not anywhere in the cause chain. (The non-ASCII case would otherwise
    # leak one character + its offset through an uncaught UnicodeEncodeError in session.)
    monkeypatch.delenv("KRX_API_KEY", raising=False)
    with pytest.raises(KRXConfigError, match="cannot send as an HTTP header") as exc:
        resolve_api_key(bad_key)
    _assert_secret_safe(exc.value, "prefix")
    _assert_secret_safe(exc.value, "SECRETTAIL")
    _assert_secret_safe(exc.value, "한")


def test_store_binding_redirects_to_a_host_namespace(tmp_path, monkeypatch):
    # A host embedding krx-openapi redirects the store via KRX_OPENAPI_STORE_APP +
    # KRX_OPENAPI_NAMESPACE, so krx-openapi's key lives in the host's store under a
    # krx-openapi section.
    _point_config_at(tmp_path, monkeypatch)
    monkeypatch.setenv("KRX_OPENAPI_STORE_APP", "host")
    monkeypatch.setenv("KRX_OPENAPI_NAMESPACE", "krx")
    host = tmp_path / "host"
    host.mkdir(parents=True)
    (host / "credentials.json").write_text(
        json.dumps({"krx": {"KRX_API_KEY": VALID_API_KEY}}), encoding="utf-8")

    assert resolve_api_key(None) == VALID_API_KEY


@pytest.mark.parametrize("source", ["explicit", "environment"])
def test_higher_tier_wins_before_an_invalid_binding_is_validated(monkeypatch, source):
    # An explicit argument or KRX_API_KEY resolves before the binding is validated
    # (lazy), so a bad binding never raises when a higher tier supplies the key.
    monkeypatch.delenv("KRX_API_KEY", raising=False)
    monkeypatch.setenv("KRX_OPENAPI_STORE_APP", "../invalid")
    explicit = None
    if source == "explicit":
        explicit = VALID_API_KEY
    else:
        monkeypatch.setenv("KRX_API_KEY", VALID_API_KEY)

    assert resolve_api_key(explicit) == VALID_API_KEY


def test_invalid_store_binding_raises_config_error(monkeypatch):
    # A malformed binding surfaces as krx-openapi's KRXConfigError on first store touch.
    monkeypatch.delenv("KRX_API_KEY", raising=False)
    monkeypatch.setenv("KRX_OPENAPI_STORE_APP", "../invalid")
    with pytest.raises(KRXConfigError, match="could not read"):
        resolve_api_key(None)


@pytest.mark.parametrize(
    "contents",
    [
        lambda secret: secret.encode() + b"\xff",           # not valid UTF-8
        lambda secret: (secret + "{").encode(),             # not valid JSON
        lambda secret: json.dumps([secret]).encode(),       # a JSON array, not an object
        lambda secret: json.dumps({"KRX_API_KEY": [secret]}).encode(),  # non-string value
    ],
)
def test_malformed_store_detaches_secret_bearing_context(tmp_path, monkeypatch, contents):
    # Whatever the fault, the key bytes must not ride along in the error, its repr, or
    # the cause chain -- credbox detaches secret-bearing content and `from err` preserves
    # that, the load-bearing secret-safety invariant.
    secret = "krx-secret-value-abcdef"
    path = _point_config_at(tmp_path, monkeypatch)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(contents(secret))
    with pytest.raises(KRXConfigError, match="could not read") as caught:
        resolve_api_key(None)
    _assert_secret_safe(caught.value, secret)


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits required")
def test_loose_permission_file_warns_and_still_reads(tmp_path, monkeypatch, capsys):
    # A group/other-readable file is warned about (chmod 600 nudge), not refused.
    path = _point_config_at(tmp_path, monkeypatch)
    _write_credentials_file(path, json.dumps({"KRX_API_KEY": VALID_API_KEY}))
    path.chmod(0o644)

    assert resolve_api_key(None) == VALID_API_KEY
    assert "chmod 600" in capsys.readouterr().err
