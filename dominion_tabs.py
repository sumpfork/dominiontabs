import re,pprint
from optparse import OptionParser
import os.path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER,A4,portrait,landscape
from reportlab.lib.units import cm,inch
from reportlab.platypus import Frame,Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

def split(l,n):
    i = 0
    while i < len(l) - n:
        yield l[i:i+n]
        i += n
    yield l[i:]

class Card:
    def __init__(self,name,cardset,types,cost,description,potcost=0):
        self.name = name
        self.cardset = cardset
        self.types = types
        self.cost = cost
        self.potcost = potcost
        self.description = description
        self.extra = ""

    def __repr__(self):
        return '"' + self.name + '"'

    def toString(self):
        return self.name + ' ' + self.cardset + ' ' + '-'.join(self.types) + ' ' + `self.cost` + ' ' + self.description + ' ' + self.extra

class CardType:
    def __init__(self, typeNames, tabImageFile, contentHeightOffset):
        self.typeNames = typeNames
        self.tabImageFile = tabImageFile
        self.contentHeightOffset = contentHeightOffset

    def getTypeNames(self):
        return self.typeNames

    def getTabImageFile(self):
        return self.tabImageFile

    def getNoCoinTabImageFile(self):
        return ''.join(os.path.splitext(self.tabImageFile)[0] + '_nc' + os.path.splitext(self.tabImageFile)[1])

    def getTabContentHeightOffset(self):
        return self.contentHeightOffset

