import unittest
from .. import main


class TestTextTabs(unittest.TestCase):

    ####################
    # Card Text and Tab Default Test
    ####################
    def test_text_tabs_default(self):
        # should be the default
        options = main.parse_opts([])
        self.assertEquals(options.text_front, 'card')
        self.assertEquals(options.text_back, 'rules')
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'right-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'left')

    ####################
    # Card Text Tests
    ####################
    def test_text_card_rules(self):
        options = main.parse_opts(
            ['--front', 'card', '--back', 'rules'])
        self.assertEquals(options.text_front, 'card')
        self.assertEquals(options.text_back, 'rules')

    def test_text_card_blank(self):
        options = main.parse_opts(
            ['--front', 'card', '--back', 'blank'])
        self.assertEquals(options.text_front, 'card')
        self.assertEquals(options.text_back, 'blank')

    def test_text_card_card(self):
        options = main.parse_opts(
            ['--front', 'card', '--back', 'card'])
        self.assertEquals(options.text_front, 'card')
        self.assertEquals(options.text_back, 'card')

    def test_text_card_none(self):
        options = main.parse_opts(
            ['--front', 'card', '--back', 'none'])
        self.assertEquals(options.text_front, 'card')
        self.assertEquals(options.text_back, 'none')

    def test_text_rules_rules(self):
        options = main.parse_opts(
            ['--front', 'rules', '--back', 'rules'])
        self.assertEquals(options.text_front, 'rules')
        self.assertEquals(options.text_back, 'rules')

    def test_text_rules_blank(self):
        options = main.parse_opts(
            ['--front', 'rules', '--back', 'blank'])
        self.assertEquals(options.text_front, 'rules')
        self.assertEquals(options.text_back, 'blank')

    def test_text_rules_card(self):
        options = main.parse_opts(
            ['--front', 'rules', '--back', 'card'])
        self.assertEquals(options.text_front, 'rules')
        self.assertEquals(options.text_back, 'card')

    def test_text_rules_none(self):
        options = main.parse_opts(
            ['--front', 'rules', '--back', 'none'])
        self.assertEquals(options.text_front, 'rules')
        self.assertEquals(options.text_back, 'none')

    def test_text_blank_rules(self):
        options = main.parse_opts(
            ['--front', 'blank', '--back', 'rules'])
        self.assertEquals(options.text_front, 'blank')
        self.assertEquals(options.text_back, 'rules')

    def test_text_blank_blank(self):
        options = main.parse_opts(
            ['--front', 'blank', '--back', 'blank'])
        self.assertEquals(options.text_front, 'blank')
        self.assertEquals(options.text_back, 'blank')

    def test_text_blank_card(self):
        options = main.parse_opts(
            ['--front', 'blank', '--back', 'card'])
        self.assertEquals(options.text_front, 'blank')
        self.assertEquals(options.text_back, 'card')

    def test_text_blank_none(self):
        options = main.parse_opts(
            ['--front', 'blank', '--back', 'none'])
        self.assertEquals(options.text_front, 'blank')
        self.assertEquals(options.text_back, 'none')

    ####################
    # Card Tab Tests
    ####################
    # --tab_name_align left
    def test_tab_left_left(self):
        options = main.parse_opts(
            ['--tab_name_align', 'left', '--tab_side', 'left'])
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'left')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'left')

    def test_tab_left_right(self):
        options = main.parse_opts(
            ['--tab_name_align', 'left', '--tab_side', 'right'])
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'right')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'right')

    def test_tab_left_leftalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'left', '--tab_side',
             'left-alternate'])
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'left-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'left-alternate')

    def test_tab_left_rightalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'left', '--tab_side',
             'right-alternate'])
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'right-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'right-alternate')

    def test_tab_left_full(self):
        options = main.parse_opts(
            ['--tab_name_align', 'left', '--tab_side', 'full'])
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'full')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'left')
        self.assertEquals(options.tab_side, 'full')

        # --tab_name_align right
    def test_tab_right_left(self):
        options = main.parse_opts(
            ['--tab_name_align', 'right', '--tab_side', 'left'])
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'left')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'left')

    def test_tab_right_right(self):
        options = main.parse_opts(['--tab_name_align',
                                   'right', '--tab_side', 'right'])
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'right')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'right')

    def test_tab_right_leftalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'right', '--tab_side',
             'left-alternate'])
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'left-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'left-alternate')

    def test_tab_right_rightalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'right', '--tab_side',
             'right-alternate'])
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'right-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'right-alternate')

    def test_tab_right_full(self):
        options = main.parse_opts(
            ['--tab_name_align', 'right', '--tab_side', 'full'])
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'full')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'right')
        self.assertEquals(options.tab_side, 'full')

    # --tab_name_align edge
    def test_tab_edge_left(self):
        options = main.parse_opts(
            ['--tab_name_align', 'edge', '--tab_side', 'left'])
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'left')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'left')

    def test_tab_edge_right(self):
        options = main.parse_opts(
            ['--tab_name_align', 'edge', '--tab_side', 'right'])
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'right')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'right')

    def test_tab_edge_leftalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'edge', '--tab_side',
             'left-alternate'])
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'left-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'left-alternate')

    def test_tab_edge_rightalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'edge', '--tab_side',
             'right-alternate'])
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'right-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'right-alternate')

    def test_tab_edge_full(self):
        options = main.parse_opts(
            ['--tab_name_align', 'edge', '--tab_side', 'full'])
        self.assertEquals(options.tab_name_align, 'edge')
        self.assertEquals(options.tab_side, 'full')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align,
                          'left')  # special check for odd condition
        self.assertEquals(options.tab_side, 'full')

        # --tab_name_align centre
    def test_tab_centre_left(self):
        options = main.parse_opts(['--tab_name_align',
                                   'centre', '--tab_side', 'left'])
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'left')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'left')

    def test_tab_centre_right(self):
        options = main.parse_opts(['--tab_name_align',
                                   'centre', '--tab_side', 'right'])
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'right')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'right')

    def test_tab_centre_leftalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'centre', '--tab_side',
             'left-alternate'])
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'left-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'left-alternate')

    def test_tab_centre_rightalt(self):
        options = main.parse_opts(
            ['--tab_name_align', 'centre', '--tab_side',
             'right-alternate'])
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'right-alternate')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'right-alternate')

    def test_tab_centre_full(self):
        options = main.parse_opts(['--tab_name_align',
                                   'centre', '--tab_side', 'full'])
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'full')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align, 'centre')
        self.assertEquals(options.tab_side, 'full')

    # --tab_name_align center.  Just do one since this is an alias to centre
    def test_tab_center_left(self):
        options = main.parse_opts(['--tab_name_align',
                                   'center', '--tab_side', 'left'])
        self.assertEquals(options.tab_name_align, 'center')
        self.assertEquals(options.tab_side, 'left')
        main.calculate_layout(options)
        self.assertEquals(options.tab_name_align,
                          'centre')  # check for change in value
        self.assertEquals(options.tab_side, 'left')
