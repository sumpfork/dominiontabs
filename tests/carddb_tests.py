from __future__ import print_function

import contextlib
import os
import shutil
import unicodedata

import pytest

from domdiv import cards as domdiv_cards
from domdiv import config_options, db, main


@pytest.fixture
def rmtestcardb(request):
    def rmd():
        testcardb_dir = os.path.join(str(request.config.rootdir), "tools/card_db")
        if os.path.exists(testcardb_dir):
            print(f"removing {testcardb_dir}")
            shutil.rmtree(testcardb_dir)

    request.addfinalizer(rmd)


def test_cardread():
    # we test the number of cards only to make sure it doesn't get changed
    # inadvertently by unrelated changes
    num_cards_expected = 1068

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
        "cornucopia extras",
        "cornucopia1stEdition",
        "cornucopia1stEditionRemoved",
        "cornucopia2ndEditionUpgrade",
        "cornucopiaAndGuilds2ndEdition",
        "hinterlands1stEdition",
        "hinterlands1stEditionRemoved",
        "hinterlands2ndEdition",
        "hinterlands2ndEditionUpgrade",
        "darkAges",
        "darkAges extras",
        "guilds1stEdition",
        "guilds1stEditionRemoved",
        "guilds2ndEditionUpgrade",
        "guilds-bigbox2-de",
        "adventures",
        "adventures extras",
        "empires",
        "empires extras",
        "nocturne",
        "nocturne extras",
        "plunder",
        "promo",
        "promo-bigbox2-de",
        "renaissance",
        "menagerie",
        "extras",
        "animals",
        "allies",
        "risingSun",
    }
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


@contextlib.contextmanager
def change_cwd(d):
    curdir = os.getcwd()
    try:
        os.chdir(d)
        yield
    finally:
        os.chdir(curdir)


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
