import os
import codecs
import json
import sys
import configargparse
import copy
import fnmatch
import pkg_resources
import unicodedata
from collections import Counter, defaultdict

import reportlab.lib.pagesizes as pagesizes
from reportlab.lib.units import cm

from .cards import Card
from .cards import CardType
from .draw import DividerDrawer

LOCATION_CHOICES = ["tab", "body-top", "hide"]
NAME_ALIGN_CHOICES = ["left", "right", "centre", "edge"]
TAB_SIDE_CHOICES = [
    "left",
    "right",
    "left-alternate",
    "right-alternate",
    "left-flip",
    "right-flip",
    "centre",
    "full",
]
TEXT_CHOICES = ["card", "rules", "blank"]
LINE_CHOICES = ["line", "dot", "cropmarks", "dot-cropmarks"]

EDITION_CHOICES = ["1", "2", "latest", "all"]

ORDER_CHOICES = ["expansion", "global", "colour", "cost"]

EXPANSION_GLOBAL_GROUP = "extras"
EXPANSION_EXTRA_POSTFIX = " extras"

LANGUAGE_DEFAULT = (
    "en_us"  # the primary language used if a language's parts are missing
)
LANGUAGE_XX = "xx"  # a dummy language for starting translations


def get_languages(path):
    languages = []
    for name in pkg_resources.resource_listdir("domdiv", path):
        dir_path = os.path.join(path, name)
        if pkg_resources.resource_isdir("domdiv", dir_path):
            cards_file = os.path.join(dir_path, "cards_{}.json".format(name))
            sets_file = os.path.join(dir_path, "sets_{}.json".format(name))
            types_file = os.path.join(dir_path, "types_{}.json".format(name))
            if (
                pkg_resources.resource_exists("domdiv", cards_file)
                and pkg_resources.resource_exists("domdiv", sets_file)
                and pkg_resources.resource_exists("domdiv", types_file)
            ):
                languages.append(name)
    if LANGUAGE_XX in languages:
        languages.remove(LANGUAGE_XX)
    return languages


LANGUAGE_CHOICES = get_languages("card_db")


def get_resource_stream(path):
    return codecs.EncodedFile(pkg_resources.resource_stream("domdiv", path), "utf-8")


def get_expansions():
    set_db_filepath = os.path.join("card_db", "sets_db.json")
    with get_resource_stream(set_db_filepath) as setfile:
        set_file = json.loads(setfile.read().decode("utf-8"))
    assert set_file, "Could not load any sets from database"

    fan = []
    official = []
    for s in set_file:
        if EXPANSION_EXTRA_POSTFIX not in s:
            # Make sure these are set either True or False
            set_file[s]["fan"] = set_file[s].get("fan", False)
            if set_file[s]["fan"]:
                fan.append(s)
            else:
                official.append(s)
    fan.sort()
    official.sort()
    return official, fan


EXPANSION_CHOICES, FAN_CHOICES = get_expansions()


def get_global_groups():
    type_db_filepath = os.path.join("card_db", "types_db.json")
    with get_resource_stream(type_db_filepath) as typefile:
        type_file = json.loads(typefile.read().decode("utf-8"))
    assert type_file, "Could not load any card types from database"

    group_global_choices = []
    group_global_valid = []
    for t in type_file:
        if "group_global_type" in t:
            group_global_valid.append("-".join(t["card_type"]).lower())
            group_global_choices.append(t["group_global_type"].lower())
    group_global_valid.extend(group_global_choices)
    group_global_valid.sort()
    group_global_choices.sort()
    return group_global_choices, group_global_valid


GROUP_GLOBAL_CHOICES, GROUP_GLOBAL_VALID = get_global_groups()


def get_types(language="en_us"):
    # get a list of valid types
    language = language.lower()
    type_text_filepath = os.path.join(
        "card_db", language, "types_{}.json".format(language)
    )
    with get_resource_stream(type_text_filepath) as type_text_file:
        type_text = json.loads(type_text_file.read().decode("utf-8"))
    assert type_text, "Could not load type file for %r" % language

    types = [x.lower() for x in type_text]
    types.sort()
    return types


TYPE_CHOICES = get_types(LANGUAGE_DEFAULT)


# Load Label information
LABEL_INFO = None
LABEL_CHOICES = []
LABEL_KEYS = []
LABEL_SELECTIONS = []
labels_db_filepath = os.path.join("card_db", "labels_db.json")
with get_resource_stream(labels_db_filepath) as labelfile:
    LABEL_INFO = json.loads(labelfile.read().decode("utf-8"))
assert LABEL_INFO, "Could not load label information from database"
for label in LABEL_INFO:
    if len(label["names"]) > 0:
        LABEL_KEYS.append(label["names"][0])
        LABEL_SELECTIONS.append(label["name"] if "name" in label else label["names"][0])
        LABEL_CHOICES.extend(label["names"])


def add_opt(options, option, value):
    assert not hasattr(options, option)
    setattr(options, option, value)


