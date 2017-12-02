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
import io
import codecs
import json
from shutil import copyfile

LANGUAGE_DEFAULT = 'en_us'  # default language, which takes priority
LANGUAGE_XX = 'xx'  # language for starting a translation
card_db_dir = os.path.join("..", "domdiv", "card_db")  # directory of card data
output_dir = os.path.join(".", "card_db")  # directory for output data


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
    print('reading {}'.format(json_file_path))
    # Read in the json from the specified file
    with codecs.open(json_file_path, 'r', 'utf-8') as json_file:
        data = json.load(json_file)
    assert data, "Could not load json at: '%r' " % json_file_path
    return data


def json_dict_entry(entry, separator=''):
    #  Return a nicely formated json dict entry.
    #  It does not include the enclosing {} and removes trailing white space
    json_data = json.dumps(entry, indent=4, ensure_ascii=False, sort_keys=True)
    json_data = json_data.strip(
        '{}').rstrip()  # Remove outer{} and then trailing whitespace
    return separator + json_data


# Multikey sort
# see: http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys
def multikeysort(items, columns):
    from operator import itemgetter
    comparers = [((itemgetter(col[1:].strip()), -1)
                  if col.startswith('-') else (itemgetter(col.strip()), 1))
                 for col in columns]

    def comparer(left, right):
        for fn, mult in comparers:
            result = cmp(fn(left), fn(right))
            if result:
                return mult * result
        else:
            return 0

    return sorted(items, cmp=comparer)


