"""krx-openapi -- read daily market data from the KRX Open API.

    from krx_openapi import KRX

    krx = KRX()                              # or set KRX_API_KEY
    rows = krx.index.kospi("20200414")       # KOSPI series, one day
    stocks = krx.stock.daily("20200414", market="KOSPI")

Reads the KRX Open API: indices, stocks and
the issue master, ETF/ETN/ELW, bonds, futures/options, oil/gold/emissions, and ESG.
Returns raw ``list[dict]`` with the vendor's own field names -- frame it your own
way, e.g. ``pandas.DataFrame(rows)`` or ``polars.DataFrame(rows)``. The offline
:mod:`krx_openapi.catalog` describes every service and its fields without a call.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from . import catalog
from ._endpoint import ENDPOINTS, KRXEndpoint
from .client import KRX
from .errors import (
    KRXAuthError,
    KRXConfigError,
    KRXError,
    KRXNetworkError,
    KRXRateLimitError,
    KRXResponseError,
)
from .session import KRXSession
from .types import Category, Market, Row, StockDerivMarket

try:
    __version__ = version("krx-openapi")   # single source of truth: pyproject.toml
except PackageNotFoundError:               # running from source without an install
    __version__ = "0.0.0+unknown"

__all__ = [
    "ENDPOINTS",
    "KRX",
    "Category",
    "KRXAuthError",
    "KRXConfigError",
    "KRXEndpoint",
    "KRXError",
    "KRXNetworkError",
    "KRXRateLimitError",
    "KRXResponseError",
    "KRXSession",
    "Market",
    "Row",
    "StockDerivMarket",
    "catalog",
]
