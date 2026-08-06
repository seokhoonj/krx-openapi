"""Live wire path against the public sample endpoint.

Skipped unless ``KRX_LIVE=1`` so CI stays hermetic and never hammers KRX (which
blocks IPs for excessive traffic). Uses the keyless sample twin -- no real
``KRX_API_KEY`` needed -- and checks the response still matches the bundled schema.
"""

import os

import pytest

from krx_openapi import catalog
from krx_openapi._endpoint import ENDPOINTS
from krx_openapi.session import KRXSession

pytestmark = pytest.mark.skipif(
    os.environ.get("KRX_LIVE") != "1",
    reason="live sample fetch: set KRX_LIVE=1 to run (hits data-dbg.krx.co.kr)",
)


def test_sample_fetch_matches_bundled_schema():
    # classmethod: no configured key needed -- it uses the public sample key
    rows = KRXSession.fetch_sample(ENDPOINTS["kospi_dd_trd"])
    assert rows, "sample endpoint returned no rows"
    assert rows[0]["BAS_DD"] == "20200414"
    # every bundled field name is actually present in the live sample row
    assert set(catalog.fields("index", "kospi")) <= set(rows[0])
