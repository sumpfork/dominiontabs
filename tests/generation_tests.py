from __future__ import print_function

import pytest

from domdiv import config_options, db, main


def get_clean_opts(opts):
    options = config_options.parse_opts(opts)
    options = config_options.clean_opts(options)
    # Clean a second time to ensure it's idempotent
    options = config_options.clean_opts(options)
    return options


def test_standard_opts():
    # should be the default
    options = get_clean_opts([])
    main.generate(options)


@pytest.mark.parametrize("lang", db.get_languages("card_db"))
def test_languages(lang):
    print("checking " + lang)
    options = get_clean_opts([f"--language={lang}"])
    main.generate(options)


def test_grouped():
    options = get_clean_opts(["--special-card-groups"])
    main.generate(options)


def test_resolution():
    options = get_clean_opts(["--tab-artwork-resolution=300"])
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
