import os
import codecs
import json
import sys
import argparse

import reportlab.lib.pagesizes as pagesizes
from reportlab.lib.units import cm

from cards import Card
from draw import DividerDrawer

LOCATION_CHOICES = ["tab", "body-top", "hide"]
NAME_ALIGN_CHOICES = ["left", "right", "centre", "edge"]
TAB_SIDE_CHOICES = ["left", "right", "left-alternate", "right-alternate",
                    "centre", "full"]
TEXT_CHOICES = ["card", "rules", "blank"]


def add_opt(options, option, value):
    assert not hasattr(options, option)
    setattr(options, option, value)


def parse_opts(arglist):
    parser = argparse.ArgumentParser(description="Generate Dominion Dividers")
    parser.add_argument('--outfile', default="dominion_dividers.pdf")
    parser.add_argument(
        "--back_offset",
        type=float,
        dest="back_offset",
        default=0,
        help="Points to offset the back page to the right; needed for some printers")
    parser.add_argument(
        "--back_offset_height",
        type=float,
        dest="back_offset_height",
        default=0,
        help="Points to offset the back page upward; needed for some printers")
    parser.add_argument("--orientation",
                        choices=["horizontal", "vertical"],
                        dest="orientation",
                        default="horizontal",
                        help="horizontal or vertical, default:horizontal")
    parser.add_argument("--sleeved",
                        action="store_true",
                        dest="sleeved",
                        help="use --size=sleeved instead")
    parser.add_argument(
        "--size",
        dest="size",
        default='normal',
        help="'<%%f>x<%%f>' (size in cm), or 'normal' = '9.1x5.9', or 'sleeved' = '9.4x6.15'")
    parser.add_argument(
        "--minmargin",
        dest="minmargin",
        default="1x1",
        help="'<%%f>x<%%f>' (size in cm, left/right, top/bottom), default: 1x1")
    parser.add_argument("--papersize",
                        dest="papersize",
                        default=None,
                        help="'<%%f>x<%%f>' (size in cm), or 'A4', or 'LETTER'")
    parser.add_argument(
        "--front",
        choices=TEXT_CHOICES,
        dest="text_front",
        default="card",
        help="Text to print on the front of the divider.  choices: card, rules, blank;"
        " 'card' will print the text from the game card;"
        " 'rules' will print additional rules for the game card;"
        " 'blank' will not print text on the divider;"
        " default:card")
    parser.add_argument(
        "--back",
        choices=TEXT_CHOICES + ["none"],
        dest="text_back",
        default="rules",
        help="Text to print on the back of the divider.  choices: card, rules, blank, none;"
        " 'card' will print the text from the game card;"
        " 'rules' will print additional rules for the game card;"
        " 'blank' will not print text on the divider;"
        " 'none' will prevent the back pages from printing;"
        " default:rules")
    parser.add_argument(
        "--tab_name_align",
        choices=NAME_ALIGN_CHOICES + ["center"],
        dest="tab_name_align",
        default="left",
        help="Alignment of text on the tab.  choices: left, right, centre (or center), edge."
        " The edge option will align the card name to the outside edge of the"
        " tab, so that when using tabs on alternating sides,"
        " the name is less likely to be hidden by the tab in front"
        " (edge will revert to left when tab_side is full since there is no edge in that case);"
        " default:left")
    parser.add_argument(
        "--tab_side",
        choices=TAB_SIDE_CHOICES,
        dest="tab_side",
        default="right-alternate",
        help="Alignment of tab.  choices: left, right, left-alternate, right-alternate, full;"
        " left/right forces all tabs to left/right side;"
        " left-alternate will start on the left and then toggle between left and right for the tabs;"
        " right-alternate will start on the right and then toggle between right and left for the tabs;"  # noqa
        " centre will force all label tabs to the centre;"
        " full will force all label tabs to be full width of the divider"
        " default:right-alternate")
    parser.add_argument(
        "--tabwidth",
        type=float,
        default=4,
        help="width in cm of stick-up tab (ignored if tab_side is full or tabs-only is used)")
    parser.add_argument("--cost",
                        action="append",
                        choices=LOCATION_CHOICES,
                        default=[],
                        help="where to display the card cost; may be set to"
                        " 'hide' to indicate it should not be displayed, or"
                        " given multiple times to show it in multiple"
                        " places; valid values are: %s; defaults to 'tab'" %
                        ", ".join("'%s'" % x for x in LOCATION_CHOICES))
    parser.add_argument("--set_icon",
                        action="append",
                        choices=LOCATION_CHOICES,
                        default=[],
                        help="where to display the set icon; may be set to"
                        " 'hide' to indicate it should not be displayed, or"
                        " given multiple times to show it in multiple"
                        " places; valid values are: %s; defaults to 'tab'" %
                        ", ".join("'%s'" % x for x in LOCATION_CHOICES))
    parser.add_argument(
        "--expansions",
        action="append",
        help="subset of dominion expansions to produce tabs for")
    parser.add_argument(
        "--cropmarks",
        action="store_true",
        dest="cropmarks",
        help="print crop marks on both sides, rather than tab outlines on one")
    parser.add_argument("--linewidth",
                        type=float,
                        default=.1,
                        help="width of lines for card outlines/crop marks")
    parser.add_argument(
        "--write_json",
        action="store_true",
        dest="write_json",
        help="write json version of card definitions and extras")
    parser.add_argument(
        "--tabs-only",
        action="store_true",
        dest="tabs_only",
        help="draw only tabs to be printed on labels, no divider outlines")
    parser.add_argument(
        "--order",
        choices=["expansion", "global", "colour"],
        dest="order",
        help="sort order for the cards, whether by expansion or globally alphabetical")
    parser.add_argument("--expansion_dividers",
                        action="store_true",
                        dest="expansion_dividers",
                        help="add dividers describing each expansion set")
    parser.add_argument(
        "--base_cards_with_expansion",
        action="store_true",
        help='print the base cards as part of the expansion; ie, a divider for "Silver"'
        ' will be printed as both a "Dominion" card and as an "Intrigue" card; if this'
        ' option is not given, all base cards are placed in their own "Base" expansion')
    parser.add_argument("--centre_expansion_dividers",
                        action="store_true",
                        dest="centre_expansion_dividers",
                        help='centre the tabs on expansion dividers')
    parser.add_argument(
        "--num_pages",
        type=int,
        default=-1,
        help="stop generating after this many pages, -1 for all")
    parser.add_argument("--language",
                        default='en_us',
                        help="language of card texts")
    parser.add_argument("--include_blanks",
                        action="store_true",
                        help="include a few dividers with extra text")
    parser.add_argument("--exclude_events",
                        action="store_true",
                        help="exclude individual dividers for events")
    parser.add_argument("--exclude_landmarks",
                        action="store_true",
                        help="exclude individual dividers for landmarks")
    parser.add_argument(
        "--special_card_groups",
        action="store_true",
        help="group some cards under special dividers (e.g. Shelters, Prizes)")
    parser.add_argument(
        "--exclude_prizes",
        action="store_true",
        help="exclude individual dividers for prizes (cornucopia)")
    parser.add_argument(
        "--cardlist",
        dest="cardlist",
        help="Path to file that enumerates each card to be printed on its own line.")
    parser.add_argument("--no-tab-artwork",
                        action="store_true",
                        dest="no_tab_artwork",
                        help="don't show background artwork on tabs")
    parser.add_argument(
        "--use-text-set-icon",
        action="store_true",
        dest="use_text_set_icon",
        help="use text/letters to represent a card's set instead of the set icon")
    parser.add_argument(
        "--no-page-footer",
        action="store_true",
        dest="no_page_footer",
        help="don't print the set name at the bottom of the page.")
    parser.add_argument("--horizontal_gap",
                        type=float,
                        default=0.,
                        help="horizontal gap between dividers in centimeters")
    parser.add_argument("--vertical_gap",
                        type=float,
                        default=0.,
                        help="vertical gap between dividers in centimeters")
    parser.add_argument("--count",
                        action="store_true",
                        dest="count",
                        help="Display card count on body of the divider.")
    parser.add_argument(
        "--wrapper",
        action="store_true",
        dest="wrapper",
        help="Draw wrapper for cards instead of a divider for the cards")
    parser.add_argument(
        "--thickness",
        type=float,
        default=2.0,
        help="Thickness of a stack of 60 cards (Copper) in centimeters."
        " Typically unsleeved cards are 2.0, thin sleeved cards are 2.4, and thick sleeved cards are 3.2."
        " This is only valid with the --wrapper option."
        " default:2.0")
    parser.add_argument("--sleeved_thick",
                        action="store_true",
                        dest="sleeved_thick",
                        help="same as --size=sleeved --thickness 3.2")
    parser.add_argument("--sleeved_thin",
                        action="store_true",
                        dest="sleeved_thin",
                        help="same as --size=sleeved --thickness 2.4")
    parser.add_argument(
        "--notch_length",
        type=float,
        default=0.0,
        help="Length of thumb notch on wrapper in centimeters."
        " This can make it easier to remove the cards from the wrapper."
        " This is only valid with the --wrapper option."
        " default:0.0 (i.e., no notch on wrapper)")
    parser.add_argument("--notch",
                        action="store_true",
                        dest="notch",
                        help="same as --notch_length thickness 1.5")

    options = parser.parse_args(arglist)
    if not options.cost:
        options.cost = ['tab']
    if not options.set_icon:
        options.set_icon = ['tab']

    if options.sleeved_thick:
        options.thickness = 3.2
        options.sleeved = True

    if options.sleeved_thin:
        options.thickness = 2.4
        options.sleeved = True

    if options.notch:
        options.notch_length = 1.5

    return options


