import json
import re
from difflib import SequenceMatcher

import mwparserfromhell
import pyquery
import requests
from wikimarkup.parser import Parser

# File paths
CARDS_FILE = "../../../card_db_src/en_us/cards_en_us.json"
MERGED_OUTPUT = "merged_cards_en_us.json"
LOG_OUTPUT = "merge_log.json"

# MediaWiki API
WIKI_API = "https://wiki.dominionstrategy.com/api.php"
WIKI_PAGE = "List_of_cards"


def fetch_wikitext():
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": WIKI_PAGE,
        "rvslots": "main",
        "rvprop": "content",
        "format": "json",
        "formatversion": 2,
    }
    response = requests.get(WIKI_API, params=params)
    response.raise_for_status()
    return response.json()["query"]["pages"][0]["revisions"][0]["slots"]["main"][
        "content"
    ]


def convert_wiki_markup(text):
    """This whole function is obsolete"""
    if not text:
        return ""

    # The wiki separates paragraphs by enclosing them in <p>...</p> tags.
    # domdiv separates them by <n> strings which are converted to newlines, and then split.
    # Split on either opening or closing tags, remove empty strings, then join with <n>
    lines = re.split(r"</?p>", text)
    text = "<n>".join([l for l in lines if l])

    # The wiki sometimes uses &nbsp; to indicate nonbreaking spaces, and sometimes it uses a {{nowrap|text}} template.
    # &nbsp; is supported natively by reportlab, so we can leave it as is. I can't think of a good way at the moment
    # to represent the {{nowrap}} templates when there's no space involved, to e.g. ensure that something like
    # {{nowrap|-1 Coin token.}} keeps the minus sign, the 1 coin icon, the word token, and the period all on the same
    # line.
    # The best I can think of is to make all spaces inside nowrap tags into nonbreaking spaces.
    def nbsp_replacer(match):
        content = match.group(1)
        content_with_nbsp = content.replace(" ", "&nbsp;")
        return content_with_nbsp

    # Match {{nowrap|...}} and replace inner spaces
    text = re.sub(r"{{nowrap\|([^{}]+?)}}", nbsp_replacer, text)

    # I think the <nobr> tags would work. Need to figure out a regex that can handle {{nowrap|-{{Cost|1}} token.}}

    # Convert cost and other icons
    text = re.sub(r"{{[Cc]ostplus?\|(1)}}", r"+\1 Coin", text)
    text = re.sub(r"{{[Cc]ostplus?\|([-0-9]+)}}", r"+\1 Coins", text)
    text = re.sub(r"{{[Cc]ost?\|(1)}}", r"\1 Coin", text)
    text = re.sub(r"{{[Cc]ost?\|([-0-9]+)}}", r"\1 Coins", text)
    text = re.sub(r"{{[Cc]ost?\|([-0-9]+)\|x?l}}", r"\1 <*COIN*>", text)
    text = re.sub(r"{{[Cc]ost\|\|\|\|P}}", r"Potion", text)
    text = re.sub(r"{{VP\|'''([-0-9]+)'''}}", r"\1 <VP>", text)
    text = re.sub(r"{{VP\|([-0-9]+)\|x?l}}", r"\1 <*VP*>", text)

    text = re.sub(r"'''([^']+)'''", r"<b>\1</b>", text)
    text = re.sub(r"''([^']+)''", r"<i>\1</i>", text)
    text = re.sub(r"{{[Dd]ivline}}", "<line>", text)

    # Unwrap nowrap tags that had nested {{}} in them that were just substituted
    text = re.sub(r"{{nowrap\|([^{}]+?)}}", r"\1", text)

    # text = text.replace("'''", "")  # bold
    # text = text.replace("''", "")   # italics
    # text = text.replace("&nbsp;", " ")

    # text = re.sub(r"\{!(\d+)\}", r"\1 <*VP*>", text)
    # text = re.sub(r"\{(\d+)\}", r"\1 <VP>", text)

    # text = re.sub(r"\[?(\d+)[ ]*[Cc]oin[s]?\]?", r"\1 <*COIN*>", text)
    # text = re.sub(r"\[?([Xx\?]) [Cc]oin[s]?\]?", r"\1 <*COIN*>", text)
    # text = text.replace("[P]", "Potion")

    # Paragraph and line breaks
    # text = text.replace("<p>", "<br>")
    # text = re.sub(r"</?[^>]+>", "", text)
    # text = text.replace("////", "<br>")
    # text = re.sub(r"(?<!/)//(?!/)", " ", text)
    # text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def extract_cards_from_wikitext(wikitext):
    cards = {}
    lines = wikitext.split("\n")
    for line in lines:
        if line.startswith("|{"):
            columns = line.split(" || ")
            if len(columns) < 5:
                continue
            name_match = re.search(r"{{[^|]+\|([^}]+)}}", columns[0])
            if not name_match:
                continue
            name = name_match.group(1).strip()
            raw_text = columns[4].strip()
            converted_text = convert_wiki_markup(raw_text)
            cards[name] = {"converted": converted_text, "raw": raw_text}
    return cards


def load_existing_cards(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_cards(existing_cards, wiki_cards):
    updated = existing_cards.copy()
    updated_count = 0
    unchanged_count = 0
    applied_changes = {}
    skipped_changes = {}
    cards_to_skip = {
        # 'Astrolabe',    # Needs extra <br> for the large coin image
    }

    for name, wiki_entry in wiki_cards.items():
        new_text = wiki_entry["converted"]
        raw = wiki_entry["raw"]
        if name in updated and "description" in updated[name]:
            original = updated[name]["description"].strip()
            similarity = SequenceMatcher(None, original, new_text).ratio()
            if name not in cards_to_skip and similarity < 1.02:
                applied_changes[name] = {
                    "original": original,
                    "updated": new_text,
                    "raw_wikitext": raw,
                    "similarity": round(similarity, 4),
                }
                updated[name]["raw_wikitext"] = raw
                updated[name]["wikitext"] = new_text
                updated_count += 1
            else:
                updated[name]["raw_wikitext"] = raw
                updated[name]["wikitext"] = new_text
                skipped_changes[name] = {
                    "original": original,
                    "converted": new_text,
                    "raw_wikitext": raw,
                    "similarity": round(similarity, 4),
                }
                unchanged_count += 1
        else:
            updated[name] = {
                "name": name,
                "description": new_text,
                "raw_wikitext": raw,
            }
            applied_changes[name] = {
                "original": None,
                "updated": new_text,
                "raw_wikitext": raw,
                "similarity": 0,
            }
            updated_count += 1

    return updated, updated_count, unchanged_count, applied_changes, skipped_changes


def main():
    print("Fetching wikitext...")
    wikitext = fetch_wikitext()

    print("Parsing card rows...")
    wiki_cards = extract_cards_from_wikitext(wikitext)
    print(f"Found {len(wiki_cards)} cards with descriptions.")

    print("Loading existing cards...")
    existing_cards = load_existing_cards(CARDS_FILE)

    print("Merging data...")
    merged, updated_count, unchanged_count, applied, skipped = merge_cards(
        existing_cards, wiki_cards
    )

    print("Writing merged cards...")
    with open(MERGED_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=4, ensure_ascii=False)

    print("Writing change log...")
    log = {
        "updated_count": updated_count,
        "unchanged_count": unchanged_count,
        "applied_changes": applied,
        "skipped_changes": skipped,
    }
    with open(LOG_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)

    print(f"Done. {updated_count} cards updated, {unchanged_count} unchanged.")


if __name__ == "__main__":
    main()
