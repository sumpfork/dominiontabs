from optparse import OptionParser
import os
import codecs
import json
import sys

import reportlab.lib.pagesizes as pagesizes
from reportlab.lib.units import cm

from cards import Card
from draw import DividerDrawer

LOCATION_CHOICES = ["tab", "body-top", "hide"]
NAME_ALIGN_CHOICES = ["left", "right", "centre", "edge"]
TAB_SIDE_CHOICES = ["left", "right", "left-alternate", "right-alternate", "full"]
TEXT_CHOICES = ["card", "rules", "blank"]


def add_opt(options, option, value):
    assert not hasattr(options, option)
    setattr(options, option, value)


def parse_opts(argstring):
    parser = OptionParser()
    parser.add_option("--back_offset", type="float", dest="back_offset", default=0,
                      help="Points to offset the back page to the right; needed for some printers")
    parser.add_option("--back_offset_height", type="float", dest="back_offset_height", default=0,
                      help="Points to offset the back page upward; needed for some printers")
    parser.add_option("--orientation", type="choice", choices=["horizontal", "vertical"],
                      dest="orientation", default="horizontal",
                      help="horizontal or vertical, default:horizontal")
    parser.add_option("--sleeved", action="store_true",
                      dest="sleeved", help="use --size=sleeved instead")
    parser.add_option("--size", type="string", dest="size", default='normal',
                      help="'<%f>x<%f>' (size in cm), or 'normal' = '9.1x5.9', or 'sleeved' = '9.4x6.15'")
    parser.add_option("--minmargin", type="string", dest="minmargin", default="1x1",
                      help="'<%f>x<%f>' (size in cm, left/right, top/bottom), default: 1x1")
    parser.add_option("--papersize", type="string", dest="papersize", default=None,
                      help="'<%f>x<%f>' (size in cm), or 'A4', or 'LETTER'")
    parser.add_option("--front", type="choice", choices=TEXT_CHOICES,
                      dest="text_front", default="card",
                      help="Text to print on the front of the divider.  choices: card, rules, blank;"
                      " 'card' will print the text from the game card;"
                      " 'rules' will print additional rules for the game card;"
                      " 'blank' will not print text on the divider;"
                      " default:card")
    parser.add_option("--back", type="choice", choices=TEXT_CHOICES + ["none"],
                      dest="text_back", default="rules",
                      help="Text to print on the back of the divider.  choices: card, rules, blank, none;"
                      " 'card' will print the text from the game card;"
                      " 'rules' will print additional rules for the game card;"
                      " 'blank' will not print text on the divider;"
                      " 'none' will prevent the back pages from printing;"
                      " default:rules")
    parser.add_option("--tab_name_align", type="choice", choices=NAME_ALIGN_CHOICES + ["center"],
                      dest="tab_name_align", default="left",
                      help="Alignment of text on the tab.  choices: left, right, centre (or center), edge."
                      " The edge option will align the card name to the outside edge of the"
                      " tab, so that when using tabs on alternating sides,"
                      " the name is less likely to be hidden by the tab in front"
                      " (edge will revert to left when tab_side is full since there is no edge in that case);"
                      " default:left")
    parser.add_option("--tab_side", type="choice", choices=TAB_SIDE_CHOICES,
                      dest="tab_side", default="right-alternate",
                      help="Alignment of tab.  choices: left, right, left-alternate, right-alternate, full;"
                      " left/right forces all tabs to left/right side;"
                      " left-alternate will start on the left and then toggle between left and right for the tabs;"
                      " right-alternate will start on the right and then toggle between right and left for the tabs;"  # noqa
                      " full will force all label tabs to be full width of the divider"
                      " default:right-alternate")
    parser.add_option("--tabwidth", type="float", default=4,
                      help="width in cm of stick-up tab (ignored if tab_side is full or tabs-only is used)")
    parser.add_option("--cost", action="append", type="choice",
                      choices=LOCATION_CHOICES, default=[],
                      help="where to display the card cost; may be set to"
                      " 'hide' to indicate it should not be displayed, or"
                      " given multiple times to show it in multiple"
                      " places; valid values are: %s; defaults to 'tab'"
                      % ", ".join("'%s'" % x for x in LOCATION_CHOICES))
    parser.add_option("--set_icon", action="append", type="choice",
                      choices=LOCATION_CHOICES, default=[],
                      help="where to display the set icon; may be set to"
                      " 'hide' to indicate it should not be displayed, or"
                      " given multiple times to show it in multiple"
                      " places; valid values are: %s; defaults to 'tab'"
                      % ", ".join("'%s'" % x for x in LOCATION_CHOICES))
    parser.add_option("--expansions", action="append", type="string",
                      help="subset of dominion expansions to produce tabs for")
    parser.add_option("--cropmarks", action="store_true", dest="cropmarks",
                      help="print crop marks on both sides, rather than tab outlines on one")
    parser.add_option("--linewidth", type="float", default=.1,
                      help="width of lines for card outlines/crop marks")
    parser.add_option("--write_json", action="store_true", dest="write_json",
                      help="write json version of card definitions and extras")
    parser.add_option("--tabs-only", action="store_true", dest="tabs_only",
                      help="draw only tabs to be printed on labels, no divider outlines")
    parser.add_option("--order", type="choice", choices=["expansion", "global", "colour"], dest="order",
                      help="sort order for the cards, whether by expansion or globally alphabetical")
    parser.add_option("--expansion_dividers", action="store_true", dest="expansion_dividers",
                      help="add dividers describing each expansion set")
    parser.add_option("--base_cards_with_expansion", action="store_true",
                      help='print the base cards as part of the expansion; ie, a divider for "Silver"'
                      ' will be printed as both a "Dominion" card and as an "Intrigue" card; if this'
                      ' option is not given, all base cards are placed in their own "Base" expansion')
    parser.add_option("--centre_expansion_dividers", action="store_true", dest="centre_expansion_dividers",
                      help='centre the tabs on expansion dividers')
    parser.add_option("--num_pages", type="int", default=-1,
                      help="stop generating after this many pages, -1 for all")
    parser.add_option("--language", default='en_us', help="language of card texts")
    parser.add_option("--include_blanks", action="store_true",
                      help="include a few dividers with extra text")
    parser.add_option("--exclude_events", action="store_true",
                      default=False, help="exclude individual dividers for events")
    parser.add_option("--exclude_landmarks", action="store_true",
                      default=False, help="exclude individual dividers for landmarks")
    parser.add_option("--special_card_groups", action="store_true",
                      default=False, help="group some cards under special dividers (e.g. Shelters, Prizes)")
    parser.add_option("--exclude_prizes", action="store_true",
                      default=False, help="exclude individual dividers for prizes (cornucopia)")
    parser.add_option("--cardlist", type="string", dest="cardlist", default=None,
                      help="Path to file that enumerates each card to be printed on its own line.")
    parser.add_option("--no-tab-artwork", action="store_true", dest="no_tab_artwork",
                      help="don't show background artwork on tabs")
    parser.add_option("--use-text-set-icon", action="store_true", dest="use_text_set_icon",
                      help="use text/letters to represent a card's set instead of the set icon")
    parser.add_option("--no-page-footer", action="store_true", dest="no_page_footer",
                      help="don't print the set name at the bottom of the page.")
    parser.add_option("--horizontal_gap", type=float, default=0.,
                      help="horizontal gap between dividers in centimeters")
    parser.add_option("--vertical_gap", type=float, default=0.,
                      help="vertical gap between dividers in centimeters")

    options, args = parser.parse_args(argstring)
    if not options.cost:
        options.cost = ['tab']
    if not options.set_icon:
        options.set_icon = ['tab']
    return options, args


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
            print 'Using custom paper size, %.2fcm x %.2fcm' % (paperwidth / cm, paperheight / cm)
        except ValueError:
            paperwidth, paperheight = pagesizes.LETTER
    return paperwidth, paperheight


