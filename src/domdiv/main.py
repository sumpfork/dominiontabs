import fnmatch
import json
import os
import sys
import unicodedata
from collections import Counter, defaultdict

from loguru import logger
from reportlab.lib.units import cm

from . import config_options, db
from .cards import Card
from .draw import DividerDrawer

try:
    from icu import Collator, Locale

    have_icu = True
except ImportError:
    have_icu = False


def generate_sample(options):
    from io import BytesIO

    from wand.image import Image

    buf = BytesIO()
    options.num_pages = 1
    options.outfile = buf
    generate(options)
    sample_out = BytesIO()
    with Image(blob=buf.getvalue(), resolution=options.preview_resolution) as sample:
        sample.format = "png"
        sample.save(sample_out)
        return sample_out.getvalue()


class CardSorter(object):
    def __init__(self, order, lang, baseCards):
        self.order = order

        # If PyICU has been successfully imported
        if have_icu:
            # Create a sort collator based on the selected language. Will be used the generate the sort keys.
            self.collator = Collator.createInstance(Locale(lang))
        else:
            logger.warning(
                "PyICU library not found. The dividers will be ordered by default sort key (might not be the "
                "correct alphabetical order for the selected language)."
            )

            self.collator = None

        if order == "global":
            self.sort_key = self.by_global_sort_key
        elif order == "colour":
            self.sort_key = self.by_colour_sort_key
        elif order == "cost":
            self.sort_key = self.by_cost_sort_key
        else:
            self.sort_key = self.by_expansion_sort_key

        self.baseOrder = [
            "Copper",
            "Silver",
            "Gold",
            "Platinum",
            "Potion",
            "Curse",
            "Estate",
            "Duchy",
            "Province",
            "Colony",
            "Trash",
            "Start Deck",
        ]
        self.baseCards = []
        for tag in self.baseOrder:
            if tag in baseCards:
                self.baseCards.append(baseCards[tag])
                del baseCards[tag]
        # now pick up those that have not been specified
        for tag in baseCards:
            self.baseCards.append(baseCards[tag])

    # When sorting cards, want to always put "base" cards after all
    # kingdom cards, and order the base cards in a particular order
    # (ie, all normal treasures by worth, then potion, then all
    # normal VP cards by worth, then Trash)
    def baseIndex(self, name):
        try:
            return self.baseCards.index(name)
        except Exception:
            return -1

    def isBaseExpansionCard(self, card):
        return card.cardset_tag.lower() != "base" and card.name in self.baseCards

    def by_global_sort_key(self, card):
        return (
            int(card.isExpansion()),
            self.baseIndex(card.name),
            self.get_card_name_sort_key(card.name),
        )

    def by_expansion_sort_key(self, card):
        return (
            card.cardset,
            int(card.isExpansion()),
            self.baseIndex(card.name),
            self.get_card_name_sort_key(card.name),
        )

    def by_colour_sort_key(self, card):
        return card.getType().getTypeNames(), self.get_card_name_sort_key(card.name)

    def by_cost_sort_key(self, card):
        return (
            card.cardset,
            int(card.isExpansion()),
            str(card.get_total_cost(card)),
            self.get_card_name_sort_key(card.name),
        )

    def get_card_name_sort_key(self, c):
        if (
            self.collator
        ):  # If the PyICU collator attribute has been set up, get the collator based sort key
            return self.collator.getSortKey(c)
        else:  # Default method: strip the card name character accents
            return self.strip_accents(c)

    @staticmethod
    def strip_accents(s):
        return "".join(
            c
            for c in unicodedata.normalize("NFD", s)
            if unicodedata.category(c) != "Mn"
        )

    def __call__(self, card):
        return self.sort_key(card)


