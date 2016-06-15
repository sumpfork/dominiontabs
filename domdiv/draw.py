import os
import re
import sys

from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont


def split(l, n):
    i = 0
    while i < len(l) - n:
        yield l[i:i + n]
        i += n
    yield l[i:]


class DividerDrawer(object):

    def __init__(self):
        self.odd = True
        self.canvas = None

    def registerFonts(self):
        try:
            dirn = os.path.join(self.options.data_path, 'fonts')
            self.fontNameRegular = 'MinionPro-Regular'
            pdfmetrics.registerFont(
                TTFont(self.fontNameRegular, os.path.join(dirn, 'MinionPro-Regular.ttf')))
            self.fontNameBold = 'MinionPro-Bold'
            pdfmetrics.registerFont(
                TTFont(self.fontNameBold, os.path.join(dirn, 'MinionPro-Bold.ttf')))
            self.fontNameOblique = 'MinionPro-Oblique'
            pdfmetrics.registerFont(
                TTFont(self.fontNameOblique, os.path.join(dirn, 'MinionPro-It.ttf')))
        except:
            print >>sys.stderr, "Warning, Minion Pro Font ttf file not found! Falling back on Times"
            self.fontNameRegular = 'Times-Roman'
            self.fontNameBold = 'Times-Bold'
            self.fontNameOblique = 'Times-Oblique'

    def draw(self, fname, cards, options):
        self.options = options

        self.registerFonts()

        dividerWidth = options.dividerWidth
        dividerHeight = options.dividerHeight
        dividerBaseHeight = options.dividerBaseHeight
        tabLabelWidth = options.labelWidth

        self.tabOutline = [(0, 0, dividerWidth, 0),
                           (dividerWidth, 0, dividerWidth, dividerHeight),
                           (dividerWidth, dividerHeight,
                            dividerWidth - tabLabelWidth, dividerHeight),
                           (dividerWidth - tabLabelWidth,
                            dividerHeight, dividerWidth - tabLabelWidth,
                            dividerBaseHeight),
                           (dividerWidth - tabLabelWidth,
                            dividerBaseHeight, 0, dividerBaseHeight),
                           (0, dividerBaseHeight, 0, 0)]

        self.expansionTabOutline = [(0, 0, dividerWidth, 0),
                                    (dividerWidth, 0, dividerWidth,
                                     dividerBaseHeight),
                                    (dividerWidth, dividerBaseHeight,
                                     dividerWidth / 2 + tabLabelWidth / 2, dividerBaseHeight),
                                    (dividerWidth / 2 + tabLabelWidth / 2, dividerBaseHeight,
                                     dividerWidth / 2 + tabLabelWidth / 2, dividerHeight),
                                    (dividerWidth / 2 + tabLabelWidth / 2, dividerHeight,
                                     dividerWidth / 2 - tabLabelWidth / 2, dividerHeight),
                                    (dividerWidth / 2 - tabLabelWidth / 2, dividerHeight,
                                     dividerWidth / 2 - tabLabelWidth / 2, dividerBaseHeight),
                                    (dividerWidth / 2 - tabLabelWidth / 2, dividerBaseHeight,
                                     0, dividerBaseHeight),
                                    (0, dividerBaseHeight, 0, 0)]

        self.canvas = canvas.Canvas(
            fname, pagesize=(options.paperwidth, options.paperheight))
        self.drawDividers(cards)
        self.canvas.save()

    def add_inline_images(self, text, fontsize):
        path = os.path.join(self.options.data_path, 'images')
        replace = '<img src='"'%s/coin_small_\\1.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (
            path, fontsize * 1.2)
        text = re.sub('(\d)\s(c|C)oin(s)?', replace, text)
        replace = '<img src='"'%s/coin_small_question.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (
            path, fontsize * 1.2)
        text = re.sub('\?\s(c|C)oin(s)?', replace, text)
        replace = '<img src='"'%s/coin_small_empty.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (
            path, fontsize * 1.2)
        text = re.sub('empty\s(c|C)oin(s)?', replace, text)
        replace = '<img src='"'%s/victory_emblem.png'"' width=%d height='"'120%%'"' valign='"'middle'"'/>' % (
            path, fontsize * 1.5)
        text = re.sub('\<VP\>', replace, text)
        replace = '<img src='"'%s/debt_\\1.png'"' width=%d height='"'105%%'"' valign='"'middle'"'/>&thinsp;' % (
            path, fontsize * 1.2)
        text = re.sub('(\d+)\sDebt', replace, text)
        replace = '<img src='"'%s/debt.png'"' width=%d height='"'105%%'"' valign='"'middle'"'/>&thinsp;' % (
            path, fontsize * 1.2)
        text = re.sub('Debt', replace, text)
        return text

    def drawOutline(self, x, y, rightSide, isBack=False, isExpansionDivider=False):
        # draw outline or cropmarks
        self.canvas.saveState()
        self.canvas.setLineWidth(self.options.linewidth)
        cropmarksright = (x == self.options.numDividersHorizontal - 1)
        cropmarksleft = (x == 0)
        if rightSide:
            self.canvas.translate(self.options.dividerWidth, 0)
            self.canvas.scale(-1, 1)
        if not self.options.cropmarks and not isBack:
            # don't draw outline on back, in case lines don't line up with
            # front
            if isExpansionDivider and self.options.centre_expansion_dividers:
                outline = self.expansionTabOutline
            else:
                outline = self.tabOutline
            self.canvas.lines(outline)
        elif self.options.cropmarks:
            cmw = 0.5 * cm

            # Horizontal-line cropmarks
            mirror = cropmarksright and not rightSide or cropmarksleft and rightSide
            if mirror:
                self.canvas.saveState()
                self.canvas.translate(self.options.dividerWidth, 0)
                self.canvas.scale(-1, 1)
            if cropmarksleft or cropmarksright:
                self.canvas.line(-2 * cmw, 0, -cmw, 0)
                self.canvas.line(-2 * cmw,
                                 self.options.dividerBaseHeight, -cmw, self.options.dividerBaseHeight)
                if y > 0:
                    self.canvas.line(-2 * cmw,
                                     self.options.dividerHeight, -cmw, self.options.dividerHeight)
            if mirror:
                self.canvas.restoreState()

            # Vertical-line cropmarks

            # want to always draw the right-edge and middle-label-edge lines..
            # ...and draw the left-edge if this is the first card on the left

            # ...but we need to take mirroring into account, to know "where"
            # to draw the left / right lines...
            if rightSide:
                leftLine = self.options.dividerWidth
                rightLine = 0
            else:
                leftLine = 0
                rightLine = self.options.dividerWidth
            middleLine = self.options.dividerWidth - self.options.labelWidth

            if y == 0:
                self.canvas.line(rightLine, -2 * cmw, rightLine, -cmw)
                self.canvas.line(middleLine, -2 * cmw, middleLine, -cmw)
                if cropmarksleft:
                    self.canvas.line(leftLine, -2 * cmw, leftLine, -cmw)
            if y == self.options.numDividersVertical - 1:
                self.canvas.line(rightLine, self.options.dividerHeight + cmw,
                                 rightLine, self.options.dividerHeight + 2 * cmw)
                self.canvas.line(middleLine, self.options.dividerHeight + cmw,
                                 middleLine, self.options.dividerHeight + 2 * cmw)
                if cropmarksleft:
                    self.canvas.line(leftLine, self.options.dividerHeight + cmw,
                                     leftLine, self.options.dividerHeight + 2 * cmw)

        self.canvas.restoreState()

    def drawCost(self, card, x, y, costOffset=-1):
        # base width is 16 (for image) + 2 (1 pt border on each side)
        width = 18

        costHeight = y + costOffset
        coinHeight = costHeight - 5
        potHeight = y - 3
        potSize = 11

        if card.debtcost:
            self.canvas.drawImage(os.path.join(self.options.data_path, 'images', 'debt.png'),
                                  x, coinHeight, 16, 16, preserveAspectRatio=True,
                                  mask=[255, 255, 255, 255, 255, 255])
            cost = str(card.debtcost)
            if card.cost != "" and int(card.cost) > 0:
                self.canvas.drawImage(os.path.join(self.options.data_path, 'images', 'coin_small.png'), x + 17,
                                      coinHeight, 16, 16, preserveAspectRatio=True,
                                      mask=[255, 255, 255, 255, 255, 255])
                self.canvas.setFont(self.fontNameBold, 12)
                self.canvas.drawCentredString(x + 8 + 17, costHeight, str(card.cost))
                self.canvas.setFillColorRGB(0, 0, 0)
                width += 16
            self.canvas.setFillColorRGB(1, 1, 1)
        else:
            self.canvas.drawImage(os.path.join(self.options.data_path, 'images', 'coin_small.png'),
                                  x, coinHeight, 16, 16, preserveAspectRatio=True, mask='auto')
            cost = str(card.cost)
        if card.potcost:
            self.canvas.drawImage(os.path.join(self.options.data_path, 'images', 'potion.png'), x + 17,
                                  potHeight, potSize, potSize, preserveAspectRatio=True,
                                  mask=[255, 255, 255, 255, 255, 255])
            width += potSize

        self.canvas.setFont(self.fontNameBold, 12)
        self.canvas.drawCentredString(x + 8, costHeight, cost)
        self.canvas.setFillColorRGB(0, 0, 0)
        return width

    def drawSetIcon(self, setImage, x, y):
        # set image
        self.canvas.drawImage(
            os.path.join(self.options.data_path, 'images', setImage), x, y, 14, 12, mask='auto')

    def nameWidth(self, name, fontSize):
        w = 0
        name_parts = name.split()
        for i, part in enumerate(name_parts):
            if i != 0:
                w += pdfmetrics.stringWidth(' ', self.fontNameRegular, fontSize)
            w += pdfmetrics.stringWidth(part[0], self.fontNameRegular, fontSize)
            w += pdfmetrics.stringWidth(part[1:],
                                        self.fontNameRegular, fontSize - 2)
        return w

    def drawTab(self, card, rightSide):
        # draw tab flap
        self.canvas.saveState()
        if card.isExpansion() and self.options.centre_expansion_dividers:
            self.canvas.translate(self.options.dividerWidth / 2 - self.options.labelWidth / 2,
                                  self.options.dividerHeight - self.options.labelHeight)
        elif not rightSide:
            self.canvas.translate(self.options.dividerWidth - self.options.labelWidth,
                                  self.options.dividerHeight - self.options.labelHeight)
        else:
            self.canvas.translate(0, self.options.dividerHeight - self.options.labelHeight)

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
            self.canvas.drawImage(os.path.join(self.options.data_path, 'images', img), 1, 0,
                                  self.options.labelWidth -
                                  2, self.options.labelHeight - 1,
                                  preserveAspectRatio=False, anchor='n', mask='auto')

        # draw cost
        if not card.isExpansion() and not card.isBlank() and not card.isLandmark():
            if 'tab' in self.options.cost:
                textInset = 4
                textInset += self.drawCost(card, textInset, textHeight,
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
            self.canvas.setFont(self.fontNameOblique, 8)
            if setText is None:
                setText = ""

            self.canvas.drawCentredString(self.options.labelWidth - 10, textHeight + 2, setText)
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
            # print 'decreasing font size for tab of',name,'now',fontSize
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
            if (not self.options.tab_name_align == "right") and (self.options.tab_name_align == "centre" or
                                                                 rightSide or
                                                                 not self.options.tab_name_align == "edge"):
                if self.options.tab_name_align == "centre":
                    w = self.options.labelWidth / 2 - self.nameWidth(line, fontSize) / 2
                else:
                    w = textInset

                def drawWordPiece(text, fontSize):
                    self.canvas.setFont(self.fontNameRegular, fontSize)
                    if text != ' ':
                        self.canvas.drawString(w, h, text)
                    return pdfmetrics.stringWidth(text, self.fontNameRegular, fontSize)
                for i, word in enumerate(words):
                    if i != 0:
                        w += drawWordPiece(' ', fontSize)
                    w += drawWordPiece(word[0], fontSize)
                    w += drawWordPiece(word[1:], fontSize - 2)
            else:
                # align text to the right if tab is on right side, to make
                # tabs easier to read when grouped together extra 3pt is for
                # space between text + set symbol

                w = self.options.labelWidth - textInsetRight - 3
                words.reverse()

                def drawWordPiece(text, fontSize):
                    self.canvas.setFont(self.fontNameRegular, fontSize)
                    if text != ' ':
                        self.canvas.drawRightString(w, h, text)
                    return -pdfmetrics.stringWidth(text, self.fontNameRegular, fontSize)
                for i, word in enumerate(words):
                    w += drawWordPiece(word[1:], fontSize - 2)
                    w += drawWordPiece(word[0], fontSize)
                    if i != len(words) - 1:
                        w += drawWordPiece(' ', fontSize)
        self.canvas.restoreState()

    def drawText(self, card, divider_text="card"):
        usedHeight = 0
        totalHeight = self.options.dividerHeight - self.options.labelHeight

        drewTopIcon = False
        if 'body-top' in self.options.cost and not card.isExpansion():
            self.drawCost(card, cm / 4.0, totalHeight - 0.5 * cm)
            drewTopIcon = True

        if 'body-top' in self.options.set_icon and not card.isExpansion():
            setImage = card.setImage()
            if setImage:
                self.drawSetIcon(setImage, self.options.dividerWidth - 16,
                                 totalHeight - 0.5 * cm - 3)
                drewTopIcon = True
        if drewTopIcon:
            usedHeight += 15

        # Figure out what text is to be printed on this divider
        if divider_text == "blank":
            # blank divider, no need to go on
            return
        elif divider_text == "rules":
            # Add the extra rules text to the divider
            if card.extra:
                descriptions = (card.extra,)
            else:
                # Asked for rules and they don't exist, so don't print anything
                return
        elif divider_text == "card":
            # Add the card text to the divider
            descriptions = re.split("\n", card.description)
        else:
            # Don't know what was asked, so don't print anything
            return

        s = getSampleStyleSheet()['BodyText']
        s.fontName = "Times-Roman"
        s.alignment = TA_JUSTIFY

        textHorizontalMargin = .5 * cm
        textVerticalMargin = .3 * cm
        textBoxWidth = self.options.dividerWidth - 2 * textHorizontalMargin
        textBoxHeight = totalHeight - usedHeight - 2 * textVerticalMargin
        spacerHeight = 0.2 * cm
        minSpacerHeight = 0.05 * cm

        while True:
            paragraphs = []
            # this accounts for the spacers we insert between paragraphs
            h = (len(descriptions) - 1) * spacerHeight
            for d in descriptions:
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

    def drawDivider(self, card, x, y, isBack=False, divider_text="card"):
        # figure out whether the tab should go on the right side or not
        if self.options.tab_side == "right":
            rightSide = isBack
        elif self.options.tab_side in ["left", "full"]:
            rightSide = not isBack
        else:
            # alternate the cards
            if not isBack:
                rightSide = not self.odd
            else:
                rightSide = self.odd

        # apply the transforms to get us to the corner of the current card
        self.canvas.resetTransforms()
        self.canvas.translate(self.options.horizontalMargin, self.options.verticalMargin)
        if isBack:
            self.canvas.translate(self.options.back_offset, self.options.back_offset_height)
        self.canvas.translate(x * self.options.dividerWidthReserved,
                              y * self.options.dividerHeightReserved)

        # actual drawing
        if not self.options.tabs_only:
            self.drawOutline(
                x, y, rightSide, isBack, card.getType().getTypeNames() == ('Expansion',))
        self.drawTab(card, rightSide)
        if not self.options.tabs_only:
            self.drawText(card, divider_text)

    def drawSetNames(self, pageCards):
        # print sets for this page
        self.canvas.saveState()

        try:
            # calculate the text height, font size, and orientation
            maxFontsize = 12
            minFontsize = 6
            fontname = self.fontNameRegular
            font = pdfmetrics.getFont(fontname)
            fontHeightRelative = (font.face.ascent + abs(font.face.descent)) / 1000.0

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
                availableMargin = layout[
                    'totalMarginHeight'] - layout['minMarginHeight']
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

            sets = []
            for c in pageCards:
                setTitle = c.cardset.title()
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

    def drawDividers(self, cards):
        # split into pages
        cards = split(cards, self.options.numDividersVertical * self.options.numDividersHorizontal)

        # Starting with tabs on the left or the right?
        if self.options.tab_side in ["right-alternate", "right"]:
            self.odd = True
        else:
            # left-alternate, left, full
            self.odd = False

        for pageNum, pageCards in enumerate(cards):
            # remember whether we start with odd or even divider for tab
            # location
            pageStartOdd = self.odd
            if not self.options.no_page_footer and (not self.options.tabs_only and self.options.order != "global"):
                self.drawSetNames(pageCards)
            for i, card in enumerate(pageCards):
                # print card
                x = i % self.options.numDividersHorizontal
                y = i / self.options.numDividersHorizontal
                self.canvas.saveState()
                self.drawDivider(card, x, self.options.numDividersVertical - 1 - y, isBack=False, divider_text=self.options.text_front)
                self.canvas.restoreState()
                self.odd = not self.odd
            self.canvas.showPage()
            if pageNum + 1 == self.options.num_pages:
                break
            if self.options.tabs_only or self.options.text_back == "none":
                # Don't print the sheets with the back of the dividers
                continue
            if not self.options.no_page_footer and self.options.order != "global":
                self.drawSetNames(pageCards)
            # start at same oddness
            self.odd = pageStartOdd
            for i, card in enumerate(pageCards):
                # print card
                x = (self.options.numDividersHorizontal - 1 - i) % self.options.numDividersHorizontal
                y = i / self.options.numDividersHorizontal
                self.canvas.saveState()
                self.drawDivider(card, x, self.options.numDividersVertical - 1 - y, isBack=True, divider_text=self.options.text_back)
                self.canvas.restoreState()
                self.odd = not self.odd
            self.canvas.showPage()
            if pageNum + 1 == self.options.num_pages:
                break
