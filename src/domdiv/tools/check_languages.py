import sys

from domdiv.tools.common import get_languages, load_language_cards


def check_languages(card_db_dir):
    languages = get_languages(card_db_dir)
    for lang in languages:
        _ = load_language_cards(lang, card_db_dir)


if __name__ == "__main__":
    check_languages(sys.argv[1])
