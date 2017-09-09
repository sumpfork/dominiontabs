import os
import re
import sys

import pkg_resources

from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth
from cards import Card


def split(l, n):
    i = 0
    while i < len(l) - n:
        yield l[i:i + n]
        i += n
    yield l[i:]


class CardPlot(object):
    # This object contains information needed to print a divider on a page.
    # It goes beyond information about the general card/divider to include page specific drawing information.
    # It also includes helpful methods used in manipulating the object and keeping up with tab locations.

    LEFT, CENTRE, RIGHT, TOP, BOTTOM = range(100, 105)  # location & directional constants

    tabNumber = 1  # Number of different tab locations
    tabIncrement = 0  # Either 1, 0, or -1.  Used to select next tab. This can change if tabSerpentine.
    tabIncrementStart = 0  # Starting value of tabIncrement
    tabStart = 1  # The starting tab location.
    tabStartSide = LEFT  # The starting side for the tabs
    tabSerpentine = False  # What to do at the end of a line of tabs.  False = start over.  True = reverses direction.
    dividerWidth = 0  # Width of just the divider, with no extra padding/spacing. NEEDS TO BE SET.
    tabWidth = 0  # Width of the tab.  NEEDS TO BE SET.

    @staticmethod
    def tabSetup(tabNumber=None, dividerWidth=None, tabWidth=None, start=None, serpentine=None):
        # Set up the basic tab information used in calculations when a new CardPlot object is created.
        # This needs to be called at least once before the first CardPlot object is created and then it
        # needs to be called any time one of the above parameters needs to change.
        CardPlot.tabNumber = tabNumber if tabNumber is not None else CardPlot.tabNumber
        CardPlot.tabStartSide = start if start is not None else CardPlot.tabStartSide
        CardPlot.tabSerpentine = serpentine if serpentine is not None else CardPlot.tabSerpentine
        CardPlot.dividerWidth = dividerWidth if dividerWidth is not None else CardPlot.dividerWidth
        CardPlot.tabWidth = tabWidth if tabWidth is not None else CardPlot.tabWidth
        # LEFT        tabs        RIGHT
        # +---+ +---+ +---+ +---+ +---+
        # | 1 | | 2 | | 3 | |...| | N |   Note: tabNumber = N, N >=1, 0 is for centred tabs
        # +   +-+   +-+   +-+   +-+   +

        # Setup first tab as well as staring point and direction of increment for tabs.
        if CardPlot.tabStartSide == CardPlot.RIGHT:
            CardPlot.tabStart = CardPlot.tabNumber
            CardPlot.tabIncrementStart = -1
        elif CardPlot.tabStartSide == CardPlot.CENTRE:
            # Get as close to centre as possible
            CardPlot.tabStart = int((CardPlot.tabNumber + 1) / 2)
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

    def __init__(self, card, x=0, y=0, rotation=0, height=0, width=0, stackHeight=0, tabIndex=None, page=0,
                 lineType='line', textTypeFront="card", textTypeBack="rules",
                 cropOnTop=False, cropOnBottom=False, cropOnLeft=False, cropOnRight=False):
        self.card = card
        self.x = x  # x location of the lower left corner of the card on the page
        self.y = y  # y location of the lower left corner of the card on the page
        self.rotation = rotation  # of the card. 0, 90, 180, 270
        self.lineType = lineType  # Type of outline to use: line, dot, none
        self.width = width  # Width of the divider including any divider to divider spacing
        self.height = height  # Height of the divider including any divider to divider spacing
        self.stackHeight = stackHeight  # The height of a stack of these cards. Used for interleaving.
        self.textTypeFront = textTypeFront  # What card text to put on the front of the divider
        self.textTypeBack = textTypeBack  # What card text to put on the back of the divider
        self.cropOnTop = cropOnTop  # When true, cropmarks needed along TOP *printed* edge of the card
        self.cropOnBottom = cropOnBottom  # When true, cropmarks needed along BOTTOM *printed* edge of the card
        self.cropOnLeft = cropOnLeft  # When true, cropmarks needed along LEFT *printed* edge of the card
        self.cropOnRight = cropOnRight  # When true, cropmarks needed along RIGHT *printed* edge of the card
        self.page = page  # holds page number of this printed card
        self.tabIndex = tabIndex  # Tab location index.  Starts at 1 and goes up to CardPlot.tabNumber
        # And figure out the backside index
        if self.tabIndex == 0:
            self.tabIndexBack = 0  # Exact Centre special case, so swapping is still exact centre
        elif CardPlot.tabNumber == 1:
            self.tabIndex = self.tabIndexBack = 1  # There is only one tab, so can only use 1 for both sides
        elif 1 <= self.tabIndex <= CardPlot.tabNumber:
            self.tabIndexBack = CardPlot.tabNumber + 1 - self.tabIndex
        else:
            self.tabIndex = self.tabIndexBack = 1  # Should never get here, but assigning a default just in case.

        # Now set the offsets and the closest edge to the tab
        if self.tabIndex == 0:
            # Special case for centred tabs
            self.tabOffset = self.tabOffsetBack = (CardPlot.dividerWidth - CardPlot.tabWidth) / 2
            self.closestSide = CardPlot.CENTRE
        elif CardPlot.tabNumber <= 1:
            # If just one tab, then can be right, centre, or left
            self.closestSide = CardPlot.tabStartSide
            if CardPlot.tabStartSide == CardPlot.RIGHT:
                self.tabOffset = CardPlot.dividerWidth - CardPlot.tabWidth
                self.tabOffsetBack = 0
            elif CardPlot.tabStartSide == CardPlot.CENTRE:
                self.tabOffset = (CardPlot.dividerWidth - CardPlot.tabWidth) / 2
                self.tabOffsetBack = (CardPlot.dividerWidth - CardPlot.tabWidth) / 2
            else:
                # LEFT and anything else
                self.tabOffset = 0
                self.tabOffsetBack = CardPlot.dividerWidth - CardPlot.tabWidth
        else:
            # More than 1 tabs
            self.tabOffset = (self.tabIndex - 1) * (
                             (CardPlot.dividerWidth - CardPlot.tabWidth) / (CardPlot.tabNumber - 1))
            self.tabOffsetBack = CardPlot.dividerWidth - CardPlot.tabWidth - self.tabOffset

            # Set  which edge is closest to the tab
            if self.tabIndex <= CardPlot.tabNumber / 2:
                self.closestSide = CardPlot.LEFT
            else:
                self.closestSide = CardPlot.RIGHT if self.tabIndex > (CardPlot.tabNumber + 1) / 2 else CardPlot.CENTRE

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

        if 1 <= tab <= CardPlot.tabNumber:
            next = tab + CardPlot.tabIncrement
            # Now check for wrap around
            if next > CardPlot.tabNumber:
                next = 1
            elif next < 1:
                next = CardPlot.tabNumber
        else:
            next = 1  # Should never get here, but assigning a default just in case.

        if CardPlot.tabSerpentine and CardPlot.tabNumber > 2:
            if (next == 1) or (next == CardPlot.tabNumber):
                # reverse direction for next tab
                CardPlot.tabIncrement *= -1
        return next

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
        # The tab moves from right(left) to left(right).  If centre, it stays the same.
        # And then the divider's text is moved to the other side of the page.
        self.tabIndex, self.tabIndexBack = self.tabIndexBack, self.tabIndex
        self.tabOffset, self.tabOffsetBack = self.tabOffsetBack, self.tabOffset
        self.textTypeFront, self.textTypeBack = self.textTypeBack, self.textTypeFront
        self.closestSide = self.getClosestSide(backside=True)

    def translate(self, canvas, page_width, backside=False):
        # Translate the page x,y of the lower left of item, taking into account the rotation,
        # and set up the canvas so that (0,0) is now at the lower lower left of the item
        # and the item can be drawn as if it is in the "standard" orientation.
        # So when done, the canvas is set and ready to draw the divider
        x = self.x
        y = self.y
        rotation = self.rotation

        if backside:
            x = page_width - x - self.width

        if self.rotation == 180:
            x += self.width
            y += self.height
        elif self.rotation == 90:
            if backside:
                x += self.width
                rotation = 270
            else:
                y += self.width
        elif self.rotation == 270:
            if backside:
                x += self.width - self.height
                y += self.width
                rotation = 90
            else:
                x += self.height

        rotation = 360 - rotation % 360  # ReportLab rotates counter clockwise, not clockwise.
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
        self.LEFT, self.RIGHT, self.TOP, self.BOTTOM, self.LINE, self.NO_LINE, self.DOT = range(1, 8)  # Constants
        if cropmarkLength < 0:
            cropmarkLength = 0.2
        if cropmarkSpacing < 0:
            cropmarkSpacing = 0.1
        self.CropMarkLength = cropmarkLength * cm  # The length of a cropmark
        self.CropMarkSpacing = cropmarkSpacing * cm  # The spacing between the cut point and the start of the cropmark
        self.DotSize = 0.2  # Size of dot marks

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def getXY(self):
        return (self.x, self.y)

    def move(self, delta_x=0, delta_y=0, pen=False):
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

    def cropmark(self, enabled, direction):
        # From current point, draw a cropmark in the correct direction and return to starting point
        if enabled:
            x, y = self.getXY()  # Saving for later

            if direction == self.TOP:
                self.move(0, self.CropMarkSpacing)
                self.move(0, self.CropMarkLength, self.LINE)
            if direction == self.BOTTOM:
                self.move(0, -self.CropMarkSpacing)
                self.move(0, -self.CropMarkLength, self.LINE)
            if direction == self.RIGHT:
                self.move(self.CropMarkSpacing, 0)
                self.move(self.CropMarkLength, 0, self.LINE)
            if direction == self.LEFT:
                self.move(-self.CropMarkSpacing, 0)
                self.move(-self.CropMarkLength, 0, self.LINE)
            self.setXY(x, y)  # Restore to starting point


