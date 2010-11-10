import re,pprint
from optparse import OptionParser

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER,A4,portrait,landscape
from reportlab.lib.units import cm,inch
from reportlab.platypus import Frame,Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

labelImages = {
    ('Action',) : 'action.png',
    ('Action','Attack') : 'action.png',
    ('Action','Reaction') : 'reaction.png',
    ('Action','Victory') : 'action-victory.png',
    ('Action','Duration') : 'duration.png',
    ('Reaction',) : 'reaction.png',
    ('Treasure',) : 'treasure.png',
    ('Treasure','Victory') : 'treasure-victory.png',
    ('Victory',) : 'victory.png',
    ('Curse',) : 'curse.png'
}
    
def drawTab(card,x,y,useExtra=False):
    #rightSide = False
    if numTabsHorizontal == 2:
        rightSide = x%2 == 1
    else:
        rightSide = useExtra
    c.resetTransforms()
    c.translate(horizontalMargin,verticalMargin)
    if useExtra:
        c.translate(options.back_offset,0)
    c.translate(x*tabWidth,y*tabTotalHeight)
    
    #draw outline
    #don't draw outline on back, in case lines don't line up with front
    if not useExtra:
        c.saveState()
        c.setLineWidth(0.1)
        if rightSide:
            c.translate(tabWidth,0)
            c.scale(-1,1)
        c.lines(tabOutline)
        c.restoreState()

    #draw tab flap
    c.saveState()
    if not rightSide:
        c.translate(tabWidth-tabLabelWidth,tabTotalHeight-tabLabelHeight)
    else:
        c.translate(0,tabTotalHeight-tabLabelHeight)
    c.drawImage(labelImages[card.types],1,0,
                tabLabelWidth-2,tabLabelHeight-1,
                preserveAspectRatio=False,anchor='n')
    if card.types == ('Treasure',) or card.types == ('Curse',):
        textHeight = tabLabelHeight/2-4
        costHeight = textHeight
        potSize = 12
        potHeight = 5
    else:
        textHeight = tabLabelHeight/2-7
        costHeight = textHeight-1
        potSize = 11
        potHeight = 2

    textInset = 22
    textWidth = 85

    if card.potcost:
        c.drawImage("potion.png",21,potHeight,potSize,potSize,preserveAspectRatio=True,mask=[255,255,255,255,255,255])
        textInset += potSize
        textWidth -= potSize

    c.setFont('MinionPro-Bold',12)
    c.drawCentredString(12,costHeight,str(card.cost))
    fontSize = 12
    name = card.name.upper()
    name_parts = name.split()
    width = pdfmetrics.stringWidth(name,'MinionPro-Regular',fontSize)
    while width > textWidth and fontSize > 8:
        fontSize -= 1
        #print 'decreasing font size for tab of',name,'now',fontSize
        width = pdfmetrics.stringWidth(name,'MinionPro-Regular',fontSize)
    tooLong = width > textWidth
    #if tooLong:
    #    print name

    #c.drawString(tabLabelWidth/2+8,tabLabelHeight/2-7,name[0])
    w = 0
    for i,n in enumerate(name_parts):
        c.setFont('MinionPro-Regular',fontSize)
        h = textHeight
        if tooLong:
            if i == 0:
                h += h/2
            else:
                h -= h/2
        c.drawString(textInset+w,h,n[0])
        w += pdfmetrics.stringWidth(n[0],'MinionPro-Regular',fontSize)
        #c.drawString(tabLabelWidth/2+8+w,tabLabelHeight/2-7,name[1:])
        c.setFont('MinionPro-Regular',fontSize-2)
        c.drawString(textInset+w,h,n[1:])
        w += pdfmetrics.stringWidth(n[1:],'MinionPro-Regular',fontSize-2)
        w += pdfmetrics.stringWidth(' ','MinionPro-Regular',fontSize)
        if tooLong:
            w = 0
    c.restoreState()
    
    #draw text
    if useExtra and card.extra:
        usingExtra = True
        descriptions = (card.extra,)
    else:
        usingExtra = False
        descriptions = re.split("--+",card.description)
    height = 0
    for d in descriptions:
        if not usingExtra:
        #d = re.sub(r"\n",";",d,flags=re.MULTILINE)
            d = re.sub(r"([^ ;])\+",r"\1; +",d)
        s = getSampleStyleSheet()['BodyText']
        s.fontName = "Times-Roman"
        p = Paragraph(d,s)
        textHeight = tabTotalHeight - tabLabelHeight + 0.3*cm
        textWidth = tabWidth - cm
        
        w,h = p.wrap(textWidth,textHeight)
        while h > textHeight:
            s.fontSize -= 1
            s.leading -= 1
            #print 'decreasing fontsize on description for',card.name,'now',s.fontSize
            p = Paragraph(d,s)
            w,h = p.wrap(textWidth,textHeight)
        p.drawOn(c,cm/2.0,textHeight-height-h-0.5*cm)
        height += h + 0.2*cm

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

