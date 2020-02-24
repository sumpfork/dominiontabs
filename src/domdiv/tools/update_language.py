###########################################################################
# This file provides maintenance on the various language files
# 1. Create new "xx/cards_xx.json" files that have entries ordered as:
#     a. the card_tag entries in "cards_db.json"
#     b. the group_tag entries as found in "cards_db.json"
#     c. the super group entries (grouping across all expansions"
#     d. any unused entries existing in the file (assumed to be work in progress)
#
# 2. Create new "sets_db.json" and "xx/cards_xx.json" with entries sorted alphabetically
#
# All output is in the designated output directory.  Original files are not overwritten.
###########################################################################

import os
import os.path
from shutil import copyfile
import argparse
import collections

from domdiv.tools.common import (
    get_json_data,
    load_language_cards,
    LANGUAGE_XX,
    LANGUAGE_DEFAULT,
    get_languages,
    multikeysort,
    load_card_data,
    write_data,
    write_language_cards,
)


def main(card_db_dir, output_dir):
    ###########################################################################
    # Get all the languages, and place the default language first in the list
    ###########################################################################
    languages = get_languages(card_db_dir)
    print("Languages:")
    print(languages)
    print()

    ###########################################################################
    #  Make sure the directories exist to hold the output
    ###########################################################################

    #  main output directory
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    #  each language directory
    for lang in languages:
        #  Make sure the directory is there to hold the file
        lang_dir = os.path.join(output_dir, lang)
        if not os.path.exists(lang_dir):
            os.makedirs(lang_dir)

    ###########################################################################
    #  Get the types_db information
    #  Store in a list in the order found in types[]. Ordered by card_type
    #  1. card_tags, 2. group_tags, 3. super groups
    ###########################################################################
    type_parts = set()

    # Get the card data
    type_data = get_json_data(os.path.join(card_db_dir, "types_db.json"))

    # Sort the cards by cardset_tags, then card_tag
    sorted_type_data = multikeysort(type_data, ["card_type"])

    write_data(sorted_type_data, os.path.join(output_dir, "types_db.json"))

    type_parts = list(set().union(*[set(t["card_type"]) for t in sorted_type_data]))
    type_parts.sort()
    print("Unique Types:")
    print(type_parts)
    print()

    ###########################################################################
    #  Get the labels_db information
    #  Store in a list in the order found.
    ###########################################################################
    all_labels = []

    # Get the card data
    label_data = get_json_data(os.path.join(card_db_dir, "labels_db.json"))

    all_labels = list(set().union(*[set(label["names"]) for label in label_data]))
    write_data(label_data, os.path.join(output_dir, "labels_db.json"))

    all_labels.sort()
    print("Labels: ")
    print(all_labels)
    print()
    ###########################################################################
    # Fix up all the xx/types_xx.json files
    # Place entries in alphabetical order
    # If entries don't exist:
    #    If the default language, set from information in the "types_db.json" file,
    #    If not the default language, set based on information from the default language.
    # Lastly, keep any extra entries that are not currently used, just in case needed
    #    in the future or is a work in progress.
    ###########################################################################
    for lang in languages:
        lang_file = "types_" + lang + ".json"
        fname = os.path.join(card_db_dir, lang, lang_file)
        if os.path.isfile(fname):
            lang_type_data = get_json_data(fname)
        else:
            lang_type_data = {}

        for t in sorted(type_parts):
            if t not in lang_type_data:
                if lang == LANGUAGE_DEFAULT:
                    lang_type_data[t] = t
                    lang_type_default = lang_type_data
                else:
                    lang_type_data[t] = lang_type_default[t]
        write_data(lang_type_data, os.path.join(output_dir, lang, lang_file))

        if lang == LANGUAGE_DEFAULT:
            lang_type_default = lang_type_data  # Keep for later languages

    sorted_card_data = load_card_data(card_db_dir)
    groups = set(card["group_tag"] for card in sorted_card_data if "group_tag" in card)
    super_groups = set(["events", "landmarks", "projects"])

    write_data(sorted_card_data, os.path.join(output_dir, "cards_db.json"))

    # maintain the sorted order, but expand with groups and super_groups
    cards = [c["card_tag"] for c in sorted_card_data]
    cards.extend(sorted(groups))
    cards.extend(sorted(super_groups))

    print("Cards:")
    print(cards)
    print()

    ###########################################################################
    # Fix up all the cards_xx.json files
    # Place entries in the same order as given in "cards_db.json".
    # If entries don't exist:
    #    If the default language, set base on information in the "cards_db.json" file,
    #    If not the default language, set based on information from the default language.
    # Lastly, keep any extra entries that are not currently used, just in case needed
    #    in the future or is a work in progress.
    ###########################################################################
    for lang in languages:

        #  contruct the cards json file name
        lang_data = load_language_cards(lang, card_db_dir)

        sorted_lang_data = collections.OrderedDict()
        for card_tag in cards:
            lang_card = lang_data.get(card_tag)

            # print(f'looking at {card_tag}: {lang_card}')
            if not lang_card or lang == LANGUAGE_XX:
                #  Card is missing, need to add it
                lang_card = {}
                if lang == LANGUAGE_DEFAULT:
                    #  Default language gets bare minimum.  Really need to add by hand.
                    lang_card["extra"] = ""
                    lang_card["name"] = card_tag
                    lang_card["description"] = ""
                    lang_default = lang_data
                else:
                    #  All other languages should get the default languages' text
                    lang_card = lang_default[card_tag].copy()
            elif lang != LANGUAGE_DEFAULT:
                # Card exists, figure out what needs updating
                lang_card.update(
                    {
                        field: value
                        for field, value in lang_default[card_tag].items()
                        if field not in lang_card
                    }
                )
            sorted_lang_data[card_tag] = lang_card
        unused = set(lang_data) - set(sorted_lang_data)
        print(
            f"unused in {lang}: {len(unused)}, used: {len(set(lang_data) & set(sorted_lang_data))}"
        )
        print(unused)
        # Now keep any unused values just in case needed in the future
        for card_tag in sorted(unused):
            lang_card = lang_data.get(card_tag)
            lang_card["notes"] = ["This card is currently not used."]
            sorted_lang_data[card_tag] = lang_card

        write_language_cards(sorted_lang_data, lang, output_dir)

        if lang == LANGUAGE_DEFAULT:
            lang_default = lang_data  # Keep for later languages

    ###########################################################################
    # Fix up the sets_db.json file
    # Place entries in alphabetical order
    ###########################################################################
    lang_file = "sets_db.json"
    set_data = get_json_data(os.path.join(card_db_dir, lang_file))

    write_data(set_data, os.path.join(output_dir, lang_file))

    print("Sets:")
    print(set(set_data))
    print()

    ###########################################################################
    # Fix up all the xx/sets_xx.json files
    # Place entries in alphabetical order
    # If entries don't exist:
    #    If the default language, set from information in the "sets_db.json" file,
    #    If not the default language, set based on information from the default language.
    ###########################################################################
    for lang in languages:
        lang_file = "sets_" + lang + ".json"
        fname = os.path.join(card_db_dir, lang, lang_file)
        if os.path.isfile(fname):
            lang_set_data = get_json_data(fname)
        else:
            lang_set_data = {}

        for s in sorted(set_data):
            if s not in lang_set_data:
                lang_set_data[s] = {}
                if lang == LANGUAGE_DEFAULT:
                    lang_set_data[s]["set_name"] = s.title()
                    lang_set_data[s]["text_icon"] = set_data[s]["text_icon"]
                    if "short_name" in set_data[s]:
                        lang_set_data[s]["short_name"] = set_data[s]["short_name"]
                    if "set_text" in set_data[s]:
                        lang_set_data[s]["set_text"] = set_data[s]["set_text"]
                else:
                    lang_set_data[s]["set_name"] = lang_default[s]["set_name"]
                    lang_set_data[s]["text_icon"] = lang_default[s]["text_icon"]
                    if "short_name" in lang_default[s]:
                        lang_set_data[s]["short_name"] = lang_default[s]["short_name"]
                    if "set_text" in lang_default[s]:
                        lang_set_data[s]["set_text"] = lang_default[s]["set_text"]
            else:
                if lang != LANGUAGE_DEFAULT:
                    for x in lang_default[s]:
                        if x not in lang_set_data[s] and x != "used":
                            lang_set_data[s][x] = lang_default[s][x]

        if lang == LANGUAGE_DEFAULT:
            lang_default = lang_set_data  # Keep for later languages

        write_data(lang_set_data, os.path.join(output_dir, lang, lang_file))

    ###########################################################################
    # bonuses_xx files
    ###########################################################################
    for lang in languages:
        # Special case for xx.  Reseed from default language
        fromLanguage = lang
        if lang == LANGUAGE_XX:
            fromLanguage = LANGUAGE_DEFAULT

        copyfile(
            os.path.join(
                card_db_dir, fromLanguage, "bonuses_" + fromLanguage + ".json"
            ),
            os.path.join(output_dir, lang, "bonuses_" + lang + ".json"),
        )

    ###########################################################################
    # translation.txt
    ###########################################################################
    copyfile(
        os.path.join(card_db_dir, "translation.md"),
        os.path.join(output_dir, "translation.md"),
    )

    # Since xx is the starting point for new translations,
    # make sure xx has the latest copy of translation.txt
    copyfile(
        os.path.join(card_db_dir, LANGUAGE_XX, "translation.txt"),
        os.path.join(output_dir, LANGUAGE_XX, "translation.txt"),
    )


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "card_db_dir",
        help="directory of card data (usually card_db_src at the top level of the distribution)",
    )
    parser.add_argument(
        "output_dir", help="directory for output data (usually src/domdiv/card_db)"
    )
    args = parser.parse_args()
    main(args.card_db_dir, args.output_dir)


if __name__ == "__main__":
    run()
