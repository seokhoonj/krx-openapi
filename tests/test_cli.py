"""CLI -- offline commands (list, fields, version) and argument validation.

The fetch path (`krx <group> <name> <date>`) needs a key and the network, so it is
exercised by the live test, not here."""

import json

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


def test_bad_group_is_usage_error():
    # argparse rejects an unknown subcommand / group with exit 2
    try:
        main(["index-typo", "kospi", "20200414"])
    except SystemExit as exit_:
        assert exit_.code == 2


def test_bad_method_is_usage_error():
    # 'name' is constrained by choices=; an unknown method exits 2
    try:
        main(["index", "not-a-method", "20200414"])
    except SystemExit as exit_:
        assert exit_.code == 2


def test_version(capsys):
    try:
        main(["--version"])
    except SystemExit as exit_:
        assert exit_.code == 0
    assert capsys.readouterr().out.startswith("krx ")