def read_card_extras(fname,cards):
    f = open(fname)
    cardName = re.compile("^:::(?P<name>[ \w']*)")
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
        else:
            extra += line
    if currentCard and extra:
        extras[currentCard] = extra
    for c in cards:
        if not c.name in extras:
            print c.name + ' missing from extras'
        else:
            c.extra = extras[c.name]
            #print c.name + ' ::: ' + extra

def read_card_defs(fname):
    cards = []
    f = open(fname)
    carddef = re.compile("^\d+\t+(?P<name>[\w' ]+)\t+(?P<set>\w+)\t+(?P<type>[-\w ]+)\t+\$(?P<cost>\d+)( (?P<potioncost>\d)+P)?\t+(?P<description>.*)")
    currentCard = None
    for line in f:
        m = carddef.match(line)
        if m:
            if m.groupdict()["potioncost"]:
                potcost = int(m.groupdict()["potioncost"])
            else:
                potcost = 0
            currentCard = Card(m.groupdict()["name"],
                               m.groupdict()["set"],
                               tuple([t.strip() for t in m.groupdict()["type"].split("-")]),
                               int(m.groupdict()["cost"]),
                               m.groupdict()["description"],
                               potcost)
            cards.append(currentCard)
        elif line.strip():
            if not currentCard.description.strip().endswith(';')\
                    and not currentCard.description.strip().endswith('.')\
                    and not currentCard.description.strip().endswith('---')\
                    and not line.startswith('---'):
                #print currentCard.description
                #print line
                currentCard.description += '; ' + line
            else:
                currentCard.description += line
        #print currentCard
        #print '----'
    return cards

def split(l,n):
    i = 0
    while i < len(l) - n:
        yield l[i:i+n]
        i += n
    yield l[i:]

def drawCards(c,cards):
    cards = split(cards,numTabsVertical*numTabsHorizontal)
    for pageCards in cards:
        print 'pageCards:',pageCards
        for i,card in enumerate(pageCards):       
            #print card
            x = i % numTabsHorizontal
            y = i / numTabsHorizontal
            c.saveState()
            drawTab(card,x,numTabsVertical-1-y)
            c.restoreState()
        c.showPage()
        for i,card in enumerate(pageCards):       
            #print card
            x = (numTabsHorizontal-1-i) % numTabsHorizontal
            y = i / numTabsHorizontal
            c.saveState()
            drawTab(card,x,numTabsVertical-1-y,useExtra=True)
            c.restoreState()
        c.showPage()
    
