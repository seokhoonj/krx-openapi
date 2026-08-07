"""The status contract in _rows_from_body (pure) and _get (offline opener fake)."""

import http.client
import io
import json
import threading
import urllib.error
import urllib.request
from email.message import Message
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from krx_openapi import session as session_mod
from krx_openapi._endpoint import ENDPOINTS
from krx_openapi.errors import (
    KRXAuthError,
    KRXNetworkError,
    KRXRateLimitError,
    KRXResponseError,
)
from krx_openapi.session import KRXSession, _NoRedirect, _rows_from_body


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


def test_outblock_prefix_requires_the_underscore():
    # The block key must be OutBlock_<n>. A bare "OutBlock" is not a data array, so a
    # body carrying only that is no recognized block -> raises.
    with pytest.raises(KRXNetworkError):
        _rows_from_body(_body({"OutBlock": []}), "http://x")
    # A near-prefix like "OutBlockMeta" must be ignored, not mistaken for a second data
    # block: with the real OutBlock_1 present, exactly one block is found and returned.
    # (Under the looser startswith("OutBlock") this would be two blocks and would raise,
    # so this pins the underscore.)
    rows = _rows_from_body(_body({"OutBlockMeta": [], "OutBlock_1": [{"a": "1"}]}), "http://x")
    assert rows == [{"a": "1"}]


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


def test_valid_utf16_json_raises_network_error():
    # Well-formed JSON, but UTF-16: json.loads(bytes) would auto-detect and accept it;
    # the contract is UTF-8 only, so decoding explicitly must reject it.
    with pytest.raises(KRXNetworkError):
        _rows_from_body('{"OutBlock_1": []}'.encode("utf-16"), "http://x")


def test_non_object_json_raises_network_error():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(b"[1, 2, 3]", "http://x")


def test_deeply_nested_json_raises_network_error():
    # A body nested deep enough to blow json's recursion limit must surface as our error,
    # not a raw RecursionError.
    depth = 100_000
    raw = ("[" * depth + "]" * depth).encode("utf-8")
    with pytest.raises(KRXNetworkError):
        _rows_from_body(raw, "http://x")


def test_non_dict_row_raises():
    with pytest.raises(KRXNetworkError):
        _rows_from_body(_body({"OutBlock_1": [{"a": "1"}, "junk"]}), "http://x")


# --- _get (offline opener fake) ---------------------------------------------

class _FakeResponse:
    def __init__(self, raw: bytes) -> None:
        self._raw = raw
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.closed = True       # the `with` in _get must release the response
        return False

    def read(self) -> bytes:
        return self._raw


class _ReadFailsResponse(_FakeResponse):
    def read(self) -> bytes:
        raise http.client.IncompleteRead(b"partial")


def _patch_opener(monkeypatch, handler):
    # _get goes through the package's private no-redirect opener, not the global
    # urllib.request.urlopen, so that is what the fakes must replace.
    monkeypatch.setattr(session_mod._OPENER, "open", handler)


def _http_error(code):
    def opener(request, timeout=None):
        raise urllib.error.HTTPError(request.full_url, code, "msg", Message(), io.BytesIO(b""))
    return opener


def test_get_success_sends_key_header_and_returns_rows(monkeypatch):
    captured = {}
    response = _FakeResponse(_body({"OutBlock_1": [{"BAS_DD": "20200414"}]}))

    def opener(request, timeout=None):
        captured["url"] = request.full_url
        captured["key"] = request.get_header("Auth_key")
        return response

    _patch_opener(monkeypatch, opener)
    rows = KRXSession(api_key="SECRETKEY123").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")
    assert rows == [{"BAS_DD": "20200414"}]
    assert captured["key"] == "SECRETKEY123"       # AUTH_KEY header carried the key
    assert "basDd=20200414" in captured["url"]      # query built from params
    assert response.closed                          # the response socket was released


def test_get_429_raises_rate_limit(monkeypatch):
    _patch_opener(monkeypatch, _http_error(429))
    with pytest.raises(KRXRateLimitError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


def test_get_403_gives_hint(monkeypatch):
    _patch_opener(monkeypatch, _http_error(403))
    with pytest.raises(KRXNetworkError) as exc:
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")
    assert "/svc/apis" in str(exc.value)            # the 403 hint is present


def test_get_other_http_status_raises_network(monkeypatch):
    _patch_opener(monkeypatch, _http_error(500))
    with pytest.raises(KRXNetworkError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


def test_get_urlerror_raises_network(monkeypatch):
    def opener(request, timeout=None):
        raise urllib.error.URLError("name resolution failed")
    _patch_opener(monkeypatch, opener)
    with pytest.raises(KRXNetworkError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


def test_get_read_failure_raises_network(monkeypatch):
    _patch_opener(monkeypatch, lambda request, timeout=None: _ReadFailsResponse(b""))
    with pytest.raises(KRXNetworkError):
        KRXSession(api_key="k").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")


# --- redirects must never carry the key -------------------------------------

def test_no_redirect_handler_refuses_and_never_follows():
    # The handler turns a 3xx into an HTTPError instead of following it, so urllib
    # never issues the second request that would copy the AUTH_KEY header onward.
    with pytest.raises(urllib.error.HTTPError):
        _NoRedirect().redirect_request(
            urllib.request.Request("https://data-dbg.krx.co.kr/svc/apis/idx/kospi_dd_trd.json"),
            io.BytesIO(b""), 302, "Found", Message(), "http://evil.example/leak")


def test_get_against_a_redirecting_server_does_not_leak_the_key():
    received = {}

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/leak"):
                received["key"] = self.headers.get("AUTH_KEY")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"OutBlock_1": []}')
            else:
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{port}/leak")
                self.end_headers()

    with HTTPServer(("127.0.0.1", 0), _Handler) as server:   # `with` closes the socket
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            session = KRXSession(api_key="SECRETKEY123")
            with pytest.raises(KRXNetworkError):    # the refused redirect surfaces as ours
                session._get(f"http://127.0.0.1:{port}/start", "SECRETKEY123",
                             {"basDd": "20200414"})
        finally:
            server.shutdown()
            thread.join()
    assert "key" not in received                    # the redirect target never saw the key


# --- the secret never appears -----------------------------------------------

def test_repr_never_shows_the_key():
    assert "SECRETKEY123" not in repr(KRXSession(api_key="SECRETKEY123"))


def test_error_message_never_shows_the_key(monkeypatch):
    _patch_opener(monkeypatch, _http_error(403))
    with pytest.raises(KRXNetworkError) as exc:
        KRXSession(api_key="SECRETKEY123").fetch(ENDPOINTS["kospi_dd_trd"], basDd="20200414")
    assert "SECRETKEY123" not in str(exc.value)
    assert "SECRETKEY123" not in str(exc.value.__cause__)