def parseDimensions(dimensionsStr):
    x, y = dimensionsStr.upper().split('X', 1)
    return (float(x) * cm, float(y) * cm)


def generate_sample(options):
    import cStringIO
    from wand.image import Image
    buf = cStringIO.StringIO()
    options.num_pages = 1
    generate(options, '.', buf)
    with Image(blob=buf.getvalue()) as sample:
        sample.format = 'png'
        sample.save(filename='sample.png')


def parse_papersize(spec):
    papersize = None
    if not spec:
        if os.path.exists("/etc/papersize"):
            papersize = open("/etc/papersize").readline().upper()
        else:
            papersize = 'LETTER'
    else:
        papersize = spec.upper()

    try:
        paperwidth, paperheight = getattr(pagesizes, papersize)
    except AttributeError:
        try:
            paperwidth, paperheight = parseDimensions(papersize)
            print 'Using custom paper size, %.2fcm x %.2fcm' % (
                paperwidth / cm, paperheight / cm)
        except ValueError:
            paperwidth, paperheight = pagesizes.LETTER
    return paperwidth, paperheight


def parse_cardsize(spec, sleeved):
    spec = spec.upper()
    if spec == 'SLEEVED' or sleeved:
        dominionCardWidth, dominionCardHeight = (9.4 * cm, 6.15 * cm)
        print 'Using sleeved card size, %.2fcm x %.2fcm' % (
            dominionCardWidth / cm, dominionCardHeight / cm)
    elif spec in ['NORMAL', 'UNSLEEVED']:
        dominionCardWidth, dominionCardHeight = (9.1 * cm, 5.9 * cm)
        print 'Using normal card size, %.2fcm x%.2fcm' % (
            dominionCardWidth / cm, dominionCardHeight / cm)
    else:
        dominionCardWidth, dominionCardHeight = parseDimensions(spec)
        print 'Using custom card size, %.2fcm x %.2fcm' % (
            dominionCardWidth / cm, dominionCardHeight / cm)
    return dominionCardWidth, dominionCardHeight


