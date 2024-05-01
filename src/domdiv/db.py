import copy
import functools
import gzip
import json
import os

import pkg_resources
from loguru import logger

from . import config_options, db
from .cards import Card, CardType

EXPANSION_EXTRA_POSTFIX = " extras"

LANGUAGE_DEFAULT = (
    "en_us"  # the primary language used if a language's parts are missing
)
LANGUAGE_XX = "xx"  # a dummy language for starting translations


@functools.lru_cache()
def get_languages(path="card_db"):
    languages = []
    for name in pkg_resources.resource_listdir("domdiv", path):
        dir_path = os.path.join(path, name)
        if pkg_resources.resource_isdir("domdiv", dir_path):
            cards_file = os.path.join(dir_path, f"cards_{name}.json.gz")
            sets_file = os.path.join(dir_path, f"sets_{name}.json.gz")
            types_file = os.path.join(dir_path, f"types_{name}.json.gz")
            if (
                pkg_resources.resource_exists("domdiv", cards_file)
                and pkg_resources.resource_exists("domdiv", sets_file)
                and pkg_resources.resource_exists("domdiv", types_file)
            ):
                languages.append(name)
    if LANGUAGE_XX in languages:
        languages.remove(LANGUAGE_XX)
    return languages


def get_resource_stream(path):
    return gzip.GzipFile(
        fileobj=pkg_resources.resource_stream("domdiv", path),
    )


@functools.lru_cache()
def get_expansions():
    set_db_filepath = os.path.join("card_db", "sets_db.json.gz")
    with get_resource_stream(set_db_filepath) as setfile:
        set_file = json.loads(setfile.read().decode("utf-8"))
    assert set_file, "Could not load any sets from database"

    fan = []
    official = []
    for s in set_file:
        if EXPANSION_EXTRA_POSTFIX not in s:
            # Make sure these are set either True or False
            set_file[s]["fan"] = set_file[s].get("fan", False)
            if set_file[s]["fan"]:
                fan.append(s)
            else:
                official.append(s)
    fan.sort()
    official.sort()
    return official, fan


@functools.lru_cache()
def get_global_groups():
    type_db_filepath = os.path.join("card_db", "types_db.json.gz")
    with get_resource_stream(type_db_filepath) as typefile:
        type_file = json.loads(typefile.read().decode("utf-8"))
    assert type_file, "Could not load any card types from database"

    group_global_choices = []
    group_global_valid = []
    for t in type_file:
        if "group_global_type" in t:
            group_global_valid.append("-".join(t["card_type"]).lower())
            group_global_choices.append(t["group_global_type"].lower())
    group_global_valid.extend(group_global_choices)
    group_global_valid.sort()
    group_global_choices.sort()
    return group_global_choices, group_global_valid


@functools.lru_cache()
def get_types(language=LANGUAGE_DEFAULT):
    # get a list of valid types
    language = language.lower()
    type_text_filepath = os.path.join("card_db", language, f"types_{language}.json.gz")
    with get_resource_stream(type_text_filepath) as type_text_file:
        type_text = json.loads(type_text_file.read().decode("utf-8"))
    assert type_text, "Could not load type file for %r" % language

    types = [x.lower() for x in type_text]
    types.sort()
    return types


@functools.lru_cache()
def get_label_data():
    labels_db_filepath = os.path.join("card_db", "labels_db.json.gz")
    label_choices = []
    label_keys = []
    label_selections = []
    with get_resource_stream(labels_db_filepath) as labelfile:
        label_info = json.loads(labelfile.read().decode("utf-8"))
    assert label_info, "Could not load label information from database"
    for label in label_info:
        if len(label["names"]) > 0:
            label_keys.append(label["names"][0])
            label_selections.append(
                label["name"] if "name" in label else label["names"][0]
            )
            label_choices.extend(label["names"])
    return label_info, label_keys, label_selections, label_choices


def find_index_of_object(lst=None, attributes=None):
    if lst is None:
        lst = []
    if attributes is None:
        attributes = {}
    # Returns the index of the first object in lst that matches the given attributes.  Otherwise returns None.
    # attributes is a dict of key: value pairs.   Object attributes that are lists are checked to have value in them.
    for i, d in enumerate(lst):
        # Set match to false just in case there are no attributes.
        match = False
        for key, value in attributes.items():
            # if anything does not match, then break out and start the next one.
            match = hasattr(d, key)
            if match:
                test = getattr(d, key, None)
                if isinstance(test, list):
                    match = value in test
                else:
                    match = value == test
            if not match:
                break

        if match:
            # If all the attributes are found, then we have a match
            return i

    # nothing matched
    return None


