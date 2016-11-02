import json
import os
from reportlab.lib.units import cm


def getType(typespec):
    return cardTypes[tuple(typespec)]


class Card(object):

    sets = None

    class CardJSONEncoder(json.JSONEncoder):

        def default(self, obj):
            if isinstance(obj, Card):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)

    @staticmethod
    def decode_json(obj):
        return Card(**obj)

    def __init__(self, name=None, cardset='', types=None, cost='', description='',
                 potcost=0, debtcost=0, extra='', count=-1, card_tag='missing card_tag',
                 cardset_tags=None, group_tag='', image=None, text_icon=None, cardset_tag=''):

        if types is None:
            types = []  # make sure types is a list
        if cardset_tags is None:
            cardset_tags = []  # make sure cardset_tags is a list
        if name is None:
            name = card_tag  # make sure there is a meaningful default name

        self.name = name.strip()
        self.cardset = cardset.strip()
        self.types = types
        self.cost = cost
        self.description = description
        self.potcost = potcost
        self.debtcost = debtcost
        self.extra = extra
        self.card_tag = card_tag
        self.cardset_tags = cardset_tags
        self.group_tag = group_tag
        self.image = image
        self.text_icon = text_icon
        self.cardset_tag = cardset_tag
        if count < 0:
            self.count = getType(self.types).getTypeDefaultCardCount()
        else:
            self.count = int(count)

    def getCardCount(self):
        return self.count

    def setCardCount(self, value):
        self.count = value

    def getStackHeight(self, thickness):
        # return height of the stacked cards in cm.  Using hight in cm of a stack of 60 Copper cards as thickness.
        return self.count * cm * (thickness / 60.0) + 2

    def getType(self):
        return getType(self.types)

    def __repr__(self):
        return '"' + self.name + '"'

    def toString(self):
        return self.name + ' ' + self.cardset + ' ' + '-'.join(self.types)\
            + ' ' + self.cost + ' ' + self.description + ' ' + self.extra

    def isType(self, what):
        return what in self.getType().getTypeNames()

    def isExpansion(self):
        return self.isType('Expansion')

    def isEvent(self):
        return self.isType('Event')

    def isLandmark(self):
        return self.isType('Landmark')

    def isPrize(self):
        return self.isType('Prize')

    def get_total_cost(self, c):
        # Return a tuple that represents the total cost of card c
        # Make any cost with a '*' larger than anything else
        # convert cost (a string) into a number
        if '*' in c.cost:
            c_cost = 9999  # make it a really big number
        else:
            try:
                c_cost = int(c.cost)
            except ValueError:
                c_cost = 9999  # can't, so make it a really big number

        return c_cost, c.potcost, c.debtcost

    def set_lowest_cost(self, other):
        # set self cost fields to the lower of the two's total cost
        self_cost = self.get_total_cost(self)
        other_cost = self.get_total_cost(other)
        if other_cost < self_cost:
            self.cost = other.cost
            self.potcost = other.potcost
            self.debtcost = other.debtcost

    def setImage(self):
        setImage = None
        if self.image is not None:
            setImage = self.image
        else:
            if self.cardset_tag in Card.sets:
                if 'image' in Card.sets[self.cardset_tag]:
                    setImage = Card.sets[self.cardset_tag]['image']

        if setImage is None and self.cardset_tag != 'base':
            print 'warning, no set image for set "{}", card "{}"'.format(self.cardset, self.name)
        return setImage

    def setTextIcon(self):
        setTextIcon = None
        if self.text_icon:
            setTextIcon = self.text_icon
        else:
            if self.cardset_tag in Card.sets:
                if 'text_icon' in Card.sets[self.cardset_tag]:
                    setTextIcon = Card.sets[self.cardset_tag]['text_icon']

        if setTextIcon is None and self.cardset != 'base':
            print 'warning, no set text for set "{}", card "{}"'.format(self.cardset, self.name)
        return setTextIcon

    def isBlank(self):
        return False


class BlankCard(Card):

    def __init__(self, num):
        Card.__init__(self, str(num), 'extra', ('Blank',), 0)

    def isBlank(self):
        return True


