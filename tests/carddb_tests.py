import unittest
from .. import domdiv
from ..domdiv import cards as domdiv_cards


class TestCardDB(unittest.TestCase):

    def test_cardread(self):
        options, args = domdiv.parse_opts(['commandname'])
        options.data_path = '.'
        cards = domdiv.read_write_card_data(options)
        self.assertEquals(len(cards), 348)
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
            u'intrigue',
            u'empires'
        }
        for c in cards:
            self.assertIsInstance(c, domdiv_cards.Card)
            self.assertIn(c.cardset, valid_cardsets)

    def test_languages(self):
        # for now, just test that they load
        options, args = domdiv.parse_opts(['commandname', '--language', 'it'])
        options.data_path = '.'
        cards = domdiv.read_write_card_data(options)
        self.assertTrue(cards, 'Italians cards did not read properly')
        self.assertIn("Maledizione", [card.name for card in cards])

        options, args = domdiv.parse_opts(['commandname', '--language', 'de'])
        options.data_path = '.'
        cards = domdiv.read_write_card_data(options)
        self.assertTrue(cards, 'German cards did not read properly')
        self.assertIn("Fluch", [card.name for card in cards])