def add_card_text(cards, language="en_us"):
    language = language.lower()
    # Read in the card text file
    card_text_filepath = os.path.join(
        "card_db", language, "cards_" + language.lower() + ".json.gz"
    )
    with db.get_resource_stream(card_text_filepath) as card_text_file:
        card_text = json.loads(card_text_file.read().decode("utf-8"))
    assert language, "Could not load card text for %r" % language

    # Now apply to all the cards
    for card in cards:
        if card.card_tag in card_text:
            if "name" in card_text[card.card_tag].keys():
                card.name = card_text[card.card_tag]["name"]
            if "description" in card_text[card.card_tag].keys():
                card.description = card_text[card.card_tag]["description"]
            if "extra" in card_text[card.card_tag].keys():
                card.extra = card_text[card.card_tag]["extra"]
    return cards


def add_set_text(options, sets, language="en_us"):
    language = language.lower()
    # Read in the set text and store for later
    set_text_filepath = os.path.join("card_db", language, f"sets_{language}.json.gz")
    with db.get_resource_stream(set_text_filepath) as set_text_file:
        set_text = json.loads(set_text_file.read().decode("utf-8"))
    assert set_text, "Could not load set text for %r" % language

    # Now apply to all the sets
    for s in sets:
        if s in set_text:
            for key in set_text[s]:
                sets[s][key] = set_text[s][key]
    return sets


def add_type_text(types=None, language="en_us"):
    if types is None:
        types = {}
    language = language.lower()
    # Read in the type text and store for later
    type_text_filepath = os.path.join("card_db", language, f"types_{language}.json.gz")
    with db.get_resource_stream(type_text_filepath) as type_text_file:
        type_text = json.loads(type_text_file.read().decode("utf-8"))
    assert type_text, "Could not load type text for %r" % language

    # Now apply to all the types
    used = {}
    for type in types:
        if type in type_text:
            types[type] = type_text[type]
            used[type] = True

    for type in type_text:
        if type not in used:
            types[type] = type_text[type]

    return types


def add_bonus_regex(options, language="en_us"):
    language = language.lower()
    # Read in the bonus regex terms
    bonus_regex_filepath = os.path.join(
        "card_db", language, f"bonuses_{language}.json.gz"
    )
    with db.get_resource_stream(bonus_regex_filepath) as bonus_regex_file:
        bonus_regex = json.loads(bonus_regex_file.read().decode("utf-8"))
    assert bonus_regex, "Could not load bonus keywords for %r" % language

    if not bonus_regex:
        bonus_regex = {}

    return bonus_regex


def combine_cards(cards, old_card_type, new_card_tag, new_cardset_tag, new_type):
    holder = Card(
        name="*Replace Later*",
        card_tag=new_card_tag,
        group_tag=new_card_tag,
        cardset_tag=new_cardset_tag,
        types=(new_type,),
        count=0,
    )
    holder.image = holder.setImage()

    filteredCards = []
    for c in cards:
        if c.isType(old_card_type):
            holder.addCardCount(c.count)  # keep track of count and skip card
        else:
            filteredCards.append(c)  # Not the right type, keep card

    if holder.getCardCount() > 0:
        filteredCards.append(holder)

    return filteredCards


