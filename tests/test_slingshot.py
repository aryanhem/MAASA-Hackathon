import unittest
from pathlib import Path

from slingshot import simulate_trajectory, trajectory_bodies


class SlingshotTrajectoryTests(unittest.TestCase):
    def test_launch_vector_reaches_target_with_deterministic_gravity(self):
        first = simulate_trajectory("Moon", 12, 2)
        second = simulate_trajectory("Moon", 12, 2)

        self.assertEqual(first["status"], "success")
        self.assertIn("Trajectory reached Moon", first["reason"])
        self.assertEqual(first["points"], second["points"])
        self.assertGreater(first["impact_speed"], 0)
        self.assertEqual(first["bodies_orbited"], second["bodies_orbited"])

    def test_missed_launch_and_obstacle_collision_fail(self):
        miss = simulate_trajectory("Moon", 0, 12)
        collision = simulate_trajectory("Moon", 0, 4)

        self.assertEqual(miss["status"], "failure")
        self.assertIn("escaped", miss["reason"])
        self.assertEqual(collision["status"], "failure")
        self.assertIn("Lunar debris", collision["reason"])

    def test_invalid_or_excessive_launch_velocity_is_rejected(self):
        for velocity_x, velocity_y in ((25, 0), (float("nan"), 0)):
            with self.subTest(velocity=(velocity_x, velocity_y)):
                with self.assertRaises(ValueError):
                    simulate_trajectory("Moon", velocity_x, velocity_y)

    def test_canvas_implements_drag_prediction_animation_and_retry(self):
        component_path = (
            Path(__file__).resolve().parents[1]
            / "gravity_slingshot"
            / "index.html"
        )
        component = component_path.read_text(encoding="utf-8")

        self.assertIn('addEventListener("pointerdown"', component)
        self.assertIn('addEventListener("pointermove"', component)
        self.assertIn('addEventListener("pointerup"', component)
        self.assertIn("ctx.setLineDash(dotted ? [3, 8] : [])", component)
        self.assertIn("requestAnimationFrame(animate)", component)
        self.assertIn("args.bodies", component)
        self.assertIn('new ResizeObserver', component)
        self.assertIn("getBoundingClientRect().height", component)
        self.assertIn("RETRY LAUNCH", component)
        self.assertIn("attempts_remaining", component)
        self.assertIn("bodies_orbited", component)
        self.assertIn("streamlit:setComponentValue", component)

    def test_routes_show_only_nearby_bodies_in_solar_system_order(self):
        moon_names = [
            body["name"] for body in trajectory_bodies("Moon")[1:]
        ]
        neptune_bodies = trajectory_bodies("Neptune")
        neptune_names = [body["name"] for body in neptune_bodies[1:]]
        expected_neptune_order = [
            "Mars",
            "Asteroid belt",
            "Jupiter",
            "Saturn",
            "Uranus",
            "Neptune",
        ]

        self.assertEqual(
            moon_names,
            ["Orbital satellite", "Lunar debris", "Debris cloud", "Moon"],
        )
        self.assertEqual(neptune_names, expected_neptune_order)
        self.assertTrue(all(
            left["x"] < right["x"]
            for left, right in zip(neptune_bodies[1:], neptune_bodies[2:])
        ))
        self.assertTrue(next(
            body for body in neptune_bodies if body["name"] == "Saturn"
        )["rings"])

    def test_destination_has_a_visible_gravity_target(self):
        target = next(
            body
            for body in trajectory_bodies("Jupiter")
            if body["kind"] == "target"
        )

        self.assertEqual(target["name"], "Jupiter")
        self.assertGreater(target["radius"], 0)
        self.assertGreater(target["mu"], 0)


if __name__ == "__main__":
    unittest.main()
