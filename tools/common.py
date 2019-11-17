import codecs
import io
import json
import os

LANGUAGE_DEFAULT = "en_us"  # default language, which takes priority
LANGUAGE_XX = "xx"  # language for starting a translation


# Multikey sort
# see: http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys
def multikeysort(items, columns):
    from operator import itemgetter

    for c in columns[::-1]:
        items = sorted(items, key=itemgetter(c))
    return items


def get_languages(card_db_dir):
    languages = get_lang_dirs(card_db_dir)
    languages.remove(LANGUAGE_DEFAULT)
    languages.insert(0, LANGUAGE_DEFAULT)
    if LANGUAGE_XX not in languages:
        languages.append(LANGUAGE_XX)
    return languages


def get_lang_dirs(path):
    # Find all valid languages.
    lang_dirs = []
    for name in os.listdir(path):
        dir_path = os.path.join(path, name)
        if os.path.isdir(dir_path):
            cards_file = os.path.join(dir_path, "cards_" + name + ".json")
            sets_file = os.path.join(dir_path, "sets_" + name + ".json")
            if os.path.isfile(cards_file) and os.path.isfile(sets_file):
                lang_dirs.append(name)
    return lang_dirs


def get_json_data(json_file_path):
    print(("reading {}".format(json_file_path)))
    # Read in the json from the specified file
    with codecs.open(json_file_path, "r", "utf-8") as json_file:
        data = json.load(json_file)
    assert data, "Could not load json at: '%r' " % json_file_path
    return data


def load_language_cards(lang, card_db_dir):
    #  contruct the cards json file name
    lang_file = f"cards_{lang}.json"
    fname = os.path.join(card_db_dir, lang, lang_file)
    if os.path.isfile(fname):
        lang_data = get_json_data(fname)
    else:
        lang_data = {}
    return lang_data


def write_data(data, fname):
    #  Process the file
    print(f"writing {fname}")
    with io.open(os.path.join(fname), "w", encoding="utf-8") as lang_out:
        json.dump(data, lang_out, indent=4, ensure_ascii=False)
        lang_out.write("\n")


def write_language_cards(cards, lang, card_db_dir):
    lang_file = f"cards_{lang}.json"
    fname = os.path.join(card_db_dir, lang, lang_file)
    write_data(cards, fname)


def load_card_data(card_db_dir):
    ###########################################################################
    #  Get the cards_db information
    #  Store in a list in the order found in cards[]. Ordered as follows:
    #  1. card_tags, 2. group_tags, 3. super groups
    ###########################################################################

    # Get the card data
    card_data = get_json_data(os.path.join(card_db_dir, "cards_db.json"))

    # Sort the cardset_tags
    for card in card_data:
        card["cardset_tags"].sort()
        # But put all the base cards together by moving to front of the list
        if "base" in card["cardset_tags"]:
            card["cardset_tags"].remove("base")
            card["cardset_tags"].insert(0, "base")

    # Sort the cards by cardset_tags, then card_tag
    return multikeysort(card_data, ["cardset_tags", "card_tag"])
