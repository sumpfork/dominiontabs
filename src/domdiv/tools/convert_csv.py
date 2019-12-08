# coding=utf-8

import csv
import sys
import json

converted = []

typemap = {
    "Aktion": "Action",
    "Geld": "Treasure",
    "Fluch": "Curse",
    "Punkte": "Victory",
    "Reaktion": "Reaction",
    "Angriff": "Attack",
    "Dauer": "Duration",
    "Plündern": "Looter",
    "Ritter": "Knight",
    "Ruine": "Ruins",
    "Unterschlupf": "Shelter",
    "Reisender": "Traveller",
    "Reserve": "Reserve",
}

with open(sys.argv[1], "U") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        if not row["Typ"]:
            continue
        # row = {k: v.decode('ISO-8859-2').encode('utf-8') if type(v) == str else v for k, v in row.iteritems()}
        # print chardet.detect(row['Kartentext'])
        if "Ritter" in row["Typ"] and row["Kartenname"] != "Ritter":
            continue
        converted_row = {
            "name": row["Kartenname"],
            "cost": row["Kosten"],
            "cardset": row["Edition"],
            "description": row["Kartentext"],
            "extra": row["Lange Erklärung"],
            "types": [
                typemap[t.strip()]
                for t in row["Typ"].split("/")
                if not t.strip() == "Ritter"
            ],
            "potcost": row.get("potcost", 0),
        }
        converted.append(converted_row)
json.dump(converted, open(sys.argv[2], "wb"), indent=True)
