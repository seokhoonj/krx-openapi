"""The status contract in _rows_from_body (pure) and _get (offline opener fake)."""

import http.client
import io
import json
import urllib.error
import urllib.request
from email.message import Message

import pytest

from krx_openapi._endpoint import ENDPOINTS
from krx_openapi.errors import (
    KRXAuthError,
    KRXNetworkError,
    KRXRateLimitError,
    KRXResponseError,
)
from krx_openapi.session import KRXSession, _rows_from_body


def _body(payload):
    return json.dumps(payload).encode("utf-8")


# --- _rows_from_body (pure) -------------------------------------------------

def test_extracts_the_outblock_array():
    rows = _rows_from_body(
        _body({"OutBlock_1": [{"BAS_DD": "20200414"}, {"BAS_DD": "20200414"}]}),
        "http://x")
    assert rows == [{"BAS_DD": "20200414"}, {"BAS_DD": "20200414"}]


def test_empty_outblock_is_empty_list():
    # a no-data date: KRX still returns the OutBlock, just empty
    assert _rows_from_body(_body({"OutBlock_1": []}), "http://x") == []


def test_no_outblock_array_raises():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(_body({"other": "1"}), "http://x")


def test_multiple_outblock_arrays_raise():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(_body({"OutBlock_1": [], "OutBlock_2": []}), "http://x")


def test_respcode_401_raises_auth_error():
    with pytest.raises(KRXAuthError):
        _rows_from_body(_body({"respCode": "401", "respMsg": "not applied"}), "http://x")


def test_respcode_other_raises_response_error():
    with pytest.raises(KRXResponseError):
        _rows_from_body(_body({"respCode": "500", "respMsg": "boom"}), "http://x")


def test_non_json_raises_network_error():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(b"<html>maintenance</html>", "http://x")


def test_invalid_utf8_raises_network_error():
    # json.loads on non-UTF-8 bytes raises UnicodeDecodeError, not JSONDecodeError
    with pytest.raises(KRXNetworkError):
        _rows_from_body(b"\xff\xfe not utf-8", "http://x")


def test_non_object_json_raises_network_error():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(b"[1, 2, 3]", "http://x")


def test_non_dict_row_raises():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(_body({"OutBlock_1": [{"a": "1"}, "junk"]}), "http://x")


# --- _get (offline opener fake) ---------------------------------------------

class _FakeResponse:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._raw


class _ReadFailsResponse(_FakeResponse):
    def read(self) -> bytes:
        raise http.client.IncompleteRead(b"partial")


def _patch_urlopen(monkeypatch, handler):
    monkeypatch.setattr(urllib.request, "urlopen", handler)


def _http_error(code):
    def urlopen(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, code, "msg", Message(), io.BytesIO(b""))
    return urlopen


def test_get_success_sends_key_header_and_returns_rows(monkeypatch):
    captured = {}

    def urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["key"] = request.get_header("Auth_key")
        return _FakeResponse(_body({"OutBlock_1": [{"BAS_DD": "20200414"}]}))

    _patch_urlopen(monkeypatch, urlopen)
    rows = KRXSession(api_key="SECRETKEY123").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")
    assert rows == [{"BAS_DD": "20200414"}]
    assert captured["key"] == "SECRETKEY123"       # AUTH_KEY header carried the key
    assert "basDd=20200414" in captured["url"]      # query built from params


def test_get_429_raises_rate_limit(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(429))
    with pytest.raises(KRXRateLimitError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


def test_get_403_gives_hint(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(403))
    with pytest.raises(KRXNetworkError) as exc:
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")
    assert "/svc/apis" in str(exc.value)            # the 403 hint is present


def test_get_other_http_status_raises_network(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(500))
    with pytest.raises(KRXNetworkError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


def test_get_urlerror_raises_network(monkeypatch):
    def urlopen(request, timeout=None):
        raise urllib.error.URLError("name resolution failed")
    _patch_urlopen(monkeypatch, urlopen)
    with pytest.raises(KRXNetworkError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


def test_get_read_failure_raises_network(monkeypatch):
    _patch_urlopen(monkeypatch, lambda request, timeout=None: _ReadFailsResponse(b""))
    with pytest.raises(KRXNetworkError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


# --- the secret never appears (Package Boundary Ch. 12) ---------------------

def test_repr_never_shows_the_key():
    assert "SECRETKEY123" not in repr(KRXSession(api_key="SECRETKEY123"))


def test_error_message_never_shows_the_key(monkeypatch):
    _patch_urlopen(monkeypatch, _http_error(403))
    with pytest.raises(KRXNetworkError) as exc:
        KRXSession(api_key="SECRETKEY123").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")
    assert "SECRETKEY123" not in str(exc.value)
    assert "SECRETKEY123" not in str(exc.value.__cause__)
