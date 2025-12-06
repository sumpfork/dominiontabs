###########################################################################
# Updates the json files in card_db_src to use consistent naming conventions for the card tags.
# Before this change, most cards from Allies used a different format for the card tag than the
# english card name, which is what all other sets used. This cleans that up, and a few others.
#
# All output is in the designated output directory.  Original files are not overwritten.
###########################################################################

import argparse
import os

from domdiv.tools.common import (
    LANGUAGE_DEFAULT,
    get_json_data,
    get_languages,
    load_language_cards,
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

    card_data = get_json_data(os.path.join(card_db_dir, "cards_db.json"))
    card_data_by_tag = {d["card_tag"]: d for d in card_data}
    default_lang_card_data = get_json_data(
        os.path.join(card_db_dir, LANGUAGE_DEFAULT, f"cards_{LANGUAGE_DEFAULT}.json")
    )

    renames = {}
    for tag, data in default_lang_card_data.items():
        if tag in card_data_by_tag and tag != data["name"]:
            if tag in ["Harem", "Start Deck"]:
                continue
            renames[tag] = data["name"]

    def rename_card_tag(card_data: dict) -> dict:
        if card_data["card_tag"] in renames:
            card_data["card_tag"] = renames[card_data["card_tag"]]
        return card_data

    renamed_card_data = [rename_card_tag(d) for d in card_data]

    write_data(
        renamed_card_data, os.path.join(output_dir, "cards_db.json"), do_gzip=False
    )

    for lang in languages:
        lang_data = load_language_cards(lang, card_db_dir)
        renamed_lang_data = {renames.get(k) or k: v for k, v in lang_data.items()}

        write_language_cards(renamed_lang_data, lang, output_dir, do_gzip=False)


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
