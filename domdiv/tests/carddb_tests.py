import unittest
from .. import main
from .. import cards as domdiv_cards


class TestCardDB(unittest.TestCase):

    def test_cardread(self):
        options = main.parse_opts([])
        options.data_path = '.'
        cards = main.read_card_data(options)
        self.assertEquals(len(cards), 524)
        valid_cardsets = {
            u'base',
            u'dominion1stEdition',
            u'dominion2ndEdition',
            u'dominion2ndEditionUpgrade',
            u'intrigue1stEdition',
            u'intrigue2ndEdition',
            u'intrigue2ndEditionUpgrade',
            u'seaside',
            u'alchemy',
            u'prosperity',
            u'cornucopia extras',
            u'cornucopia',
            u'hinterlands',
            u'dark ages',
            u'dark ages extras',
            u'guilds',
            u'adventures',
            u'adventures extras',
            u'empires',
            u'empires extras',
            u'nocturne',
            u'nocturne extras',
            u'promo',
            u'extras',
            u'animals'
        }
        for c in cards:
            self.assertIsInstance(c, domdiv_cards.Card)
            self.assertIn(c.cardset_tag, valid_cardsets)

    def test_languages(self):
        # for now, just test that they load
        options = main.parse_opts(['--language', 'it'])
        options.data_path = '.'
        cards = main.read_card_data(options)
        self.assertTrue(cards, 'Italians cards did not read properly')
        cards = main.add_card_text(options, cards, 'en_us')
        cards = main.add_card_text(options, cards, 'it')
        self.assertIn("Maledizione", [card.name for card in cards])

        options = main.parse_opts(['--language', 'de'])
        options.data_path = '.'
        cards = main.read_card_data(options)
        self.assertTrue(cards, 'German cards did not read properly')
        cards = main.add_card_text(options, cards, 'en_us')
        cards = main.add_card_text(options, cards, 'de')
        self.assertIn("Fluch", [card.name for card in cards])
