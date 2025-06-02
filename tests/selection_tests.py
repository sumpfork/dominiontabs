from domdiv import db, main
from tests import parse_and_clean_args


def test_group_special():
    options = parse_and_clean_args(["--group-special"])
    all_cards = db.read_card_data(options)
    cards = main.filter_sort_cards(all_cards, options)

    # Make assertions that a few specific cards are handled correctly
    empires_event_cards = [
        c for c in cards if c.isType("Event") and c.cardset_tag == "empires"
    ]
    assert len(empires_event_cards) == 1
    empires_events = empires_event_cards[0]
    assert empires_events.getCardCounts() == [1] * 13
    assert empires_events.name == "Events: Empires"
    assert empires_events.types == ["Event"]

    # test some split piles
    gladiator_matches = [c for c in cards if c.group_tag == "Gladiator - Fortune"]
    assert len(gladiator_matches) == 1
    gladiator_fortune = gladiator_matches[0]
    gladiator_fortune.name.startswith("Gladiator")
    assert "Fortune" in gladiator_fortune.name
    assert gladiator_fortune.getCardCounts() == [5, 5]
    assert gladiator_fortune.types == ["Action"]
    assert gladiator_fortune.cost == "3"

    joust_matches = [c for c in cards if c.group_tag == "Joust and Rewards"]
    assert len(joust_matches) == 1
    joust_rewards = joust_matches[0]
    assert joust_rewards.name.startswith("Joust")
    assert "Rewards" in joust_rewards.name
    counts = joust_rewards.getCardCounts()
    counts.sort()
    assert counts == 6 * [2] + [10]
    assert joust_rewards.types == ["Action"]

    allies_ally_cards = [
        c for c in cards if c.cardset_tag == "allies" and c.isType("Ally")
    ]
    assert len(allies_ally_cards) == 1
    allies_allies = allies_ally_cards[0]
    assert allies_allies.name == "Allies: Allies"
    assert allies_allies.getCardCounts() == [1] * 23
