"""Deterministic arcade trajectory model for the gravity slingshot phase."""

from __future__ import annotations

from math import hypot, isfinite
from typing import TypedDict

WORLD_WIDTH = 900
WORLD_HEIGHT = 480
LAUNCH_POSITION = (139.0, 320.0)
MAX_LAUNCH_SPEED = 24.0
SIMULATION_STEP_S = 0.12
MAX_SIMULATION_TIME_S = 60.0


class Body(TypedDict):
    name: str
    x: float
    y: float
    radius: float
    mu: float
    kind: str
    color: str
    surface: str
    rings: bool


class TrajectoryResult(TypedDict):
    status: str
    reason: str
    points: list[tuple[float, float]]
    impact_speed: float
    bodies_orbited: int


TARGET_RADII = {
    "Moon": 38.0,
    "Mercury": 39.0,
    "Venus": 43.0,
    "Mars": 41.0,
    "Jupiter": 58.0,
    "Saturn": 53.0,
    "Uranus": 47.0,
    "Neptune": 47.0,
}
PLANET_DETAILS: dict[str, tuple[float, str, str, float, bool]] = {
    "Mercury": (29.0, "#a9a9a5", "mercury", 12000.0, False),
    "Venus": (33.0, "#d5b078", "venus", 18000.0, False),
    "Moon": (35.0, "#aeb9ca", "moon", 24000.0, False),
    "Mars": (29.0, "#d77b58", "mars", 28000.0, False),
    "Jupiter": (39.0, "#d59a68", "jupiter", 42000.0, False),
    "Saturn": (35.0, "#d7be82", "saturn", 38000.0, True),
    "Uranus": (31.0, "#79cbd1", "uranus", 34000.0, False),
    "Neptune": (32.0, "#417fc4", "neptune", 36000.0, False),
}
DESTINATION_ROUTES = {
    "Moon": ("Orbital satellite", "Lunar debris", "Debris cloud"),
    "Mercury": ("Earth satellite", "Orbital debris"),
    "Venus": ("Earth satellite", "Orbital debris"),
    "Mars": ("Earth satellite", "Orbital debris"),
    "Jupiter": ("Mars", "Asteroid belt"),
    "Saturn": ("Mars", "Asteroid belt", "Jupiter"),
    "Uranus": ("Mars", "Asteroid belt", "Jupiter", "Saturn"),
    "Neptune": ("Mars", "Asteroid belt", "Jupiter", "Saturn", "Uranus"),
}
SMALL_BODY_DETAILS: dict[str, tuple[float, str, str, float]] = {
    "Orbital satellite": (11.0, "#b9c9dc", "satellite", 5200.0),
    "Earth satellite": (12.0, "#9cb6cf", "satellite", 5800.0),
    "Lunar debris": (13.0, "#a9b4c3", "debris", 0.0),
    "Debris cloud": (15.0, "#8190a3", "debris", 0.0),
    "Orbital debris": (14.0, "#8998aa", "debris", 0.0),
    "Asteroid belt": (16.0, "#9b8b79", "asteroids", 0.0),
}


def trajectory_bodies(destination: str) -> list[Body]:
    """Return only the planets, satellites, and hazards on this arcade route."""
    if destination not in TARGET_RADII:
        raise ValueError(f"Unknown trajectory destination: {destination!r}.")
    target_radius = TARGET_RADII[destination]
    bodies: list[Body] = [
        {
            "name": "Earth",
            "x": 100.0,
            "y": 320.0,
            "radius": 34.0,
            "mu": 0.0,
            "kind": "launch",
            "color": "#368fd0",
            "surface": "earth",
            "rings": False,
        },
    ]
    route = DESTINATION_ROUTES[destination]
    target_x, target_y = 800.0, 250.0
    for index, name in enumerate(route):
        x = 139.0 + (target_x - 139.0) * (index + 1) / (len(route) + 1)
        y = 185.0 if index % 2 == 0 else 360.0
        if name in PLANET_DETAILS:
            radius, color, surface, mu, rings = PLANET_DETAILS[name]
            body: Body = {
                "name": name,
                "x": x,
                "y": y,
                "radius": radius,
                "mu": mu,
                "kind": "gravity",
                "color": color,
                "surface": surface,
                "rings": rings,
            }
        else:
            radius, color, surface, mu = SMALL_BODY_DETAILS[name]
            body = {
                "name": name,
                "x": x,
                "y": y,
                "radius": radius,
                "mu": mu,
                "kind": "gravity" if mu else "hazard",
                "color": color,
                "surface": surface,
                "rings": False,
            }
        bodies.append(body)

    radius, color, surface, _, rings = PLANET_DETAILS[destination]
    bodies.append({
        "name": destination,
        "x": target_x,
        "y": target_y,
        "radius": target_radius,
        "mu": 55000.0,
        "kind": "target",
        "color": color,
        "surface": surface,
        "rings": rings,
    })
    return bodies


