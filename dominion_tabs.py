#!python
import re
from optparse import OptionParser
import os.path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER,A4
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.enums import TA_JUSTIFY

def split(l,n):
    i = 0
    while i < len(l) - n:
        yield l[i:i+n]
        i += n
    yield l[i:]

class Card:
    def __init__(self,name,cardset,types,cost,description,potcost=0):
        self.name = name.strip()
        self.cardset = cardset.strip()
        self.types = types
        self.cost = cost
        self.potcost = potcost
        self.description = description
        self.extra = ""

    def getType(self):
        return DominionTabs.cardTypes[self.types]

    def __repr__(self):
        return '"' + self.name + '"'

    def toString(self):
        return self.name + ' ' + self.cardset + ' ' + '-'.join(self.types) + ' ' + `self.cost` + ' ' + self.description + ' ' + self.extra

    def isExpansion(self):
        return self.getType().getTypeNames() == ('Expansion',)

    def setImage(self):
        setImage = DominionTabs.setImages.get(self.cardset, None)
        if not setImage:
            setImage = DominionTabs.promoImages.get(self.name.lower(), None)
        if setImage == None and self.cardset != 'base' and not self.isExpansion():
            print 'warning, no set image for set "%s" card "%s"' % (self.cardset, self.name)
            DominionTabs.setImages[self.cardset] = 0
            DominionTabs.promoImages[self.name.lower()] = 0
        return setImage


class CardType:
    def __init__(self, typeNames, tabImageFile, tabTextHeightOffset=0, tabCostHeightOffset=-1):
        self.typeNames = typeNames
        self.tabImageFile = tabImageFile
        self.tabTextHeightOffset = tabTextHeightOffset
        self.tabCostHeightOffset = tabCostHeightOffset

    def getTypeNames(self):
        return self.typeNames

    def getTabImageFile(self):
        return self.tabImageFile

    def getNoCoinTabImageFile(self):
        return ''.join(os.path.splitext(self.tabImageFile)[0] + '_nc' + os.path.splitext(self.tabImageFile)[1])

    def getTabTextHeightOffset(self):
        return self.tabTextHeightOffset

    def getTabCostHeightOffset(self):
        return self.tabCostHeightOffset