class DividerDrawer(object):
    def __init__(self, options=None):
        self.canvas = None
        self.pages = None
        self.options = options

    @staticmethod
    def get_image_filepath(fname):
        return pkg_resources.resource_filename('domdiv', os.path.join('images', fname))

    def draw(self, cards=[], options=None):
        if options is not None:
            self.options = options

        self.registerFonts()
        self.canvas = canvas.Canvas(
            self.options.outfile,
            pagesize=(self.options.paperwidth, self.options.paperheight))
        self.drawDividers(cards)
        if self.options.info or self.options.info_all:
            self.drawInfo()
        self.canvas.save()

    def registerFonts(self):
        # the following are filenames from both an Adobe Reader install and a download from fontsgeek
        fontfilenames = ['MinionPro-Regular.ttf',
                         'MinionPro-Bold.ttf',
                         'MinionPro-It.ttf',
                         'Minion Pro Regular.ttf',
                         'Minion Pro Bold.ttf',
                         'Minion Pro Italic.ttf']
        # first figure out which, if any, are present
        fontpaths = [os.path.join('fonts', fname) for fname in fontfilenames]
        fontpaths = [fpath for fpath in fontpaths if pkg_resources.resource_exists('domdiv', fpath)]
        self.font_mapping = {'Regular': [fpath for fpath in fontpaths if 'Regular' in fpath],
                             'Bold': [fpath for fpath in fontpaths if 'Bold' in fpath],
                             'Italic': [fpath for fpath in fontpaths if 'It' in fpath]}
        # then make sure that we have at least one for each type
        for fonttype in self.font_mapping:
            if not len(self.font_mapping[fonttype]):
                print >> sys.stderr, ("Warning, Minion Pro ttf file for {} missing from domdiv/fonts!"
                                      " Falling back on Times font for everything.").format(fonttype)
                self.font_mapping = {'Regular': 'Times-Roman',
                                     'Bold': 'Times-Bold',
                                     'Italic': 'Times-Oblique'}
                break
            else:
                # and finally register and tag one for each type
                ftag = 'MinionPro-{}'.format(fonttype)
                pdfmetrics.registerFont(TTFont(ftag,
                                               pkg_resources.resource_filename('domdiv',
                                                                               self.font_mapping[fonttype][0])))
                self.font_mapping[fonttype] = ftag

        self.font_mapping['Monospaced'] = 'Courier'

    def drawTextPages(self, pages, margin=1.0, fontsize=10, leading=10, spacer=0.05):
        s = getSampleStyleSheet()['BodyText']
        s.fontName = self.font_mapping['Monospaced']
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
                    p = Paragraph(line, s)
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
        pageCount = 0
        if self.options.info or self.options.info_all:
            text = "<para alignment='center'><font size=18><b>Sumpfork's Dominion Tabbed Divider Generator</b></font>\n"
            text += "&nbsp;\n" * 2
            text += "Online generator at: "
            text += "<a href='http://domtabs.sandflea.org/' color='blue'>http://domtabs.sandflea.org</a>\n\n"
            text += "Source code on GitHub at: "
            text += "<a href='https://github.com/sumpfork/dominiontabs' color='blue'>"
            text += "https://github.com/sumpfork/dominiontabs</a>\n\n"
            text += "Options for this file:  "

            sep = '@@@***!!!***@@@'
            cmd = " ".join(self.options.argv)
            cmd = cmd.replace(' --', sep + '--')
            cmd = cmd.replace(' -', sep + '-')
            cmd = cmd.replace(sep, '\n' + '&nbsp;' * 25)
            text += cmd
            text += '&nbsp;\n' * 2

            if printIt:
                self.drawTextPages([text], margin=1.0, fontsize=10, leading=10, spacer=0.05)
            pageCount += 1

        if self.options.info_all:
            linesPerPage = 80
            lines = self.options.help.replace('\n\n', '\n \n').replace(' ', '&nbsp;').split('\n')
            pages = []
            lineCount = 0
            text = ""
            for line in lines:
                lineCount += 1
                text += line + '\n'
                if lineCount >= linesPerPage:
                    pages.append(text)
                    pageCount += 1
                    lineCount = 0
                    text = ""
            if text:
                pages.append(text)
                pageCount += 1
            if printIt:
                self.drawTextPages(pages, margin=0.75, fontsize=6, leading=7, spacer=0.1)

        return pageCount

    def wantCentreTab(self, card):
        return (card.isExpansion() and self.options.centre_expansion_dividers) or self.options.tab_side == "centre"

    def drawOutline(self, item, isBack=False):
        # draw outline or cropmarks
        if isBack and not self.options.cropmarks:
            return
        self.canvas.saveState()
        self.canvas.setLineWidth(self.options.linewidth)

        # The back is flipped
        if isBack:
            self.canvas.translate(self.options.dividerWidth, 0)
            self.canvas.scale(-1, 1)

        plotter = Plotter(self.canvas,
                          cropmarkLength=self.options.cropmarkLength,
                          cropmarkSpacing=self.options.cropmarkSpacing)

        dividerWidth = self.options.dividerWidth
        dividerHeight = self.options.dividerHeight
        dividerBaseHeight = self.options.dividerBaseHeight
        tabLabelWidth = self.options.labelWidth

        theTabHeight = dividerHeight - dividerBaseHeight
        theTabWidth = self.options.labelWidth
        left2tab = item.getTabOffset(backside=isBack)
        right2tab = dividerWidth - tabLabelWidth - left2tab
        nearZero = 0.01
        left2tab = left2tab if left2tab > nearZero else 0
        right2tab = right2tab if right2tab > nearZero else 0

        if item.lineType.lower() == 'line':
            lineType = plotter.LINE
            lineTypeNoDot = plotter.LINE
        elif item.lineType.lower() == 'dot':
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

        CropRight = self.options.cropmarks and item.translateCropmarkEnable(item.RIGHT)
        CropLeft = self.options.cropmarks and item.translateCropmarkEnable(item.LEFT)
        CropTop = self.options.cropmarks and item.translateCropmarkEnable(item.TOP)
        CropBottom = self.options.cropmarks and item.translateCropmarkEnable(item.BOTTOM)

        RIGHT = plotter.RIGHT
        LEFT = plotter.LEFT
        BOTTOM = plotter.BOTTOM
        TOP = plotter.TOP
        NO_LINE = plotter.NO_LINE

        if not self.options.wrapper:
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
            plotter.move(0, 0)  # to A
            plotter.cropmark(CropLeft, LEFT)
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.move(left2tab, 0, lineStyle[0])  # A to V
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.move(theTabWidth, 0, lineStyle[0])  # V to W
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.move(right2tab, 0, lineStyle[7])  # W to B
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.cropmark(CropRight, RIGHT)
            plotter.move(0, dividerBaseHeight, lineStyle[9])  # B to C
            plotter.cropmark(CropRight, RIGHT)
            plotter.move(-right2tab, 0, lineStyle[9])  # C to D
            plotter.move(0, theTabHeight, lineStyle[7])  # D to E
            plotter.cropmark(CropTop, TOP)
            plotter.move(right2tab, 0, NO_LINE)  # E to Y
            plotter.cropmark(CropTop, TOP)
            plotter.cropmark(CropRight, RIGHT)
            plotter.move(-right2tab, 0, NO_LINE)  # Y to E
            plotter.move(-theTabWidth, 0, lineStyle[7])  # E to F
            plotter.cropmark(CropTop, TOP)
            plotter.move(0, -theTabHeight, lineStyle[8])  # F to G
            plotter.move(-left2tab, 0, lineStyle[8])  # G to H
            plotter.cropmark(CropLeft, LEFT)
            plotter.move(0, theTabHeight, NO_LINE)  # H to Z
            plotter.cropmark(CropTop, TOP)
            plotter.cropmark(CropLeft, LEFT)
            plotter.move(0, -theTabHeight, NO_LINE)  # Z to H
            plotter.move(0, -dividerBaseHeight, lineStyle[7])  # H to A

        else:
            # Card Wrapper Outline

            # Set up values used in the outline
            minNotch = 0.1 * cm  # Don't really want notches that are smaller than this.
            if self.options.notch_length * cm > minNotch:
                # A notch length was given, so notches are wanted
                notch_height = self.options.notch_height * cm  # thumb notch height
                notch1 = notch2 = notch3 = notch4 = self.options.notch_length * cm  # thumb notch width
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

            # Setup the rest of the lineStyle's
            lineStyle[1] = lineType if notch1used else lineTypeNoDot
            lineStyle[2] = lineType if notch2used else lineTypeNoDot
            lineStyle[3] = lineType if notch3used else lineTypeNoDot
            lineStyle[4] = lineType if notch4used else lineTypeNoDot
            lineStyle[5] = lineType if notch1used and right2tab > 0 else lineTypeNoDot
            lineStyle[6] = lineType if notch4used and left2tab > 0 else lineTypeNoDot

            stackHeight = item.card.getStackHeight(self.options.thickness)
            body_minus_notches = dividerBaseHeight - (2.0 * notch_height)
            tab2notch1 = right2tab - notch1
            tab2notch4 = left2tab - notch4

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
            #    +        0CC.................................................M0        +
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
            #  B-+       Cb8---------------8                   9---------------1G       +-Ia
            #                              |                   |
            #   -+A      Cc+              D7-------------------7E              +Ga      +-Ib
            #    |         |               |                   |               |        |
            #     <-----left2tab----------> <--tabLabelWidth--> <-----right2tab-------->

            plotter.setXY(0, 0)                              # to A
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.cropmark(CropLeft, LEFT)
            plotter.move(0, theTabHeight, NO_LINE)           # A to B
            plotter.cropmark(CropLeft, LEFT)
            plotter.move(0, notch_height, NO_LINE)           # B to GG
            plotter.cropmark(CropLeft and (notch4used or notch1used), LEFT)
            plotter.move(notch4, 0, lineStyle[4])              # GG to Ca
            plotter.move(0, -notch_height, lineStyle[8])       # Ca  to Cb
            plotter.move(0, -theTabHeight, NO_LINE)          # Cb to Cc
            plotter.cropmark(CropBottom and (notch4used or notch2used), BOTTOM)
            plotter.move(0, theTabHeight, NO_LINE)           # Cc to Cb
            plotter.move(tab2notch4, 0, lineStyle[8])          # Cb to C
            plotter.move(0, -theTabHeight, lineStyle[7])       # C  to D
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.move(tabLabelWidth, 0, lineStyle[7])       # D to E
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.move(0, theTabHeight, lineStyle[9])        # E to F
            plotter.move(tab2notch1, 0, lineStyle[1])           # F to G
            plotter.move(0, -theTabHeight, NO_LINE)          # G to Ga
            plotter.cropmark(CropBottom and (notch1used or notch3used), BOTTOM)
            plotter.move(0, theTabHeight, NO_LINE)           # Ga to G
            plotter.move(0, notch_height, lineStyle[1])        # G to H
            plotter.move(notch1, 0, lineStyle[5])              # H to I
            plotter.cropmark(CropRight and (notch1used or notch4used), RIGHT)
            plotter.move(0, -notch_height, NO_LINE)          # I to Ia
            plotter.cropmark(CropRight, RIGHT)
            plotter.move(0, -theTabHeight, NO_LINE)          # Ia to Ib
            plotter.cropmark(CropRight, RIGHT)
            plotter.cropmark(CropBottom, BOTTOM)
            plotter.move(0, theTabHeight, NO_LINE)           # Ib to Ia
            plotter.move(0, notch_height, NO_LINE)           # Ia to I
            plotter.move(0, body_minus_notches, lineStyle[3])  # I  to J
            plotter.cropmark(CropRight and (notch2used or notch3used), RIGHT)
            plotter.move(-notch3, 0, lineStyle[3])             # J  to K
            plotter.move(0, notch_height, lineStyle[0])        # K  to L
            plotter.move(0, stackHeight, lineStyle[0])         # L  to M
            plotter.move(0, notch_height, lineStyle[3])        # M  to N
            plotter.move(notch3, 0, lineStyle[3])              # N  to O
            plotter.cropmark(CropRight and (notch2used or notch3used), RIGHT)
            plotter.move(0, body_minus_notches, lineStyle[5])  # O  to P
            plotter.cropmark(CropRight and (notch1used or notch4used), RIGHT)
            plotter.move(0, notch_height, NO_LINE)           # P  to Pa
            plotter.cropmark(CropRight, RIGHT)
            plotter.move(0, -notch_height, NO_LINE)          # Pa  to P
            plotter.move(-notch1, 0, lineStyle[1])             # P  to Q
            plotter.move(0, notch_height, lineStyle[9])        # Q  to R
            plotter.move(-tab2notch1, 0, lineStyle[9])          # R  to S
            plotter.move(0, stackHeight, lineStyle[0])         # S  to T
            plotter.move(0, theTabHeight, lineStyle[7])        # S  to U
            plotter.cropmark(CropTop, TOP)
            plotter.move(tab2notch1, 0, NO_LINE)              # U to Ua
            plotter.cropmark(CropTop and (notch1used or notch3used), TOP)
            plotter.move(notch1, 0, NO_LINE)                 # Ua to Ub
            plotter.cropmark(CropTop, TOP)
            plotter.cropmark(CropRight, RIGHT)
            plotter.move(-notch1, 0, NO_LINE)                # Ub to Ua
            plotter.move(-tab2notch1, 0, NO_LINE)             # Ua to U
            plotter.move(-theTabWidth, 0, lineStyle[7])        # U  to V
            plotter.cropmark(CropTop, TOP)
            plotter.move(-tab2notch4, 0, NO_LINE)            # V to Va
            plotter.cropmark(CropTop and (notch4used or notch2used), TOP)
            plotter.move(tab2notch4, 0, NO_LINE)             # Va to V
            plotter.move(0, -theTabHeight, lineStyle[0])       # V  to W
            plotter.move(0, -stackHeight, lineStyle[8])        # W  to X
            plotter.move(-tab2notch4, 0, lineStyle[8])         # X  to Y
            plotter.move(0, -notch_height, lineStyle[4])       # Y  to Ya
            plotter.move(-notch4, 0, lineStyle[6])             # Ya to Z
            plotter.cropmark(CropLeft and (notch1used or notch4used), LEFT)
            plotter.move(0, notch_height, NO_LINE)           # Z  to Za
            plotter.cropmark(CropLeft, LEFT)
            plotter.move(0, theTabHeight + stackHeight, NO_LINE)  # Za to Zb
            plotter.cropmark(CropTop, TOP)
            plotter.cropmark(CropLeft, LEFT)
            plotter.move(0, -theTabHeight - stackHeight, NO_LINE)  # Zb to Za
            plotter.move(0, -notch_height, NO_LINE)           # Za  to Z
            plotter.move(0, -body_minus_notches, lineStyle[2])  # Z  to AA
            plotter.cropmark(CropLeft and (notch2used or notch3used), LEFT)
            plotter.move(notch2, 0, lineStyle[2])               # AA to BB
            plotter.move(0, -notch_height, lineStyle[0])        # BB to CC
            plotter.move(0, -stackHeight, lineStyle[0])         # CC to DD
            plotter.move(0, -notch_height, lineStyle[2])        # DD to EE
            plotter.move(-notch2, 0, lineStyle[2])              # EE to FF
            plotter.cropmark(CropLeft and (notch2used or notch3used), LEFT)
            plotter.move(0, -body_minus_notches, lineStyle[6])  # FF  to GG

            # Add fold lines
            self.canvas.setStrokeGray(0.9)
            plotter.setXY(left2tab, dividerHeight + stackHeight + dividerBaseHeight)  # to X
            plotter.move(theTabWidth, 0, plotter.LINE)  # X to S
            plotter.move(0, stackHeight)                 # S to T
            plotter.move(-theTabWidth, 0, plotter.LINE)   # V to S

            plotter.setXY(notch2, dividerHeight)   # to DD
            plotter.move(dividerWidth - notch2 - notch3, 0, plotter.LINE)   # DD to L
            plotter.move(0, stackHeight)                 # L to M
            plotter.move(-dividerWidth + notch2 + notch3, 0, plotter.LINE)  # M to CC

        self.canvas.restoreState()

    def add_inline_images(self, text, fontsize):
        def replace_image_tag(text,
                              fontsize,
                              tag_pattern,
                              fname_replace,
                              fontsize_multiplier,
                              height_percent,
                              text_fontsize_multiplier=None):
            replace_template = '<img src="{fpath}" width={width} height="{height_percent}%" valign="middle" />&thinsp;'
            offset = 0
            for match in re.finditer(tag_pattern, text):
                replace = replace_template
                tag = match.group(0)
                fname = re.sub(tag_pattern, fname_replace, tag)
                if text_fontsize_multiplier is not None:
                    font_replace = re.sub(tag_pattern,
                                          '<font size={}>\\1</font>'.format(fontsize * text_fontsize_multiplier),
                                          tag)
                    replace = font_replace + replace
                replace = replace.format(fpath=DividerDrawer.get_image_filepath(fname),
                                         width=fontsize * fontsize_multiplier,
                                         height_percent=height_percent)
                text = text[:match.start() + offset] + replace + text[match.end() + offset:]
                offset += len(replace) - len(match.group(0))
            return text
        # Coins
        replace_specs = [
            # Coins
            (r'(\d+)\s\<\*COIN\*\>', 'coin_small_\\1.png', 2.4, 200),
            (r'(\d+)\s(c|C)oin(s)?', 'coin_small_\\1.png', 1.2, 100),
            (r'\?\s(c|C)oin(s)?', 'coin_small_question.png', 1.2, 100),
            (r'(empty|\_)\s(c|C)oin(s)?', 'coin_small_empty.png', 1.2, 100),

            # VP
            (r'(?:\s+|\<)VP(?:\s+|\>|\.|$)', 'victory_emblem.png', 1.25, 100),
            (r'(\d+)\s*\<\*VP\*\>', 'victory_emblem.png', 2, 160, 1.3),

            # Debt
            (r'(\d+)\sDebt', 'debt_\\1.png', 1.2, 105),
            (r'Debt', 'debt.png', 1.2, 105),

            # Potion
            (r'(\d+)\s*\<\*POTION\*\>', 'potion_small.png', 2, 140, 1.5),
            (r'Potion', 'potion_small.png', 1.2, 100)

        ]
        for args in replace_specs:
            text = replace_image_tag(text, fontsize, *args)

        return text.strip()

    def add_inline_text(self, card, text):
        # Bonuses
        text = card.getBonusBoldText(text)

        # <line>
        replace = "<center>%s\n" % ("&ndash;" * 22)
        text = re.sub("\<line\>", replace, text)

        #  <tab> and \t
        text = re.sub("\<tab\>", '\t', text)
        text = re.sub("\<t\>", '\t', text)
        text = re.sub("\t", "&nbsp;" * 4, text)

        # various breaks
        text = re.sub("\<br\>", "<br />", text)
        text = re.sub("\<n\>", "\n", text)

        # alignments
        text = re.sub("\<c\>", "<center>", text)
        text = re.sub("\<center\>", "\n<para alignment='center'>", text)

        text = re.sub("\<l\>", "<left>", text)
        text = re.sub("\<left\>", "\n<para alignment='left'>", text)

        text = re.sub("\<r\>", "<right>", text)
        text = re.sub("\<right\>", "\n<para alignment='right'>", text)

        text = re.sub("\<j\>", "<justify>", text)
        text = re.sub("\<justify\>", "\n<para alignment='justify'>", text)
        return text.strip().strip('\n')

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
                DividerDrawer.get_image_filepath('card.png'),
                x,
                countHeight,
                16,
                16,
                preserveAspectRatio=True,
                mask='auto')
            self.canvas.setFont(self.font_mapping['Bold'], 10)
            self.canvas.drawCentredString(x + 8, countHeight + 4, str(value))

            # now draw the number of sets
            if count > 1:
                count_string = u"{}\u00d7".format(count)
                width_string = stringWidth(count_string, self.font_mapping['Regular'], 10)
                width_string -= 1  # adjust to make it closer to image
                width += width_string
                x -= width_string
                self.canvas.setFont(self.font_mapping['Regular'], 10)
                self.canvas.drawString(x, countHeight + 4, count_string)

        return width + 1

    def drawCost(self, card, x, y, costOffset=-1):
        # width starts at 2 (1 pt border on each side)
        width = 2

        costHeight = y + costOffset
        coinHeight = costHeight - 5
        potHeight = y - 3
        potSize = 11

        if (not(card.cost == "" or
                (card.debtcost and int(card.cost) == 0) or
                (card.potcost and int(card.cost) == 0))):

            self.canvas.drawImage(
                DividerDrawer.get_image_filepath('coin_small.png'),
                x,
                coinHeight,
                16,
                16,
                preserveAspectRatio=True,
                mask='auto')
            self.canvas.setFont(self.font_mapping['Bold'], 12)
            self.canvas.drawCentredString(x + 8, costHeight, str(card.cost))
            self.canvas.setFillColorRGB(0, 0, 0)
            x += 17
            width += 16

        if card.debtcost:
            self.canvas.drawImage(
                DividerDrawer.get_image_filepath('debt.png'),
                x,
                coinHeight,
                16,
                16,
                preserveAspectRatio=True,
                mask=[170, 255, 170, 255, 170, 255])
            self.canvas.setFillColorRGB(1, 1, 1)
            self.canvas.setFont(self.font_mapping['Bold'], 12)
            self.canvas.drawCentredString(x + 8, costHeight, str(card.debtcost))
            self.canvas.setFillColorRGB(0, 0, 0)
            x += 17
            width += 16

        if card.potcost:
            self.canvas.drawImage(
                DividerDrawer.get_image_filepath('potion.png'),
                x,
                potHeight,
                potSize,
                potSize,
                preserveAspectRatio=True,
                mask='auto')
            width += potSize

        return width

    def drawSetIcon(self, setImage, x, y):
        # set image
        w = 2
        self.canvas.drawImage(
            DividerDrawer.get_image_filepath(setImage),
            x,
            y,
            14,
            12,
            mask='auto')
        return w + 14

    def nameWidth(self, name, fontSize):
        w = 0
        name_parts = name.split()
        for i, part in enumerate(name_parts):
            if i != 0:
                w += pdfmetrics.stringWidth(' ', self.font_mapping['Regular'],
                                            fontSize)
            w += pdfmetrics.stringWidth(part[0], self.font_mapping['Regular'],
                                        fontSize)
            w += pdfmetrics.stringWidth(part[1:], self.font_mapping['Regular'],
                                        fontSize - 2)
        return w

    def drawTab(self, item, wrapper="no", backside=False):
        card = item.card
        # draw tab flap
        self.canvas.saveState()

        translate_y = self.options.dividerHeight - self.options.labelHeight
        if self.wantCentreTab(card):
            translate_x = self.options.dividerWidth / 2 - self.options.labelWidth / 2
        else:
            translate_x = item.getTabOffset(backside=backside)

        if wrapper == "back":
            translate_y = self.options.labelHeight
            if self.wantCentreTab(card):
                translate_x = self.options.dividerWidth / 2 + self.options.labelWidth / 2
            else:
                translate_x = item.getTabOffset(backside=False) + self.options.labelWidth

        if wrapper == "front":
            translate_y = translate_y + self.options.dividerHeight + 2.0 * card.getStackHeight(
                self.options.thickness)

        self.canvas.translate(translate_x, translate_y)

        if wrapper == "back":
            self.canvas.rotate(180)

        # allow for 3 pt border on each side
        textWidth = self.options.labelWidth - 6
        textHeight = 7
        if self.options.no_tab_artwork:
            textHeight = 4
        textHeight = self.options.labelHeight / 2 - textHeight + \
            card.getType().getTabTextHeightOffset()

        # draw banner
        img = card.getType().getNoCoinTabImageFile()
        if not self.options.no_tab_artwork and img:
            self.canvas.drawImage(
                DividerDrawer.get_image_filepath(img),
                1,
                0,
                self.options.labelWidth - 2,
                self.options.labelHeight - 1,
                preserveAspectRatio=False,
                anchor='n',
                mask='auto')

        # draw cost
        if not card.isExpansion() and not card.isBlank(
        ) and not card.isLandmark() and not card.isType('Trash'):
            if 'tab' in self.options.cost:
                textInset = 4
                textInset += self.drawCost(
                    card, textInset, textHeight,
                    card.getType().getTabCostHeightOffset())
            else:
                textInset = 6
        else:
            textInset = 13

        # draw set image
        # always need to offset from right edge, to make sure it stays on
        # banner
        textInsetRight = 6
        if self.options.use_text_set_icon:
            setImageHeight = card.getType().getTabTextHeightOffset()
            setText = card.setTextIcon()
            self.canvas.setFont(self.font_mapping['Italic'], 8)
            if setText is None:
                setText = ""

            self.canvas.drawCentredString(self.options.labelWidth - 10,
                                          textHeight + 2, setText)
            textInsetRight = 15
        else:
            setImage = card.setImage()
            if setImage and 'tab' in self.options.set_icon:
                setImageHeight = 3 + card.getType().getTabTextHeightOffset()

                self.drawSetIcon(setImage, self.options.labelWidth - 20,
                                 setImageHeight)

                textInsetRight = 20

        # draw name
        fontSize = 12
        name = card.name.upper()

        textWidth -= textInset
        textWidth -= textInsetRight

        width = self.nameWidth(name, fontSize)
        while width > textWidth and fontSize > 8:
            fontSize -= .01
            width = self.nameWidth(name, fontSize)
        tooLong = width > textWidth
        if tooLong:
            name_lines = name.partition(' / ')
            if name_lines[1]:
                name_lines = (name_lines[0] + ' /', name_lines[2])
            else:
                name_lines = name.split(None, 1)
        else:
            name_lines = [name]
        # if tooLong:
        #    print name

        for linenum, line in enumerate(name_lines):
            h = textHeight
            if tooLong and len(name_lines) > 1:
                if linenum == 0:
                    h += h / 2
                else:
                    h -= h / 2

            words = line.split()
            NotRightEdge = (
                not self.options.tab_name_align == "right" and
                (self.options.tab_name_align == "centre" or
                 item.getClosestSide(backside=backside) != CardPlot.RIGHT or
                 not self.options.tab_name_align == "edge"))
            if wrapper == "back" and not self.options.tab_name_align == "centre":
                NotRightEdge = not NotRightEdge
            if NotRightEdge:
                if (self.options.tab_name_align == "centre" or self.wantCentreTab(card)
                        or (item.getClosestSide(backside=backside) == CardPlot.CENTRE)):
                    w = self.options.labelWidth / 2 - self.nameWidth(
                        line, fontSize) / 2
                else:
                    w = textInset

                def drawWordPiece(text, fontSize):
                    self.canvas.setFont(self.font_mapping['Regular'], fontSize)
                    if text != ' ':
                        self.canvas.drawString(w, h, text)
                    return pdfmetrics.stringWidth(text, self.font_mapping['Regular'],
                                                  fontSize)

                for i, word in enumerate(words):
                    if i != 0:
                        w += drawWordPiece(' ', fontSize)
                    w += drawWordPiece(word[0], fontSize)
                    w += drawWordPiece(word[1:], fontSize - 2)
            else:
                # align text to the right if tab is on right side
                if self.options.tab_name_align == "centre" or self.wantCentreTab(card):
                    w = self.options.labelWidth / 2 - self.nameWidth(
                        line, fontSize) / 2
                    w = self.options.labelWidth - w
                else:
                    w = self.options.labelWidth - textInsetRight

                # to make tabs easier to read when grouped together extra 3pt is for
                # space between text + set symbol
                w -= 3

                words.reverse()

                def drawWordPiece(text, fontSize):
                    self.canvas.setFont(self.font_mapping['Regular'], fontSize)
                    if text != ' ':
                        self.canvas.drawRightString(w, h, text)
                    return -pdfmetrics.stringWidth(text, self.font_mapping['Regular'],
                                                   fontSize)

                for i, word in enumerate(words):
                    w += drawWordPiece(word[1:], fontSize - 2)
                    w += drawWordPiece(word[0], fontSize)
                    if i != len(words) - 1:
                        w += drawWordPiece(' ', fontSize)

        if wrapper == "front" and card.getCardCount() >= 5:
            # Print smaller version of name on the top wrapper edge
            self.canvas.translate(0, -card.getStackHeight(
                self.options.thickness))  # move into area used by the wrapper
            fontSize = 8  # use the smallest font
            self.canvas.setFont(self.font_mapping['Regular'], fontSize)

            textHeight = fontSize - 2
            textHeight = card.getStackHeight(
                self.options.thickness) / 2 - textHeight / 2
            h = textHeight
            words = name.split()
            w = self.options.labelWidth / 2 - self.nameWidth(name,
                                                             fontSize) / 2

            def drawWordPiece(text, fontSize):
                self.canvas.setFont(self.font_mapping['Regular'], fontSize)
                if text != ' ':
                    self.canvas.drawString(w, h, text)
                return pdfmetrics.stringWidth(text, self.font_mapping['Regular'],
                                              fontSize)

            for i, word in enumerate(words):
                if i != 0:
                    w += drawWordPiece(' ', fontSize)
                w += drawWordPiece(word[0], fontSize)
                w += drawWordPiece(word[1:], fontSize - 2)

        self.canvas.restoreState()

    def drawText(self, card, divider_text="card", wrapper="no"):

        self.canvas.saveState()
        usedHeight = 0
        totalHeight = self.options.dividerHeight - self.options.labelHeight

        # Figure out if any translation needs to be done
        if wrapper == "back":
            self.canvas.translate(self.options.dividerWidth,
                                  self.options.dividerHeight)
            self.canvas.rotate(180)

        if wrapper == "front":
            self.canvas.translate(0, self.options.dividerHeight +
                                  card.getStackHeight(self.options.thickness))

        if wrapper == "front" or wrapper == "back":
            if self.options.notch_length > 0:
                usedHeight += self.options.notch_height * cm

        # Add 'body-top' items
        drewTopIcon = False
        Image_x_left = 4
        if 'body-top' in self.options.cost and not card.isExpansion():
            Image_x_left += self.drawCost(card, Image_x_left, totalHeight - usedHeight - 0.5 * cm)
            drewTopIcon = True

        Image_x_right = self.options.dividerWidth - 4
        if 'body-top' in self.options.set_icon and not card.isExpansion():
            setImage = card.setImage()
            if setImage:
                Image_x_right -= 16
                self.drawSetIcon(setImage, Image_x_right,
                                 totalHeight - usedHeight - 0.5 * cm - 3)
                drewTopIcon = True

        if self.options.count:
            Image_x_right -= self.drawCardCount(card, Image_x_right,
                                                totalHeight - usedHeight - 0.5 * cm)
            drewTopIcon = True

        if (self.options.types and not card.isExpansion()):

            #  Calculate how much width have for printing
            #  Want centered, but number of other items can limit
            left_margin = Image_x_left
            right_margin = self.options.dividerWidth - Image_x_right
            worst_margin = max(left_margin, right_margin)
            w = self.options.dividerWidth / 2
            textWidth = self.options.dividerWidth - 2 * worst_margin
            textWidth2 = self.options.dividerWidth - left_margin - right_margin

            #  Calculate font size that will fit in the area
            #  Start with centering type.  But if the fontSize gets too small
            #  use all the available space, even if it is not centered on the card
            fontSize = 8
            failover = False
            width = stringWidth(card.types_name, self.font_mapping['Regular'], fontSize)
            while width > textWidth:
                fontSize -= .01
                if fontSize < 6 and not failover:
                    # Start over using all available space left on line
                    textWidth = textWidth2
                    w = left_margin + (textWidth2 / 2)
                    fontSize = 8
                    failover = True
                width = stringWidth(card.types_name, self.font_mapping['Regular'], fontSize)

            #  Print out the text in the right spot
            h = totalHeight - usedHeight - 0.5 * cm
            self.canvas.setFont(self.font_mapping['Regular'], fontSize)
            if card.types_name != ' ':
                self.canvas.drawCentredString(w, h, card.types_name)
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

        s = getSampleStyleSheet()['BodyText']
        s.fontName = "Times-Roman"
        if divider_text == "card" and not card.isExpansion():
            s.alignment = TA_CENTER
        else:
            s.alignment = TA_JUSTIFY

        textHorizontalMargin = .5 * cm
        textVerticalMargin = .3 * cm
        textBoxWidth = self.options.dividerWidth - 2 * textHorizontalMargin
        textBoxHeight = totalHeight - usedHeight - 2 * textVerticalMargin
        spacerHeight = 0.2 * cm
        minSpacerHeight = 0.05 * cm

        if not card.isExpansion():
            descriptions = self.add_inline_text(card, descriptions)
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
                p = Paragraph(dmod, s)
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
            self.canvas.translate(self.options.back_offset,
                                  self.options.back_offset_height)
            pageWidth -= 2 * self.options.back_offset

        item.translate(self.canvas, pageWidth, isBack)

        # actual drawing
        if not self.options.tabs_only:
            self.drawOutline(item, isBack)

        if self.options.wrapper:
            wrap = "front"
            isBack = False  # Safety.  If a wrapper, there is no backside
        else:
            wrap = "no"

        cardText = item.textTypeFront
        if isBack:
            cardText = item.textTypeBack

        self.drawTab(item, wrapper=wrap, backside=isBack)
        if not self.options.tabs_only:
            self.drawText(item.card, cardText, wrapper=wrap)
            if self.options.wrapper:
                self.drawTab(item, wrapper="back", backside=True)
                self.drawText(item.card, item.textTypeBack, wrapper="back")

        # retore the canvas state to the way we found it
        self.canvas.restoreState()

    def drawSetNames(self, pageItems):
        # print sets for this page
        self.canvas.saveState()

        try:
            # calculate the text height, font size, and orientation
            maxFontsize = 12
            minFontsize = 6
            fontname = self.font_mapping['Regular']
            font = pdfmetrics.getFont(fontname)
            fontHeightRelative = (
                font.face.ascent + abs(font.face.descent)) / 1000.0

            canFit = False

            layouts = [{'rotation': 0,
                        'minMarginHeight': self.options.minVerticalMargin,
                        'totalMarginHeight': self.options.verticalMargin,
                        'width': self.options.paperwidth},
                       {'rotation': 90,
                        'minMarginHeight': self.options.minHorizontalMargin,
                        'totalMarginHeight': self.options.horizontalMargin,
                        'width': self.options.paperheight}]

            for layout in layouts:
                availableMargin = layout['totalMarginHeight'] - layout[
                    'minMarginHeight']
                fontsize = availableMargin / fontHeightRelative
                fontsize = min(maxFontsize, fontsize)
                if fontsize >= minFontsize:
                    canFit = True
                    break

            if not canFit:
                import warnings
                warnings.warn("Not enough space to display set names")
                return

            self.canvas.setFont(fontname, fontsize)

            xPos = layout['width'] / 2
            # Place at the very edge of the margin
            yPos = layout['minMarginHeight']

            sets = []
            for item in pageItems:
                setTitle = item.card.cardset.title()
                if setTitle not in sets:
                    sets.append(setTitle)

                # Centered on page
                xPos = layout['width'] / 2
                # Place at the very edge of the margin
                yPos = layout['minMarginHeight']

                if layout['rotation']:
                    self.canvas.rotate(layout['rotation'])
                    yPos = -yPos

            self.canvas.drawCentredString(xPos, yPos, '/'.join(sets))
        finally:
            self.canvas.restoreState()

    def calculatePages(self, cards):
        options = self.options

        if options.orientation == "vertical":
            options.dividerWidth, options.dividerBaseHeight = options.dominionCardHeight, options.dominionCardWidth
        else:
            options.dividerWidth, options.dividerBaseHeight = options.dominionCardWidth, options.dominionCardHeight

        options.fixedMargins = False
        if options.tabs_only:
            # fixed for Avery 8867 for now
            options.minmarginwidth = 0.86 * cm  # was 0.76
            options.minmarginheight = 1.37 * cm  # was 1.27
            options.labelHeight = 1.07 * cm  # was 1.27
            options.labelWidth = 4.24 * cm  # was 4.44
            options.horizontalBorderSpace = 0.96 * cm  # was 0.76
            options.verticalBorderSpace = 0.20 * cm  # was 0.01
            options.dividerBaseHeight = 0
            options.dividerWidth = options.labelWidth
            options.fixedMargins = True
        else:
            if options.tab_side == "full":
                options.labelWidth = options.dividerWidth
            else:
                options.labelWidth = options.tabwidth * cm
            options.labelHeight = .9 * cm
            options.horizontalBorderSpace = options.horizontal_gap * cm
            options.verticalBorderSpace = options.vertical_gap * cm

        options.dividerHeight = options.dividerBaseHeight + options.labelHeight

        options.dividerWidthReserved = options.dividerWidth + options.horizontalBorderSpace
        options.dividerHeightReserved = options.dividerHeight + options.verticalBorderSpace
        if options.wrapper:
            max_card_stack_height = max(c.getStackHeight(options.thickness)
                                        for c in cards)
            options.dividerHeightReserved = (options.dividerHeightReserved * 2) + (
                max_card_stack_height * 2)
            print "Max Card Stack Height: {:.2f}cm ".format(max_card_stack_height)

        # as we don't draw anything in the final border, it shouldn't count towards how many tabs we can fit
        # so it gets added back in to the page size here
        numDividersVerticalP = int(
            (options.paperheight - 2 * options.minmarginheight + options.verticalBorderSpace) /
            options.dividerHeightReserved)
        numDividersHorizontalP = int(
            (options.paperwidth - 2 * options.minmarginwidth + options.horizontalBorderSpace) /
            options.dividerWidthReserved)
        numDividersVerticalL = int(
            (options.paperwidth - 2 * options.minmarginwidth + options.verticalBorderSpace) /
            options.dividerHeightReserved)
        numDividersHorizontalL = int(
            (options.paperheight - 2 * options.minmarginheight + options.horizontalBorderSpace) /
            options.dividerWidthReserved)

        if ((numDividersVerticalL * numDividersHorizontalL > numDividersVerticalP *
             numDividersHorizontalP) and not options.fixedMargins):
            options.numDividersVertical = numDividersVerticalL
            options.numDividersHorizontal = numDividersHorizontalL
            options.minHorizontalMargin = options.minmarginheight
            options.minVerticalMargin = options.minmarginwidth
            options.paperheight, options.paperwidth = options.paperwidth, options.paperheight
        else:
            options.numDividersVertical = numDividersVerticalP
            options.numDividersHorizontal = numDividersHorizontalP
            options.minHorizontalMargin = options.minmarginheight
            options.minVerticalMargin = options.minmarginwidth

        if not options.fixedMargins:
            # dynamically max margins
            options.horizontalMargin = (options.paperwidth - options.numDividersHorizontal *
                                        options.dividerWidthReserved + options.horizontalBorderSpace) / 2
            options.verticalMargin = (options.paperheight - options.numDividersVertical *
                                      options.dividerHeightReserved + options.verticalBorderSpace) / 2
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
            if 'dot' in options.linetype.lower():
                lineType = 'dot'  # Allow the DOTs if requested
            else:
                lineType = 'no_line'
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

        # Initialized CardPlot tabs
        CardPlot.tabSetup(tabNumber=options.tab_number,
                          dividerWidth=options.dividerWidth,
                          tabWidth=options.labelWidth,
                          start=tabSideStart,
                          serpentine=options.tab_serpentine)

        # Now go through all the cards and create their plotter information record...
        items = []
        nextTabIndex = CardPlot.tabRestart()
        lastCardSet = None
        reset_expansion_tabs = options.expansion_dividers and options.expansion_reset_tabs

        for card in cards:
            lastTabIndex = nextTabIndex
            if options.wrapper:
                height = ((2 * (options.dividerHeight + card.getStackHeight(options.thickness)))
                          + options.verticalBorderSpace)
            else:
                height = options.dividerHeightReserved

            if reset_expansion_tabs and not card.isExpansion():
                if lastCardSet != card.cardset_tag:
                    # In a new expansion, so reset the tabs to start over
                    nextTabIndex = CardPlot.tabRestart()
                    if options.tab_number > Card.sets[card.cardset_tag]['count']:
                        #  Limit to the number of tabs to the number of dividers in the expansion
                        CardPlot.tabSetup(tabNumber=Card.sets[card.cardset_tag]['count'])
                    elif CardPlot.tabNumber != options.tab_number:
                        # Make sure tabs are set back to the original
                        CardPlot.tabSetup(tabNumber=options.tab_number)
            lastCardSet = card.cardset_tag

            if self.wantCentreTab(card):
                # If we want centred expansion cards, then force this divider to centre
                thisTabIndex = 0
            else:
                thisTabIndex = nextTabIndex

            item = CardPlot(card,
                            height=height,
                            width=options.dividerWidthReserved,
                            lineType=lineType,
                            tabIndex=thisTabIndex,
                            textTypeFront=options.text_front,
                            textTypeBack=options.text_back,
                            stackHeight=card.getStackHeight(options.thickness)
                            )
            if options.flip and (options.tab_number == 2) and (thisTabIndex != CardPlot.tabStart):
                item.flipFront2Back()  # Instead of flipping the tab, flip the whole divider front to back

            # Before moving on, setup the tab for the next item if this tab slot was used
            if thisTabIndex == nextTabIndex:
                nextTabIndex = item.nextTab(nextTabIndex)  # already used, so move on to the next tab

            items.append(item)

        return items

    def convert2pages(self, options, items=[]):
        # Take the layout and all the items and separate the items into pages.
        # Each item will have all its plotting information filled in.
        rows = options.numDividersVertical
        columns = options.numDividersHorizontal
        numPerPage = rows * columns

        items = split(items, numPerPage)
        pages = []
        for pageNum, pageItems in enumerate(items):
            page = []
            for i in range(numPerPage):
                if pageItems and i < len(pageItems):
                    # Given a CardPlot object called item, its number on the page, and the page number
                    # Return/set the items x,y,rotation, crop mark settings, and page number
                    # For x,y assume the canvas has already been adjusted for the margins
                    x = i % columns
                    y = (rows - 1) - (i // columns)
                    pageItems[i].x = x * options.dividerWidthReserved
                    pageItems[i].y = y * options.dividerHeightReserved
                    pageItems[i].cropOnTop = (y == rows - 1)
                    pageItems[i].cropOnBottom = (y == 0)
                    pageItems[i].cropOnLeft = (x == 0)
                    pageItems[i].cropOnRight = (x == columns - 1)
                    pageItems[i].rotation = 0
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

            # Front page footer
            if not self.options.no_page_footer and (
                    not self.options.tabs_only and
                    self.options.order != "global"):
                self.drawSetNames(page)

            # Front page
            for item in page:
                # print the dividor
                self.drawDivider(item, isBack=False, horizontalMargin=hMargin, verticalMargin=vMargin)
            self.canvas.showPage()
            if pageNum + 1 == self.options.num_pages:
                break
            if self.options.tabs_only or self.options.text_back == "none" or self.options.wrapper:
                continue  # Don't print the backside of the page

            # back page footer
            if not self.options.no_page_footer and self.options.order != "global":
                self.drawSetNames(page)

            # Back page
            for item in page:
                # print the dividor
                self.drawDivider(item, isBack=True, horizontalMargin=hMargin, verticalMargin=vMargin)
            self.canvas.showPage()
            if pageNum + 1 == self.options.num_pages:
                break
