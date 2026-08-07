"""CLI -- offline commands (list, fields, version), argument validation, and the
fetch dispatch path with the client faked so no key or network is needed."""

import json

import pytest

from krx_openapi.cli import main


def test_list_all_groups(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "index kospi" in out
    assert "stock daily" in out
    assert "bond treasury" in out


def test_list_one_group(capsys):
    assert main(["list", "stock"]) == 0
    out = capsys.readouterr().out
    assert "stock info" in out and "stock daily" in out
    assert "index kospi" not in out


def test_list_json(capsys):
    assert main(["list", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["index"][1] == "kospi"           # (order: krx, kospi, ...)
    assert set(data) == {"index", "stock", "etp", "bond", "derivatives", "commodity", "esg"}


def test_fields_shows_schema(capsys):
    assert main(["fields", "index", "kospi"]) == 0
    out = capsys.readouterr().out
    assert "BAS_DD" in out and "MKTCAP" in out


def test_fields_unknown_method_is_usage_error(capsys):
    assert main(["fields", "index", "nope"]) == 2
    assert "unknown service" in capsys.readouterr().err


def test_bad_command_is_usage_error():
    # argparse rejects an unknown subcommand (not list/fields/fetch) with exit 2
    try:
        main(["frobnicate"])
    except SystemExit as exit_:
        assert exit_.code == 2


def test_fetch_bad_group_is_usage_error():
    # 'group' is constrained by choices=; an unknown group exits 2
    try:
        main(["fetch", "index-typo", "kospi", "20200414"])
    except SystemExit as exit_:
        assert exit_.code == 2


def test_fetch_unknown_method_is_usage_error(monkeypatch, capsys):
    # The method is validated in _run_fetch against the group, BEFORE KRX() is built --
    # so an unknown method exits 2 without a key. Prove it never constructs the client.
    def boom(*a, **k):
        raise AssertionError("KRX must not be constructed for an unknown method")

    monkeypatch.setattr("krx_openapi.cli.KRX", boom)
    assert main(["fetch", "index", "not-a-method", "20200414"]) == 2
    assert "unknown service" in capsys.readouterr().err


def test_fetch_valid_service_without_a_key_is_error_exit_1(monkeypatch, capsys):
    # A valid service but no key: KRX() raises KRXConfigError, which main() reports as a
    # one-line message and exit 1 (an operational failure, not a usage error).
    monkeypatch.delenv("KRX_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", "/nonexistent-krx-config")
    assert main(["fetch", "index", "kospi", "20200414"]) == 1
    assert "no KRX API key" in capsys.readouterr().err


def test_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exit_:
        assert exit_.code == 0
    assert capsys.readouterr().out.startswith("krx ")


# --- the fetch dispatch path (client faked: no key, no network) --------------

class _RecordingSurface:
    def __init__(self, group, log):
        self._group, self._log = group, log

    def __getattr__(self, name):
        def call(date, market=None):
            self._log.append((self._group, name, date, market))
            return [{"BAS_DD": date, "COL": "v"}]
        return call


class _FakeKRX:
    def __init__(self, *args, **kwargs):
        self.log: list[tuple[str, str, str, str | None]] = []
        for group in ("index", "stock", "etp", "bond", "derivatives", "commodity", "esg"):
            setattr(self, group, _RecordingSurface(group, self.log))


@pytest.fixture
def fake_krx(monkeypatch):
    fake = _FakeKRX()
    monkeypatch.setattr("krx_openapi.cli.KRX", lambda *a, **k: fake)
    return fake


def test_fetch_dispatches_to_the_named_accessor(fake_krx, capsys):
    assert main(["fetch", "index", "kospi", "20200414"]) == 0
    assert fake_krx.log == [("index", "kospi", "20200414", None)]
    assert "BAS_DD" in capsys.readouterr().out


def test_fetch_forwards_market(fake_krx, capsys):
    assert main(["fetch", "stock", "daily", "20200414", "--market", "kosdaq"]) == 0
    assert fake_krx.log == [("stock", "daily", "20200414", "kosdaq")]


def test_fetch_json_emits_all_rows(fake_krx, capsys):
    assert main(["fetch", "bond", "treasury", "20200414", "--json"]) == 0
    assert json.loads(capsys.readouterr().out) == [{"BAS_DD": "20200414", "COL": "v"}]


def test_market_on_method_without_it_is_usage_error(monkeypatch, capsys):
    # index.kospi takes no market; --market on it is a usage error (exit 2), detected
    # offline BEFORE KRX() -- so it needs no key. Prove the client is never constructed.
    def boom(*a, **k):
        raise AssertionError("KRX must not be constructed to reject a stray --market")

    monkeypatch.setattr("krx_openapi.cli.KRX", boom)
    assert main(["fetch", "index", "kospi", "20200414", "--market", "KOSPI"]) == 2
    assert "takes no --market" in capsys.readouterr().err


def test_unknown_market_value_is_usage_error(monkeypatch, capsys):
    # A bad --market VALUE on a market-capable service reaches the client's _pick, which
    # raises ValueError; the CLI turns that into exit 2, not a traceback. This one needs
    # the client (value validation lives there), so a key is set; nothing hits the network.
    monkeypatch.setenv("KRX_API_KEY", "unused")
    assert main(["fetch", "stock", "daily", "20200414", "--market", "XYZ"]) == 2
    assert "market must be one of" in capsys.readouterr().err
