#!/usr/bin/python3
# coding=utf-8

import csv
import sys
import json

new_cards_db = []
new_cards_en_us = {}

with open(sys.argv[1]) as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';', quotechar='"', escapechar='')
    # NOTE: csv file must be saved in UTF-8
    for card in reader:
        card_db_entry = {
            "card_tag": card["Card"].strip(),
            "cardset_tags": [
                s.strip() for s in card["Sets"].split(",")            
            ],
            "cost": card["Cost"].strip(),
            "types": [
                t.strip() for t in card["Types"].split(",")
            ],
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
                "description" : card["Description"].replace('\\"', '"').strip(),
                "extra" : card["Extra"].replace('\\"', '"').strip(),
                "name": name
            }

json.dump(new_cards_db, open("new_cards_db.json", "w"), indent=4)
json.dump(new_cards_en_us, open("new_cards_en_us.json", "w"), indent=4)
