"""Parser-Tests mit SYNTHETISCHEN Fixtures.

Die Payload-Formen folgen den dokumentierten Strukturen (EDHREC
cardviews-Gruppen, Moxfield boards), sind aber handgebaut — sie belegen
die Parser-Logik, nicht die Live-Antwort einer Website.
"""

import browser_deck_harvest as h


def test_edhrec_style_cardviews():
    payload = {
        "deck": {
            "cardviews": {
                "Commanders": [{"name": "Chulane, Teller of Tales"}],
                "Creatures": [
                    {"name": "Birds of Paradise"},
                    {"name": "Birds of Paradise"},  # Duplikat -> Anzahl 2
                    {"name": "Llanowar Elves"},
                ],
                "Lands": [{"name": "Forest", "quantity": 10}],
            }
        }
    }
    cards = h.parse_deck_payload(payload)
    by_name = {c["name"]: c for c in cards}
    assert by_name["Chulane, Teller of Tales"]["quantity"] == 1
    assert by_name["Birds of Paradise"]["quantity"] == 2
    assert by_name["Birds of Paradise"]["section"] == "Creatures"
    assert by_name["Forest"]["quantity"] == 10
    assert by_name["Forest"]["section"] == "Lands"


def test_moxfield_style_boards():
    payload = {
        "boards": {
            "commanders": {"cards": {
                "abc": {"quantity": 1, "card": {"name": "Ayli, Eternal Pilgrim"}},
            }},
            "mainboard": {"cards": {
                "x": {"quantity": 1, "card": {"name": "Sol Ring"}},
                "y": {"quantity": 4, "card": {"name": "Plains"}},
            }},
        }
    }
    cards = h.parse_deck_payload(payload)
    by_name = {c["name"]: c for c in cards}
    assert by_name["Ayli, Eternal Pilgrim"]["section"] == "commanders"
    assert by_name["Sol Ring"]["quantity"] == 1
    assert by_name["Plains"]["quantity"] == 4


def test_text_fallback():
    text = "Commander\n1 Chulane, Teller of Tales\n4 Forest\n1x Sol Ring\nUnfug ohne Zahl\n"
    cards = h.parse_deck_text(text)
    by_name = {c["name"]: c["quantity"] for c in cards}
    assert by_name == {
        "Chulane, Teller of Tales": 1,
        "Forest": 4,
        "Sol Ring": 1,
    }


def test_no_false_positives_on_metadata():
    payload = {"deck": {"name": "Mein Deck", "author": {"name": "Moritz"}}}
    # "Mein Deck" haengt unter "deck" und darf als Karte zaehlen duerfen,
    # der Autor aber nicht.
    names = {c["name"] for c in h.parse_deck_payload(payload)}
    assert "Moritz" not in names


def test_detect_source():
    assert h.detect_source("https://edhrec.com/deckpreview/abc") == "edhrec"
    assert h.detect_source("https://www.moxfield.com/decks/xyz") == "moxfield"
    assert h.detect_source("https://archidekt.com/decks/1") == "archidekt"
