import os
import codecs
import json
import sys
import io
import csv
from shutil import copyfile

LANGUAGE_DEFAULT = "en_us"  # default language, which takes priority
LANGUAGE_XX = "xx"  # language for starting a translation

card_db_dir = os.path.join("..", "domdiv", "card_db")  # directory of card data
output_dir = os.path.join(".", "card_db")  # directory for output data
crossReference = "./CrossReference"

if len(sys.argv) > 1:
    LANGUAGE_NEW = sys.argv[1].strip().lower()
else:
    print("Usage: ", sys.argv[0], " xx")
    print("where xx is the two letter language abreviation.")
    sys.exit()


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [cell.decode("iso-8859-15") for cell in row]


def get_json_data(json_file_path):
    # Read in the json from the specified file
    with codecs.open(json_file_path, "r", "utf-8") as json_file:
        data = json.load(json_file)
    assert data, "Could not load json at: '%r' " % json_file_path
    return data


def json_dict_entry(entry, separator=""):
    #  Return a nicely formated json dict entry.
    #  It does not include the enclosing {} and removes trailing white space
    json_data = json.dumps(entry, indent=4, ensure_ascii=False, sort_keys=True)
    json_data = json_data.strip(
        "{}"
    ).rstrip()  # Remove outer{} and then trailing whitespace
    return separator + json_data


def find_index(items, find):
    if find in items:
        return items.index(find)
    else:
        return None


reader = unicode_csv_reader(open(crossReference + ".csv"))
cards = list(reader)
headers = cards[0]

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

lang_dir = os.path.join(output_dir, LANGUAGE_NEW)
if not os.path.exists(lang_dir):
    os.makedirs(lang_dir)

for f in ["bonuses_", "cards_", "sets_", "types_"]:
    copyfile(
        os.path.join(card_db_dir, LANGUAGE_XX, f + LANGUAGE_XX + ".json"),
        os.path.join(output_dir, LANGUAGE_NEW, f + LANGUAGE_NEW + ".json"),
    )


lang_index = find_index(headers, LANGUAGE_NEW)
card_index = find_index(headers, "card_tag")

if lang_index is None or card_index is None:
    print("Cound not find new language '", LANGUAGE_NEW, "' in the CrossReference file")
    print("Files copied, but no name changes were made.")
    sys.exit()

# Get the new names for those in the CrossReference
cardlist = {}
for row in cards:
    if row[lang_index]:
        cardlist[row[card_index]] = row[lang_index]

# Update the names based upon names in the cross reference file
fname = os.path.join(card_db_dir, LANGUAGE_XX, "cards_" + LANGUAGE_XX + ".json")
if os.path.isfile(fname):
    lang_data = get_json_data(fname)
else:
    print("ERROR: Failed to open :", fname)
    sys.exit()

if cardlist:
    with io.open(
        os.path.join(output_dir, LANGUAGE_NEW, "cards_" + LANGUAGE_NEW + ".json"),
        "w",
        encoding="utf-8",
    ) as lang_out:

        lang_out.write("{")  # Start of set
        sep = ""

        for card in lang_data:
            # print card, lang_data[card]
            data = lang_data[card]
            if card in cardlist:
                # Have a new name, so update name
                data["name"] = cardlist[card]
                fields = ["description", "extra"]  # but no u"name"
                data["untranslated"] = fields
            lang_out.write(json_dict_entry({card: data}, sep))
            sep = ","
        lang_out.write("\n}\n")  # End of Set
