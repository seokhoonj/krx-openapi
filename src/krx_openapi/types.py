"""Shared type aliases for krx-openapi.

KRX returns every field as a string (numbers included, a missing value as ``""``),
so a row is a plain ``dict[str, str]`` -- ``Row``. The client passes rows through
untouched, which is why there is no per-endpoint ``TypedDict`` here: the field set
is the vendor's, documented in :mod:`krx_openapi.catalog`, and a caller frames a
list of rows into a table in one line (``pandas.DataFrame(rows)`` /
``polars.DataFrame(rows)``) and coerces the columns they need.
"""

from __future__ import annotations

from typing import Literal

Row = dict[str, str]

# The three cash-equity markets, by their common names. The client maps these to
# KRX's internal segment codes (KOSPI->stk, KOSDAQ->ksq, KONEX->knx) when picking
# the endpoint; the name never goes on the wire.
Market = Literal["KOSPI", "KOSDAQ", "KONEX"]

# The subset that has stock futures/options: KRX lists these only for the KOSPI and
# KOSDAQ markets, never KONEX. A narrower type than Market so an unsupported KONEX is
# rejected by the type checker, not only at runtime.
StockDerivMarket = Literal["KOSPI", "KOSDAQ"]

# The seven service path codes under /svc/apis/<Category>/<api_id>.
Category = Literal["idx", "sto", "etp", "bon", "drv", "gen", "esg"]
