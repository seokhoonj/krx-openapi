"""The KRXEndpoint value object and the registry of every KRX Open API service.

Each endpoint is data: its service path code (``category``), its ``api_id``, the
name of its field schema (:mod:`krx_openapi.catalog`), its Korean title, and the
earliest ``basDd`` for which KRX serves data. ``url`` and ``sample_url`` resolve
from those -- the wire location lives in exactly one place.

KRX also publishes a keyless *sample* twin of every endpoint: the same shape at a
fixed sample date, reachable with a public sample key -- :attr:`KRXEndpoint.sample_url`,
:data:`SAMPLE_KEY`, and :data:`SAMPLE_DATE` describe it.

``ENDPOINTS`` is exposed read-only (a ``MappingProxyType``): it is package dispatch
state that every category accessor reads, so a caller must not be able to mutate it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from .types import Category

BASE_URL = "https://data-dbg.krx.co.kr/svc/apis"
SAMPLE_URL = "https://data-dbg.krx.co.kr/svc/sample/apis"

# Published by KRX on its own API test page -- a public sample key, not a secret.
# It reaches only the sample endpoints, which always answer for SAMPLE_DATE.
SAMPLE_KEY = "74D1B99DFBF345BBA3FB4476510A4BED4C78D13A"
SAMPLE_DATE = "20200414"


@dataclass(frozen=True, slots=True)
class KRXEndpoint:
    """One KRX Open API service and where its data and spec live."""

    category: Category       # service path code: idx, sto, etp, bon, drv, gen, esg
    api_id: str              # e.g. "krx_dd_trd"
    schema: str = ""         # field-schema name, keys into krx_openapi.catalog
    name_ko: str = ""        # Korean title, e.g. "KRX 시리즈 일별시세정보"
    start: str = ""          # earliest basDd with data, e.g. "2010-01-04"

    @property
    def url(self) -> str:
        # .json makes the JSON format explicit (KRX's documented contract) and https
        # avoids the http -> https 302 that would drop the AUTH_KEY header.
        return f"{BASE_URL}/{self.category}/{self.api_id}.json"

    @property
    def sample_url(self) -> str:
        return f"{SAMPLE_URL}/{self.category}/{self.api_id}.json"


def _registry(*endpoints: KRXEndpoint) -> Mapping[str, KRXEndpoint]:
    return MappingProxyType({endpoint.api_id: endpoint for endpoint in endpoints})


# Every service, grouped by category. api_id -> KRXEndpoint. Read-only.
ENDPOINTS: Mapping[str, KRXEndpoint] = _registry(
    # -- 지수 (idx) --------------------------------------------------------
    KRXEndpoint("idx", "krx_dd_trd",     "IDX_DAILY",   "KRX 시리즈 일별시세정보",    "2010-01-04"),
    KRXEndpoint("idx", "kospi_dd_trd",   "IDX_DAILY",   "KOSPI 시리즈 일별시세정보",  "2010-01-04"),
    KRXEndpoint("idx", "kosdaq_dd_trd",  "IDX_DAILY",   "KOSDAQ 시리즈 일별시세정보", "2010-01-04"),
    KRXEndpoint("idx", "bon_dd_trd",     "BOND_IDX",    "채권지수 시세정보",          "2010-01-04"),
    KRXEndpoint("idx", "drvprod_dd_trd", "DRVPROD_IDX", "파생상품지수 시세정보",      "2010-01-04"),
    # -- 주식 (sto) --------------------------------------------------------
    KRXEndpoint("sto", "stk_bydd_trd",      "STOCK_TRD",  "유가증권 일별매매정보",       "2010-01-04"),
    KRXEndpoint("sto", "ksq_bydd_trd",      "STOCK_TRD",  "코스닥 일별매매정보",         "2010-01-04"),
    KRXEndpoint("sto", "knx_bydd_trd",      "STOCK_TRD",  "코넥스 일별매매정보",         "2013-07-01"),
    KRXEndpoint("sto", "sw_bydd_trd",       "WARRANT_SW", "신주인수권증권 일별매매정보", "2010-01-04"),
    KRXEndpoint("sto", "sr_bydd_trd",       "WARRANT_SR", "신주인수권증서 일별매매정보", "2010-02-12"),
    KRXEndpoint("sto", "stk_isu_base_info", "ISU_BASE",   "유가증권 종목기본정보",       "2010-01-04"),
    KRXEndpoint("sto", "ksq_isu_base_info", "ISU_BASE",   "코스닥 종목기본정보",         "2010-01-04"),
    KRXEndpoint("sto", "knx_isu_base_info", "ISU_BASE",   "코넥스 종목기본정보",         "2013-07-01"),
    # -- 증권상품 (etp) ----------------------------------------------------
    KRXEndpoint("etp", "etf_bydd_trd", "ETF_TRD", "ETF 일별매매정보", "2010-01-04"),
    KRXEndpoint("etp", "etn_bydd_trd", "ETN_TRD", "ETN 일별매매정보", "2014-11-17"),
    KRXEndpoint("etp", "elw_bydd_trd", "ELW_TRD", "ELW 일별매매정보", "2010-01-04"),
    # -- 채권 (bon) --------------------------------------------------------
    KRXEndpoint("bon", "kts_bydd_trd", "GOVBOND_TRD", "국채전문유통시장 일별매매정보", "2010-01-04"),
    KRXEndpoint("bon", "bnd_bydd_trd", "BOND_TRD",    "일반채권시장 일별매매정보",     "2010-01-04"),
    KRXEndpoint("bon", "smb_bydd_trd", "BOND_TRD",    "소액채권시장 일별매매정보",     "2010-01-04"),
    # -- 파생상품 (drv) ----------------------------------------------------
    KRXEndpoint("drv", "fut_bydd_trd",        "FUTURES_TRD", "선물 일별매매정보 (주식선물外)", "2010-01-04"),
    KRXEndpoint("drv", "eqsfu_stk_bydd_trd",  "FUTURES_TRD", "주식선물(유가) 일별매매정보",    "2010-01-04"),
    KRXEndpoint("drv", "eqkfu_ksq_bydd_trd",  "FUTURES_TRD", "주식선물(코스닥) 일별매매정보",  "2015-08-03"),
    KRXEndpoint("drv", "opt_bydd_trd",        "OPTION_TRD",  "옵션 일별매매정보 (주식옵션外)", "2010-01-04"),
    KRXEndpoint("drv", "eqsop_bydd_trd",      "OPTION_TRD",  "주식옵션(유가) 일별매매정보",    "2010-01-04"),
    KRXEndpoint("drv", "eqkop_bydd_trd",      "OPTION_TRD",  "주식옵션(코스닥) 일별매매정보",  "2017-06-26"),
    # -- 일반상품 (gen) ----------------------------------------------------
    KRXEndpoint("gen", "oil_bydd_trd",  "OIL_TRD",      "석유시장 일별매매정보",   "2012-03-30"),
    KRXEndpoint("gen", "gold_bydd_trd", "GOLD_ETS_TRD", "금시장 일별매매정보",     "2014-03-24"),
    KRXEndpoint("gen", "ets_bydd_trd",  "GOLD_ETS_TRD", "배출권 시장 일별매매정보", "2015-01-12"),
    # -- ESG (esg) ---------------------------------------------------------
    KRXEndpoint("esg", "sri_bond_info",  "SRI_BOND", "사회책임투자채권 정보", "2019-01-01"),
    KRXEndpoint("esg", "esg_index_info", "ESG_IDX",  "ESG 지수",              "2020-01-02"),
    KRXEndpoint("esg", "esg_etp_info",   "ESG_ETP",  "ESG 증권상품",          "2020-01-02"),
)
