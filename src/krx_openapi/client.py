"""KRX -- the entry point.

Built from an API key (constructor, ``KRX_API_KEY`` env, or config file), it holds a
:class:`KRXSession` and wires the seven category sub-surfaces -- ``index``,
``stock``, ``etp``, ``bond``, ``derivatives``, ``commodity``, ``esg`` -- whose methods
mirror the KRX service list one-to-one. Each method takes ``date`` (the
``YYYYMMDD`` trade date) and returns ``list[dict[str, str]]``, the vendor's rows with
their own field names. :meth:`KRX.get` is the escape hatch for any service by
``category`` + ``api_id``.
"""

from __future__ import annotations

from ._endpoint import ENDPOINTS
from .session import KRXSession
from .types import Market, Row, StockDerivMarket

_STOCK_TRD = {"KOSPI": "stk_bydd_trd", "KOSDAQ": "ksq_bydd_trd", "KONEX": "knx_bydd_trd"}
_STOCK_INFO = {
    "KOSPI": "stk_isu_base_info", "KOSDAQ": "ksq_isu_base_info", "KONEX": "knx_isu_base_info",
}
_STOCK_FUTURES = {"KOSPI": "eqsfu_stk_bydd_trd", "KOSDAQ": "eqkfu_ksq_bydd_trd"}
_STOCK_OPTIONS = {"KOSPI": "eqsop_bydd_trd", "KOSDAQ": "eqkop_bydd_trd"}


def _pick(mapping: dict[str, str], market: str) -> str:
    """Resolve a ``market`` against ``mapping``, case-insensitively, with a clear
    ``ValueError`` for an unknown code (a caller mistake, not a runtime failure).

    ``market`` is upper-cased first, so ``"kospi"`` and ``"KOSPI"`` both resolve;
    the type hint keeps the canonical upper-case form (:data:`Market`)."""
    try:
        return mapping[market.upper()]
    except (KeyError, AttributeError):
        raise ValueError(f"market must be one of {list(mapping)}, got {market!r}") from None


class _Surface:
    """Base for a category sub-surface: holds the session and fetches by api_id."""

    def __init__(self, session: KRXSession) -> None:
        self._session = session

    def _fetch(self, api_id: str, **params: str) -> list[Row]:
        return self._session.fetch(ENDPOINTS[api_id], **params)


class _Index(_Surface):
    """지수 (idx) -- daily index series."""

    def krx(self, date: str) -> list[Row]:
        """KRX 시리즈 일별시세정보 (idx/krx_dd_trd)."""
        return self._fetch("krx_dd_trd", basDd=date)

    def kospi(self, date: str) -> list[Row]:
        """KOSPI 시리즈 일별시세정보 (idx/kospi_dd_trd)."""
        return self._fetch("kospi_dd_trd", basDd=date)

    def kosdaq(self, date: str) -> list[Row]:
        """KOSDAQ 시리즈 일별시세정보 (idx/kosdaq_dd_trd)."""
        return self._fetch("kosdaq_dd_trd", basDd=date)

    def bond(self, date: str) -> list[Row]:
        """채권지수 시세정보 (idx/bon_dd_trd)."""
        return self._fetch("bon_dd_trd", basDd=date)

    def derivatives(self, date: str) -> list[Row]:
        """파생상품지수 시세정보 (idx/drvprod_dd_trd)."""
        return self._fetch("drvprod_dd_trd", basDd=date)


class _Stock(_Surface):
    """주식 (sto) -- daily trades and the issue master."""

    def info(self, date: str, market: Market = "KOSPI") -> list[Row]:
        """종목기본정보 (sto/{stk|ksq|knx}_isu_base_info). The issue master:
        ISU_CD/ISU_SRT_CD/ISU_NM, LIST_DD, MKT_TP_NM, SECUGRP_NM, SECT_TP_NM, PARVAL,
        LIST_SHRS. market KOSPI/KOSDAQ/KONEX."""
        return self._fetch(_pick(_STOCK_INFO, market), basDd=date)

    def daily(self, date: str, market: Market = "KOSPI") -> list[Row]:
        """일별매매정보 (sto/{stk|ksq|knx}_bydd_trd). market: KOSPI 유가증권,
        KOSDAQ 코스닥, KONEX 코넥스."""
        return self._fetch(_pick(_STOCK_TRD, market), basDd=date)

    def warrant(self, date: str) -> list[Row]:
        """신주인수권증권 일별매매정보 (sto/sw_bydd_trd)."""
        return self._fetch("sw_bydd_trd", basDd=date)

    def right(self, date: str) -> list[Row]:
        """신주인수권증서 일별매매정보 (sto/sr_bydd_trd)."""
        return self._fetch("sr_bydd_trd", basDd=date)


