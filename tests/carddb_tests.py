from __future__ import print_function

import os
import shutil
import unicodedata

import pytest

from domdiv import cards as domdiv_cards
from domdiv import config_options, db, main
from domdiv.cards import Card
from tests import parse_and_clean_args


def test_cardread():
    # we test the number of cards only to make sure it doesn't get changed
    # inadvertently by unrelated changes
    num_cards_expected = 1068

    total_cards = sum(c.num_ungrouped_cards for c in expected_card_counts)
    assert total_cards == num_cards_expected

    options = config_options.parse_opts([])
    cards = db.read_card_data(options)
    assert len(cards) == num_cards_expected
    valid_cardsets = {
        "base",
        "dominion1stEdition",
        "dominion1stEditionRemoved",
        "dominion2ndEdition",
        "dominion2ndEditionUpgrade",
        "intrigue1stEdition",
        "intrigue1stEditionRemoved",
        "intrigue2ndEdition",
        "intrigue2ndEditionUpgrade",
        "seaside1stEdition",
        "seaside1stEditionRemoved",
        "seaside2ndEdition",
        "seaside2ndEditionUpgrade",
        "alchemy",
        "prosperity1stEdition",
        "prosperity1stEditionRemoved",
        "prosperity2ndEdition",
        "prosperity2ndEditionUpgrade",
        "cornucopia1stEdition",
        "cornucopia1stEditionRemoved",
        "cornucopia2ndEditionUpgrade",
        "cornucopiaAndGuilds2ndEdition",
        "hinterlands1stEdition",
        "hinterlands1stEditionRemoved",
        "hinterlands2ndEdition",
        "hinterlands2ndEditionUpgrade",
        "darkAges",
        "guilds1stEdition",
        "guilds1stEditionRemoved",
        "guilds2ndEditionUpgrade",
        "guilds-bigbox2-de",
        "adventures",
        "empires",
        "nocturne",
        "plunder",
        "promo",
        "promo-bigbox2-de",
        "renaissance",
        "menagerie",
        "animals",
        "allies",
        "risingSun",
    }
    asserted_cardsets = {c.cardset_tag for c in expected_card_counts}
    assert valid_cardsets == asserted_cardsets
    for c in cards:
        assert isinstance(c, domdiv_cards.Card)
        assert c.cardset_tag in valid_cardsets
        assert all(t in valid_cardsets for t in c.cardset_tags)
        assert len(c.cardset_tags) >= 1

    # Option modified card count
    options = config_options.parse_opts(
        ["--no-trash", "--curse10", "--start-decks", "--include-blanks", "7"]
    )
    options = config_options.clean_opts(options)
    options.data_path = "."
    cards = db.read_card_data(options)
    # Total delta cards is +28 from
    #      Trash:       -1 * 3 sets = -3
    #      Curse:       +2 * 4 sets = +8
    #      Start Decks: +4 * 4 sets = +16
    #      Blanks:      +7          = +7
    assert len(cards) == num_cards_expected + 28


class ExpectedSetCardCount:
    def __init__(
        self, cardset_tag, num_ungrouped_cards, num_grouped_cards, num_individual_cards
    ):
        self.cardset_tag = cardset_tag
        self.num_ungrouped_cards = num_ungrouped_cards
        self.num_grouped_cards = num_grouped_cards
        self.num_individual_cards = num_individual_cards

    def filter_in_set(self, cards):
        return [c for c in cards if self.cardset_tag in c.cardset_tags]

    def assert_total_card_count(self, cards: list[Card]):
        total_card_count = sum([c.getCardCount() for c in self.filter_in_set(cards)])
        assert total_card_count == self.num_individual_cards, (
            f"{self.cardset_tag} had {total_card_count} individual cards, not {self.num_individual_cards} as expected"
        )


