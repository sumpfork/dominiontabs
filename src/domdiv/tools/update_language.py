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

import argparse
import collections
import json
import os
import os.path
import shutil
import sqlite3

from domdiv.tools.common import (
    get_json_data,
    load_language_cards,
    LANGUAGE_XX,
    LANGUAGE_DEFAULT,
    get_languages,
    load_card_data,
)

VALID_CARD_FIELD_NAMES = {"description", "extra", "name"}


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
    # could move this to a tmp dir, but it's nice to have here for debugging
    if os.path.exists("domdiv.db"):
        os.remove("domdiv.db")
    with sqlite3.connect("domdiv.db") as db:
        db.execute("PRAGMA foreign_keys = ON")
        db.execute(
            """
            create table card_types
                (
                    keywords text not null primary key,
                    image text,
                    default_count integer,
                    tab_cost_height_offset integer default 0,
                    tab_text_height_offset integer default 0,
                    group_cost text,
                    group_global_type text
                )
            """
        )

        ###########################################################################
        #  Get the types_db information
        #  Store in a list in the order found in types[]. Ordered by card_type
        #  1. card_tags, 2. group_tags, 3. super groups
        ###########################################################################
        # Get the card data
        type_data = get_json_data(os.path.join(card_db_dir, "types_db.json"))
        for t in type_data:
            t["card_type"] = tuple(sorted(t["card_type"]))

        types = set(t["card_type"] for t in type_data)
        assert len(type_data) == len(
            types
        ), f"{[t for t, c in collections.Counter(ty['card_type'] for ty in type_data).items() if c > 1]}"

        type_parts = list(set().union(*[set(t["card_type"]) for t in type_data]))
        type_parts.sort()
        print("Unique Types:")
        print(type_parts)
        print()

        for t in type_data:
            t["card_type"] = json.dumps(t["card_type"])

        db.executemany(
            """
            insert into card_types values
                (
                    :card_type,
                    :card_type_image,
                    :defaultCardCount,
                    :tabCostHeightOffset,
                    :tabTextHeightOffset,
                    :group_cost,
                    :group_global_type
                )
            """,
            [collections.defaultdict(lambda: None, t) for t in type_data],
        )

        ###########################################################################
        #  Get the labels_db information
        ###########################################################################

        # db.execute("create table labels")
        # label_data = get_json_data(os.path.join(card_db_dir, "labels_db.json"))
        # label_table.insert_multiple(label_data)

        # all_labels = list(
        #     set().union(*[set(label["names"]) for label in label_table.all()])
        # )

        # print("Labels: ")
        # print(all_labels)
        # print()

        # card type translations go into a single db table keyed by type and language
        db.execute(
            """
            create table card_type_translations
                (
                    type_keyword text not null,
                    language text not null,
                    translation text not null,
                    primary key (type_keyword, language)
                )
            """
        )

        for lang in languages:
            lang_file = "types_" + lang + ".json"
            fname = os.path.join(card_db_dir, lang, lang_file)
            if os.path.isfile(fname):
                lang_type_data = get_json_data(fname)
                db.executemany(
                    """
                    insert into card_type_translations values
                    (
                        :type_keyword,
                        :language,
                        :translation
                    )
                """,
                    [
                        {
                            "type_keyword": type_keyword,
                            "language": lang,
                            "translation": translation,
                        }
                        for type_keyword, translation in lang_type_data.items()
                    ],
                )

        db.execute(
            """
            create table cards
            (
                card_tag text not null primary key,
                types text not null,
                cardset_tags text,
                cost integer,
                group_tag text,
                randomizer integer
            )
        """
        )
        sorted_card_data = load_card_data(card_db_dir)
        for c in sorted_card_data:
            c["cardset_tags"] = json.dumps(sorted(c["cardset_tags"]))
            c["types"] = json.dumps(sorted(c["types"]))

        db.executemany(
            """
            insert into cards values
            (
                :card_tag,
                :types,
                :cardset_tags,
                :cost,
                :group_tag,
                :randomizer
            )
        """,
            [collections.defaultdict(lambda: None, c) for c in sorted_card_data],
        )

        groups = set(
            card["group_tag"] for card in sorted_card_data if "group_tag" in card
        )
        super_groups = set(["events", "landmarks", "projects"])

        # maintain the sorted order, but expand with groups and super_groups
        card_tags = [c["card_tag"] for c in sorted_card_data]
        card_tags.extend(sorted(groups))
        card_tags.extend(sorted(super_groups))

        print("Cards Tags:")
        print(card_tags)
        print()

        ###########################################################################
        # Fix up the sets_db.json file
        # Place entries in alphabetical order
        ###########################################################################
        db.execute(
            """
            create table sets
            (
                set_tag text not null primary key,
                edition text not null,
                image text not null,
                set_name_pattern text not null unique,
                is_fan_expansion integer default 0,
                no_randomizer integer default 0
            )
        """
        )

        lang_file = "sets_db.json"
        set_data = get_json_data(os.path.join(card_db_dir, lang_file))
        print([s["set_name"] for s in set_data.values()])
        db.executemany(
            """
            insert into sets values
            (
                :set_tag,
                :edition,
                :image,
                :set_name_pattern,
                :is_fan_expansion,
                :no_randomizer
            )
        """,
            [
                {
                    "set_tag": set_tag,
                    "edition": json.dumps(sorted(s["edition"])),
                    "image": s["image"],
                    "set_name_pattern": s["set_name"],
                    "is_fan_expansion": s.get("is_fan_expansion", False),
                    "no_randomizer": s.get("no_randomizer", False),
                }
                for set_tag, s in set_data.items()
            ],
        )
        print("Sets:")
        print(set(set_data))
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

        db.execute(
            """
            create table card_translations
            (
                card_tag text,
                name text default null,
                description text default "",
                extra text default "",
                language text not null,
                primary key (card_tag, language)
            )
        """
        )
        # would like to add 'foreign key (card_tag) references cards(card_tag)' above, but
        # need to change groups and other cards generated on the fly

        for lang in languages:
            print(f"updating cards for {lang}")
            #  contruct the cards json file name
            lang_data = load_language_cards(lang, card_db_dir)
            tags = set(lang_data)
            print(
                f"extra tags (from groups, etc): {tags - set(c['card_tag'] for c in sorted_card_data)}"
            )
            db.executemany(
                """
                insert into card_translations values
                (
                    :card_tag,
                    :name,
                    :description,
                    :extra,
                    :language
                )
            """,
                [
                    collections.defaultdict(
                        lambda: None, {"card_tag": card_tag, "language": lang, **v}
                    )
                    for card_tag, v in lang_data.items()
                ],
            )
        db.commit()
        ###########################################################################
        # Fix up all the xx/sets_xx.json files
        # Place entries in alphabetical order
        # If entries don't exist:
        #    If the default language, set from information in the "sets_db.json" file,
        #    If not the default language, set based on information from the default language.
        ###########################################################################

        db.execute(
            """
            create table set_translations
            (
                set_tag text not null,
                name text not null,
                description text,
                short_name text,
                text_icon text not null,
                language text not null,
                primary key (set_tag, language)
            )
            """
        )
        for lang in languages:
            lang_file = "sets_" + lang + ".json"
            fname = os.path.join(card_db_dir, lang, lang_file)
            lang_set_data = get_json_data(fname)
            db.executemany(
                """
                insert into set_translations values
                (
                    :set_tag,
                    :name,
                    :description,
                    :short_name,
                    :text_icon,
                    :language
                )
            """,
                [
                    {
                        "set_tag": set_tag,
                        "name": s["set_name"],
                        "description": s["set_text"],
                        "short_name": s.get("short_name"),
                        "text_icon": s["text_icon"],
                        "language": lang,
                    }
                    for set_tag, s in lang_set_data.items()
                ],
            )

        ###########################################################################
        # bonuses_xx files
        ###########################################################################
        db.execute(
            """
            create table bonuses
            (
                word text not null,
                include integer,
                language text not null
            )
        """
        )
        for lang in languages:
            # Special case for xx.  Reseed from default language
            fromLanguage = lang
            if lang == LANGUAGE_XX:
                fromLanguage = LANGUAGE_DEFAULT

            db.executemany(
                """
            insert into bonuses values
            (
                :word,
                :include,
                :language
            )
            """,
                [
                    {"word": word, "include": key == "include", "language": lang}
                    for key, vals in get_json_data(
                        os.path.join(
                            card_db_dir, fromLanguage, f"bonuses_{fromLanguage}.json"
                        )
                    ).items()
                    for word in vals
                ],
            )

    shutil.move("domdiv.db", os.path.join(output_dir, "domdiv.db"))


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
