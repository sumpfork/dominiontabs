import json
import os


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
    'summon': 'summon_set.png'
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

    def __init__(self, name, cardset, types, cost, description='', potcost=0, debtcost=0, extra=''):
        self.name = name.strip()
        self.cardset = cardset.strip()
        self.types = types
        self.cost = cost
        self.potcost = potcost
        self.debtcost = debtcost
        self.description = description
        self.extra = extra

    def getType(self):
        return getType(self.types)

    def __repr__(self):
        return '"' + self.name + '"'

    def toString(self):
        return self.name + ' ' + self.cardset + ' ' + '-'.join(self.types)\
            + ' ' + self.cost + ' ' + self.description + ' ' + self.extra

    def isExpansion(self):
        return self.getType().getTypeNames() == ('Expansion',)

    def isEvent(self):
        return self.getType().getTypeNames() == ('Event',)

    def isLandmark(self):
        return self.getType().getTypeNames() == ('Landmark',)

    def isPrize(self):
        return 'Prize' in self.getType().getTypeNames()

    def setImage(self):
        setImage = Card.getSetImage(self.cardset, self.name)
        if setImage is None and self.cardset not in ['base', 'extra'] and not self.isExpansion():
            print 'warning, no set image for set "%s" card "%s"' % (self.cardset, self.name)
            setImages[self.cardset] = 0
            promoImages[self.name.lower()] = 0
        return setImage

    def setTextIcon(self):
        setTextIcon = Card.getSetText(self.cardset, self.name)
        if setTextIcon is None and self.cardset not in ['base', 'extra'] and not self.isExpansion():
            print 'warning, no set text for set "%s" card "%s"' % (self.cardset, self.name)
            setTextIcons[self.cardset] = 0
            promoTextIcons[self.name.lower()] = 0
        return setTextIcon

    def isBlank(self):
        return False


class BlankCard(Card):

    def __init__(self, num):
        Card.__init__(self, str(num), 'extra', ('Blank',), 0)

    def isBlank(self):
        return True


class CardType(object):

    def __init__(self, typeNames, tabImageFile, tabTextHeightOffset=0, tabCostHeightOffset=-1):
        self.typeNames = typeNames
        self.tabImageFile = tabImageFile
        self.tabTextHeightOffset = tabTextHeightOffset
        self.tabCostHeightOffset = tabCostHeightOffset

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
    CardType(('Action', 'Attack', 'Prize'), 'action.png'),
    CardType(('Action', 'Reaction'), 'reaction.png'),
    CardType(('Action', 'Victory'), 'action-victory.png'),
    CardType(('Action', 'Duration'), 'duration.png'),
    CardType(('Action', 'Duration', 'Reaction'), 'duration-reaction.png'),
    CardType(('Action', 'Attack', 'Duration'), 'duration.png'),
    CardType(('Action', 'Looter'), 'action.png'),
    CardType(('Action', 'Prize'), 'action.png'),
    CardType(('Action', 'Ruins'), 'ruins.png', 0, 1),
    CardType(('Action', 'Shelter'), 'action-shelter.png'),
    CardType(('Action', 'Attack', 'Duration'), 'duration.png'),
    CardType(('Action', 'Attack', 'Looter'), 'action.png'),
    CardType(('Action', 'Attack', 'Traveller'), 'action.png'),
    CardType(('Action', 'Reserve'), 'reserve.png'),
    CardType(('Action', 'Reserve', 'Victory'), 'reserve-victory.png'),
    CardType(('Action', 'Traveller'), 'action.png'),
    CardType(('Action', 'Gathering'), 'action.png'),
    CardType(('Action', 'Treasure'), 'treasure.png'),
    CardType(('Prize',), 'action.png'),
    CardType(('Event',), 'event.png'),
    CardType(('Reaction',), 'reaction.png'),
    CardType(('Reaction', 'Shelter'), 'reaction-shelter.png'),
    CardType(('Treasure',), 'treasure.png', 3, 0),
    CardType(('Treasure', 'Attack'), 'treasure.png'),
    CardType(('Treasure', 'Victory'), 'treasure-victory.png'),
    CardType(('Treasure', 'Prize'), 'treasure.png', 3, 0),
    CardType(('Treasure', 'Reaction'), 'treasure-reaction.png', 0, 1),
    CardType(('Treasure', 'Reserve'), 'reserve-treasure.png'),
    CardType(('Victory',), 'victory.png'),
    CardType(('Victory', 'Reaction'), 'victory-reaction.png', 0, 1),
    CardType(('Victory', 'Shelter'), 'victory-shelter.png'),
    CardType(('Victory', 'Castle'), 'victory.png'),
    CardType(('Curse',), 'curse.png', 3),
    CardType(('Expansion',), 'expansion.png', 4),
    CardType(('Blank',), ''),
    CardType(('Landmark',), 'landmark.png')
]

cardTypes = dict(((c.getTypeNames(), c) for c in cardTypes))