expected_card_counts = [
    ExpectedSetCardCount(
        "dominion1stEdition",
        25 + 7 + 1,  # 26 kingdom, 7 base, trash
        25 + 7 + 1,  # no grouping
        # 500 cards printed, 25 randomizers, 7 blue base randomizers, 7 blanks
        500 - 25 - 7 - 7,
    ),
    ExpectedSetCardCount(
        "dominion2ndEdition",
        26 + 7,  # 26 kingdom, 7 base
        26 + 7,  # no grouping
        500 - 26 - 4,  # 500 cards printed, 26 blue randomizers, 4 blanks
    ),
    ExpectedSetCardCount(
        "dominion1stEditionRemoved",
        6,
        6,  # no grouping
        60,
    ),
    ExpectedSetCardCount(
        "dominion2ndEditionUpgrade",
        7,  # 26 kingdom, 7 base
        7,  # no grouping
        80 - 7 - 3,  # 80 cards printed, 7 blue randomizers, 3 blanks
    ),
    ExpectedSetCardCount(
        "intrigue1stEdition",
        25 + 7 + 1,  # 26 kingdom, 7 base, trash
        25 + 7 + 1,  # no grouping
        500 - 25 - 8,  # 500 cards printed, 25 blue kingdom randomizers, 8 blanks
    ),
    ExpectedSetCardCount(
        "intrigue2ndEdition",
        26,  # 26 kingdom
        26,  # no grouping
        300 - 26 - 6,  # 500 cards printed, 26 blue randomizers, 4 blanks
    ),
    ExpectedSetCardCount(
        "intrigue1stEditionRemoved",
        6,
        6,
        62,  # 1 victory card
    ),
    ExpectedSetCardCount(
        "intrigue2ndEditionUpgrade",
        7,  # 26 kingdom, 7 base
        7,  # no grouping
        80 - 7 - 1,  # 80 cards printed, 7 blue randomizers, 3 blanks
    ),
    ExpectedSetCardCount(
        "seaside1stEdition",
        26,  # 26 kingdom
        26,  # no grouping
        300 - 26 - 12,  # 300 cards printed, 26 blue randomizers, 12 blanks
    ),
    ExpectedSetCardCount(
        "seaside2ndEdition",
        27,  # 27 kingdom
        27,  # no grouping
        300 - 27 - 1,  # 300 cards printed, 27 blue randomizers, 1 blank
    ),
    ExpectedSetCardCount(
        "seaside1stEditionRemoved",
        8,
        8,
        80,
    ),
    ExpectedSetCardCount(
        "seaside2ndEditionUpgrade",
        9,  # 26 kingdom, 7 base
        9,  # no grouping
        100 - 9 - 1,  # 100 cards printed, 9 blue randomizers, 1 blank
    ),
    ExpectedSetCardCount(
        "alchemy",
        12 + 1,  # 12 kingdom, potion
        12 + 1,  # no grouping
        150 - 12,  # 500 cards printed, 12 blue randomizers
    ),
    ExpectedSetCardCount(
        "prosperity1stEdition",
        25 + 2,  # 25 kingdom, 2 base
        25 + 2,  # no grouping
        300 - 25 - 1,  # 300 cards printed, 25 blue kingdom randomizers, 1 blank
    ),
    ExpectedSetCardCount(
        "prosperity2ndEdition",
        25 + 2,  # 25 kingdom, 2 base
        25 + 2,  # no grouping
        300 - 25 - 1,  # 300 cards printed, 25 blue kingdom randomizers, 1 blank
    ),
    ExpectedSetCardCount(
        "prosperity1stEditionRemoved",
        9,
        9,
        90,
    ),
    ExpectedSetCardCount(
        "prosperity2ndEditionUpgrade",
        9,
        9,
        100 - 9 - 1,  # 100 cards printed, 9 blue randomizers, 1 blank
    ),
    ExpectedSetCardCount(
        "hinterlands1stEdition",
        26,  # 26 kingdom
        26,  # no grouping
        300 - 26 - 8,  # 300 cards printed, 26 blue kingdom randomizers, 10 blanks
    ),
    ExpectedSetCardCount(
        "hinterlands2ndEdition",
        26,  # 26 kingdom
        26,  # no grouping
        300 - 26 - 10,  # 300 cards printed, 26 blue kingdom randomizers, 10 blanks
    ),
    ExpectedSetCardCount(
        "hinterlands1stEditionRemoved",
        9,
        9,
        92,  # 1 victory card
    ),
    ExpectedSetCardCount(
        "hinterlands2ndEditionUpgrade",
        9,
        9,
        100 - 9 - 1,  # 100 cards printed, 9 blue randomizers, 1 blank
    ),
    ExpectedSetCardCount(
        "cornucopia1stEdition",
        13 + 5,  # 5 prizes
        13,  # 13 kingdom. Prizes grouped with Tournament
        150 - 13,  # 150 cards printed, 13 blue kingdom randomizers
    ),
    ExpectedSetCardCount(
        "cornucopia1stEditionRemoved",
        5 + 5,  # 5 kingdom, 5 prizes
        5,  # Prizes grouped with Tournament
        55,
    ),
    ExpectedSetCardCount(
        "cornucopia2ndEditionUpgrade",
        5 + 6,  # 6 rewards
        5,  # 5 kingdom. Rewards grouped with Joust
        62,
    ),
    ExpectedSetCardCount(
        "guilds1stEdition",
        13,  # 13 kingdom
        13,
        150 - 13 - 7,  # 150 cards printed, 13 blue kingdom randomizers, 7 blanks
    ),
    ExpectedSetCardCount(
        "guilds1stEditionRemoved",
        3,
        3,
        30,
    ),
    ExpectedSetCardCount(
        "guilds2ndEditionUpgrade",
        3,
        3,
        30,
    ),
    ExpectedSetCardCount(
        "cornucopiaAndGuilds2ndEdition",
        26 + 6,  # 6 rewards
        26,  # 26 kingdom. Prizes grouped with Tournament
        300 - 26,  # 300 cards printed, 26 blue kingdom randomizers
    ),
    ExpectedSetCardCount(  # There was only ever one upgrade pack sold for both cornucopia and guilds combined
        "darkAges",
        # TODO update when ungrouping ruins
        35 + 4 + 3,  # 35 kingdom, spoils, ruins, madman, mercenary, 3 shelters.
        35 + 3,  # spoils, ruins, shelters
        500 - 35,  # 500 cards printed, 35 randomizers
    ),
    ExpectedSetCardCount(
        "adventures",
        30 + 20 + 8,  # 30 kingdom, 20 events, 8 traveler upgrades
        30 + 1,  # Events. Travelers with their base card
        400 - 30 - 6,  # 400 cards printed, 30 randomizers, 6 blank
    ),
    ExpectedSetCardCount(
        "empires",
        24 + 5 + 13 + 21,  # 24 kingdom, 5 split pile, 13 events, 21 landmarks
        24 + 2,
        300 - 24,
    ),
    ExpectedSetCardCount(
        "nocturne",
        # 33 kingdom, 7 heirlooms, 3 zombies, 3 spirits, 12 boons, 12 hexes, bat, wish, 3 states
        33 + 7 + 3 + 3 + 12 + 12 + 1 + 1 + 3,
        33 + 1 + 1 + 1 + 1 + 3,  # 33 kingdom, boons, hexes, states, wish, 3 spirits
        500 - 33,
    ),
    ExpectedSetCardCount(
        "renaissance",
        25 + 20 + 5,  # 25 kingdom, 20 project, 5 artifact
        25 + 1,  # 25 kingdom, projects. Artifacts grouped with cards that use them
        300 - 25,
    ),
    ExpectedSetCardCount(
        "menagerie",
        30 + 20 + 20 + 1,  # 30 kingdom, 20 way, 20 event, horse
        30 + 1 + 1 + 1,  # 30 kingdom, ways, events, horses
        400 - 30,
    ),
    ExpectedSetCardCount(
        "allies",
        # TODO this includes all the split pile cards and also their randomizers.
        31 + 23 + 6 * 4,  # 31 kingdom, 23 ally, 6 4-card split piles
        31 + 1,  # 31 kingdom, ally
        400 - 31,
    ),
    ExpectedSetCardCount(
        "plunder",
        # TODO update when ungrouping loot
        40 + 15 + 15 + 1,  # 40 kingdom, 15 trait, 15 event, loot
        40 + 1 + 1 + 1,  # 40 kingdom, traits, events, loot
        500 - 40,
    ),
    ExpectedSetCardCount(
        "risingSun",
        25 + 10 + 15,  # 25 kingdom, 10 event, 15 prophecy
        25 + 1 + 1,  # 25 kingdom, events, prophecies
        300 - 25,
    ),
    ExpectedSetCardCount(
        "promo",
        12 + 1,  # sauna/avanto split
        12,
        113,  # 1 victory, summon
    ),
    ExpectedSetCardCount(
        "base",
        11,  # Curse, 4 victory, 4 treasure, potion, trash
        11,
        250 - 1,  # 250 printed, including 1 trash, 1 blank
    ),
    ExpectedSetCardCount(
        "guilds-bigbox2-de",
        13,
        13,
        130,  # 250 printed, including 1 trash, 1 blank
    ),
    ExpectedSetCardCount(
        "promo-bigbox2-de",
        4,
        4,
        40,  # 250 printed, including 1 trash, 1 blank
    ),
    ExpectedSetCardCount(
        "animals",
        3,
        3,
        32,
    ),
]