def parse_cardsize(spec, sleeved):
    spec = spec.upper()
    if spec == 'SLEEVED' or sleeved:
        dominionCardWidth, dominionCardHeight = (9.4 * cm, 6.15 * cm)
        print 'Using sleeved card size, %.2fcm x %.2fcm' % (dominionCardWidth / cm,
                                                            dominionCardHeight / cm)
    elif spec in ['NORMAL', 'UNSLEEVED']:
        dominionCardWidth, dominionCardHeight = (9.1 * cm, 5.9 * cm)
        print 'Using normal card size, %.2fcm x%.2fcm' % (dominionCardWidth / cm,
                                                          dominionCardHeight / cm)
    else:
        dominionCardWidth, dominionCardHeight = parseDimensions(spec)
        print 'Using custom card size, %.2fcm x %.2fcm' % (dominionCardWidth / cm,
                                                           dominionCardHeight / cm)
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
        return card.cardset, int(card.isExpansion()), self.baseIndex(card.name), card.name

    def colour_sort_key(self, card):
        return card.getType().getTypeNames(), card.name

    def __call__(self, card):
        return self.sort_key(card)


def filter_sort_cards(cards, options):

    cardSorter = CardSorter(options.order,
                            [card.name for card in cards if card.cardset.lower() == 'base'])
    if options.base_cards_with_expansion:
        cards = [card for card in cards if card.cardset.lower() != 'base']
    else:
        cards = [card for card in cards if not cardSorter.isBaseExpansionCard(card)]

    if options.special_card_groups:
        # Load the card groups file
        data_dir = os.path.join(options.data_path, "card_db", options.language)
        card_groups_file = os.path.join(data_dir, "card_groups.json")
        with codecs.open(card_groups_file, 'r', 'utf-8') as cardgroup_file:
            card_groups = json.load(cardgroup_file)
            # pull out any cards which are a subcard, and rename the master card
            new_cards = []
            all_subcards = []
            for subs in [card_groups[x]["subcards"] for x in card_groups]:
                all_subcards += subs
            for card in cards:
                if card.name in card_groups.keys():
                    card.name = card_groups[card.name]["new_name"]
                elif card.name in all_subcards:
                    continue
                new_cards.append(card)
            cards = new_cards

    if options.expansions:
        options.expansions = [o.lower()
                              for o in options.expansions]
        reverseMapping = {
            v: k for k, v in Card.language_mapping.iteritems()}
        options.expansions = [
            reverseMapping.get(e, e) for e in options.expansions]
        filteredCards = []
        knownExpansions = set()
        for c in cards:
            knownExpansions.add(c.cardset)
            if next((e for e in options.expansions if c.cardset.startswith(e)), None):
                filteredCards.append(c)
        unknownExpansions = set(options.expansions) - knownExpansions
        if unknownExpansions:
            print "Error - unknown expansion(s): %s" % ", ".join(unknownExpansions)

        cards = filteredCards

    if options.exclude_events:
        cards = [card for card in cards if not card.isEvent() or card.name == 'Events']

    if options.exclude_landmarks:
        cards = [card for card in cards if not card.isLandmark() or card.name == 'Landmarks']

    if options.exclude_prizes:
        cards = [card for card in cards if not card.isPrize()]

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
            cardnamesByExpansion.setdefault(
                c.cardset, []).append(c.name.strip())
        for exp, names in cardnamesByExpansion.iteritems():
            c = Card(
                exp, exp, ("Expansion",), None, ' | '.join(sorted(names)))
            cards.append(c)

    cards.sort(key=cardSorter)

    return cards


