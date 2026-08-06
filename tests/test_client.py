"""Client wiring -- accessors map to the right api_id, market pick, case-folding.

No network: the session's fetch is monkeypatched to record which endpoint each
accessor asks for.
"""

import pytest

from krx_openapi import KRX


def _recording_krx(monkeypatch):
    """A KRX whose session records (category, api_id, params) instead of fetching."""
    krx = KRX(api_key="unused")
    calls = []

    def fetch(endpoint, **params):
        calls.append((endpoint.category, endpoint.api_id, params))
        return [{"ok": "1"}]

    monkeypatch.setattr(krx._session, "fetch", fetch)
    return krx, calls


def test_index_accessor_maps_to_api_id(monkeypatch):
    krx, calls = _recording_krx(monkeypatch)
    assert krx.index.kospi("20200414") == [{"ok": "1"}]
    assert calls == [("idx", "kospi_dd_trd", {"basDd": "20200414"})]


def test_stock_daily_market_pick(monkeypatch):
    krx, calls = _recording_krx(monkeypatch)
    krx.stock.daily("20200414", market="KOSDAQ")
    assert calls[0][1] == "ksq_bydd_trd"


def test_stock_daily_default_market_is_kospi(monkeypatch):
    krx, calls = _recording_krx(monkeypatch)
    krx.stock.daily("20200414")
    assert calls[0][1] == "stk_bydd_trd"


def test_market_is_case_insensitive(monkeypatch):
    krx, calls = _recording_krx(monkeypatch)
    krx.stock.daily("20200414", market="kospi")
    krx.stock.daily("20200414", market="Kosdaq")
    assert [c[1] for c in calls] == ["stk_bydd_trd", "ksq_bydd_trd"]


def test_bad_market_raises_valueerror():
    with pytest.raises(ValueError):
        KRX(api_key="unused").stock.daily("20200414", market="XXX")  # type: ignore[arg-type]


def test_stock_futures_rejects_knx_at_runtime():
    # KONEX is not in StockDerivMarket, so this is also a static type error; the runtime
    # guard (_pick -> ValueError) is what the test asserts.
    with pytest.raises(ValueError):
        KRX(api_key="unused").derivatives.stock_futures("20200414", market="KONEX")  # type: ignore[arg-type]


def test_repr_never_shows_the_key():
    assert "secret-key-1234" not in repr(KRX(api_key="secret-key-1234"))
