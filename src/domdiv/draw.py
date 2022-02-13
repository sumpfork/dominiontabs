import os
import re
import sys

import pkg_resources

from PIL import Image, ImageEnhance

from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, XPreformatted
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from .cards import Card


def split(seq, n):
    # Split a sequence into runs of n items each.
    i = 0
    while i < len(seq) - n:
        yield seq[i : i + n]
        i += n
    yield seq[i:]


def totalHeight(options, stackHeight):
    # Calculate divider total height given current options and stack height.
    return (
        options.dividerBaseHeight
        + options.headHeight
        + options.tailHeight
        + stackHeight * options.headWrapper
        + stackHeight * options.tailWrapper
    )


class CardPlot(object):
    # This object contains information needed to print a divider on a page.
    # It goes beyond information about the general card/divider to include page specific drawing information.
    # It also includes helpful methods used in manipulating the object and keeping up with tab locations.

    LEFT, CENTRE, RIGHT, TOP, BOTTOM = range(
        100, 105
    )  # location & directional constants

    tabNumber = 1  # Number of different tab locations
    tabIncrement = 0  # Either 1, 0, or -1.  Used to select next tab. This can change if tabSerpentine.
    tabIncrementStart = 0  # Starting value of tabIncrement
    tabStart = 1  # The starting tab location.
    tabStartSide = LEFT  # The starting side for the tabs
    tabSerpentine = False  # What to do at the end of a line of tabs.  False = start over.  True = reverses direction.
    lineType = "line"  # Type of outline to use: line, dot, none
    cardWidth = (
        0  # Width of just the divider, with no extra padding/spacing. NEEDS TO BE SET.
    )
    cardHeight = 0  # Height of just the divider, with no extra padding/spacing or tab. NEEDS TO BE SET.
    tabWidth = 0  # Width of the tab.  NEEDS TO BE SET.
    tabHeight = 0  # Height of the tab. NEEDS TO BE SET.
    wrapper = False  # If the divider is a sleeve/wrapper.

    @staticmethod
    def tabSetup(
        tabNumber=None,
        cardWidth=None,
        cardHeight=None,
        tabWidth=None,
        tabHeight=None,
        lineType=None,
        start=None,
        serpentine=None,
        wrapper=None,
    ):
        # Set up the basic tab information used in calculations when a new CardPlot object is created.
        # This needs to be called at least once before the first CardPlot object is created and then it
        # needs to be called any time one of the above parameters needs to change.
        CardPlot.tabNumber = tabNumber if tabNumber is not None else CardPlot.tabNumber
        CardPlot.cardWidth = cardWidth if cardWidth is not None else CardPlot.cardWidth
        CardPlot.cardHeight = (
            cardHeight if cardHeight is not None else CardPlot.cardHeight
        )
        CardPlot.tabWidth = tabWidth if tabWidth is not None else CardPlot.tabWidth
        CardPlot.tabHeight = tabHeight if tabHeight is not None else CardPlot.tabHeight
        CardPlot.lineType = lineType if lineType is not None else CardPlot.lineType
        CardPlot.tabStartSide = start if start is not None else CardPlot.tabStartSide
        CardPlot.tabSerpentine = (
            serpentine if serpentine is not None else CardPlot.tabSerpentine
        )
        CardPlot.wrapper = wrapper if wrapper is not None else CardPlot.wrapper
        # LEFT        tabs        RIGHT
        # +---+ +---+ +---+ +---+ +---+
        # | 1 | | 2 | | 3 | |...| | N |   Note: tabNumber = N, N >=1, 0 is for centred tabs
        # +   +-+   +-+   +-+   +-+   +

        # Setup first tab as well as starting point and direction of increment for tabs.
        if CardPlot.tabStartSide == CardPlot.RIGHT:
            CardPlot.tabStart = CardPlot.tabNumber
            CardPlot.tabIncrementStart = -1
        elif CardPlot.tabStartSide == CardPlot.CENTRE:
            # Get as close to centre as possible
            CardPlot.tabStart = (CardPlot.tabNumber + 1) // 2
            CardPlot.tabIncrementStart = 1
        else:
            # LEFT and anything else
            CardPlot.tabStartSide = CardPlot.LEFT
            CardPlot.tabStart = 1
            CardPlot.tabIncrementStart = 1

        if CardPlot.tabNumber == 1:
            CardPlot.tabIncrementStart = 0
        CardPlot.tabIncrement = CardPlot.tabIncrementStart

    @staticmethod
    def tabRestart():
        # Resets the tabIncrement to the starting value and returns the starting tabIndex number.
        CardPlot.tabIncrement = CardPlot.tabIncrementStart
        return CardPlot.tabStart

    def __init__(
        self,
        card,
        x=0,
        y=0,
        rotation=0,
        stackHeight=0,
        tabIndex=None,
        page=0,
        textTypeFront="card",
        textTypeBack="rules",
        cropOnTop=False,
        cropOnBottom=False,
        cropOnLeft=False,
        cropOnRight=False,
        options=None,
    ):
        self.card = card
        self.x = x  # x location of the lower left corner of the card on the page
        self.y = y  # y location of the lower left corner of the card on the page
        self.rotation = rotation  # of the card. 0, 90, 180, 270
        self.stackHeight = (
            stackHeight  # The height of a stack of these cards. Used for interleaving.
        )
        self.tabIndex = tabIndex  # Tab location index.  Starts at 1 and goes up to CardPlot.tabNumber
        self.page = page  # holds page number of this printed card
        self.textTypeFront = (
            textTypeFront  # What card text to put on the front of the divider
        )
        self.textTypeBack = (
            textTypeBack  # What card text to put on the back of the divider
        )
        self.cropOnTop = cropOnTop  # When true, cropmarks needed along TOP *printed* edge of the card
        self.cropOnBottom = cropOnBottom  # When true, cropmarks needed along BOTTOM *printed* edge of the card
        self.cropOnLeft = cropOnLeft  # When true, cropmarks needed along LEFT *printed* edge of the card
        self.cropOnRight = cropOnRight  # When true, cropmarks needed along RIGHT *printed* edge of the card
        self.options = options  # other script options

        # And figure out the backside index
        if self.tabIndex == 0:
            self.tabIndexBack = (
                0  # Exact Centre special case, so swapping is still exact centre
            )
        elif CardPlot.tabNumber == 1:
            self.tabIndex = (
                self.tabIndexBack
            ) = 1  # There is only one tab, so can only use 1 for both sides
        elif 1 <= self.tabIndex <= CardPlot.tabNumber:
            self.tabIndexBack = CardPlot.tabNumber + 1 - self.tabIndex
        else:
            # For anything else, just start at 1
            self.tabIndex = self.tabIndexBack = 1

        # Now set the offsets and the closest edge to the tab
        if self.tabIndex == 0:
            # Special case for centred tabs
            self.tabOffset = self.tabOffsetBack = (
                CardPlot.cardWidth - CardPlot.tabWidth
            ) / 2
            self.closestSide = CardPlot.CENTRE
        elif CardPlot.tabNumber <= 1:
            # If just one tab, then can be right, centre, or left
            self.closestSide = CardPlot.tabStartSide
            if CardPlot.tabStartSide == CardPlot.RIGHT:
                self.tabOffset = CardPlot.cardWidth - CardPlot.tabWidth
                self.tabOffsetBack = 0
            elif CardPlot.tabStartSide == CardPlot.CENTRE:
                self.tabOffset = (CardPlot.cardWidth - CardPlot.tabWidth) / 2
                self.tabOffsetBack = (CardPlot.cardWidth - CardPlot.tabWidth) / 2
            else:
                # LEFT and anything else
                self.tabOffset = 0
                self.tabOffsetBack = CardPlot.cardWidth - CardPlot.tabWidth
        else:
            # More than 1 tabs
            self.tabOffset = (self.tabIndex - 1) * (
                (CardPlot.cardWidth - CardPlot.tabWidth) / (CardPlot.tabNumber - 1)
            )
            self.tabOffsetBack = CardPlot.cardWidth - CardPlot.tabWidth - self.tabOffset

            # Set  which edge is closest to the tab
            if self.tabIndex <= CardPlot.tabNumber / 2:
                self.closestSide = CardPlot.LEFT
            else:
                self.closestSide = (
                    CardPlot.RIGHT
                    if self.tabIndex > (CardPlot.tabNumber + 1) / 2
                    else CardPlot.CENTRE
                )

    def setXY(self, x, y, rotation=None):
        # set the card to the given x,y and optional rotation
        self.x = x
        self.y = y
        if rotation is not None:
            self.rotation = rotation

    def rotate(self, delta):
        # rotate the card by amount delta
        self.rotation = (self.rotation + delta) % 360

    def getTabOffset(self, backside=False):
        # Get the tab offset (from the left edge) of the tab given
        if backside:
            return self.tabOffsetBack
        else:
            return self.tabOffset

    def nextTab(self, tab=None):
        # For a given tab, calculate the next tab in the sequence
        tab = tab if tab is not None else self.tabIndex
        if CardPlot.tabNumber == 1:
            return 1  # it is the same, nothing else to do

        # Increment if in range
        if 1 <= tab <= CardPlot.tabNumber:
            tab += CardPlot.tabIncrement

        # Now check for wrap around
        if tab > CardPlot.tabNumber:
            tab = 1
        elif tab < 1:
            tab = CardPlot.tabNumber

        if CardPlot.tabSerpentine and CardPlot.tabNumber > 2:
            if (tab == 1) or (tab == CardPlot.tabNumber):
                # reverse direction for next tab
                CardPlot.tabIncrement *= -1
        return tab

    def getClosestSide(self, backside=False):
        # Get the closest side for this tab.
        # Used when wanting text to be aligned towards the outer edge.
        side = self.closestSide
        if backside:
            # Need to flip
            if side == CardPlot.LEFT:
                side = CardPlot.RIGHT
            elif side == CardPlot.RIGHT:
                side = CardPlot.LEFT
        return side

    def flipFront2Back(self):
        # Flip a card from front to back.  i.e., print the front of the divider on the page's back
        # and print the back of the divider on the page's front.  So what does that mean...
        # If it is a wrapper / slipcover, then it is rotated 180 degrees.
        # Otherwise, the tab moves from right(left) to left(right).  If centre, it stays the same.
        # And then the divider's text is moved to the other side of the page.
        if self.wrapper:
            self.rotate(180)
        else:
            self.tabIndex, self.tabIndexBack = self.tabIndexBack, self.tabIndex
            self.tabOffset, self.tabOffsetBack = self.tabOffsetBack, self.tabOffset
            self.textTypeFront, self.textTypeBack = (
                self.textTypeBack,
                self.textTypeFront,
            )
            self.closestSide = self.getClosestSide(backside=True)

    def translate(self, canvas, page_width, backside=False):
        # Translate the page x,y of the lower left of item, taking into account the rotation,
        # and set up the canvas so that (0,0) is now at the lower lower left of the item
        # and the item can be drawn as if it is in the "standard" orientation.
        # So when done, the canvas is set and ready to draw the divider
        x = self.x
        y = self.y
        rotation = self.rotation

        # set width and height for this card
        width = self.cardWidth
        height = totalHeight(self.options, self.stackHeight)

        if backside:
            x = page_width - x - width

        if self.rotation == 180:
            x += width
            y += height
        elif self.rotation == 90:
            if backside:
                x += width
                rotation = 270
            else:
                y += width
        elif self.rotation == 270:
            if backside:
                x += width - height
                y += width
                rotation = 90
            else:
                x += height

        rotation = (
            360 - rotation % 360
        )  # ReportLab rotates counter clockwise, not clockwise.
        canvas.translate(x, y)
        canvas.rotate(rotation)

    def translateCropmarkEnable(self, side):
        # Returns True if a cropmark is needed on that side of the card
        # Takes into account the card's rotation, if the tab is flipped, if the card is next to an edge, etc.

        # First the rotation. The page does not change even if the card is rotated.
        # So need to translate page side to the actual drawn card edge
        if self.rotation == 0:
            sideTop = self.cropOnTop
            sideBottom = self.cropOnBottom
            sideRight = self.cropOnRight
            sideLeft = self.cropOnLeft
        elif self.rotation == 90:
            sideTop = self.cropOnRight
            sideBottom = self.cropOnLeft
            sideRight = self.cropOnBottom
            sideLeft = self.cropOnTop
        elif self.rotation == 180:
            sideTop = self.cropOnBottom
            sideBottom = self.cropOnTop
            sideRight = self.cropOnLeft
            sideLeft = self.cropOnRight
        elif self.rotation == 270:
            sideTop = self.cropOnLeft
            sideBottom = self.cropOnRight
            sideRight = self.cropOnTop
            sideLeft = self.cropOnBottom

        # Now can return the proper value based upon what side is requested
        if side == self.TOP:
            return sideTop
        elif side == self.BOTTOM:
            return sideBottom
        elif side == self.RIGHT:
            return sideRight
        elif side == self.LEFT:
            return sideLeft
        else:
            return False  # just in case