def calculate_layout(options):

    dominionCardWidth, dominionCardHeight = parse_cardsize(options.size, options.sleeved)
    paperwidth, paperheight = parse_papersize(options.papersize)

    if options.orientation == "vertical":
        dividerWidth, dividerBaseHeight = dominionCardHeight, dominionCardWidth
    else:
        dividerWidth, dividerBaseHeight = dominionCardWidth, dominionCardHeight

    if options.tab_name_align == "center":
        options.tab_name_align = "centre"

    if options.tab_side == "full" and options.tab_name_align == "edge":
        # This case does not make sense since there are two tab edges in this case.  So picking left edge.
        print >>sys.stderr, "** Warning: Aligning card name as 'left' for 'full' tabs **"
        options.tab_name_align = "left"

    fixedMargins = False
    if options.tabs_only:
        # fixed for Avery 8867 for now
        minmarginwidth = 0.86 * cm   # was 0.76
        minmarginheight = 1.37 * cm   # was 1.27
        labelHeight = 1.07 * cm   # was 1.27
        labelWidth = 4.24 * cm   # was 4.44
        horizontalBorderSpace = 0.96 * cm   # was 0.76
        verticalBorderSpace = 0.20 * cm   # was 0.01
        dividerBaseHeight = 0
        dividerWidth = labelWidth
        fixedMargins = True
    else:
        minmarginwidth, minmarginheight = parseDimensions(
            options.minmargin)
        if options.tab_side == "full":
            labelWidth = dividerWidth
        else:
            labelWidth = options.tabwidth * cm
        labelHeight = .9 * cm
        horizontalBorderSpace = options.horizontal_gap * cm
        verticalBorderSpace = options.vertical_gap * cm

    dividerHeight = dividerBaseHeight + labelHeight

    add_opt(options, 'dividerWidth', dividerWidth)
    add_opt(options, 'dividerHeight', dividerHeight)
    add_opt(options, 'dividerBaseHeight', dividerBaseHeight)
    add_opt(options, 'dividerWidthReserved', dividerWidth + horizontalBorderSpace)
    add_opt(options, 'dividerHeightReserved', dividerHeight + verticalBorderSpace)
    add_opt(options, 'labelWidth', labelWidth)
    add_opt(options, 'labelHeight', labelHeight)

    # as we don't draw anything in the final border, it shouldn't count towards how many tabs we can fit
    # so it gets added back in to the page size here
    numDividersVerticalP = int(
        (paperheight - 2 * minmarginheight + verticalBorderSpace) / options.dividerHeightReserved)
    numDividersHorizontalP = int(
        (paperwidth - 2 * minmarginwidth + horizontalBorderSpace) / options.dividerWidthReserved)
    numDividersVerticalL = int(
        (paperwidth - 2 * minmarginwidth + verticalBorderSpace) / options.dividerHeightReserved)
    numDividersHorizontalL = int(
        (paperheight - 2 * minmarginheight + horizontalBorderSpace) / options.dividerWidthReserved)

    if ((numDividersVerticalL * numDividersHorizontalL >
         numDividersVerticalP * numDividersHorizontalP) and not fixedMargins):
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
                (options.paperwidth -
                 options.numDividersHorizontal * options.dividerWidthReserved + horizontalBorderSpace) / 2)
        add_opt(options, 'verticalMargin',
                (options.paperheight -
                 options.numDividersVertical * options.dividerHeightReserved + verticalBorderSpace) / 2)
    else:
        add_opt(options, 'horizontalMargin', minmarginwidth)
        add_opt(options, 'verticalMargin', minmarginheight)


def generate(options, data_path, f):

    add_opt(options, 'data_path', data_path)

    calculate_layout(options)

    print "Paper dimensions: {:.2f}cm (w) x {:.2f}cm (h)".format(options.paperwidth / cm,
                                                                 options.paperheight / cm)
    print "Tab dimensions: {:.2f}cm (w) x {:.2f}cm (h)".format(options.dividerWidthReserved / cm,
                                                               options.dividerHeightReserved / cm)
    print '{} dividers horizontally, {} vertically'.format(options.numDividersHorizontal,
                                                           options.numDividersVertical)
    print "Margins: {:.2f}cm h, {:.2f}cm v\n".format(options.horizontalMargin / cm,
                                                     options.verticalMargin / cm)

    cards = read_write_card_data(options)
    assert cards, "No cards after reading"
    cards = filter_sort_cards(cards, options)
    assert cards, "No cards after filtering/sorting"

    if not f:
        f = "dominion_dividers.pdf"

    dd = DividerDrawer()
    dd.draw(f, cards, options)


def main(argstring, data_path):
    options, args = parse_opts(argstring)
    fname = None
    if args:
        fname = args[0]
    return generate(options, data_path, fname)