class CardType(object):

    def __init__(self, typeNames, tabImageFile, defaultCardCount=10, tabTextHeightOffset=0, tabCostHeightOffset=-1):
        self.typeNames = typeNames
        self.tabImageFile = tabImageFile
        self.tabTextHeightOffset = tabTextHeightOffset
        self.tabCostHeightOffset = tabCostHeightOffset
        self.defaultCardCount = defaultCardCount

    def getTypeDefaultCardCount(self):
        return self.defaultCardCount

    def getTypeNames(self):
        return self.typeNames

    def getTabImageFile(self):
        if not self.tabImageFile:
            return None
        return self.tabImageFile

    def getNoCoinTabImageFile(self):
        if not self.tabImageFile:
            return None
        return ''.join(os.path.splitext(self.tabImageFile)[0] + '_nc' + os.path.splitext(self.tabImageFile)[1])

    def getTabTextHeightOffset(self):
        return self.tabTextHeightOffset

    def getTabCostHeightOffset(self):
        return self.tabCostHeightOffset

cardTypes = [
    CardType(('Action',), 'action.png'),
    CardType(('Action', 'Attack'), 'action.png'),
    CardType(('Action', 'Attack', 'Prize'), 'action.png', 1),
    CardType(('Action', 'Reaction'), 'reaction.png'),
    CardType(('Action', 'Victory'), 'action-victory.png', 12),
    CardType(('Action', 'Duration'), 'duration.png', 10),
    CardType(('Action', 'Duration', 'Reaction'), 'duration-reaction.png'),
    CardType(('Action', 'Attack', 'Duration'), 'duration.png'),
    CardType(('Action', 'Looter'), 'action.png'),
    CardType(('Action', 'Prize'), 'action.png', 1),
    CardType(('Action', 'Ruins'), 'ruins.png', 10, 0, 1),
    CardType(('Action', 'Shelter'), 'action-shelter.png', 6),
    CardType(('Action', 'Attack', 'Duration'), 'duration.png'),
    CardType(('Action', 'Attack', 'Looter'), 'action.png'),
    CardType(('Action', 'Attack', 'Traveller'), 'action.png', 5),
    CardType(('Action', 'Reserve'), 'reserve.png', 10),
    CardType(('Action', 'Reserve', 'Victory'), 'reserve-victory.png', 12),
    CardType(('Action', 'Traveller'), 'action.png', 5),
    CardType(('Action', 'Gathering'), 'action.png'),
    CardType(('Action', 'Treasure'), 'action-treasure.png'),
    CardType(('Prize',), 'action.png', 1),
    CardType(('Event',), 'event.png', 1),
    CardType(('Reaction',), 'reaction.png'),
    CardType(('Reaction', 'Shelter'), 'reaction-shelter.png', 6),
    CardType(('Treasure',), 'treasure.png', 10, 3, 0),
    CardType(('Treasure', 'Attack'), 'treasure.png'),
    CardType(('Treasure', 'Victory'), 'treasure-victory.png', 12),
    CardType(('Treasure', 'Prize'), 'treasure.png', 1, 3, 0),
    CardType(('Treasure', 'Reaction'), 'treasure-reaction.png', 10, 0, 1),
    CardType(('Treasure', 'Reserve'), 'reserve-treasure.png'),
    CardType(('Victory',), 'victory.png', 12),
    CardType(('Victory', 'Reaction'), 'victory-reaction.png', 12, 0, 1),
    CardType(('Victory', 'Shelter'), 'victory-shelter.png', 6),
    CardType(('Victory', 'Castle'), 'victory.png', 12),
    CardType(('Curse',), 'curse.png', 30, 3),
    CardType(('Trash',), 'action.png', 1),
    CardType(('Prizes',), 'action.png', 0),
    CardType(('Events',), 'event.png', 0),
    CardType(('Shelters',), 'shelter.png', 0),
    CardType(('Expansion',), 'expansion.png', 0, 4),
    CardType(('Blank',), ''),
    CardType(('Landmark',), 'landmark.png', 1),
    CardType(('Landmarks',), 'landmark.png', 0)
]

cardTypes = dict(((c.getTypeNames(), c) for c in cardTypes))
