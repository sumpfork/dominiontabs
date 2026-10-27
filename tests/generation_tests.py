from __future__ import print_function

from types import SimpleNamespace

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


def test_cost_weights_default_and_override():
    defaults = get_clean_opts([])
    assert defaults.debt_cost is None
    assert defaults.potion_cost is None

    zero_costs = get_clean_opts(["--debt-cost=0", "--potion-cost=0"])
    assert zero_costs.debt_cost == 0.0
    assert zero_costs.potion_cost == 0.0


def test_cost_sorter_applies_debt_and_potion_weights():
    def card(name, cost):
        return SimpleNamespace(
            name=name,
            cardset="Test",
            isExpansion=lambda: False,
            cost_sort_key=lambda: cost,
        )

    debt = card("Debt", (0, 0, "4"))
    potion = card("Potion", (0, "1", 0))
    coin = card("Coin", (4, 0, 0))

    default_sorter = main.CardSorter("cost", "en_us", {})
    assert default_sorter.by_cost_sort_key(debt)[2] == str(debt.cost_sort_key())
    assert default_sorter.by_cost_sort_key(potion)[2] == str(potion.cost_sort_key())
    assert default_sorter.by_cost_sort_key(coin)[2] == str(coin.cost_sort_key())

    debt_one_sorter = main.CardSorter("cost", "en_us", {}, debt_cost=1.0)
    assert debt_one_sorter.by_cost_sort_key(debt)[2] == 4.0
    assert debt_one_sorter.by_cost_sort_key(coin)[2] == 4.0

    zero_weight_sorter = main.CardSorter(
        "cost", "en_us", {}, debt_cost=0.0, potion_cost=0.0
    )
    assert zero_weight_sorter.by_cost_sort_key(debt)[2] == 0.0
    assert zero_weight_sorter.by_cost_sort_key(potion)[2] == 0.0
    assert zero_weight_sorter.by_cost_sort_key(coin)[2] == 4.0


def test_debt_and_potion_weights_change_cost_ordering():
    def card(name, cost):
        return SimpleNamespace(
            name=name,
            cardset="Empires",
            isExpansion=lambda: False,
            cost_sort_key=lambda: cost,
        )

    cards = [
        card("0C/0P/4D", (0, 0, "4")),
        card("3C/1P/0D", (3, "1", 0)),
        card("1C/0P/0D", (1, 0, 0)),
        card("8C/0P/0D", (8, 0, 0)),
    ]

    no_debt_weight = main.CardSorter("cost", "en_us", {}, debt_cost=0.0)
    assert [c.name for c in sorted(cards, key=no_debt_weight)] == [
        "0C/0P/4D",
        "1C/0P/0D",
        "3C/1P/0D",
        "8C/0P/0D",
    ]

    debt_as_coin = main.CardSorter("cost", "en_us", {}, debt_cost=1.0)
    assert [c.name for c in sorted(cards, key=debt_as_coin)] == [
        "1C/0P/0D",
        "3C/1P/0D",
        "0C/0P/4D",
        "8C/0P/0D",
    ]

    potion_as_coin = main.CardSorter(
        "cost", "en_us", {}, debt_cost=0.0, potion_cost=4.0
    )
    assert [c.name for c in sorted(cards, key=potion_as_coin)] == [
        "0C/0P/4D",
        "1C/0P/0D",
        "3C/1P/0D",
        "8C/0P/0D",
    ]


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
