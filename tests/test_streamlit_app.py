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

    def _launch_slingshot(self, preset_key="hardcore_preset"):
        self.app.sidebar.button(key=preset_key).click().run()
        self.assertFalse(
            self.app.button(key="initiate_launch_sequence").disabled
        )
        self.app.button(key="initiate_launch_sequence").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 3)
        self.assertEqual(self.app.session_state["flight_status"], "slingshot")

    def _submit_slingshot_vector(self, velocity_x, velocity_y):
        self.app.session_state["gravity_slingshot"] = {
            "kind": "launch",
            "attempt_id": self.app.session_state["slingshot_attempt_id"],
            "velocity_x": velocity_x,
            "velocity_y": velocity_y,
        }
        self.app.run()

    def _submit_landing_step(self, duration_s, thrusting):
        event_id = self.app.session_state["landing_last_event_id"] + 1
        self.app.session_state["landing_canvas"] = {
            "kind": "step",
            "event_id": event_id,
            "duration_s": duration_s,
            "thrusting": thrusting,
        }
        self.app.run()

    def _submit_landing_snapshot(
        self,
        event_id,
        altitude_m,
        velocity_m_s,
        fuel_remaining_kg,
        used_thrust,
    ):
        self.app.session_state["landing_canvas"] = {
            "kind": "snapshot",
            "event_id": event_id,
            "altitude_m": altitude_m,
            "velocity_m_s": velocity_m_s,
            "fuel_remaining_kg": fuel_remaining_kg,
            "used_thrust": used_thrust,
        }
        self.app.run()

    def _submit_successful_slingshot(self):
        destination = self.app.session_state["mission_destination"]
        launch_vectors = {
            "Moon": (12, 2),
            "Mercury": (14, 0),
            "Venus": (14, 0),
            "Mars": (14, 0),
            "Jupiter": (18, 4),
            "Saturn": (20, 7),
            "Uranus": (11, -2),
            "Neptune": (10, -2),
        }
        self._submit_slingshot_vector(*launch_vectors[destination])

    def _advance_to_arrival(self, preset_key="hardcore_preset"):
        self._launch_slingshot(preset_key)
        self._submit_successful_slingshot()
        self.assertEqual(
            self.app.session_state["slingshot_outcome"]["status"],
            "success",
        )
        self.app.button(key="continue_to_phase_four").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 4)
        self.assertEqual(self.app.session_state["flight_status"], "arrival")

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
            "Guiana Space Centre"
        ).run()
        self.assertEqual(
            self.app.session_state["selected_launch_site"],
            "Guiana Space Centre",
        )
        self.assertTrue(
            any(
                "https://centrespatialguyanais.cnes.fr/en" in item.value
                for item in self.app.markdown
            )
        )
        self.assertTrue(any("Europe's Spaceport" in item.value for item in self.app.caption))

        self.app.selectbox(key="launch_site_picker").select(
            "Kennedy Space Center"
        ).run()
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

    def test_phase_three_slingshot_advances_to_phase_four_and_five(self):
        self._launch_slingshot()
        self.assertTrue(
            any(
                item.value == "Phase 3 — Gravitational Trajectory Slingshot"
                for item in self.app.subheader
            )
        )
        self.assertEqual(
            self.app.session_state["slingshot_outcome"],
            None,
        )
        self.assertIn("gravity_slingshot", self.app.session_state)
        self.assertTrue(
            any("Drag backward from the rocket" in item.value
                for item in self.app.caption)
        )
        self.assertTrue(
            any(
                item.label == "Real physics: gravity assists and rocket Δv"
                for item in self.app.expander
            )
        )
        phase_markdown = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("inverse-square dependence on distance", phase_markdown)
        self.assertIn("conservation of energy and momentum", phase_markdown)
        self.assertIn(
            "https://science.nasa.gov/learn/basics-of-space-flight/chapter3-1/",
            phase_markdown,
        )

        self._submit_successful_slingshot()
        self.assertEqual(
            self.app.session_state["slingshot_outcome"]["status"],
            "success",
        )
        self.app.button(key="continue_to_phase_four").click().run()

        self.assertEqual(self.app.session_state["mission_phase"], 4)
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
        self.assertEqual(self.app.session_state["mission_phase"], 5)
        self.assertEqual(self.app.session_state["flight_status"], "landing")
        self.assertIn("landing_canvas", self.app.session_state)
        starting_fuel = self.app.session_state["flight_fuel_remaining_kg"]
        starting_action_id = self.app.session_state["landing_action_id"]
        self._submit_landing_step(0.2, True)
        self.assertEqual(self.app.session_state["flight_status"], "landing")
        self.assertLess(self.app.session_state["landing_velocity_m_s"], 8)
        self.assertLess(self.app.session_state["landing_altitude_m"], 180)
        self.assertEqual(self.app.session_state["landing_last_action"], "burn")
        self.assertEqual(
            self.app.session_state["landing_action_id"],
            starting_action_id + 1,
        )
        self.assertLess(
            self.app.session_state["flight_fuel_remaining_kg"],
            starting_fuel,
        )
        thrust_sound = self._sound_payloads()[-1]
        self._submit_landing_step(0.2, False)
        coast_sound = self._sound_payloads()[-1]
        self.assertNotEqual(thrust_sound, coast_sound)
        self.assertEqual(self.app.session_state["landing_last_action"], "coast")
        self.assertEqual(
            self.app.session_state["landing_action_id"],
            starting_action_id + 2,
        )
        self.app.button(key="back_to_assembly").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertEqual(self.app.session_state["flight_status"], "assembly")
        self.assertEqual(self.app.session_state["mission_destination"], "Jupiter")
        self.assertFalse(self.app.exception)

    def test_slingshot_failure_retry_and_success_are_session_state_driven(self):
        self._launch_slingshot()
        self._submit_slingshot_vector(0, 12)

        self.assertEqual(
            self.app.session_state["slingshot_outcome"]["status"],
            "failure",
        )
        self.assertEqual(self.app.session_state["mission_phase"], 3)
        first_attempt = self.app.session_state["slingshot_attempt_id"]
        self.app.session_state["gravity_slingshot"] = {
            "kind": "retry",
            "attempt_id": first_attempt,
        }
        self.app.run()

        self.assertEqual(
            self.app.session_state["slingshot_attempt_id"],
            first_attempt + 1,
        )
        self.assertEqual(self.app.session_state["slingshot_attempt_number"], 2)
        self.assertIsNone(self.app.session_state["slingshot_outcome"])
        self._submit_successful_slingshot()
        self.assertEqual(
            self.app.session_state["slingshot_outcome"]["status"],
            "success",
        )
        self.assertFalse(self.app.exception)

    def test_slingshot_second_failure_shows_diagnostic_scorecard(self):
        self._launch_slingshot()
        self._submit_slingshot_vector(0, 12)
        first_attempt = self.app.session_state["slingshot_attempt_id"]
        self.app.session_state["gravity_slingshot"] = {
            "kind": "retry",
            "attempt_id": first_attempt,
        }
        self.app.run()
        self._submit_slingshot_vector(0, 12)

        self.assertEqual(self.app.session_state["slingshot_attempt_number"], 2)
        self.assertEqual(
            self.app.session_state["slingshot_outcome"]["status"],
            "failure",
        )
        self.assertTrue(
            any(item.value == "## Mission Failure" for item in self.app.markdown)
        )
        self.assertTrue(
            any("escaped" in item.value for item in self.app.error)
        )
        self.app.button(key="return_to_design_after_failure").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertFalse(self.app.exception)

    def test_planetarium_uses_body_specific_surface_styles_and_distance_timing(self):
        self._advance_to_arrival("beginner_preset")
        frames = [frame.proto.srcdoc for frame in self.app.get("iframe")]
        self.assertTrue(any('dur="4.00s"' in frame for frame in frames))
        self.assertTrue(any('id="earth-ocean"' in frame for frame in frames))
        self.assertTrue(any('fill="#55bd83"' in frame for frame in frames))

    def test_landing_success_crash_and_restart_conditions(self):
        self._advance_to_arrival("beginner_preset")
        self.app.button(key="begin_landing").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 5)

        self.app.session_state["landing_altitude_m"] = 1
        self.app.session_state["landing_velocity_m_s"] = 0.1
        self._submit_landing_step(0.2, False)
        self.assertEqual(self.app.session_state["flight_status"], "landed")
        self.assertEqual(self.app.session_state["landing_score"], 95)
        self.assertTrue(
            any("Mission Complete" in item.value for item in self.app.markdown)
        )
        self.assertTrue(
            any(
                item.label == "Total Mission Score"
                for item in self.app.metric
            )
        )
        total_score = next(
            item.value
            for item in self.app.metric
            if item.label == "Total Mission Score"
        )
        self.assertEqual(total_score, "133.0")
        self.assertEqual(self.app.session_state["slingshot_bodies_orbited"], 0)
        self.assertFalse(self.app.exception)

    def test_landing_failure_allows_one_retry_then_shows_diagnostics(self):
        self._advance_to_arrival("beginner_preset")
        self.app.button(key="begin_landing").click().run()
        self.app.session_state["landing_altitude_m"] = 1
        self.app.session_state["landing_velocity_m_s"] = 8
        self._submit_landing_step(0.2, False)
        self.assertEqual(self.app.session_state["flight_status"], "crashed")
        self.assertIn("exceeded the 6 m/s limit", self.app.session_state["flight_result"])
        self.assertEqual(self.app.session_state["landing_attempt_number"], 1)
        self.app.button(key="restart_landing").click().run()
        self.assertEqual(self.app.session_state["landing_attempt_number"], 2)
        self.app.session_state["landing_altitude_m"] = 500
        self.app.session_state["flight_fuel_remaining_kg"] = 0
        self._submit_landing_step(0.2, False)
        self.assertEqual(self.app.session_state["flight_status"], "crashed")
        self.assertIn("Fuel depleted", self.app.session_state["flight_result"])
        self.assertTrue(
            any(item.value == "## Mission Failure" for item in self.app.markdown)
        )
        self.assertTrue(
            any("Fuel depleted" in item.value for item in self.app.error)
        )
        self.app.button(key="return_to_design_after_failure").click().run()
        self.assertEqual(self.app.session_state["mission_phase"], 2)
        self.assertFalse(self.app.exception)

    def test_landing_canvas_has_planet_surfaces_vertical_gauges_and_outcomes(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Neptune"
        self.app.session_state["flight_fuel_capacity_kg"] = 800
        self.app.session_state["flight_fuel_remaining_kg"] = 800
        self.app.session_state["landing_altitude_m"] = 180
        self.app.session_state["landing_velocity_m_s"] = 8
        self.app.run()

        canvas_path = (
            Path(__file__).resolve().parents[1]
            / "landing_canvas"
            / "index.html"
        )
        canvas = canvas_path.read_text(encoding="utf-8")
        self.assertTrue(
            any(
                item.label == "Real physics: thrust, fuel, and touchdown"
                for item in self.app.expander
            )
        )
        landing_markdown = "\n".join(item.value for item in self.app.markdown)
        self.assertIn("changing vehicle mass", landing_markdown)
        self.assertIn(
            "https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/ideal-rocket-equation/",
            landing_markdown,
        )
        for expected in (
            "Neptune:",
            "drawGauge",
            "SAFE",
            "≤ 6",
            "spawnExhaust",
            "spawnExplosion",
            "HOLD TO BURN RETRO-THRUST",
            "SURFACE GRAVITY",
            "SAFE_VELOCITY = 6",
            "descentGravity",
            "SOFT-START BELOW",
            "Contact at 4 m",
            "height: 32px",
            "streamlit:setComponentValue",
            'kind: "snapshot"',
            "TOUCHDOWN CONFIRMED",
            "LANDING FAILED",
            "ResizeObserver",
        ):
            self.assertIn(expected, canvas)
        self.assertNotIn("STEP_HEARTBEAT_S", canvas)
        self.assertEqual(canvas.count("sendSnapshot();"), 1)
        self.assertIn("landing_canvas", self.app.session_state)
        self.assertFalse(self.app.exception)

    def test_landing_snapshots_sync_once_without_physics_heartbeat_reruns(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Mars"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 1000
        self.app.session_state["landing_altitude_m"] = 180
        self.app.session_state["landing_velocity_m_s"] = 8
        self.app.run()

        self._submit_landing_snapshot(1, 150, 12, 900, True)

        self.assertEqual(self.app.session_state["landing_altitude_m"], 150)
        self.assertEqual(self.app.session_state["landing_velocity_m_s"], 12)
        self.assertEqual(
            self.app.session_state["flight_fuel_remaining_kg"],
            900,
        )
        self.assertEqual(self.app.session_state["landing_last_action"], "burn")
        action_id = self.app.session_state["landing_action_id"]

        self._submit_landing_snapshot(1, 150, 12, 900, True)
        self.assertEqual(self.app.session_state["landing_action_id"], action_id)
        self.assertFalse(self.app.exception)

    def test_landing_snapshot_touchdown_uses_server_safe_speed_threshold(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Mars"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 900
        self.app.session_state["landing_altitude_m"] = 180
        self.app.session_state["landing_velocity_m_s"] = 8
        self.app.run()

        self._submit_landing_snapshot(1, 4, 5, 900, False)
        self.assertEqual(self.app.session_state["flight_status"], "landed")
        self.assertEqual(self.app.session_state["landing_score"], 90)

        self.app.button(key="restart_mission_after_victory").click().run()
        self._advance_to_arrival("beginner_preset")
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 900
        self.app.button(key="begin_landing").click().run()
        self.app.session_state["landing_attempt_number"] = 1
        self._submit_landing_snapshot(2, 4, 6.1, 900, False)
        self.assertEqual(self.app.session_state["flight_status"], "crashed")
        self.assertIn("exceeded the 6 m/s limit", self.app.session_state["flight_result"])
        self.assertFalse(self.app.exception)

    def test_touchdown_at_exactly_six_meters_per_second_is_successful(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Mars"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 1000
        self.app.session_state["landing_altitude_m"] = 0
        self.app.session_state["landing_velocity_m_s"] = 6
        self.app.run()

        self._submit_landing_step(0.2, True)

        self.assertEqual(self.app.session_state["flight_status"], "landed")
        self.assertEqual(self.app.session_state["landing_velocity_m_s"], 6)
        self.assertFalse(self.app.exception)

    def test_jupiter_retro_thrust_can_brake_to_a_safe_touchdown(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Jupiter"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 1000
        self.app.session_state["landing_altitude_m"] = 4.5
        self.app.session_state["landing_velocity_m_s"] = 5
        self.app.run()

        self._submit_landing_step(0.2, True)
        for _ in range(3):
            if self.app.session_state["flight_status"] != "landing":
                break
            self._submit_landing_step(0.2, False)

        self.assertEqual(self.app.session_state["flight_status"], "landed")
        self.assertLessEqual(self.app.session_state["landing_velocity_m_s"], 6)
        self.assertFalse(self.app.exception)

    def test_jupiter_descent_uses_full_surface_gravity(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Jupiter"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 1000
        self.app.session_state["landing_altitude_m"] = 180
        self.app.session_state["landing_velocity_m_s"] = 6
        self.app.run()

        self._submit_landing_step(0.2, False)

        self.assertAlmostEqual(
            self.app.session_state["landing_velocity_m_s"],
            6 + 24.79 * 1.05 * 0.2,
        )
        self.assertLess(self.app.session_state["landing_altitude_m"], 180)
        self.assertFalse(self.app.exception)

    def test_zero_velocity_uses_soft_start_gravity(self):
        self.app.session_state["mission_phase"] = 5
        self.app.session_state["flight_status"] = "landing"
        self.app.session_state["mission_destination"] = "Jupiter"
        self.app.session_state["flight_fuel_capacity_kg"] = 1000
        self.app.session_state["flight_fuel_remaining_kg"] = 1000
        self.app.session_state["landing_altitude_m"] = 180
        self.app.session_state["landing_velocity_m_s"] = 0
        self.app.run()

        self._submit_landing_step(0.2, False)

        self.assertAlmostEqual(
            self.app.session_state["landing_velocity_m_s"],
            24.79 * 1.05 * 0.15 * 0.2,
        )
        self.assertFalse(self.app.exception)

    def test_sidebar_presets_load_mission_and_play_menu_cue(self):
        self.assertEqual(self.app.sidebar.slider(key="interface_volume").value, 35)
        sidebar_expanders = list(self.app.sidebar.expander)
        self.assertEqual(len(sidebar_expanders), 2)
        self.assertEqual(
            {expander.label for expander in sidebar_expanders},
            {"About NASA Space Apps", "Simulation Fidelity & Engineering Assumptions"},
        )
        self.assertTrue(
            any("Super Intelligence (SI/AI)" in item.value for item in self.app.sidebar.caption)
        )
        self.assertTrue(
            any("Atmospheric drag" in item.value for item in self.app.sidebar.markdown)
        )
        sidebar_markdown = "\n".join(
            item.value for item in self.app.sidebar.markdown
        )
        for source in (
            "https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/ideal-rocket-equation/",
            "https://tfaws.nasa.gov/wp-content/uploads/Rickman-Presentation.pdf",
            "https://science.nasa.gov/learn/basics-of-space-flight/chapter3-1/",
            "Kepler's laws",
            "attitude",
        ):
            with self.subTest(source=source):
                self.assertIn(source, sidebar_markdown)

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