class Plotter(object):
    # Creates a simple plotting object that goes from point to point.
    # This makes outline drawing easier since calculations only need to be the delta from
    # one point to the next.  The default plotting in reportlab requires both
    # ends of the line in absolute sense.  Thus calculations can become increasingly more
    # complicated given various options.  Using this object simplifies the calculations significantly.

    def __init__(self, canvas, x=0, y=0, cropmarkLength=-1, cropmarkSpacing=-1):
        self.canvas = canvas
        self.x = x
        self.y = y
        (
            self.LEFT,
            self.RIGHT,
            self.TOP,
            self.BOTTOM,
            self.LINE,
            self.NO_LINE,
            self.DOT,
        ) = range(
            1, 8
        )  # Constants
        if cropmarkLength < 0:
            cropmarkLength = 0.2
        if cropmarkSpacing < 0:
            cropmarkSpacing = 0.1
        self.CropMarkLength = cropmarkLength * cm  # The length of a cropmark
        self.CropMarkSpacing = (
            cropmarkSpacing * cm
        )  # The spacing between the cut point and the start of the cropmark
        self.DotSize = 0.2  # Size of dot marks
        self.CropEnable = {
            self.LEFT: False,
            self.RIGHT: False,
            self.TOP: False,
            self.BOTTOM: False,
        }

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def getXY(self):
        return (self.x, self.y)

    def setCropEnable(self, mark, enable=False):
        if mark in self.CropEnable:
            self.CropEnable[mark] = enable

    def plot(self, delta_x=0, delta_y=0, pen=False, cropmarks=[]):
        # Move the pen, drawing along the way
        if pen is False:
            pen = self.NO_LINE
        x, y = self.getXY()  # get current point
        new_x = x + delta_x  # calculate new point from delta
        new_y = y + delta_y
        if pen == self.LINE:
            self.canvas.line(x, y, new_x, new_y)
        if pen == self.DOT:
            self.canvas.circle(new_x, new_y, self.DotSize)
        self.setXY(new_x, new_y)  # save the new point

        # Make sure cropmarks is a list
        cropmarks = cropmarks if isinstance(cropmarks, list) else [cropmarks]
        # Now add any cropmarks
        for mark in cropmarks:
            # setCropEnable must be called for each direction ahead of time (once per divider).
            # Cropmarks are only drawn for directions that are enabled (as set above).
            # Each crop mark given is either:
            #   1. A tuple of direction and a boolean of additional enablement criteria
            #   2. A direction to draw a drop mark
            if isinstance(mark, tuple):
                direction, enable = mark
                enable = (
                    enable and self.CropEnable[direction]
                    if direction in self.CropEnable
                    else False
                )
            else:
                direction = mark
                enable = (
                    self.CropEnable[direction]
                    if direction in self.CropEnable
                    else False
                )
            if direction in self.CropEnable:
                self.cropmark(direction, enable)

    def cropmark(self, direction, enabled=False):
        # From current point, draw a cropmark in the correct direction and return to starting point
        if enabled:
            x, y = self.getXY()  # Saving for later

            if direction == self.TOP:
                self.plot(0, self.CropMarkSpacing)
                self.plot(0, self.CropMarkLength, self.LINE)
            if direction == self.BOTTOM:
                self.plot(0, -self.CropMarkSpacing)
                self.plot(0, -self.CropMarkLength, self.LINE)
            if direction == self.RIGHT:
                self.plot(self.CropMarkSpacing, 0)
                self.plot(self.CropMarkLength, 0, self.LINE)
            if direction == self.LEFT:
                self.plot(-self.CropMarkSpacing, 0)
                self.plot(-self.CropMarkLength, 0, self.LINE)
            self.setXY(x, y)  # Restore to starting point


