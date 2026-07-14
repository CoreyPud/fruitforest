"""Tests for FruitForest's pure routing helpers."""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys
import unittest

MODELS_PATH = (
    Path(__file__).parents[1] / "custom_components" / "fruitforest" / "models.py"
)
SPEC = spec_from_file_location("fruitforest_models", MODELS_PATH)
assert SPEC is not None and SPEC.loader is not None
MODELS = module_from_spec(SPEC)
sys.modules[SPEC.name] = MODELS
SPEC.loader.exec_module(MODELS)


class BuildSearchPhraseTest(unittest.TestCase):
    def test_track(self) -> None:
        self.assertEqual(
            MODELS.build_search_phrase(
                "track", title="Songbird", artist="Fleetwood Mac"
            ),
            "Songbird by Fleetwood Mac",
        )

    def test_album(self) -> None:
        self.assertEqual(
            MODELS.build_search_phrase(
                "album", title="Rumours", artist="Fleetwood Mac"
            ),
            "the album Rumours by Fleetwood Mac",
        )

    def test_playlist(self) -> None:
        self.assertEqual(
            MODELS.build_search_phrase("playlist", name="Sunday Morning"),
            "the playlist Sunday Morning",
        )


class TargetDisambiguationTest(unittest.TestCase):
    def test_duplicate_area_names_are_readable_and_unique(self) -> None:
        target_type = MODELS.PlaybackTarget
        targets = MODELS.disambiguate_targets(
            [
                target_type(
                    "",
                    "Office",
                    "device",
                    "media_player.one",
                    True,
                    fallback_name="Desk Echo",
                ),
                target_type(
                    "",
                    "Office",
                    "device",
                    "media_player.two",
                    True,
                    fallback_name="Show",
                ),
            ]
        )

        self.assertEqual(
            [target.name for target in targets], ["Office (Desk Echo)", "Office (Show)"]
        )
        self.assertEqual(
            [target.target_id for target in targets],
            ["office-desk-echo", "office-show"],
        )

    def test_group_and_device_collision_is_disambiguated(self) -> None:
        target_type = MODELS.PlaybackTarget
        targets = MODELS.disambiguate_targets(
            [
                target_type(
                    "",
                    "Everywhere",
                    "device",
                    "media_player.everywhere",
                    True,
                    fallback_name="Echo",
                ),
                target_type(
                    "",
                    "Everywhere",
                    "group",
                    "media_player.kitchen",
                    True,
                    phrase="Everywhere",
                    fallback_name="Group",
                ),
            ]
        )

        self.assertEqual(
            [target.name for target in targets],
            ["Everywhere (Echo)", "Everywhere (Group)"],
        )


if __name__ == "__main__":
    unittest.main()
