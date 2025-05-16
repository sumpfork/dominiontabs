from domdiv import config_options, main


####################
# Card Text and Tab Default Test
####################
def test_text_tabs_default():
    # should be the default
    options = config_options.parse_opts([])
    options = config_options.clean_opts(options)
    assert options.text_front == "card"
    assert options.text_back == "rules"
    assert options.tab_name_align == "left"
    assert options.tab_side == "right-alternate"
    main.calculate_layout(options)
    assert options.tab_name_align == "left"


####################
# Card Text Tests
####################


def test_text_card_rules():
    options = config_options.parse_opts(["--front", "card", "--back", "rules"])
    options = config_options.clean_opts(options)
    assert options.text_front == "card"
    assert options.text_back == "rules"


def test_text_card_blank():
    options = config_options.parse_opts(["--front", "card", "--back", "blank"])
    options = config_options.clean_opts(options)
    assert options.text_front == "card"
    assert options.text_back == "blank"


def test_text_card_card():
    options = config_options.parse_opts(["--front", "card", "--back", "card"])
    options = config_options.clean_opts(options)
    assert options.text_front == "card"
    assert options.text_back == "card"


def test_text_card_none():
    options = config_options.parse_opts(["--front", "card", "--back", "none"])
    options = config_options.clean_opts(options)
    assert options.text_front == "card"
    assert options.text_back == "none"


def test_text_rules_rules():
    options = config_options.parse_opts(["--front", "rules", "--back", "rules"])
    options = config_options.clean_opts(options)
    assert options.text_front == "rules"
    assert options.text_back == "rules"


def test_text_rules_blank():
    options = config_options.parse_opts(["--front", "rules", "--back", "blank"])
    options = config_options.clean_opts(options)
    assert options.text_front == "rules"
    assert options.text_back == "blank"


def test_text_rules_card():
    options = config_options.parse_opts(["--front", "rules", "--back", "card"])
    options = config_options.clean_opts(options)
    assert options.text_front == "rules"
    assert options.text_back == "card"


def test_text_rules_none():
    options = config_options.parse_opts(["--front", "rules", "--back", "none"])
    options = config_options.clean_opts(options)
    assert options.text_front == "rules"
    assert options.text_back == "none"


def test_text_blank_rules():
    options = config_options.parse_opts(["--front", "blank", "--back", "rules"])
    options = config_options.clean_opts(options)
    assert options.text_front == "blank"
    assert options.text_back == "rules"


def test_text_blank_blank():
    options = config_options.parse_opts(["--front", "blank", "--back", "blank"])
    options = config_options.clean_opts(options)
    assert options.text_front == "blank"
    assert options.text_back == "blank"


def test_text_blank_card():
    options = config_options.parse_opts(["--front", "blank", "--back", "card"])
    options = config_options.clean_opts(options)
    assert options.text_front == "blank"
    assert options.text_back == "card"


def test_text_blank_none():
    options = config_options.parse_opts(["--front", "blank", "--back", "none"])
    options = config_options.clean_opts(options)
    assert options.text_front == "blank"
    assert options.text_back == "none"


####################
# Card Tab Tests
####################
# --tab_name_align left


def test_tab_left_left():
    options = config_options.parse_opts(
        ["--tab-name-align", "left", "--tab-side", "left"]
    )
    assert options.tab_name_align == "left"
    assert options.tab_side == "left"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "left"
    assert options.tab_side == "left"


def test_tab_left_right():
    options = config_options.parse_opts(
        ["--tab-name-align", "left", "--tab-side", "right"]
    )
    assert options.tab_name_align == "left"
    assert options.tab_side == "right"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "left"
    assert options.tab_side == "right"


def test_tab_left_leftalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "left", "--tab-side", "left-alternate"]
    )
    assert options.tab_name_align == "left"
    assert options.tab_side == "left-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "left"
    assert options.tab_side == "left-alternate"


def test_tab_left_rightalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "left", "--tab-side", "right-alternate"]
    )
    assert options.tab_name_align == "left"
    assert options.tab_side == "right-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "left"
    assert options.tab_side == "right-alternate"


def test_tab_left_full():
    options = config_options.parse_opts(
        ["--tab-name-align", "left", "--tab-side", "full"]
    )
    assert options.tab_name_align == "left"
    assert options.tab_side == "full"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "left"
    assert options.tab_side == "full"

    # --tab_name_align right


