"""The offline catalog -- schemas, fields, search, and the accessor descriptor."""

import pytest

from krx_openapi import KRX, catalog
from krx_openapi._endpoint import ENDPOINTS


def test_19_distinct_schemas():
    assert len(catalog.SCHEMAS) == 19


def test_idx_daily_fields():
    fields = catalog.fields("index", "kospi")
    assert fields[0] == "BAS_DD"
    assert "MKTCAP" in fields
    assert len(fields) == 12


def test_shared_schema_is_the_same_for_all_members():
    # the KRX/KOSPI/KOSDAQ series all carry the same IDX_DAILY schema
    assert catalog.fields("index", "krx") == catalog.fields("index", "kospi")
    assert catalog.fields("index", "kospi") == catalog.fields("index", "kosdaq")


def test_fields_unknown_method_raises_keyerror():
    with pytest.raises(KeyError):
        catalog.fields("index", "nope")


def test_schemas_returns_a_copy():
    catalog.schemas()["IDX_DAILY"].append("MUTATED")
    assert "MUTATED" not in catalog.SCHEMAS["IDX_DAILY"]


def test_endpoints_are_all_31():
    assert len(catalog.endpoints()) == 31


def test_schemas_is_read_only():
    with pytest.raises(TypeError):
        catalog.SCHEMAS["NEW"] = ("x",)  # type: ignore[index]  # MappingProxyType rejects mutation


def test_endpoints_registry_is_read_only():
    with pytest.raises(TypeError):
        ENDPOINTS["nope"] = None  # type: ignore[index]


# --- the accessor descriptor stays in step with the client (drift guard) ----

def test_accessors_match_the_client_methods():
    krx = KRX(api_key="unused")
    for group in catalog.groups():
        surface = getattr(krx, group)
        public = {
            name for name in dir(surface)
            if not name.startswith("_") and callable(getattr(surface, name))
        }
        assert public == set(catalog.methods(group)), group


def test_accessor_api_ids_all_exist():
    for group in catalog.groups():
        for name, api_id in catalog.ACCESSORS[group]:
            assert api_id in ENDPOINTS, (group, name, api_id)


def test_internal_api_id_bridge_resolves_and_raises():
    assert catalog._api_id_for("index", "kospi") == "kospi_dd_trd"
    assert catalog._api_id_for("bond", "treasury") == "kts_bydd_trd"
    with pytest.raises(KeyError):
        catalog._api_id_for("index", "nope")


def test_accessors_read_only():
    with pytest.raises(TypeError):
        catalog.ACCESSORS["new"] = ()  # type: ignore[index]
