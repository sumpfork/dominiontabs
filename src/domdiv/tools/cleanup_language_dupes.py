import argparse
import collections
import json
import os


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("card_db_src_dir")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    with open(os.path.join(args.card_db_src_dir, "en_us/cards_en_us.json")) as f:
        en_contents = json.load(f)

    for fname in os.listdir(args.card_db_src_dir):
        if fname not in ["en_us", "xx"] and os.path.isdir(
            os.path.join(args.card_db_src_dir, fname)
        ):
            print(f"processing {fname}")
            full_fname = os.path.join(
                args.card_db_src_dir, fname, f"cards_{fname}.json"
            )
            with open(full_fname) as f:
                other_contents = json.load(f)
            trimmed = {}
            trimmed_counts = collections.Counter()

            for card_name, card_spec in other_contents.items():
                matched = en_contents.get(card_name)
                if matched is None:
                    print(f"warning - leaving {card_name} as it doesn't exist in en_us")
                    trimmed[card_name] = card_spec
                    continue
                new_card_spec = {}
                for key in ["description", "extra", "name"]:
                    entry = card_spec.get(key)
                    if entry is not None and entry != matched[key]:
                        new_card_spec[key] = entry
                    else:
                        trimmed_counts[key] += 1
                # do not remove name if something else is translated
                if (
                    "name" in card_spec
                    and "name" not in new_card_spec
                    and len(set(new_card_spec) - {"name"}) > 0
                ):
                    new_card_spec["name"] = card_spec["name"]
                    trimmed_counts["name"] -= 1
                if new_card_spec:
                    # preserve other keys
                    for other_key in set(card_spec) - {"name", "description", "extra"}:
                        new_card_spec[other_key] = card_spec[other_key]
                    trimmed[card_name] = new_card_spec

            print(f"trimmed: {dict(trimmed_counts)}")
            print(f"{len(trimmed)} cards left of {len(other_contents)}")
            print(f"{len(trimmed)} cards (partially) translated of {len(en_contents)}")

            if args.write:
                with open(full_fname, "wt", encoding="utf-8") as outf:
                    json.dump(trimmed, outf, indent=4, ensure_ascii=False)
                    outf.write("\n")
                print("rewrote contents")

            print()


if __name__ == "__main__":
    main()
