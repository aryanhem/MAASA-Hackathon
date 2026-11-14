"""Data and arcade-style calculations for the space mission design game."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Dict, Mapping, Optional

import pandas as pd
import streamlit as st


LAUNCH_SITES = (
    "Guiana Space Centre",
    "Kennedy Space Center",
    "Baikonur Cosmodrome",
    "China Jiuquan Launch Center",
)

DESTINATION_DIFFICULTY: Dict[str, float] = {
    "Moon": 0.7,
    "Mars": 1.0,
    "Mercury": 1.2,
    "Venus": 1.7,
    "Saturn": 2.0,
    "Neptune": 1.8,
    "Jupiter": 2.1,
    "Uranus": 1.6,
}

LAUNCHPAD_MODIFIERS: Dict[str, Dict[str, float]] = {
    "Guiana Space Centre": {
        "Moon": 0.8,
        "Mercury": 1.0,
        "Venus": 1.0,
        "Mars": 1.0,
        "Jupiter": 1.0,
        "Saturn": 1.0,
        "Uranus": 1.1,
        "Neptune": 1.1,
    },
    "Kennedy Space Center": {
        "Moon": 0.9,
        "Mercury": 1.2,
        "Venus": 1.1,
        "Mars": 1.1,
        "Jupiter": 1.1,
        "Saturn": 1.2,
        "Uranus": 1.3,
        "Neptune": 1.3,
    },
    "Baikonur Cosmodrome": {
        "Moon": 1.1,
        "Mercury": 1.5,
        "Venus": 1.4,
        "Mars": 1.3,
        "Jupiter": 1.5,
        "Saturn": 1.6,
        "Uranus": 1.7,
        "Neptune": 1.8,
    },
    "China Jiuquan Launch Center": {
        "Moon": 1.0,
        "Mercury": 1.3,
        "Venus": 1.2,
        "Mars": 1.2,
        "Jupiter": 1.3,
        "Saturn": 1.4,
        "Uranus": 1.5,
        "Neptune": 1.6,
    },
}

COMPONENT_CHOICES: Dict[str, Dict[str, Dict[str, float]]] = {
    "hull": {
        "Lightweight Aluminum Frame": {"mass_kg": 300},
        "Carbon-Composite Shell": {"mass_kg": 550},
        "Reinforced Titanium-Alloy Hull": {"mass_kg": 1100},
    },
    "power": {
        "Standard Solar Array Panels": {"mass_kg": 200},
        "High-Efficiency Deep-Space Solar Wings": {"mass_kg": 450},
        "Radioisotope Thermoelectric Generator (RTG)": {"mass_kg": 350},
    },
    "avionics": {
        "Basic Sun & Earth Sensors": {"mass_kg": 50},
        "Advanced IMU & Star Tracker": {"mass_kg": 120},
        "Redundant Deep-Space Command Computer": {"mass_kg": 180},
    },
    "thermal": {
        "Passive MLI Insulation Blankets": {"mass_kg": 80},
        "Active Fluid-Loop Heat Exchangers": {"mass_kg": 220},
        "Ablative Thermal Protection System (TPS) Shield": {"mass_kg": 600},
    },
    "instruments": {
        "Optical Imaging Camera Suite": {"mass_kg": 100},
        "Geological Drill & Sample Spectrometer": {"mass_kg": 250},
        "Atmospheric Gas Analyzer": {"mass_kg": 180},
    },
}

HULL_MINIMUM_BY_DESTINATION: Dict[str, str] = {
    "Moon": "Lightweight Aluminum Frame",
    "Mars": "Lightweight Aluminum Frame",
    "Mercury": "Carbon-Composite Shell",
    "Venus": "Carbon-Composite Shell",
    "Uranus": "Reinforced Titanium-Alloy Hull",
    "Saturn": "Reinforced Titanium-Alloy Hull",
    "Jupiter": "Reinforced Titanium-Alloy Hull",
    "Neptune": "Reinforced Titanium-Alloy Hull",
}

ENGINE_CHOICES: Dict[str, Dict[str, float]] = {
    "Solid Rocket Booster (SRB)": {"mass_kg": 850, "upthrust": 2800},
    "Standard Kerolox Engine": {"mass_kg": 500, "upthrust": 1600},
    "High-Performance Hydrolox Engine": {"mass_kg": 320, "upthrust": 1300},
    "Advanced Ion Thruster": {"mass_kg": 90, "upthrust": 250},
    "Heavy-Duty Deep Space Cluster": {"mass_kg": 1200, "upthrust": 8200},
}

FUEL_TANK_CHOICES: Dict[str, Dict[str, float]] = {
    "Small Reserve Tank": {"mass_kg": 200},
    "Standard Interplanetary Tank": {"mass_kg": 600},
    "Heavy-Duty Deep Space Pod": {"mass_kg": 800},
}


@dataclass(frozen=True)
class MissionResult:
    total_mass_kg: float
    required_upthrust: float
    selected_upthrust: float
    success: bool
    progress_percentage: float


def _selected_option(
    options: Mapping[str, Mapping[str, float]],
    selection: Optional[str],
    category: str,
) -> Optional[Mapping[str, float]]:
    if not selection:
        return None
    try:
        return options[selection]
    except KeyError as error:
        raise ValueError(f"Unknown {category} selection: {selection!r}.") from error


def calculate_total_mass(
    selected_components: Mapping[str, Optional[str]],
    engine: Optional[str],
    fuel_tank: Optional[str],
) -> float:
    """Return selected component mass in kg; unselected parts contribute zero."""
    mass = 0.0
    for category, choices in COMPONENT_CHOICES.items():
        selection = selected_components.get(category)
        option = _selected_option(choices, selection, category)
        if option:
            mass += option["mass_kg"]

    engine_option = _selected_option(ENGINE_CHOICES, engine, "engine")
    if engine_option:
        mass += engine_option["mass_kg"]
    tank_option = _selected_option(FUEL_TANK_CHOICES, fuel_tank, "fuel tank")
    if tank_option:
        mass += tank_option["mass_kg"]
    return mass


def calculate_required_upthrust(
    total_mass_kg: float,
    launch_site: Optional[str],
    destination: Optional[str],
) -> float:
    """Apply the team's game modifiers; this is not a physical rocket model."""
    if (
        isinstance(total_mass_kg, bool)
        or not isinstance(total_mass_kg, (int, float))
        or not isfinite(total_mass_kg)
        or total_mass_kg < 0
    ):
        raise ValueError("Total mass must be a non-negative number of kilograms.")
    if launch_site and launch_site not in LAUNCHPAD_MODIFIERS:
        raise ValueError(f"Unknown launch site: {launch_site!r}.")
    if destination and destination not in DESTINATION_DIFFICULTY:
        raise ValueError(f"Unknown destination: {destination!r}.")
    if total_mass_kg == 0 or not launch_site or not destination:
        return 0.0
    if destination not in LAUNCHPAD_MODIFIERS[launch_site]:
        raise ValueError(
            f"No launch-site modifier is defined for {launch_site!r} to "
            f"{destination!r}."
        )

    return (
        total_mass_kg
        * LAUNCHPAD_MODIFIERS[launch_site][destination]
        * DESTINATION_DIFFICULTY[destination]
    )


def evaluate_mission(
    selected_components: Mapping[str, Optional[str]],
    engine: Optional[str],
    fuel_tank: Optional[str],
    launch_site: Optional[str],
    destination: Optional[str],
) -> MissionResult:
    """Calculate mass, thrust requirement, success, and uncapped progress."""
    total_mass = calculate_total_mass(selected_components, engine, fuel_tank)
    required_upthrust = calculate_required_upthrust(
        total_mass, launch_site, destination
    )
    engine_option = _selected_option(ENGINE_CHOICES, engine, "engine")
    selected_upthrust = engine_option["upthrust"] if engine_option else 0.0
    has_requirement = required_upthrust > 0

    return MissionResult(
        total_mass_kg=total_mass,
        required_upthrust=required_upthrust,
        selected_upthrust=selected_upthrust,
        success=has_requirement and selected_upthrust >= required_upthrust,
        progress_percentage=(
            selected_upthrust / required_upthrust * 100 if has_requirement else 0.0
        ),
    )