def parse_opts(cmdline_args=None):
    parser = configargparse.ArgParser(
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter,
        description="Generate Dominion Dividers",
        epilog="Source can be found at 'https://github.com/sumpfork/dominiontabs'. "
        "An online version can be found at 'http://domtabs.sandflea.org/'. ",
    )

    # Basic Divider Information
    group_basic = parser.add_argument_group(
        "Basic Divider Options", "Basic choices for the dividers."
    )
    group_basic.add_argument(
        "--outfile",
        "-o",
        dest="outfile",
        default="dominion_dividers.pdf",
        help="The output file name.",
    )
    group_basic.add_argument(
        "--papersize",
        dest="papersize",
        default=None,
        help="The size of paper to use; '<%%f>x<%%f>' (size in cm), or 'A4', or 'LETTER'. "
        "If not specified, it will default to system defaults, and if the system defaults "
        "are not found, then to 'LETTER'.",
    )
    group_basic.add_argument(
        "--language",
        "-l",
        dest="language",
        default=LANGUAGE_DEFAULT,
        choices=LANGUAGE_CHOICES,
        help="Language of divider text.",
    )
    group_basic.add_argument(
        "--orientation",
        choices=["horizontal", "vertical"],
        dest="orientation",
        default="horizontal",
        help="Either horizontal or vertical divider orientation.",
    )
    group_basic.add_argument(
        "--size",
        dest="size",
        default="normal",
        help="Dimentions of the cards to use with the dividers '<%%f>x<%%f>' (size in cm), "
        "or 'normal' = '9.1x5.9', or 'sleeved' = '9.4x6.15'.",
    )
    group_basic.add_argument(
        "--sleeved", action="store_true", dest="sleeved", help="Same as --size=sleeved."
    )
    group_basic.add_argument(
        "--order",
        choices=ORDER_CHOICES,
        default="expansion",
        dest="order",
        help="Sort order for the dividers: "
        " 'global' will sort by card name;"
        " 'expansion' will sort by expansion, then card name;"
        " 'colour' will sort by card type, then card name;"
        " 'cost' will sort by expansion, then card cost, then name.",
    )

    # Divider Body
    group_body = parser.add_argument_group(
        "Divider Body", "Changes what is displayed on the body of the dividers."
    )
    group_body.add_argument(
        "--front",
        choices=TEXT_CHOICES,
        dest="text_front",
        default="card",
        help="Text to print on the front of the divider; "
        "'card' will print the text from the game card; "
        "'rules' will print additional rules for the game card; "
        "'blank' will not print text on the divider.",
    )
    group_body.add_argument(
        "--back",
        choices=TEXT_CHOICES + ["none"],
        dest="text_back",
        default="rules",
        help="Text to print on the back of the divider; "
        "'card' will print the text from the game card; "
        "'rules' will print additional rules for the game card; "
        "'blank' will not print text on the divider; "
        "'none' will prevent the back pages from printing. ",
    )
    group_body.add_argument(
        "--count",
        action="store_true",
        dest="count",
        help="Display the card count on the body of card dividers "
        "and the randomizer count on the body of expansion dividers.",
    )
    group_body.add_argument(
        "--types",
        action="store_true",
        dest="types",
        help="Display card type on the body of the divider.",
    )

    # Divider Tab
    group_tab = parser.add_argument_group(
        "Divider Tab", "Changes what is displayed on on the Divider Tab."
    )
    group_tab.add_argument(
        "--tab-side",
        choices=TAB_SIDE_CHOICES,
        dest="tab_side",
        default="right-alternate",
        help="Alignment of tab; "
        "'left'/'right'/'centre' sets the starting side of the tabs; "
        "'full' will force all label tabs to be full width of the divider; sets --tab_number 1 "
        "'left-alternate' will start on the left and then toggle between left and right for the tabs,"
        " sets --tab_number 2; "
        "'right-alternate' will start on the right and then toggle between right and left for the tabs,"
        " sets --tab_number 2; "
        "'left-flip' like left-alternate, but the right will be flipped front/back with tab on left,"
        " sets --tab_number 2; "
        "'right-flip' like right-alternate, but the left will be flipped front/back with tab on right,"
        " sets --tab_number 2; ",
    )
    group_tab.add_argument(
        "--tab-number",
        type=int,
        default=1,
        help="The number of tabs. When set to 1, all tabs are on the same side (specified by --tab_side). "
        "When set to 2, tabs will alternate between left and right. (starting side specified by --tab_side). "
        "When set > 2, the first tab will be on left/right side specified by --tab_side, then the rest "
        "of the tabs will be evenly spaced until ending on the opposite side. Then the cycle repeats. "
        "May be overriden by some options of --tab_side.",
    )
    group_tab.add_argument(
        "--tab-serpentine",
        action="store_true",
        help="Affects the order of tabs.  When not selected, tabs will progress from the starting side (left/right) "
        "to the opposite side (right/left), and then repeat (e.g., left to right, left to right, etc.). "
        "When selected, the order is changed to smoothly alternate between the two sides "
        "(e.g., left to right, to left, to right, etc.) "
        "Only valid if --tab_number > 2.",
    )
    group_tab.add_argument(
        "--tab-name-align",
        choices=NAME_ALIGN_CHOICES + ["center"],
        dest="tab_name_align",
        default="left",
        help="Alignment of text on the tab; "
        "The 'edge' option will align the card name to the outside edge of the "
        "tab, so that when using tabs on alternating sides, "
        "the name is less likely to be hidden by the tab in front "
        "(edge will revert to left when tab_side is full since there is no edge in that case).",
    )
    group_tab.add_argument(
        "--tabwidth",
        type=float,
        default=4.0,
        help="Width in cm of stick-up tab (ignored if --tab_side is 'full' or --tabs_only is used).",
    )
    group_tab.add_argument(
        "--cost",
        action="append",
        choices=LOCATION_CHOICES,
        help="Where to display the card cost; may be set to "
        "'hide' to indicate it should not be displayed, or "
        "given multiple times to show it in multiple places. "
        "(If not given, will default to 'tab'.)",
    )
    group_tab.add_argument(
        "--set-icon",
        action="append",
        choices=LOCATION_CHOICES,
        help="Where to display the set icon; may be set to "
        "'hide' to indicate it should not be displayed, or "
        "given multiple times to show it in multiple places. "
        "(If not given, will default to 'tab'.)",
    )
    group_tab.add_argument(
        "--no-tab-artwork",
        action="store_true",
        dest="no_tab_artwork",
        help="Don't show background artwork on tabs.",
    )
    group_tab.add_argument(
        "--tab-artwork-opacity",
        type=float,
        default=1.0,
        help="Multiply opacity of tab background art by this value; "
        "can be used to make text show up clearer on dark backrounds, "
        "particularly on printers that output darker than average",
    )
    group_tab.add_argument(
        "--use-text-set-icon",
        action="store_true",
        dest="use_text_set_icon",
        help="Use text/letters to represent a card's set instead of the set icon.",
    )
    group_tab.add_argument(
        "--use-set-icon",
        action="store_true",
        dest="use_set_icon",
        help="Use set icon instead of a card icon.  Applies to Promo cards.",
    )

    # Expanion Dividers
    group_expansion = parser.add_argument_group(
        "Expansion Dividers", "Adding separator dividers for each expansion."
    )
    group_expansion.add_argument(
        "--expansion-dividers",
        action="store_true",
        dest="expansion_dividers",
        help="Add dividers describing each expansion set. "
        "A list of cards in the expansion will be shown on the front of the divider.",
    )
    group_expansion.add_argument(
        "--centre-expansion-dividers",
        action="store_true",
        dest="centre_expansion_dividers",
        help="Centre the tabs on expansion dividers (same width as dividers.)",
    )
    group_expansion.add_argument(
        "--full-expansion-dividers",
        action="store_true",
        dest="full_expansion_dividers",
        help="Full width expansion dividers.",
    )
    group_expansion.add_argument(
        "--expansion-reset-tabs",
        action="store_true",
        dest="expansion_reset_tabs",
        help="When set, the tabs are restarted (left/right) at the beginning of each expansion. "
        "If not set, the tab pattern will continue from one expansion to the next. ",
    )
    group_expansion.add_argument(
        "--expansion-dividers-long-name",
        action="store_true",
        dest="expansion_dividers_long_name",
        help="Use the long name with edition information on the expansion divider tab. "
        "Without this, the shorter expansion name is used on the expansion divider tab.",
    )

    # Divider Selection
    group_select = parser.add_argument_group(
        "Divider Selection", "What expansions are used, and grouping of dividers."
    )
    group_select.add_argument(
        "--expansions",
        "--expansion",
        nargs="*",
        action="append",
        dest="expansions",
        help="Limit dividers to only the specified expansions. "
        "If no limits are set, then all expansions are included. "
        "Expansion names can also be given in the language specified by "
        "the --language parameter. Any expansion with a space in the name must "
        "be enclosed in double quotes. This may be called multiple times. "
        "Values are not case sensitive. Wildcards may be used: "
        "'*' any number of characters, '?' matches any single character, "
        "'[seq]' matches any character in seq, and '[!seq]' matches any character not in seq. "
        "For example, 'dominion*' will match all expansions that start with 'dominion'. "
        "Choices available in all languages include: {}".format(
            ", ".join("%s" % x for x in EXPANSION_CHOICES)
        ),
    )
    group_select.add_argument(
        "--fan",
        nargs="*",
        action="append",
        dest="fan",
        help="Add dividers from the specified fan made expansions. "
        "If this option is not used, no fan expansions will be included. "
        "Fan made expansion names can also be given in the language specified by "
        "the --language parameter. Any fan expansion with a space in the name must "
        "be enclosed in double quotes. This may be called multiple times. "
        "Values are not case sensitive. Wildcards may be used: "
        "'*' any number of characters, '?' matches any single character, "
        "'[seq]' matches any character in seq, and '[!seq]' matches any character not in seq. "
        "Choices available in all languages include: {}".format(
            ", ".join("%s" % x for x in FAN_CHOICES)
        ),
    )
    group_select.add_argument(
        "--exclude-expansions",
        "--exclude-expansion",
        nargs="*",
        action="append",
        metavar="EXCLUDED",
        dest="exclude_expansions",
        help="Limit dividers to not include the specified expansions. "
        "Useful if you want all the expansions, except for one or two. "
        "If an expansion is explicitly specified with both '--expansion' and "
        "'--exclude-expansion', then '--exclude-expansion' wins, and the "
        "expansion is NOT included. Expansion names can also be given in the "
        "language specified by the --language parameter. Any expansion with a "
        "space in the name must be enclosed in double quotes. This may be "
        "called multiple times.  Values are not case sensitive. Wildcards may "
        "be used. See the help for '--expansion' for details on wildcards. May "
        "be the name of an official expansion or fan expansion - see the help "
        "for --expansion and --fan for a list of possible names.",
    )
    group_select.add_argument(
        "--edition",
        choices=EDITION_CHOICES,
        dest="edition",
        default="all",
        help="Editions to include: "
        "'1' is for all 1st Editions; "
        "'2' is for all 2nd Editions; "
        "'latest' is for the latest edition for each expansion; "
        "'all' is for all editions of expansions; "
        " This can be combined with other options to refine the expansions to include in the output.",
    )
    group_select.add_argument(
        "--upgrade-with-expansion",
        action="store_true",
        dest="upgrade_with_expansion",
        help="Include any new edition upgrade cards with the expansion being upgraded.",
    )
    group_select.add_argument(
        "--base-cards-with-expansion",
        action="store_true",
        help="Print the base cards as part of the expansion (i.e., a divider for 'Silver' "
        "will be printed as both a 'Dominion' card and as an 'Intrigue 1st Edition' card). "
        "If this option is not given, all base cards are placed in their own 'Base' expansion.",
    )
    group_select.add_argument(
        "--group-special",
        "--special-card-groups",
        action="store_true",
        dest="group_special",
        help="Group cards that generally are used together "
        "(e.g., Shelters, Tournament and Prizes, Urchin/Mercenary, etc.).",
    )
    group_select.add_argument(
        "--group-kingdom",
        action="store_true",
        dest="group_kingdom",
        help="Group cards that have randomizers into the expansion, "
        "and those that don't have randomizers into the expansion's 'Extra' section.",
    )
    group_select.add_argument(
        "--group-global",
        nargs="*",
        action="append",
        dest="group_global",
        help="Group all cards of the specified types across all expansions into one 'Extras' divider. "
        "This may be called multiple times. Values are not case sensitive. "
        "Choices available include: {}".format(
            ", ".join("%s" % x for x in GROUP_GLOBAL_VALID)
        ),
    )
    group_select.add_argument(
        "--no-trash",
        action="store_true",
        dest="no_trash",
        help="Exclude Trash from cards.",
    )
    group_select.add_argument(
        "--curse10",
        action="store_true",
        dest="curse10",
        help="Package Curse cards into groups of ten cards.",
    )
    group_select.add_argument(
        "--start-decks",
        action="store_true",
        dest="start_decks",
        help="Include four start decks with the Base cards.",
    )
    group_select.add_argument(
        "--include-blanks",
        type=int,
        default=0,
        help="Number of blank dividers to include.",
    )
    group_select.add_argument(
        "--exclude-events",
        action="store_true",
        help="Group all 'Event' cards across all expansions into one divider."
        "Same as '--group-global Events'",
    )
    group_select.add_argument(
        "--exclude-landmarks",
        action="store_true",
        help="Group all 'Landmark' cards across all expansions into one divider."
        "Same as '--group-global landmarks'",
    )
    group_select.add_argument(
        "--exclude-projects",
        action="store_true",
        help="Group all 'Project' cards across all expansions into one divider."
        "Same as '--group-global projects'",
    )
    group_select.add_argument(
        "--exclude-ways",
        action="store_true",
        help="Group all 'Way' cards across all expansions into one divider."
        "Same as '--group-global ways'",
    )
    group_select.add_argument(
        "--only-type-any",
        "--only-type",
        "--type-any",
        nargs="*",
        action="append",
        dest="only_type_any",
        help="Limit dividers to only those with the specified types. "
        "A divider is kept if ANY of the provided types are associated with the divider. "
        "Default is all types are included. "
        "Any type with a space in the name must be enclosed in double quotes. "
        "Values are not case sensitive. "
        "Choices available in all languages include: {}".format(
            ", ".join("%s" % x for x in TYPE_CHOICES)
        ),
    )
    group_select.add_argument(
        "--only-type-all",
        "--type-all",
        nargs="*",
        action="append",
        dest="only_type_all",
        help="Limit dividers to only those with the specified types. "
        "A divider is kept if ALL of the provided types are associated with the divider. "
        "Any type with a space in the name must be enclosed in double quotes. "
        "Values are not case sensitive. "
        "Choices available in all languages include: {}".format(
            ", ".join("%s" % x for x in TYPE_CHOICES)
        ),
    )

    # Divider Sleeves/Wrappers
    group_wrapper = parser.add_argument_group(
        "Card Sleeves/Wrappers", "Generating dividers that are card sleeves/wrappers."
    )
    group_wrapper.add_argument(
        "--wrapper",
        action="store_true",
        dest="wrapper",
        help="Draw sleeves (aka wrapper) for the cards instead of a divider for the cards.",
    )
    group_wrapper.add_argument(
        "--thickness",
        type=float,
        default=2.0,
        help="Thickness of a stack of 60 cards (Copper) in centimeters. "
        "Typically unsleeved cards are 2.0, thin sleeved cards are 2.4, and thick sleeved cards are 3.2. "
        "This is only valid with the --wrapper option.",
    )
    group_wrapper.add_argument(
        "--sleeved-thick",
        action="store_true",
        dest="sleeved_thick",
        help="Same as --size=sleeved --thickness 3.2.",
    )
    group_wrapper.add_argument(
        "--sleeved-thin",
        action="store_true",
        dest="sleeved_thin",
        help="Same as --size=sleeved --thickness 2.4.",
    )
    group_wrapper.add_argument(
        "--notch-length",
        type=float,
        default=0.0,
        help="Length of thumb notch on wrapper in centimeters "
        "(a value of 0.0 means no notch on wrapper). "
        "This can make it easier to remove the actual cards from the wrapper. "
        "This is only valid with the --wrapper option.",
    )
    group_wrapper.add_argument(
        "--notch",
        action="store_true",
        dest="notch",
        help="Same as --notch_length thickness 1.5.",
    )

    # Printing
    group_printing = parser.add_argument_group(
        "Printing", "Changes how the Dividers are printed."
    )
    group_printing.add_argument(
        "--minmargin",
        dest="minmargin",
        default="1x1",
        help="Page margin in cm in the form '<%%f>x<%%f>', left/right x top/bottom).",
    )
    group_printing.add_argument(
        "--cropmarks",
        action="store_true",
        dest="cropmarks",
        help="Print crop marks on both sides, rather than tab outlines on the front side.",
    )
    group_printing.add_argument(
        "--linewidth",
        type=float,
        default=0.1,
        help="Width of lines for card outlines and crop marks.",
    )
    group_printing.add_argument(
        "--front-offset",
        type=float,
        dest="front_offset",
        default=0,
        help="Front page horizontal offset points to shift to the right. Only needed for some printers.",
    )
    group_printing.add_argument(
        "--front-offset-height",
        type=float,
        dest="front_offset_height",
        default=0,
        help="Front page vertical offset points to shift upward. Only needed for some printers.",
    )
    group_printing.add_argument(
        "--back-offset",
        type=float,
        dest="back_offset",
        default=0,
        help="Back page horizontal offset points to shift to the right. Only needed for some printers.",
    )
    group_printing.add_argument(
        "--back-offset-height",
        type=float,
        dest="back_offset_height",
        default=0,
        help="Back page vertical offset points to shift upward. Only needed for some printers.",
    )
    group_printing.add_argument(
        "--vertical-gap",
        type=float,
        default=0.0,
        help="Vertical gap between dividers in centimeters.",
    )
    group_printing.add_argument(
        "--horizontal-gap",
        type=float,
        default=0.0,
        help="Horizontal gap between dividers in centimeters.",
    )
    group_printing.add_argument(
        "--no-page-footer",
        action="store_true",
        dest="no_page_footer",
        help="Do not print the expansion name at the bottom of the page.",
    )
    group_printing.add_argument(
        "--num-pages",
        type=int,
        default=-1,
        help="Stop generating dividers after this many pages, -1 for all.",
    )
    group_printing.add_argument(
        "--tabs-only",
        action="store_true",
        dest="tabs_only",
        help="Draw only the divider tabs and no divider outlines. "
        "Used to print the divider tabs on labels.",
    )
    group_printing.add_argument(
        "--black-tabs",
        action="store_true",
        help="In tabs-only mode, draw tabs on black background",
    )
    group_printing.add_argument(
        "--linetype",
        choices=LINE_CHOICES,
        dest="linetype",
        default="line",
        help="The divider outline type. "
        "'line' will print a solid line outlining the divider; "
        "'dot' will print a dot at each corner of the divider; "
        "'cropmarks' will print cropmarks for the divider; "
        "'dot-cropmarks' will combine 'dot' and 'cropmarks'",
    )
    group_printing.add_argument(
        "--cropmarkLength",
        type=float,
        default=0.2,
        help="Length of actual drawn cropmark in centimeters.",
    )
    group_printing.add_argument(
        "--cropmarkSpacing",
        type=float,
        default=0.1,
        help="Spacing between card and the start of the cropmark in centimeters.",
    )
    group_printing.add_argument(
        "--rotate",
        type=int,
        choices=[0, 90, 180, 270],
        default=0,
        help="Divider degrees of rotation relative to the page edge. "
        "No optimization will be done on the number of dividers per page.",
    )
    group_printing.add_argument(
        "--label",
        dest="label_name",
        choices=LABEL_CHOICES,
        default=None,
        help="Use preset label dimentions. Specify a label name. "
        "This will override settings that conflict with the preset label settings.",
    )
    group_printing.add_argument(
        "--info",
        action="store_true",
        dest="info",
        help="Add a page that has all the options used for the file.",
    )
    group_printing.add_argument(
        "--info-all",
        action="store_true",
        dest="info_all",
        help="Same as --info, but includes pages with all the possible options that can be used.",
    )
    group_printing.add_argument(
        "--preview",
        action="store_true",
        help="Only generate a preview png image of the first page",
    )
    group_printing.add_argument(
        "--preview-resolution",
        type=int,
        default=150,
        help="resolution in DPI to render preview at, for --preview option",
    )
    # Special processing
    group_special = parser.add_argument_group(
        "Miscellaneous", "These options are generally not used."
    )
    group_special.add_argument(
        "--cardlist",
        dest="cardlist",
        help="Path to file that enumerates each card to be printed on its own line.",
    )
    group_special.add_argument(
        "--write-json",
        action="store_true",
        dest="write_json",
        help="Write json version of card definitions and extras.",
    )
    group_special.add_argument(
        "-c",
        is_config_file=True,
        help="Use the specified configuration file to provide options. "
        "Command line options override options from this file.",
    )
    group_special.add_argument(
        "-w",
        is_write_out_config_file_arg=True,
        help="Write out the given options to the specified configuration file.",
    )

    options = parser.parse_args(args=cmdline_args)
    # Need to do these while we have access to the parser
    options.argv = sys.argv if options.info or options.info_all else None
    options.help = parser.format_help() if options.info_all else None
    return options