class DominionTabs:
    cardTypes = [
        CardType(('Action',), 'action.png'),
        CardType(('Action','Attack'), 'action.png'),
        CardType(('Action','Attack','Prize'), 'action.png'),
        CardType(('Action','Reaction'), 'reaction.png'),
        CardType(('Action','Victory'), 'action-victory.png'),
        CardType(('Action','Duration'), 'duration.png'),
        CardType(('Action','Looter'), 'action.png'),
        CardType(('Action','Prize'), 'action.png'),
        CardType(('Action','Ruins'), 'ruins.png', 0, 1),
        CardType(('Action','Shelter'), 'shelter.png', 0, 1),
        CardType(('Action','Attack','Looter'), 'action.png'),
        CardType(('Reaction',), 'reaction.png'),
        CardType(('Reaction','Shelter'), 'shelter.png', 0, 1),
        CardType(('Treasure',), 'treasure.png',3,0),
        CardType(('Treasure','Victory'), 'treasure-victory.png'),
        CardType(('Treasure','Prize'), 'treasure.png',3,0),
        CardType(('Treasure','Reaction'), 'treasure-reaction.png', 0, 1),
        CardType(('Victory',), 'victory.png'),
        CardType(('Victory','Reaction'), 'victory-reaction.png', 0, 1),
        CardType(('Victory','Shelter'), 'shelter.png', 0, 1),
        CardType(('Curse',), 'curse.png',3),
        CardType(('Expansion',), 'expansion.png',4)
        ]

    cardTypes = dict(((c.getTypeNames(),c) for c in cardTypes))

    setImages = {
        'dominion' : 'base_set.png',
        'intrigue' : 'intrigue_set.png',
        'seaside' : 'seaside_set.png',
        'prosperity' : 'prosperity_set.png',
        'alchemy' : 'alchemy_set.png',
        'cornucopia' : 'cornucopia_set.png',
        'hinterlands' : 'hinterlands_set.png',
        'dark ages' : 'dark_ages_set.png',
        'dark ages extras' : 'dark_ages_set.png',
        'guilds' : 'guilds_set.png'
        }
    promoImages = {
        'walled village' : 'walled_village_set.png',
        'stash' : 'stash_set.png',
        'governor' : 'governor_set.png',
        'black market' : 'black_market_set.png',
        'envoy' : 'envoy_set.png'
        }

    def __init__(self):
        self.filedir = os.path.dirname(__file__)

    def add_inline_images(self, text, fontsize):
        path = os.path.join(self.filedir,'images')
        replace = '<img src='"'%s/coin_small_\\1.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (path,fontsize*1.2)
        text = re.sub('(\d)\s(c|C)oin(s)?', replace,text)
        replace = '<img src='"'%s/coin_small_question.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (path,fontsize*1.2)
        text = re.sub('\?\s(c|C)oin(s)?', replace,text)
        replace = '<img src='"'%s/victory_emblem.png'"' width=%d height='"'120%%'"' valign='"'middle'"'/>' % (path,fontsize*1.5)
        text = re.sub('\<VP\>', replace,text)
        return text

    def drawOutline(self, x, y, rightSide, isBack=False, isExpansionDivider=False):
        #draw outline or cropmarks
        self.canvas.saveState()
        self.canvas.setLineWidth(self.options.linewidth)
        cropmarksright = (x == self.numTabsHorizontal-1)
        cropmarksleft = (x == 0)
        if rightSide:
            self.canvas.translate(self.tabWidth,0)
            self.canvas.scale(-1,1)
        if not self.options.cropmarks and not isBack:
            #don't draw outline on back, in case lines don't line up with front
            if isExpansionDivider and self.options.centre_expansion_dividers:
                outline = self.expansionTabOutline
            else:
                outline = self.tabOutline
            self.canvas.lines(outline)
        elif self.options.cropmarks:
            cmw = 0.5*cm

            # Horizontal-line cropmarks
            mirror = cropmarksright and not rightSide or cropmarksleft and rightSide
            if mirror:
                self.canvas.saveState()
                self.canvas.translate(self.tabWidth,0)
                self.canvas.scale(-1,1)
            if cropmarksleft or cropmarksright:
                self.canvas.line(-2*cmw,0,-cmw,0)
                self.canvas.line(-2*cmw,self.tabBaseHeight,-cmw,self.tabBaseHeight)
                if y > 0:
                    self.canvas.line(-2*cmw,self.tabHeight,-cmw,self.tabHeight)
            if mirror:
                self.canvas.restoreState()

            # Vertical-line cropmarks

            # want to always draw the right-edge and middle-label-edge lines..
            # ...and draw the left-edge if this is the first card on the left

            # ...but we need to take mirroring into account, to know "where"
            # to draw the left / right lines...
            if rightSide:
                leftLine = self.tabWidth
                rightLine = 0
            else:
                leftLine = 0
                rightLine = self.tabWidth
            middleLine = self.tabWidth-self.tabLabelWidth

            if y == 0:
                self.canvas.line(rightLine,-2*cmw,rightLine,-cmw)
                self.canvas.line(middleLine,-2*cmw,middleLine,-cmw)
                if cropmarksleft:
                    self.canvas.line(leftLine,-2*cmw,leftLine,-cmw)
            if y == self.numTabsVertical-1:
                self.canvas.line(rightLine,self.tabHeight+cmw,
                                 rightLine,self.tabHeight+2*cmw)
                self.canvas.line(middleLine, self.tabHeight+cmw,
                                 middleLine, self.tabHeight+2*cmw)
                if cropmarksleft:
                    self.canvas.line(leftLine,self.tabHeight+cmw,
                                     leftLine,self.tabHeight+2*cmw)

        self.canvas.restoreState()

    def drawCost(self, card, x, y, costOffset=-1):
        # base width is 16 (for image) + 2 (1 pt border on each side)
        width = 18

        costHeight = y + costOffset
        coinHeight = costHeight - 5
        potHeight = y - 3
        potSize = 11

        self.canvas.drawImage(os.path.join(self.filedir,'images','coin_small.png'),x,coinHeight,16,16,preserveAspectRatio=True,mask='auto')
        if card.potcost:
            self.canvas.drawImage(os.path.join(self.filedir,'images','potion.png'),x+17,potHeight,potSize,potSize,preserveAspectRatio=True,mask=[255,255,255,255,255,255])
            width += potSize

        self.canvas.setFont('MinionPro-Bold',12)
        cost = str(card.cost)
        if 'Prize' in card.types:
            cost += '*'
        self.canvas.drawCentredString(x+8,costHeight,cost)
        return width

    def drawSetIcon(self, setImage, x, y):
        # set image
        self.canvas.drawImage(os.path.join(self.filedir,'images',setImage), x, y, 14, 12, mask='auto')

    @classmethod
    def nameWidth(self, name, fontSize):
        w = 0
        name_parts = name.split()
        for i, part in enumerate(name_parts):
            if i != 0:
                w += pdfmetrics.stringWidth(' ','MinionPro-Regular',fontSize)
            w += pdfmetrics.stringWidth(part[0],'MinionPro-Regular',fontSize)
            w += pdfmetrics.stringWidth(part[1:],'MinionPro-Regular',fontSize-2)
        return w

    def drawTab(self, card, rightSide):
        #draw tab flap
        self.canvas.saveState()
        if card.isExpansion() and self.options.centre_expansion_dividers:
             self.canvas.translate(self.tabWidth/2-self.tabLabelWidth/2,
                                   self.tabHeight-self.tabLabelHeight)
        elif not rightSide:
            self.canvas.translate(self.tabWidth-self.tabLabelWidth,
                        self.tabHeight-self.tabLabelHeight)
        else:
            self.canvas.translate(0,self.tabHeight-self.tabLabelHeight)

        textWidth = self.tabLabelWidth - 6 # allow for 3 pt border on each side
        textHeight = self.tabLabelHeight/2-7+card.getType().getTabTextHeightOffset()

        # draw banner
        self.canvas.drawImage(os.path.join(self.filedir,'images',card.getType().getNoCoinTabImageFile()),1,0,
            self.tabLabelWidth-2,self.tabLabelHeight-1,
            preserveAspectRatio=False,anchor='n',mask='auto')

        # draw cost
        if not card.isExpansion():
            if 'tab' in self.options.cost:
                textInset = 4
                textInset += self.drawCost(card, textInset, textHeight,
                                           card.getType().getTabCostHeightOffset())
            else:
                textInset = 6
        else:
            textInset = 13

        # draw set image
        setImage = card.setImage()
        if setImage and 'tab' in self.options.set_icon:
            setImageHeight = 3 + card.getType().getTabTextHeightOffset()
            self.drawSetIcon(setImage, self.tabLabelWidth-20,
                             setImageHeight)
            textInsetRight = 20
        else:
            # always need to offset from right edge, to make sure it stays on
            # banner
            textInsetRight = 6

        # draw name
        fontSize = 12
        name = card.name.upper()

        textWidth -= textInset
        textWidth -= textInsetRight

        width = self.nameWidth(name, fontSize)
        while width > textWidth and fontSize > 8:
            fontSize -= .01
            #print 'decreasing font size for tab of',name,'now',fontSize
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
        #if tooLong:
        #    print name

        for linenum, line in enumerate(name_lines):
            h = textHeight
            if tooLong and len(name_lines) > 1:
                if linenum == 0:
                    h += h/2
                else:
                    h -= h/2

            words = line.split()
            if rightSide or not self.options.edge_align_name:
                w = textInset
                def drawWordPiece(text, fontSize):
                    self.canvas.setFont('MinionPro-Regular',fontSize)
                    if text != ' ':
                        self.canvas.drawString(w,h,text)
                    return pdfmetrics.stringWidth(text,'MinionPro-Regular',fontSize)
                for i, word in enumerate(words):
                    if i != 0:
                        w += drawWordPiece(' ', fontSize)
                    w += drawWordPiece(word[0], fontSize)
                    w += drawWordPiece(word[1:], fontSize-2)
            else:
                # align text to the right if tab is on right side, to make
                # tabs easier to read when grouped together extra 3pt is for
                # space between text + set symbol

                w = self.tabLabelWidth - textInsetRight - 3
                words.reverse()
                def drawWordPiece(text, fontSize):
                    self.canvas.setFont('MinionPro-Regular',fontSize)
                    if text != ' ':
                        self.canvas.drawRightString(w,h,text)
                    return -pdfmetrics.stringWidth(text,'MinionPro-Regular',fontSize)
                for i, word in enumerate(words):
                    w += drawWordPiece(word[1:], fontSize-2)
                    w += drawWordPiece(word[0], fontSize)
                    if i != len(words) - 1:
                        w += drawWordPiece(' ', fontSize)
        self.canvas.restoreState()

    def drawText(self, card, useExtra=False):
        usedHeight = 0
        totalHeight = self.tabHeight - self.tabLabelHeight

        drewTopIcon = False
        if 'body-top' in self.options.cost and not card.isExpansion():
            self.drawCost(card, cm/4.0, totalHeight - 0.5*cm)
            drewTopIcon = True

        if 'body-top' in self.options.set_icon and not card.isExpansion():
            setImage = card.setImage()
            if setImage:
                self.drawSetIcon(setImage, self.tabWidth-16,
                                 totalHeight-0.5*cm-3)
                drewTopIcon = True
        if drewTopIcon:
            usedHeight += 15

        #draw text
        if useExtra and card.extra:
            descriptions = (card.extra,)
        else:
                descriptions = re.split("\n",card.description)

        s = getSampleStyleSheet()['BodyText']
        s.fontName = "Times-Roman"
        s.alignment = TA_JUSTIFY

        textHorizontalMargin = .5*cm
        textVerticalMargin = .3*cm
        textBoxWidth = self.tabWidth - 2*textHorizontalMargin
        textBoxHeight = totalHeight - usedHeight - 2*textVerticalMargin
        spacerHeight = 0.2*cm
        minSpacerHeight = 0.05*cm

        while True:
            paragraphs = []
            # this accounts for the spacers we insert between paragraphs
            h = (len(descriptions) - 1) * spacerHeight
            for d in descriptions:
                dmod = self.add_inline_images(d,s.fontSize)
                p = Paragraph(dmod,s)
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

    def drawDivider(self,card,x,y,useExtra=False):
        #figure out whether the tab should go on the right side or not
        if not self.options.sameside:
            rightSide = x%2 == 1
        else:
            rightSide = useExtra
        #apply the transforms to get us to the corner of the current card
        self.canvas.resetTransforms()
        self.canvas.translate(self.horizontalMargin,self.verticalMargin)
        if useExtra:
            self.canvas.translate(self.options.back_offset,0)
        self.canvas.translate(x*self.totalTabWidth,y*self.totalTabHeight)

        #actual drawing
        if not self.options.tabs_only:
            self.drawOutline(x, y, rightSide, useExtra,card.getType().getTypeNames() == ('Expansion',))
        self.drawTab(card, rightSide)
        if not self.options.tabs_only:
            self.drawText(card, useExtra)

    def read_card_extras(self,fname,cards):
        f = open(fname)
        cardName = re.compile("^:::(?P<name>[ \w\-/']*)")
        extras = {}
        currentCard = ""
        extra = ""
        for line in f:
            m = cardName.match(line)
            if m:
                if currentCard:
                    #print 'found',currentCard
                    #print extra
                    #print '------------------'
                    extras[currentCard] = extra
                currentCard = m.groupdict()["name"]
                extra = ""
                if not self.options.expansions and currentCard and (currentCard not in (c.name for c in cards)):
                    print currentCard + ' has extra description, but is not in cards'
            else:
                extra += ' ' + line.strip()
        if currentCard and extra:
            extras[currentCard] = extra.strip()
        for c in cards:
            if not c.name in extras:
                print c.name + ' missing from extras'
            else:
                c.extra = extras[c.name]
                #print c.name + ' ::: ' + extra

    baseactionRE = re.compile("^\s*(\+\d+\s+\w+)(?:[,.;])")

    def add_definition_line(self,card,line):
        # Unfortunately, the way things are specified in the old card spec
        # format is somewhat haphazard. In particular:
        #   1) Sometimes "basic actions", which would be separated on the
        #      actual card text by separate lines, are instead only separated
        #      by punctuation ('.', ',', or ';')
        #      [Example: Intrigue - Courtyard]
        #   2) When there is an actual horizontal line drawn on the card, this
        #      can be represented using either '____'  or '-----'
        #   3) There are sometimes random blank lines

        # To solve:

        # 1)
        #try to figure out if this a 'basic action' like +X Cards or +Y Actions
        descriptions = [card.description]
        while True:
            m = self.baseactionRE.match(line)
            if not m:
                break
            descriptions.append(m.group(1))
            line = line[m.end():]

        # 2) Standardize on '____' as the format for a divider line
        line = line.strip()
        if not line.strip('-'):
            line = line.replace('-', '_')

        # 3) get rid of blank lines
        descriptions.append(line)
        descriptions = [x.strip() for x in descriptions]
        descriptions = [x for x in descriptions if x]

        card.description = '\n'.join(descriptions)

    def read_card_defs(self,fname,fileobject=None):
        cards = []
        f = open(fname)
        carddef = re.compile("^\d+\t+(?P<name>[\w\-'/ ]+)\t+(?P<set>[\w ]+)\t+(?P<type>[-\w ]+)\t+\$(?P<cost>\d+)( (?P<potioncost>\d)+P)?\t+(?P<description>.*)")
        currentCard = None
        for line in f:
            line = line.strip()
            m = carddef.match(line)
            if m:
                if m.groupdict()["potioncost"]:
                    potcost = int(m.groupdict()["potioncost"])
                else:
                    potcost = 0
                currentCard = Card(m.groupdict()["name"].strip(),
                                   m.groupdict()["set"].lower().strip(),
                                   tuple([t.strip() for t in m.groupdict()["type"].split("-")]),
                                   int(m.groupdict()["cost"]),
                                   '',
                                   potcost)
                self.add_definition_line(currentCard,m.groupdict()["description"])
                cards.append(currentCard)
            elif line:
                assert currentCard
                self.add_definition_line(currentCard,line)
            #print currentCard
            #print '----'
        return cards

    def drawSetNames(self, pageCards):
        #print sets for this page
        self.canvas.saveState()

        try:
            # calculate the text height, font size, and orientation
            maxFontsize = 12
            minFontsize = 6
            fontname = 'MinionPro-Regular'
            font = pdfmetrics.getFont(fontname)
            fontHeightRelative = (font.face.ascent + font.face.descent) / 1000

            canFit = False

            layouts = [{'rotation': 0,
                        'minMarginHeight': self.minVerticalMargin,
                        'totalMarginHeight': self.verticalMargin,
                        'width': self.paperwidth},
                       {'rotation': 90,
                        'minMarginHeight': self.minHorizontalMargin,
                        'totalMarginHeight': self.horizontalMargin,
                        'width': self.paperheight}]

            for layout in layouts:
                availableMargin = layout['totalMarginHeight'] - layout['minMarginHeight']
                fontsize = availableMargin / fontHeightRelative
                fontsize = min(maxFontsize, fontsize)
                if fontsize >= minFontsize:
                    canFit = True
                    break

            if not canFit:
                import warnings
                warnings.warn("Not enough space to display set names")
                return

            self.canvas.setFont(fontname,fontsize)

            sets = []
            for c in pageCards:
                setTitle = c.cardset.title()
                if setTitle not in sets:
                    sets.append(setTitle)

                xPos = layout['width'] / 2
                yPos = layout['minMarginHeight'] + availableMargin / 2

                if layout['rotation']:
                    self.canvas.rotate(layout['rotation'])
                    yPos = -yPos

            self.canvas.drawCentredString(xPos,yPos,'/'.join(sets))
        finally:
            self.canvas.restoreState()

    def drawDividers(self,cards):
        cards = split(cards,self.numTabsVertical*self.numTabsHorizontal)
        for pageCards in cards:
            if self.options.order != "global":
                self.drawSetNames(pageCards)
            for i,card in enumerate(pageCards):
                #print card
                x = i % self.numTabsHorizontal
                y = i / self.numTabsHorizontal
                self.canvas.saveState()
                self.drawDivider(card,x,self.numTabsVertical-1-y)
                self.canvas.restoreState()
            self.canvas.showPage()
            if self.options.order != "global":
                self.drawSetNames(pageCards)
            for i,card in enumerate(pageCards):
                #print card
                x = (self.numTabsHorizontal-1-i) % self.numTabsHorizontal
                y = i / self.numTabsHorizontal
                self.canvas.saveState()
                self.drawDivider(card,x,self.numTabsVertical-1-y,useExtra=True)
                self.canvas.restoreState()
            self.canvas.showPage()



    LOCATION_CHOICES = ["tab", "body-top", "hide"]

    @classmethod
    def parse_opts(cls, argstring):
        parser = OptionParser()
        parser.add_option("--back_offset",type="float",dest="back_offset",default=0,
                          help="Points to offset the back page to the right; needed for some printers")
        parser.add_option("--orientation",type="choice",choices=["horizontal","vertical"],dest="orientation",default="horizontal",
                          help="horizontal or vertical, default:horizontal")
        parser.add_option("--sleeved",action="store_true",dest="sleeved",help="use --size=sleeved instead")
        parser.add_option("--size",type="string",dest="size",default='normal',
                          help="'<%f>x<%f>' (size in cm), or 'normal' = '9.1x5.9', or 'sleeved' = '9.4x6.15'")
        parser.add_option("--minmargin",type="string",dest="minmargin",default="1x1",
                          help="'<%f>x<%f>' (size in cm, left/right, top/bottom), default: 1x1")
        parser.add_option("--papersize",type="string",dest="papersize",default=None,
                          help="'<%f>x<%f>' (size in cm), or 'A4', or 'LETTER'")
        parser.add_option("--tabwidth",type="float",default=4,
                          help="width in cm of stick-up tab (ignored if tabs-only used)")
        parser.add_option("--samesidelabels",action="store_true",dest="sameside",
                          help="force all label tabs to be on the same side"
                          " (this will be forced on if there is an uneven"
                          " number of cards horizontally across the page)")
        parser.add_option("--edge_align_name",action="store_true",
                          help="align the card name to the outside edge of the"
                          " tab, so that when using tabs on alternating sides,"
                          " the name is less likely to be hidden by the tab"
                          " in front; ignored if samesidelabels is on")
        parser.add_option("--cost",action="append",type="choice",
                          choices=cls.LOCATION_CHOICES,  default=[],
                          help="where to display the card cost; may be set to"
                          " 'hide' to indicate it should not be displayed, or"
                          " given multiple times to show it in multiple"
                          " places; valid values are: %s; defaults to 'tab'"
                          % ", ".join("'%s'" % x for x in cls.LOCATION_CHOICES))
        parser.add_option("--set_icon",action="append",type="choice",
                          choices=cls.LOCATION_CHOICES,  default=[],
                          help="where to display the set icon; may be set to"
                          " 'hide' to indicate it should not be displayed, or"
                          " given multiple times to show it in multiple"
                          " places; valid values are: %s; defaults to 'tab'"
                          % ", ".join("'%s'" % x for x in cls.LOCATION_CHOICES))
        parser.add_option("--expansions",action="append",type="string",
                          help="subset of dominion expansions to produce tabs for")
        parser.add_option("--cropmarks",action="store_true",dest="cropmarks",
                          help="print crop marks on both sides, rather than tab outlines on one")
        parser.add_option("--linewidth",type="float",default=.1,
                          help="width of lines for card outlines/crop marks")
        parser.add_option("--read_yaml", action="store_true",dest="read_yaml",
                          help="read yaml version of card definitions and extras")
        parser.add_option("--write_yaml", action="store_true",dest="write_yaml",
                          help="write yaml version of card definitions and extras")
        parser.add_option("--tabs-only", action="store_true", dest="tabs_only",
                          help="draw only tabs to be printed on labels, no divider outlines")
        parser.add_option("--order", type="choice", choices=["expansion","global"], dest="order",
                          help="sort order for the cards, whether by expansion or globally alphabetical")
        parser.add_option("--expansion_dividers", action="store_true", dest="expansion_dividers",
                          help="add dividers describing each expansion set")
        parser.add_option("--base_cards_with_expansion", action="store_true",
                          help='print the base cards as part of the expansion; ie, a divider for "Silver"'
                          'will be printed as both a "Dominion" card and as an "Intrigue" card; if this'
                          'option is not given, all base cards are placed in their own "Base" expansion')
        parser.add_option("--centre_expansion_dividers", action="store_true", dest="centre_expansion_dividers",
                          help='centre the tabs on expansion dividers')

        options, args = parser.parse_args(argstring)
        if not options.cost:
            options.cost = ['tab']
        if not options.set_icon:
            options.set_icon = ['tab']
        return options, args

    def main(self,argstring):
        options,args = DominionTabs.parse_opts(argstring)
        fname = None
        if args:
            fname = args[0]
        return self.generate(options,fname)

    def parseDimensions(self, dimensionsStr):
        x, y = dimensionsStr.upper().split('X', 1)
        return (float (x) * cm, float (y) * cm)

    def generate(self,options,f):
        self.options = options
        size = self.options.size.upper()
        if size == 'SLEEVED' or self.options.sleeved:
            dominionCardWidth, dominionCardHeight = (9.4*cm, 6.15*cm)
            print 'Using sleeved card size, %.2fcm x %.2fcm' % (dominionCardWidth/cm,dominionCardHeight/cm)
        elif size in ['NORMAL','UNSLEEVED']:
            dominionCardWidth, dominionCardHeight = (9.1*cm, 5.9*cm)
            print 'Using normal card size, %.2fcm x%.2fcm' % (dominionCardWidth/cm,dominionCardHeight/cm)
        else:
            dominionCardWidth, dominionCardHeight = self.parseDimensions(size)
            print 'Using custom card size, %.2fcm x %.2fcm' % (dominionCardWidth/cm,dominionCardHeight/cm)

        papersize = None
        if not self.options.papersize:
            if os.path.exists("/etc/papersize"):
                papersize = open ("/etc/papersize").readline().upper()
            else:
                papersize = 'LETTER'
        else:
            papersize = self.options.papersize.upper()

        if papersize == 'A4':
            print "Using A4 sized paper."
            self.paperwidth, self.paperheight = A4
        elif papersize == 'LETTER':
            print "Using letter sized paper."
            self.paperwidth, self.paperheight = LETTER
        else:
            self.paperwidth, self.paperheight = self.parseDimensions(papersize)
            print 'Using custom paper size, %.2fcm x %.2fcm' % (self.paperwidth/cm,self.paperheight/cm)

        if self.options.orientation == "vertical":
            self.tabWidth, self.tabBaseHeight = dominionCardHeight, dominionCardWidth
        else:
            self.tabWidth, self.tabBaseHeight = dominionCardWidth, dominionCardHeight

        fixedMargins = False
        if self.options.tabs_only:
            #fixed for Avery 8867 for now
            minmarginwidth=0.76*cm
            minmarginheight=1.27*cm
            self.tabLabelHeight = 1.27*cm
            self.tabLabelWidth = 4.44*cm
            self.tabBaseHeight = 0
            self.tabWidth = self.tabLabelWidth
            self.horizontalBorderSpace = 0.76*cm
            self.verticalBorderSpace = 0.01*cm
            fixedMargins = True
        else:
            minmarginwidth, minmarginheight = self.parseDimensions(self.options.minmargin)
            self.tabLabelWidth = self.options.tabwidth * cm
            self.tabLabelHeight = .9*cm
            self.horizontalBorderSpace = 0*cm
            self.verticalBorderSpace = 0*cm

        self.tabHeight = self.tabBaseHeight + self.tabLabelHeight

        self.totalTabWidth = self.tabWidth + self.horizontalBorderSpace
        self.totalTabHeight = self.tabHeight + self.verticalBorderSpace

        print "Paper dimensions: %fcm (w) x %fcm (h)" % (self.paperwidth / cm, self.paperheight / cm)
        print "Tab dimensions: %fcm (w) x %fcm (h)" % (self.totalTabWidth / cm, self.totalTabHeight / cm)

        numTabsVerticalP = int ((self.paperheight - 2*minmarginheight) / self.totalTabHeight)
        numTabsHorizontalP = int ((self.paperwidth - 2*minmarginwidth) / self.totalTabWidth)
        numTabsVerticalL = int ((self.paperwidth - 2*minmarginwidth) / self.totalTabHeight)
        numTabsHorizontalL = int ((self.paperheight - 2*minmarginheight) / self.totalTabWidth)

        if numTabsVerticalL * numTabsHorizontalL > numTabsVerticalP * numTabsHorizontalP and not fixedMargins:
            self.numTabsVertical, self.numTabsHorizontal\
                = numTabsVerticalL, numTabsHorizontalL
            self.paperheight, self.paperwidth = self.paperwidth, self.paperheight
            self.minHorizontalMargin = minmarginheight
            self.minVerticalMargin = minmarginwidth
        else:
            self.numTabsVertical, self.numTabsHorizontal\
                = numTabsVerticalP, numTabsHorizontalP
            self.minHorizontalMargin = minmarginwidth
            self.minVerticalMargin = minmarginheight

        if self.numTabsHorizontal % 2 != 0:
            # force on sameside if an uneven # of tabs horizontally
            self.options.sameside = True

        if not fixedMargins:
            #dynamically max margins
            self.horizontalMargin = (self.paperwidth-self.numTabsHorizontal*self.totalTabWidth)/2
            self.verticalMargin = (self.paperheight-self.numTabsVertical*self.totalTabHeight)/2
        else:
            self.horizontalMargin = minmarginwidth
            self.verticalMargin = minmarginheight

        print "Margins: %fcm h, %fcm v\n" % (self.horizontalMargin / cm,
                                             self.verticalMargin / cm)

        self.tabOutline = [(0,0,self.tabWidth,0),
                      (self.tabWidth,0,self.tabWidth,self.tabHeight),
                      (self.tabWidth,self.tabHeight,
                       self.tabWidth-self.tabLabelWidth,self.tabHeight),
                      (self.tabWidth-self.tabLabelWidth,
                       self.tabHeight,self.tabWidth-self.tabLabelWidth,
                       self.tabBaseHeight),
                      (self.tabWidth-self.tabLabelWidth,
                       self.tabBaseHeight,0,self.tabBaseHeight),
                      (0,self.tabBaseHeight,0,0)]

        self.expansionTabOutline = [(0,0,self.tabWidth,0),
                      (self.tabWidth,0,self.tabWidth,self.tabBaseHeight),
                      (self.tabWidth,self.tabBaseHeight,
                       self.tabWidth/2+self.tabLabelWidth/2,self.tabBaseHeight),
                      (self.tabWidth/2+self.tabLabelWidth/2,self.tabBaseHeight,
                       self.tabWidth/2+self.tabLabelWidth/2,self.tabHeight),
                      (self.tabWidth/2+self.tabLabelWidth/2,self.tabHeight,
                       self.tabWidth/2-self.tabLabelWidth/2,self.tabHeight),
                      (self.tabWidth/2-self.tabLabelWidth/2,self.tabHeight,
                       self.tabWidth/2-self.tabLabelWidth/2,self.tabBaseHeight),
                      (self.tabWidth/2-self.tabLabelWidth/2,self.tabBaseHeight,
                       0,self.tabBaseHeight),
                      (0,self.tabBaseHeight,0,0)]
        
        try:
            dirn = os.path.join(self.filedir,'fonts')
            pdfmetrics.registerFont(TTFont('MinionPro-Regular',os.path.join(dirn,'MinionPro-Regular.ttf')))
            pdfmetrics.registerFont(TTFont('MinionPro-Bold',os.path.join(dirn,'MinionPro-Bold.ttf')))
        except:
            raise
            pdfmetrics.registerFont(TTFont('MinionPro-Regular','OptimusPrincepsSemiBold.ttf'))
            pdfmetrics.registerFont(TTFont('MinionPro-Bold','OptimusPrinceps.ttf'))
        if options.read_yaml:
            import yaml
            cardfile = open("cards.yaml","r")
            cards = yaml.load(cardfile)
        else:
            cards = self.read_card_defs(os.path.join(self.filedir,"dominion_cards.txt"))
            self.read_card_extras(os.path.join(self.filedir,"dominion_card_extras.txt"),cards)


        baseCards = [card.name for card in cards if card.cardset.lower() == 'base']
        def isBaseExpansionCard(card):
            return card.cardset.lower() != 'base' and card.name in baseCards
        if self.options.base_cards_with_expansion:
            cards = [card for card in cards if card.cardset.lower() != 'base']
        else:
            cards = [card for card in cards if not isBaseExpansionCard(card)]

        if self.options.expansions:
            self.options.expansions = [o.lower() for o in self.options.expansions]
            filteredCards = []
            knownExpansions = set()
            for c in cards:
                knownExpansions.add(c.cardset)
                if c.cardset in self.options.expansions:
                    filteredCards.append(c)
            unknownExpansions = set(self.options.expansions) - knownExpansions
            if unknownExpansions:
                print "Error - unknown expansion(s): %s" % ", ".join(unknownExpansions)
                return

            cards = filteredCards

        if options.expansion_dividers:
            cardnamesByExpansion = {}
            for c in cards:
                if isBaseExpansionCard(c):
                    continue
                cardnamesByExpansion.setdefault(c.cardset,[]).append(c.name.strip())
            for exp,names in cardnamesByExpansion.iteritems():
                c = Card(exp, exp, ("Expansion",), None, ' | '.join(sorted(names)))
                cards.append(c)

        if options.write_yaml:
            import yaml
            out = yaml.dump(cards)
            open('cards.yaml','w').write(out)

        # When sorting cards, want to always put "base" cards after all
        # kingdom cards, and order the base cards in a set order - the
        # order they are listed in the database (ie, all normal treasures
        # by worth, then potion, then all normal VP cards by worth, then
        # trash)
        def baseIndex(name):
            try:
                return baseCards.index(name)
            except Exception:
                return -1

        if options.order == "global":
            sortKey = lambda x: (int(x.isExpansion()), baseIndex(x.name),x.name)
        else:
            sortKey = lambda x: (x.cardset,int(x.isExpansion()),baseIndex(x.name),x.name)
        cards.sort(key=sortKey)

        if not f:
            f = "dominion_tabs.pdf"
        self.canvas = canvas.Canvas(f, pagesize=(self.paperwidth, self.paperheight))
        self.drawDividers(cards)
        self.canvas.save()

if __name__=='__main__':
    import sys
    tabs = DominionTabs()
    tabs.main(sys.argv[1:])
