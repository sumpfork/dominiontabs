import argparse
import collections
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("en_card_file")
    parser.add_argument("other_card_file")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    with open(args.en_card_file) as f:
        en_contents = json.load(f)
    with open(args.other_card_file) as f:
        other_contents = json.load(f)
    trimmed = {}
    trimmed_counts = collections.Counter()

    for card_name, card_spec in other_contents.items():
        matched = en_contents[card_name]
        new_card_spec = {}
        for key in ["description", "extra", "name"]:
            entry = card_spec.get(key)
            if entry is not None and entry != matched[key]:
                new_card_spec[key] = entry
            else:
                trimmed_counts[key] += 1
        if new_card_spec:
            trimmed[card_name] = new_card_spec

    print(f"trimmed: {trimmed_counts}")
    print(f"{len(trimmed)} cards left of {len(other_contents)}")
    print(f"{len(trimmed)} cards (partially) translated of {len(en_contents)}")

    if args.write:
        with open(args.other_card_file, "wt", encoding="utf-8") as outf:
            json.dump(trimmed, outf, indent=4, ensure_ascii=False)
            outf.write("\n")


if __name__ == "__main__":
    main()