def clean_opts(options):

    if "center" in options.tab_side:
        options.tab_side = str(options.tab_side).replace("center", "centre")

    if "center" in options.tab_name_align:
        options.tab_name_align = str(options.tab_name_align).replace("center", "centre")

    if options.tab_side == "full" and options.tab_name_align == "edge":
        # This case does not make sense since there are two tab edges in this case.  So picking left edge.
        print("** Warning: Aligning card name as 'left' for 'full' tabs **")
        options.tab_name_align = "left"

    if options.tab_number < 1:
        print("** Warning: --tab-number must be 1 or greater.  Setting to 1. **")
        options.tab_number = 1

    if options.tab_side == "full" and options.tab_number != 1:
        options.tab_number = 1  # Full is 1 big tab

    if "-alternate" in options.tab_side:
        if options.tab_number != 2:
            print(
                "** Warning: --tab-side with 'alternate' implies 2 tabs. Setting --tab-number to 2 **"
            )
        options.tab_number = 2  # alternating left and right, so override tab_number

    if "-flip" in options.tab_side:
        # for left and right tabs
        if options.tab_number != 2:
            print(
                "** Warning: --tab-side with 'flip' implies 2 tabs. Setting --tab-number to 2 **"
            )
        options.tab_number = (
            2  # alternating left and right with a flip, so override tab_number
        )
        options.flip = True
    else:
        options.flip = False

    if options.tab_number < 3 and options.tab_serpentine:
        print("** Warning: --tab-serpentine only valid if --tab-number > 2. **")
        options.tab_serpentine = False

    if options.cost is None:
        options.cost = ["tab"]

    if options.set_icon is None:
        options.set_icon = ["tab"]

    if options.sleeved_thick:
        options.thickness = 3.2
        options.sleeved = True

    if options.sleeved_thin:
        options.thickness = 2.4
        options.sleeved = True

    if options.notch:
        options.notch_length = 1.5

    if options.notch_length > 0:
        options.notch_height = 0.25  # thumb notch height

    if options.cropmarks and options.linetype == "line":
        options.linetype = "cropmarks"

    if options.linetype == "cropmarks":
        options.cropmarks = True

    if options.linetype == "dot-cropmarks":
        options.linetype = "dot"
        options.cropmarks = True

    if options.expansions is None:
        # No instance given, so default to all Official expansions
        options.expansions = ["*"]
    else:
        # options.expansions is a list of lists.  Reduce to single lowercase list
        options.expansions = [
            item.lower() for sublist in options.expansions for item in sublist
        ]
    if "none" in options.expansions:
        # keyword to indicate no options.  Same as --expansions without any expansions given.
        options.expansions = []

    if options.exclude_expansions:
        # options.exclude_expansions is a list of lists.  Reduce to single lowercase list
        options.exclude_expansions = [
            item.lower() for sublist in options.exclude_expansions for item in sublist
        ]

    if options.fan is None:
        # No instance given, so default to no Fan expansions
        options.fan = []
    else:
        # options.fan is a list of lists.  Reduce to single lowercase list
        options.fan = [item.lower() for sublist in options.fan for item in sublist]
    if "none" in options.fan:
        # keyword to indicate no options.  Same as --fan without any expansions given
        options.fan = []

    if options.only_type_any is None:
        # No instance given, so default to empty list
        options.only_type_any = []
    else:
        # options.only_type_any is a list of lists.  Reduce to single lowercase list
        options.only_type_any = list(
            set([item.lower() for sublist in options.only_type_any for item in sublist])
        )

    if options.only_type_all is None:
        # No instance given, so default to empty list
        options.only_type_all = []
    else:
        # options.only_type_any is a list of lists.  Reduce to single lowercase list
        options.only_type_all = list(
            set([item.lower() for sublist in options.only_type_all for item in sublist])
        )

    if options.group_global is None:
        options.group_global = []
    elif not any(options.group_global):
        # option given with nothing indicates all possible global groupings
        options.group_global = GROUP_GLOBAL_VALID
    else:
        # options.group_global is a list of lists.  Reduce to single lowercase list
        options.group_global = [
            item.lower() for sublist in options.group_global for item in sublist
        ]
    # For backwards compatibility
    if options.exclude_events:
        options.group_global.append("events")
    if options.exclude_landmarks:
        options.group_global.append("landmarks")
    if options.exclude_projects:
        options.group_global.append("projects")
    if options.exclude_ways:
        options.group_global.append("ways")
    # Remove duplicates from the list
    options.group_global = list(set(options.group_global))

    if options.tabs_only and options.label_name is None:
        # default is Avery 8867
        options.label_name = "8867"

    options.label = None
    if options.label_name is not None:
        for label in LABEL_INFO:
            if options.label_name.upper() in [n.upper() for n in label["names"]]:
                options.label = label
                break

        assert options.label is not None, "Label '{}' not defined".format(
            options.label_name
        )

        # Defaults for missing values
        label = options.label
        label["paper"] = label["paper"] if "paper" in label else "LETTER"
        label["tab-only"] = label["tab-only"] if "tab-only" in label else True
        label["tab-height"] = (
            label["tab-height"] if "tab-height" in label else label["height"]
        )
        label["body-height"] = (
            label["body-height"]
            if "body-height" in label
            else label["height"] - label["tab-height"]
        )
        label["gap-vertical"] = (
            label["gap-vertical"] if "gap-vertical" in label else 0.0
        )
        label["gap-horizontal"] = (
            label["gap-horizontal"] if "gap-horizontal" in label else 0.0
        )
        label["pad-vertical"] = (
            label["pad-vertical"] if "pad-vertical" in label else 0.1
        )
        label["pad-horizontal"] = (
            label["pad-horizontal"] if "pad-horizontal" in label else 0.1
        )

        # Option Overrides when using labels
        MIN_BODY_CM_FOR_COUNT = 0.6
        MIN_BODY_CM_FOR_TEXT = 4.0
        MIN_HEIGHT_CM_FOR_VERTICAL = 5.0
        MIN_WIDTH_CM_FOR_FULL = 5.0

        options.linewidth = 0.0
        options.cropmarks = False
        options.wrapper = False
        options.papersize = label["paper"]
        if label["tab-only"]:
            options.tabs_only = True
        if label["body-height"] < MIN_BODY_CM_FOR_TEXT:
            # Not enough room for any text
            options.text_front = "blank"
            options.text_back = "blank"
        if label["body-height"] < MIN_BODY_CM_FOR_COUNT:
            # Not enough room for count and type
            options.count = False
            options.types = False
        if label["height"] < MIN_HEIGHT_CM_FOR_VERTICAL:
            # Not enough room to make vertical
            options.orientation = "horizontal"
        if (
            options.label["width"] - 2 * options.label["pad-horizontal"]
        ) < MIN_WIDTH_CM_FOR_FULL:
            options.tab_side = "full"
        options.label = label

    return options


