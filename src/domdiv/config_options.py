import os
import sys

import configargparse
import reportlab.lib.pagesizes as pagesizes
from loguru import logger
from reportlab.lib.units import cm

from . import db

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
LINE_CHOICES = ["line", "dot", "cropmarks", "line-cropmarks", "dot-cropmarks"]

HEAD_CHOICES = ["tab", "strap", "cover", "none"]
TAIL_CHOICES = ["tab", "strap", "cover", "folder", "none"]
FACE_CHOICES = ["front", "back"]
SPINE_CHOICES = ["name", "types", "tab", "blank"]

EDITION_CHOICES = ["1", "2", "latest", "upgrade", "removed", "all"]

ORDER_CHOICES = ["expansion", "global", "colour", "cost"]

EXPANSION_GLOBAL_GROUP = "extras"


def add_opt(options, option, value):
    assert not hasattr(options, option)
    setattr(options, option, value)


def parse_opts(cmdline_args=None):
    parser = configargparse.ArgParser(
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter,
        description="Generate Dominion Dividers",
        epilog="Source can be found at 'https://github.com/sumpfork/dominiontabs'. "
        "An online version can be found at 'http://domdiv.bgtools.net/'. ",
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
        default=db.LANGUAGE_DEFAULT,
        choices=db.get_languages(),
        help="Language of divider text.",
    )
    group_basic.add_argument(
        "--font-dir",
        help="A directory path to scan for font files, preferring them over fonts in the domdiv package",
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
        help="Dimensions of the cards to use with the dividers '<%%f>x<%%f>' (size in cm), "
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
        default=2,
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
        "--tab-artwork-resolution",
        type=int,
        default=0,
        help="Limit the DPI resolution of tab background art.  "
        "If nonzero, any higher-resolution images will be resized to "
        "reduce output file size.",
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
    group_tab.add_argument(
        "--expansion-reset-tabs",
        action="store_true",
        dest="expansion_reset_tabs",
        help="When set, the tabs are restarted (left/right) at the beginning of each expansion. "
        "If not set, the tab pattern will continue from one expansion to the next. ",
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
        "If no limits are set, then the latest expansions are included. "
        "Expansion names can also be given in the language specified by "
        "the --language parameter. Any expansion with a space in the name must "
        "be enclosed in double quotes. This may be called multiple times. "
        "Values are not case sensitive. Wildcards may be used: "
        "'*' any number of characters, '?' matches any single character, "
        "'[seq]' matches any character in seq, and '[!seq]' matches any character not in seq. "
        "For example, 'dominion*' will match all expansions that start with 'dominion'. "
        "Choices available in all languages include: {}".format(
            ", ".join("%s" % x for x in db.get_expansions()[0])
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
            ", ".join("%s" % x for x in db.get_expansions()[1])
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
        help="Editions to include: "
        "'1' is for all 1st Editions; "
        "'2' is for all 2nd Editions; "
        "'upgrade' is for all upgrade cards for each expansion; "
        "'removed' is for all removed cards for each expansion; "
        "'latest' is for the latest edition for each expansion; "
        "'all' is for all editions of expansions, upgrade cards, and removed cards; "
        " This can be combined with other options to refine the expansions to include in the output."
        " (default: all)",
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
            ", ".join("%s" % x for x in db.get_global_groups()[1])
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
        "--exclude-traits",
        action="store_true",
        help="Group all 'Trait' cards across all expansions into one divider."
        "Same as '--group-global traits'",
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
            ", ".join("%s" % x for x in db.get_types())
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
            ", ".join("%s" % x for x in db.get_types())
        ),
    )

    # Divider Sleeves/Wrappers
    group_wrapper = parser.add_argument_group(
        "Card Sleeves/Wrappers", "Generating dividers that are card sleeves/wrappers."
    )
    group_wrapper.add_argument(
        "--wrapper",
        action="store_true",
        dest="wrapper_meta",
        help="Draw sleeves (wrappers) instead of dividers for the cards. "
        "Same as --head=strap --tail=folder",
    )
    group_wrapper.add_argument(
        "--pull-tab",
        action="store_true",
        dest="pull_tab_meta",
        help="Draw folding pull tabs instead of dividers for the cards. "
        "Same as --head=tab --tail=cover",
    )
    group_wrapper.add_argument(
        "--tent",
        action="store_true",
        dest="tent_meta",
        help="Draw folding tent covers instead of dividers for the cards. "
        "Same as --head=cover --head-facing=back --head-text=back "
        "--tail=tab --tail-facing=front",
    )
    group_wrapper.add_argument(
        "--head",
        choices=HEAD_CHOICES,
        dest="head",
        default="tab",
        help="Top tab or wrapper type: "
        "'tab' for divider tabs, "
        "'strap' for longer folding tabs, "
        "'cover' for matchbook-style folding covers, "
        "or 'none' to leave the top edge plain. "
        "The folding options create a top spine that you can customize "
        "with --spine.",
    )
    group_wrapper.add_argument(
        "--tail",
        choices=TAIL_CHOICES,
        dest="tail",
        default="none",
        help="Bottom tab or wrapper type: "
        "'tab' for a bottom tab banner, "
        "'strap' for a pull tab under the cards, "
        "'cover' for a simple back cover, "
        "'folder' to create tab folders, "
        "or 'none' to leave the bottom edge plain.",
    )
    group_wrapper.add_argument(
        "--head-facing",
        choices=FACE_CHOICES,
        dest="head_facing",
        default="front",
        help="Text orientation for top tabs and wrappers: "
        "'front' shows the text upright when flat, "
        "'back' shows it upright when folded over.",
    )
    group_wrapper.add_argument(
        "--tail-facing",
        choices=FACE_CHOICES,
        dest="tail_facing",
        default="back",
        help="Text orientation for tail wrappers: "
        "'front' shows the text upright when flat, "
        "'back' shows it upright when folded under.",
    )
    group_wrapper.add_argument(
        "--head-text",
        choices=TEXT_CHOICES + FACE_CHOICES,
        dest="head_text",
        default="blank",
        help="Text to print on top cover panels: "
        "'card' shows the text from the game card, "
        "'rules' shows additional rules for the game card, "
        "'blank' leaves the panel blank; "
        "'front' uses the same setting as --front; "
        "'back' uses the same setting as --back.",
    )
    group_wrapper.add_argument(
        "--tail-text",
        choices=TEXT_CHOICES + FACE_CHOICES,
        dest="tail_text",
        default="back",
        help="Text to print on bottom folder panels: "
        "'card' shows the text from the game card, "
        "'rules' shows additional rules for the game card, "
        "'blank' leaves the panel blank; "
        "'front' uses the same setting as --front; "
        "'back' uses the same setting as --back.",
    )
    group_wrapper.add_argument(
        "--head-height",
        type=float,
        default=0.0,
        help="Height of the top panel in centimeters "
        "(a value of 0 uses tab height or card height as appropriate).",
    )
    group_wrapper.add_argument(
        "--tail-height",
        type=float,
        default=0.0,
        help="Height of the bottom panel in centimeters "
        "(a value of 0 uses tab height or card height as appropriate).",
    )
    group_wrapper.add_argument(
        "--spine",
        choices=SPINE_CHOICES,
        dest="spine",
        default="name",
        help="Text to print on the spine of top covers: "
        "'name' prints the card name; "
        "'type' prints the card type; "
        "'tab' prints tab text and graphics; "
        "'blank' leaves the spine blank. "
        "This is only valid with folding --head options.",
    )
    group_wrapper.add_argument(
        "--thickness",
        type=float,
        default=2.0,
        help="Thickness of a stack of 60 cards (Copper) in centimeters. "
        "Typically unsleeved cards are 2.0, thin sleeved cards are 2.4, and thick sleeved cards are 3.2. "
        "This is only valid with --wrapper or other folding options.",
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
        "--notch",
        action="store_true",
        dest="notch",
        help="Creates thumb notches opposite to the divider tabs, "
        "which can make it easier to remove cards from wrappers or stacks. "
        "Equivalent to --notch-length=1.5 --notch-height=0.25",
    )
    group_wrapper.add_argument(
        "--notch-length",
        type=float,
        default=0.0,
        help="Sets the length of thumb notches in centimeters.",
    )
    group_wrapper.add_argument(
        "--notch-height",
        type=float,
        default=0.0,
        help="Sets the height of thumb notches in centimeters.",
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
        "'line-cropmarks' will combine 'line' and 'cropmarks'; "
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
        choices=db.get_label_data()[3],
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
        help="Path to file that enumerates each card on its own line to be included or excluded."
        " To include a card, add its card name on a line.  The name can optionally be preceeded by '+'."
        " To exclude a card, add its card name on a line preseeded by a '-'"
        " If any card is included by this method, only cards specified in this file will be printed.",
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
    group_special.add_argument(
        "--log-level",
        default="WARNING",
        help="Set the logging level.",
        choices=["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
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
        logger.warning(
            "Tab side 'full' and tab name align 'edge' are incompatible. Aligning card name as 'left' for 'full' tabs"
        )
        options.tab_name_align = "left"

    if options.tab_number < 1:
        logger.warning("--tab-number must be 1 or greater.  Setting to 1.")
        options.tab_number = 1

    if options.tab_side == "full" and options.tab_number != 1:
        options.tab_number = 1  # Full is 1 big tab

    if "-alternate" in options.tab_side:
        if options.tab_number != 2:
            logger.warning(
                "--tab-side with 'alternate' implies 2 tabs. Setting --tab-number to 2."
            )
        options.tab_number = 2  # alternating left and right, so override tab_number

    if "-flip" in options.tab_side:
        # for left and right tabs
        if options.tab_number != 2:
            logger.warning(
                "--tab-side with 'flip' implies 2 tabs. Setting --tab-number to 2."
            )
        options.tab_number = (
            2  # alternating left and right with a flip, so override tab_number
        )
        options.flip = True
    else:
        options.flip = False

    if options.tab_number < 3 and options.tab_serpentine:
        logger.warning("--tab-serpentine only valid if --tab-number > 2.")
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

    # if notch is enabled with missing dimensions, provide defaults
    notch = options.notch or options.notch_length or options.notch_height
    if notch and not options.notch_length:
        options.notch_length = 1.5
    if notch and not options.notch_height:
        options.notch_height = 0.25

    if options.cropmarks and options.linetype == "line":
        options.linetype = "cropmarks"

    if "cropmarks" in options.linetype:
        options.cropmarks = True

    if options.expansions is None:
        # No instance given, so default to the latest Official expansions
        options.expansions = ["*"]
        if options.edition is None:
            options.edition = "latest"
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

    if options.edition is None:
        # set the default
        options.edition = "all"

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
        options.group_global = db.get_global_groups()[1]
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
    if options.exclude_traits:
        options.group_global.append("traits")
    # Remove duplicates from the list
    options.group_global = list(set(options.group_global))

    if options.tabs_only and options.label_name is None:
        # default is Avery 8867
        options.label_name = "8867"

    options.label = None
    if options.label_name is not None:
        for label in db.get_label_data()[0]:
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
        options.head = "tab"
        options.tail = "none"
        options.wrapper_meta = options.pull_tab_meta = options.tent_meta = False
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

    if options.wrapper_meta:
        # Same as --head=strap --tail=folder
        options.head = "strap"
        options.tail = "folder"
    if options.pull_tab_meta:
        # Same as --head=tab --tail=cover
        options.head = "tab"
        options.tail = "cover"
    if options.tent_meta:
        # Same as --head=cover --head-facing=back --head-text=back
        #         --tail=tab --tail-facing=front
        options.head = "cover"
        options.head_facing = "back"
        options.head_text = "back"
        options.tail = "tab"
        options.tail_facing = "front"
    # Flags set if there's a head wrapper, a tail wrapper, or either
    options.headWrapper = options.head in ["strap", "cover", "folder"]
    options.tailWrapper = options.tail in ["strap", "cover", "folder"]
    options.wrapper = options.headWrapper or options.tailWrapper

    # Expand --head-text and --tail-text if they refer to --front or --back
    if options.head_text == "front":
        options.head_text = options.text_front
    elif options.head_text == "back":
        options.head_text = options.text_back
    if options.tail_text == "front":
        options.tail_text = options.text_front
    elif options.tail_text == "back":
        options.tail_text = options.text_back

    return options


def parse_dimensions(dimensionsStr):
    x, y = dimensionsStr.upper().split("X", 1)
    return (float(x) * cm, float(y) * cm)


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
            paperwidth, paperheight = parse_dimensions(papersize)
            logger.info(
                (
                    f"Using custom paper size, {paperwidth / cm:.2f}cm x {paperheight / cm:.2f}cm"
                )
            )
        except ValueError:
            paperwidth, paperheight = pagesizes.LETTER
    return paperwidth, paperheight


def parse_cardsize(spec, sleeved):
    spec = spec.upper()
    if spec == "SLEEVED" or sleeved:
        dominionCardWidth, dominionCardHeight = (9.4 * cm, 6.15 * cm)
        logger.info(
            (
                f"Using sleeved card size, {dominionCardWidth / cm:.2f}cm x {dominionCardHeight / cm:.2f}cm"
            )
        )
    elif spec in ["NORMAL", "UNSLEEVED"]:
        dominionCardWidth, dominionCardHeight = (9.1 * cm, 5.9 * cm)
        logger.info(
            (
                f"Using normal card size, {dominionCardWidth / cm:.2f}cm x{dominionCardHeight / cm:.2f}cm"
            )
        )
    else:
        dominionCardWidth, dominionCardHeight = parse_dimensions(spec)
        logger.info(
            (
                f"Using custom card size, {dominionCardWidth / cm:.2f}cm x {dominionCardHeight / cm:.2f}cm"
            )
        )
    return dominionCardWidth, dominionCardHeight
