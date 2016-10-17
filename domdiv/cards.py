import json
import os
from reportlab.lib.units import cm


def getType(typespec):
    return cardTypes[tuple(typespec)]

setImages = {
    'dominion': 'base_set.png',
    'intrigue': 'intrigue_set.png',
    'seaside': 'seaside_set.png',
    'prosperity': 'prosperity_set.png',
    'alchemy': 'alchemy_set.png',
    'cornucopia': 'cornucopia_set.png',
    'cornucopia extras': 'cornucopia_set.png',
    'hinterlands': 'hinterlands_set.png',
    'dark ages': 'dark_ages_set.png',
    'dark ages extras': 'dark_ages_set.png',
    'guilds': 'guilds_set.png',
    'adventures': 'adventures_set.png',
    'adventures extras': 'adventures_set.png',
    'empires': 'empires_set.png',
    'empires extras': 'empires_set.png'
}
promoImages = {
    'walled village': 'walled_village_set.png',
    'stash': 'stash_set.png',
    'governor': 'governor_set.png',
    'black market': 'black_market_set.png',
    'envoy': 'envoy_set.png',
    'prince': 'prince_set.png',
    'summon': 'promo_set.png',
    'sauna': 'promo_set.png',
    'avanto': 'promo_set.png',
    'sauna \/ avanto': 'promo_set.png'
}

setTextIcons = {
    'dominion': 'D',
    'intrigue': 'I',
    'seaside': 'S',
    'prosperity': 'P',
    'alchemy': 'A',
    'cornucopia': 'C',
    'cornucopia extras': 'C',
    'hinterlands': 'H',
    'dark ages': 'DA',
    'dark ages extras': 'DA',
    'guilds': 'G',
    'adventures': 'Ad',
    'adventures extras': 'Ad',
    'empires': 'E',
    'empires extras': 'E'
}

promoTextIcons = {
    'walled village': '',
    'stash': '',
    'governor': '',
    'black market': '',
    'envoy': '',
    'prince': ''
}

language_mapping = None


class Card(object):

    language_mapping = None

    class CardJSONEncoder(json.JSONEncoder):

        def default(self, obj):
            if isinstance(obj, Card):
                return obj.__dict__
            return json.JSONEncoder.default(self, obj)

    @staticmethod
    def decode_json(obj):
        return Card(**obj)

    @classmethod
    def getSetImage(cls, setName, cardName):
        if setName in setImages:
            return setImages[setName]
        if cardName.lower() in promoImages:
            return promoImages[cardName.lower()]
        if setName in cls.language_mapping:
            trans = cls.language_mapping[setName]
            if trans in setImages:
                return setImages[trans]
        if cardName in cls.language_mapping:
            trans = cls.language_mapping[cardName]
            if trans.lower() in promoImages:
                return promoImages[trans.lower()]
        return None

    @classmethod
    def getSetText(cls, setName, cardName):
        if setName in setTextIcons:
            return setTextIcons[setName]
        if cardName.lower() in promoTextIcons:
            return promoTextIcons[cardName.lower()]
        return None

    def __init__(self, name, cardset, types, cost, description='', potcost=0, debtcost=0, extra='', count=-1):
        self.name = name.strip()
        self.cardset = cardset.strip()
        self.types = types
        self.cost = cost
        self.potcost = potcost
        self.debtcost = debtcost
        self.description = description
        self.extra = extra
        if count < 0:
            self.count = getType(self.types).getTypeDefaultCardCount()
        else:
            self.count = count

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

    def isExpansion(self):
        return 'Expansion' in self.getType().getTypeNames()

    def isEvent(self):
        return 'Event' in self.getType().getTypeNames()

    def isLandmark(self):
        return 'Landmark' in self.getType().getTypeNames()

    def isPrize(self):
        return 'Prize' in self.getType().getTypeNames()

    def isType(self, what):
        return what in self.getType().getTypeNames()

    def setImage(self):
        setImage = Card.getSetImage(self.cardset, self.name)
        if setImage is None and self.cardset != 'base':
            print 'warning, no set image for set "{}" card "{}"'.format(self.cardset, self.name)
        return setImage

    def setTextIcon(self):
        setTextIcon = Card.getSetText(self.cardset, self.name)
        if setTextIcon is None and self.cardset != 'base':
            print 'warning, no set text for set "{}" card "{}"'.format(self.cardset, self.name)
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