def parseDimensions(dimensionsStr):
    x, y = dimensionsStr.upper().split("X", 1)
    return (float(x) * cm, float(y) * cm)


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


def parse_papersize(spec):
    papersize = None
    if not spec:
        if os.path.exists("/etc/papersize"):
            papersize = open("/etc/papersize").readline().upper()
        else:
            papersize = "LETTER"
    else:
        papersize = spec.upper()

    try:
        paperwidth, paperheight = getattr(pagesizes, papersize)
    except AttributeError:
        try:
            paperwidth, paperheight = parseDimensions(papersize)
            print(
                (
                    "Using custom paper size, {:.2f}cm x {:.2f}cm".format(
                        paperwidth / cm, paperheight / cm
                    )
                )
            )
        except ValueError:
            paperwidth, paperheight = pagesizes.LETTER
    return paperwidth, paperheight


def parse_cardsize(spec, sleeved):
    spec = spec.upper()
    if spec == "SLEEVED" or sleeved:
        dominionCardWidth, dominionCardHeight = (9.4 * cm, 6.15 * cm)
        print(
            (
                "Using sleeved card size, {:.2f}cm x {:.2f}cm".format(
                    dominionCardWidth / cm, dominionCardHeight / cm
                )
            )
        )
    elif spec in ["NORMAL", "UNSLEEVED"]:
        dominionCardWidth, dominionCardHeight = (9.1 * cm, 5.9 * cm)
        print(
            (
                "Using normal card size, {:.2f}cm x{:.2f}cm".format(
                    dominionCardWidth / cm, dominionCardHeight / cm
                )
            )
        )
    else:
        dominionCardWidth, dominionCardHeight = parseDimensions(spec)
        print(
            (
                "Using custom card size, {:.2f}cm x {:.2f}cm".format(
                    dominionCardWidth / cm, dominionCardHeight / cm
                )
            )
        )
    return dominionCardWidth, dominionCardHeight


