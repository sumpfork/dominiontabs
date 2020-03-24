#!/usr/bin/python3
# coding=utf-8

import csv
import json
import argparse


def parse_opts(cmdline_args=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="""From a CSV file containing card information, generate JSON code that can be added
                       to the cards_db.json and /en_us/cards_en_us.json files.
                       Column headings used include:
                       "Sets";"Card";"Cost";"Count";"Randomizer";"Types";"Group";"Description";"Extra".

                       "Sets" and "Types" are each a comma separated list.
                       A value for "Cost" is only needed if it is different from the default for the card Type.
                       "Randomizer" should contain an 'N' if the card has no randomizer.
                       A blank "Sets" field will add the "Card", "Description", and "Extra" to the
                       cards_en_us.json file, but no entry will be added to the cards_db.json file.

                       If "Group" is used, this should be a unique card name value for the group.
                       Cards with the same "Group" value will be group together with --special-card-groups.
                       A row should then be added with a blank "Sets" with this group value as a "Card" to include
                       the text values for the tab used by the group.
        """,
        epilog="Source can be found at 'https://github.com/sumpfork/dominiontabs'. ",
    )
    parser.add_argument(
        "csv",
        help='input CSV file saved in UTF-8 format with ";" as the column seperator.',
    )

    # Basic Divider Information
    group_basic = parser.add_argument_group(
        "Output File Options", "Specify output files."
    )
    group_basic.add_argument(
        "--cards_db",
        "--db",
        dest="cards_db",
        default="new_cards_db.json",
        help="The card db output file name.",
    )
    group_basic.add_argument(
        "--cards_text",
        "--text",
        dest="cards_text",
        default="new_cards_en_us.json",
        help="The card text output file name.",
    )
    options = parser.parse_args(args=cmdline_args)
    return options


def clean_opts(options):
    # None for now
    return options


def generate(options):
    new_cards_db = []
    new_cards_en_us = {}

    with open(options.csv) as csvfile:
        reader = csv.DictReader(csvfile, delimiter=";", quotechar='"', escapechar="")
        # NOTE: csv file must be saved in UTF-8
        for card in reader:
            card_db_entry = {
                "card_tag": card["Card"].strip(),
                "cardset_tags": [s.strip() for s in card["Sets"].split(",")],
                "cost": card["Cost"].strip(),
                "types": [t.strip() for t in card["Types"].split(",")],
            }

            if card["Randomizer"]:
                if "N" in card["Randomizer"].upper():
                    card_db_entry["randomizer"] = False
            if card["Count"]:
                card_db_entry["count"] = card["Count"].strip()
            if card["Group"]:
                card_db_entry["group_tag"] = card["Group"].strip()

            if card["Sets"]:
                # Add this card to the db
                new_cards_db.append(card_db_entry)
                # For Text, use Card as the Name of the Card
                name = card["Card"].strip()
            else:
                # Skip cards without a set. These are created in program, but they need text.
                # For Text, use what is in the Group column for the Name of the Card
                name = card["Group"].strip()

            new_cards_en_us[card["Card"]] = {
                "description": card["Description"].replace('\\"', '"').strip(),
                "extra": card["Extra"].replace('\\"', '"').strip(),
                "name": name,
            }

    json.dump(new_cards_db, open(options.cards_db, "w"), indent=4)
    json.dump(new_cards_en_us, open(options.cards_text, "w"), indent=4)


def main():
    options = parse_opts()
    options = clean_opts(options)
    generate(options)


if __name__ == "__main__":
    main()
