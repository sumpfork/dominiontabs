import unittest
from .. import domdiv
from ..domdiv import cards as domdiv_cards


class TestCardDB(unittest.TestCase):

    def test_cardread(self):
        options, args = domdiv.parse_opts(['commandname'])
        options.data_path = '.'
        cards = domdiv.read_write_card_data(options)
        self.assertEquals(len(cards), 312)
        print set(c.cardset for c in cards)
        valid_cardsets = {
            u'prosperity',
            u'cornucopia extras',
            u'cornucopia',
            u'promo',
            u'adventures extras',
            u'seaside',
            u'adventures',
            u'dark ages',
            u'hinterlands',
            u'dark ages extras',
            u'alchemy',
            u'base',
            u'dominion',
            u'guilds',
            u'intrigue'
        }
        for c in cards:
            self.assertIsInstance(c, domdiv_cards.Card)
            self.assertIn(c.cardset, valid_cardsets)