def find_index_of_object(lst=[], attributes={}):
    # Returns the index of the first object in lst that matches the given attributes.  Otherwise returns None.
    # attributes is a dict of key: value pairs.   Object attributes that are lists are checked to have value in them.
    for i, d in enumerate(lst):
        # Set match to false just in case there are no attributes.
        match = False
        for key, value in attributes.items():
            # if anything does not match, then break out and start the next one.
            match = hasattr(d, key)
            if match:
                test = getattr(d, key, None)
                if type(test) is list:
                    match = value in test
                else:
                    match = value == test
            if not match:
                break

        if match:
            # If all the attributes are found, then we have a match
            return i

    # nothing matched
    return None


def read_card_data(options):

    # Read in the card types
    types_db_filepath = os.path.join("card_db", "types_db.json")
    with get_resource_stream(types_db_filepath) as typefile:
        Card.types = json.loads(
            typefile.read().decode("utf-8"), object_hook=CardType.decode_json
        )
    assert Card.types, "Could not load any card types from database"

    # extract unique types
    type_list = []
    for c in Card.types:
        type_list = list(set(c.getTypeNames()) | set(type_list))
    # set up the basic type translation.  The actual language will be added later.
    Card.type_names = {}
    for t in type_list:
        Card.type_names[t] = t

    # turn Card.types into a dictionary for later
    Card.types = dict(((c.getTypeNames(), c) for c in Card.types))

    # Read in the card database
    card_db_filepath = os.path.join("card_db", "cards_db.json")
    with get_resource_stream(card_db_filepath) as cardfile:
        cards = json.loads(
            cardfile.read().decode("utf-8"), object_hook=Card.decode_json
        )
    assert cards, "Could not load any cards from database"

    set_db_filepath = os.path.join("card_db", "sets_db.json")
    with get_resource_stream(set_db_filepath) as setfile:
        Card.sets = json.loads(setfile.read().decode("utf-8"))
    assert Card.sets, "Could not load any sets from database"
    new_sets = {}
    for s in Card.sets:
        # Make sure these are set either True or False
        Card.sets[s]["no_randomizer"] = Card.sets[s].get("no_randomizer", False)
        Card.sets[s]["fan"] = Card.sets[s].get("fan", False)
        Card.sets[s]["has_extras"] = Card.sets[s].get("has_extras", True)
        Card.sets[s]["upgrades"] = Card.sets[s].get("upgrades", None)
        new_sets[s] = Card.sets[s]
        # Make an "Extras" set for normal expansions
        if Card.sets[s]["has_extras"]:
            e = s + EXPANSION_EXTRA_POSTFIX
            new_sets[e] = copy.deepcopy(Card.sets[s])
            new_sets[e]["set_name"] = "*" + s + EXPANSION_EXTRA_POSTFIX + "*"
            new_sets[e]["no_randomizer"] = True
            new_sets[e]["has_extras"] = False
    Card.sets = new_sets

    # Remove the Trash card. Do early before propagating to various sets.
    if options.no_trash:
        i = find_index_of_object(cards, {"card_tag": "Trash"})
        if i is not None:
            del cards[i]

    # Repackage Curse cards into 10 per divider. Do early before propagating to various sets.
    if options.curse10:
        i = find_index_of_object(cards, {"card_tag": "Curse"})
        if i is not None:
            new_cards = []
            cards_remaining = cards[i].getCardCount()
            while cards_remaining > 10:
                # make a new copy of the card and set count to 10
                new_card = copy.deepcopy(cards[i])
                new_card.setCardCount(10)
                new_cards.append(new_card)
                cards_remaining -= 10

            # Adjust original Curse card to the remaining cards (should be 10)
            cards[i].setCardCount(cards_remaining)
            # Add the new dividers
            cards.extend(new_cards)

    # Add any blank cards
    if options.include_blanks > 0:
        for x in range(0, options.include_blanks):
            c = Card(
                card_tag="Blank",
                cardset=EXPANSION_GLOBAL_GROUP,
                cardset_tag=EXPANSION_GLOBAL_GROUP,
                cardset_tags=[EXPANSION_GLOBAL_GROUP],
                randomizer=False,
                types=("Blank",),
            )
            cards.append(c)

    # Create Start Deck dividers. 4 sets. Adjust totals for other cards, too.
    # Do early before propagating to various sets.
    # The card database contains one prototype divider that needs to be either duplicated or deleted.
    if options.start_decks:
        # Find the index to the individual cards that need changed in the cards list
        StartDeck_index = find_index_of_object(cards, {"card_tag": "Start Deck"})
        Copper_index = find_index_of_object(cards, {"card_tag": "Copper"})
        Estate_index = find_index_of_object(cards, {"card_tag": "Estate"})
        if Copper_index is None or Estate_index is None or StartDeck_index is None:
            # Something is wrong, can't find one or more of the cards that need to change
            print("Error - cannot create Start Decks")

            # Remove the Start Deck prototype if we can
            if StartDeck_index is not None:
                del cards[StartDeck_index]
        else:
            # Start Deck Constants
            STARTDECK_COPPERS = 7
            STARTDECK_ESTATES = 3
            STARTDECK_NUMBER = 4

            # Add correct card counts to Start Deck prototype.  This will be used to make copies.
            cards[StartDeck_index].setCardCount(STARTDECK_COPPERS)
            cards[StartDeck_index].addCardCount([int(STARTDECK_ESTATES)])

            # Make new Start Deck Dividers and adjust the corresponding card counts
            for x in range(0, STARTDECK_NUMBER):
                # Add extra copies of the Start Deck prototype.
                # But don't need to add the first one again, since the prototype is already there.
                if x > 0:
                    cards.append(copy.deepcopy(cards[StartDeck_index]))
                    # Note: By appending, it should not change any of the index values being used

                # Remove Copper and Estate card counts from their dividers
                cards[Copper_index].setCardCount(
                    cards[Copper_index].getCardCount() - STARTDECK_COPPERS
                )
                cards[Estate_index].setCardCount(
                    cards[Estate_index].getCardCount() - STARTDECK_ESTATES
                )
    else:
        # Remove Start Deck prototype.  It is not needed.
        StartDeck_index = find_index_of_object(cards, {"card_tag": "Start Deck"})
        if StartDeck_index is not None:
            del cards[StartDeck_index]

    # Set cardset_tag and expand cards that are used in multiple sets
    new_cards = []
    for card in cards:
        sets = list(card.cardset_tags)
        if len(sets) > 0:
            # Set and save the first one
            card.cardset_tag = sets.pop(0)
            new_cards.append(card)
            for s in sets:
                # for the rest, create a copy of the first
                if s:
                    new_card = copy.deepcopy(card)
                    new_card.cardset_tag = s
                    new_cards.append(new_card)
    cards = new_cards

    # Make sure each card has the right image file.
    for card in cards:
        card.image = card.setImage()

    return cards


