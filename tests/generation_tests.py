from __future__ import print_function

from types import SimpleNamespace

import pytest

from domdiv import config_options, db, main
from domdiv.cards import Card, CardType


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


def test_cost_weights_default_and_override():
    defaults = get_clean_opts([])
    assert defaults.debt_cost is None
    assert defaults.potion_cost is None

    zero_costs = get_clean_opts(["--debt-cost=0", "--potion-cost=0"])
    assert zero_costs.debt_cost == 0.0
    assert zero_costs.potion_cost == 0.0

    debt_only = get_clean_opts(["--debt-cost=2"])
    assert debt_only.debt_cost == 2.0
    assert debt_only.potion_cost is None

    potion_only = get_clean_opts(["--potion-cost=3"])
    assert potion_only.debt_cost is None
    assert potion_only.potion_cost == 3.0


def test_weighted_cost_sorting_is_independent_and_keeps_raw_cost_tiebreaks(
    monkeypatch,
):
    monkeypatch.setattr(
        Card,
        "types",
        {("Action",): CardType(["Action"], "action.png")},
    )

    def card(name, coin, potion=0, debt=0):
        return Card(
            name=name,
            cardset="Empires",
            cardset_tag="empires",
            types=("Action",),
            cost=str(coin),
            potcost=potion,
            debtcost=debt,
        )

    cards = [
        card("0C/0P/4D", 0, debt="4"),
        card("1C/0P/0D", 1),
        card("3C/1P/0D", 3, potion="1"),
        card("4C/0P/0D", 4),
        card("8C/0P/0D", 8),
    ]

    # Unweighted sorting starts with coin cost and retains the original costs as tie-breakers.
    default_sorter = main.CardSorter("cost", "en_us", {})
    assert [c.name for c in sorted(cards, key=default_sorter)] == [
        "0C/0P/4D",
        "1C/0P/0D",
        "3C/1P/0D",
        "4C/0P/0D",
        "8C/0P/0D",
    ]

    # A debt weight of 1 makes 4 Debt tie with 4 Coins; raw costs break the tie.
    debt_as_coin = main.CardSorter("cost", "en_us", {}, debt_cost=1.0)
    assert [c.name for c in sorted(cards, key=debt_as_coin)] == [
        "1C/0P/0D",
        "3C/1P/0D",
        "0C/0P/4D",
        "4C/0P/0D",
        "8C/0P/0D",
    ]

    # Specifying a Potion weight does not implicitly apply a Debt weight.
    potion_as_coin = main.CardSorter("cost", "en_us", {}, potion_cost=4.0)
    assert [c.name for c in sorted(cards, key=potion_as_coin)] == [
        "0C/0P/4D",
        "1C/0P/0D",
        "4C/0P/0D",
        "3C/1P/0D",
        "8C/0P/0D",
    ]


def test_cost_alpha_sort_mixes_expansions_and_sorts_names():
    options = get_clean_opts(["--order=cost-alpha"])
    assert options.order == "cost-alpha"

    def card(name, cardset, cost):
        return SimpleNamespace(
            name=name,
            cardset=cardset,
            isExpansion=lambda: False,
            cost_sort_key=lambda: cost,
        )

    cards = [
        card("Zulu", "First Edition", (3, 0, 0)),
        card("Cheap", "Second Edition", (2, 0, 0)),
        card("Alpha", "Second Edition", (3, 0, 0)),
    ]
    sorter = main.CardSorter("cost-alpha", "en_us", {})

    cards.sort(key=sorter)

    assert [card.name for card in cards] == ["Cheap", "Alpha", "Zulu"]


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