def test_tab_right_left():
    options = config_options.parse_opts(
        ["--tab-name-align", "right", "--tab-side", "left"]
    )
    assert options.tab_name_align == "right"
    assert options.tab_side == "left"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "right"
    assert options.tab_side == "left"


def test_tab_right_right():
    options = config_options.parse_opts(
        ["--tab-name-align", "right", "--tab-side", "right"]
    )
    assert options.tab_name_align == "right"
    assert options.tab_side == "right"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "right"
    assert options.tab_side == "right"


def test_tab_right_leftalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "right", "--tab-side", "left-alternate"]
    )
    assert options.tab_name_align == "right"
    assert options.tab_side == "left-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "right"
    assert options.tab_side == "left-alternate"


def test_tab_right_rightalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "right", "--tab-side", "right-alternate"]
    )
    assert options.tab_name_align == "right"
    assert options.tab_side == "right-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "right"
    assert options.tab_side == "right-alternate"


def test_tab_right_full():
    options = config_options.parse_opts(
        ["--tab-name-align", "right", "--tab-side", "full"]
    )
    assert options.tab_name_align == "right"
    assert options.tab_side == "full"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "right"
    assert options.tab_side == "full"


# --tab_name_align edge


def test_tab_edge_left():
    options = config_options.parse_opts(
        ["--tab-name-align", "edge", "--tab-side", "left"]
    )
    assert options.tab_name_align == "edge"
    assert options.tab_side == "left"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "edge"
    assert options.tab_side == "left"


def test_tab_edge_right():
    options = config_options.parse_opts(
        ["--tab-name-align", "edge", "--tab-side", "right"]
    )
    assert options.tab_name_align == "edge"
    assert options.tab_side == "right"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "edge"
    assert options.tab_side == "right"


def test_tab_edge_leftalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "edge", "--tab-side", "left-alternate"]
    )
    assert options.tab_name_align == "edge"
    assert options.tab_side == "left-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "edge"
    assert options.tab_side == "left-alternate"


def test_tab_edge_rightalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "edge", "--tab-side", "right-alternate"]
    )
    assert options.tab_name_align == "edge"
    assert options.tab_side == "right-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "edge"
    assert options.tab_side == "right-alternate"


def test_tab_edge_full():
    options = config_options.parse_opts(
        ["--tab-name-align", "edge", "--tab-side", "full"]
    )
    assert options.tab_name_align == "edge"
    assert options.tab_side == "full"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "left"  # special check for odd condition
    assert options.tab_side == "full"

    # --tab_name_align centre


def test_tab_centre_left():
    options = config_options.parse_opts(
        ["--tab-name-align", "centre", "--tab-side", "left"]
    )
    assert options.tab_name_align == "centre"
    assert options.tab_side == "left"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "centre"
    assert options.tab_side == "left"


def test_tab_centre_right():
    options = config_options.parse_opts(
        ["--tab-name-align", "centre", "--tab-side", "right"]
    )
    assert options.tab_name_align == "centre"
    assert options.tab_side == "right"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "centre"
    assert options.tab_side == "right"


def test_tab_centre_leftalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "centre", "--tab-side", "left-alternate"]
    )
    assert options.tab_name_align == "centre"
    assert options.tab_side == "left-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "centre"
    assert options.tab_side == "left-alternate"


def test_tab_centre_rightalt():
    options = config_options.parse_opts(
        ["--tab-name-align", "centre", "--tab-side", "right-alternate"]
    )
    assert options.tab_name_align == "centre"
    assert options.tab_side == "right-alternate"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "centre"
    assert options.tab_side == "right-alternate"


def test_tab_centre_full():
    options = config_options.parse_opts(
        ["--tab-name-align", "centre", "--tab-side", "full"]
    )
    assert options.tab_name_align == "centre"
    assert options.tab_side == "full"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "centre"
    assert options.tab_side == "full"


# --tab_name_align center.  Just do one since this is an alias to centre


def test_tab_center_left():
    options = config_options.parse_opts(
        ["--tab-name-align", "center", "--tab-side", "left"]
    )
    assert options.tab_name_align == "center"
    assert options.tab_side == "left"
    options = config_options.clean_opts(options)
    main.calculate_layout(options)
    assert options.tab_name_align == "centre"  # check for change in value
    assert options.tab_side == "left"
