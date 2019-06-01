from reportlab.lib.units import cm

from domdiv import main


def test_horizontal():
    # should be the default
    options = main.parse_opts([])
    assert options.orientation == "horizontal"
    main.calculate_layout(options)
    assert options.numDividersHorizontal == 2
    assert options.numDividersVertical == 3
    assert options.dividerWidth == 9.1 * cm
    assert options.labelHeight == 0.9 * cm
    assert options.dividerHeight == 5.9 * cm + options.labelHeight


def test_vertical():
    options = main.parse_opts(["--orientation", "vertical"])
    assert options.orientation == "vertical"
    main.calculate_layout(options)
    assert options.numDividersHorizontal == 3
    assert options.numDividersVertical == 2
    assert options.dividerWidth == 5.9 * cm
    assert options.labelHeight == 0.9 * cm
    assert options.dividerHeight == 9.1 * cm + options.labelHeight


def test_sleeved():
    options = main.parse_opts(["--size", "sleeved"])
    main.calculate_layout(options)
    assert options.dividerWidth == 9.4 * cm
    assert options.labelHeight == 0.9 * cm
    assert options.dividerHeight == 6.15 * cm + options.labelHeight


def test_cost():
    options = main.parse_opts([])
    options = main.clean_opts(options)
    assert options.cost == ["tab"]

    options = main.parse_opts(["--cost=tab"])
    options = main.clean_opts(options)
    assert options.cost == ["tab"]

    options = main.parse_opts(["--cost=body-top"])
    options = main.clean_opts(options)
    assert options.cost == ["body-top"]

    options = main.parse_opts(["--cost=hide"])
    options = main.clean_opts(options)
    assert options.cost == ["hide"]

    options = main.parse_opts(["--cost=tab", "--cost=body-top"])
    options = main.clean_opts(options)
    assert set(options.cost) == {"tab", "body-top"}


def test_set_icon():
    options = main.parse_opts([])
    options = main.clean_opts(options)
    assert options.set_icon == ["tab"]

    options = main.parse_opts(["--set-icon=tab"])
    options = main.clean_opts(options)
    assert options.set_icon == ["tab"]

    options = main.parse_opts(["--set-icon=body-top"])
    options = main.clean_opts(options)
    assert options.set_icon == ["body-top"]

    options = main.parse_opts(["--set-icon=hide"])
    options = main.clean_opts(options)
    assert options.set_icon == ["hide"]

    options = main.parse_opts(["--set-icon=tab", "--set-icon=body-top"])
    options = main.clean_opts(options)
    assert set(options.set_icon) == {"tab", "body-top"}