if __name__=='__main__':

    parser = OptionParser()
    parser.add_option("--back_offset",type="int",dest="back_offset",default=5,
                      help="Points to offset the back page to the right; needed for some printers")
    parser.add_option("--orientation",type="string",dest="orientation",default="horizontal",
                      help="horizontal or vertical, default:horizontal")
    parser.add_option("--sleeved",action="store_true",dest="sleeved",help="use --size=sleeved instead")
    parser.add_option("--size",type="string",dest="size",default=None,help="'<%f>x<%f>' (size in cm), or 'normal' = '9.1x5.9', or 'sleeved' = '9.4x6.15'")
    parser.add_option("--minmargin",type="string",dest="minmargin",default="1x1",help="'<%f>x<%f>' (size in cm, left/right, top/bottom), default: 1x1")
    parser.add_option("--papersize",type="string",dest="papersize",default=None,help="'<%f>x<%f>' (size in cm), or 'A4', or 'LETTER'")

    (options,args) = parser.parse_args()

    if options.sleeved:
        dominionCardWidth, dominionCardHeight = (9.4*cm, 6.15*cm)
    else:
        dominionCardWidth, dominionCardHeight = (9.1*cm, 5.9*cm)
    if options.size != None:
        x, y = options.size.split ("x", 1)
        dominionCardWidth, dominionCardHeight = (float (x) * cm, float (y) * cm)

    if options.papersize == 'A4' or options.papersize == 'a4':
        print "Using A4 sized paper."
        paperwidth, paperheight = A4
    elif options.papersize == 'LETTER' or options.papersize == 'letter':
        print "Using letter sized paper."
        paperwidth, paperheight = LETTER
    elif open ("/etc/papersize").readline == "letter":
        print "Using letter sized paper."
        paperwidth, paperheight = LETTER
    else:
        print "Using A4 sized paper."
        paperwidth, paperheight = A4
    
    minmarginwidth, minmarginheight = options.minmargin.split ("x", 1)
    minmarginwidth, minmarginheight = float (minmarginwidth) * cm, float (minmarginheight) * cm

    if options.orientation == "vertical":
        tabWidth, tabBaseHeight = dominionCardHeight, dominionCardWidth
    else:
        tabWidth, tabBaseHeight = dominionCardWidth, dominionCardHeight
    
    tabLabelHeight = 0.9*cm
    tabLabelWidth = 3.5*cm
    tabTotalHeight = tabBaseHeight + tabLabelHeight
    
    numTabsVerticalP = int ((paperheight - 2*minmarginheight) / tabTotalHeight)
    numTabsHorizontalP = int ((paperwidth - 2*minmarginwidth) / tabWidth)
    numTabsVerticalL = int ((paperwidth - 2*minmarginwidth) / tabWidth)
    numTabsHorizontalL = int ((paperheight - 2*minmarginheight) / tabtotalHeight)
    
    if numTabsVerticalL * numTabsHorizontalL > numTabsVerticalP * numTabsHorizontalP:
        numTabsVertical, numTabsHorizontal = numTabsVerticalL, numTabsHorizontalL
        paperheight, paperwidth = paperwidth, paperheight
    else:
        numTabsVertical, numTabsHorizontal = numTabsVerticalP, numTabsHorizontalP

    horizontalMargin = (paperwidth-numTabsHorizontal*tabWidth)/2
    verticalMargin = (paperheight-numTabsVertical*tabTotalHeight)/2
    
    print "Offset: %fcm h, %fcm v\n" % (horizontalMargin / cm, verticalMargin / cm)

    tabOutline = [(0,0,tabWidth,0),
                  (tabWidth,0,tabWidth,tabTotalHeight),
                  (tabWidth,tabTotalHeight,tabWidth-tabLabelWidth,tabTotalHeight),
                  (tabWidth-tabLabelWidth,tabTotalHeight,tabWidth-tabLabelWidth,tabBaseHeight),
                  (tabWidth-tabLabelWidth,tabBaseHeight,0,tabBaseHeight),
                  (0,tabBaseHeight,0,0)]
    
    try:
        pdfmetrics.registerFont(TTFont('MinionPro-Regular','MinionPro-Regular.ttf'))
        pdfmetrics.registerFont(TTFont('MinionPro-Bold','MinionPro-Bold.ttf'))
    except:
        pdfmetrics.registerFont(TTFont('MinionPro-Regular','OptimusPrincepsSemiBold.ttf'))
        pdfmetrics.registerFont(TTFont('MinionPro-Bold','OptimusPrinceps.ttf'))
    cards = read_card_defs("dominion_cards.txt")
    cards.sort(cmp=lambda x,y: cmp((x.cardset,x.name),(y.cardset,y.name)))
    extras = read_card_extras("dominion_card_extras.txt",cards)
    print '%d cards read' % len(cards)
    sets = {}
    types = {}
    for c in cards:
        sets[c.cardset] = sets.get(c.cardset,0) + 1
        types[c.types] = types.get(c.types,0) + 1
    pprint.pprint(sets)
    pprint.pprint(types)

    if args:
        fname = args[0]
    else:
        fname = "dominion_tabs.pdf"
    c = canvas.Canvas(fname, pagesize=(paperwidth, paperheight))
    #pprint.pprint(c.getAvailableFonts())
    drawCards(c,cards)
    c.save()

