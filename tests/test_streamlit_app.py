import json
from pathlib import Path
import re
import unittest
from xml.etree import ElementTree

from streamlit.testing.v1 import AppTest

from mission_design import LAUNCH_SITES


class StreamlitAppTests(unittest.TestCase):
    def setUp(self):
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        self.app = AppTest.from_file(str(app_path), default_timeout=30).run()
        self.assertFalse(self.app.exception)

    def _sound_payload(self):
        match = None
        for frame in self.app.get("iframe"):
            match = re.search(
                r'src="data:audio/wav;base64,([^"]+)"></audio>',
                frame.proto.srcdoc,
            )
            if match:
                break
        self.assertIsNotNone(match)
        return match.group(1)

    def _sound_payloads(self):
        return [
            match.group(1)
            for frame in self.app.get("iframe")
            if (
                match := re.search(
                    r'src="data:audio/wav;base64,([^"]+)"></audio>',
                    frame.proto.srcdoc,
                )
            )
        ]

    def _schematic_markup(self):
        for frame in self.app.get("iframe"):
            if "Live spacecraft schematic" in frame.proto.srcdoc:
                return frame.proto.srcdoc
        self.fail("Phase 2 spacecraft schematic was not rendered.")

    def test_phase_one_renders_interactive_geographic_map_and_theme_options(self):
        self.assertEqual(len(self.app.get("plotly_chart")), 1)
        chart = self.app.get("plotly_chart")[0]
        figure = json.loads(chart.proto.spec)

        self.assertEqual(figure["layout"]["geo"]["projection"]["type"], "natural earth")
        self.assertEqual(
            figure["data"][3]["customdata"],
            list(LAUNCH_SITES),
        )
        self.assertEqual(
            figure["data"][3]["lat"],
            [5.236, 28.572, 45.965, 40.96],
        )
        self.assertEqual(
            figure["data"][3]["lon"],
            [-52.768, -80.649, 63.305, 100.298],
        )
        self.assertEqual(chart.proto.selection_mode, [0])
        self.assertEqual(self.app.selectbox(key="visual_theme").value, "Aurora")
        self.assertEqual(len(self.app.progress), 1)

    def test_launch_site_and_theme_choices_update_map(self):
        self.app.selectbox(key="launch_site_picker").select(
            "Kennedy Space Center"
        ).run()
        self.assertEqual(
            self.app.session_state["selected_launch_site"],
            "Kennedy Space Center",
        )

        self.app.selectbox(key="visual_theme").select("Arctic Pulse").run()
        figure = json.loads(self.app.get("plotly_chart")[0].proto.spec)
        self.assertEqual(figure["data"][0]["line"]["color"], "#68d9ff")
        self.assertEqual(figure["data"][3]["customdata"], list(LAUNCH_SITES))
        self.assertEqual(
            figure["data"][3]["marker"]["color"][1],
            "#68d9ff",
        )
        self.assertFalse(self.app.exception)

    def test_light_themes_use_bright_surfaces_and_readable_map_labels(self):
        light_palettes = {
            "Solaris": ("#1f2937", "#e8eee8", "#334155", "#14532d"),
            "Botanical": ("#172b26", "#e4eee2", "#29443a", "#14532d"),
            "Daybreak": ("#2b1d27", "#f0e9e7", "#453849", "#881337"),
        }
        for name, (
            text_color,
            land_color,
            map_text_color,
            alert_text_color,
        ) in light_palettes.items():
            with self.subTest(theme=name):
                self.app.selectbox(key="visual_theme").select(name).run()
                figure = json.loads(self.app.get("plotly_chart")[0].proto.spec)
                self.assertEqual(
                    figure["layout"]["geo"]["landcolor"],
                    land_color,
                )
                self.assertEqual(
                    figure["data"][3]["textfont"]["color"],
                    map_text_color,
                )
                self.assertTrue(
                    any(
                        f'--mission-text: {text_color}' in item.value
                        for item in self.app.markdown
                    )
                )
                self.assertTrue(
                    any(
                        '[data-testid="stSelectbox"] [data-baseweb="select"] > div > div'
                        in item.value
                        and f"color: {alert_text_color} !important" in item.value
                        for item in self.app.markdown
                    )
                )
                self.assertFalse(self.app.exception)

    def test_progress_panel_remains_visible_after_confirming_phase_one(self):
        self.app.selectbox(key="launch_site_picker").select(
            "Guiana Space Centre"
        ).run()
        self.app.selectbox(key="visual_theme").select("Solar Flare").run()
        self.app.selectbox(key="destination_picker").select("Moon").run()
        self.app.button(key="confirm_location").click().run()

        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertEqual(self.app.session_state["visual_theme"], "Solar Flare")
        self.assertEqual(len(self.app.get("plotly_chart")), 0)
        self.assertEqual(len(self.app.progress), 1)
        self.assertEqual(self.app.progress[0].value, 0)
        self.assertEqual(self.app.metric[0].value, "0 kg")
        self.assertEqual(self.app.metric[2].value, "0")
        self.assertFalse(self.app.exception)

    def test_phase_two_schematic_updates_with_unselected_and_selected_parts(self):
        self.app.selectbox(key="launch_site_picker").select(
            "Guiana Space Centre"
        ).run()
        self.app.selectbox(key="destination_picker").select("Moon").run()
        self.app.button(key="confirm_location").click().run()

        markup = self._schematic_markup()
        self.assertIn("<svg", markup)
        self.assertIn("Hull not selected", markup)
        self.assertIn("Engine not selected", markup)
        self.assertIn("Fuel tank not selected", markup)
        self.assertNotIn("THRUST</text>", markup)

        self.app.selectbox(key="component_picker_hull").select(
            "Carbon-Composite Shell"
        ).run()
        self.app.selectbox(key="engine_picker").select(
            "Heavy-Duty Deep Space Cluster"
        ).run()
        self.app.selectbox(key="fuel_tank_picker").select(
            "Heavy-Duty Deep Space Pod"
        ).run()
        self.app.selectbox(key="component_picker_thermal").select(
            "Passive MLI Insulation Blankets"
        ).run()
        self.app.selectbox(key="component_picker_power").select(
            "Standard Solar Array Panels"
        ).run()
        self.app.selectbox(key="component_picker_avionics").select(
            "Redundant Deep-Space Command Computer"
        ).run()
        self.app.selectbox(key="component_picker_instruments").select(
            "Geological Drill & Sample Spectrometer"
        ).run()
        markup = self._schematic_markup()
        self.assertIn("Carbon-Composite Shell", markup)
        self.assertIn("Heavy-Duty Deep Space Cluster", markup)
        self.assertIn("Heavy-Duty Deep Space Pod", markup)
        self.assertIn("8,200 THRUST", markup)
        self.assertIn("800 kg FUEL", markup)
        self.assertIn("Passive MLI Insulation Blankets", markup)
        self.assertIn("woven matrix offering high thermal", markup)
        self.assertIn("fault-tolerant flight computer", markup)
        self.assertIn("collecting and analyzing planetary surface samples", markup)
        self.assertIn('id="thermal-insulation"', markup)
        self.assertIn('id="avionics-circuit"', markup)
        self.assertIn('cx="260" cy="78" r="11"', markup)
        self.assertIn('clipPath id="hull-clip"', markup)
        self.assertIn(
            "grid-template-columns:minmax(0, 1fr) minmax(0, 1fr)",
            markup,
        )
        self.assertIn(
            "<title>Heavy-Duty Deep Space Cluster: A high-thrust multi-nozzle",
            markup,
        )
        self.assertIn('g[tabindex="0"] {cursor:default}', markup)
        self.assertNotIn("cursor:help", markup)
        svg_start = markup.index("<svg")
        svg_end = markup.index("</svg>") + len("</svg>")
        ElementTree.fromstring(markup[svg_start:svg_end])
        self.assertFalse(self.app.exception)

    def test_phase_three_launch_animates_trajectory_and_opens_landing_controls(self):
        self.app.sidebar.button(key="hardcore_preset").click().run()
        self.assertFalse(
            self.app.button(key="initiate_launch_sequence").disabled
        )

        self.app.button(key="initiate_launch_sequence").click().run()

        self.assertEqual(self.app.session_state["mission_phase"], 3)
        self.assertEqual(self.app.session_state["flight_status"], "arrival")
        self.assertEqual(self.app.session_state["landing_altitude_m"], 180)
        self.assertLess(self.app.session_state["flight_fuel_remaining_kg"],
                        self.app.session_state["flight_fuel_capacity_kg"])
        self.assertEqual(len(self.app.get("plotly_chart")), 0)
        self.assertTrue(
            any("flight-path" in frame.proto.srcdoc
                for frame in self.app.get("iframe"))
        )
        self.assertTrue(
            any("Estimated time to arrival" in element.label
                for element in self.app.metric)
        )
        iframe_sources = [frame.proto.srcdoc for frame in self.app.get("iframe")]
        self.assertTrue(any("parentWindow.scrollTo" in source for source in iframe_sources))
        self.assertTrue(any('dur="7.82s"' in source for source in iframe_sources))
        self.assertTrue(any("EARTH DEPARTURE" in source for source in iframe_sources))
        self.assertTrue(any('M91 210L98 201' in source for source in iframe_sources))
        self.assertTrue(any('cx="695" cy="194"' in source for source in iframe_sources))
        animation_markup = next(
            source[source.index("<svg"):source.index("</svg>") + len("</svg>")]
            for source in iframe_sources
            if "flight-path" in source
        )
        ElementTree.fromstring(animation_markup)
        sounds_during_flight = self._sound_payloads()
        self.assertTrue(sounds_during_flight)
        self.app.button(key="begin_landing").click().run()
        self.assertEqual(self.app.session_state["flight_status"], "landing")
        self.assertTrue(
            any("gravity is capped" in item.value for item in self.app.markdown)
        )
        self.assertGreater(len(self.app.metric), 3)
        self.app.button(key="burn_retro_thrust")
        self.app.button(key="coast_descent")
        self.assertTrue(
            any("SAFE ZONE" in item.value for item in self.app.markdown)
        )
        starting_fuel = self.app.session_state["flight_fuel_remaining_kg"]
        self.app.button(key="burn_retro_thrust").click().run()
        self.assertEqual(self.app.session_state["flight_status"], "landing")
        self.assertEqual(self.app.session_state["landing_velocity_m_s"], 0)
        self.assertLess(self.app.session_state["landing_altitude_m"], 180)
        self.assertLess(
            self.app.session_state["flight_fuel_remaining_kg"],
            starting_fuel,
        )
        thrust_sound = self._sound_payloads()[-1]
        self.app.button(key="coast_descent").click().run()
        coast_sound = self._sound_payloads()[-1]
        self.assertNotEqual(thrust_sound, coast_sound)
        self.app.button(key="back_to_assembly").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertEqual(self.app.session_state["flight_status"], "assembly")
        self.assertEqual(self.app.session_state["mission_destination"], "Jupiter")
        self.assertFalse(self.app.exception)

    def test_planetarium_uses_body_specific_surface_styles_and_distance_timing(self):
        self.app.sidebar.button(key="beginner_preset").click().run()
        self.app.button(key="initiate_launch_sequence").click().run()
        frames = [frame.proto.srcdoc for frame in self.app.get("iframe")]
        self.assertTrue(any('dur="4.00s"' in frame for frame in frames))
        self.assertTrue(any('id="earth-ocean"' in frame for frame in frames))
        self.assertTrue(any('fill="#55bd83"' in frame for frame in frames))

    def test_landing_success_crash_and_restart_conditions(self):
        self.app.sidebar.button(key="beginner_preset").click().run()
        self.app.button(key="initiate_launch_sequence").click().run()
        self.app.button(key="begin_landing").click().run()

        self.app.session_state["landing_altitude_m"] = 1
        self.app.session_state["landing_velocity_m_s"] = 0.1
        for _ in range(3):
            self.app.button(key="coast_descent").click().run()
            if self.app.session_state["flight_status"] != "landing":
                break
        self.assertEqual(self.app.session_state["flight_status"], "landed")
        self.assertEqual(self.app.session_state["landing_score"], 95)

        self.app.button(key="restart_landing").click().run()
        self.assertEqual(self.app.session_state["flight_status"], "landing")
        self.assertEqual(self.app.session_state["landing_altitude_m"], 180)

        self.app.session_state["landing_altitude_m"] = 1
        self.app.session_state["landing_velocity_m_s"] = 8
        self.app.button(key="coast_descent").click().run()
        self.assertEqual(self.app.session_state["flight_status"], "crashed")
        self.assertIn("exceeded the 5 m/s limit", self.app.session_state["flight_result"])
        self.app.button(key="restart_landing").click().run()
        self.app.session_state["landing_altitude_m"] = 500
        self.app.session_state["flight_fuel_remaining_kg"] = 0
        self.app.button(key="coast_descent").click().run()
        self.assertEqual(self.app.session_state["flight_status"], "crashed")
        self.assertIn("Fuel depleted", self.app.session_state["flight_result"])
        self.assertFalse(self.app.exception)

    def test_jupiter_landing_can_be_completed_with_speed_guided_controls(self):
        self.app.session_state["mission_phase"] = 3
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Jupiter"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 1000
        self.app.session_state["landing_altitude_m"] = 180
        self.app.session_state["landing_velocity_m_s"] = 8
        self.app.run()

        for _ in range(20):
            if self.app.session_state["flight_status"] != "landing":
                break
            control = (
                "burn_retro_thrust"
                if self.app.session_state["landing_velocity_m_s"] > 5
                else "coast_descent"
            )
            self.app.button(key=control).click().run()

        self.assertEqual(self.app.session_state["flight_status"], "landed")
        self.assertLess(self.app.session_state["landing_velocity_m_s"], 5)
        self.assertFalse(self.app.exception)

    def test_sidebar_presets_load_mission_and_play_menu_cue(self):
        self.assertEqual(self.app.sidebar.slider(key="interface_volume").value, 35)
        self.assertEqual(len(self.app.sidebar.expander), 1)

        self.app.sidebar.button(key="beginner_preset").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertEqual(self.app.session_state["mission_destination"], "Moon")
        self.assertEqual(
            self.app.session_state["mission_components"]["hull"],
            "Lightweight Aluminum Frame",
        )
        self.assertEqual(self.app.metric[0].value, "1,430 kg")
        self.assertEqual(self.app.metric[2].value, "1,600")
        frames = [frame.proto.srcdoc for frame in self.app.get("iframe")]
        self.assertTrue(any("<svg" in frame for frame in frames))
        self.assertTrue(any("data:audio/wav;base64," in frame for frame in frames))
        self.assertFalse(self.app.exception)

    def test_hardcore_preset_and_reset_restore_defaults(self):
        self.app.sidebar.button(key="hardcore_preset").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertEqual(self.app.session_state["mission_destination"], "Jupiter")
        self.assertEqual(
            self.app.session_state["selected_launch_site"],
            "Guiana Space Centre",
        )
        self.assertEqual(
            self.app.session_state["mission_components"]["hull"],
            "Reinforced Titanium-Alloy Hull",
        )
        self.assertEqual(
            self.app.session_state["mission_components"]["power"],
            "Standard Solar Array Panels",
        )
        self.assertEqual(
            self.app.session_state["mission_components"]["avionics"],
            "Basic Sun & Earth Sensors",
        )
        self.assertEqual(
            self.app.session_state["mission_components"]["thermal"],
            "Passive MLI Insulation Blankets",
        )
        self.assertEqual(
            self.app.session_state["mission_components"]["instruments"],
            "Optical Imaging Camera Suite",
        )
        self.assertEqual(
            self.app.session_state["mission_engine"],
            "Heavy-Duty Deep Space Cluster",
        )
        self.assertEqual(
            self.app.session_state["mission_fuel_tank"],
            "Heavy-Duty Deep Space Pod",
        )
        self.assertEqual(self.app.metric[0].value, "3,530 kg")
        self.assertEqual(self.app.metric[2].value, "8,200")
        self.assertIn(
            "Heavy-Duty Deep Space Cluster — 1,200 kg, 8,200 upthrust",
            self.app.selectbox(key="engine_picker").options,
        )

        self.app.sidebar.button(key="reset_mission").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 1)
        self.assertIsNone(self.app.session_state["selected_launch_site"])
        self.assertIsNone(self.app.session_state["mission_destination"])
        self.assertEqual(self.app.session_state["mission_components"], {})
        self.assertIsNone(self.app.session_state["mission_engine"])
        self.assertIsNone(self.app.session_state["mission_fuel_tank"])
        self.assertEqual(self.app.sidebar.slider(key="interface_volume").value, 35)
        self.assertEqual(self.app.metric[0].value, "0 kg")
        self.assertFalse(self.app.exception)

    def test_updating_launchpad_preserves_loaded_preset_components(self):
        self.app.sidebar.button(key="hardcore_preset").click().run()
        preset_components = dict(self.app.session_state["mission_components"])
        preset_engine = self.app.session_state["mission_engine"]
        preset_tank = self.app.session_state["mission_fuel_tank"]

        self.app.button(key="edit_location").click().run()
        self.app.selectbox(key="launch_site_picker").select(
            "Kennedy Space Center"
        ).run()
        self.app.button(key="confirm_location").click().run()

        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertEqual(
            self.app.session_state["selected_launch_site"],
            "Kennedy Space Center",
        )
        self.assertEqual(
            self.app.session_state["mission_components"],
            preset_components,
        )
        self.assertEqual(self.app.session_state["mission_engine"], preset_engine)
        self.assertEqual(self.app.session_state["mission_fuel_tank"], preset_tank)
        self.assertEqual(
            self.app.selectbox(key="engine_picker").value,
            preset_engine,
        )
        self.assertFalse(self.app.exception)

    def test_hull_picker_enforces_minimum_and_clears_hull_on_planet_change(self):
        self.app.sidebar.button(key="beginner_preset").click().run()
        self.assertEqual(self.app.session_state["mission_components"]["hull"],
                         "Lightweight Aluminum Frame")

        self.app.button(key="edit_location").click().run()
        self.app.selectbox(key="destination_picker").select("Jupiter").run()
        self.app.button(key="confirm_location").click().run()
        self.assertIsNone(self.app.session_state["mission_components"]["hull"])
        self.assertEqual(
            self.app.selectbox(key="component_picker_hull").options,
            [
                "Choose a component",
                "Reinforced Titanium-Alloy Hull — 1,100 kg",
            ],
        )

        self.app.button(key="edit_location").click().run()
        self.app.selectbox(key="destination_picker").select("Mercury").run()
        self.app.button(key="confirm_location").click().run()
        self.assertIsNone(self.app.session_state["mission_components"]["hull"])
        self.assertEqual(
            self.app.selectbox(key="component_picker_hull").options,
            [
                "Choose a component",
                "Carbon-Composite Shell — 550 kg",
                "Reinforced Titanium-Alloy Hull — 1,100 kg",
            ],
        )
        self.assertFalse(self.app.exception)

    def test_volume_zero_mutes_menu_sound(self):
        self.app.sidebar.slider(key="interface_volume").set_value(0).run()
        self.assertEqual(self.app.sidebar.slider(key="interface_volume").value, 0)
        self.assertEqual(len(self.app.get("iframe")), 0)

    def test_selection_menu_and_phase_transitions_use_distinct_sounds(self):
        self.app.selectbox(key="launch_site_picker").select(
            "Kennedy Space Center"
        ).run()
        selection_sound = self._sound_payload()

        self.app.selectbox(key="visual_theme").select("Solar Flare").run()
        menu_sound = self._sound_payload()
        self.assertNotEqual(selection_sound, menu_sound)

        self.app.selectbox(key="destination_picker").select("Mars").run()
        destination_sound = self._sound_payload()
        self.assertEqual(selection_sound, destination_sound)

        self.app.button(key="confirm_location").click().run()
        phase_sound = self._sound_payload()
        self.assertNotEqual(selection_sound, phase_sound)
        self.assertNotEqual(menu_sound, phase_sound)
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertFalse(self.app.exception)


if __name__ == "__main__":
    unittest.main()
