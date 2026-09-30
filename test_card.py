"""The page card uses the scanner's words."""

import unittest

import server
from card import LIKELY, RETAKE, announcement, card_from_scan


SAUCE = {
    "nova_group": 3,
    "verdict_state": "confirmed",
    "ingredients": [
        {"name": "Italian Whole Peeled Tomatoes", "marker": False, "kind": ""},
        {"name": "Olive Oil", "marker": False, "kind": ""},
        {"name": "Onions", "marker": False, "kind": ""},
        {"name": "Salt", "marker": False, "kind": ""},
        {"name": "Garlic", "marker": False, "kind": ""},
        {"name": "Basil", "marker": False, "kind": ""},
        {"name": "Black Pepper", "marker": False, "kind": ""},
        {"name": "Oregano", "marker": False, "kind": ""},
    ],
}


class CardTests(unittest.TestCase):
    def test_known_sauce_is_processed(self):
        card = card_from_scan(SAUCE)
        self.assertEqual(card["title"], "Group 3: Processed foods")
        self.assertEqual(card["group"], 3)
        self.assertIsNone(card["notice"])
        self.assertEqual(card["ingredients"][0]["name"], "Italian Whole Peeled Tomatoes")
        self.assertFalse(any(item["marker"] for item in card["ingredients"]))
        self.assertEqual(announcement(card), "NOVA 3, processed food, 0 markers found")

    def test_unsettled_name_uses_the_likely_sentence(self):
        card = card_from_scan({
            "nova_group": 3,
            "verdict_state": "provisional",
            "ingredients": [{"name": "zorbitol x", "marker": False, "kind": ""}],
        })
        self.assertEqual(card["title"], LIKELY)
        self.assertIsNone(card["group"])

    def test_unreadable_photo_keeps_the_lines_and_hides_the_group(self):
        card = card_from_scan({
            "nova_group": None,
            "verdict_state": "cannot_determine",
            "retake_reason": "No ingredients list can be seen in this photo.",
            "ingredients": [{"name": "Salt", "marker": False}],
        })
        self.assertEqual(card["title"], "No ingredients list can be seen in this photo.")
        self.assertEqual(card["notice"], RETAKE)
        self.assertEqual(len(card["ingredients"]), 1)
        self.assertIsNone(card["group"])


class NoFoodTests(unittest.TestCase):
    def test_screenshot_with_no_list_has_no_group(self):
        card = card_from_scan({
            "status": "no ingredients",
            "nova_group": None,
            "reason": "No ingredients list can be seen in this photo.",
            "notice": "",
            "ingredients": [],
        })
        self.assertIsNone(card["group"])
        self.assertEqual(card["title"], "No ingredients list can be seen in this photo.")
        self.assertEqual(card["notice"], RETAKE)
        self.assertEqual(card["ingredients"], [])
        self.assertNotIn("ultra-processed", card["title"].lower())

    def test_each_unreadable_label_keeps_the_scanner_sentence(self):
        sentences = (
            "No ingredients list can be seen in this photo.",
            "No ingredients have been listed on this tray of chicken.",
            "The ingredients list is not fully in view. Photograph it so the whole list can be read.",
            "The ingredients are printed on a paper bag and are not fully readable. Flatten the bag and photograph the list so every ingredient can be read.",
            "Couldn't tell what kind of item this is.",
            "Could not determine a group.",
        )
        for sentence in sentences:
            card = card_from_scan({
                "nova_group": None,
                "verdict_state": "cannot_determine",
                "retake_reason": sentence,
                "ingredients": [],
            })
            self.assertEqual(card["title"], sentence)
            self.assertIsNone(card["group"])
            self.assertEqual(card["notice"], RETAKE)

    def test_non_food_has_no_group_even_when_a_marker_was_read(self):
        card = card_from_scan({
            "nova_group": None,
            "verdict_state": "cannot_determine",
            "reason": "Not a food or drink, so NOVA doesn't apply.",
            "ingredients": [{"name": "Fragrance", "marker": True, "kind": "flavourings"}],
        })
        self.assertIsNone(card["group"])
        self.assertEqual(card["title"], "Not a food or drink, so NOVA doesn't apply.")
        self.assertEqual(card["ingredients"][0]["name"], "Fragrance")
        self.assertTrue(card["ingredients"][0]["marker"])

    def test_non_food_marker_sentence_is_not_a_group(self):
        card = card_from_scan({
            "nova_group": None,
            "verdict_state": "cannot_determine",
            "reason": "Not a food. Contains an ingredient that makes a food ultra-processed.",
            "ingredients": [{"name": "Fragrance", "marker": True, "kind": "flavourings"}],
        })
        self.assertIsNone(card["group"])
        self.assertEqual(
            card["title"],
            "Not a food. Contains an ingredient that makes a food ultra-processed.",
        )


class ScanCallTests(unittest.TestCase):
    def test_photo_bytes_reach_the_scanner(self):
        seen = {}

        def accept(image, frame=None):
            seen["image"] = image
            seen["frame"] = frame
            return {
                "nova_group": 3,
                "verdict_state": "confirmed",
                "ingredients": [{"name": "Tomatoes", "marker": False, "kind": ""}],
            }

        server._accept_photo = accept
        server._client_error_body = lambda error: {"error": "The scan did not finish."}
        code, payload = server.scan_image(b"\xff\xd8\xff-photo")
        self.assertEqual(code, 200)
        self.assertEqual(seen["image"], b"\xff\xd8\xff-photo")
        self.assertEqual(payload["title"], "Group 3: Processed foods")


if __name__ == "__main__":
    unittest.main()
