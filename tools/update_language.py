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
import io
import codecs
import json
from shutil import copyfile
import argparse
import collections

LANGUAGE_DEFAULT = "en_us"  # default language, which takes priority
LANGUAGE_XX = "xx"  # language for starting a translation


def get_lang_dirs(path):
    # Find all valid languages.
    languages = []
    for name in os.listdir(path):
        dir_path = os.path.join(path, name)
        if os.path.isdir(dir_path):
            cards_file = os.path.join(dir_path, "cards_" + name + ".json")
            sets_file = os.path.join(dir_path, "sets_" + name + ".json")
            if os.path.isfile(cards_file) and os.path.isfile(sets_file):
                languages.append(name)
    return languages


def get_json_data(json_file_path):
    print(("reading {}".format(json_file_path)))
    # Read in the json from the specified file
    with codecs.open(json_file_path, "r", "utf-8") as json_file:
        data = json.load(json_file)
    assert data, "Could not load json at: '%r' " % json_file_path
    return data


# Multikey sort
# see: http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys
def multikeysort(items, columns):
    from operator import itemgetter

    for c in columns[::-1]:
        items = sorted(items, key=itemgetter(c))
    return items


def main(card_db_dir, output_dir):
    print("foo")
    ###########################################################################
    # Get all the languages, and place the default language first in the list
    ###########################################################################
    languages = get_lang_dirs(card_db_dir)
    languages.remove(LANGUAGE_DEFAULT)
    languages.insert(0, LANGUAGE_DEFAULT)
    if LANGUAGE_XX not in languages:
        languages.append(LANGUAGE_XX)
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

    with io.open(os.path.join(output_dir, "types_db.json"), "w", encoding="utf-8") as f:
        json.dump(sorted_type_data, f, indent=4, ensure_ascii=False)
        f.write("\n")
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

    with io.open(
        os.path.join(output_dir, "labels_db.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(label_data, f, indent=4, ensure_ascii=False)
        f.write("\n")

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

        with io.open(
            os.path.join(output_dir, lang, lang_file), "w", encoding="utf-8"
        ) as f:
            json.dump(lang_type_data, f, indent=4, ensure_ascii=False)
            f.write("\n")

        if lang == LANGUAGE_DEFAULT:
            lang_type_default = lang_type_data  # Keep for later languages

    ###########################################################################
    #  Get the cards_db information
    #  Store in a list in the order found in cards[]. Ordered as follows:
    #  1. card_tags, 2. group_tags, 3. super groups
    ###########################################################################

    # Get the card data
    card_data = get_json_data(os.path.join(card_db_dir, "cards_db.json"))

    cards = set(card["card_tag"] for card in card_data)
    groups = set(card["group_tag"] for card in card_data if "group_tag" in card)
    super_groups = set(["events", "landmarks"])

    # Sort the cardset_tags
    for card in card_data:
        card["cardset_tags"].sort()
        # But put all the base cards together by moving to front of the list
        if "base" in card["cardset_tags"]:
            card["cardset_tags"].remove("base")
            card["cardset_tags"].insert(0, "base")

    # Sort the cards by cardset_tags, then card_tag
    sorted_card_data = multikeysort(card_data, ["cardset_tags", "card_tag"])

    with io.open(
        os.path.join(output_dir, "cards_db.json"), "w", encoding="utf-8"
    ) as lang_out:
        json.dump(sorted_card_data, lang_out, indent=4, ensure_ascii=False)
        lang_out.write("\n")

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
        lang_file = "cards_" + lang + ".json"
        fname = os.path.join(card_db_dir, lang, lang_file)
        if os.path.isfile(fname):
            lang_data = get_json_data(fname)
        else:
            lang_data = {}

        sorted_lang_data = collections.OrderedDict()
        fields = ["description", "extra", "name"]
        for card_tag in cards:
            lang_card = lang_data.get(card_tag)
            # print(f'looking at {card_tag}: {lang_card}')
            if not lang_card or lang == LANGUAGE_XX:
                #  Card is missing, need to add it
                lang_card = {}
                if lang == LANGUAGE_DEFAULT:
                    #  Default language gets bare minimum.  Really need to add by hand.
                    lang_card["extra"] = ""
                    lang_card["name"] = card
                    lang_card["description"] = ""
                    lang_card["untranslated"] = fields
                    lang_default = lang_data
                else:
                    #  All other languages should get the default languages' text
                    lang_card["extra"] = lang_default[card_tag]["extra"]
                    lang_card["name"] = lang_default[card_tag]["name"]
                    lang_card["description"] = lang_default[card_tag]["description"]
                    lang_card["untranslated"] = fields
            else:
                # Card exists, figure out what needs updating (don't update default language)
                if lang != LANGUAGE_DEFAULT:
                    if "untranslated" in lang_card:
                        #  Has an 'untranslated' field.  Process accordingly
                        if not lang_card["untranslated"]:
                            #  It is empty, so just remove it
                            del lang_card["untranslated"]
                        else:
                            #  If a field remains untranslated, then replace with the default languages copy
                            for field in fields:
                                if field in lang_card["untranslated"]:
                                    lang_card[field] = lang_default[card_tag][field]
                    else:
                        #  Need to create the 'untranslated' field and update based upon existing fields
                        untranslated = []
                        for field in fields:
                            if field not in lang_data[card_tag]:
                                lang_card[field] = lang_default[card_tag][field]
                                untranslated.append(field)
                        if untranslated:
                            #  only add if something is still needing translation
                            lang_card["untranslated"] = untranslated
            lang_card["used"] = True
            sorted_lang_data[card_tag] = lang_card
        unused = [c for c in lang_data.values() if "used" not in c]
        print(
            f'unused in {lang}: {len(unused)}, used: {len([c for c in lang_data.values() if "used" in c])}'
        )
        print([c["name"] for c in unused])
        # Now keep any unused values just in case needed in the future
        for card_tag in lang_data:
            lang_card = lang_data.get(card_tag)
            if "used" not in lang_card:
                if lang != LANGUAGE_XX:
                    lang_card["untranslated"] = [
                        "Note: This card is currently not used."
                    ]
                sorted_lang_data[card_tag] = lang_card
            else:
                del lang_card["used"]

        #  Process the file
        with io.open(
            os.path.join(output_dir, lang, lang_file), "w", encoding="utf-8"
        ) as lang_out:
            json.dump(sorted_lang_data, lang_out, indent=4, ensure_ascii=False)
            lang_out.write("\n")

        if lang == LANGUAGE_DEFAULT:
            lang_default = lang_data  # Keep for later languages

    ###########################################################################
    # Fix up the sets_db.json file
    # Place entries in alphabetical order
    ###########################################################################
    lang_file = "sets_db.json"
    set_data = get_json_data(os.path.join(card_db_dir, lang_file))

    with io.open(
        os.path.join(output_dir, lang_file), "w", encoding="utf-8"
    ) as lang_out:
        json.dump(set_data, lang_out, sort_keys=True, indent=4, ensure_ascii=False)
        lang_out.write("\n")

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

        with io.open(
            os.path.join(output_dir, lang, lang_file), "w", encoding="utf-8"
        ) as lang_out:
            json.dump(lang_set_data, lang_out, ensure_ascii=False, indent=4)
            lang_out.write("\n")

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--card_db_dir",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "src", "domdiv", "card_db"
        ),
        help="directory of card data",
    )
    parser.add_argument(
        "--output_dir",
        default=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".", "card_db"
        ),
        help="directory for output data",
    )
    args = parser.parse_args()
    main(args.card_db_dir, args.output_dir)
