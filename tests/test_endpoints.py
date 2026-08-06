"""The endpoint registry -- counts, URLs, and schema integrity."""

from krx_openapi._endpoint import BASE_URL, ENDPOINTS, SAMPLE_URL
from krx_openapi.catalog import SCHEMAS

_EXPECTED_PER_CATEGORY = {
    "idx": 5, "sto": 8, "etp": 3, "bon": 3, "drv": 6, "gen": 3, "esg": 3,
}


def test_registry_has_31_endpoints():
    assert len(ENDPOINTS) == 31


def test_registry_is_keyed_by_api_id():
    assert all(api_id == endpoint.api_id for api_id, endpoint in ENDPOINTS.items())


def test_category_counts():
    counts: dict[str, int] = {}
    for endpoint in ENDPOINTS.values():
        counts[endpoint.category] = counts.get(endpoint.category, 0) + 1
    assert counts == _EXPECTED_PER_CATEGORY


def test_url_is_https_json_under_svc_apis():
    endpoint = ENDPOINTS["kospi_dd_trd"]
    assert endpoint.url == f"{BASE_URL}/idx/kospi_dd_trd.json"
    assert endpoint.url.startswith("https://")


def test_sample_url_uses_the_sample_path():
    endpoint = ENDPOINTS["kospi_dd_trd"]
    assert endpoint.sample_url == f"{SAMPLE_URL}/idx/kospi_dd_trd.json"


def test_every_endpoint_schema_exists():
    for endpoint in ENDPOINTS.values():
        assert endpoint.schema in SCHEMAS, endpoint.api_id


def test_every_endpoint_has_a_name_and_start():
    for endpoint in ENDPOINTS.values():
        assert endpoint.name_ko and endpoint.start