def simulate_trajectory(
    destination: str,
    velocity_x: float,
    velocity_y: float,
) -> TrajectoryResult:
    """Integrate a bounded, simplified two-dimensional gravity trajectory."""
    if any(
        not isinstance(value, (int, float)) or isinstance(value, bool)
        for value in (velocity_x, velocity_y)
    ):
        raise ValueError("Launch velocity must contain finite numeric values.")
    if not isfinite(velocity_x) or not isfinite(velocity_y):
        raise ValueError("Launch velocity must contain finite numeric values.")
    if hypot(velocity_x, velocity_y) > MAX_LAUNCH_SPEED:
        raise ValueError("Launch velocity exceeds the arcade launch limit.")

    bodies = trajectory_bodies(destination)
    earth, *route_bodies = bodies
    x, y = LAUNCH_POSITION
    vx, vy = float(velocity_x), float(velocity_y)
    points = [(x, y)]
    encountered_bodies: set[str] = set()
    steps = int(MAX_SIMULATION_TIME_S / SIMULATION_STEP_S)

    for _ in range(steps):
        ax = 0.0
        ay = 0.0
        for body in route_bodies:
            dx = body["x"] - x
            dy = body["y"] - y
            distance_squared = dx * dx + dy * dy
            if body["mu"] and distance_squared:
                softened_distance = distance_squared + body["radius"] ** 2
                acceleration = body["mu"] / softened_distance
                ax += acceleration * dx / distance_squared**0.5
                ay += acceleration * dy / distance_squared**0.5

        acceleration_magnitude = hypot(ax, ay)
        if acceleration_magnitude > 3.2:
            scale = 3.2 / acceleration_magnitude
            ax *= scale
            ay *= scale
        vx += ax * SIMULATION_STEP_S
        vy += ay * SIMULATION_STEP_S
        x += vx * SIMULATION_STEP_S
        y += vy * SIMULATION_STEP_S
        points.append((x, y))

        for body in route_bodies:
            if (
                body["kind"] == "gravity"
                and hypot(body["x"] - x, body["y"] - y) <= body["radius"] * 3.5
            ):
                encountered_bodies.add(body["name"])

        for body in bodies:
            if body["kind"] == "launch":
                continue
            distance = hypot(body["x"] - x, body["y"] - y)
            if distance <= body["radius"]:
                if body["kind"] == "target":
                    return {
                        "status": "success",
                        "reason": (
                            f"Trajectory reached {destination} after "
                            f"{len(encountered_bodies)} gravity assists."
                        ),
                        "points": points,
                        "impact_speed": hypot(vx, vy),
                        "bodies_orbited": len(encountered_bodies),
                    }
                return {
                    "status": "failure",
                    "reason": f"Trajectory collided with {body['name']}.",
                    "points": points,
                    "impact_speed": hypot(vx, vy),
                    "bodies_orbited": len(encountered_bodies),
                }

        if hypot(earth["x"] - x, earth["y"] - y) <= earth["radius"]:
            return {
                "status": "failure",
                "reason": "Trajectory re-entered the launch planet.",
                "points": points,
                "impact_speed": hypot(vx, vy),
                "bodies_orbited": len(encountered_bodies),
            }
        if x < 0 or x > WORLD_WIDTH or y < 0 or y > WORLD_HEIGHT:
            return {
                "status": "failure",
                "reason": "Trajectory escaped the navigable flight corridor.",
                "points": points,
                "impact_speed": hypot(vx, vy),
                "bodies_orbited": len(encountered_bodies),
            }

    return {
        "status": "failure",
        "reason": "Trajectory missed the target within the flight window.",
        "points": points,
        "impact_speed": hypot(vx, vy),
        "bodies_orbited": len(encountered_bodies),
    }