def filter_sort_cards(cards, options):
    # Filter out cards by edition
    if options.edition and options.edition != "all":
        keep_sets = []
        for set_tag in Card.sets:
            for edition in Card.sets[set_tag]["edition"]:
                if options.edition == edition:
                    keep_sets.append(set_tag)

        keep_cards = []  # holds the cards that are to be kept
        for card in cards:
            if card.cardset_tag in keep_sets:
                keep_cards.append(card)

        cards = keep_cards

    # Combine upgrade cards with their expansion
    if options.upgrade_with_expansion:
        if options.exclude_expansions is None:
            options.exclude_expansions = []
        for card in cards:
            if Card.sets[card.cardset_tag]["upgrades"]:
                options.exclude_expansions.append(card.cardset_tag.lower())
                card.cardset_tag = Card.sets[card.cardset_tag]["upgrades"]

    # Combine globally all cards of the given types
    # For example, Events, Landmarks, Projects, Ways, Traits
    if options.group_global:
        # First find all possible types to group that match options.group_global
        types_to_group = {}
        for t in Card.types:
            group_global_type = Card.types[t].getGroupGlobalType()
            if group_global_type:
                theType = "-".join(t)
                # Save if either the old or the new type matches the option
                # Remember options.global_group is already lowercase
                if theType.lower() in options.group_global:
                    types_to_group[theType] = group_global_type
                elif group_global_type.lower() in options.group_global:
                    types_to_group[theType] = group_global_type

        # Now work through the matching types to group
        for t in types_to_group:
            cards = combine_cards(
                cards,
                old_card_type=t,
                new_type=types_to_group[t],
                new_card_tag=types_to_group[t].lower(),
                new_cardset_tag=config_options.EXPANSION_GLOBAL_GROUP,
            )
        if options.expansions:
            options.expansions.append(config_options.EXPANSION_GLOBAL_GROUP)

    # Take care of any blank cards
    if options.include_blanks > 0:
        if options.expansions:
            options.expansions.append(config_options.EXPANSION_GLOBAL_GROUP)

    # Group all the special cards together
    if options.group_special:
        keep_cards = []  # holds the cards that are to be kept
        group_cards = {}  # holds the cards for each group
        for card in cards:
            if not card.group_tag:
                keep_cards.append(card)  # not part of a group, so just keep the card
            else:
                # have a card in a group
                if (card.group_tag, card.cardset_tag) not in group_cards:
                    # First card of a group
                    group_cards[(card.group_tag, card.cardset_tag)] = (
                        card  # save to update cost later
                    )
                    # this card becomes the card holder for the whole group.
                    card.card_tag = card.group_tag
                    # These text fields should be updated later if there is a translation for this group_tag.
                    error_msg = (
                        "ERROR: Missing language entry for group_tab '%s'."
                        % card.group_tag
                    )
                    card.name = (
                        card.group_tag
                    )  # For now, change the name to the group_tab
                    card.description = error_msg
                    card.extra = error_msg
                    if card.get_GroupCost():
                        card.cost = card.get_GroupCost()
                    # now save the card
                    keep_cards.append(card)
                else:
                    # subsequent cards in the group. Update group info, but don't keep the card.
                    if card.group_top:
                        # this is a designated card to represent the group, so update important data
                        group_cards[(card.group_tag, card.cardset_tag)].cost = card.cost
                        group_cards[(card.group_tag, card.cardset_tag)].potcost = (
                            card.potcost
                        )
                        group_cards[(card.group_tag, card.cardset_tag)].debtcost = (
                            card.debtcost
                        )
                        group_cards[(card.group_tag, card.cardset_tag)].types = (
                            card.types
                        )
                        group_cards[(card.group_tag, card.cardset_tag)].randomizer = (
                            card.randomizer
                        )
                        group_cards[(card.group_tag, card.cardset_tag)].image = (
                            card.image
                        )

                    group_cards[(card.group_tag, card.cardset_tag)].addCardCount(
                        card.count
                    )  # increase the count
                    # set holder to lowest cost of the two cards
                    # group_cards[(card.group_tag, card.cardset_tag)].set_lowest_cost(card)

        cards = keep_cards

        # Now fix up card costs for groups by Type (Events, Landmarks, etc.)
        for card in cards:
            if (card.card_tag, card.cardset_tag) in group_cards and group_cards[
                (card.group_tag, card.cardset_tag)
            ].get_GroupCost():
                group_cards[(card.group_tag, card.cardset_tag)].cost = group_cards[
                    (card.group_tag, card.cardset_tag)
                ].get_GroupCost()
                group_cards[(card.group_tag, card.cardset_tag)].debtcost = 0
                group_cards[(card.group_tag, card.cardset_tag)].potcost = 0

    # Get the final type names in the requested language
    Card.type_names = add_type_text(Card.type_names, db.LANGUAGE_DEFAULT)
    if options.language != db.LANGUAGE_DEFAULT:
        Card.type_names = add_type_text(Card.type_names, options.language)
    for card in cards:
        card.types_name = " - ".join([Card.type_names[t] for t in card.types])

    # Get the card bonus keywords in the requested language
    bonus = add_bonus_regex(options, db.LANGUAGE_DEFAULT)
    Card.addBonusRegex(bonus)
    if options.language != db.LANGUAGE_DEFAULT:
        bonus = add_bonus_regex(options, options.language)
        Card.addBonusRegex(bonus)

    # Fix up cardset text.  Waited as long as possible.
    Card.sets = add_set_text(options, Card.sets, db.LANGUAGE_DEFAULT)
    if options.language != db.LANGUAGE_DEFAULT:
        Card.sets = add_set_text(options, Card.sets, options.language)

    # Split out Official and Fan set information
    Official_sets = set()  # Will hold official sets
    Official_search = (
        []
    )  # Will hold official sets for searching, both set key and set_name
    Fan_sets = set()  # Will hold fan sets
    Fan_search = []  # Will hold fan sets for searching, both set key and set_name
    wantedSets = set()  # Will hold all the sets requested for printing

    All_search = []  # Will hold all sets for searching, both set key and set_name
    for s in Card.sets:
        search_items = [s.lower(), Card.sets[s].get("set_name", None).lower()]
        All_search.extend(search_items)
        if Card.sets[s].get("fan", False):
            # Fan Expansion
            Fan_sets.add(s)
            Fan_search.extend(search_items)
        else:
            # Official Expansion
            Official_sets.add(s)
            Official_search.extend(search_items)

    # If expansion names given, then find out which expansions are requested
    # Expansion names can be the names from the language or the cardset_tag
    if options.expansions:
        # Expand out any wildcards, matching set key or set name in the given language
        expanded_expansions = []
        for e in options.expansions:
            matches = fnmatch.filter(Official_search, e)
            if matches:
                expanded_expansions.extend(matches)
            else:
                expanded_expansions.append(e)

        # Now get the actual sets that are matched above
        options.expansions = set(
            [e.lower() for e in expanded_expansions]
        )  # Remove duplicates
        knownExpansions = set()
        for e in options.expansions:
            for s in Official_sets:
                if s.lower() == e or Card.sets[s].get("set_name", "").lower() == e:
                    wantedSets.add(s)
                    knownExpansions.add(e)
        # Give indication if an imput did not match anything
        unknownExpansions = options.expansions - knownExpansions
        if unknownExpansions:
            logger.warning((f"Unknown expansion(s): {', '.join(unknownExpansions)}"))

    # Take care of fan expansions.  Fan expansions must be explicitly named to be added.
    # If no --fan is given, then no fan cards are added.
    # Fan expansion names can be the names from the language or the cardset_tag
    if options.fan:
        # Expand out any wildcards, matching set key or set name in the given language
        expanded_expansions = []
        for e in options.fan:
            matches = fnmatch.filter(Fan_search, e)
            if matches:
                expanded_expansions.extend(matches)
            else:
                expanded_expansions.append(e)

        # Now get the actual sets that are matched above
        options.fan = set([e.lower() for e in expanded_expansions])  # Remove duplicates
        knownExpansions = set()
        for e in options.fan:
            for s in Fan_sets:
                if s.lower() == e or Card.sets[s].get("set_name", "").lower() == e:
                    wantedSets.add(s)
                    knownExpansions.add(e)
        # Give indication if an imput did not match anything
        unknownExpansions = options.fan - knownExpansions
        if unknownExpansions:
            logger.warning(
                (f"Unknown fan expansion(s): {', '.join(unknownExpansions)}")
            )

    if options.exclude_expansions:
        # Expand out any wildcards, matching set key or set name in the given language
        expanded_expansions = []
        for e in options.exclude_expansions:
            matches = fnmatch.filter(All_search, e)
            if matches:
                expanded_expansions.extend(matches)
            else:
                expanded_expansions.append(e)

        # Now get the actual sets that are matched above
        options.exclude_expansions = set(
            [e for e in expanded_expansions]
        )  # Remove duplicates
        knownExpansions = set()
        for e in options.exclude_expansions:
            for s in Card.sets:
                if s.lower() == e or Card.sets[s].get("set_name", "").lower() == e:
                    wantedSets.discard(s)
                    knownExpansions.add(e)
        # Give indication if an imput did not match anything
        unknownExpansions = options.exclude_expansions - knownExpansions
        if unknownExpansions:
            logger.warning(
                f"Unknown exclude expansion(s): {', '.join(unknownExpansions)}"
            )

    # Now keep only the cards that are in the sets that have been requested
    keep_cards = []
    for c in cards:
        if c.cardset_tag in wantedSets:
            if options.group_kingdom:
                # Separate non-Kingdom cards (without Randomizer) into new "Extras" set
                if not c.randomizer and Card.sets[c.cardset_tag]["has_extras"]:
                    c.cardset_tag += db.EXPANSION_EXTRA_POSTFIX
            # Add the cardset informaiton to the card and add it to the list of cards to use
            c.cardset = Card.sets[c.cardset_tag].get("set_name", c.cardset_tag)
            keep_cards.append(c)
    cards = keep_cards

    # Now add text to the cards.  Waited as long as possible to catch all groupings
    cards = add_card_text(cards, options.language)

    # Get list of cards from a file
    if options.cardlist:
        cardlist = set()
        cardlist_exclude = set()
        with open(options.cardlist) as cardfile:
            for line in cardfile:
                line = line.strip()
                if not line or line.startswith("#"):
                    pass  # ignore empty and "comment" lines
                elif line.startswith("-"):
                    cardlist_exclude.add(line.lstrip("- \t"))
                else:
                    cardlist.add(line.lstrip("+ \t"))
        if cardlist_exclude:
            cards = [card for card in cards if card.name not in cardlist_exclude]
        if cardlist:
            cards = [card for card in cards if card.name in cardlist]

    # Set up the card sorter
    cardSorter = CardSorter(
        options.order,
        options.language,
        {
            card.card_tag: card.name
            for card in cards
            if "base" in [set_name.lower() for set_name in card.cardset_tags]
        },
    )

    # Optionally remove base cards from expansions that have them
    if not options.base_cards_with_expansion:
        cards = [card for card in cards if not cardSorter.isBaseExpansionCard(card)]

    # Add expansion divider
    if options.expansion_dividers:
        cardnamesByExpansion = defaultdict(dict)
        randomizerCountByExpansion = Counter()
        for c in cards:
            if c.isBlank() or (
                cardSorter.isBaseExpansionCard(c)
                and not options.base_cards_with_expansion
            ):
                continue
            if c.randomizer:
                randomizerCountByExpansion[c.cardset] += 1

            if c.card_tag in cardnamesByExpansion[c.cardset]:
                # Already have one, so just update the count (for extra Curses, Start Decks, etc)
                cardnamesByExpansion[c.cardset][c.card_tag]["count"] += 1
            else:
                # New, so save off information about the card to be used on the expansion divider
                order = 0
                if c.card_tag in cardSorter.baseOrder:
                    # Use the base card ordering
                    order = 100 + cardSorter.baseOrder.index(c.card_tag)
                cardnamesByExpansion[c.cardset][c.card_tag] = {
                    "name": c.name.strip().replace(" ", "&nbsp;"),
                    "randomizer": c.randomizer,
                    "count": 1,
                    "sort": "%03d%s"
                    % (
                        order,
                        cardSorter.get_card_name_sort_key(c.name.strip()),
                    ),
                }

        for set_tag, set_values in Card.sets.items():
            exp = set_values["set_name"]
            if exp in cardnamesByExpansion:
                exp_name = exp

                count = randomizerCountByExpansion[exp]
                Card.sets[set_tag]["count"] = count
                if "no_randomizer" in set_values:
                    if set_values["no_randomizer"]:
                        count = 0

                if not options.expansion_dividers_long_name:
                    if "short_name" in set_values:
                        exp_name = set_values["short_name"]

                card_names = []
                for n in sorted(
                    cardnamesByExpansion[exp].values(), key=lambda x: x["sort"]
                ):
                    if not n["randomizer"]:
                        # Highlight cards without Randomizers
                        n["name"] = "<i>" + n["name"] + "</i>"
                    if n["count"] > 1:
                        # Add number of copies
                        n["name"] = (
                            "{}&nbsp;\u00d7&nbsp;".format(n["count"]) + n["name"]
                        )
                    card_names.append(n["name"])

                c = Card(
                    name=exp_name,
                    cardset=exp,
                    cardset_tag=set_tag,
                    types=("Expansion",),
                    cost=None,
                    description=" | ".join(card_names),
                    extra=set_values.get("set_text", ""),
                    count=count,
                    card_tag=set_tag,
                )
                cards.append(c)

    # Take care of any --only-type-xxx requirements
    if options.only_type_any or options.only_type_all:
        # First make a dictionary for easier lookup of Type name used by the program
        # The index in each case is lower case for easier matching
        # The value in each case is the type index as used in types_en_us.json
        types_lookup = defaultdict(dict)
        for x in Card.type_names:
            types_lookup[x.lower()] = x
            types_lookup[Card.type_names[x].lower()] = x

        # Start the valid lists
        type_unknown = []
        type_known_any = []
        type_known_all = []

        # Assemble a list of valid "any" types.  Options are already lowercase.
        for x in options.only_type_any:
            if x in types_lookup:
                type_known_any.append(types_lookup[x])
            else:
                type_unknown.append(x)

        # Assemble a list of valid "all" types. Options are already lowercase.
        for x in options.only_type_all:
            if x in types_lookup:
                type_known_all.append(types_lookup[x])
            else:
                type_unknown.append(x)

        # Indicate if unknown types are given
        assert not type_unknown, "Error - unknown type(s): {}".format(
            ", ".join(type_unknown)
        )

        # If there are any valid Types left, go through the cards and keep cards that match
        if type_known_any or type_known_all:
            keep_cards = []
            for c in cards:
                if type_known_any and any(x in c.types for x in type_known_any):
                    keep_it = True
                elif type_known_all and all(x in c.types for x in type_known_all):
                    keep_it = True
                else:
                    keep_it = False

                if keep_it:
                    keep_cards.append(c)
            cards = keep_cards

    # Now sort what is left
    cards.sort(key=cardSorter)

    return cards