@pytest.mark.parametrize(
    "expected",
    expected_card_counts,
    ids=map(lambda s: s.cardset_tag, expected_card_counts),
)
def test_ungrouped_card_count_by_set(expected):
    options = parse_and_clean_args(
        [
            "--expansions",
            expected.cardset_tag,
            "--fan",
            expected.cardset_tag,
            "--base-cards-with-expansion",
        ]
    )
    all_cards = db.read_card_data(options)
    selected_cards = main.filter_sort_cards(all_cards, options)
    assert len(selected_cards) == expected.num_ungrouped_cards
    expected.assert_total_card_count(selected_cards)
    multi_card_piles = [c for c in selected_cards if len(c.getCardCounts()) != 1]
    assert len(multi_card_piles) == 0


@pytest.mark.parametrize(
    "expected",
    expected_card_counts,
    ids=map(lambda s: s.cardset_tag, expected_card_counts),
)
def test_grouped_card_count_by_set(expected):
    options = parse_and_clean_args(
        [
            "--expansions",
            expected.cardset_tag,
            "--fan",
            expected.cardset_tag,
            "--base-cards-with-expansion",
            "--group-special",
        ]
    )
    all_cards = db.read_card_data(options)
    selected_cards = main.filter_sort_cards(all_cards, options)
    assert len(selected_cards) == expected.num_grouped_cards
    expected.assert_total_card_count(selected_cards)