class _Etp(_Surface):
    """증권상품 (etp) -- ETF / ETN / ELW daily trades."""

    def etf(self, date: str) -> list[Row]:
        """ETF 일별매매정보 (etp/etf_bydd_trd). Carries each ETF's base-index name
        (IDX_IND_NM) and NAV alongside price."""
        return self._fetch("etf_bydd_trd", basDd=date)

    def etn(self, date: str) -> list[Row]:
        """ETN 일별매매정보 (etp/etn_bydd_trd)."""
        return self._fetch("etn_bydd_trd", basDd=date)

    def elw(self, date: str) -> list[Row]:
        """ELW 일별매매정보 (etp/elw_bydd_trd)."""
        return self._fetch("elw_bydd_trd", basDd=date)


class _Bond(_Surface):
    """채권 (bon) -- daily bond trades (price + yield pairs)."""

    def treasury(self, date: str) -> list[Row]:
        """국채전문유통시장 일별매매정보 (bon/kts_bydd_trd)."""
        return self._fetch("kts_bydd_trd", basDd=date)

    def general(self, date: str) -> list[Row]:
        """일반채권시장 일별매매정보 (bon/bnd_bydd_trd)."""
        return self._fetch("bnd_bydd_trd", basDd=date)

    def small_lot(self, date: str) -> list[Row]:
        """소액채권시장 일별매매정보 (bon/smb_bydd_trd)."""
        return self._fetch("smb_bydd_trd", basDd=date)


class _Derivatives(_Surface):
    """파생상품 (drv) -- futures and options daily trades."""

    def futures(self, date: str) -> list[Row]:
        """선물 일별매매정보, 주식선물 제외 (drv/fut_bydd_trd)."""
        return self._fetch("fut_bydd_trd", basDd=date)

    def options(self, date: str) -> list[Row]:
        """옵션 일별매매정보, 주식옵션 제외 (drv/opt_bydd_trd). Large response (every
        listed series) -- can take tens of seconds."""
        return self._fetch("opt_bydd_trd", basDd=date)

    def stock_futures(self, date: str, market: StockDerivMarket = "KOSPI") -> list[Row]:
        """주식선물 일별매매정보 (drv/eqsfu_stk_bydd_trd 유가, eqkfu_ksq_bydd_trd
        코스닥). market KOSPI/KOSDAQ (KONEX has no stock futures)."""
        return self._fetch(_pick(_STOCK_FUTURES, market), basDd=date)

    def stock_options(self, date: str, market: StockDerivMarket = "KOSPI") -> list[Row]:
        """주식옵션 일별매매정보 (drv/eqsop_bydd_trd 유가, eqkop_bydd_trd 코스닥).
        market KOSPI/KOSDAQ (KONEX has no stock options)."""
        return self._fetch(_pick(_STOCK_OPTIONS, market), basDd=date)


class _Commodity(_Surface):
    """일반상품 (gen) -- oil, gold, emissions daily trades."""

    def oil(self, date: str) -> list[Row]:
        """석유시장 일별매매정보 (gen/oil_bydd_trd)."""
        return self._fetch("oil_bydd_trd", basDd=date)

    def gold(self, date: str) -> list[Row]:
        """금시장 일별매매정보 (gen/gold_bydd_trd)."""
        return self._fetch("gold_bydd_trd", basDd=date)

    def emissions(self, date: str) -> list[Row]:
        """배출권 시장 일별매매정보 (gen/ets_bydd_trd)."""
        return self._fetch("ets_bydd_trd", basDd=date)


class _Esg(_Surface):
    """ESG (esg)."""

    def sri_bond(self, date: str) -> list[Row]:
        """사회책임투자채권 정보 (esg/sri_bond_info)."""
        return self._fetch("sri_bond_info", basDd=date)

    def index(self, date: str) -> list[Row]:
        """ESG 지수 (esg/esg_index_info)."""
        return self._fetch("esg_index_info", basDd=date)

    def etp(self, date: str) -> list[Row]:
        """ESG 증권상품 (esg/esg_etp_info)."""
        return self._fetch("esg_etp_info", basDd=date)


class KRX:
    """Client for the KRX Open API. Groups services as sub-surfaces.

    Construct it with an API key, or leave it out to resolve one from the
    ``KRX_API_KEY`` environment variable or ``~/.config/krx-openapi/credentials.json``::

        krx = KRX()
        rows = krx.index.kospi("20200414")
        stocks = krx.stock.daily("20200414", market="KOSPI")

    Each service is authorized separately on the KRX account; a call to one not
    applied for raises :class:`KRXAuthError` (respCode 401). Rows come back as
    ``list[dict[str, str]]`` -- frame them with ``pandas.DataFrame(rows)`` /
    ``polars.DataFrame(rows)``.
    """

    def __init__(self, api_key: str | None = None, *, timeout: float = 60.0) -> None:
        self._session = KRXSession(api_key, timeout=timeout)
        self.index = _Index(self._session)          # 지수 (idx)
        self.stock = _Stock(self._session)          # 주식 (sto)
        self.etp = _Etp(self._session)              # 증권상품 (etp)
        self.bond = _Bond(self._session)            # 채권 (bon)
        self.derivatives = _Derivatives(self._session)   # 파생상품 (drv)
        self.commodity = _Commodity(self._session)  # 일반상품 (gen)
        self.esg = _Esg(self._session)              # ESG (esg)

    def __repr__(self) -> str:
        return f"KRX({self._session!r})"
