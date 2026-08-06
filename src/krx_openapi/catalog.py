"""The offline catalog -- every service and its field schema, no network needed.

The 31 endpoints share 19 distinct field schemas (the index-daily endpoints all
carry the same twelve fields; the three stock-trade endpoints another fifteen; and
so on). :data:`SCHEMAS` maps each schema name to its field tuple -- the vendor's own
``OutBlock_*`` field names, in order -- so a caller can see what a call returns
before making it. :func:`fields` turns a readable ``group name`` into the columns
that service returns.

``SCHEMAS`` is exposed read-only (a ``MappingProxyType`` of tuples): it is
authoritative package state, so a caller must not be able to mutate it. Every value
KRX returns is a string; these are the field *names*, not types.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType

from ._endpoint import ENDPOINTS, KRXEndpoint

# schema name -> its OutBlock field names, in the order KRX returns them.
SCHEMAS: Mapping[str, tuple[str, ...]] = MappingProxyType({
    "IDX_DAILY": (
        "BAS_DD", "IDX_CLSS", "IDX_NM", "CLSPRC_IDX", "CMPPREVDD_IDX", "FLUC_RT",
        "OPNPRC_IDX", "HGPRC_IDX", "LWPRC_IDX", "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP",
    ),
    "BOND_IDX": (
        "BAS_DD", "BND_IDX_GRP_NM", "TOT_EARNG_IDX", "TOT_EARNG_IDX_CMPPREVDD",
        "NETPRC_IDX", "NETPRC_IDX_CMPPREVDD", "ZERO_REINVST_IDX",
        "ZERO_REINVST_IDX_CMPPREVDD", "CALL_REINVST_IDX", "CALL_REINVST_IDX_CMPPREVDD",
        "MKT_PRC_IDX", "MKT_PRC_IDX_CMPPREVDD", "AVG_DURATION", "AVG_CONVEXITY_PRC",
        "BND_IDX_AVG_YD",
    ),
    "DRVPROD_IDX": (
        "BAS_DD", "IDX_CLSS", "IDX_NM", "CLSPRC_IDX", "CMPPREVDD_IDX", "FLUC_RT",
        "OPNPRC_IDX", "HGPRC_IDX", "LWPRC_IDX",
    ),
    "STOCK_TRD": (
        "BAS_DD", "ISU_CD", "ISU_NM", "MKT_NM", "SECT_TP_NM", "TDD_CLSPRC",
        "CMPPREVDD_PRC", "FLUC_RT", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC",
        "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP", "LIST_SHRS",
    ),
    "WARRANT_SW": (
        "BAS_DD", "MKT_NM", "ISU_CD", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC",
        "FLUC_RT", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL", "ACC_TRDVAL",
        "MKTCAP", "LIST_SHRS", "EXER_PRC", "EXST_STRT_DD", "EXST_END_DD",
        "TARSTK_ISU_SRT_CD", "TARSTK_ISU_NM", "TARSTK_ISU_PRSNT_PRC",
    ),
    "WARRANT_SR": (
        "BAS_DD", "MKT_NM", "ISU_CD", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC",
        "FLUC_RT", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL", "ACC_TRDVAL",
        "MKTCAP", "LIST_SHRS", "ISU_PRC", "DELIST_DD", "TARSTK_ISU_SRT_CD",
        "TARSTK_ISU_NM", "TARSTK_ISU_PRSNT_PRC",
    ),
    "ISU_BASE": (
        "ISU_CD", "ISU_SRT_CD", "ISU_NM", "ISU_ABBRV", "ISU_ENG_NM", "LIST_DD",
        "MKT_TP_NM", "SECUGRP_NM", "SECT_TP_NM", "KIND_STKCERT_TP_NM", "PARVAL",
        "LIST_SHRS",
    ),
    "ETF_TRD": (
        "BAS_DD", "ISU_CD", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC", "FLUC_RT", "NAV",
        "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP",
        "INVSTASST_NETASST_TOTAMT", "LIST_SHRS", "IDX_IND_NM", "OBJ_STKPRC_IDX",
        "CMPPREVDD_IDX", "FLUC_RT_IDX",
    ),
    "ETN_TRD": (
        "BAS_DD", "ISU_CD", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC", "FLUC_RT",
        "PER1SECU_INDIC_VAL", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL",
        "ACC_TRDVAL", "MKTCAP", "INDIC_VAL_AMT", "LIST_SHRS", "IDX_IND_NM",
        "OBJ_STKPRC_IDX", "CMPPREVDD_IDX", "FLUC_RT_IDX",
    ),
    "ELW_TRD": (
        "BAS_DD", "ISU_CD", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC", "TDD_OPNPRC",
        "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL", "ACC_TRDVAL", "MKTCAP", "LIST_SHRS",
        "ULY_NM", "ULY_PRC", "CMPPREVDD_PRC_ULY", "FLUC_RT_ULY",
    ),
    "GOVBOND_TRD": (
        "BAS_DD", "MKT_NM", "ISU_CD", "ISU_NM", "BND_EXP_TP_NM", "GOVBND_ISU_TP_NM",
        "CLSPRC", "CMPPREVDD_PRC", "CLSPRC_YD", "OPNPRC", "OPNPRC_YD", "HGPRC",
        "HGPRC_YD", "LWPRC", "LWPRC_YD", "ACC_TRDVOL", "ACC_TRDVAL",
    ),
    "BOND_TRD": (
        "BAS_DD", "MKT_NM", "ISU_CD", "ISU_NM", "CLSPRC", "CMPPREVDD_PRC", "CLSPRC_YD",
        "OPNPRC", "OPNPRC_YD", "HGPRC", "HGPRC_YD", "LWPRC", "LWPRC_YD", "ACC_TRDVOL",
        "ACC_TRDVAL",
    ),
    "FUTURES_TRD": (
        "BAS_DD", "PROD_NM", "MKT_NM", "ISU_CD", "ISU_NM", "TDD_CLSPRC",
        "CMPPREVDD_PRC", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "SPOT_PRC", "SETL_PRC",
        "ACC_TRDVOL", "ACC_TRDVAL", "ACC_OPNINT_QTY",
    ),
    "OPTION_TRD": (
        "BAS_DD", "PROD_NM", "RGHT_TP_NM", "ISU_CD", "ISU_NM", "TDD_CLSPRC",
        "CMPPREVDD_PRC", "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "IMP_VOLT",
        "NXTDD_BAS_PRC", "ACC_TRDVOL", "ACC_TRDVAL", "ACC_OPNINT_QTY",
    ),
    "OIL_TRD": (
        "BAS_DD", "OIL_NM", "WT_AVG_PRC", "WT_DIS_AVG_PRC", "ACC_TRDVOL", "ACC_TRDVAL",
    ),
    "GOLD_ETS_TRD": (
        "BAS_DD", "ISU_CD", "ISU_NM", "TDD_CLSPRC", "CMPPREVDD_PRC", "FLUC_RT",
        "TDD_OPNPRC", "TDD_HGPRC", "TDD_LWPRC", "ACC_TRDVOL", "ACC_TRDVAL",
    ),
    "ESG_ETP": (
        "BAS_DD", "ISU_ABBRV", "TDD_CLSPRC", "CMPPREVDD_PRC", "FLUC_RT", "LIST_SHRS",
        "ACC_TRDVOL", "ACC_TRDVAL",
    ),
    "SRI_BOND": (
        "BAS_DD", "ISUR_NM", "ISU_CD", "SRI_BND_TP_NM", "ISU_NM", "LIST_DD", "ISU_DD",
        "REDMPT_DD", "ISU_RT", "ISU_AMT", "LIST_AMT", "BND_TP_NM",
    ),
    "ESG_IDX": (
        "BAS_DD", "IDX_NM", "CLSPRC_IDX", "PRV_DD_CMPR", "UPDN_RATE", "TRD_ISU_CNT",
        "ACC_TRDVOL", "ACC_TRDVAL",
    ),
})


# The KRX client's accessor tree as data: group -> [(method name, representative
# api_id)]. It mirrors the KRX / _Surface accessors so the CLI can offer the same
# readable names (`krx index kospi`) instead of raw api_ids, and drive `list` /
# `fields` offline. The api_id is only used to look up a field schema, and every
# market variant of a method shares one schema, so a single representative suffices.
# (A test keeps this in step with the client.)
ACCESSORS: Mapping[str, tuple[tuple[str, str], ...]] = MappingProxyType({
    "index": (
        ("krx", "krx_dd_trd"), ("kospi", "kospi_dd_trd"), ("kosdaq", "kosdaq_dd_trd"),
        ("bond", "bon_dd_trd"), ("derivatives", "drvprod_dd_trd"),
    ),
    "stock": (
        ("info", "stk_isu_base_info"), ("daily", "stk_bydd_trd"),
        ("warrant", "sw_bydd_trd"), ("right", "sr_bydd_trd"),
    ),
    "etp": (("etf", "etf_bydd_trd"), ("etn", "etn_bydd_trd"), ("elw", "elw_bydd_trd")),
    "bond": (
        ("treasury", "kts_bydd_trd"), ("general", "bnd_bydd_trd"),
        ("small_lot", "smb_bydd_trd"),
    ),
    "derivatives": (
        ("futures", "fut_bydd_trd"), ("options", "opt_bydd_trd"),
        ("stock_futures", "eqsfu_stk_bydd_trd"), ("stock_options", "eqsop_bydd_trd"),
    ),
    "commodity": (
        ("oil", "oil_bydd_trd"), ("gold", "gold_bydd_trd"), ("emissions", "ets_bydd_trd"),
    ),
    "esg": (
        ("sri_bond", "sri_bond_info"), ("index", "esg_index_info"), ("etp", "esg_etp_info"),
    ),
})


def groups() -> list[str]:
    """The client accessor groups, in tree order (``index``, ``stock``, ...)."""
    return list(ACCESSORS)


def methods(group: str) -> list[str]:
    """The method names under one accessor group (raises ``KeyError`` if unknown)."""
    return [name for name, _ in ACCESSORS[group]]


def fields(group: str, name: str) -> list[str]:
    """The field (column) names an accessor ``group.name`` returns, in order.

        catalog.fields("index", "kospi")   # -> ["BAS_DD", "IDX_CLSS", ..., "MKTCAP"]

    Reads the bundled schema -- no network, no key. Raises ``KeyError`` for an
    unknown group or method (the same signal the client gives).
    """
    return _schema_fields(_api_id_for(group, name))


def _api_id_for(group: str, name: str) -> str:
    """Translate an accessor ``group.name`` to the KRX api_id it maps to -- the bridge
    from the readable names to the api_id-keyed schema data. Internal: users and the
    CLI go through :func:`fields`, never an api_id."""
    for method_name, api_id in ACCESSORS[group]:
        if method_name == name:
            return api_id
    raise KeyError(f"{group}.{name}")


def _schema_fields(api_id: str) -> list[str]:
    """The field names of an api_id's schema, in order. Internal: reached through
    :func:`fields` by accessor name, never by a raw api_id."""
    return list(SCHEMAS[ENDPOINTS[api_id].schema])


def endpoints() -> list[KRXEndpoint]:
    """Every KRX endpoint, in registry order."""
    return list(ENDPOINTS.values())


def schemas() -> dict[str, list[str]]:
    """A mutable copy of the schema-name -> field-list map."""
    return {name: list(fields) for name, fields in SCHEMAS.items()}