def read_write_card_data(options):
    data_dir = os.path.join(options.data_path, "card_db", options.language)
    card_db_filepath = os.path.join(data_dir, "cards.json")
    with codecs.open(card_db_filepath, "r", "utf-8") as cardfile:
        cards = json.load(cardfile, object_hook=Card.decode_json)

    assert cards, "Could not load any cards from database"

    language_mapping_filepath = os.path.join(data_dir, "mapping.json")
    with codecs.open(language_mapping_filepath, 'r', 'utf-8') as mapping_file:
        Card.language_mapping = json.load(mapping_file)

    if options.write_json:
        fpath = "cards.json"
        with codecs.open(fpath, 'w', encoding='utf-8') as ofile:
            json.dump(cards,
                      ofile,
                      cls=Card.CardJSONEncoder,
                      ensure_ascii=False,
                      indent=True,
                      sort_keys=True)
    return cards


class CardSorter(object):
    def __init__(self, order, baseCards):
        self.order = order
        if order == "global":
            self.sort_key = self.global_sort_key
        elif order == "colour":
            self.sort_key = self.colour_sort_key
        else:
            self.sort_key = self.by_expansion_sort_key

        self.baseCards = baseCards

    # When sorting cards, want to always put "base" cards after all
    # kingdom cards, and order the base cards in a set order - the
    # order they are listed in the database (ie, all normal treasures
    # by worth, then potion, then all normal VP cards by worth, then
    # trash)
    def baseIndex(self, name):
        try:
            return self.baseCards.index(name)
        except Exception:
            return -1

    def isBaseExpansionCard(self, card):
        return card.cardset.lower() != 'base' and card.name in self.baseCards

    def global_sort_key(self, card):
        return int(card.isExpansion()), self.baseIndex(card.name), card.name

    def by_expansion_sort_key(self, card):
        return card.cardset, int(card.isExpansion()), self.baseIndex(
            card.name), card.name

    def colour_sort_key(self, card):
        return card.getType().getTypeNames(), card.name

    def __call__(self, card):
        return self.sort_key(card)


