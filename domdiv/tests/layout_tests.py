import unittest
from .. import main
from reportlab.lib.units import cm


class TestLayout(unittest.TestCase):

    def test_horizontal(self):
        # should be the default
        options = main.parse_opts([])
        self.assertEquals(options.orientation, 'horizontal')
        main.calculate_layout(options)
        self.assertEquals(options.numDividersHorizontal, 2)
        self.assertEquals(options.numDividersVertical, 3)
        self.assertEquals(options.dividerWidth, 9.1 * cm)
        self.assertEquals(options.labelHeight, 0.9 * cm)
        self.assertEquals(options.dividerHeight, 5.9 * cm + options.labelHeight)

    def test_vertical(self):
        options = main.parse_opts(['--orientation', 'vertical'])
        self.assertEquals(options.orientation, 'vertical')
        main.calculate_layout(options)
        self.assertEquals(options.numDividersHorizontal, 3)
        self.assertEquals(options.numDividersVertical, 2)
        self.assertEquals(options.dividerWidth, 5.9 * cm)
        self.assertEquals(options.labelHeight, 0.9 * cm)
        self.assertEquals(options.dividerHeight, 9.1 * cm + options.labelHeight)

    def test_sleeved(self):
        options = main.parse_opts(['--size', 'sleeved'])
        main.calculate_layout(options)
        self.assertEquals(options.dividerWidth, 9.4 * cm)
        self.assertEquals(options.labelHeight, 0.9 * cm)
        self.assertEquals(options.dividerHeight, 6.15 * cm + options.labelHeight)