class CardSorter(object):
    def __init__(self, order, baseCards):
        self.order = order
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
            self.strip_accents(card.name),
        )

    def by_expansion_sort_key(self, card):
        return (
            card.cardset,
            int(card.isExpansion()),
            self.baseIndex(card.name),
            self.strip_accents(card.name),
        )

    def by_colour_sort_key(self, card):
        return card.getType().getTypeNames(), self.strip_accents(card.name)

    def by_cost_sort_key(self, card):
        return (
            card.cardset,
            int(card.isExpansion()),
            str(card.get_total_cost(card)),
            self.strip_accents(card.name),
        )

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
        "card_db", language, "cards_" + language.lower() + ".json"
    )
    with get_resource_stream(card_text_filepath) as card_text_file:
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
    set_text_filepath = os.path.join(
        "card_db", language, "sets_{}.json".format(language)
    )
    with get_resource_stream(set_text_filepath) as set_text_file:
        set_text = json.loads(set_text_file.read().decode("utf-8"))
    assert set_text, "Could not load set text for %r" % language

    # Now apply to all the sets
    for s in sets:
        if s in set_text:
            for key in set_text[s]:
                sets[s][key] = set_text[s][key]
    return sets


def add_type_text(types={}, language="en_us"):
    language = language.lower()
    # Read in the type text and store for later
    type_text_filepath = os.path.join(
        "card_db", language, "types_{}.json".format(language)
    )
    with get_resource_stream(type_text_filepath) as type_text_file:
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
        "card_db", language, "bonuses_{}.json".format(language)
    )
    with get_resource_stream(bonus_regex_filepath) as bonus_regex_file:
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
        for card in cards:
            if Card.sets[card.cardset_tag]["upgrades"]:
                card.cardset_tag = Card.sets[card.cardset_tag]["upgrades"]
                options.expansions.append(card.cardset_tag.lower())

    # Combine globally all cards of the given types
    # For example, Events, Landmarks, Projects, Ways
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
                new_cardset_tag=EXPANSION_GLOBAL_GROUP,
            )
        if options.expansions:
            options.expansions.append(EXPANSION_GLOBAL_GROUP)

    # Take care of any blank cards
    if options.include_blanks > 0:
        if options.expansions:
            options.expansions.append(EXPANSION_GLOBAL_GROUP)

    # Group all the special cards together
    if options.group_special:
        keep_cards = []  # holds the cards that are to be kept
        group_cards = {}  # holds the cards for each group
        for card in cards:
            if not card.group_tag:
                keep_cards.append(card)  # not part of a group, so just keep the card
            else:
                # have a card in a group
                if card.group_tag not in group_cards:
                    # First card of a group
                    group_cards[card.group_tag] = card  # save to update cost later
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
                        group_cards[card.group_tag].cost = card.cost
                        group_cards[card.group_tag].potcost = card.potcost
                        group_cards[card.group_tag].debtcost = card.debtcost
                        group_cards[card.group_tag].types = card.types
                        group_cards[card.group_tag].randomizer = card.randomizer
                        group_cards[card.group_tag].image = card.image

                    group_cards[card.group_tag].addCardCount(
                        card.count
                    )  # increase the count
                    # group_cards[card.group_tag].set_lowest_cost(card)  # set holder to lowest cost of the two cards

        cards = keep_cards

        # Now fix up card costs for groups by Type (Events, Landmarks, etc.)
        for card in cards:
            if (
                card.card_tag in group_cards
                and group_cards[card.group_tag].get_GroupCost()
            ):
                group_cards[card.group_tag].cost = group_cards[
                    card.group_tag
                ].get_GroupCost()
                group_cards[card.group_tag].debtcost = 0
                group_cards[card.group_tag].potcost = 0

    # Separate Kingdom (with Randomizer) from non-Kingdom cards (without Randomizer)
    if options.group_kingdom:
        new_cards = []
        new_sets = {}
        for card in cards:
            if not card.randomizer and Card.sets[card.cardset_tag]["has_extras"]:
                card.cardset_tag += EXPANSION_EXTRA_POSTFIX
                new_sets[card.cardset_tag] = True
            new_cards.append(card)
        cards = new_cards
        if options.expansions and new_cards:
            # Add the new expansion "extras" to the overall expansion list
            options.expansions.extend([s for s in new_sets])

    # Get the final type names in the requested language
    Card.type_names = add_type_text(Card.type_names, LANGUAGE_DEFAULT)
    if options.language != LANGUAGE_DEFAULT:
        Card.type_names = add_type_text(Card.type_names, options.language)
    for card in cards:
        card.types_name = " - ".join([Card.type_names[t] for t in card.types]).upper()

    # Get the card bonus keywords in the requested language
    bonus = add_bonus_regex(options, LANGUAGE_DEFAULT)
    Card.addBonusRegex(bonus)
    if options.language != LANGUAGE_DEFAULT:
        bonus = add_bonus_regex(options, options.language)
        Card.addBonusRegex(bonus)

    # Fix up cardset text.  Waited as long as possible.
    Card.sets = add_set_text(options, Card.sets, LANGUAGE_DEFAULT)
    if options.language != LANGUAGE_DEFAULT:
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
            print(
                (
                    "Error - unknown expansion(s): {}".format(
                        ", ".join(unknownExpansions)
                    )
                )
            )

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
            print(
                (
                    "Error - unknown expansion(s): {}".format(
                        ", ".join(unknownExpansions)
                    )
                )
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
            print(
                "Error - unknown exclude expansion(s): %s"
                % ", ".join(unknownExpansions)
            )

    # Now keep only the cards that are in the sets that have been requested
    keep_cards = []
    for c in cards:
        if c.cardset_tag in wantedSets:
            # Add the cardset informaiton to the card and add it to the list of cards to use
            c.cardset = Card.sets[c.cardset_tag].get("set_name", c.cardset_tag)
            keep_cards.append(c)
    cards = keep_cards

    # Now add text to the cards.  Waited as long as possible to catch all groupings
    cards = add_card_text(cards, LANGUAGE_DEFAULT)
    if options.language != LANGUAGE_DEFAULT:
        cards = add_card_text(cards, options.language)

    # Get list of cards from a file
    if options.cardlist:
        cardlist = set()
        with open(options.cardlist) as cardfile:
            for line in cardfile:
                cardlist.add(line.strip())
        if cardlist:
            cards = [card for card in cards if card.name in cardlist]

    # Set up the card sorter
    cardSorter = CardSorter(
        options.order,
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
                    % (order, CardSorter.strip_accents(c.name.strip())),
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


def calculate_layout(options, cards=[]):
    # This is in place to allow for test cases to it call directly to get
    options = clean_opts(options)
    options.dominionCardWidth, options.dominionCardHeight = parse_cardsize(
        options.size, options.sleeved
    )
    options.paperwidth, options.paperheight = parse_papersize(options.papersize)
    options.minmarginwidth, options.minmarginheight = parseDimensions(options.minmargin)

    dd = DividerDrawer(options)
    dd.calculatePages(cards)
    return dd


def generate(options):

    cards = read_card_data(options)
    assert cards, "No cards after reading"
    cards = filter_sort_cards(cards, options)
    assert cards, "No cards after filtering/sorting"

    dd = calculate_layout(options, cards)

    print(
        "Paper dimensions: {:.2f}cm (w) x {:.2f}cm (h)".format(
            options.paperwidth / cm, options.paperheight / cm
        )
    )
    print(
        "Tab dimensions: {:.2f}cm (w) x {:.2f}cm (h)".format(
            options.dividerWidthReserved / cm, options.dividerHeightReserved / cm
        )
    )
    print(
        "{} dividers horizontally, {} vertically".format(
            options.numDividersHorizontal, options.numDividersVertical
        )
    )
    print(
        "Margins: {:.2f}cm h, {:.2f}cm v\n".format(
            options.horizontalMargin / cm, options.verticalMargin / cm
        )
    )

    dd.draw(cards)


def main():
    options = parse_opts()
    options = clean_opts(options)
    if options.preview:
        fname = "{}.{}".format(os.path.splitext(options.outfile)[0], "png")
        open(fname, "wb").write(generate_sample(options).getvalue())
    else:
        generate(options)
