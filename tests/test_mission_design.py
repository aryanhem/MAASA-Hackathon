import ast
import inspect
import unittest
from pathlib import Path

import mission_design
from mission_design import (
    COMPONENT_CHOICES,
    DESTINATION_DIFFICULTY,
    ENGINE_CHOICES,
    FUEL_TANK_CHOICES,
    HULL_MINIMUM_BY_DESTINATION,
    LAUNCHPAD_MODIFIERS,
    LAUNCH_SITES,
    calculate_mission_score,
    calculate_required_upthrust,
    calculate_total_mass,
    evaluate_mission,
)


class MissionDesignTests(unittest.TestCase):
    def setUp(self):
        self.components = {
            category: next(iter(choices))
            for category, choices in COMPONENT_CHOICES.items()
        }

    def test_total_mass_includes_one_item_from_each_category_engine_and_tank(self):
        expected = sum(
            COMPONENT_CHOICES[category][selection]["mass_kg"]
            for category, selection in self.components.items()
        )
        expected += ENGINE_CHOICES["Standard Kerolox Engine"]["mass_kg"]
        expected += FUEL_TANK_CHOICES["Small Reserve Tank"]["mass_kg"]

        self.assertEqual(
            calculate_total_mass(
                self.components, "Standard Kerolox Engine", "Small Reserve Tank"
            ),
            expected,
        )

    def test_heavy_duty_engine_specs(self):
        self.assertEqual(
            ENGINE_CHOICES["Heavy-Duty Deep Space Cluster"],
            {"mass_kg": 1200, "upthrust": 8200},
        )

    def test_required_upthrust_applies_both_modifiers(self):
        # 1000 kg * Kennedy's Mars modifier (1.1) * updated Mars difficulty (1.0).
        self.assertAlmostEqual(
            calculate_required_upthrust(
                1000, "Kennedy Space Center", "Mars"
            ),
            1100,
        )

    def test_mission_result_reports_success_and_progress(self):
        result = evaluate_mission(
            self.components,
            "Heavy-Duty Deep Space Cluster",
            "Small Reserve Tank",
            "Guiana Space Centre",
            "Mars",
        )
        self.assertTrue(result.success)
        self.assertGreater(result.progress_percentage, 100)

    def test_unselected_parts_contribute_zero_mass(self):
        self.assertEqual(calculate_total_mass({}, None, None), 0)
        self.assertEqual(
            calculate_total_mass(
                {"hull": "Lightweight Aluminum Frame"}, None, None
            ),
            300,
        )

    def test_unselected_engine_has_zero_upthrust_and_progress(self):
        result = evaluate_mission({}, None, None, "Guiana Space Centre", "Moon")
        self.assertEqual(result.total_mass_kg, 0)
        self.assertEqual(result.required_upthrust, 0)
        self.assertEqual(result.selected_upthrust, 0)
        self.assertFalse(result.success)
        self.assertEqual(result.progress_percentage, 0)

    def test_selected_engine_without_location_does_not_fake_success(self):
        result = evaluate_mission(
            {}, "Heavy-Duty Deep Space Cluster", None, None, None
        )
        self.assertEqual(result.required_upthrust, 0)
        self.assertEqual(result.selected_upthrust, 8200)
        self.assertFalse(result.success)
        self.assertEqual(result.progress_percentage, 0)

    def test_moon_launch_site_modifiers_match_team_notes(self):
        expected = {
            "Guiana Space Centre": 0.8,
            "Kennedy Space Center": 0.9,
            "Baikonur Cosmodrome": 1.1,
            "China Jiuquan Launch Center": 1.0,
        }
        for launch_site, modifier in expected.items():
            with self.subTest(launch_site=launch_site):
                self.assertEqual(LAUNCHPAD_MODIFIERS[launch_site]["Moon"], modifier)

    def test_moon_required_upthrust_applies_launchpad_and_destination_modifiers(self):
        # Guiana Moon modifier 0.8 * updated Moon difficulty 0.7.
        self.assertAlmostEqual(
            calculate_required_upthrust(1000, "Guiana Space Centre", "Moon"),
            560,
        )

    def test_launch_site_options_match_modifier_data(self):
        self.assertEqual(set(LAUNCH_SITES), set(LAUNCHPAD_MODIFIERS))

    def test_destination_difficulty_modifiers_use_requested_reductions(self):
        self.assertEqual(
            {
                "Moon": 0.7,
                "Mars": 1.0,
                "Mercury": 1.2,
                "Venus": 1.7,
                "Saturn": 2.0,
                "Neptune": 1.8,
                "Jupiter": 2.1,
                "Uranus": 1.6,
            },
            DESTINATION_DIFFICULTY,
        )

    def test_hull_minimums_follow_destination_hazard_notes(self):
        self.assertEqual(
            HULL_MINIMUM_BY_DESTINATION,
            {
                "Moon": "Lightweight Aluminum Frame",
                "Mars": "Lightweight Aluminum Frame",
                "Mercury": "Carbon-Composite Shell",
                "Venus": "Carbon-Composite Shell",
                "Uranus": "Reinforced Titanium-Alloy Hull",
                "Saturn": "Reinforced Titanium-Alloy Hull",
                "Jupiter": "Reinforced Titanium-Alloy Hull",
                "Neptune": "Reinforced Titanium-Alloy Hull",
            },
        )

    def test_mission_score_combines_research_risk_gravity_assists_and_fuel(self):
        score = calculate_mission_score(
            self.components,
            "Kennedy Space Center",
            2,
            remaining_fuel_kg=500,
            starting_fuel_kg=1000,
        )

        self.assertEqual(score.research_points, 38)
        self.assertEqual(score.launch_difficulty_multiplier, 1.5)
        self.assertEqual(score.slingshot_body_bonus, 1.4)
        self.assertEqual(score.fuel_efficiency_bonus, 50)
        self.assertEqual(score.total_score, 129.8)

    def test_mission_score_rejects_missing_components_and_invalid_fuel(self):
        with self.assertRaisesRegex(ValueError, "Select a power component"):
            calculate_mission_score(
                {"hull": self.components["hull"]},
                "Guiana Space Centre",
                0,
                100,
                100,
            )
        with self.assertRaisesRegex(ValueError, "between zero and starting fuel"):
            calculate_mission_score(
                self.components,
                "Guiana Space Centre",
                0,
                101,
                100,
            )

    def test_app_imports_are_defined_and_exported_with_compatible_signatures(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        app_tree = ast.parse(app_path.read_text(encoding="utf-8"))
        app_imports = {
            alias.name
            for node in app_tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "mission_design"
            for alias in node.names
        }

        self.assertTrue(app_imports)
        self.assertNotIn("calculate_mission_score", app_imports)
        self.assertLessEqual(app_imports, set(mission_design.__all__))
        for name in app_imports:
            with self.subTest(import_name=name):
                self.assertTrue(hasattr(mission_design, name))
        app_functions = {
            node.name for node in app_tree.body if isinstance(node, ast.FunctionDef)
        }
        self.assertIn("calculate_mission_score", app_functions)

        inspect.signature(mission_design.calculate_required_upthrust).bind(
            1000, "Guiana Space Centre", "Moon"
        )
        inspect.signature(mission_design.evaluate_mission).bind(
            {}, "Standard Kerolox Engine", "Small Reserve Tank",
            "Guiana Space Centre", "Moon",
        )


if __name__ == "__main__":
    unittest.main()
