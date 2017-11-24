import os
import re
import sys

import pkg_resources

from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth


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

    @staticmethod
    def get_image_filepath(fname):
        return pkg_resources.resource_filename('domdiv', os.path.join('images', fname))

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

    def wantCentreTab(self, card):
        return (card.isExpansion() and self.options.centre_expansion_dividers) or self.options.tab_side == "centre"

    def getOutline(self, card):

        dividerWidth = self.options.dividerWidth
        dividerHeight = self.options.dividerHeight
        dividerBaseHeight = self.options.dividerBaseHeight
        tabLabelWidth = self.options.labelWidth
        notch_height = self.options.notch_height  # thumb notch height
        notch_width1 = self.options.notch_width1  # thumb notch width: top away from tab
        notch_width2 = self.options.notch_width2  # thumb notch width: bottom on side of tab

        theTabHeight = dividerHeight - dividerBaseHeight
        theTabWidth = self.options.labelWidth

        if self.wantCentreTab(card):
            side_2_tab = (dividerWidth - theTabWidth) / 2
        else:
            side_2_tab = 0

        nonTabWidth = dividerWidth - tabLabelWidth - side_2_tab

        def DeltaXYtoLines(delta):
            result = []
            started = False
            for x, y in delta:
                if not started:
                    last_x = x
                    last_y = y
                    started = True
                else:
                    result.append((last_x, last_y, last_x + x, last_y + y))
                    last_x = last_x + x
                    last_y = last_y + y
            return result

        self.canvas.saveState()

        if not self.options.wrapper:
            # Normal Card Outline
            #    +                      F+-------------------+E
            #                            |                   |
            #   H+-----------------------+G                 D+-----+C
            #    |                                                 |
            #    |             Generic Divider                     |
            #    |          Tab Centered or to the Side            |
            #    |                                                 |
            #   A+-------------------------------------------------+B
            #             delta x          delta y
            delta = [(0, 0),  # to A
                     (dividerWidth, 0),  # A to B
                     (0, dividerBaseHeight),  # B to C
                     (-side_2_tab, 0),  # C to D
                     (0, theTabHeight),  # D to E
                     (-theTabWidth, 0),  # E to F
                     (0, -theTabHeight),  # F to G
                     (-nonTabWidth, 0),  # G to H
                     (0, -dividerBaseHeight)]  # H to A
            self.canvas.lines(DeltaXYtoLines(delta))

        else:
            # Card Wrapper Outline
            notch_width3 = notch_width1  # thumb notch width: bottom away from tab
            stackHeight = card.getStackHeight(self.options.thickness)
            body_minus_notches = dividerBaseHeight - (2.0 * notch_height)
            tab_2_notch = dividerWidth - theTabWidth - side_2_tab - notch_width1
            if (tab_2_notch < 0):
                tab_2_notch = dividerWidth - theTabWidth - side_2_tab
                notch_width1 = 0
            #    +                            U+-------------------+T   +
            #                                  |                   |
            #    +                            V+. . . . . . . . . .+S   +
            #                                  |                   |
            #    +      X+---------------------+W . . . . . . . . R+----+Q
            #            |                                              |
            #   Z+-------+Y                                             +P
            #    |                                                      |
            #    |                    Generic Wrapper                   |
            #    |                      Normal Side                     |
            #    |                                                      |
            #  AA+-------+BB                                   N+-------+O
            #            |                                      |
            #    +       +CC. . . . . . . . . . . . . . . . . .M+       +
            #            |                                      |
            #    +       +DD. . . . . . . . . . . . . . . . . .L+       +
            #            |                                      |
            #  FF+-------+EE                                   K+-------+J
            #    |                                                      |
            #    |                      Reverse Side                    |
            #    |                       rotated 180                    |
            #    |                                                      |
            #   A+-------+B                                             +I
            #            |                                              |
            #    +      C+---------------------+D                 G+----+H
            #                                  |                   |
            #    +                            E+-------------------+F   +
            #
            #           delta x              delta y
            delta = [(0, theTabHeight + notch_height),  # to A
                     (notch_width1, 0),  # A  to B
                     (0, -notch_height),  # B  to C
                     (tab_2_notch, 0),  # C  to D
                     (0, -theTabHeight),  # D  to E
                     (theTabWidth, 0),  # E  to F
                     (0, theTabHeight),  # F  to G
                     (side_2_tab, 0),  # G  to H
                     (0, notch_height),  # H  to I
                     (0, body_minus_notches),  # I  to J
                     (-notch_width2, 0),  # J  to K
                     (0, notch_height),  # K  to L
                     (0, stackHeight),  # L  to M
                     (0, notch_height),  # M  to N
                     (notch_width2, 0),  # N  to O
                     (0, body_minus_notches),  # O  to P
                     (0, notch_height),  # P  to Q
                     (-side_2_tab, 0),  # Q  to R
                     (0, stackHeight),  # R  to S
                     (0, theTabHeight),  # S  to T
                     (-theTabWidth, 0),  # T  to U
                     (0, -theTabHeight),  # U  to V
                     (0, -stackHeight),  # V  to W
                     (-tab_2_notch, 0),  # W  to X
                     (0, -notch_height),  # X  to Y
                     (-notch_width1, 0),  # Y  to Z
                     (0, -body_minus_notches),  # Z  to AA
                     (notch_width3, 0),  # AA to BB
                     (0, -notch_height),  # BB to CC
                     (0, -stackHeight),  # CC to DD
                     (0, -notch_height),  # DD to EE
                     (-notch_width3, 0),  # EE to FF
                     (0, -body_minus_notches)]  # FF to A

            self.canvas.lines(DeltaXYtoLines(delta))

            self.canvas.setStrokeGray(0.9)
            self.canvas.line(dividerWidth - side_2_tab,
                             dividerHeight + dividerBaseHeight + stackHeight,
                             dividerWidth - side_2_tab - theTabWidth,
                             dividerHeight + dividerBaseHeight + stackHeight)
            self.canvas.line(
                dividerWidth - side_2_tab, dividerHeight + dividerBaseHeight +
                2 * stackHeight, dividerWidth - side_2_tab - theTabWidth,
                dividerHeight + dividerBaseHeight + 2 * stackHeight)
            self.canvas.line(notch_width1, dividerHeight,
                             dividerWidth - notch_width2, dividerHeight)
            self.canvas.line(notch_width1, dividerHeight + stackHeight,
                             dividerWidth - notch_width2,
                             dividerHeight + stackHeight)

        self.canvas.restoreState()

    def draw(self, cards, options):
        self.options = options

        self.registerFonts()
        self.canvas = canvas.Canvas(
            options.outfile,
            pagesize=(options.paperwidth, options.paperheight))
        self.drawDividers(cards)
        self.canvas.save()

    def add_inline_images(self, text, fontsize):
        def replace_image_tag(text,
                              fontsize,
                              tag_pattern,
                              fname_replace,
                              fontsize_multiplier,
                              height_percent,
                              text_fontsize_multiplier=None):
            replace_template = '<img src="{fpath}" width={width} height="{height_percent}%" valign="middle" />'
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

    def drawOutline(self,
                    card,
                    x,
                    y,
                    rightSide,
                    isBack=False):
        # draw outline or cropmarks

        # Don't draw anything if zero (or less) line width
        if self.options.linewidth <= 0.0:
            return

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
            self.getOutline(card)

        elif self.options.cropmarks and not self.options.wrapper:
            cmw = 0.5 * cm

            # Horizontal-line cropmarks
            mirror = cropmarksright and not rightSide or cropmarksleft and rightSide
            if mirror:
                self.canvas.saveState()
                self.canvas.translate(self.options.dividerWidth, 0)
                self.canvas.scale(-1, 1)
            if cropmarksleft or cropmarksright:
                self.canvas.line(-2 * cmw, 0, -cmw, 0)
                self.canvas.line(-2 * cmw, self.options.dividerBaseHeight,
                                 -cmw, self.options.dividerBaseHeight)
                if y > 0:
                    self.canvas.line(-2 * cmw, self.options.dividerHeight,
                                     -cmw, self.options.dividerHeight)
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
                                 rightLine,
                                 self.options.dividerHeight + 2 * cmw)
                self.canvas.line(middleLine, self.options.dividerHeight + cmw,
                                 middleLine,
                                 self.options.dividerHeight + 2 * cmw)
                if cropmarksleft:
                    self.canvas.line(
                        leftLine, self.options.dividerHeight + cmw, leftLine,
                        self.options.dividerHeight + 2 * cmw)

        self.canvas.restoreState()

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

    def drawTab(self, card, rightSide, wrapper="no"):
        # draw tab flap
        self.canvas.saveState()
        if self.wantCentreTab(card):
            translate_x = self.options.dividerWidth / 2 - self.options.labelWidth / 2
            translate_y = self.options.dividerHeight - self.options.labelHeight
        elif not rightSide:
            translate_x = self.options.dividerWidth - self.options.labelWidth
            translate_y = self.options.dividerHeight - self.options.labelHeight
        else:
            translate_x = 0
            translate_y = self.options.dividerHeight - self.options.labelHeight

        if wrapper == "back":
            translate_y = self.options.labelHeight
            if self.wantCentreTab(card):
                translate_x = self.options.dividerWidth / 2 + self.options.labelWidth / 2
            elif not rightSide:
                translate_x = self.options.dividerWidth
            else:
                translate_x = self.options.labelWidth

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
                (self.options.tab_name_align == "centre" or rightSide or
                 not self.options.tab_name_align == "edge"))
            if wrapper == "back" and not self.options.tab_name_align == "centre":
                NotRightEdge = not NotRightEdge
            if NotRightEdge:
                if self.options.tab_name_align == "centre" or self.wantCentreTab(card):
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
            if self.options.notch_width1 > 0:
                usedHeight += self.options.notch_height

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

    def drawDivider(self,
                    card,
                    x,
                    y,
                    isBack=False,
                    divider_text="card",
                    divider_text2="rules"):
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
        self.canvas.translate(self.options.horizontalMargin,
                              self.options.verticalMargin)
        if isBack:
            self.canvas.translate(self.options.back_offset,
                                  self.options.back_offset_height)
        self.canvas.translate(x * self.options.dividerWidthReserved,
                              y * self.options.dividerHeightReserved)

        # actual drawing
        if not self.options.tabs_only:
            self.drawOutline(card, x, y, rightSide, isBack)

        if self.options.wrapper:
            wrap = "front"
        else:
            wrap = "no"
        self.drawTab(card, rightSide, wrapper=wrap)
        if not self.options.tabs_only:
            self.drawText(card, divider_text, wrapper=wrap)
            if self.options.wrapper:
                self.drawTab(card, rightSide, wrapper="back")
                self.drawText(card, divider_text2, wrapper="back")

    def drawSetNames(self, pageCards):
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
            for c in pageCards:
                setTitle = c.cardset
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
        cards = split(cards, self.options.numDividersVertical *
                      self.options.numDividersHorizontal)

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
            if not self.options.no_page_footer and (
                    not self.options.tabs_only and
                    self.options.order != "global"):
                self.drawSetNames(pageCards)
            for i, card in enumerate(pageCards):
                # print card
                x = i % self.options.numDividersHorizontal
                y = i / self.options.numDividersHorizontal
                self.canvas.saveState()
                self.drawDivider(card,
                                 x,
                                 self.options.numDividersVertical - 1 - y,
                                 isBack=False,
                                 divider_text=self.options.text_front,
                                 divider_text2=self.options.text_back)
                self.canvas.restoreState()
                self.odd = not self.odd
            self.canvas.showPage()
            if pageNum + 1 == self.options.num_pages:
                break
            if self.options.tabs_only or self.options.text_back == "none" or self.options.wrapper:
                # Don't print the sheets with the back of the dividers
                continue
            if not self.options.no_page_footer and self.options.order != "global":
                self.drawSetNames(pageCards)
            # start at same oddness
            self.odd = pageStartOdd
            for i, card in enumerate(pageCards):
                # print card
                x = (self.options.numDividersHorizontal - 1 - i
                     ) % self.options.numDividersHorizontal
                y = i / self.options.numDividersHorizontal
                self.canvas.saveState()
                self.drawDivider(card,
                                 x,
                                 self.options.numDividersVertical - 1 - y,
                                 isBack=True,
                                 divider_text=self.options.text_back)
                self.canvas.restoreState()
                self.odd = not self.odd
            self.canvas.showPage()
            if pageNum + 1 == self.options.num_pages:
                break
