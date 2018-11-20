from reportlab.lib.units import cm

from .. import main


def test_horizontal():
    # should be the default
    options = main.parse_opts([])
    assert options.orientation == 'horizontal'
    main.calculate_layout(options)
    assert options.numDividersHorizontal == 2
    assert options.numDividersVertical == 3
    assert options.dividerWidth == 9.1 * cm
    assert options.labelHeight == 0.9 * cm
    assert options.dividerHeight == 5.9 * cm + options.labelHeight


def test_vertical():
    options = main.parse_opts(['--orientation', 'vertical'])
    assert options.orientation == 'vertical'
    main.calculate_layout(options)
    assert options.numDividersHorizontal == 3
    assert options.numDividersVertical == 2
    assert options.dividerWidth == 5.9 * cm
    assert options.labelHeight == 0.9 * cm
    assert options.dividerHeight == 9.1 * cm + options.labelHeight


def test_sleeved():
    options = main.parse_opts(['--size', 'sleeved'])
    main.calculate_layout(options)
    assert options.dividerWidth == 9.4 * cm
    assert options.labelHeight == 0.9 * cm
    assert options.dividerHeight == 6.15 * cm + options.labelHeight