def calculate_layout(options, cards=None):
    if cards is None:
        cards = []
    # This is in place to allow for test cases to it call directly to get
    options = config_options.clean_opts(options)
    options.dominionCardWidth, options.dominionCardHeight = (
        config_options.parse_cardsize(options.size, options.sleeved)
    )
    options.paperwidth, options.paperheight = config_options.parse_papersize(
        options.papersize
    )
    options.minmarginwidth, options.minmarginheight = config_options.parse_dimensions(
        options.minmargin
    )

    dd = DividerDrawer(options)
    dd.calculatePages(cards)
    return dd


def generate(options):
    cards = db.read_card_data(options)
    assert cards, "No cards after reading"
    cards = filter_sort_cards(cards, options)
    assert cards, "No cards after filtering/sorting"

    dd = calculate_layout(options, cards)

    logger.info(
        f"Paper dimensions: {options.paperwidth / cm:.2f}cm (w) x {options.paperheight / cm:.2f}cm (h)"
    )
    logger.info(
        f"Tab dimensions: {options.dividerWidthReserved / cm:.2f}cm (w) "
        f"x {options.dividerHeightReserved / cm:.2f}cm (h)"
    )
    logger.info(
        f"{options.numDividersHorizontal} dividers horizontally, {options.numDividersVertical} vertically"
    )
    logger.info(
        f"Margins: {options.horizontalMargin / cm:.2f}cm h, {options.verticalMargin / cm:.2f}cm v"
    )

    dd.draw(cards)


def main():
    options = config_options.parse_opts()
    logger.remove()
    logger.add(sys.stderr, level=options.log_level)

    options = config_options.clean_opts(options)
    if options.preview:
        fname = "{}.{}".format(os.path.splitext(options.outfile)[0], "png")
        open(fname, "wb").write(generate_sample(options).getvalue())
    else:
        generate(options)
