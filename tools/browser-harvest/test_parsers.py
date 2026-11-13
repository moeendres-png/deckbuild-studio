"""Parser-Tests mit SYNTHETISCHEN Fixtures.

Die Payload-Formen folgen den dokumentierten Strukturen (EDHREC
cardviews-Gruppen, Moxfield boards), sind aber handgebaut — sie belegen
die Parser-Logik, nicht die Live-Antwort einer Website.
"""

import json
from pathlib import Path

import browser_deck_harvest as h

FIXTURE_DIR = Path(__file__).parent / "fixture"


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
    payload = {"deck": {"name": "Mein Deck", "author": {"name": "Testautor"}}}
    # "Mein Deck" haengt unter "deck" und darf als Karte zaehlen duerfen,
    # der Autor aber nicht.
    names = {c["name"] for c in h.parse_deck_payload(payload)}
    assert "Testautor" not in names


def test_detect_source():
    assert h.detect_source("https://edhrec.com/deckpreview/abc") == "edhrec"
    assert h.detect_source("https://www.moxfield.com/decks/xyz") == "moxfield"
    assert h.detect_source("https://archidekt.com/decks/1") == "archidekt"


def test_rsc_deckpreview_fixture():
    """Aktuelle EDHREC-Deckpreview: Flight-Strom statt JSON.

    Altes Verhalten: Der generische JSON-Parser liest aus dem
    Seiten-HTML 0 Karten (genau der belegte Defekt). Neues Verhalten:
    parse_rsc_payload setzt die __next_f.push-Chunks zusammen und
    extrahiert die volle Liste aus decklist.recs.
    """
    html = (FIXTURE_DIR / "edhrec_deckpreview_rsc.html").read_text(
        encoding="utf-8")
    assert h.parse_deck_payload(html) == []
    cards = h.parse_rsc_payload(html)
    by_name = {c["name"]: c for c in cards}
    assert by_name["Test Card C1"]["quantity"] == 2  # Duplikat summiert
    assert by_name["Test Card C1"]["section"] == "Creatures"
    assert by_name["Test Card C2"]["section"] == "Creatures"
    assert by_name["Test Land"]["quantity"] == 36
    assert by_name["Test Land"]["section"] == "Lands"
    assert by_name["Test Commander"]["section"] == "Commanders"
    assert by_name["Test Flat Card"]["quantity"] == 2
    assert by_name["Test Wrapped Card"]["quantity"] == 3
    assert "Synthetic Fixture Deck" not in by_name  # Deckname != Karte
    assert sum(c["quantity"] for c in cards) == 45


def test_rsc_decklist_reference_row():
    """decklist darf auch als "$L<id>"-Referenz auf eine Flight-Zeile
    stehen; ein reiner Flight-Strom (ohne HTML) wird ebenso gelesen."""
    decklist = {
        "recs": [
            {"header": "Instants",
             "cardviews": [{"name": "Test Instant", "quantity": 4}]},
        ]
    }
    stream = (
        '0:{"decklist":"$L2"}\n'
        "2:" + json.dumps(decklist) + "\n"
    )
    cards = h.parse_rsc_payload(stream)
    assert cards == [
        {"name": "Test Instant", "quantity": 4, "section": "Instants"}
    ]


def test_rsc_without_decklist_is_empty():
    assert h.parse_rsc_payload("<html><body>kein Payload</body></html>") == []
    assert h.parse_rsc_payload('0:{"unrelated":true}\n') == []
