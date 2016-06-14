import unittest
from .. import domdiv
from reportlab.lib.units import cm


class TestLayout(unittest.TestCase):

    def test_horizontal(self):
        # should be the default
        options, args = domdiv.parse_opts(['commandname'])
        self.assertEquals(options.orientation, 'horizontal')
        domdiv.calculate_layout(options)
        self.assertEquals(options.numDividersHorizontal, 2)
        self.assertEquals(options.numDividersVertical, 3)
        self.assertEquals(options.dividerWidth, 9.1 * cm)
        self.assertEquals(options.labelHeight, 0.9 * cm)
        self.assertEquals(options.dividerHeight, 5.9 * cm + options.labelHeight)

    def test_vertical(self):
        options, args = domdiv.parse_opts(['commandname', '--orientation', 'vertical'])
        self.assertEquals(options.orientation, 'vertical')
        domdiv.calculate_layout(options)
        self.assertEquals(options.numDividersHorizontal, 3)
        self.assertEquals(options.numDividersVertical, 2)
        self.assertEquals(options.dividerWidth, 5.9 * cm)
        self.assertEquals(options.labelHeight, 0.9 * cm)
        self.assertEquals(options.dividerHeight, 9.1 * cm + options.labelHeight)

    def test_sleeved(self):
        options, args = domdiv.parse_opts(['commandname', '--size', 'sleeved'])
        domdiv.calculate_layout(options)
        self.assertEquals(options.dividerWidth, 9.4 * cm)
        self.assertEquals(options.labelHeight, 0.9 * cm)
        self.assertEquals(options.dividerHeight, 6.15 * cm + options.labelHeight)