def main():
    ###########################################################################
    # Get all the languages, and place the default language first in the list
    ###########################################################################
    languages = get_lang_dirs(card_db_dir)
    languages.remove(LANGUAGE_DEFAULT)
    languages.insert(0, LANGUAGE_DEFAULT)
    if LANGUAGE_XX not in languages:
        languages.append(LANGUAGE_XX)
    print "Languages:"
    print languages
    print

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
    type_parts = []

    # Get the card data
    type_data = get_json_data(os.path.join(card_db_dir, "types_db.json"))

    # Sort the cards by cardset_tags, then card_tag
    sorted_type_data = multikeysort(type_data, ['card_type'])

    with io.open(
            os.path.join(output_dir, "types_db.json"), 'w',
            encoding='utf-8') as lang_out:
        lang_out.write(unicode("["))  # Start of list
        sep = ""
        for type in sorted_type_data:
            # Collect all the individual types
            type_parts = list(set(type['card_type']) | set(type_parts))
            lang_out.write(sep + json.dumps(
                type, indent=4, ensure_ascii=False, sort_keys=True))
            sep = ","
        lang_out.write(unicode("\n]\n"))  # End of List

    type_parts.sort()
    print "Unique Types:"
    print type_parts
    print

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

        with io.open(
                os.path.join(output_dir, lang, lang_file), 'w',
                encoding='utf-8') as lang_out:
            lang_out.write(unicode("{"))  # Start of types
            sep = ""
            used = []

            for type in sorted(type_parts):
                if type not in lang_type_data:
                    if lang == LANGUAGE_DEFAULT:
                        lang_type_data[type] = type
                        lang_type_default = lang_type_data
                    else:
                        lang_type_data[type] = lang_type_default[type]

                lang_out.write(json_dict_entry({type: lang_type_data[type]}, sep))
                used.append(type)
                sep = ","

            # Now keep any unused values just in case needed in the future
            for key in lang_type_data:
                if key not in used:
                    lang_out.write(
                        json_dict_entry({
                            key: lang_type_data[key]
                        }, sep))
                    sep = ","

            lang_out.write(unicode("\n}\n"))  # End of Types

            if lang == LANGUAGE_DEFAULT:
                lang_type_default = lang_type_data  # Keep for later languages

    ###########################################################################
    #  Get the cards_db information
    #  Store in a list in the order found in cards[]. Ordered as follows:
    #  1. card_tags, 2. group_tags, 3. super groups
    ###########################################################################
    cards = []
    groups = []
    super_groups = [u'events', u'landmarks']

    # Get the card data
    card_data = get_json_data(os.path.join(card_db_dir, "cards_db.json"))

    # Sort the cardset_tags
    for card in card_data:
        card["cardset_tags"].sort()
        # But put all the base cards together by moving to front of the list
        if 'base' in card["cardset_tags"]:
            card["cardset_tags"].remove('base')
            card["cardset_tags"].insert(0, 'base')

    # Sort the cards by cardset_tags, then card_tag
    sorted_card_data = multikeysort(card_data, ['cardset_tags', 'card_tag'])

    with io.open(
            os.path.join(output_dir, "cards_db.json"), 'w',
            encoding='utf-8') as lang_out:
        lang_out.write(unicode("["))  # Start of list
        sep = ""
        for card in sorted_card_data:
            if card['card_tag'] not in cards:
                cards.append(card['card_tag'])
            if 'group_tag' in card:
                if card['group_tag'] not in groups:
                    groups.append(card['group_tag'])
            lang_out.write(sep + json.dumps(
                card, indent=4, ensure_ascii=False, sort_keys=True))
            sep = ","
        lang_out.write(unicode("\n]\n"))  # End of List

    cards.extend(groups)
    cards.extend(super_groups)

    print "Cards:"
    print cards
    print

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

        #  Process the file
        with io.open(
                os.path.join(output_dir, lang, lang_file), 'w',
                encoding='utf-8') as lang_out:
            lang_out.write(unicode("{"))  # Start of set
            sep = ""
            fields = [u"description", u"extra", u"name"]

            for card in cards:
                if card not in lang_data or lang == LANGUAGE_XX:
                    #  Card is missing, need to add it
                    lang_data[card] = {}
                    if lang == LANGUAGE_DEFAULT:
                        #  Default language gets bare minimum.  Really need to add by hand.
                        lang_data[card]["extra"] = ""
                        lang_data[card]["name"] = card
                        lang_data[card]["description"] = ""
                        lang_data[card]["untranslated"] = ', '.join(fields)
                        lang_default = lang_data
                    else:
                        #  All other languages should get the default languages' text
                        lang_data[card]["extra"] = lang_default[card]["extra"]
                        lang_data[card]["name"] = lang_default[card]["name"]
                        lang_data[card]["description"] = lang_default[card][
                            "description"]
                        lang_data[card]["untranslated"] = ', '.join(fields)
                else:
                    # Card exists, figure out what needs updating (don't update default language)
                    if lang != LANGUAGE_DEFAULT:
                        if 'untranslated' in lang_data[card]:
                            #  Has an 'untranslated' field.  Process accordingly
                            if not lang_data[card]["untranslated"].strip():
                                #  It is empty, so just remove it
                                del lang_data[card]["untranslated"]
                            else:
                                #  If a field remains untranslated, then replace with the default languages copy
                                for field in fields:
                                    if field in lang_data[card]['untranslated']:
                                        lang_data[card][field] = lang_default[
                                            card][field]
                        else:
                            #  Need to create the 'untranslated' field and update based upon existing fields
                            untranslated = []
                            for field in fields:
                                if field not in lang_data[card]:
                                    lang_data[card][field] = lang_default[card][
                                        field]
                                    untranslated.append(field)
                            if untranslated:
                                #  only add if something is still needing translation
                                lang_data[card]["untranslated"] = ', '.join(
                                    untranslated)

                lang_out.write(json_dict_entry({card: lang_data[card]}, sep))
                lang_data[card]['used'] = True
                sep = ","

            # Now keep any unused values just in case needed in the future
            for key in lang_data:
                if 'used' not in lang_data[key]:
                    lang_data[key][
                        "untranslated"] = "Note: This card is currently not used."
                    lang_out.write(json_dict_entry({key: lang_data[key]}, sep))
                    sep = ","
            lang_out.write(unicode("\n}\n"))  # End of Set

            if lang == LANGUAGE_DEFAULT:
                lang_default = lang_data  # Keep for later languages

    ###########################################################################
    # Fix up the sets_db.json file
    # Place entries in alphabetical order
    ###########################################################################
    lang_file = "sets_db.json"
    set_data = get_json_data(os.path.join(card_db_dir, lang_file))

    with io.open(
            os.path.join(output_dir, lang_file), 'w',
            encoding='utf-8') as lang_out:
        lang_out.write(unicode("{"))  # Start of set
        sep = ""
        sets = []
        for s in sorted(set_data):
            lang_out.write(json_dict_entry({s: set_data[s]}, sep))
            sep = ","
            if s not in sets:
                sets.append(s)

        lang_out.write(unicode("\n}\n"))  # End of Set

    print "Sets:"
    print sets
    print

    ###########################################################################
    # Fix up all the xx/sets_xx.json files
    # Place entries in alphabetical order
    # If entries don't exist:
    #    If the default language, set from information in the "sets_db.json" file,
    #    If not the default language, set based on information from the default language.
    # Lastly, keep any extra entries that are not currently used, just in case needed
    #    in the future or is a work in progress.
    ###########################################################################
    for lang in languages:
        lang_file = "sets_" + lang + ".json"
        fname = os.path.join(card_db_dir, lang, lang_file)
        if os.path.isfile(fname):
            lang_set_data = get_json_data(fname)
        else:
            lang_set_data = {}
        with io.open(
                os.path.join(output_dir, lang, lang_file), 'w',
                encoding='utf-8') as lang_out:
            lang_out.write(unicode("{"))  # Start of set
            sep = ""

            for s in sorted(set_data):
                if s not in lang_set_data:
                    lang_set_data[s] = {}
                    if lang == LANGUAGE_DEFAULT:
                        lang_set_data[s]["set_name"] = s.title()
                        lang_set_data[s]["text_icon"] = set_data[s][
                            "text_icon"]
                        if 'short_name' in set_data[s]:
                            lang_set_data[s]["short_name"] = set_data[s][
                                "short_name"]
                        if 'set_text' in set_data[s]:
                            lang_set_data[s]["set_text"] = set_data[s][
                                "set_text"]
                    else:
                        lang_set_data[s]["set_name"] = lang_default[s][
                            "set_name"]
                        lang_set_data[s]["text_icon"] = lang_default[s][
                            "text_icon"]
                        if 'short_name' in lang_default[s]:
                            lang_set_data[s]["short_name"] = lang_default[s][
                                "short_name"]
                        if 'set_text' in lang_default[s]:
                            lang_set_data[s]["set_text"] = lang_default[s][
                                "set_text"]
                else:
                    if lang != LANGUAGE_DEFAULT:
                        for x in lang_default[s]:
                            if x not in lang_set_data[s] and x is not 'used':
                                lang_set_data[s][x] = lang_default[s][x]

                lang_out.write(json_dict_entry({s: lang_set_data[s]}, sep))
                lang_set_data[s]['used'] = True
                sep = ","

            # Now keep any unused values just in case needed in the future
            for key in lang_set_data:
                if 'used' not in lang_set_data[key]:
                    lang_out.write(json_dict_entry({key: lang_set_data[key]}, sep))
                    sep = ","

            lang_out.write(unicode("\n}\n"))  # End of Set

            if lang == LANGUAGE_DEFAULT:
                lang_default = lang_set_data  # Keep for later languages

    ###########################################################################
    # bonuses_xx files
    ###########################################################################
    for lang in languages:
        # Special case for xx.  Reseed from default language
        fromLanguage = lang
        if lang == LANGUAGE_XX:
            fromLanguage = LANGUAGE_DEFAULT

        copyfile(
            os.path.join(card_db_dir, fromLanguage, "bonuses_" + fromLanguage + ".json"),
            os.path.join(output_dir, lang, "bonuses_" + lang + ".json"))

    ###########################################################################
    # translation.txt
    ###########################################################################
    copyfile(
        os.path.join(card_db_dir, "translation.md"),
        os.path.join(output_dir, "translation.md"))

    # Since xx is the starting point for new translations,
    # make sure xx has the latest copy of translation.txt
    copyfile(
        os.path.join(card_db_dir, LANGUAGE_XX, "translation.txt"),
        os.path.join(output_dir,  LANGUAGE_XX, "translation.txt"))


if __name__ == '__main__':
    main()