def filter_sort_cards(cards, options):

    cardSorter = CardSorter(
        options.order,
        [card.name for card in cards if card.cardset.lower() == 'base'])
    if options.base_cards_with_expansion:
        cards = [card for card in cards if card.cardset.lower() != 'base']
    else:
        cards = [card for card in cards
                 if not cardSorter.isBaseExpansionCard(card)]

    if options.special_card_groups:
        # Load the card groups file
        data_dir = os.path.join(options.data_path, "card_db", options.language)
        card_groups_file = os.path.join(data_dir, "card_groups.json")
        with codecs.open(card_groups_file, 'r', 'utf-8') as cardgroup_file:
            card_groups = json.load(cardgroup_file)
            # pull out any cards which are a subcard, and rename the master card
            new_cards = []  # holds the cards that are to be kept
            all_subcards = []  # holds names of cards that will be removed
            subcard_parent = {
            }  # holds reverse map of subcard name to group name
            subcard_count = {
            }  # holds total card count of the subcards for a group

            # Initialize each of the new card groups
            for group in card_groups:
                subcard_count[group] = 0
                for subs in card_groups[group]["subcards"]:
                    all_subcards.append(
                        subs)  # add card names to the list for removal
                    subcard_parent[
                        subs] = group  # create the reverse mapping of subgroup to group

                    # go through the cards and add up the number of subgroup cards
            for card in cards:
                if card.name in all_subcards:
                    subcard_count[subcard_parent[
                        card.name]] += card.getCardCount()

                    # fix up the group card holders count & name, and weed out the subgroup cards
            for card in cards:
                if card.name in card_groups.keys():
                    card.count += subcard_count[card.name]
                    card.name = card_groups[card.name]["new_name"]
                elif card.name in all_subcards:
                    continue
                new_cards.append(card)
            cards = new_cards

    if options.expansions:
        options.expansions = [o.lower() for o in options.expansions]
        reverseMapping = {v: k for k, v in Card.language_mapping.iteritems()}
        options.expansions = [
            reverseMapping.get(e, e) for e in options.expansions
        ]
        filteredCards = []
        knownExpansions = set()
        for c in cards:
            knownExpansions.add(c.cardset)
            if next((e for e in options.expansions
                     if c.cardset.startswith(e)), None):
                filteredCards.append(c)
        unknownExpansions = set(options.expansions) - knownExpansions
        if unknownExpansions:
            print "Error - unknown expansion(s): %s" % ", ".join(
                unknownExpansions)

        cards = filteredCards

    if options.exclude_events:
        filteredCards = []
        count = 0
        holder = False
        for c in cards:
            if c.isType('Events'):  # Language Independant by using Type
                holder = c
                filteredCards.append(c)
            elif c.isEvent():
                count += c.getCardCount()
            else:
                filteredCards.append(c)
        if holder and count > 0:
            holder.setCardCount(count)
        cards = filteredCards

    if options.exclude_landmarks:
        filteredCards = []
        count = 0
        holder = False
        for c in cards:
            if c.isType('Landmarks'):  # Language Independant, use Type
                holder = c
                filteredCards.append(c)
            elif c.isLandmark():
                count += c.getCardCount()
            else:
                filteredCards.append(c)
        if holder and count > 0:
            holder.setCardCount(count)
        cards = filteredCards

    if options.exclude_prizes:
        filteredCards = []
        count = 0
        holder = False
        for c in cards:
            if c.isType('Prizes'):  # Language Independant, use Type
                holder = c
                filteredCards.append(c)
            elif c.isPrize():
                count += c.getCardCount()
            else:
                filteredCards.append(c)
        if holder and count > 0:
            holder.setCardCount(count)
        cards = filteredCards

    if options.cardlist:
        cardlist = set()
        with open(options.cardlist) as cardfile:
            for line in cardfile:
                cardlist.add(line.strip())
        if cardlist:
            cards = [card for card in cards if card.name in cardlist]

    if options.expansion_dividers:
        cardnamesByExpansion = {}
        for c in cards:
            if cardSorter.isBaseExpansionCard(c):
                continue
            cardnamesByExpansion.setdefault(c.cardset,
                                            []).append(c.name.strip())
        for exp, names in cardnamesByExpansion.iteritems():
            c = Card(exp,
                     exp, ("Expansion", ),
                     None,
                     ' | '.join(sorted(names)),
                     count=len(names))
            cards.append(c)

    cards.sort(key=cardSorter)

    return cards