class DividerDrawer(object):
    def __init__(self, options=None):
        self.canvas = None
        self.pages = None
        self.options = options

    @staticmethod
    def get_image_filepath(fname):
        return pkg_resources.resource_filename("domdiv", os.path.join("images", fname))

    def draw(self, cards=[], options=None):
        if options is not None:
            self.options = options

        self.registerFonts()
        self.canvas = canvas.Canvas(
            self.options.outfile,
            pagesize=(self.options.paperwidth, self.options.paperheight),
        )
        self.drawDividers(cards)
        if self.options.info or self.options.info_all:
            self.drawInfo()
        self.canvas.save()

    def registerFonts(self):
        # Fonts used in Dominion:
        # TrajanPro-Bold        card titles and types
        # MinionStd-Black       numbers on base cards & icons
        # Times-Roman           rules text*
        # Times-Bold            bold rules text
        # Times-Italic          italic rules text
        # Helvetica-Bold        superscript + in some card costs
        # CharlemagneStd-Bold   expansion names on box art
        # Capitals              player mat banners
        # Barbedor-Bold         player mat rules

        # * the cards mostly use Times New Roman rather than Times Roman, but they're
        #   not totally consistent, and the differences are very subtle

        # Common filenames used by Adobe Reader and Creative Cloud, as well as
        # alternatives available from free sites like fontsgeek:
        fontfilenames = {
            "TrajanPro-Bold": [
                "TrajanPro-Bold.ttf",
                "TrajanPro3-Semibold.ttf",
                "Trajan Pro Bold.ttf",
            ],
            "MinionStd-Black": [
                "MinionStd-Black.ttf",
                "Minion Std Black.ttf",
            ],
            "CharlemagneStd-Bold": [
                "CharlemagneStd-Bold.ttf",
                "Charlemagne Std Bold.ttf",
            ],
            "MinionPro-Regular": [
                "MinionPro-Regular.ttf",
                "Minion Pro Regular.ttf",
            ],
            "MinionPro-Bold": [
                "MinionPro-Bold.ttf",
                "Minion Pro Bold.ttf",
            ],
            "MinionPro-Italic": [
                "MinionPro-Italic.ttf",
                "MinionPro-It.ttf",
                "Minion Pro Italic.ttf",
            ],
            # Built-in fonts
            "Times-Roman": None,
            "Times-Bold": None,
            "Times-Italic": None,
            "Helvetica-Bold": None,
            "Courier": None,
        }
        # Locate the files in package data, if present
        fontpaths = {}
        for font, filenames in fontfilenames.items():
            if filenames is None:  # built-ins
                fontpaths[font] = None
                continue
            for fname in filenames:
                fpath = os.path.join("fonts", fname)
                if pkg_resources.resource_exists("domdiv", fpath):
                    fontpaths[font] = fpath
                    break
        # Mark the built-in files as pre-registered
        registered = {
            font: None for font, fontpath in fontpaths.items() if fontpath is None
        }
        # Determine the best matching fonts for each font type.
        fontprefs = {
            "Name": [  # card names & types
                "TrajanPro-Bold",
                "MinionPro-Regular",
                "Times-Roman",
            ],
            "Expansion": [  # expansion names
                "CharlemagneStd-Bold",
                "TrajanPro-Bold",
                "MinionPro-Regular",
                "Times-Roman",
            ],
            "Cost": [  # card costs (coins, debt, etc)
                "MinionStd-Black",
                "MinionPro-Bold",
                "Times-Bold",
            ],
            "PlusCost": [  # card cost superscript "+" modifiers
                "Helvetica-Bold",
            ],
            "Regular": [  # regular text
                "MinionPro-Regular",
                "Times-Roman",
            ],
            "Bold": [  # miscellaneous bold text
                "MinionPro-Bold",
                "Times-Bold",
            ],
            "Italic": [  # for --use-set-text-icon
                "MinionPro-Italic",
                "Times-Italic",
            ],
            "Rules": [
                "Times-Roman",
            ],
            "Monospaced": [
                "Courier",
            ],
        }
        self.fontStyle = {
            # select the first matching preference for each font type
            style: [font for font in prefs if font in fontpaths][0]
            for style, prefs in fontprefs.items()
        }
        for style, font in self.fontStyle.items():
            best = fontprefs[style][0]
            if font != best:
                print(
                    "Warning, {} missing from domdiv/fonts; "
                    "using {} instead.".format(best, font),
                    file=sys.stderr,
                )
            if font in registered:
                continue
            fontpath = fontpaths[font]
            # print("Registering {} = {}".format(font, fontpath))
            pdfmetrics.registerFont(
                TTFont(
                    font,
                    pkg_resources.resource_filename("domdiv", fontpath),
                )
            )
            registered[font] = fontpath

    def drawTextPages(self, pages, margin=1.0, fontsize=10, leading=10, spacer=0.05):
        s = getSampleStyleSheet()["BodyText"]
        s.fontName = self.fontStyle["Monospaced"]
        s.alignment = TA_LEFT

        textHorizontalMargin = margin * cm
        textVerticalMargin = margin * cm
        textBoxWidth = self.options.paperwidth - 2 * textHorizontalMargin
        textBoxHeight = self.options.paperheight - 2 * textVerticalMargin
        minSpacerHeight = 0.05 * cm

        for page in pages:
            s.fontsize = fontsize
            s.leading = leading
            spacerHeight = spacer * cm
            text = re.split("\n", page)
            while True:
                paragraphs = []
                # this accounts for the spacers we insert between paragraphs
                h = (len(text) - 1) * spacerHeight
                for line in text:
                    p = XPreformatted(line, s)
                    h += p.wrap(textBoxWidth, textBoxHeight)[1]
                    paragraphs.append(p)

                if h <= textBoxHeight or s.fontSize <= 1 or s.leading <= 1:
                    break
                else:
                    s.fontSize -= 0.2
                    s.leading -= 0.2
                    spacerHeight = max(spacerHeight - 1, minSpacerHeight)

            h = self.options.paperheight - textVerticalMargin
            for p in paragraphs:
                h -= p.height
                p.drawOn(self.canvas, textHorizontalMargin, h)
                h -= spacerHeight
            self.canvas.showPage()

    def drawInfo(self, printIt=True):
        # Keep track of the number of pages
        pageCount = 0
        # A unique separator that will not be found in any normal text.  Was '@@@***!!!***@@@' at one time.
        sep = chr(30) + chr(31)
        # Generic space.  Other options are ' ', '&nbsp;', '&#xa0;'
        space = "&nbsp;"
        tab_spaces = 4
        blank_line = (space + "\n") * 2

        if self.options.info or self.options.info_all:
            text = "<para alignment='center'><font size=18><b>"
            text += "Sumpfork's Dominion Tabbed Divider Generator"
            text += "</b></font></para>\n"
            text += blank_line
            text += "Online generator at: "
            text += "<a href='http://domtabs.sandflea.org/' color='blue'>http://domtabs.sandflea.org</a>\n\n"
            text += "Source code on GitHub at: "
            text += "<a href='https://github.com/sumpfork/dominiontabs' color='blue'>"
            text += "https://github.com/sumpfork/dominiontabs</a>\n\n"
            text += "Options for this file:\n"

            cmd = " ".join(self.options.argv)
            cmd = cmd.replace(" --", sep + "--")
            cmd = cmd.replace(" -", sep + "-")
            cmd = cmd.replace(sep, "\n" + space * tab_spaces)

            text += cmd
            text += blank_line

            if printIt:
                self.drawTextPages(
                    [text], margin=1.0, fontsize=10, leading=10, spacer=0.05
                )
            pageCount += 1

        if self.options.info_all:
            linesPerPage = 80
            lines = (
                self.options.help.replace("\n\n", blank_line)
                .replace(" ", space)
                .split("\n")
            )
            pages = []
            lineCount = 0
            text = ""
            for line in lines:
                lineCount += 1
                text += line + "\n"
                if lineCount >= linesPerPage:
                    pages.append(text)
                    pageCount += 1
                    lineCount = 0
                    text = ""
            if text:
                pages.append(text)
                pageCount += 1
            if printIt:
                self.drawTextPages(
                    pages, margin=0.75, fontsize=6, leading=7, spacer=0.1
                )

        return pageCount

    def wantCentreTab(self, card):
        return (
            card.isExpansion()
            and (
                self.options.centre_expansion_dividers
                or self.options.full_expansion_dividers
            )
        ) or self.options.tab_side == "centre"

    def drawOutline(self, item, isBack=False):
        # draw outline or cropmarks
        if isBack and not self.options.cropmarks:
            return
        if self.options.linewidth <= 0.0:
            return
        self.canvas.saveState()
        self.canvas.setLineWidth(self.options.linewidth)

        # The back is flipped
        if isBack:
            self.canvas.translate(item.cardWidth, 0)
            self.canvas.scale(-1, 1)

        plotter = Plotter(
            self.canvas,
            cropmarkLength=self.options.cropmarkLength,
            cropmarkSpacing=self.options.cropmarkSpacing,
        )

        dividerWidth = item.cardWidth
        dividerBaseHeight = item.cardHeight
        tabLabelWidth = item.tabWidth
        theTabWidth = item.tabWidth
        theTabHeight = self.options.headHeight

        left2tab = item.getTabOffset(
            backside=False
        )  # translate/scale above takes care of backside
        right2tab = dividerWidth - tabLabelWidth - left2tab
        nearZero = 0.01
        left2tab = left2tab if left2tab > nearZero else 0
        right2tab = right2tab if right2tab > nearZero else 0

        if item.lineType.lower() == "line":
            lineType = plotter.LINE
            lineTypeNoDot = plotter.LINE
        elif item.lineType.lower() == "dot":
            lineType = plotter.DOT
            lineTypeNoDot = plotter.NO_LINE
        else:
            lineType = plotter.NO_LINE
            lineTypeNoDot = plotter.NO_LINE

        # Setup bare minimum lineStyle's
        lineStyle = [lineType for i in range(0, 10)]
        lineStyle[0] = lineTypeNoDot
        lineStyle[7] = lineType
        lineStyle[8] = lineType if left2tab > 0 else lineTypeNoDot
        lineStyle[9] = lineType if right2tab > 0 else lineTypeNoDot

        RIGHT = plotter.RIGHT
        LEFT = plotter.LEFT
        BOTTOM = plotter.BOTTOM
        TOP = plotter.TOP
        NO_LINE = plotter.NO_LINE

        plotter.setCropEnable(
            RIGHT, self.options.cropmarks and item.translateCropmarkEnable(item.RIGHT)
        )
        plotter.setCropEnable(
            LEFT, self.options.cropmarks and item.translateCropmarkEnable(item.LEFT)
        )
        plotter.setCropEnable(
            TOP, self.options.cropmarks and item.translateCropmarkEnable(item.TOP)
        )
        plotter.setCropEnable(
            BOTTOM, self.options.cropmarks and item.translateCropmarkEnable(item.BOTTOM)
        )

        if not item.wrapper:
            # Normal Card Outline
            #     <-left2tab-> <--tabLabelWidth--> <-right2tab->
            #    |            |                   |             |
            #  Z-+           F7-------------------7E            +-Y
            #                 |                   |
            #  H-8------------8                   9-------------9-C
            #    |            G                   D             |
            #    |               Generic Divider                |
            #    |            Tab Centered or to the Side       |
            #    |                                              |
            #  A-7------------0-------------------0-------------7-B
            #    |           V|                  W|             |
            #
            plotter.plot(0, 0, NO_LINE, [LEFT, BOTTOM])  # ? to A
            plotter.plot(left2tab, 0, lineStyle[0], BOTTOM)  # A to V
            plotter.plot(theTabWidth, 0, lineStyle[0], BOTTOM)  # V to W
            plotter.plot(right2tab, 0, lineStyle[7], [BOTTOM, RIGHT])  # W to B
            plotter.plot(0, dividerBaseHeight, lineStyle[9], RIGHT)  # B to C
            plotter.plot(-right2tab, 0, lineStyle[9])  # C to D
            plotter.plot(0, theTabHeight, lineStyle[7], TOP)  # D to E
            plotter.plot(right2tab, 0, NO_LINE, [TOP, RIGHT])  # E to Y
            plotter.plot(-right2tab, 0, NO_LINE)  # Y to E
            plotter.plot(-theTabWidth, 0, lineStyle[7], TOP)  # E to F
            plotter.plot(0, -theTabHeight, lineStyle[8])  # F to G
            plotter.plot(-left2tab, 0, lineStyle[8], LEFT)  # G to H
            plotter.plot(0, theTabHeight, NO_LINE, [TOP, LEFT])  # H to Z
            plotter.plot(0, -theTabHeight, NO_LINE)  # Z to H
            plotter.plot(0, -dividerBaseHeight, lineStyle[7])  # H to A

        else:
            # Card Wrapper Outline

            # Set up values used in the outline
            minNotch = 0.1 * cm  # Don't really want notches that are smaller than this.
            if self.options.notch_length * cm > minNotch:
                # A notch length was given, so notches are wanted
                notch_height = self.options.notch_height * cm  # thumb notch height
                notch1 = notch2 = notch3 = notch4 = (
                    self.options.notch_length * cm
                )  # thumb notch width
                notch1used = notch2used = notch3used = notch4used = True  # For now
            else:
                # No notches are wanted
                notch_height = 0
                notch1 = notch2 = notch3 = notch4 = 0
                notch1used = notch2used = notch3used = notch4used = False

            # Even if wanted, there may not be room, and limit to one pair of notches
            if (right2tab - minNotch < notch1) or not notch1used:
                notch1 = notch3 = 0
                notch1used = notch3used = False
            if (left2tab - minNotch < notch4) or not notch4used or notch1used:
                notch4 = notch2 = 0
                notch4used = notch2used = False
            if not self.options.headWrapper:  # no top fold
                notch1 = notch4 = 0
                notch1used = notch4used = False
            if not self.options.tailWrapper:  # no bottom fold
                notch2 = notch3 = 0
                notch2used = notch3used = False

            # Setup the rest of the lineStyle's
            lineStyle[1] = lineType if notch1used else lineTypeNoDot
            lineStyle[2] = lineType if notch2used else lineTypeNoDot
            lineStyle[3] = lineType if notch3used else lineTypeNoDot
            lineStyle[4] = lineType if notch4used else lineTypeNoDot
            lineStyle[5] = lineType if notch1used and right2tab > 0 else lineTypeNoDot
            lineStyle[6] = lineType if notch4used and left2tab > 0 else lineTypeNoDot

            # TODO: this needs generalizing to match the new head/tail system
            headStackHeight = item.stackHeight * self.options.headWrapper
            tailStackHeight = item.stackHeight * self.options.tailWrapper
            frontTabHeight = self.options.headHeight
            backTabHeight = item.tabHeight if self.options.tail == "folder" else 0
            backWrapHeight = self.options.tailHeight - backTabHeight
            frontWrapHeight = dividerBaseHeight

            front_minus_notches = frontWrapHeight - (2.0 * notch_height)
            tab2notch1 = right2tab - notch1
            tab2notch4 = left2tab - notch4
            backBottomNotch = min(notch_height, backWrapHeight)
            backTopNotch = (
                max(notch_height + backWrapHeight - frontWrapHeight, 0)
                if self.options.tailWrapper
                else 0
            )
            back_minus_notches = max(backWrapHeight - backBottomNotch - backTopNotch, 0)

            # Some corners collapse if the back tab height or notch height is 0
            # external corners:
            x5 = 5 if backTopNotch else 7
            x6 = 6 if backTopNotch else 7
            x7 = 7 if backTabHeight else 0
            x8 = 8 if backTabHeight else 7 if backTopNotch else 0
            x9 = 9 if backTabHeight else 7 if backTopNotch else 0
            # internal corners:
            i1 = 1 if backTopNotch else 0
            i4 = 4 if backTopNotch else 0
            i8 = 8 if backTabHeight else 0
            i9 = 9 if backTabHeight else 0

            #     <-----left2tab----------> <--tabLabelWidth--> <-----right2tab-------->
            #    |         |               |                   |               |        |
            # Zb-+       Va+              V7-------------------7U              +Ua      +-Ub
            #               <--tab2notch4->|                   |<--tab2notch1->
            #    +                        W0...................0T
            #              Y               |                   |               R
            # Za-+         8---------------8...................9---------------9        +-Pa
            #     <notch4 >|               X                   S               |<notch1>
            #  Z-6---------4Ya                                                Q1--------5-P
            #    |                                                                      |
            #    |                         Generic Wrapper                              |
            #    |                           Normal Side                                |
            #    |                                                                      |
            # AA-2--------2BB                                                 N3--------3-O
            #     <notch2>|                                                    |<notch3>
            #    +        0CC.................................................M0        +-Oa
            #             |                                                    |
            #    +        0DD.................................................L0        +
            #     <notch2>|                                                    |<notch3>
            # FF-2--------2EE                                                 K3--------3-J
            #    |                                                                      |
            #    |                            Reverse Side                              |
            #    |                            rotated 180                               |
            #    |         Ca                                                  H        |
            # GG-6---------4<--tab2notch4->                     <--tab2notch1->1--------5-I
            #     <notch4 >|               C                   F               |<notch1>
            #  B-+       Cb8---------------8                   9---------------9G       +-Ia
            #                              |                   |
            #   -+A      Cc+              D7-------------------7E              +Ga      +-Ib
            #    |         |               |                   |               |        |
            #     <-----left2tab----------> <--tabLabelWidth--> <-----right2tab-------->

            plotter.plot(0, 0, NO_LINE, [BOTTOM, LEFT])  # ?  to A
            plotter.plot(0, backTabHeight, NO_LINE, LEFT)  # A  to B
            plotter.plot(
                0, backTopNotch, NO_LINE, (LEFT, notch4used or notch1used)
            )  # B  to GG
            plotter.plot(notch4, 0, lineStyle[i4])  # GG to Ca
            plotter.plot(0, -backTopNotch, lineStyle[x8])  # Ca to Cb
            plotter.plot(
                0, -backTabHeight, NO_LINE, (BOTTOM, notch4used or notch2used)
            )  # Cb to Cc
            plotter.plot(0, backTabHeight, NO_LINE)  # Cc to Cb
            plotter.plot(tab2notch4, 0, lineStyle[i8])  # Cb to C
            plotter.plot(0, -backTabHeight, lineStyle[x7], BOTTOM)  # C  to D
            plotter.plot(tabLabelWidth, 0, lineStyle[x7], BOTTOM)  # D  to E
            plotter.plot(0, backTabHeight, lineStyle[i9])  # E  to F
            plotter.plot(tab2notch1, 0, lineStyle[x9])  # F  to G
            plotter.plot(
                0, -backTabHeight, NO_LINE, (BOTTOM, notch1used or notch3used)
            )  # G  to Ga
            plotter.plot(0, backTabHeight, NO_LINE)  # Ga to G
            plotter.plot(0, backTopNotch, lineStyle[i1])  # G  to H
            plotter.plot(
                notch1, 0, lineStyle[x5], (RIGHT, notch1used or notch4used)
            )  # H  to I
            plotter.plot(0, -backTopNotch, NO_LINE, RIGHT)  # I  to Ia
            plotter.plot(0, -backTabHeight, NO_LINE, [RIGHT, BOTTOM])  # Ia to Ib
            plotter.plot(0, backTabHeight, NO_LINE)  # Ib to Ia
            plotter.plot(0, backTopNotch, NO_LINE)  # Ia to I
            plotter.plot(
                0, back_minus_notches, lineStyle[3], (RIGHT, notch2used or notch3used)
            )  # I  to J
            plotter.plot(-notch3, 0, lineStyle[3])  # J  to K
            plotter.plot(0, backBottomNotch, lineStyle[0])  # K  to L
            plotter.plot(0, tailStackHeight, lineStyle[0])  # L  to M
            plotter.plot(0, notch_height, lineStyle[3])  # M  to N
            plotter.plot(
                notch3, 0, lineStyle[3], (RIGHT, notch2used or notch3used)
            )  # N  to O
            plotter.plot(
                0, front_minus_notches, lineStyle[5], (RIGHT, notch1used or notch4used)
            )  # O  to P
            plotter.plot(0, notch_height, NO_LINE, RIGHT)  # P  to Pa
            plotter.plot(0, -notch_height, NO_LINE)  # Pa to P
            plotter.plot(-notch1, 0, lineStyle[1])  # P  to Q
            plotter.plot(0, notch_height, lineStyle[9])  # Q  to R
            plotter.plot(-tab2notch1, 0, lineStyle[9])  # R  to S
            plotter.plot(0, headStackHeight, lineStyle[0])  # S  to T
            plotter.plot(0, frontTabHeight, lineStyle[7], TOP)  # S  to U
            plotter.plot(
                tab2notch1, 0, NO_LINE, (TOP, notch1used or notch3used)
            )  # U  to Ua
            plotter.plot(notch1, 0, NO_LINE, [TOP, RIGHT])  # Ua to Ub
            plotter.plot(-notch1, 0, NO_LINE)  # Ub to Ua
            plotter.plot(-tab2notch1, 0, NO_LINE)  # Ua to U
            plotter.plot(-theTabWidth, 0, lineStyle[7], TOP)  # U  to V
            plotter.plot(
                -tab2notch4, 0, NO_LINE, (TOP, notch4used or notch2used)
            )  # V  to Va
            plotter.plot(tab2notch4, 0, NO_LINE)  # Va to V
            plotter.plot(0, -frontTabHeight, lineStyle[0])  # V  to W
            plotter.plot(0, -headStackHeight, lineStyle[8])  # W  to X
            plotter.plot(-tab2notch4, 0, lineStyle[8])  # X  to Y
            plotter.plot(0, -notch_height, lineStyle[4])  # Y  to Ya
            plotter.plot(
                -notch4, 0, lineStyle[6], (LEFT, notch1used or notch4used)
            )  # Ya to Z
            plotter.plot(0, notch_height, NO_LINE, LEFT)  # Z  to Za
            plotter.plot(
                0, frontTabHeight + headStackHeight, NO_LINE, [TOP, LEFT]
            )  # Za to Zb
            plotter.plot(0, -frontTabHeight - headStackHeight, NO_LINE)  # Zb to Za
            plotter.plot(0, -notch_height, NO_LINE)  # Za to Z
            plotter.plot(
                0, -front_minus_notches, lineStyle[2], (LEFT, notch2used or notch3used)
            )  # Z  to AA
            plotter.plot(notch2, 0, lineStyle[2])  # AA to BB
            plotter.plot(0, -notch_height, lineStyle[0])  # BB to CC
            plotter.plot(0, -tailStackHeight, lineStyle[0])  # CC to DD
            plotter.plot(0, -backBottomNotch, lineStyle[2])  # DD to EE
            plotter.plot(
                -notch2, 0, lineStyle[2], (LEFT, notch2used or notch3used)
            )  # EE to FF
            plotter.plot(0, -back_minus_notches, lineStyle[x6])  # FF to GG

            # Add fold lines
            self.canvas.setStrokeGray(0.9)
            # top fold
            plotter.setXY(
                left2tab,
                backTabHeight + backWrapHeight + tailStackHeight + frontWrapHeight,
            )  # ?  to X
            plotter.plot(theTabWidth, 0, plotter.LINE)  # X  to S
            plotter.plot(0, headStackHeight)  # S  to T
            plotter.plot(-theTabWidth, 0, plotter.LINE)  # V  to S
            # bottom fold
            if backWrapHeight:
                plotter.setXY(notch2, backTabHeight + backWrapHeight)  # ?  to DD
                plotter.plot(dividerWidth - notch2 - notch3, 0, plotter.LINE)  # DD to L
                plotter.plot(0, tailStackHeight)  # L  to M
                plotter.plot(
                    -dividerWidth + notch2 + notch3, 0, plotter.LINE
                )  # M  to CC

        self.canvas.restoreState()

    def add_inline_images(self, text, fontsize):
        def replace_image_tag(
            text,
            fontsize,
            tag_pattern,
            fname_replace,
            fontsize_multiplier,
            height_percent,
            text_fontsize_multiplier=None,
        ):
            replace_template = '<img src="{fpath}" width={width} height="{height_percent}%" valign="middle" />'
            offset = 0
            for match in re.finditer(tag_pattern, text):
                replace = replace_template
                tag = match.group(0)
                fname = re.sub(tag_pattern, fname_replace, tag)
                if text_fontsize_multiplier is not None:
                    font_replace = re.sub(
                        tag_pattern,
                        "<font size={}>\\1</font>".format(
                            fontsize * text_fontsize_multiplier
                        ),
                        tag,
                    )
                    replace = font_replace + replace
                replace = replace.format(
                    fpath=DividerDrawer.get_image_filepath(fname),
                    width=fontsize * fontsize_multiplier,
                    height_percent=height_percent,
                )
                text = (
                    text[: match.start() + offset]
                    + replace
                    + text[match.end() + offset :]
                )
                offset += len(replace) - len(match.group(0))
            return text

        # Coins
        replace_specs = [
            # Coins
            # TODO: coin text baseline should align with surrounding text
            (r"(\d+)\s\<\*COIN\*\>", "coin_small_\\1.png", 2.4, 200),
            (r"(\d+)\s(c|C)oin(s)?", "coin_small_\\1.png", 1.2, 100),
            (r"\?\s(c|C)oin(s)?", "coin_small_question.png", 1.2, 100),
            (r"(empty|\_)\s(c|C)oin(s)?", "coin_small_empty.png", 1.2, 100),
            # VP
            (r"(?:\s+|\<)VP(?:\s+|\>|\.|$)", "victory_emblem.png", 1.25, 100),
            (r"(\d+)\s*\<\*VP\*\>", "victory_emblem.png", 2, 160, 1.3),
            # Debt
            (r"(\d+)\sDebt", "debt_\\1.png", 1.2, 105),
            (r"Debt", "debt.png", 1.2, 105),
            # Potion
            (r"(\d+)\s*\<\*POTION\*\>", "potion_small.png", 2, 140, 1.5),
            (r"Potion", "potion_small.png", 1.2, 100),
        ]
        for args in replace_specs:
            text = replace_image_tag(text, fontsize, *args)

        return text.strip()

    def add_inline_text(self, card, text, emWidth):
        # Bonuses
        text = card.getBonusBoldText(text)

        # <line>: 11 em dashes, but not wider than the text box
        replace = "<center>{}</center>\n".format("&mdash;" * min(11, int(emWidth)))
        text = re.sub(r"\<line\>", replace, text)
        #  <tab> and \t
        text = re.sub(r"\<tab\>", "\t", text)
        text = re.sub(r"\<t\>", "\t", text)
        text = re.sub(r"\t", "&nbsp;" * 4, text)

        # various breaks
        text = re.sub(r"\<br\>", "<br />", text)
        text = re.sub(r"\<n\>", "\n", text)

        # alignments
        text = re.sub(r"\<c\>", "<center>", text)
        text = re.sub(r"\<center\>", "\n<para alignment='center'>", text)
        text = re.sub(r"\</c\>", "</center>", text)
        text = re.sub(r"\</center\>", "</para>", text)

        text = re.sub(r"\<l\>", "<left>", text)
        text = re.sub(r"\<left\>", "\n<para alignment='left'>", text)
        text = re.sub(r"\</l\>", "</left>", text)
        text = re.sub(r"\</left\>", "</para>", text)

        text = re.sub(r"\<r\>", "<right>", text)
        text = re.sub(r"\<right\>", "\n<para alignment='right'>", text)
        text = re.sub(r"\</r\>", "</right>", text)
        text = re.sub(r"\</right\>", "</para>", text)

        text = re.sub(r"\<j\>", "<justify>", text)
        text = re.sub(r"\<justify\>", "\n<para alignment='justify'>", text)
        text = re.sub(r"\</j\>", "</justify>", text)
        text = re.sub(r"\</justify\>", "</para>", text)

        return text.strip().strip("\n")

    def drawCardCount(self, card, x, y, offset=-1):
        # Note that this is right justified.
        # x represents the right most for the image (image grows to the left)
        if card.getCardCount() < 1:
            return 0

        #  draw_list = [(card.getCardCount(), 1)]
        draw_list = sorted([(i, card.count.count(i)) for i in set(card.count)])

        cardIconHeight = y + offset
        countHeight = cardIconHeight - 4
        width = 0

        for value, count in draw_list:
            # draw the image set with the number of cards inside it
            width += 16
            x -= 16
            self.canvas.drawImage(
                DividerDrawer.get_image_filepath("card.png"),
                x,
                countHeight,
                16,
                16,
                preserveAspectRatio=True,
                mask="auto",
            )
            self.canvas.setFont(self.fontStyle["Bold"], 10)
            self.canvas.drawCentredString(x + 8, countHeight + 4, str(value))

            # now draw the number of sets
            if count > 1:
                count_string = "{}\u00d7".format(count)
                width_string = stringWidth(count_string, self.fontStyle["Regular"], 10)
                width_string -= 1  # adjust to make it closer to image
                width += width_string
                x -= width_string
                self.canvas.setFont(self.fontStyle["Regular"], 10)
                self.canvas.drawString(x, countHeight + 4, count_string)

        return width + 1

    def drawCost(self, card, x, y, costOffset=-1, scale=1):
        # card = subject card
        # x = left side of coin
        # y = baseline height for text
        # (costOffset is no longer used)

        # Measured card metrics:
        # coins are 17 pt with a 1 pt drop shadow
        # cost numbers are Minion Std Black 18 (11.7 pt ascent)
        # with a baseline 3 pt above the bottom of the coin
        fontSize = 18 * scale
        coinSize = 17 * scale
        potSize = 15 * scale
        baseline = 3 * scale  # distance from coin bottom to baseline

        # set relative positions of coin and coin text
        costHeight = y  # text baseline height
        coinHeight = costHeight - baseline  # bottom of coin graphic
        potHeight = coinHeight + (coinSize - potSize) / 2  # bottom of potion graphic

        def drawCostText(text, x, y, color=None):
            # x, y = center of baseline
            cost = str(text)
            font = self.fontStyle["Cost"]

            # handle superscript cost modifiers
            mod = ""
            modSize = modSpacing = modWidth = modHeight = 0
            if cost[-1] in "*+":
                mod = cost[-1]
                cost = cost[:-1]
                modFont = font
                modSpacing = -0.5 * scale
                if mod == "*":
                    # asterisks are set in Minion Std Black 12 and raised 3.75 pt
                    modSize = 12 * scale
                    modHeight = 3.75 * scale
                    modSpacing -= 0.25 * scale  # all asterisks are a little tighter
                elif mod == "+":
                    # plusses are set in Arial/Helvetica Bold 9 and raised 9 pt
                    modFont = self.fontStyle["PlusCost"]
                    modSize = 9 * scale
                    modHeight = 6 * scale
                    if cost.endswith("4"):  # "4+" is kerned tighter
                        modSpacing += -0.5 * scale
                if not cost:  # lonely star or plus
                    modSpacing = 0
                modWidth = pdfmetrics.stringWidth(mod, modFont, modSize)

            # get text width metrics
            costWidth = [
                pdfmetrics.stringWidth(digit, font, fontSize) for digit in cost
            ]
            spacing = -2.0  # compress multi-digit costs
            totalWidth = (
                sum(costWidth)
                + spacing * max(0, len(costWidth) - 1)
                + modSpacing
                + modWidth
            )

            # write the text
            self.canvas.saveState()
            if color is not None:
                self.canvas.setFillColorRGB(*color)
            self.canvas.setFont(font, fontSize)
            left = x - totalWidth / 2
            right = x + totalWidth / 2
            for i, digit in enumerate(cost):
                prefix = sum(costWidth[:i]) + i * spacing
                self.canvas.drawString(left + prefix, y, digit)
            if mod:
                self.canvas.setFont(modFont, modSize)
                self.canvas.drawString(right - modWidth, y + modHeight, mod)
            self.canvas.restoreState()

        def scaleImage(name, x, y, h, mask):
            path = DividerDrawer.get_image_filepath(name)
            with Image.open(path) as img:
                w0, h0 = img.size
            scale = h / h0
            w = w0 * scale
            self.canvas.drawImage(path, x, y, w, h, mask)
            return w

        width = 0

        cost = card.cost
        debt = card.debtcost
        pots = card.potcost

        if cost and (cost[0] != "0" or not debt and not pots):
            shadowXY = [0.5, 1]  # leave room for a drop shadow (TODO: draw the shadow)
            dx = scaleImage(
                "coin_small.png", x + width, coinHeight, coinSize, mask="auto"
            )
            drawCostText(cost, x + width + dx / 2, costHeight)
            width += dx + shadowXY[0]

        if debt:
            shadowXY = [0.5, 1]  # leave room for a drop shadow (TODO: draw the shadow)
            mask = [170, 255, 170, 255, 170, 255]
            dx = scaleImage("debt.png", x + width, coinHeight, coinSize, mask=mask)
            drawCostText(debt, x + width + dx / 2, costHeight, color=(1, 1, 1))
            width += dx + shadowXY[0]

        if pots:
            if width:  # add a little extra room before the potion
                width += 1
            dx = scaleImage("potion.png", x + width, potHeight, potSize, mask="auto")
            width += dx

        return width

    def drawSetIcon(self, setImage, x, y):
        # set image
        size = 10
        path = DividerDrawer.get_image_filepath(setImage)
        self.canvas.drawImage(
            path, x, y, size, size, mask="auto", preserveAspectRatio=True
        )
        return size + 2

    def smallCapsConfig(self, text, size, style="Name"):
        # Adapter for installations that don't have access to Trajan or Charlemagne.
        # Looks up the best available font for the style and returns any necessary text
        # or metric adjustments as (text, caps, small, font):
        #   text    original text, or uppercase if simulating small caps
        #   caps    font size for full capitals (first letter of each word)
        #   small   font size for small caps (subsequent letters)
        #   font    best matching font
        # If the recommended font is present, returns (text, size, size, font) with the
        # text and the two font sizes unchanged from the method parameters.

        # Metrics for the two small caps fonts and the main fallback
        capsMinion = 0.650  # Times is very similar, about 0.66
        capsCharlemagne = 0.700
        capsTrajan = 0.750
        smallTrajan = 0.638

        font = self.fontStyle[style]
        if "Trajan" in font or "Charlemagne" in font:
            # Close enough, even if we're subbing Trajan for Charlemagne
            return text, size, size, font
        if style == "Expansion":
            # Scale Minion up to Charlemagne metrics
            caps = size * capsCharlemagne / capsMinion
            small = caps  # the "small" caps are the same size as the full caps
        else:
            # Scale Minion up to Trajan metrics
            caps = size * capsTrajan / capsMinion
            small = caps * smallTrajan / capsTrajan
        return text.upper(), caps, small, font

    def nameWidth(self, name, fontSize, style="Name"):
        name, caps, small, font = self.smallCapsConfig(name, fontSize, style)
        w = 0
        name_parts = name.split()
        for i, part in enumerate(name_parts):
            if i != 0:
                w += pdfmetrics.stringWidth(" ", font, caps)
            if small == caps:
                w += pdfmetrics.stringWidth(part, font, caps)
            else:
                w += pdfmetrics.stringWidth(part[0], font, caps)
                w += pdfmetrics.stringWidth(part[1:], font, small)
        return w

    def drawTab(self, item, panel="main", backside=False):
        from io import BytesIO

        card = item.card
        # Skip blank cards
        if card.isBlank():
            return

        # Get panel options
        # TODO: Provide more options for tab & spine graphics, instead of a simple
        # no_tab_artwork switch here.  Perhaps treat banners the same as --cost and
        # --set-icon and add head / tail / spine to LOCATION_OPTIONS. Then you could
        # choose any of the graphic options at any of the locations.  Also, add an option
        # for simple block colors instead of banners.
        if panel == "head":
            if self.options.head == "none":
                return  # no head!
            edge = self.options.head
            facing = self.options.head_facing
            artwork = not self.options.no_tab_artwork
        elif panel == "tail":
            if not self.options.tailWrapper:
                return  # no tail!
            edge = self.options.tail
            facing = self.options.tail_facing
            artwork = not self.options.no_tab_artwork
        elif panel == "spine":
            if not self.options.headWrapper:
                return  # no spine!
            # The spine uses the head edge for widths, and it always faces front
            edge = self.options.head
            facing = "front"
            artwork = not self.options.no_tab_artwork

        # set vertical dimensions
        translate_y = 0
        tabHeight = item.tabHeight
        if panel == "head":
            translate_y += (
                self.options.headWrapper * item.stackHeight
                + self.options.headHeight
                - item.tabHeight
            )
        elif panel == "spine":
            # center tab on the spine
            translate_y += item.stackHeight / 2 - item.tabHeight / 2
        if panel != "tail":
            translate_y += (
                item.cardHeight
                + self.options.tailHeight
                + self.options.tailWrapper * item.stackHeight
            )
        # set horizontal dimensions
        if edge == "wrapper":
            translate_x = 0
            tabWidth = item.cardWidth
        elif self.wantCentreTab(card):
            translate_x = item.cardWidth / 2 - item.tabWidth / 2
            tabWidth = item.tabWidth
        else:
            translate_x = item.getTabOffset(backside=backside and panel == "head")
            tabWidth = item.tabWidth
        margin = 3
        textWidth = tabWidth - 2 * margin

        self.canvas.saveState()
        self.canvas.translate(translate_x, translate_y)

        # set orientation
        if facing == "back":
            # Turn back faces around so they're right side up after folding
            self.canvas.translate(tabWidth, item.tabHeight)
            self.canvas.rotate(180)

        # set background color
        if self.options.black_tabs:
            self.canvas.saveState()
            self.canvas.setFillColorRGB(0, 0, 0)
            self.canvas.rect(0, 0, tabWidth, tabHeight, fill=True)
            self.canvas.restoreState()

        # Determine relative vertical positioning of the major tab elements:
        # align the tops of the card name, the cost numerals, and the set icon.

        # The cost symbols determine vertical positioning, as they are the largest
        # element.  On the Dominion cards, the coin symbols are 17 pt tall, and the cost
        # numbers are set in Minion Std Black 18 (which has numerals ~11 pt tall).

        # The card names and set icons are then top aligned with the cost numerals.  Both
        # use the same 10 pt design size, but the set icon uses the full 10 pt whereas
        # the text is set in small caps and has a higher baseline.

        # If the text is too wide to fit in the space, the method finds a smaller size
        # that fits, keeping the same baseline.  This could bring the text out of
        # alignment with the other two elements, but that's OK.  The actual cards do the
        # same thing.

        # metrics measured from the cards
        trueBannerSize = 18
        trueCoinSize = 17
        bannerSize = trueBannerSize
        bannerHeight = 0

        # metrics from the package assets
        cardType = card.getType()
        if artwork:
            # adjust dimensions based on the application image metrics
            # (ideally they will match the card metrics when space permits)
            # TODO: correctly handle base cards and landscape card-shaped things
            bannerSize = 17
            bannerHeight = cardType.getTabTextHeightOffset()

        # cost symbol metrics
        coinSize = bannerSize - 1
        coinScale = coinSize / trueCoinSize
        coinHeight = bannerHeight
        costHeight = coinHeight + 3 * coinScale
        costTop = costHeight + coinScale * 18 * 0.624  # Minion Std Black numeral height

        # card name metrics
        font = pdfmetrics.getFont(self.fontStyle["Name"])
        fontSize = maxFontSize = 10  # same as the bottom banner on the cards
        nameAscent = fontSize * 0.750  # Trajan caps height
        nameTop = costTop
        nameHeight = nameTop - nameAscent
        textHeight = nameHeight

        # set symbol metrics
        setTop = costTop
        setImageSize = 10
        setImageHeight = setTop - setImageSize
        setTextSize = nameAscent / 0.701  # Minion Pro Italic ascender height
        setTextHeight = textHeight

        # draw banner
        img = cardType.getTabImageFile()
        if artwork and img:
            imgToDraw = DividerDrawer.get_image_filepath(img)
            if self.options.tab_artwork_opacity != 1.0:
                imgObj = Image.open(imgToDraw)
                if imgObj.mode != "RGBA":
                    imgObj = imgObj.convert("RGBA")
                alpha = imgObj.getchannel("A")
                alpha = ImageEnhance.Brightness(alpha).enhance(
                    self.options.tab_artwork_opacity
                )
                imgObj.putalpha(alpha)
                imageBytes = BytesIO()
                imgObj.save(imageBytes, "PNG")
                imageBytes.seek(0)
                imgToDraw = ImageReader(imageBytes)
            self.canvas.drawImage(
                imgToDraw,
                1,
                0,
                tabWidth - 2,
                item.tabHeight - 1,
                preserveAspectRatio=False,
                anchor="n",
                mask="auto",
            )

        # initialize margins
        textInset = textInsetRight = 2 * margin
        if card.isExpansion() and self.options.full_expansion_dividers:
            # TODO: accommodate the scalloped ends on wider expansion dividers
            pass

        # draw cost
        if (
            "tab" in self.options.cost
            and not card.isExpansion()
            and not card.isBlank()
            and card.get_GroupCost() != ""
            and not card.isType("Trash")
        ):
            textInset = 4
            textInset += self.drawCost(card, textInset, costHeight, scale=coinScale)
            textInset += 2

        # draw set image
        if "tab" in self.options.set_icon:
            if self.options.use_text_set_icon:
                italic = self.fontStyle["Italic"]
                setText = card.setTextIcon()
                if setText:
                    self.canvas.setFont(italic, setTextSize)
                    setTextWidth = pdfmetrics.stringWidth(setText, italic, setTextSize)
                    textInsetRight += setTextWidth
                    self.canvas.drawString(
                        tabWidth - textInsetRight, setTextHeight, setText
                    )
                    textInsetRight -= margin
            else:
                setImage = card.setImage(self.options.use_set_icon)
                if setImage:
                    textInsetRight += margin + setImageSize  # they're all square
                    self.drawSetIcon(
                        setImage, tabWidth - textInsetRight + margin, setImageHeight
                    )

        # draw name
        textWidth -= textInset
        textWidth -= textInsetRight

        name = card.name
        # arrows don't format properly in all fonts, so convert them to en dashes
        name = name.replace("→", "–")
        style = "Expansion" if card.isExpansion() else "Name"
        width = self.nameWidth(name, fontSize, style)
        while width > textWidth and fontSize > 7:
            fontSize -= 0.01
            width = self.nameWidth(name, fontSize, style)
        tooLong = width > textWidth
        delimiterText = ""
        if tooLong:
            # Break on a delimiter, if possible
            for delimiter in "/-–—→":  # slashes, dashes, and arrows
                name_lines = name.partition(" {:s} ".format(delimiter))
                if name_lines[1]:
                    delimiterText = name_lines[1][:2]
                    break
            if delimiterText:
                name_lines = name_lines[0] + delimiterText, name_lines[2]
            else:
                # Othersie, break near the middle of the text
                n = len(name) // 2
                lname, _, lmid = name[:n].rpartition(" ")
                rmid, _, rname = name[n:].partition(" ")
                if len(lname) < len(rname):  # which end is shorter?
                    name_lines = (lname + " " + lmid + rmid).lstrip(), rname
                else:
                    name_lines = lname, (lmid + rmid + " " + rname).rstrip()
        else:
            name_lines = (name,)

        nameAscent = font.face.ascent / 1000 * fontSize  # recalc with actual font size
        for linenum, line in enumerate(name_lines):
            h = textHeight
            if tooLong and len(name_lines) > 1:
                if linenum == 0:
                    h += nameAscent / 2 + 1
                else:
                    h -= nameAscent / 2
            # handle line-break delimiters gracefully for centre & right alignment:
            lineWidth = centreWidth = rightWidth = self.nameWidth(line, fontSize, style)
            delimiterIndent = 0
            if delimiterText:
                nudge = margin - 1  # how far delimiters can bleed into the margin
                if linenum == 0:
                    # centering should ignore delimiters
                    centreWidth = self.nameWidth(
                        line[: -len(delimiterText)], fontSize, style
                    )
                    # right alignment should extend them partly into the margin
                    delimiterIndent = min(lineWidth - centreWidth, nudge)
                else:
                    # right align subsequent lines
                    rightWidth = self.nameWidth(line + delimiterText, fontSize, style)
                    delimiterIndent = min(lineWidth - rightWidth + nudge, 0)

            # determine tab alignment
            side = (
                CardPlot.CENTRE
                if self.options.tab_name_align == "centre" or self.wantCentreTab(card)
                else CardPlot.LEFT
                if self.options.tab_name_align == "left"
                else CardPlot.RIGHT
                if self.options.tab_name_align == "right"
                else item.getClosestSide(backside=backside)
            )

            # calculate x position and write text
            lmin = textInset
            rmax = tabWidth - textInsetRight + delimiterIndent - lineWidth
            if side == CardPlot.LEFT:
                w = lmin
            elif side == CardPlot.RIGHT:
                w = rmax
            else:  # centre, but keep it inside the margins
                w = max(lmin, min(tabWidth / 2 - centreWidth / 2, rmax))
            self.drawSmallCaps(line, fontSize, w, h, style=style)

        if False:  # TODO: debug scaffolding
            capheight = 0.750
            xheight = 0.638
            self.canvas.saveState()
            self.canvas.setStrokeGray(0.5)
            self.canvas.setLineWidth(0.1)
            self.canvas.rect(0, textHeight, tabWidth, capheight * maxFontSize)
            self.canvas.rect(0, textHeight, tabWidth, xheight * maxFontSize)
            self.canvas.setLineWidth(0.25)
            self.canvas.setStrokeColorRGB(0.5, 0, 0)
            self.canvas.rect(0, bannerHeight, tabWidth, bannerSize)
            self.canvas.restoreState()

        self.canvas.restoreState()

    def drawSmallCaps(self, text, fontSize, x, y, rightAlign=False, style="Name"):
        # Print small caps text, simulating it if necessary

        def drawWordPiece(text, fontSize):
            self.canvas.setFont(font, fontSize)
            if text != " ":
                self.canvas.drawString(x, y, text)
            return pdfmetrics.stringWidth(text, font, fontSize)

        # Improve typography
        text = text.replace("'", "’")

        text, caps, small, font = self.smallCapsConfig(text, fontSize, style)
        for i, word in enumerate(text.split()):
            if i != 0:
                x += drawWordPiece(" ", caps)
            if small == caps:
                x += drawWordPiece(word, caps)
            else:
                x += drawWordPiece(word[0], caps)
                x += drawWordPiece(word[1:], small)

    def drawSpine(self, item):
        # Draw on the spine (top edge) of wrappers
        card = item.card

        # Skip blank cards
        if card.isBlank():
            return
        # Use the drawTab method for tab-style spines
        if self.options.spine == "tab":
            return self.drawTab(item, panel="spine")

        fontSize = 8  # use the smallest font
        text = card.types_name if self.options.spine == "types" else card.name

        # Skip cards no text, no spine, or no room
        if not text or not self.options.headWrapper or item.stackHeight < fontSize:
            return

        # Print text on the top wrapper edge
        self.canvas.saveState()

        translate_y = (
            item.cardHeight
            + self.options.tailHeight
            + self.options.tailWrapper * item.stackHeight
        )
        margin = 3
        if self.options.head == "wrapper":
            # use full width
            textWidth = item.cardWidth - 2 * margin
            translate_x = margin
        elif self.wantCentreTab(card):
            textWidth = item.tabWidth - 2 * margin
            translate_x = item.cardWidth / 2 - item.tabWidth / 2 + margin
        else:
            textWidth = item.tabWidth - 2 * margin
            translate_x = item.getTabOffset(backside=False) + margin
        self.canvas.translate(translate_x, translate_y)

        # Determine text size
        style = "Expansion" if card.isExpansion() else "Name"
        width = self.nameWidth(text, fontSize, style)
        while width > textWidth and fontSize > 6:
            fontSize -= 0.01
            width = self.nameWidth(text, fontSize, style)
        # self.canvas.setFont(self.fontStyle["Name"], fontSize)

        font = pdfmetrics.getFont(self.fontStyle["Name"])
        textAscent = font.face.ascent / 1000 * fontSize
        h = item.stackHeight / 2 - textAscent / 2
        w = textWidth / 2 - width / 2

        self.drawSmallCaps(text, fontSize, w, h, style=style)
        self.canvas.restoreState()

    def drawText(self, item, divider_text="card", wrapper="no"):
        card = item.card
        # Skip blank cards
        if card.isBlank():
            return

        self.canvas.saveState()
        usedHeight = 0
        totalHeight = item.cardHeight

        # Figure out if any translation needs to be done
        # TODO: adjust non-sleeve wrappers as needed
        if wrapper == "back":
            self.canvas.translate(item.cardWidth, item.cardHeight + item.tabHeight)
            self.canvas.rotate(180)

        if wrapper == "front":
            self.canvas.translate(
                0, item.cardHeight + item.tabHeight + item.stackHeight
            )

        if wrapper == "front" or wrapper == "back":
            if self.options.notch_length > 0:
                usedHeight += self.options.notch_height * cm

        # Add 'body-top' items
        drewTopIcon = False
        Image_x_left = 4
        if "body-top" in self.options.cost and not card.isExpansion():
            Image_x_left += self.drawCost(
                card, Image_x_left, totalHeight - usedHeight - 0.5 * cm
            )
            drewTopIcon = True

        Image_x_right = item.cardWidth - 4
        if "body-top" in self.options.set_icon and not card.isExpansion():
            setImage = card.setImage(self.options.use_set_icon)
            if setImage:
                Image_x_right -= 16
                self.drawSetIcon(
                    setImage, Image_x_right, totalHeight - usedHeight - 0.5 * cm - 3
                )
                drewTopIcon = True

        if self.options.count:
            Image_x_right -= self.drawCardCount(
                card, Image_x_right, totalHeight - usedHeight - 0.5 * cm
            )
            drewTopIcon = True

        if self.options.types and not card.isExpansion():

            #  Calculate how much width have for printing
            #  Want centered, but number of other items can limit
            left_margin = Image_x_left
            right_margin = item.cardWidth - Image_x_right
            worst_margin = max(left_margin, right_margin)
            w = item.cardWidth / 2
            textWidth = item.cardWidth - 2 * worst_margin
            textWidth2 = item.cardWidth - left_margin - right_margin

            #  Calculate font size that will fit in the area
            #  Start with centering type.  But if the fontSize gets too small
            #  use all the available space, even if it is not centered on the card
            fontSize = 8
            failover = False
            width = self.nameWidth(card.types_name, fontSize)
            while width > textWidth:
                fontSize -= 0.01
                if fontSize < 6 and not failover:
                    # Start over using all available space left on line
                    textWidth = textWidth2
                    w = left_margin + (textWidth2 / 2)
                    fontSize = 8
                    failover = True
                width = self.nameWidth(card.types_name, fontSize)

            #  Print out the text in the right spot
            h = totalHeight - usedHeight - 0.5 * cm
            if card.types_name != " ":
                self.drawSmallCaps(card.types_name, fontSize, w - width / 2, h)
            drewTopIcon = True

        if drewTopIcon:
            usedHeight += 15

        # Figure out what text is to be printed on this divider
        descriptions = None
        if divider_text == "card" and card.description:
            # Add the card text to the divider
            descriptions = card.description
        elif divider_text == "rules" and card.extra:
            # Add the extra rules text to the divider
            descriptions = card.extra

        if descriptions is None:
            # No text to print, so exit early and cleanly
            self.canvas.restoreState()
            return

        s = getSampleStyleSheet()["BodyText"]
        s.fontName = self.fontStyle["Rules"]
        if divider_text == "card" and not card.isExpansion():
            s.alignment = TA_CENTER
        else:
            s.alignment = TA_JUSTIFY

        textHorizontalMargin = 0.5 * cm
        textVerticalMargin = 0.3 * cm
        textBoxWidth = item.cardWidth - 2 * textHorizontalMargin
        textBoxHeight = totalHeight - usedHeight - 2 * textVerticalMargin
        spacerHeight = 0.2 * cm
        minSpacerHeight = 0.05 * cm

        if not card.isExpansion():
            emWidth = textBoxWidth / s.fontSize
            descriptions = self.add_inline_text(card, descriptions, emWidth)
        descriptions = re.split("\n", descriptions)
        while True:
            paragraphs = []
            # this accounts for the spacers we insert between paragraphs
            h = (len(descriptions) - 1) * spacerHeight
            for d in descriptions:
                if card.isExpansion():
                    dmod = d
                else:
                    dmod = self.add_inline_images(d, s.fontSize)
                try:
                    p = Paragraph(dmod, s)
                except ValueError as e:
                    raise ValueError(
                        'Error rendering text from "{}": {} ("{}")'.format(
                            card.name, e, dmod
                        )
                    )
                h += p.wrap(textBoxWidth, textBoxHeight)[1]
                paragraphs.append(p)

            if h <= textBoxHeight or s.fontSize <= 1 or s.leading <= 1:
                break
            else:
                s.fontSize -= 1
                s.leading -= 1
                spacerHeight = max(spacerHeight - 1, minSpacerHeight)

        h = totalHeight - usedHeight - textVerticalMargin
        for p in paragraphs:
            h -= p.height
            p.drawOn(self.canvas, textHorizontalMargin, h)
            h -= spacerHeight

        self.canvas.restoreState()

    def drawDivider(self, item, isBack=False, horizontalMargin=-1, verticalMargin=-1):
        # First save canvas state
        self.canvas.saveState()

        # Make sure we use the right margins
        if horizontalMargin < 0:
            horizontalMargin = self.options.horizontalMargin
        if verticalMargin < 0:
            verticalMargin = self.options.verticalMargin

        # apply the transforms to get us to the corner of the current card
        self.canvas.resetTransforms()
        pageWidth = self.options.paperwidth - (2 * horizontalMargin)
        self.canvas.translate(horizontalMargin, verticalMargin)
        if isBack:
            self.canvas.translate(
                self.options.back_offset, self.options.back_offset_height
            )
            pageWidth -= 2 * self.options.back_offset
        else:
            self.canvas.translate(
                self.options.front_offset, self.options.front_offset_height
            )

        item.translate(self.canvas, pageWidth, isBack)

        # actual drawing
        if not self.options.tabs_only:
            self.drawOutline(item, isBack)

        if self.options.wrapper:
            wrap = "front"
            isBack = False  # Safety.  If a wrapper, there is no backside
        else:
            wrap = "no"

        # TODO: simplify this
        cardText = item.textTypeBack if isBack else item.textTypeFront

        self.drawTab(item, panel="head", backside=isBack)
        self.drawSpine(item)
        if not self.options.tabs_only:
            self.drawTab(item, panel="tail", backside=True)
            self.drawText(item, cardText, wrapper=wrap)  # TODO
            # if self.options.headWrapper:
            #     self.drawText(item, self.options.head_text, wrapper="back")  # TODO
            if self.options.tailWrapper:
                self.drawText(item, self.options.tail_text, wrapper="back")  # TODO

        # retore the canvas state to the way we found it
        self.canvas.restoreState()

    def drawSetNames(self, pageItems, backside=False):
        # print sets for this page
        self.canvas.saveState()

        try:
            # calculate the text height, font size, and orientation
            maxFontsize = 12
            minFontsize = 6
            fontname = self.fontStyle["Regular"]
            font = pdfmetrics.getFont(fontname)
            fontHeightRelative = (font.face.ascent + abs(font.face.descent)) / 1000.0

            layouts = [
                {
                    "rotation": 0,
                    "minMarginHeight": self.options.minVerticalMargin,
                    "totalMarginHeight": self.options.verticalMargin
                    + (self.options.back_offset_height if backside else 0),
                    "width": self.options.paperwidth,
                },
                {
                    "rotation": 90,
                    "minMarginHeight": self.options.minHorizontalMargin,
                    "totalMarginHeight": self.options.horizontalMargin
                    + (-self.options.back_offset if backside else 0),
                    "width": self.options.paperheight,
                },
            ]

            # Pick whether to print setnames horizontally along bottom
            # (i=0) or vertically along left (i=1).  We pick whichever has more
            # space.
            fontsize = 0
            maxAvailableMargin = 0
            layoutIndex = -1
            for i, layout in enumerate(layouts):
                availableMargin = (
                    layout["totalMarginHeight"] - layout["minMarginHeight"]
                )
                if availableMargin > maxAvailableMargin:
                    maxAvailableMargin = availableMargin
                    fontsize = availableMargin / fontHeightRelative
                    fontsize = min(maxFontsize, fontsize)
                    layoutIndex = i

            if fontsize < minFontsize:
                import warnings

                warnings.warn("Not enough space to display set names")
                return

            layout = layouts[layoutIndex]

            self.canvas.setFont(fontname, fontsize)

            # Centered on page
            xPos = layout["width"] / 2
            # Place at the very edge of the margin
            yPos = layout["minMarginHeight"]

            if layout["rotation"]:
                self.canvas.rotate(layout["rotation"])
                yPos = -yPos

            sets = []
            for item in pageItems:
                setTitle = " ".join(
                    word.capitalize() for word in item.card.cardset.split()
                )
                if setTitle not in sets:
                    sets.append(setTitle)

            self.canvas.drawCentredString(xPos, yPos, "/".join(sets))
        finally:
            self.canvas.restoreState()

    def calculatePages(self, cards):
        options = self.options

        # Adjust for Vertical vs Horizontal
        if options.orientation == "vertical":
            options.dividerWidth, options.dividerBaseHeight = (
                options.dominionCardHeight,
                options.dominionCardWidth,
            )
        else:
            options.dividerWidth, options.dividerBaseHeight = (
                options.dominionCardWidth,
                options.dominionCardHeight,
            )

        options.fixedMargins = False
        options.spin = 0
        options.label = options.label if "label" in options else None
        if options.label is not None:
            # Set Margins
            options.minmarginheight = (
                options.label["margin-top"] + options.label["pad-vertical"]
            ) * cm
            options.minmarginwidth = (
                options.label["margin-left"] + options.label["pad-horizontal"]
            ) * cm
            # Set Label size
            options.labelHeight = (
                options.label["tab-height"] - 2 * options.label["pad-vertical"]
            ) * cm
            options.labelWidth = (
                options.label["width"] - 2 * options.label["pad-horizontal"]
            ) * cm
            # Set spacing between labels
            options.verticalBorderSpace = (
                options.label["gap-vertical"] + 2 * options.label["pad-vertical"]
            ) * cm
            options.horizontalBorderSpace = (
                options.label["gap-horizontal"] + 2 * options.label["pad-horizontal"]
            ) * cm
            # Fix up other settings
            options.fixedMargins = True
            options.dividerBaseHeight = options.label["body-height"] * cm
            options.dividerWidth = options.labelWidth
            options.rotate = 0
            options.dominionCardWidth = options.dividerWidth
            options.dominionCardHeight = options.dividerBaseHeight
            if options.orientation == "vertical":
                # Spin the card.  This is similar to a rotate, but given a label has a fixed location on the page
                # the divider must change shape and rotation.  Rotate can't be used directly,
                # since that is used in the calculation of where to place the dividers on the page.
                # This 'spins' the divider only, but keeps all the other calcuations the same.
                options.spin = 270
                # Now fix up the card dimentions.
                options.dominionCardWidth = (
                    options.labelHeight + options.label["body-height"] * cm
                )
                options.dominionCardHeight = (
                    options.labelWidth - options.label["tab-height"] * cm
                )
                options.labelWidth = options.dominionCardWidth
                # Need to swap now because they will be swapped again later because "vertical"
                options.dominionCardWidth, options.dominionCardHeight = (
                    options.dominionCardHeight,
                    options.dominionCardWidth,
                )

            # Fix up the label dimentions
            if options.tab_side != "full":
                options.labelWidth = options.tabwidth * cm

        else:
            # Margins already set
            # Set Label size
            options.labelHeight = 0.9 * cm
            options.labelWidth = options.tabwidth * cm
            if options.tab_side == "full" or options.labelWidth > options.dividerWidth:
                options.labelWidth = options.dividerWidth
            # Set spacing between labels
            options.verticalBorderSpace = options.vertical_gap * cm
            options.horizontalBorderSpace = options.horizontal_gap * cm

        # Set head & tail heights now that card & label heights are set
        options.headHeight = (
            options.head_height * cm
            if options.head_height
            else options.dividerBaseHeight
            if options.head == "wrapper"
            else options.labelHeight
            if options.head in ["tab", "strap"]
            else 0
        )
        options.tailHeight = (
            options.tail_height * cm
            if options.tail_height
            else options.dividerBaseHeight + options.labelHeight
            if options.tail == "folder"
            else options.dividerBaseHeight
            if options.tail == "wrapper"
            else options.labelHeight
            if options.tail == "strap"
            else 0
        )

        # Set Height
        options.dividerHeight = options.dividerBaseHeight + options.headHeight

        # Start building up the space reserved for each divider
        options.dividerWidthReserved = options.dividerWidth
        options.dividerHeightReserved = options.dividerHeight

        if options.wrapper:
            # Adjust height for wrapper.  Use the maximum thickness of any divider so we know anything will fit.
            maxStackHeight = max(c.getStackHeight(options.thickness) for c in cards)
            print("Max Card Stack Height: {:.2f}cm ".format(maxStackHeight / cm))
            options.dividerHeightReserved = totalHeight(options, maxStackHeight)

        # Adjust for rotation
        if options.rotate == 90 or options.rotate == 270:
            # for page calculations, this just means switching horizontal and vertical for these rotations.
            options.dividerWidth, options.dividerHeight = (
                options.dividerHeight,
                options.dividerWidth,
            )
            options.dividerWidthReserved, options.dividerHeightReserved = (
                options.dividerHeightReserved,
                options.dividerWidthReserved,
            )

        options.dividerWidthReserved += options.horizontalBorderSpace
        options.dividerHeightReserved += options.verticalBorderSpace

        # as we don't draw anything in the final border, it shouldn't count towards how many tabs we can fit
        # so it gets added back in to the page size here
        numDividersVerticalP = int(
            (
                options.paperheight
                - 2 * options.minmarginheight
                + options.verticalBorderSpace
            )
            / options.dividerHeightReserved
        )
        numDividersHorizontalP = int(
            (
                options.paperwidth
                - 2 * options.minmarginwidth
                + options.horizontalBorderSpace
            )
            / options.dividerWidthReserved
        )
        numDividersVerticalL = int(
            (
                options.paperwidth
                - 2 * options.minmarginwidth
                + options.verticalBorderSpace
            )
            / options.dividerHeightReserved
        )
        numDividersHorizontalL = int(
            (
                options.paperheight
                - 2 * options.minmarginheight
                + options.horizontalBorderSpace
            )
            / options.dividerWidthReserved
        )

        if (
            (
                numDividersVerticalL * numDividersHorizontalL
                > numDividersVerticalP * numDividersHorizontalP
            )
            and not options.fixedMargins
        ) and options.rotate == 0:
            options.numDividersVertical = numDividersVerticalL
            options.numDividersHorizontal = numDividersHorizontalL
            options.minHorizontalMargin = options.minmarginheight
            options.minVerticalMargin = options.minmarginwidth
            options.paperheight, options.paperwidth = (
                options.paperwidth,
                options.paperheight,
            )
        else:
            options.numDividersVertical = numDividersVerticalP
            options.numDividersHorizontal = numDividersHorizontalP
            options.minHorizontalMargin = options.minmarginheight
            options.minVerticalMargin = options.minmarginwidth

        assert (
            options.numDividersVertical > 0
        ), "Could not vertically fit the divider on the page"
        assert (
            options.numDividersHorizontal > 0
        ), "Could not horizontally fit the divider on the page"

        if not options.fixedMargins:
            # dynamically max margins
            options.horizontalMargin = (
                options.paperwidth
                - options.numDividersHorizontal * options.dividerWidthReserved
                + options.horizontalBorderSpace
            ) / 2
            options.verticalMargin = (
                options.paperheight
                - options.numDividersVertical * options.dividerHeightReserved
                + options.verticalBorderSpace
            ) / 2
        else:
            options.horizontalMargin = options.minmarginwidth
            options.verticalMargin = options.minmarginheight

        items = self.setupCardPlots(options, cards)  # Turn cards into items to plot
        self.pages = self.convert2pages(options, items)  # plot items into pages

    def setupCardPlots(self, options, cards=[]):
        # First, set up common information for the dividers
        # Doing a lot of this up front, while the cards are ordered
        # just in case the dividers need to be reordered on the page.
        # By setting up first, any tab or text flipping will be correct,
        # even if the divider moves around a bit on the pages.

        # Drawing line type
        if options.cropmarks:
            if "dot" in options.linetype.lower():
                lineType = "dot"  # Allow the DOTs if requested
            elif "line" in options.linetype.lower():
                lineType = "line"  # Allow the LINEs if requested
            else:
                lineType = "no_line"
        else:
            lineType = options.linetype.lower()

        # Starting with tabs on the left, right, or centre?
        if "right" in options.tab_side:
            tabSideStart = CardPlot.RIGHT  # right, right-alternate, right-flip
        elif "left" in options.tab_side:
            tabSideStart = CardPlot.LEFT  # left, left-alternate, left-flip
        elif "centre" in options.tab_side:
            tabSideStart = CardPlot.CENTRE  # centre
        elif "full" == options.tab_side:
            tabSideStart = CardPlot.CENTRE  # full
        else:
            tabSideStart = CardPlot.LEFT  # catch anything else

        cardWidth = options.dominionCardWidth
        cardHeight = options.dominionCardHeight

        # Adjust for Vertical
        if options.orientation == "vertical":
            cardWidth, cardHeight = cardHeight, cardWidth

        # Initialized CardPlot tabs
        CardPlot.tabSetup(
            tabNumber=options.tab_number,
            cardWidth=cardWidth,
            cardHeight=cardHeight,
            lineType=lineType,
            tabWidth=options.labelWidth,
            tabHeight=options.labelHeight,
            start=tabSideStart,
            serpentine=options.tab_serpentine,
            wrapper=options.wrapper,
        )

        # Now go through all the cards and create their plotter information record...
        items = []
        nextTabIndex = CardPlot.tabRestart()
        lastCardSet = None

        for card in cards:
            # Check if tab needs to be reset to the start
            if options.expansion_reset_tabs and not card.isExpansion():
                if lastCardSet != card.cardset_tag:
                    # In a new expansion, so reset the tabs to start over
                    nextTabIndex = CardPlot.tabRestart()
                    cardset_count = Card.sets[card.cardset_tag].get("count", 0)
                    if options.tab_number > cardset_count and cardset_count > 0:

                        #  Limit to the number of tabs to the number of dividers in the expansion
                        CardPlot.tabSetup(
                            tabNumber=Card.sets[card.cardset_tag]["count"]
                        )
                    elif CardPlot.tabNumber != options.tab_number:
                        # Make sure tabs are set back to the original
                        CardPlot.tabSetup(tabNumber=options.tab_number)
            lastCardSet = card.cardset_tag

            if self.wantCentreTab(card):
                # If we want centred expansion cards, then force this divider to centre
                thisTabIndex = 0
            else:
                thisTabIndex = nextTabIndex

            item = CardPlot(
                card,
                rotation=options.spin if options.spin != 0 else options.rotate,
                tabIndex=thisTabIndex,
                textTypeFront=options.text_front,
                textTypeBack=options.text_back,
                stackHeight=card.getStackHeight(options.thickness),
                options=options,
            )

            if card.isExpansion() and options.full_expansion_dividers:
                # Fix up the item to have a full tab with text centred
                item.tabWidth = cardWidth
                item.tabNumber = 1
                item.tabOffset = 0

            if (
                options.flip
                and (options.tab_number == 2)
                and (thisTabIndex != CardPlot.tabStart)
            ):
                item.flipFront2Back()  # Instead of flipping the tab, flip the whole divider front to back

            # Before moving on, setup the tab for the next item if this tab slot was used
            if thisTabIndex == nextTabIndex:
                nextTabIndex = item.nextTab(
                    nextTabIndex
                )  # already used, so move on to the next tab

            items.append(item)
        return items

    def convert2pages(self, options, items=[]):
        # Take the layout and all the items and separate the items into pages.
        # Each item will have all its plotting information filled in.
        rows = options.numDividersVertical
        columns = options.numDividersHorizontal
        numPerPage = rows * columns
        # Calculate if there is always enough room for horizontal and vertical crop marks
        RoomForCropH = (
            options.horizontalBorderSpace
            > 2 * (options.cropmarkLength + options.cropmarkSpacing) * cm
        )
        RoomForCropV = (
            options.verticalBorderSpace
            > 2 * (options.cropmarkLength + options.cropmarkSpacing) * cm
        )

        items = split(items, numPerPage)
        pages = []
        for pageNum, pageItems in enumerate(items):
            page = []
            last_item = len(pageItems) - 1
            last_row = (rows - 1) - (last_item // columns)
            for i in range(numPerPage):
                if pageItems and i < len(pageItems):
                    # Given a CardPlot object called item, its number on the page, and the page number
                    # Return/set the items x,y,rotation, crop mark settings, and page number
                    # For x,y assume the canvas has already been adjusted for the margins
                    x = i % columns
                    y = (rows - 1) - (i // columns)
                    pageItems[i].x = x * options.dividerWidthReserved
                    pageItems[i].y = y * options.dividerHeightReserved
                    pageItems[i].cropOnTop = (y == rows - 1) or RoomForCropV
                    pageItems[i].cropOnBottom = (
                        (y == last_row)
                        or (y == last_row + 1 and x > last_item % columns)
                        or RoomForCropV
                    )
                    pageItems[i].cropOnLeft = (x == 0) or RoomForCropH
                    pageItems[i].cropOnRight = (
                        (x == columns - 1) or (i == last_item) or RoomForCropH
                    )
                    # pageItems[i].rotation = 0
                    pageItems[i].page = pageNum + 1
                    page.append(pageItems[i])

            pages.append((options.horizontalMargin, options.verticalMargin, page))
        return pages

    def drawDividers(self, cards=[]):
        if not self.pages:
            self.calculatePages(cards)

        # Now go page by page and print the dividers
        for pageNum, pageInfo in enumerate(self.pages):
            hMargin, vMargin, page = pageInfo

            drawFooter = not self.options.no_page_footer and (
                not self.options.tabs_only and self.options.order != "global"
            )

            if (
                self.options.tabs_only
                or self.options.text_back == "none"
                or self.options.wrapper
            ):
                # Don't print the sheets with the back of the dividers
                backSides = [False]
            else:
                backSides = [False, True]

            for isBack in backSides:
                # Page footer
                if drawFooter:
                    self.drawSetNames(page, isBack)

                # Page
                for item in page:
                    # print the dividor
                    self.drawDivider(
                        item,
                        isBack=isBack,
                        horizontalMargin=hMargin,
                        verticalMargin=vMargin,
                    )
                self.canvas.showPage()

            if pageNum + 1 == self.options.num_pages:
                break