def read_card_data(options):
    # Read in the card types
    types_db_filepath = os.path.join("card_db", "types_db.json.gz")
    with db.get_resource_stream(types_db_filepath) as typefile:
        Card.types = json.loads(
            typefile.read().decode("utf-8"), object_hook=CardType.decode_json
        )
    assert Card.types, "Could not load any card types from database"

    # extract unique types
    type_list = []
    for c in Card.types:
        type_list = list(set(c.getTypeNames()) | set(type_list))
    # set up the basic type translation.  The actual language will be added later.
    Card.type_names = {}
    for t in type_list:
        Card.type_names[t] = t

    # turn Card.types into a dictionary for later
    Card.types = dict(((c.getTypeNames(), c) for c in Card.types))

    # Read in the card database
    card_db_filepath = os.path.join("card_db", "cards_db.json.gz")
    with get_resource_stream(card_db_filepath) as cardfile:
        cards = json.loads(
            cardfile.read().decode("utf-8"), object_hook=Card.decode_json
        )
    assert cards, "Could not load any cards from database"

    set_db_filepath = os.path.join("card_db", "sets_db.json.gz")
    with get_resource_stream(set_db_filepath) as setfile:
        Card.sets = json.loads(setfile.read().decode("utf-8"))
    assert Card.sets, "Could not load any sets from database"
    new_sets = {}
    for s in Card.sets:
        # Make sure these are set either True or False
        Card.sets[s]["no_randomizer"] = Card.sets[s].get("no_randomizer", False)
        Card.sets[s]["fan"] = Card.sets[s].get("fan", False)
        Card.sets[s]["has_extras"] = Card.sets[s].get("has_extras", True)
        Card.sets[s]["upgrades"] = Card.sets[s].get("upgrades", None)
        new_sets[s] = Card.sets[s]
        # Make an "Extras" set for normal expansions
        if Card.sets[s]["has_extras"]:
            e = s + db.EXPANSION_EXTRA_POSTFIX
            new_sets[e] = copy.deepcopy(Card.sets[s])
            new_sets[e]["set_name"] = "*" + s + db.EXPANSION_EXTRA_POSTFIX + "*"
            new_sets[e]["no_randomizer"] = True
            new_sets[e]["has_extras"] = False
    Card.sets = new_sets

    # Remove the Trash card. Do early before propagating to various sets.
    if options.no_trash:
        i = find_index_of_object(cards, {"card_tag": "Trash"})
        if i is not None:
            del cards[i]

    # Repackage Curse cards into 10 per divider. Do early before propagating to various sets.
    if options.curse10:
        i = find_index_of_object(cards, {"card_tag": "Curse"})
        if i is not None:
            new_cards = []
            cards_remaining = cards[i].getCardCount()
            while cards_remaining > 10:
                # make a new copy of the card and set count to 10
                new_card = copy.deepcopy(cards[i])
                new_card.setCardCount(10)
                new_cards.append(new_card)
                cards_remaining -= 10

            # Adjust original Curse card to the remaining cards (should be 10)
            cards[i].setCardCount(cards_remaining)
            # Add the new dividers
            cards.extend(new_cards)

    # Add any blank cards
    if options.include_blanks > 0:
        for _ in range(0, options.include_blanks):
            c = Card(
                card_tag="Blank",
                cardset=config_options.EXPANSION_GLOBAL_GROUP,
                cardset_tag=config_options.EXPANSION_GLOBAL_GROUP,
                cardset_tags=[config_options.EXPANSION_GLOBAL_GROUP],
                randomizer=False,
                types=("Blank",),
            )
            cards.append(c)

    # Create Start Deck dividers. 4 sets. Adjust totals for other cards, too.
    # Do early before propagating to various sets.
    # The card database contains one prototype divider that needs to be either duplicated or deleted.
    if options.start_decks:
        # Find the index to the individual cards that need changed in the cards list
        StartDeck_index = find_index_of_object(cards, {"card_tag": "Start Deck"})
        Copper_index = find_index_of_object(cards, {"card_tag": "Copper"})
        Estate_index = find_index_of_object(cards, {"card_tag": "Estate"})
        if Copper_index is None or Estate_index is None or StartDeck_index is None:
            # Something is wrong, can't find one or more of the cards that need to change
            logger.warning("Cannot create Start Decks")

            # Remove the Start Deck prototype if we can
            if StartDeck_index is not None:
                del cards[StartDeck_index]
        else:
            # Start Deck Constants
            STARTDECK_COPPERS = 7
            STARTDECK_ESTATES = 3
            STARTDECK_NUMBER = 4

            # Add correct card counts to Start Deck prototype.  This will be used to make copies.
            cards[StartDeck_index].setCardCount(STARTDECK_COPPERS)
            cards[StartDeck_index].addCardCount([int(STARTDECK_ESTATES)])

            # Make new Start Deck Dividers and adjust the corresponding card counts
            for x in range(0, STARTDECK_NUMBER):
                # Add extra copies of the Start Deck prototype.
                # But don't need to add the first one again, since the prototype is already there.
                if x > 0:
                    cards.append(copy.deepcopy(cards[StartDeck_index]))
                    # Note: By appending, it should not change any of the index values being used

                # Remove Copper and Estate card counts from their dividers
                cards[Copper_index].setCardCount(
                    cards[Copper_index].getCardCount() - STARTDECK_COPPERS
                )
                cards[Estate_index].setCardCount(
                    cards[Estate_index].getCardCount() - STARTDECK_ESTATES
                )
    else:
        # Remove Start Deck prototype.  It is not needed.
        StartDeck_index = find_index_of_object(cards, {"card_tag": "Start Deck"})
        if StartDeck_index is not None:
            del cards[StartDeck_index]

    # Set cardset_tag and expand cards that are used in multiple sets
    new_cards = []
    for card in cards:
        sets = list(card.cardset_tags)
        if len(sets) > 0:
            # Set and save the first one
            card.cardset_tag = sets.pop(0)
            new_cards.append(card)
            for s in sets:
                # for the rest, create a copy of the first
                if s:
                    new_card = copy.deepcopy(card)
                    new_card.cardset_tag = s
                    new_cards.append(new_card)
    cards = new_cards

    # Make sure each card has the right image file.
    for card in cards:
        card.image = card.setImage()

    return cards