def calculate_layout(options, cards=[]):

    dominionCardWidth, dominionCardHeight = parse_cardsize(options.size,
                                                           options.sleeved)
    paperwidth, paperheight = parse_papersize(options.papersize)

    if options.orientation == "vertical":
        dividerWidth, dividerBaseHeight = dominionCardHeight, dominionCardWidth
    else:
        dividerWidth, dividerBaseHeight = dominionCardWidth, dominionCardHeight

    if options.tab_name_align == "center":
        options.tab_name_align = "centre"

    if options.tab_side == "full" and options.tab_name_align == "edge":
        # This case does not make sense since there are two tab edges in this case.  So picking left edge.
        print >> sys.stderr, "** Warning: Aligning card name as 'left' for 'full' tabs **"
        options.tab_name_align = "left"

    fixedMargins = False
    if options.tabs_only:
        # fixed for Avery 8867 for now
        minmarginwidth = 0.86 * cm  # was 0.76
        minmarginheight = 1.37 * cm  # was 1.27
        labelHeight = 1.07 * cm  # was 1.27
        labelWidth = 4.24 * cm  # was 4.44
        horizontalBorderSpace = 0.96 * cm  # was 0.76
        verticalBorderSpace = 0.20 * cm  # was 0.01
        dividerBaseHeight = 0
        dividerWidth = labelWidth
        fixedMargins = True
    else:
        minmarginwidth, minmarginheight = parseDimensions(options.minmargin)
        if options.tab_side == "full":
            labelWidth = dividerWidth
        else:
            labelWidth = options.tabwidth * cm
        labelHeight = .9 * cm
        horizontalBorderSpace = options.horizontal_gap * cm
        verticalBorderSpace = options.vertical_gap * cm

    dividerHeight = dividerBaseHeight + labelHeight

    dividerWidthReserved = dividerWidth + horizontalBorderSpace
    dividerHeightReserved = dividerHeight + verticalBorderSpace
    if options.wrapper:
        max_card_stack_height = max(c.getStackHeight(options.thickness)
                                    for c in cards)
        dividerHeightReserved = (dividerHeightReserved * 2) + (
            max_card_stack_height * 2)
        print "Max Card Stack Height: {:.2f}cm ".format(max_card_stack_height)

    # Notch measurements
    notch_height = 0.25 * cm  # thumb notch height
    notch_width1 = options.notch_length * cm  # thumb notch width: top away from tab
    notch_width2 = 0.00 * cm  # thumb notch width: bottom on side of tab

    add_opt(options, 'dividerWidth', dividerWidth)
    add_opt(options, 'dividerHeight', dividerHeight)
    add_opt(options, 'dividerBaseHeight', dividerBaseHeight)
    add_opt(options, 'dividerWidthReserved', dividerWidthReserved)
    add_opt(options, 'dividerHeightReserved', dividerHeightReserved)
    add_opt(options, 'labelWidth', labelWidth)
    add_opt(options, 'labelHeight', labelHeight)
    add_opt(options, 'notch_height', notch_height)
    add_opt(options, 'notch_width1', notch_width1)
    add_opt(options, 'notch_width2', notch_width2)

    # as we don't draw anything in the final border, it shouldn't count towards how many tabs we can fit
    # so it gets added back in to the page size here
    numDividersVerticalP = int(
        (paperheight - 2 * minmarginheight + verticalBorderSpace) /
        options.dividerHeightReserved)
    numDividersHorizontalP = int(
        (paperwidth - 2 * minmarginwidth + horizontalBorderSpace) /
        options.dividerWidthReserved)
    numDividersVerticalL = int(
        (paperwidth - 2 * minmarginwidth + verticalBorderSpace) /
        options.dividerHeightReserved)
    numDividersHorizontalL = int(
        (paperheight - 2 * minmarginheight + horizontalBorderSpace) /
        options.dividerWidthReserved)

    if ((numDividersVerticalL * numDividersHorizontalL > numDividersVerticalP *
         numDividersHorizontalP) and not fixedMargins):
        add_opt(options, 'numDividersVertical', numDividersVerticalL)
        add_opt(options, 'numDividersHorizontal', numDividersHorizontalL)
        add_opt(options, 'paperheight', paperwidth)
        add_opt(options, 'paperwidth', paperheight)
        add_opt(options, 'minHorizontalMargin', minmarginheight)
        add_opt(options, 'minVerticalMargin', minmarginwidth)
    else:
        add_opt(options, 'numDividersVertical', numDividersVerticalP)
        add_opt(options, 'numDividersHorizontal', numDividersHorizontalP)
        add_opt(options, 'paperheight', paperheight)
        add_opt(options, 'paperwidth', paperwidth)
        add_opt(options, 'minHorizontalMargin', minmarginheight)
        add_opt(options, 'minVerticalMargin', minmarginwidth)

    if not fixedMargins:
        # dynamically max margins
        add_opt(options, 'horizontalMargin',
                (options.paperwidth - options.numDividersHorizontal *
                 options.dividerWidthReserved + horizontalBorderSpace) / 2)
        add_opt(options, 'verticalMargin',
                (options.paperheight - options.numDividersVertical *
                 options.dividerHeightReserved + verticalBorderSpace) / 2)
    else:
        add_opt(options, 'horizontalMargin', minmarginwidth)
        add_opt(options, 'verticalMargin', minmarginheight)


def generate(options, data_path):

    add_opt(options, 'data_path', data_path)

    cards = read_write_card_data(options)
    assert cards, "No cards after reading"
    cards = filter_sort_cards(cards, options)
    assert cards, "No cards after filtering/sorting"

    calculate_layout(options, cards)

    print "Paper dimensions: {:.2f}cm (w) x {:.2f}cm (h)".format(
        options.paperwidth / cm, options.paperheight / cm)
    print "Tab dimensions: {:.2f}cm (w) x {:.2f}cm (h)".format(
        options.dividerWidthReserved / cm, options.dividerHeightReserved / cm)
    print '{} dividers horizontally, {} vertically'.format(
        options.numDividersHorizontal, options.numDividersVertical)
    print "Margins: {:.2f}cm h, {:.2f}cm v\n".format(
        options.horizontalMargin / cm, options.verticalMargin / cm)

    dd = DividerDrawer()
    dd.draw(cards, options)


def main(arglist, data_path):
    options = parse_opts(arglist)
    return generate(options, data_path)
