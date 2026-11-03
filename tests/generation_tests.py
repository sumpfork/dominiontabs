from __future__ import print_function

import pytest

from domdiv import config_options, db, main


def get_clean_opts(opts, outfile=None):
    options = config_options.parse_opts(opts)
    options = config_options.clean_opts(options)
    # Clean a second time to ensure it's idempotent
    options = config_options.clean_opts(options)
    if outfile is not None:
        options.outfile = str(outfile)
    return options


def test_standard_opts(tmp_path):
    # Smoke-test the default generation configuration with only one output page.
    options = get_clean_opts(["--num-pages=1"], tmp_path / "standard.pdf")
    main.generate(options)


@pytest.mark.parametrize("lang", db.get_languages("card_db"))
def test_languages(lang, tmp_path):
    print("checking " + lang)
    options = get_clean_opts(
        [f"--language={lang}", "--num-pages=1"], tmp_path / "language.pdf"
    )
    main.generate(options)


def test_grouped(tmp_path):
    options = get_clean_opts(
        ["--special-card-groups", "--num-pages=1"], tmp_path / "grouped.pdf"
    )
    main.generate(options)


def test_resolution(tmp_path):
    options = get_clean_opts(
        ["--tab-artwork-resolution=300", "--num-pages=1"],
        tmp_path / "resolution.pdf",
    )
    main.generate(options)


def test_no_group_global():
    options = get_clean_opts([])
    assert not options.group_global


def test_group_global():
    options = get_clean_opts(["--group-global"])
    # It's confusing that this includes both singular and plural. Perhaps a future refactor can simplify it.
    expected_groups = [
        "allies",
        "ally",
        "boon",
        "boons",
        "event",
        "events",
        "hex",
        "hexes",
        "landmark",
        "landmarks",
        "project",
        "projects",
        "prophecies",
        "prophecy",
        "state",
        "states",
        "trait",
        "traits",
        "way",
        "ways",
    ]
    for expected in expected_groups:
        assert expected in options.group_global
    assert len(options.group_global) == len(expected_groups)


def test_exclude_events():
    options = get_clean_opts(["--exclude-events"])
    expected_groups = ["events"]
    for expected in expected_groups:
        assert expected in options.group_global
    assert len(options.group_global) == len(expected_groups)