@pytest.mark.parametrize("lang", db.get_languages("card_db"))
def test_languages_db(lang):
    print("checking " + lang)
    # for now, just test that they load
    options = config_options.parse_opts(["--language", lang])
    options.data_path = "."
    cards = db.read_card_data(options)
    assert cards, f'"{lang}" cards did not read properly'
    cards = main.add_card_text(cards, "en_us")
    cards = main.add_card_text(cards, lang)
    if lang == "it":
        assert "Maledizione" in [card.name for card in cards]
    elif lang == "de":
        assert "Fluch" in [card.name for card in cards]


def test_only_type():
    options = config_options.parse_opts(
        [
            "--expansions",
            "base",
            "alchemy",
            "--include-blanks",
            "5",
            "--only-type-any",
            "blank",
            "curse",
            "--only-type-all",
            "attack",
            "action",
        ]
    )
    options = config_options.clean_opts(options)
    options.data_path = "."
    cards = db.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    # Total 8 from
    #      Blank:         +5 added in options
    #      Curse:         +1 from base
    #      Action Attack: +2 from Alchemy
    print(cards)
    assert len(cards) == 8


def test_expansion():
    # test that we can use --expansion or
    # --expansions, that we can have multiple
    # items with a single flag, that * syntax
    # works, that we can use either the
    # cardset tag or name, and that capitalization
    # doesn't matter
    options = config_options.parse_opts(
        [
            "--expansion",
            "advEntUres",
            "dominion 2nd*",
            "--expansions=intrigue1stEdition",
        ]
    )
    options = config_options.clean_opts(options)
    options.data_path = "."
    cards = db.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    card_sets = set(x.cardset.lower() for x in cards)
    assert card_sets == {
        "adventures",
        "dominion 2nd edition",
        "dominion 2nd edition upgrade",
        "intrigue 1st edition",
    }


def test_exclude_expansion():
    # test that we can use --exclude-expansion or
    # --exclude-expansions, that we can have multiple
    # items with a single flag, that * syntax
    # works, that we can use either the
    # cardset tag or name, and that capitalization
    # doesn't matter
    options = config_options.parse_opts(
        [
            "--expansions",
            "adventures",
            "dominion*",
            "intrigue*",
            "--exclude-expansions",
            "dominiOn1stEditIon",
            "intrigue 2nd*",
            "--exclude-expansion",
            "dominion 2nd edition",
        ]
    )
    options = config_options.clean_opts(options)
    options.data_path = "."
    cards = db.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    card_sets = set(x.cardset.lower() for x in cards)
    assert card_sets == {
        "adventures",
        "dominion 1st edition removed",
        "dominion 2nd edition upgrade",
        "intrigue 1st edition",
        "intrigue 1st edition removed",
    }


def test_expansion_description_card_order():
    # test that the expansions cards lists cards
    # in alphabetical order, like they are printed,
    # and that accents don't matter
    options = config_options.parse_opts(
        [
            "--expansions",
            "hinterlands1stEdition",
            "--expansion-dividers",
            "--language",
            "fr",
            "--only-type-any",
            "Expansion",
        ]
    )
    options = config_options.clean_opts(options)
    options.data_path = "."
    cards = db.read_card_data(options)
    cards = main.filter_sort_cards(cards, options)
    card_names = [c.strip() for c in cards[0].description.split("|")]
    # The 26 french card names of the Hinterlands expansion should be sorted as if no accent
    assert len(card_names) == 26
    assert card_names == sorted(
        card_names,
        key=lambda s: "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        ),
    )