class DominionTabs:
    cardTypes = [
        CardType(('Action',), 'action.png', 0),
        CardType(('Action','Attack'), 'action.png', 0),
        CardType(('Action','Attack','Prize'), 'action.png', 0),
        CardType(('Action','Reaction'), 'reaction.png', 0),
        CardType(('Action','Victory'), 'action-victory.png', 0),
        CardType(('Action','Duration'), 'duration.png', 0),
        CardType(('Action','Looter'), 'action.png', 0),
        CardType(('Action','Prize'), 'action.png', 0),
        CardType(('Action','Ruins'), 'ruins.png', 0),
        CardType(('Action','Shelter'), 'shelter.png', 0),
        CardType(('Action','Attack','Looter'), 'action.png', 0),
        CardType(('Reaction',), 'reaction.png', 0),
        CardType(('Reaction','Shelter'), 'Shelter.png', 0),
        CardType(('Treasure',), 'treasure.png', 0),
        CardType(('Treasure','Victory'), 'treasure-victory.png', 0),
        CardType(('Treasure','Prize'), 'treasure.png', 0),
        CardType(('Treasure','Reaction'), 'treasure-reaction.png', 0),
        CardType(('Victory',), 'victory.png', 0),
        CardType(('Victory','Reaction'), 'victory-reaction.png', 0),
        CardType(('Victory','Shelter'), 'shelter.png', 0),
        CardType(('Curse',), 'curse.png', 0),
        ]

    cardTypes = dict(((c.getTypeNames(),c) for c in cardTypes))

    labelImages = {
        ('Action',) : 'action.png',
        ('Action','Attack') : 'action.png',
        ('Action','Attack','Prize') : 'action.png',
        ('Action','Reaction') : 'reaction.png',
        ('Action','Victory') : 'action-victory.png',
        ('Action','Duration') : 'duration.png',
        ('Action','Looter') : 'action.png',
        ('Action','Prize') : 'action.png',
        ('Action','Ruins') : 'ruins.png',
        ('Action','Shelter') : 'shelter.png',
        ('Action','Attack','Looter') : 'action.png',
        ('Reaction',) : 'reaction.png',
        ('Reaction','Shelter') : 'Shelter.png',
        ('Treasure',) : 'treasure.png',
        ('Treasure','Victory') : 'treasure-victory.png',
        ('Treasure','Prize') : 'treasure.png',
        ('Treasure','Reaction') : 'treasure-reaction.png',
        ('Victory',) : 'victory.png',
        ('Victory','Reaction') : 'victory-reaction.png',
        ('Victory','Shelter') : 'shelter.png',
        ('Curse',) : 'curse.png'
        }

    noCoinLabelImages = dict(((name,''.join((os.path.splitext(fname)[0]+'_nc',os.path.splitext(fname)[1]))) for name,fname in labelImages.iteritems()))

    setImages = {
        'base' : 'base_set.png',
        'intrigue' : 'intrigue_set.png',
        'seaside' : 'seaside_set.png',
        'prosperity' : 'prosperity_set.png',
        }

    def add_inline_images(self, text, fontsize):
        replace = '<img src='"'images/coin_small_\\1.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (fontsize*1.2)
        text = re.sub('(\d)\s(c|C)oin(s)?', replace,text)
        replace = '<img src='"'images/coin_small_question.png'"' width=%d height='"'100%%'"' valign='"'middle'"'/>' % (fontsize*1.2)
        text = re.sub('\?\s(c|C)oin(s)?', replace,text)
        replace = '<img src='"'images/victory_emblem.png'"' width=%d height='"'120%%'"' valign='"'middle'"'/>' % (fontsize*1.5)
        text = re.sub('\<VP\>', replace,text)
        return text

    def drawTab(self,card,x,y,useExtra=False):
    #rightSide = False
        if self.numTabsHorizontal == 2:
            rightSide = x%2 == 1
        else:
            rightSide = useExtra
        self.canvas.resetTransforms()
        self.canvas.translate(self.horizontalMargin,self.verticalMargin)
        if useExtra:
            self.canvas.translate(self.options.back_offset,0)
        self.canvas.translate(x*self.tabWidth,y*self.tabTotalHeight)
    
        #draw outline or cropmarks
        self.canvas.saveState()
        self.canvas.setLineWidth(0.1)
        cropmarksright = (x == self.numTabsHorizontal-1)
        cropmarksleft = (x == 0)
        if rightSide and not self.options.sameside:
            self.canvas.translate(self.tabWidth,0)
            self.canvas.scale(-1,1)
        if not self.options.cropmarks and not useExtra:
            #don't draw outline on back, in case lines don't line up with front
            self.canvas.lines(self.tabOutline)
        elif self.options.cropmarks:
            cmw = 0.5*cm
            mirror = cropmarksright and not rightSide or cropmarksleft and rightSide
            if mirror:
                self.canvas.saveState()
                self.canvas.translate(self.tabWidth,0)
                self.canvas.scale(-1,1)
            if cropmarksleft or cropmarksright:
                self.canvas.line(-2*cmw,0,-cmw,0)
                self.canvas.line(-2*cmw,self.tabBaseHeight,-cmw,self.tabBaseHeight)
                if y > 0:
                    self.canvas.line(-2*cmw,self.tabTotalHeight,-cmw,self.tabTotalHeight)
            if mirror:
                self.canvas.restoreState()
            if y == 0:
                self.canvas.line(self.tabWidth,-2*cmw,self.tabWidth,-cmw)
                self.canvas.line(self.tabWidth-self.tabLabelWidth,-2*cmw,self.tabWidth-self.tabLabelWidth,-cmw)
                if x == 0:
                    self.canvas.line(0,-2*cmw,0,-cmw)
            elif y == self.numTabsVertical-1:
                self.canvas.line(self.tabWidth,self.tabTotalHeight+cmw,self.tabWidth,self.tabTotalHeight+2*cmw)
                self.canvas.line(self.tabWidth-self.tabLabelWidth,
                                 self.tabTotalHeight+cmw,
                                 self.tabWidth-self.tabLabelWidth,
                                 self.tabTotalHeight+2*cmw)
                if x == 0:
                    self.canvas.line(0,self.tabTotalHeight+cmw,0,self.tabTotalHeight+2*cmw)
                
        self.canvas.restoreState()

        #draw tab flap
        self.canvas.saveState()
        if not rightSide or self.options.sameside:
            self.canvas.translate(self.tabWidth-self.tabLabelWidth,
                        self.tabTotalHeight-self.tabLabelHeight)
        else:
            self.canvas.translate(0,self.tabTotalHeight-self.tabLabelHeight)
        self.canvas.drawImage(os.path.join('images',DominionTabs.noCoinLabelImages[card.types]),1,0,
                    self.tabLabelWidth-2,self.tabLabelHeight-1,
                    preserveAspectRatio=False,anchor='n',mask='auto')
        if card.types[0] == 'Treasure' and (len(card.types) == 1 or card.types[1] != 'Reaction'
                                            and card.types[1] != 'Victory')\
                or card.types == ('Curse',):
            textHeight = self.tabLabelHeight/2-4
            costHeight = textHeight
            potSize = 12
            potHeight = 5
        else:
            textHeight = self.tabLabelHeight/2-7
            costHeight = textHeight-1
            if card.types == ('Victory','Reaction') or\
                    card.types == ('Treasure','Reaction') or\
                    card.types == ('Action','Ruins') or\
                    len(card.types) > 1 and card.types[1].lower() == 'shelter':
                costHeight = textHeight+1
            potSize = 11
            potHeight = 2

        self.canvas.drawImage("images/coin_small.png",4,costHeight-5,16,16,preserveAspectRatio=True,mask='auto')
        textInset = 22
        textWidth = 85

        if card.potcost:
            self.canvas.drawImage("images/potion.png",21,potHeight,potSize,potSize,preserveAspectRatio=True,mask=[255,255,255,255,255,255])
            textInset += potSize
            textWidth -= potSize

        #set image
        setImage = DominionTabs.setImages.get(card.cardset, None)
        if setImage:
            self.canvas.drawImage(os.path.join('images',setImage), self.tabLabelWidth-20, potHeight, 14, 12, mask='auto')
        elif setImage == None:
            print 'warning, no image for set',card.cardset
            DominionTabs.setImages[card.cardset] = 0

        self.canvas.setFont('MinionPro-Bold',12)
        cost = str(card.cost)
        if 'Prize' in card.types:
            cost += '*'
        costWidthOffset = 12
        #if len(card.types) > 1 and card.types[1].lower() == 'shelter':
        #    costWidthOffset = 10
        self.canvas.drawCentredString(costWidthOffset,costHeight,cost)
        fontSize = 12
        name = card.name.upper()
        name_parts = name.partition(' / ')
        if name_parts[1]:
            name_parts = (name_parts[0] + ' /', name_parts[2])
        else:
            name_parts = name.split()
            
        width = pdfmetrics.stringWidth(name,'MinionPro-Regular',fontSize)
        while width > textWidth and fontSize > 8:
            fontSize -= 1
            #print 'decreasing font size for tab of',name,'now',fontSize
            width = pdfmetrics.stringWidth(name,'MinionPro-Regular',fontSize)
        tooLong = width > textWidth
        #if tooLong:
        #    print name

        #self.canvas.drawString(tabLabelWidth/2+8,tabLabelHeight/2-7,name[0])
        w = 0
        for i,n in enumerate(name_parts):
            self.canvas.setFont('MinionPro-Regular',fontSize)
            h = textHeight
            if tooLong:
                if i == 0:
                    h += h/2
                else:
                    h -= h/2
            self.canvas.drawString(textInset+w,h,n[0])
            w += pdfmetrics.stringWidth(n[0],'MinionPro-Regular',fontSize)
            #self.canvas.drawString(tabLabelWidth/2+8+w,tabLabelHeight/2-7,name[1:])
            self.canvas.setFont('MinionPro-Regular',fontSize-2)
            self.canvas.drawString(textInset+w,h,n[1:])
            w += pdfmetrics.stringWidth(n[1:],'MinionPro-Regular',fontSize-2)
            w += pdfmetrics.stringWidth(' ','MinionPro-Regular',fontSize)
            if tooLong:
                w = 0
        self.canvas.restoreState()

        #draw text
        if useExtra and card.extra:
            descriptions = (card.extra,)
        else:
            descriptions = re.split("--+",card.description)

        height = 0
        for d in descriptions:
            s = getSampleStyleSheet()['BodyText']
            s.fontName = "Times-Roman"
            dmod = self.add_inline_images(d,s.fontSize)
            p = Paragraph(dmod,s)
            textHeight = self.tabTotalHeight - self.tabLabelHeight + 0.2*cm
            textWidth = self.tabWidth - cm
            
            w,h = p.wrap(textWidth,textHeight)
            while h > textHeight:
                s.fontSize -= 1
                s.leading -= 1
                #print 'decreasing fontsize on description for',card.name,'now',s.fontSize
                dmod = self.add_inline_images(d,s.fontSize)
                p = Paragraph(dmod,s)
                w,h = p.wrap(textWidth,textHeight)
            p.drawOn(self.canvas,cm/2.0,textHeight-height-h-0.5*cm)
            height += h + 0.2*cm

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
                if currentCard and (currentCard not in (c.name for c in cards)):
                    print currentCard + ' has extra description, but is not in cards'
            else:
                extra += line
        if currentCard and extra:
            extras[currentCard] = extra.strip()
        for c in cards:
            if not c.name in extras:
                print c.name + ' missing from extras'
            else:
                c.extra = extras[c.name]
                #print c.name + ' ::: ' + extra

    def add_definition_line(self,card,line):
        baseaction = re.compile("^\s*(\+\d+\s+\w+)(?:[,.;])")
        m = baseaction.match(line)
        prefix = ''
        while m:
            prefix += line[m.start(1):m.end(1)] + '----'
            line = line[m.end():]
            m = baseaction.match(line)
        line = prefix + line
        if not card.description.strip().endswith(';')\
                and not card.description.strip().endswith('---')\
                and not line.startswith('---'):
            card.description += '----' + line
        else:
            card.description += line

    def read_card_defs(self,fname):
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
                currentCard = Card(m.groupdict()["name"],
                                   m.groupdict()["set"].lower(),
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

    def drawCards(self,cards):
        cards = split(cards,self.numTabsVertical*self.numTabsHorizontal)
        for pageCards in cards:
            #print 'pageCards:',pageCards

            #print sets for this page
            self.canvas.saveState()
            self.canvas.setFont('MinionPro-Regular',12)
            sets = []
            for c in pageCards:
                setTitle = c.cardset.title() 
                if setTitle not in sets:
                    sets.append(setTitle)
            self.canvas.drawCentredString(self.paperwidth/2,20,'/'.join(sets))
            self.canvas.restoreState()

            for i,card in enumerate(pageCards):       
                #print card
                x = i % self.numTabsHorizontal
                y = i / self.numTabsHorizontal
                self.canvas.saveState()
                self.drawTab(card,x,self.numTabsVertical-1-y)
                self.canvas.restoreState()
            self.canvas.showPage()
            for i,card in enumerate(pageCards):       
                #print card
                x = (self.numTabsHorizontal-1-i) % self.numTabsHorizontal
                y = i / self.numTabsHorizontal
                self.canvas.saveState()
                self.drawTab(card,x,self.numTabsVertical-1-y,useExtra=True)
                self.canvas.restoreState()
            self.canvas.showPage()

    def main(self,argstring):
        parser = OptionParser()
        parser.add_option("--back_offset",type="int",dest="back_offset",default=0,
                          help="Points to offset the back page to the right; needed for some printers")
        parser.add_option("--orientation",type="string",dest="orientation",default="horizontal",
                          help="horizontal or vertical, default:horizontal")
        parser.add_option("--sleeved",action="store_true",dest="sleeved",help="use --size=sleeved instead")
        parser.add_option("--size",type="string",dest="size",default='normal',
                          help="'<%f>x<%f>' (size in cm), or 'normal' = '9.1x5.9', or 'sleeved' = '9.4x6.15'")
        parser.add_option("--minmargin",type="string",dest="minmargin",default="1x1",
                          help="'<%f>x<%f>' (size in cm, left/right, top/bottom), default: 1x1")
        parser.add_option("--papersize",type="string",dest="papersize",default=None,
                          help="'<%f>x<%f>' (size in cm), or 'A4', or 'LETTER'")
        parser.add_option("--samesidelabels",action="store_true",dest="sameside",
                          help="force all label tabs to be on the same side")
        parser.add_option("--expansions",action="append",type="string",
                          help="subset of dominion expansions to produce tabs for")
        parser.add_option("--cropmarks",action="store_true",dest="cropmarks",
                           help="print crop marks on both sides, rather than tab outlines on one")
        (self.options,args) = parser.parse_args(argstring)

        size = self.options.size.upper()
        if size == 'SLEEVED' or self.options.sleeved:
            dominionCardWidth, dominionCardHeight = (9.4*cm, 6.15*cm)
            print 'Using sleeved card size, %.2fcm x %.2fcm' % (dominionCardWidth/cm,dominionCardHeight/cm)
        elif size == 'NORMAL':
            dominionCardWidth, dominionCardHeight = (9.1*cm, 5.9*cm)
            print 'Using normal card size, %.2fcm x%.2fcm' % (dominionCardWidth/cm,dominionCardHeight/cm)
        else:
            x, y = size.split ("X", 1)
            dominionCardWidth, dominionCardHeight = (float (x) * cm, float (y) * cm)
            print 'Using custom card size, %.2fcm x %.2fcm' % (dominionCardWidth/cm,dominionCardHeight/cm)

        papersize = None
        if not self.options.papersize:
            if os.path.exists("/etc/papersize"):
                papersize = open ("/etc/papersize").readline().upper()
        else:
            papersize = self.options.papersize.upper()

        if papersize == 'A4':
            print "Using A4 sized paper."
            self.paperwidth, self.paperheight = A4
        else:
            print "Using letter sized paper."
            self.paperwidth, self.paperheight = LETTER

        minmarginwidth, minmarginheight = self.options.minmargin.split ("x", 1)
        minmarginwidth, minmarginheight = float (minmarginwidth) * cm, float (minmarginheight) * cm

        if self.options.orientation == "vertical":
            self.tabWidth, self.tabBaseHeight = dominionCardHeight, dominionCardWidth
        else:
            self.tabWidth, self.tabBaseHeight = dominionCardWidth, dominionCardHeight

        self.tabLabelHeight = 0.9*cm
        self.tabLabelWidth = 4*cm
        self.tabTotalHeight = self.tabBaseHeight + self.tabLabelHeight

        numTabsVerticalP = int ((self.paperheight - 2*minmarginheight) / self.tabTotalHeight)
        numTabsHorizontalP = int ((self.paperwidth - 2*minmarginwidth) / self.tabWidth)
        numTabsVerticalL = int ((self.paperwidth - 2*minmarginwidth) / self.tabWidth)
        numTabsHorizontalL = int ((self.paperheight - 2*minmarginheight) / self.tabTotalHeight)

        if numTabsVerticalL * numTabsHorizontalL > numTabsVerticalP * numTabsHorizontalP:
            self.numTabsVertical, self.numTabsHorizontal\
                = numTabsVerticalL, numTabsHorizontalL
            self.paperheight, self.paperwidth = self.paperwidth, self.paperheight
        else:
            self.numTabsVertical, self.numTabsHorizontal\
                = numTabsVerticalP, numTabsHorizontalP

        self.horizontalMargin = (self.paperwidth-self.numTabsHorizontal*self.tabWidth)/2
        self.verticalMargin = (self.paperheight-self.numTabsVertical*self.tabTotalHeight)/2

        print "Margins: %fcm h, %fcm v\n" % (self.horizontalMargin / cm, 
                                             self.verticalMargin / cm)

        self.tabOutline = [(0,0,self.tabWidth,0),
                      (self.tabWidth,0,self.tabWidth,self.tabTotalHeight),
                      (self.tabWidth,self.tabTotalHeight,
                       self.tabWidth-self.tabLabelWidth,self.tabTotalHeight),
                      (self.tabWidth-self.tabLabelWidth,
                       self.tabTotalHeight,self.tabWidth-self.tabLabelWidth,
                       self.tabBaseHeight),
                      (self.tabWidth-self.tabLabelWidth,
                       self.tabBaseHeight,0,self.tabBaseHeight),
                      (0,self.tabBaseHeight,0,0)]

        try:
            pdfmetrics.registerFont(TTFont('MinionPro-Regular','fonts/MinionPro-Regular.ttf'))
            pdfmetrics.registerFont(TTFont('MinionPro-Bold','fonts/MinionPro-Bold.ttf'))
        except:
            pdfmetrics.registerFont(TTFont('MinionPro-Regular','OptimusPrincepsSemiBold.ttf'))
            pdfmetrics.registerFont(TTFont('MinionPro-Bold','OptimusPrinceps.ttf'))
        cards = self.read_card_defs("dominion_cards.txt")
        if self.options.expansions:
            self.options.expansions = [o.lower() for o in self.options.expansions]
            cards=[c for c in cards if c.cardset in self.options.expansions]
        cards.sort(cmp=lambda x,y: cmp((x.cardset,x.name),(y.cardset,y.name)))
        extras = self.read_card_extras("dominion_card_extras.txt",cards)
        #print '%d cards read' % len(cards)
        sets = {}
        types = {}
        for c in cards:
            sets[c.cardset] = sets.get(c.cardset,0) + 1
            types[c.types] = types.get(c.types,0) + 1
        #pprint.pprint(sets)
        #pprint.pprint(types)

        if args:
            fname = args[0]
        else:
            fname = "dominion_tabs.pdf"
        self.canvas = canvas.Canvas(fname, pagesize=(self.paperwidth, self.paperheight))
        #pprint.pprint(self.canvas.getAvailableFonts())
        self.drawCards(cards)
        self.canvas.save()
    
if __name__=='__main__':
    import sys
    tabs = DominionTabs()
    tabs.main(sys.argv[1:])
