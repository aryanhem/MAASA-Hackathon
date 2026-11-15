"""Streamlit space mission design, flight, and landing game."""

import base64
from html import escape
import io
import math
from pathlib import Path
import struct
from textwrap import dedent
import time
import wave
from typing import Any, Optional

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from mission_design import (
    COMPONENT_CHOICES,
    DESTINATION_DIFFICULTY,
    ENGINE_CHOICES,
    FUEL_TANK_CHOICES,
    HULL_MINIMUM_BY_DESTINATION,
    LAUNCHPAD_MODIFIERS,
    LAUNCH_SITES,
    evaluate_mission,
)
from slingshot import simulate_trajectory, trajectory_bodies


gravity_slingshot = components.declare_component(
    "gravity_slingshot",
    path=str(Path(__file__).parent / "gravity_slingshot"),
)
landing_canvas = components.declare_component(
    "landing_canvas",
    path=str(Path(__file__).parent / "landing_canvas"),
)

SITE_COORDINATES = {
    "Guiana Space Centre": (5.236, -52.768),
    "Kennedy Space Center": (28.572, -80.649),
    "Baikonur Cosmodrome": (45.965, 63.305),
    "China Jiuquan Launch Center": (40.960, 100.298),
}

THEMES = {
    "Aurora": {
        "accent": "#55f2c2",
        "accent_secondary": "#6d8cff",
        "background": "radial-gradient(ellipse at 12% 0%, #142f3c 0%, #101723 40%, #0b1018 100%)",
        "panel": "rgba(16, 28, 40, 0.88)",
        "sidebar_end": "rgba(7, 12, 20, 0.96)",
        "metric_end": "rgba(10, 15, 25, 0.58)",
        "control_end": "rgba(18, 24, 36, 0.84)",
        "border": "rgba(85, 242, 194, 0.26)",
        "text": "#e9f4f7",
        "muted": "#a7bdc8",
        "button_text": "#07121a",
        "map_land": "#1e222a",
        "map_ocean": "#0e1117",
        "map_country": "#383e4a",
        "map_coast": "#383e4a",
        "map_text": "#f0f4fa",
        "map_marker": "#9aabc0",
        "map_marker_line": "#4b5a70",
        "schematic_end": "rgba(8,13,22,.72)",
        "alert_background": "#103c2d",
        "alert_text": "#d1fae5",
        "alert_border": "#34d399",
    },
    "Solar Flare": {
        "accent": "#ffc857",
        "accent_secondary": "#ff6d8a",
        "background": "radial-gradient(ellipse at 12% 0%, #40252a 0%, #211923 42%, #10121a 100%)",
        "panel": "rgba(39, 29, 34, 0.9)",
        "sidebar_end": "rgba(7, 12, 20, 0.96)",
        "metric_end": "rgba(10, 15, 25, 0.58)",
        "control_end": "rgba(18, 24, 36, 0.84)",
        "border": "rgba(255, 200, 87, 0.28)",
        "text": "#fff3e7",
        "muted": "#d4b7aa",
        "button_text": "#07121a",
        "map_land": "#1e222a",
        "map_ocean": "#0e1117",
        "map_country": "#383e4a",
        "map_coast": "#383e4a",
        "map_text": "#f0f4fa",
        "map_marker": "#9aabc0",
        "map_marker_line": "#4b5a70",
        "schematic_end": "rgba(8,13,22,.72)",
        "alert_background": "#463219",
        "alert_text": "#fff3c4",
        "alert_border": "#fbbf24",
    },
    "Arctic Pulse": {
        "accent": "#68d9ff",
        "accent_secondary": "#b18cff",
        "background": "radial-gradient(ellipse at 12% 0%, #1d2c49 0%, #151b30 42%, #0c111d 100%)",
        "panel": "rgba(24, 31, 51, 0.9)",
        "sidebar_end": "rgba(7, 12, 20, 0.96)",
        "metric_end": "rgba(10, 15, 25, 0.58)",
        "control_end": "rgba(18, 24, 36, 0.84)",
        "border": "rgba(104, 217, 255, 0.28)",
        "text": "#edf4ff",
        "muted": "#b0bfd8",
        "button_text": "#07121a",
        "map_land": "#1e222a",
        "map_ocean": "#0e1117",
        "map_country": "#383e4a",
        "map_coast": "#383e4a",
        "map_text": "#f0f4fa",
        "map_marker": "#9aabc0",
        "map_marker_line": "#4b5a70",
        "schematic_end": "rgba(8,13,22,.72)",
        "alert_background": "#1e3150",
        "alert_text": "#e0f2fe",
        "alert_border": "#38bdf8",
    },
    "Solaris": {
        "accent": "#9a3412",
        "accent_secondary": "#7e22ce",
        "background": "linear-gradient(135deg, #fff7ed 0%, #fef3c7 48%, #fdf2f8 100%)",
        "panel": "rgba(255, 255, 255, 0.92)",
        "sidebar_end": "rgba(255, 255, 255, 0.96)",
        "metric_end": "rgba(255, 255, 255, 0.74)",
        "control_end": "rgba(255, 247, 237, 0.92)",
        "border": "rgba(154, 52, 18, 0.24)",
        "text": "#1f2937",
        "muted": "#475569",
        "button_text": "#ffffff",
        "map_land": "#e8eee8",
        "map_ocean": "#dceef8",
        "map_country": "#b8c5d3",
        "map_coast": "#91a4b8",
        "map_text": "#334155",
        "map_marker": "#64748b",
        "map_marker_line": "#475569",
        "schematic_end": "rgba(255,255,255,.72)",
        "alert_background": "#dcfce7",
        "alert_text": "#14532d",
        "alert_border": "#86efac",
    },
    "Botanical": {
        "accent": "#047857",
        "accent_secondary": "#1d4ed8",
        "background": "linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 46%, #eff6ff 100%)",
        "panel": "rgba(255, 255, 255, 0.93)",
        "sidebar_end": "rgba(255, 255, 255, 0.97)",
        "metric_end": "rgba(240, 253, 244, 0.82)",
        "control_end": "rgba(239, 246, 255, 0.92)",
        "border": "rgba(4, 120, 87, 0.24)",
        "text": "#172b26",
        "muted": "#405b53",
        "button_text": "#ffffff",
        "map_land": "#e4eee2",
        "map_ocean": "#dceff2",
        "map_country": "#b6cbbf",
        "map_coast": "#8fa99b",
        "map_text": "#29443a",
        "map_marker": "#647c72",
        "map_marker_line": "#456257",
        "schematic_end": "rgba(240,253,244,.8)",
        "alert_background": "#dcfce7",
        "alert_text": "#14532d",
        "alert_border": "#86efac",
    },
    "Daybreak": {
        "accent": "#be123c",
        "accent_secondary": "#6d28d9",
        "background": "linear-gradient(135deg, #fff1f2 0%, #fff7ed 48%, #f5f3ff 100%)",
        "panel": "rgba(255, 255, 255, 0.93)",
        "sidebar_end": "rgba(255, 255, 255, 0.97)",
        "metric_end": "rgba(255, 241, 242, 0.82)",
        "control_end": "rgba(245, 243, 255, 0.94)",
        "border": "rgba(190, 18, 60, 0.22)",
        "text": "#2b1d27",
        "muted": "#5c4654",
        "button_text": "#ffffff",
        "map_land": "#f0e9e7",
        "map_ocean": "#e8eefb",
        "map_country": "#c8bfd0",
        "map_coast": "#a69bb2",
        "map_text": "#453849",
        "map_marker": "#766579",
        "map_marker_line": "#56475d",
        "schematic_end": "rgba(255,241,242,.8)",
        "alert_background": "#ffe4e6",
        "alert_text": "#881337",
        "alert_border": "#fda4af",
    },
}

DEFAULT_VOLUME = 35
SOUND_SAMPLE_RATE = 22050

ORBITAL_RADIUS_AU = {
    "Mercury": 0.39,
    "Venus": 0.72,
    "Moon": 1.00257,
    "Earth": 1.0,
    "Mars": 1.52,
    "Jupiter": 5.2,
    "Saturn": 9.5,
    "Uranus": 19.2,
    "Neptune": 30.1,
}
PLANET_GRAVITY_M_S2 = {
    "Moon": 1.62,
    "Mercury": 3.70,
    "Venus": 8.87,
    "Mars": 3.71,
    "Jupiter": 24.79,
    "Saturn": 10.44,
    "Uranus": 8.69,
    "Neptune": 11.15,
}
LANDING_GRAVITY_GAME_SCALE = 1.05
LANDING_CONTACT_ALTITUDE_M = 4.0
LANDING_MAX_STEP_DURATION_S = 0.3
LANDING_ACTION_DURATION_S = 4.0
LANDING_START_ALTITUDE_M = 180.0
LANDING_START_VELOCITY_M_S = 9.0
LANDING_SAFE_TOUCHDOWN_SPEED_M_S = 6.0
LANDING_SOFT_START_SPEED_M_S = LANDING_SAFE_TOUCHDOWN_SPEED_M_S
LANDING_MIN_GRAVITY_FRACTION = 0.15
LANDING_MAX_ATTEMPTS = 2
SLINGSHOT_MAX_ATTEMPTS = 2
SLINGSHOT_FUEL_COST_PER_BODY = 0.04
COMPONENT_RESEARCH_POINTS = {
    "hull": {
        "Lightweight Aluminum Frame": 10,
        "Carbon-Composite Shell": 20,
        "Reinforced Titanium-Alloy Hull": 30,
    },
    "power": {
        "Standard Solar Array Panels": 8,
        "High-Efficiency Deep-Space Solar Wings": 16,
        "Radioisotope Thermoelectric Generator (RTG)": 20,
    },
    "avionics": {
        "Basic Sun & Earth Sensors": 5,
        "Advanced IMU & Star Tracker": 12,
        "Redundant Deep-Space Command Computer": 20,
    },
    "thermal": {
        "Passive MLI Insulation Blankets": 5,
        "Active Fluid-Loop Heat Exchangers": 12,
        "Ablative Thermal Protection System (TPS) Shield": 20,
    },
    "instruments": {
        "Optical Imaging Camera Suite": 10,
        "Geological Drill & Sample Spectrometer": 25,
        "Atmospheric Gas Analyzer": 20,
    },
}
LAUNCH_SITE_SCORE_MULTIPLIERS = {
    "Guiana Space Centre": 1.0,
    "Kennedy Space Center": 1.5,
    "China Jiuquan Launch Center": 2.0,
    "Baikonur Cosmodrome": 2.2,
}


def calculate_mission_score(
    selected_components: dict[str, Optional[str]],
    launch_site: str,
    bodies_orbited: int,
    remaining_fuel_kg: float,
    starting_fuel_kg: float,
) -> dict[str, float]:
    """Score the mission locally so app.py tolerates an older deployed data module."""
    research_points = 0.0
    for category, weights in COMPONENT_RESEARCH_POINTS.items():
        selection = selected_components.get(category)
        if selection is None:
            raise ValueError(f"Select a {category} component before scoring.")
        try:
            research_points += weights[selection]
        except KeyError as error:
            raise ValueError(
                f"Unknown {category} component for research scoring: {selection!r}."
            ) from error

    try:
        launch_multiplier = LAUNCH_SITE_SCORE_MULTIPLIERS[launch_site]
    except KeyError as error:
        raise ValueError(f"Unknown launch site for scoring: {launch_site!r}.") from error

    if (
        not isinstance(bodies_orbited, int)
        or isinstance(bodies_orbited, bool)
        or bodies_orbited < 0
    ):
        raise ValueError("The number of gravity-assist bodies must be a non-negative integer.")
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in (remaining_fuel_kg, starting_fuel_kg)
    ):
        raise ValueError("Fuel values must be finite numbers of kilograms.")
    if starting_fuel_kg <= 0 or not 0 <= remaining_fuel_kg <= starting_fuel_kg:
        raise ValueError("Remaining fuel must be between zero and starting fuel.")

    body_bonus = 1.0 + 0.2 * bodies_orbited
    fuel_percentage = remaining_fuel_kg / starting_fuel_kg * 100
    return {
        "research_points": research_points,
        "launch_difficulty_multiplier": launch_multiplier,
        "bodies_orbited": float(bodies_orbited),
        "slingshot_body_bonus": body_bonus,
        "fuel_remaining_percentage": fuel_percentage,
        "fuel_efficiency_bonus": fuel_percentage,
        "total_score": round(
            research_points * launch_multiplier * body_bonus + fuel_percentage,
            1,
        ),
    }


def _landing_gravity(destination: str) -> float:
    """Return the destination's real surface gravity for the descent simulation."""
    return PLANET_GRAVITY_M_S2[destination] * LANDING_GRAVITY_GAME_SCALE


def _landing_retro_acceleration(gravity_m_s2: float) -> float:
    """Make held retro-thrust stronger than gravity on every destination."""
    return max(2.5, gravity_m_s2 * 3.0)


def _landing_descent_acceleration(velocity_m_s: float, gravity_m_s2: float) -> float:
    """Ease gravity in below the safe-speed threshold to avoid control chatter."""
    speed_fraction = min(
        1.0,
        max(0.0, velocity_m_s / LANDING_SOFT_START_SPEED_M_S),
    )
    gravity_fraction = LANDING_MIN_GRAVITY_FRACTION + (
        1.0 - LANDING_MIN_GRAVITY_FRACTION
    ) * speed_fraction
    return gravity_m_s2 * gravity_fraction


def _build_ui_sound(notes: tuple[tuple[float, float], ...]) -> str:
    """Create a brief synthesized UI cue without external audio assets."""
    duration = max(note_start + 0.085 for note_start, _ in notes)
    sample_count = int(SOUND_SAMPLE_RATE * duration)
    samples = bytearray()
    for index in range(sample_count):
        time_seconds = index / SOUND_SAMPLE_RATE
        amplitude = 0
        for note_start, frequency in notes:
            elapsed = time_seconds - note_start
            if 0 <= elapsed <= 0.085:
                envelope = (1 - elapsed / 0.085) ** 3
                amplitude += int(
                    4200 * envelope * math.sin(2 * math.pi * frequency * elapsed)
                )
        amplitude = max(-32767, min(32767, amplitude))
        samples.extend(struct.pack("<h", amplitude))

    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SOUND_SAMPLE_RATE)
        wav_file.writeframes(samples)
    return base64.b64encode(audio.getvalue()).decode("ascii")


UI_SOUNDS = {
    "select": _build_ui_sound(((0.0, 780.0),)),
    "menu": _build_ui_sound(((0.0, 520.0), (0.055, 720.0))),
    "phase": _build_ui_sound(((0.0, 540.0), (0.075, 720.0), (0.15, 960.0))),
    "flight": _build_ui_sound(
        ((0.0, 180.0), (0.12, 240.0), (0.24, 320.0), (0.36, 420.0))
    ),
    "coast": _build_ui_sound(((0.0, 540.0), (0.12, 460.0), (0.24, 390.0))),
    "thrust": _build_ui_sound(
        ((0.0, 150.0), (0.06, 210.0), (0.12, 165.0), (0.18, 245.0))
    ),
}


def _queue_menu_sound(sound_type: str = "select") -> None:
    if sound_type not in UI_SOUNDS:
        raise ValueError(f"Unknown interface sound: {sound_type!r}.")
    st.session_state.menu_sound_pending = sound_type


def _queue_menu_action_sound() -> None:
    _queue_menu_sound("menu")


def _queue_phase_sound() -> None:
    _queue_menu_sound("phase")


def _scroll_page_to_top() -> None:
    components.html(
        """
        <script>
          const parentWindow = window.parent;
          parentWindow.scrollTo({top: 0, behavior: "smooth"});
          const appView = parentWindow.document.querySelector(
            '[data-testid="stAppViewContainer"]'
          );
          if (appView) appView.scrollTo({top: 0, behavior: "smooth"});
          const mainSection = parentWindow.document.querySelector(
            'section.main'
          );
          if (mainSection) mainSection.scrollTo({top: 0, behavior: "smooth"});
        </script>
        """,
        height=0,
        scrolling=False,
    )


def _set_preset(preset: str) -> None:
    if preset == "beginner":
        launch_site = "Guiana Space Centre"
        destination = "Moon"
        components = {
            "hull": "Lightweight Aluminum Frame",
            "power": "Standard Solar Array Panels",
            "avionics": "Basic Sun & Earth Sensors",
            "thermal": "Passive MLI Insulation Blankets",
            "instruments": "Optical Imaging Camera Suite",
        }
        engine = "Standard Kerolox Engine"
        fuel_tank = "Small Reserve Tank"
    else:
        launch_site = "Guiana Space Centre"
        destination = "Jupiter"
        components = {
            "hull": "Reinforced Titanium-Alloy Hull",
            "power": "Standard Solar Array Panels",
            "avionics": "Basic Sun & Earth Sensors",
            "thermal": "Passive MLI Insulation Blankets",
            "instruments": "Optical Imaging Camera Suite",
        }
        engine = "Heavy-Duty Deep Space Cluster"
        fuel_tank = "Heavy-Duty Deep Space Pod"

    st.session_state.selected_launch_site = launch_site
    st.session_state.mission_destination = destination
    st.session_state.mission_components = components
    st.session_state.mission_engine = engine
    st.session_state.mission_fuel_tank = fuel_tank
    st.session_state.mission_phase = 2
    st.session_state.flight_status = "assembly"
    st.session_state.launch_site_picker = launch_site
    st.session_state.destination_picker = destination
    for category, selection in components.items():
        st.session_state[f"component_picker_{category}"] = selection
    st.session_state.engine_picker = engine
    st.session_state.fuel_tank_picker = fuel_tank
    _queue_menu_action_sound()


def _load_beginner_preset() -> None:
    _set_preset("beginner")


def _load_hardcore_preset() -> None:
    _set_preset("hardcore")


def _reset_mission() -> None:
    st.session_state.clear()
    st.session_state.interface_volume = DEFAULT_VOLUME
    st.session_state.menu_sound_pending = "menu"


def _build_launch_map(
    selected_site: Optional[str],
    theme: dict[str, str],
) -> go.Figure:
    """Create a selectable launch-site map styled for the selected theme."""
    accent = theme["accent"]
    fig = go.Figure()
    fig.add_trace(
        go.Scattergeo(
            lon=[-180, 180],
            lat=[0, 0],
            mode="lines",
            line={"color": accent, "width": 1.4, "dash": "dash"},
            opacity=0.72,
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lon=[3],
            lat=[3],
            mode="text",
            text=["EQUATOR · OPTIMAL BOOST ZONE"],
            textfont={"size": 10, "color": accent},
            hoverinfo="skip",
            showlegend=False,
        )
    )

    sites = list(LAUNCH_SITES)
    lats = [SITE_COORDINATES[site][0] for site in sites]
    lons = [SITE_COORDINATES[site][1] for site in sites]
    fig.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            mode="markers",
            marker={
                "size": [27 if site == selected_site else 10 for site in sites],
                "color": [
                    accent if site == selected_site else theme["map_marker"]
                    for site in sites
                ],
                "opacity": [0.26 if site == selected_site else 0.78 for site in sites],
                "line": {"width": 0},
            },
            hoverinfo="skip",
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scattergeo(
            lon=lons,
            lat=lats,
            mode="markers+text",
            customdata=sites,
            text=[
                f"{'✦ ' if site == selected_site else ''}{site}"
                for site in sites
            ],
            textposition=["top center" if lat > 15 else "bottom center" for lat in lats],
            textfont={"size": 10, "color": theme["map_text"]},
            marker={
                "size": [13 if site == selected_site else 8 for site in sites],
                "color": [
                    accent if site == selected_site else theme["map_marker"]
                    for site in sites
                ],
                "line": {
                    "color": [
                        accent if site == selected_site else theme["map_marker_line"]
                        for site in sites
                    ],
                    "width": [3 if site == selected_site else 1 for site in sites],
                },
            },
            hovertemplate="<b>%{customdata}</b><br>%{lat:.3f}°, %{lon:.3f}°<extra></extra>",
            showlegend=False,
        )
    )

    fig.update_layout(
        height=440,
        margin={"l": 0, "r": 0, "t": 8, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        clickmode="event+select",
        geo={
            "projection_type": "natural earth",
            "showland": True,
            "landcolor": theme["map_land"],
            "showocean": True,
            "oceancolor": theme["map_ocean"],
            "showcountries": True,
            "countrycolor": theme["map_country"],
            "bgcolor": "rgba(0,0,0,0)",
            "showframe": False,
            "showcoastlines": True,
            "coastlinecolor": theme["map_coast"],
            "lataxis": {"range": [-60, 82], "showgrid": False},
            "lonaxis": {"showgrid": False},
        },
        dragmode="select",
    )
    return fig


def _map_selected_site(event: Any) -> Optional[str]:
    """Get the selected facility name from a Plotly selection event."""
    try:
        points = event.selection.points
    except (AttributeError, KeyError, TypeError):
        return None

    for point in points:
        if point.get("curve_number") != 3:
            continue
        customdata = point.get("customdata")
        if isinstance(customdata, str) and customdata in SITE_COORDINATES:
            return customdata
        point_index = point.get("point_index")
        if isinstance(point_index, int) and 0 <= point_index < len(LAUNCH_SITES):
            return LAUNCH_SITES[point_index]
    return None


def _update_launch_site_from_picker() -> None:
    st.session_state.selected_launch_site = st.session_state.launch_site_picker
    st.session_state.ignore_map_selection = True
    _queue_menu_sound("select")


def _eligible_hulls(destination: str) -> list[str]:
    choice_names = list(COMPONENT_CHOICES["hull"])
    minimum_hull = HULL_MINIMUM_BY_DESTINATION[destination]
    return choice_names[choice_names.index(minimum_hull) :]


PART_DESCRIPTIONS = {
    "hull": {
        "Lightweight Aluminum Frame": (
            "A budget-friendly structural skeleton ideal for low-gravity bodies "
            "like the Moon and Mars."
        ),
        "Carbon-Composite Shell": (
            "A lightweight woven matrix offering high thermal and structural "
            "resilience against moderate entry forces."
        ),
        "Reinforced Titanium-Alloy Hull": (
            "Heavy-duty armored plating capable of surviving extreme atmospheric "
            "pressure and Jupiter's crushing gravity well."
        ),
    },
    "power": {
        "Standard Solar Array Panels": (
            "Lightweight photovoltaic wings that generate steady electrical "
            "power near inner planets."
        ),
        "High-Efficiency Deep-Space Solar Wings": (
            "Large, high-efficiency photovoltaic wings designed to gather useful "
            "power farther from the Sun."
        ),
        "Radioisotope Thermoelectric Generator (RTG)": (
            "A nuclear decay power source providing reliable energy regardless "
            "of solar distance."
        ),
    },
    "avionics": {
        "Basic Sun & Earth Sensors": (
            "A lightweight guidance and orientation package for straightforward "
            "lunar and near-Earth missions."
        ),
        "Advanced IMU & Star Tracker": (
            "Precision inertial and star-tracking instruments for accurate "
            "spacecraft navigation."
        ),
        "Redundant Deep-Space Command Computer": (
            "A fault-tolerant flight computer built to guide long-duration "
            "interplanetary trajectories."
        ),
    },
    "thermal": {
        "Passive MLI Insulation Blankets": (
            "Lightweight multi-layer reflective sheets shielding internal "
            "electronics from ambient space cold."
        ),
        "Active Fluid-Loop Heat Exchangers": (
            "A pumped coolant system designed to dissipate intense solar "
            "radiation heat near Mercury or Venus."
        ),
        "Ablative Thermal Protection System (TPS) Shield": (
            "Sacrificial thermal tiles that erode away to protect the spacecraft "
            "during high-speed atmospheric entry."
        ),
    },
    "instruments": {
        "Optical Imaging Camera Suite": (
            "Lightweight visible-light cameras for basic surface reconnaissance "
            "and imaging."
        ),
        "Geological Drill & Sample Spectrometer": (
            "A drill and spectrometer package for collecting and analyzing "
            "planetary surface samples."
        ),
        "Atmospheric Gas Analyzer": (
            "A scientific instrument for measuring the composition of a "
            "destination's atmosphere."
        ),
    },
    "engine": {
        "Solid Rocket Booster (SRB)": (
            "A high-thrust solid-propellant booster for powerful launch-stage "
            "acceleration."
        ),
        "Standard Kerolox Engine": (
            "A reliable liquid-propellant thruster providing balanced thrust "
            "for standard launches."
        ),
        "High-Performance Hydrolox Engine": (
            "A high-performance liquid-hydrogen engine designed for efficient "
            "launch and transfer burns."
        ),
        "Advanced Ion Thruster": (
            "A low-thrust, ultra-efficient electric propulsion system optimized "
            "for deep-space cruising."
        ),
        "Heavy-Duty Deep Space Cluster": (
            "A high-thrust multi-nozzle booster designed to lift massive "
            "payloads on demanding missions."
        ),
    },
    "fuel_tank": {
        "Small Reserve Tank": (
            "A compact fuel storage unit keeping dead weight to a minimum for "
            "short lunar hops."
        ),
        "Standard Interplanetary Tank": (
            "A balanced propellant tank providing fuel capacity for "
            "interplanetary transit."
        ),
        "Heavy-Duty Deep Space Pod": (
            "A large-capacity fuel pod to sustain heavy engines over long "
            "journeys."
        ),
    },
}


def _rocket_schematic(
    selected_components: dict[str, Optional[str]],
    engine: Optional[str],
    fuel_tank: Optional[str],
    theme: dict[str, str],
) -> str:
    """Render a live, selection-driven spacecraft preview as inline SVG."""
    hull = selected_components.get("hull")
    power = selected_components.get("power")
    avionics = selected_components.get("avionics")
    instruments = selected_components.get("instruments")
    thermal = selected_components.get("thermal")

    selected_parts = [
        (category, category.title(), selection)
        for category, selection in selected_components.items()
        if selection
    ]
    if engine:
        selected_parts.append(("engine", "Engine", engine))
    if fuel_tank:
        selected_parts.append(("fuel_tank", "Fuel tank", fuel_tank))
    description_markup = "".join(
        f"""
        <div class="part-description">
          <strong>{escape(label)} · {escape(selection)}</strong>
          <p>{escape(PART_DESCRIPTIONS[category][selection])}</p>
        </div>
        """
        for category, label, selection in selected_parts
    )
    if not description_markup:
        description_markup = (
            '<p class="empty-description">Choose a spacecraft part to see its '
            "description here. Hover over a selected part in the schematic for "
            "a quick tooltip.</p>"
        )

    def part_tooltip(category: str, selection: Optional[str]) -> str:
        if not selection:
            return ""
        return (
            f"<title>{escape(selection)}: "
            f"{escape(PART_DESCRIPTIONS[category][selection])}</title>"
        )

    hull_styles = {
        "Lightweight Aluminum Frame": {
            "width": 72,
            "fill": "url(#aluminum)",
            "detail": '<path d="M224 136H296M224 234H296" stroke="#d5e5ee" stroke-opacity=".62" stroke-width="2"/>',
        },
        "Carbon-Composite Shell": {
            "width": 86,
            "fill": "url(#carbon)",
            "detail": '<path d="M222 136H298M222 234H298" stroke="#93a6b8" stroke-opacity=".62" stroke-width="2"/>',
        },
        "Reinforced Titanium-Alloy Hull": {
            "width": 102,
            "fill": "url(#titanium)",
            "detail": '<path d="M214 136H306M214 234H306M214 244H306" stroke="#e5e9f1" stroke-opacity=".72" stroke-width="2"/>',
        },
    }
    hull_style = hull_styles.get(hull)
    body_width = hull_style["width"] if hull_style else 72
    half_width = body_width // 2
    body_fill = hull_style["fill"] if hull_style else "rgba(151, 174, 193, .08)"
    body_stroke = theme["accent"] if hull else "#8496a8"
    body_dash = "" if hull else 'stroke-dasharray="6 5"'

    tank = FUEL_TANK_CHOICES.get(fuel_tank) if fuel_tank else None
    tank_height = 0 if not tank else int(28 + tank["mass_kg"] * 0.065)
    tank_width = max(body_width - 22, 38)
    tank_markup = ""
    if tank:
        tank_top = 260 - tank_height
        tank_markup = f"""
        <g tabindex="0">{part_tooltip("fuel_tank", fuel_tank)}
        <rect x="{260 - tank_width // 2}" y="{tank_top}" width="{tank_width}"
          height="{tank_height}" rx="7" fill="url(#tank)" stroke="{theme["accent"]}"
          stroke-width="1.5"/>
        <path d="M{260 - tank_width // 2 + 8} {tank_top + 9}H{260 + tank_width // 2 - 8}"
          stroke="#ffffff" stroke-opacity=".42"/>
        <text x="260" y="{tank_top + tank_height // 2 + 4}" text-anchor="middle"
          class="small">{tank["mass_kg"]:,} kg FUEL</text>
        </g>
        """

    engine_data = ENGINE_CHOICES.get(engine) if engine else None
    engine_height = 0 if not engine_data else int(24 + engine_data["mass_kg"] * 0.035)
    engine_width = 0 if not engine_data else min(82, 34 + engine_data["mass_kg"] // 30)
    engine_top = 267
    engine_markup = ""
    if engine_data:
        engine_markup = f"""
        <g tabindex="0">{part_tooltip("engine", engine)}
        <path d="M{260 - engine_width // 2} {engine_top}
          L{260 - engine_width // 2 + 8} {engine_top + engine_height}
          H{260 + engine_width // 2 - 8}
          L{260 + engine_width // 2} {engine_top}Z"
          fill="url(#engine)" stroke="#d7e4f0" stroke-opacity=".7" stroke-width="1.5"/>
        <path d="M{260 - engine_width // 3} {engine_top + engine_height}
          L260 {min(350, engine_top + engine_height + 28)}
          L{260 + engine_width // 3} {engine_top + engine_height}Z"
          fill="url(#flame)" opacity=".92"/>
        <text x="260" y="{engine_top + engine_height // 2 + 4}" text-anchor="middle"
          class="small">{engine_data["upthrust"]:,} THRUST</text>
        </g>
        """
    else:
        engine_markup = (
            '<path d="M246 267H274L268 286H252Z" fill="none" '
            'stroke="#8496a8" stroke-dasharray="4 4"/>'
        )

    if hull_style:
        fuselage_detail = hull_style["detail"]
    else:
        fuselage_detail = (
            '<path d="M232 136V258M288 136V258" stroke="#8496a8" '
            'stroke-opacity=".6" stroke-dasharray="4 5"/>'
        )
    hull_path = f"""M260 38
      Q{260 + half_width} 67 {260 + half_width} 112
      V260 Q260 274 {260 - half_width} 260
      V112 Q{260 - half_width} 67 260 38Z"""

    solar_panels = ""
    if power:
        solar_width = 82 if "High-Efficiency" in power else 62
        solar_panels = f"""
        <g tabindex="0">{part_tooltip("power", power)}
        <path d="M{260 - half_width} 162H{260 - half_width - solar_width}
          L{260 - half_width - solar_width - 8} 211H{260 - half_width}Z"
          fill="url(#solar)" stroke="{theme["accent_secondary"]}" stroke-width="1.5"/>
        <path d="M{260 + half_width} 162H{260 + half_width + solar_width}
          L{260 + half_width + solar_width + 8} 211H{260 + half_width}Z"
          fill="url(#solar)" stroke="{theme["accent_secondary"]}" stroke-width="1.5"/>
        <path d="M{260 - half_width - solar_width // 2} 164V209M{260 + half_width + solar_width // 2} 164V209"
          stroke="#d5e9ff" stroke-opacity=".55"/>
        </g>
        """

    avionics_lights = ""
    avionics_texture = ""
    if avionics:
        avionics_lights = f"""
        <g tabindex="0">{part_tooltip("avionics", avionics)}
        <circle cx="244" cy="111" r="3.5" fill="#68d9ff" class="glow"/>
        <circle cx="276" cy="111" r="3.5" fill="#68d9ff" class="glow"/>
        <path d="M244 111L231 124M276 111L289 124" stroke="#68d9ff"
          stroke-opacity=".75" stroke-width="1.5"/>
        </g>
        """
        avionics_texture = f"""
        <g tabindex="0">{part_tooltip("avionics", avionics)}
        <rect x="234" y="139" width="52" height="38" rx="4"
          fill="url(#avionics-circuit)" stroke="{theme["accent_secondary"]}"
          stroke-opacity=".75" stroke-width="1"/>
        <circle cx="260" cy="158" r="5" fill="none"
          stroke="{theme["accent_secondary"]}" stroke-width="1.4"/>
        <path d="M239 146H249M271 146H281M239 170H249M271 170H281"
          stroke="{theme["accent_secondary"]}" stroke-width="1"/>
        </g>
        """

    instrument_lights = ""
    instrument_texture = ""
    if instruments:
        instrument_lights = f"""
        <g tabindex="0">{part_tooltip("instruments", instruments)}
        <circle cx="249" cy="83" r="3" fill="#ffc857" class="glow"/>
        <circle cx="271" cy="83" r="3" fill="#ff6d8a" class="glow"/>
        <path d="M249 83L242 96M271 83L278 96" stroke="#ffc857"
          stroke-opacity=".7" stroke-width="1.2"/>
        </g>
        """
        instrument_texture = f"""
        <g tabindex="0">{part_tooltip("instruments", instruments)}
        <circle cx="260" cy="78" r="11" fill="none"
          stroke="{theme["accent_secondary"]}" stroke-opacity=".85" stroke-width="1.5"/>
        <circle cx="260" cy="78" r="6" fill="{theme["accent_secondary"]}"
          fill-opacity=".28" stroke="{theme["accent_secondary"]}" stroke-width="1"/>
        <path d="M260 63V68M260 88V93M245 78H250M270 78H275"
          stroke="{theme["accent_secondary"]}" stroke-width="1"/>
        </g>
        """

    thermal_texture = ""
    if thermal:
        thermal_color = (
            "#ff7d67" if "Ablative" in thermal else theme["accent_secondary"]
        )
        thermal_texture = f"""
        <g tabindex="0">{part_tooltip("thermal", thermal)}
        <path d="M220 207H300V240H220Z" fill="url(#thermal-insulation)"
          opacity=".78"/>
        <path d="M{260-half_width+5} 211H{260+half_width-5}
          M{260-half_width+5} 218H{260+half_width-5}
          M{260-half_width+5} 225H{260+half_width-5}
          M{260-half_width+5} 232H{260+half_width-5}"
          stroke="{thermal_color}"           stroke-width="2" stroke-linecap="round"
          opacity=".9"/>
        </g>
        """

    hull_label = escape(hull or "Hull not selected")
    engine_label = escape(engine or "Engine not selected")
    tank_label = escape(fuel_tank or "Fuel tank not selected")
    texture_defs = """
      <pattern id="weave" width="8" height="8" patternUnits="userSpaceOnUse">
        <path d="M0 0L8 8M8 0L0 8" stroke="#7f93a8" stroke-opacity=".28" stroke-width="1"/>
      </pattern>
      <linearGradient id="aluminum" x1="0" x2="1" y1="0" y2="0">
        <stop stop-color="#657d8d"/><stop offset=".48" stop-color="#d0dce2"/>
        <stop offset="1" stop-color="#536c7d"/>
      </linearGradient>
      <linearGradient id="carbon" x1="0" x2="1" y1="0" y2="1">
        <stop stop-color="#202b38"/><stop offset=".5" stop-color="#111820"/>
        <stop offset="1" stop-color="#394657"/>
      </linearGradient>
      <linearGradient id="titanium" x1="0" x2="1" y1="0" y2="0">
        <stop stop-color="#75808d"/><stop offset=".25" stop-color="#d9e0e9"/>
        <stop offset=".52" stop-color="#8493a3"/><stop offset=".78" stop-color="#e6ebf0"/>
        <stop offset="1" stop-color="#667484"/>
      </linearGradient>
      <linearGradient id="tank" x1="0" x2="1" y1="0" y2="0">
        <stop stop-color="#364a62"/><stop offset=".5" stop-color="#849bb3"/>
        <stop offset="1" stop-color="#2d4057"/>
      </linearGradient>
      <linearGradient id="engine" x1="0" x2="1" y1="0" y2="0">
        <stop stop-color="#4f5c69"/><stop offset=".5" stop-color="#c1cbd2"/>
        <stop offset="1" stop-color="#45515e"/>
      </linearGradient>
      <linearGradient id="flame" x1="0" x2="0" y1="0" y2="1">
        <stop stop-color="#fff5a8"/><stop offset=".42" stop-color="#ffac52"/>
        <stop offset="1" stop-color="#ff6384" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="solar" x1="0" x2="1" y1="0" y2="1">
        <stop stop-color="#214b74"/><stop offset=".55" stop-color="#267bb0"/>
        <stop offset="1" stop-color="#243b75"/>
      </linearGradient>
    """
    carbon_texture = (
        f'<path d="M{260-half_width+2} 112H{260+half_width-2}V258'
        f'H{260-half_width+2}Z" fill="url(#weave)"/>'
        if hull == "Carbon-Composite Shell"
        else ""
    )
    return dedent(f"""
    <div style="border:1px solid {theme["border"]}; border-radius:16px;
      padding:12px 16px 8px; margin:4px 0 18px;
      background:linear-gradient(145deg,{theme["panel"]},{theme["schematic_end"]});">
      <div style="font:600 0.9rem sans-serif;color:{theme["muted"]};
        letter-spacing:.12em;text-transform:uppercase;margin:2px 4px 0;">
        Live spacecraft schematic</div>
      <div class="schematic-layout">
      <div class="schematic-art">
      <svg viewBox="0 0 520 410" role="img"
        aria-label="Rocket schematic: {hull_label}; {engine_label}; {tank_label}"
        style="display:block;width:100%;height:auto;max-height:410px;">
        <defs>{texture_defs}
          <pattern id="thermal-insulation" width="8" height="8"
            patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
            <rect width="8" height="8" fill="{theme["accent_secondary"]}" fill-opacity=".08"/>
            <path d="M0 0V8" stroke="{theme["accent_secondary"]}"
              stroke-opacity=".62" stroke-width="2"/>
          </pattern>
          <pattern id="avionics-circuit" width="8" height="8"
            patternUnits="userSpaceOnUse">
            <rect width="8" height="8" fill="#101d2b" fill-opacity=".9"/>
            <path d="M0 2H4V6H8M2 0V2M6 6V8" fill="none"
              stroke="{theme["accent_secondary"]}" stroke-opacity=".72" stroke-width=".8"/>
            <circle cx="4" cy="2" r=".8" fill="{theme["accent_secondary"]}"/>
          </pattern>
          <filter id="soft-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
          <style>
            .small {{font:600 7px sans-serif;fill:#f4f7fb;letter-spacing:.04em}}
            .legend {{font:11px sans-serif;fill:{theme["muted"]}}}
            .glow {{filter:url(#soft-glow)}}
            g[tabindex="0"] {{cursor:default}}
            g[tabindex="0"]:focus {{outline:1px solid {theme["accent"]}}}
          </style>
        </defs>
        <circle cx="260" cy="183" r="136" fill="{theme["accent"]}" opacity=".035"/>
        <path d="M260 28V350" stroke="{theme["accent"]}" stroke-opacity=".18"
          stroke-dasharray="3 7"/>
        <defs>
          <clipPath id="hull-clip"><path d="{hull_path}"/></clipPath>
        </defs>
        {solar_panels}
        <g tabindex="0">{part_tooltip("hull", hull)}
        <path d="{hull_path}" fill="{body_fill}" stroke="{body_stroke}"
          stroke-width="2.5" {body_dash}/>
        {carbon_texture}
        {fuselage_detail}
        </g>
        <g clip-path="url(#hull-clip)">
          {thermal_texture}
          {avionics_texture}
          {instrument_texture}
        </g>
        <path d="M243 100L260 48L277 100Z" fill="#263544"
          stroke="{theme["accent"]}" stroke-width="1.5"/>
        <path d="M252 91L260 63L268 91Z" fill="{theme["accent"]}" opacity=".24"/>
        {instrument_lights}{avionics_lights}
        {tank_markup}{engine_markup}
        <text x="16" y="350" class="legend">HULL · {hull_label}</text>
        <text x="504" y="350" text-anchor="end" class="legend">POWER · {escape(power or "Not selected")}</text>
        <text x="16" y="370" class="legend">ENGINE · {engine_label}</text>
        <text x="504" y="370" text-anchor="end" class="legend">TANK · {tank_label}</text>
        <text x="16" y="390" class="legend">THERMAL · {escape(thermal or "Not selected")}</text>
        <text x="504" y="390" text-anchor="end" class="legend">
          SENSORS · {"Active" if avionics or instruments else "Not selected"}</text>
      </svg>
      </div>
      <aside class="description-panel">
        <h3>Selected systems</h3>
        {description_markup}
        <p class="tooltip-hint">Hover over a drawn part for its description.</p>
      </aside>
      </div>
      <style>
        .schematic-layout {{
          display:grid;
          grid-template-columns:minmax(0, 1fr) minmax(0, 1fr);
          gap:12px;
          align-items:center;
        }}
        .schematic-art svg {{width:100%;height:auto;max-height:390px}}
        .description-panel {{
          max-height:385px;
          overflow-y:auto;
          border-left:1px solid {theme["border"]};
          padding:4px 10px 4px 14px;
          color:{theme["text"]};
          font:12px/1.4 sans-serif;
        }}
        .description-panel h3 {{
          color:{theme["accent"]};
          font-size:12px;
          letter-spacing:.1em;
          margin:0 0 9px;
          text-transform:uppercase;
        }}
        .part-description {{
          border-bottom:1px solid {theme["border"]};
          padding:0 0 7px;
          margin:0 0 7px;
        }}
        .part-description strong {{
          color:{theme["accent_secondary"]};
          display:block;
          font-size:11px;
        }}
        .part-description p,.empty-description,.tooltip-hint {{
          color:{theme["muted"]};
          font-size:11px;
          line-height:1.4;
          margin:3px 0 0;
        }}
        @media (max-width:620px) {{
          .schematic-layout {{grid-template-columns:minmax(0, 1fr)}}
          .description-panel {{
            border-left:0;
            border-top:1px solid {theme["border"]};
            max-height:120px;
            padding:10px 4px 0;
          }}
        }}
      </style>
    </div>
    """).strip()


def _update_destination_from_picker() -> None:
    destination = st.session_state.destination_picker
    st.session_state.mission_destination = destination
    hull_selection = st.session_state.mission_components.get("hull")
    if (
        hull_selection
        and destination
        and hull_selection not in _eligible_hulls(destination)
    ):
        st.session_state.mission_components["hull"] = None
        st.session_state.component_picker_hull = None
    _queue_menu_sound("select")


def _render_menu_sound(volume: int, sound_type: str) -> None:
    st.iframe(
        f"""
        <audio id="mission-menu-sound" autoplay
          src="data:audio/wav;base64,{UI_SOUNDS[sound_type]}"></audio>
        <script>
          const sound = document.getElementById("mission-menu-sound");
          sound.volume = {volume / 100:.2f};
          sound.play().catch(() => {{}});
        </script>
        """,
        height=1,
        alt="Menu interaction sound",
    )


def _apply_theme(theme: dict[str, str]) -> None:
    st.markdown(
        f"""
        <style>
        :root {{
          --mission-accent: {theme["accent"]};
          --mission-accent-secondary: {theme["accent_secondary"]};
          --mission-panel: {theme["panel"]};
          --mission-border: {theme["border"]};
          --mission-text: {theme["text"]};
          --mission-muted: {theme["muted"]};
        }}
        [data-testid="stAppViewContainer"] {{
          background: {theme["background"]};
          color: var(--mission-text);
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] {{
          background: linear-gradient(165deg, var(--mission-panel), {theme["sidebar_end"]});
          border-right: 1px solid var(--mission-border);
          color: var(--mission-text);
        }}
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        label, [data-testid="stCaptionContainer"] {{
          color: var(--mission-text);
        }}
        h1, h2, h3 {{
          color: var(--mission-text);
          letter-spacing: 0.015em;
        }}
        h1 {{
          background: linear-gradient(90deg, var(--mission-accent), var(--mission-accent-secondary));
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }}
        [data-testid="stMetric"] {{
          background: linear-gradient(145deg, var(--mission-panel), {theme["metric_end"]});
          border: 1px solid var(--mission-border);
          border-radius: 14px;
          padding: 14px 16px;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--mission-muted); }}
        [data-testid="stMetricValue"] {{ color: var(--mission-text); }}
        div.stButton > button[kind="primary"] {{
          color: {theme["button_text"]};
          border: 0;
          border-radius: 10px;
          background: linear-gradient(100deg, var(--mission-accent), var(--mission-accent-secondary));
          font-weight: 700;
          box-shadow: 0 4px 18px var(--mission-border);
        }}
        div.stButton > button[kind="secondary"] {{
          color: var(--mission-text);
          border: 1px solid var(--mission-border);
          border-radius: 10px;
          background: linear-gradient(120deg, var(--mission-panel), {theme["control_end"]});
        }}
        [data-testid="stProgressBar"] > div > div {{
          background: linear-gradient(90deg, var(--mission-accent), var(--mission-accent-secondary));
        }}
        [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
          border-color: var(--mission-border);
          background-color: var(--mission-panel);
          color: var(--mission-text);
        }}
        [data-testid="stSelectbox"] [data-baseweb="select"] > div > div,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div > div:last-child {{
          background-color: transparent !important;
          color: var(--mission-text) !important;
        }}
        [data-testid="stSelectbox"] [data-baseweb="select"] svg {{
          color: var(--mission-text) !important;
          fill: var(--mission-text) !important;
        }}
        [data-baseweb="popover"],
        [data-baseweb="popover"] [role="option"] {{
          background-color: {theme["panel"]};
          color: var(--mission-text);
        }}
        [data-testid="stAlert"] {{
          background-color: {theme["alert_background"]} !important;
          border: 1px solid {theme["alert_border"]} !important;
          color: {theme["alert_text"]} !important;
        }}
        [data-testid="stAlert"] [data-baseweb="notification"] {{
          background-color: {theme["alert_background"]} !important;
          color: {theme["alert_text"]} !important;
        }}
        [data-testid="stAlert"] [data-testid="stMarkdownContainer"],
        [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p {{
          color: {theme["alert_text"]} !important;
        }}
        input, textarea {{
          color: var(--mission-text) !important;
          background-color: var(--mission-panel) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _show_mission_status(
    selected_components: dict,
    engine: Optional[str],
    fuel_tank: Optional[str],
) -> None:
    launch_site = st.session_state.get("selected_launch_site")
    destination = st.session_state.get("mission_destination")
    result = evaluate_mission(
        selected_components,
        engine,
        fuel_tank,
        launch_site,
        destination,
    )
    progress = min(max(result.progress_percentage / 100, 0.0), 1.0)

    st.subheader("Mission readiness")
    st.progress(progress, text=f"Upthrust progress: {progress:.0%}")
    st.metric("Total spacecraft mass", f"{result.total_mass_kg:,.0f} kg")
    st.metric("Required upthrust", f"{result.required_upthrust:,.1f}")
    st.metric("Selected engine upthrust", f"{result.selected_upthrust:,.0f}")

    if result.success:
        st.success("Success — selected engine meets the required upthrust.")
    elif result.required_upthrust > 0 and result.selected_upthrust > 0:
        st.warning(
            f"More upthrust required: "
            f"{result.required_upthrust - result.selected_upthrust:,.1f}."
        )
    elif st.session_state.mission_phase == 1:
        st.info("Choose a location, then select spacecraft parts in Phase 2.")
    elif st.session_state.mission_phase == 2:
        st.info("Select spacecraft parts and an engine to calculate readiness.")
    else:
        st.info("Mission thrust is below the required launch threshold.")

    if launch_site and destination:
        st.caption(
            f"Launchpad modifier: "
            f"{LAUNCHPAD_MODIFIERS[launch_site][destination]:g} · "
            f"Destination modifier: {DESTINATION_DIFFICULTY[destination]:g}"
        )


def _planet_appearance(destination: str) -> tuple[str, str, str]:
    """Return visual surface colors and clipped detail for a stylized planet."""
    appearances = {
        "Moon": (
            "#cbd0d4",
            "#737b83",
            """
            <circle cx="665" cy="172" r="8" fill="#929aa0"/>
            <circle cx="694" cy="204" r="12" fill="none" stroke="#9ba2a7" stroke-width="4"/>
            <circle cx="671" cy="215" r="5" fill="#a4abb0"/>
            <circle cx="700" cy="165" r="4" fill="none" stroke="#a4abb0" stroke-width="2"/>
            """,
        ),
        "Mercury": (
            "#aeb3b7",
            "#575e66",
            """
            <circle cx="662" cy="171" r="8" fill="#7e858a"/>
            <circle cx="691" cy="199" r="12" fill="none" stroke="#747b80" stroke-width="4"/>
            <circle cx="672" cy="215" r="5" fill="#7e858a"/>
            <circle cx="700" cy="163" r="4" fill="none" stroke="#777e84" stroke-width="2"/>
            """,
        ),
        "Venus": (
            "#e9c77f",
            "#b87545",
            """
            <path d="M624 173Q652 147 680 171T735 167M620 197Q653 177 685 198T738 192
              M628 218Q656 197 686 218T731 211" fill="none"
              stroke="#fff0bd" stroke-opacity=".48" stroke-width="10"/>
            """,
        ),
        "Mars": (
            "#d8794e",
            "#8b382c",
            """
            <path d="M636 175Q660 161 681 172T719 167M640 205Q667 192 687 205T720 201"
              fill="none" stroke="#efaa73" stroke-opacity=".55" stroke-width="8"/>
            <path d="M659 151Q678 144 695 153L687 162H665Z" fill="#f3d9bd" opacity=".8"/>
            """,
        ),
        "Jupiter": (
            "#e6bd91",
            "#9d5a41",
            """
            <path d="M626 157H730M624 177H732M624 196H732M628 218H728"
              stroke="#f1ddbd" stroke-opacity=".82" stroke-width="8"/>
            <path d="M626 167H730M626 207H730M633 230H722"
              stroke="#a64d37" stroke-opacity=".72" stroke-width="6"/>
            <ellipse cx="695" cy="194" rx="12" ry="7" fill="#c65340"/>
            """,
        ),
        "Saturn": (
            "#ead39a",
            "#ac8053",
            """
            <path d="M634 164H722M631 184H725M632 205H724M639 223H717"
              stroke="#fff0bd" stroke-opacity=".7" stroke-width="7"/>
            <path d="M630 174H727M634 215H720"
              stroke="#bc9565" stroke-opacity=".8" stroke-width="5"/>
            """,
        ),
        "Uranus": (
            "#a5e5e8",
            "#4a9fb1",
            """
            <path d="M633 168Q677 158 723 169M631 192Q678 184 725 193
              M635 216Q679 207 720 217" fill="none"
              stroke="#d7fbf7" stroke-opacity=".45" stroke-width="6"/>
            """,
        ),
        "Neptune": (
            "#5d8fe3",
            "#203b8b",
            """
            <path d="M630 166Q676 154 726 169M629 191Q679 178 728 194
              M635 216Q680 205 721 217" fill="none"
              stroke="#9ccaff" stroke-opacity=".52" stroke-width="7"/>
            <path d="M685 201Q698 192 711 198" fill="none"
              stroke="#263b7a" stroke-width="5"/>
            """,
        ),
    }
    return appearances.get(
        destination,
        ("#88b9ee", "#2775b8", '<path d="M90 0H145" stroke="#82d8c2"/>'),
    )


def _build_starfield_animation(
    destination: str,
    accent: str,
    duration_seconds: float,
) -> str:
    """Create a self-contained Earth-to-planet travel scene."""
    stars = "".join(
        f'<circle cx="{(index * 127 + 43) % 800}" '
        f'cy="{(index * 71 + 29) % 420}" '
        f'r="{0.7 + index % 3 * 0.45:.1f}" '
        f'fill="#eaf4ff" opacity="{0.25 + (index % 5) * 0.13:.2f}">'
        f'<animate attributeName="opacity" values=".25;.9;.25" '
        f'dur="{1.4 + (index % 4) * .35:.2f}s" '
        f'begin="{(index % 8) * -.23:.2f}s" repeatCount="indefinite"/>'
        "</circle>"
        for index in range(72)
    )
    planet_light, planet_dark, planet_detail = _planet_appearance(destination)
    saturn_rings = (
        """
        <ellipse cx="678" cy="190" rx="72" ry="24" fill="none"
          stroke="#d9c18c" stroke-opacity=".82" stroke-width="12"/>
        <ellipse cx="678" cy="190" rx="84" ry="29" fill="none"
          stroke="#9d805b" stroke-opacity=".72" stroke-width="4"/>
        """
        if destination == "Saturn"
        else ""
    )
    saturn_ring_front = (
        """
        <ellipse cx="678" cy="190" rx="72" ry="24" fill="none"
          stroke="#ead6a8" stroke-opacity=".9" stroke-width="9"
          stroke-dasharray="155 75" transform="rotate(-16 678 190)"/>
        """
        if destination == "Saturn"
        else ""
    )
    return dedent(f"""
    <div style="width:100%;overflow:hidden;border:1px solid rgba(126,161,205,.25);
      border-radius:16px;background:#070d18;color:#eaf4ff;
      font:600 13px/1.4 sans-serif;">
      <svg viewBox="0 0 800 420" role="img"
        aria-label="Animated spacecraft journey from Earth to {escape(destination)}"
        style="display:block;width:100%;height:auto;">
        <defs>
          <radialGradient id="space-glow">
            <stop stop-color="{accent}" stop-opacity=".18"/>
            <stop offset="1" stop-color="#070d18" stop-opacity="0"/>
          </radialGradient>
          <linearGradient id="planet-surface" x1="0" x2="1" y1="0" y2="1">
            <stop stop-color="{planet_light}"/><stop offset="1" stop-color="{planet_dark}"/>
          </linearGradient>
          <path id="flight-path" d="M118 228 C265 72 500 350 678 190"/>
          <clipPath id="earth-clip"><circle cx="118" cy="228" r="32"/></clipPath>
          <clipPath id="destination-clip"><circle cx="678" cy="190" r="48"/></clipPath>
          <filter id="rocket-glow" x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="4" result="blur"/>
            <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
          </filter>
        </defs>
        <rect width="800" height="420" fill="#070d18"/>
        <circle cx="405" cy="210" r="290" fill="url(#space-glow)"/>
        {stars}
        <path d="M118 228 C265 72 500 350 678 190" fill="none"
          stroke="{accent}" stroke-opacity=".38" stroke-width="2"
          stroke-dasharray="5 9"/>
        <g>
          <circle cx="118" cy="228" r="32" fill="url(#earth-ocean)"
            stroke="#90d5ff" stroke-width="2"/>
          <defs>
            <linearGradient id="earth-ocean" x1="0" x2="1" y1="0" y2="1">
              <stop stop-color="#4eafe9"/><stop offset=".55" stop-color="#1767a6"/>
              <stop offset="1" stop-color="#0b315f"/>
            </linearGradient>
          </defs>
          <g clip-path="url(#earth-clip)" fill="#55bd83" stroke="#9de0a8"
            stroke-width=".8">
            <path d="M91 210L98 201L106 203L110 211L117 213L116 220L108 223L105 232
              L99 230L96 222L90 220Z"/>
            <path d="M111 233L119 235L124 244L121 254L117 260L112 251L114 243Z"/>
            <path d="M126 204L133 200L140 204L147 202L153 208L148 214L141 213
              L138 220L131 218L127 212Z"/>
            <path d="M132 221L140 221L145 228L142 237L137 243L132 237L128 230Z"/>
            <path d="M151 230L157 228L161 233L158 238L153 237Z"/>
          </g>
          <path d="M90 219Q106 209 120 218T146 215M94 239Q111 228 136 239"
            fill="none" stroke="#d9f5ff" stroke-opacity=".42" stroke-width="2"/>
          <path d="M100 202A32 32 0 0 0 95 247" fill="none"
            stroke="#fff" stroke-opacity=".24" stroke-width="4"/>
          <text x="118" y="284" fill="#cfe5f5" text-anchor="middle" font-size="13">
            EARTH DEPARTURE</text>
        </g>
        <g>
          {saturn_rings}
          <circle cx="678" cy="190" r="48" fill="url(#planet-surface)"
            stroke="{accent}" stroke-width="2"/>
          <g clip-path="url(#destination-clip)">{planet_detail}</g>
          {saturn_ring_front}
          <ellipse cx="678" cy="190" rx="68" ry="15" fill="none"
            stroke="{accent}" stroke-opacity=".25" stroke-width="1.5"/>
          <text x="678" y="263" fill="#eaf4ff" text-anchor="middle" font-size="14">
            {escape(destination.upper())}</text>
        </g>
        <g filter="url(#rocket-glow)">
          <g transform="translate(-12,-12)">
            <path d="M12 0C6 7 3 16 3 23L12 19L21 23C21 16 18 7 12 0Z"
              fill="#f3f7fc" stroke="{accent}" stroke-width="1.5"/>
            <path d="M8 21L5 29L12 26L19 29L16 21Z" fill="#ffb05a"/>
            <circle cx="12" cy="11" r="3" fill="{accent}"/>
          </g>
          <animateMotion dur="{duration_seconds:.2f}s" calcMode="spline"
            keyTimes="0;1" keySplines=".35 0 .65 1" fill="freeze">
            <mpath href="#flight-path"/>
          </animateMotion>
        </g>
        <text x="400" y="390" fill="#a9bbcf" text-anchor="middle" font-size="13">
          INTERPLANETARY TRANSIT · SIMULATION</text>
      </svg>
    </div>
    """).strip()


def _flight_duration_seconds(destination: str) -> float:
    """Scale arcade transit time with radial distance from Earth's orbit."""
    distance_au = abs(ORBITAL_RADIUS_AU[destination] - ORBITAL_RADIUS_AU["Earth"])
    return max(4.0, 3.2 + distance_au * 1.1)


def _initiate_launch_sequence() -> None:
    components_selected = st.session_state.mission_components
    engine = st.session_state.mission_engine
    fuel_tank = st.session_state.mission_fuel_tank
    destination = st.session_state.mission_destination
    launch_site = st.session_state.selected_launch_site
    complete_build = (
        all(components_selected.get(category) for category in COMPONENT_CHOICES)
        and engine is not None
        and fuel_tank is not None
    )
    result = evaluate_mission(
        components_selected,
        engine,
        fuel_tank,
        launch_site,
        destination,
    )
    if not complete_build or not result.success:
        return

    st.session_state.mission_phase = 3
    st.session_state.flight_status = "slingshot"
    st.session_state.slingshot_attempt_number = 1
    st.session_state.slingshot_bodies_orbited = 0
    st.session_state.slingshot_attempt_id = (
        st.session_state.get("slingshot_attempt_id", 0) + 1
    )
    st.session_state.slingshot_processed_attempt_id = None
    st.session_state.slingshot_outcome = None
    st.session_state.pop("menu_sound_pending", None)


def _process_slingshot_event(event: Any) -> bool:
    """Apply one client slingshot event to authoritative mission state."""
    if not isinstance(event, dict):
        return False
    if event.get("attempt_id") != st.session_state.slingshot_attempt_id:
        return False
    if event.get("kind") == "retry":
        if st.session_state.slingshot_attempt_number >= SLINGSHOT_MAX_ATTEMPTS:
            return False
        st.session_state.slingshot_attempt_number += 1
        st.session_state.slingshot_attempt_id += 1
        st.session_state.slingshot_processed_attempt_id = None
        st.session_state.slingshot_outcome = None
        _queue_menu_action_sound()
        return True
    if (
        event.get("kind") != "launch"
        or st.session_state.slingshot_processed_attempt_id
        == st.session_state.slingshot_attempt_id
    ):
        return False

    try:
        trajectory = simulate_trajectory(
            st.session_state.mission_destination,
            float(event["velocity_x"]),
            float(event["velocity_y"]),
        )
    except (KeyError, TypeError, ValueError) as error:
        st.session_state.slingshot_outcome = {
            "status": "failure",
            "reason": f"Invalid launch input: {error}",
        }
    else:
        st.session_state.slingshot_outcome = {
            "status": trajectory["status"],
            "reason": trajectory["reason"],
            "impact_speed": trajectory["impact_speed"],
            "bodies_orbited": trajectory["bodies_orbited"],
        }
        st.session_state.slingshot_bodies_orbited = trajectory["bodies_orbited"]
    st.session_state.slingshot_processed_attempt_id = (
        st.session_state.slingshot_attempt_id
    )
    return True


def _continue_to_flight() -> None:
    outcome = st.session_state.get("slingshot_outcome")
    if not outcome or outcome.get("status") != "success":
        return
    fuel_capacity = float(
        FUEL_TANK_CHOICES[st.session_state.mission_fuel_tank]["mass_kg"]
    )
    bodies_orbited = st.session_state.get("slingshot_bodies_orbited", 0)
    remaining_fuel = fuel_capacity * max(
        0.0,
        1.0 - SLINGSHOT_FUEL_COST_PER_BODY * bodies_orbited,
    )
    st.session_state.mission_phase = 4
    st.session_state.flight_status = "in_flight"
    st.session_state.flight_fuel_capacity_kg = fuel_capacity
    st.session_state.flight_fuel_remaining_kg = remaining_fuel
    st.session_state.flight_fuel_start_kg = remaining_fuel
    st.session_state.landing_altitude_m = LANDING_START_ALTITUDE_M
    st.session_state.landing_velocity_m_s = LANDING_START_VELOCITY_M_S
    st.session_state.landing_score = None
    st.session_state.flight_result = None
    st.session_state.landing_attempt_number = 0
    st.session_state.landing_last_event_id = 0
    st.session_state.landing_action_id += 1
    st.session_state.landing_last_action = None
    st.session_state.pop("menu_sound_pending", None)


def _begin_landing() -> None:
    if st.session_state.flight_status == "arrival":
        st.session_state.mission_phase = 5
        st.session_state.flight_status = "landing"
        st.session_state.landing_attempt_number = 1
        st.session_state.landing_start_fuel_kg = (
            st.session_state.flight_fuel_remaining_kg
        )
        st.session_state.landing_last_event_id = 0
        st.session_state.landing_action_id += 1
        st.session_state.landing_last_action = None
        _queue_phase_sound()


def _return_to_assembly() -> None:
    st.session_state.mission_phase = 2
    st.session_state.flight_status = "assembly"
    st.session_state.slingshot_outcome = None
    st.session_state.flight_result = None
    st.session_state.landing_score = None
    _queue_menu_action_sound()


def _return_to_rocket_design() -> None:
    _return_to_assembly()
    st.session_state.mission_components = {}
    st.session_state.mission_engine = None
    st.session_state.mission_fuel_tank = None
    for category in COMPONENT_CHOICES:
        st.session_state[f"component_picker_{category}"] = None
    st.session_state.engine_picker = None
    st.session_state.fuel_tank_picker = None


def _show_failure_scorecard(
    phase: str,
    reason: str,
    attempts: int,
    telemetry: tuple[tuple[str, str], ...],
) -> None:
    with st.container(border=True):
        st.markdown("## Mission Failure")
        st.caption(f"Failure phase: {phase} · Attempts used: {attempts}/{2}")
        st.error(reason)
        if telemetry:
            columns = st.columns(len(telemetry))
            for column, (label, value) in zip(columns, telemetry):
                column.metric(label, value)
        st.button(
            "Return to Rocket Design",
            key="return_to_design_after_failure",
            type="primary",
            on_click=_return_to_rocket_design,
        )


def _show_victory_scorecard() -> None:
    with st.container(border=True):
        st.markdown("# 🏆 Mission Complete")
        try:
            score = calculate_mission_score(
                st.session_state.mission_components,
                st.session_state.selected_launch_site,
                st.session_state.get("slingshot_bodies_orbited", 0),
                st.session_state.flight_fuel_remaining_kg,
                st.session_state.flight_fuel_capacity_kg,
            )
        except (KeyError, TypeError, ValueError) as error:
            st.error(f"Mission succeeded, but its score could not be calculated: {error}")
        else:
            st.metric("Total Mission Score", f"{score['total_score']:,.1f}")
            breakdown = st.columns(4)
            breakdown[0].metric(
                "Research value",
                f"{score['research_points']:g} pts",
            )
            breakdown[1].metric(
                "Launch-site risk",
                f"{score['launch_difficulty_multiplier']:.1f}×",
            )
            breakdown[2].metric(
                "Slingshot body bonus",
                f"{score['slingshot_body_bonus']:.1f}×",
                f"{int(score['bodies_orbited'])} gravity assists",
            )
            breakdown[3].metric(
                "Fuel efficiency bonus",
                f"+{score['fuel_efficiency_bonus']:.1f} pts",
                f"{score['fuel_remaining_percentage']:.1f}% remaining",
            )
            st.caption(
                "Score = research × launch-site risk × gravity-assist bonus "
                "+ fuel remaining percentage."
            )

        st.markdown("### Touchdown telemetry")
        telemetry = st.columns(3)
        telemetry[0].metric("Final altitude", "0 m")
        telemetry[1].metric(
            "Touchdown speed",
            f"{st.session_state.landing_velocity_m_s:.1f} m/s",
        )
        telemetry[2].metric(
            "Remaining fuel",
            f"{st.session_state.flight_fuel_remaining_kg:,.0f} kg",
        )
        st.button(
            "Restart Mission / Design New Rocket",
            key="restart_mission_after_victory",
            type="primary",
            on_click=_return_to_rocket_design,
            use_container_width=True,
        )


def _apply_landing_action(action: str, duration_s: float) -> None:
    if st.session_state.flight_status != "landing":
        return
    if action not in ("burn", "coast"):
        raise ValueError(f"Unknown landing action: {action!r}.")

    altitude = st.session_state.landing_altitude_m
    velocity = st.session_state.landing_velocity_m_s
    fuel_remaining = st.session_state.flight_fuel_remaining_kg
    fuel_capacity = st.session_state.flight_fuel_capacity_kg
    gravity = _landing_gravity(st.session_state.mission_destination)
    retro_acceleration = _landing_retro_acceleration(gravity)
    if fuel_remaining <= 0 and altitude > LANDING_CONTACT_ALTITUDE_M:
        st.session_state.flight_status = "crashed"
        st.session_state.flight_result = "Fuel depleted before touchdown."
        return

    def advance_segment(segment_duration: float, acceleration: float) -> bool:
        nonlocal altitude, velocity
        if segment_duration <= 0:
            return False
        if altitude <= LANDING_CONTACT_ALTITUDE_M:
            altitude = 0.0
            return True
        stop_time = (
            velocity / -acceleration
            if acceleration < 0 and velocity + acceleration * segment_duration < 0
            else segment_duration
        )
        traveled = max(
            0.0,
            velocity * stop_time + 0.5 * acceleration * stop_time**2,
        )
        distance_to_contact = altitude - LANDING_CONTACT_ALTITUDE_M
        if traveled >= distance_to_contact:
            impact_velocity = math.sqrt(
                max(0.0, velocity**2 + 2 * acceleration * distance_to_contact)
            )
            altitude = 0.0
            velocity = impact_velocity
            return True
        altitude -= traveled
        velocity = max(0.0, velocity + acceleration * segment_duration)
        return False

    touched_down = False
    if action == "burn" and fuel_remaining > 0:
        fuel_rate = fuel_capacity * 0.03 / LANDING_ACTION_DURATION_S
        burn_duration = min(duration_s, fuel_remaining / fuel_rate)
        fuel_remaining = max(0.0, fuel_remaining - fuel_rate * burn_duration)
        touched_down = advance_segment(
            burn_duration,
            _landing_descent_acceleration(velocity, gravity)
            - retro_acceleration,
        )
        if not touched_down and burn_duration < duration_s:
            altitude = max(0.0, altitude)
            st.session_state.flight_status = "crashed"
            st.session_state.flight_result = "Fuel depleted before touchdown."
    else:
        touched_down = advance_segment(
            duration_s,
            _landing_descent_acceleration(velocity, gravity),
        )

    st.session_state.landing_altitude_m = altitude
    st.session_state.landing_velocity_m_s = velocity
    st.session_state.flight_fuel_remaining_kg = fuel_remaining
    if st.session_state.flight_status != "landing":
        return
    if fuel_remaining <= 0 and altitude > LANDING_CONTACT_ALTITUDE_M:
        st.session_state.flight_status = "crashed"
        st.session_state.flight_result = "Fuel depleted before touchdown."
        return
    if touched_down:
        if velocity <= LANDING_SAFE_TOUCHDOWN_SPEED_M_S:
            st.session_state.flight_status = "landed"
            st.session_state.landing_score = (
                round(fuel_remaining / fuel_capacity * 100)
                if fuel_capacity > 0
                else 0
            )
            st.session_state.flight_result = "Successful Mission & Landing!"
        else:
            st.session_state.flight_status = "crashed"
            st.session_state.flight_result = (
                f"Impact velocity {velocity:.1f} m/s exceeded the "
                f"{LANDING_SAFE_TOUCHDOWN_SPEED_M_S:g} m/s limit."
            )


def _process_landing_event(event: Any) -> bool:
    """Apply a sequenced landing snapshot or a bounded legacy physics step."""
    if not isinstance(event, dict):
        return False
    if event.get("kind") == "snapshot":
        event_id = event.get("event_id")
        altitude = event.get("altitude_m")
        velocity = event.get("velocity_m_s")
        fuel_remaining = event.get("fuel_remaining_kg")
        used_thrust = event.get("used_thrust")
        numeric_values = (altitude, velocity, fuel_remaining)
        if (
            not isinstance(event_id, int)
            or isinstance(event_id, bool)
            or event_id < 1
            or any(
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
                for value in numeric_values
            )
            or not 0 <= altitude <= LANDING_START_ALTITUDE_M
            or not 0 <= velocity <= 1000
            or not 0 <= fuel_remaining
            <= st.session_state.flight_fuel_capacity_kg
            or not isinstance(used_thrust, bool)
        ):
            st.session_state.flight_status = "crashed"
            st.session_state.flight_result = (
                "Invalid landing-control data. Restart the landing attempt."
            )
            return True
        if event_id <= st.session_state.landing_last_event_id:
            return False

        st.session_state.landing_last_event_id = event_id
        if st.session_state.flight_status != "landing":
            return False

        action = "burn" if used_thrust else "coast"
        st.session_state.landing_last_action = action
        st.session_state.landing_action_id += 1
        st.session_state.landing_altitude_m = float(altitude)
        st.session_state.landing_velocity_m_s = float(velocity)
        st.session_state.flight_fuel_remaining_kg = float(fuel_remaining)

        if altitude <= LANDING_CONTACT_ALTITUDE_M:
            st.session_state.landing_altitude_m = 0.0
            if velocity <= LANDING_SAFE_TOUCHDOWN_SPEED_M_S:
                st.session_state.flight_status = "landed"
                fuel_capacity = st.session_state.flight_fuel_capacity_kg
                st.session_state.landing_score = (
                    round(fuel_remaining / fuel_capacity * 100)
                    if fuel_capacity > 0
                    else 0
                )
                st.session_state.flight_result = "Successful Mission & Landing!"
            else:
                st.session_state.flight_status = "crashed"
                st.session_state.flight_result = (
                    f"Impact velocity {velocity:.1f} m/s exceeded the "
                    f"{LANDING_SAFE_TOUCHDOWN_SPEED_M_S:g} m/s limit."
                )
        elif fuel_remaining <= 0:
            st.session_state.flight_status = "crashed"
            st.session_state.flight_result = "Fuel depleted before touchdown."
        return True

    if event.get("kind") != "step":
        return False
    event_id = event.get("event_id")
    duration_s = event.get("duration_s")
    thrusting = event.get("thrusting")
    if (
        not isinstance(event_id, int)
        or isinstance(event_id, bool)
        or event_id < 1
        or not isinstance(duration_s, (int, float))
        or isinstance(duration_s, bool)
        or not math.isfinite(duration_s)
        or not 0 < duration_s <= LANDING_MAX_STEP_DURATION_S
        or not isinstance(thrusting, bool)
    ):
        st.session_state.flight_status = "crashed"
        st.session_state.flight_result = (
            "Invalid landing-control data. Restart the landing attempt."
        )
        return True
    if event_id <= st.session_state.landing_last_event_id:
        return False

    st.session_state.landing_last_event_id = event_id
    if st.session_state.flight_status != "landing":
        return False

    action = "burn" if thrusting else "coast"
    if action != st.session_state.landing_last_action:
        _queue_menu_sound("thrust" if action == "burn" else "coast")
    st.session_state.landing_last_action = action
    st.session_state.landing_action_id += 1
    _apply_landing_action(action, float(duration_s))
    return True


def _restart_landing() -> None:
    if (
        st.session_state.flight_status != "crashed"
        or st.session_state.landing_attempt_number >= LANDING_MAX_ATTEMPTS
    ):
        return
    st.session_state.mission_phase = 5
    st.session_state.flight_status = "landing"
    st.session_state.landing_attempt_number += 1
    st.session_state.flight_fuel_remaining_kg = (
        st.session_state.get(
            "landing_start_fuel_kg",
            st.session_state.flight_fuel_capacity_kg,
        )
    )
    st.session_state.landing_altitude_m = LANDING_START_ALTITUDE_M
    st.session_state.landing_velocity_m_s = LANDING_START_VELOCITY_M_S
    st.session_state.landing_score = None
    st.session_state.flight_result = None
    st.session_state.landing_action_id += 1
    st.session_state.landing_last_action = None
    _queue_menu_action_sound()


def _run_trajectory_animation(destination: str, theme: dict[str, str]) -> None:
    """Animate the route while updating telemetry and arrival progress."""
    st.markdown("#### Interplanetary trajectory")
    st.caption(
        f"Simulated route: Earth departure → {destination}. "
        "The starfield journey is a visual simulation, not to scale."
    )
    scene = st.empty()
    telemetry = st.empty()
    distance_au = abs(ORBITAL_RADIUS_AU[destination] - 1.0)
    duration_seconds = _flight_duration_seconds(destination)
    fuel_capacity = st.session_state.flight_fuel_capacity_kg
    fuel_start = st.session_state.flight_fuel_start_kg
    frame_count = max(10, math.ceil(duration_seconds / 0.4))
    frame_delay = duration_seconds / frame_count
    if st.session_state.interface_volume > 0:
        _render_menu_sound(st.session_state.interface_volume, "flight")
    with scene.container():
        components.html(
            _build_starfield_animation(
                destination,
                theme["accent"],
                duration_seconds,
            ),
            height=440,
            scrolling=False,
        )
    for frame in range(frame_count + 1):
        progress = frame / frame_count
        fuel_remaining = fuel_start * (1.0 - 0.05 * progress)
        with telemetry.container():
            distance_col, eta_col, fuel_col = st.columns(3)
            distance_col.metric(
                "Distance covered",
                f"{distance_au * progress:.3f} AU",
            )
            eta_seconds = round((1.0 - progress) * duration_seconds)
            eta_col.metric(
                "Estimated time to arrival",
                f"{eta_seconds // 60:02d}:{eta_seconds % 60:02d}",
            )
            fuel_col.metric(
                "Fuel level",
                f"{fuel_remaining:,.0f} kg",
                f"{fuel_remaining / fuel_capacity:.0%}",
            )
            st.progress(progress, text=f"Trajectory progress: {progress:.0%}")
        if frame < frame_count:
            time.sleep(frame_delay)

    st.session_state.flight_fuel_remaining_kg = fuel_start * 0.95
    st.session_state.flight_distance_au = distance_au
    st.session_state.flight_status = "arrival"


def _show_landing_controls() -> None:
    if (
        st.session_state.landing_attempt_number == 0
        and st.session_state.flight_status in ("landing", "landed", "crashed")
    ):
        st.session_state.landing_attempt_number = 1
    _process_landing_event(st.session_state.get("landing_canvas"))
    destination = st.session_state.mission_destination
    st.subheader(f"Landing Minigame — {destination}")
    canvas_slot = st.empty()
    status = st.session_state.flight_status
    if status == "landed":
        _show_victory_scorecard()
    elif status == "crashed":
        attempts = st.session_state.landing_attempt_number
        if attempts < LANDING_MAX_ATTEMPTS:
            st.error(f"Landing attempt failed — {st.session_state.flight_result}")
            st.caption("One retry remains. The retry starts with arrival fuel restored.")
            st.button(
                "Retry Landing",
                key="restart_landing",
                on_click=_restart_landing,
                type="primary",
            )
        else:
            _show_failure_scorecard(
                "Phase 5 — Landing Control",
                st.session_state.flight_result or "Landing attempt failed.",
                attempts,
                (
                    ("Final altitude", f"{st.session_state.landing_altitude_m:.1f} m"),
                    (
                        "Impact speed",
                        f"{st.session_state.landing_velocity_m_s:.1f} m/s",
                    ),
                    (
                        "Fuel remaining",
                        f"{st.session_state.flight_fuel_remaining_kg:,.0f} kg",
                    ),
                ),
            )

    with canvas_slot:
        landing_canvas(
            destination=destination,
            altitude_m=st.session_state.landing_altitude_m,
            velocity_m_s=st.session_state.landing_velocity_m_s,
            fuel_capacity_kg=st.session_state.flight_fuel_capacity_kg,
            fuel_remaining_kg=st.session_state.flight_fuel_remaining_kg,
            retro_acceleration_m_s2=_landing_retro_acceleration(
                _landing_gravity(destination)
            ),
            gravity_m_s2=_landing_gravity(destination),
            status=st.session_state.flight_status,
            result=st.session_state.get("flight_result"),
            score=st.session_state.get("landing_score"),
            last_action=st.session_state.landing_last_action,
            action_id=st.session_state.landing_action_id,
            last_event_id=st.session_state.landing_last_event_id,
            height=500,
            accent=THEMES[st.session_state.visual_theme]["accent"],
            surface_gravity_m_s2=PLANET_GRAVITY_M_S2[destination],
            contact_altitude_m=LANDING_CONTACT_ALTITUDE_M,
            key="landing_canvas",
            default=None,
        )


def _show_arrival_screen() -> None:
    destination = st.session_state.mission_destination
    st.success(f"Arrival at {destination}")
    st.write(
        f"The spacecraft has completed interplanetary transit and is ready "
        f"to begin its descent toward {destination}."
    )
    st.button(
        f"Begin Descent to {destination}",
        key="begin_landing",
        type="primary",
        on_click=_begin_landing,
        use_container_width=True,
    )


st.set_page_config(page_title="Mission Design", page_icon="🚀", layout="wide")

for key, default in (
    ("mission_phase", 1),
    ("selected_launch_site", None),
    ("mission_destination", None),
    ("mission_components", {}),
    ("mission_engine", None),
    ("mission_fuel_tank", None),
    ("visual_theme", "Aurora"),
    ("interface_volume", DEFAULT_VOLUME),
    ("slingshot_attempt_id", 0),
    ("slingshot_attempt_number", 0),
    ("slingshot_processed_attempt_id", None),
    ("slingshot_outcome", None),
    ("slingshot_bodies_orbited", 0),
    ("landing_action_id", 0),
    ("landing_last_action", None),
    ("landing_last_event_id", 0),
    ("landing_attempt_number", 0),
):
    if key not in st.session_state:
        st.session_state[key] = default

st.sidebar.selectbox(
    "Color scheme",
    tuple(THEMES),
    key="visual_theme",
    on_change=_queue_menu_action_sound,
)
st.sidebar.slider(
    "Interface volume",
    min_value=0,
    max_value=100,
    key="interface_volume",
    help="Set menu sound effects volume to 0 to mute them.",
    on_change=_queue_menu_action_sound,
)

st.sidebar.markdown("### Quick Test Presets")
st.sidebar.button(
    "Load Beginner Moon Run",
    key="beginner_preset",
    on_click=_load_beginner_preset,
    use_container_width=True,
)
st.sidebar.button(
    "Load Hardcore Jupiter Run",
    key="hardcore_preset",
    on_click=_load_hardcore_preset,
    use_container_width=True,
)
st.sidebar.button(
    "Reset Mission",
    key="reset_mission",
    on_click=_reset_mission,
    use_container_width=True,
)
with st.sidebar.expander("About NASA Space Apps"):
    st.write(
        "Space Apps is NASA's annual hackathon, where teams use creativity, "
        "science, and technology to address challenges inspired by space and "
        "Earth. This project explores how mission destination and launch-site "
        "choices affect a spacecraft design."
    )
    st.caption(
        "Required upthrust = spacecraft mass × launch-site modifier × "
        "destination difficulty. This is an arcade-style game calculation, "
        "not a physical rocket simulation."
    )

theme = THEMES[st.session_state.visual_theme]
_apply_theme(theme)

st.title("Space Mission Design")
st.caption(
    "Choose a destination, build a spacecraft, then fly and land. The right-hand panel updates the "
    "spacecraft mass and upthrust progress as you make selections."
)

configuration, status = st.columns([2, 1], gap="large")
selected_components = dict(st.session_state.mission_components)
engine = st.session_state.mission_engine
fuel_tank = st.session_state.mission_fuel_tank

with configuration:
    if st.session_state.mission_phase == 1:
        st.subheader("Phase 1 — Choose mission location")
        st.markdown("#### Launch site map")
        st.caption(
            "Select a launch site directly on the map or use the selector below."
        )

        map_event = st.plotly_chart(
            _build_launch_map(st.session_state.selected_launch_site, theme),
            key="launch_site_map",
            on_select="rerun",
            selection_mode="points",
            width="stretch",
            config={"displayModeBar": False, "scrollZoom": False},
        )
        map_site = _map_selected_site(map_event)
        map_signature = map_site or ""
        if "last_map_selection" not in st.session_state:
            st.session_state.last_map_selection = ""
        ignore_map_selection = st.session_state.pop("ignore_map_selection", False)
        if (
            map_site
            and map_signature != st.session_state.last_map_selection
            and not ignore_map_selection
        ):
            st.session_state.selected_launch_site = map_site
            st.session_state.launch_site_picker = map_site
            _queue_menu_sound("select")
        st.session_state.last_map_selection = map_signature

        site_options = [None, *LAUNCH_SITES]
        if "launch_site_picker" not in st.session_state:
            st.session_state.launch_site_picker = (
                st.session_state.selected_launch_site
            )
        selected_site = st.selectbox(
            "Launch site",
            site_options,
            key="launch_site_picker",
            on_change=_update_launch_site_from_picker,
            format_func=lambda value: value or "Choose a launch site",
        )
        st.session_state.selected_launch_site = selected_site

        destination_options = [None, *DESTINATION_DIFFICULTY]
        if "destination_picker" not in st.session_state:
            st.session_state.destination_picker = st.session_state.mission_destination
        st.selectbox(
            "Target planet",
            destination_options,
            key="destination_picker",
            on_change=_update_destination_from_picker,
            format_func=lambda value: value or "Choose a destination",
        )
        st.session_state.mission_destination = st.session_state.destination_picker

        location_confirmed = (
            st.session_state.selected_launch_site is not None
            and st.session_state.mission_destination is not None
        )
        if st.button(
            "Confirm location and continue to Phase 2",
            key="confirm_location",
            on_click=_queue_phase_sound,
            disabled=not location_confirmed,
            type="primary",
        ):
            st.session_state.mission_phase = 2
            st.rerun()
    elif st.session_state.mission_phase == 2:
        st.subheader("Phase 2 — Build your spacecraft")
        st.write(
            f"**Mission:** {st.session_state.selected_launch_site} → "
            f"{st.session_state.mission_destination}"
        )
        if st.button(
            "← Edit launch site or destination",
            key="edit_location",
            on_click=_queue_phase_sound,
        ):
            st.session_state.mission_phase = 1
            st.rerun()

        schematic_preview = st.empty()
        st.markdown("#### Spacecraft components")
        st.caption("Nothing is selected by default; unselected parts weigh 0 kg.")
        for category, choices in COMPONENT_CHOICES.items():
            widget_key = f"component_picker_{category}"
            if category == "hull":
                st.caption(
                    f"{st.session_state.mission_destination} requires at least "
                    f"{HULL_MINIMUM_BY_DESTINATION[st.session_state.mission_destination]}."
                )
            available_choices = (
                {
                    name: choices[name]
                    for name in _eligible_hulls(st.session_state.mission_destination)
                }
                if category == "hull" and st.session_state.mission_destination
                else choices
            )
            current_selection = st.session_state.mission_components.get(category)
            if current_selection and current_selection not in available_choices:
                st.session_state.mission_components[category] = None
                current_selection = None
            if widget_key not in st.session_state:
                st.session_state[widget_key] = current_selection
            elif st.session_state[widget_key] not in (None, *available_choices):
                st.session_state[widget_key] = None
            selected_components[category] = st.selectbox(
                category.replace("_", " ").title(),
                [None, *available_choices],
                key=widget_key,
                on_change=_queue_menu_sound,
                format_func=lambda value, choices=choices: (
                    "Choose a component"
                    if value is None
                    else f"{value} — {choices[value]['mass_kg']:,} kg"
                ),
            )
            st.session_state.mission_components[category] = selected_components[
                category
            ]

        if "engine_picker" not in st.session_state:
            st.session_state.engine_picker = st.session_state.mission_engine
        engine = st.selectbox(
            "Engine",
            [None, *ENGINE_CHOICES],
            key="engine_picker",
            on_change=_queue_menu_sound,
            format_func=lambda value: (
                "Choose an engine"
                if value is None
                else f"{value} — {ENGINE_CHOICES[value]['mass_kg']:,} kg, "
                f"{ENGINE_CHOICES[value]['upthrust']:,} upthrust"
            ),
        )
        st.session_state.mission_engine = engine
        if "fuel_tank_picker" not in st.session_state:
            st.session_state.fuel_tank_picker = st.session_state.mission_fuel_tank
        fuel_tank = st.selectbox(
            "Fuel tank",
            [None, *FUEL_TANK_CHOICES],
            key="fuel_tank_picker",
            on_change=_queue_menu_sound,
            format_func=lambda value: (
                "Choose a fuel tank"
                if value is None
                else f"{value} — {FUEL_TANK_CHOICES[value]['mass_kg']:,} kg"
            ),
        )
        st.session_state.mission_fuel_tank = fuel_tank
        with schematic_preview:
            svg_string = _rocket_schematic(
                selected_components,
                engine,
                fuel_tank,
                theme,
            )
            components.html(svg_string, height=450, scrolling=False)
        launch_ready = (
            all(selected_components.get(category) for category in COMPONENT_CHOICES)
            and engine is not None
            and fuel_tank is not None
            and evaluate_mission(
                selected_components,
                engine,
                fuel_tank,
                st.session_state.selected_launch_site,
                st.session_state.mission_destination,
            ).success
        )
        st.markdown("#### Phase 3 — Gravity slingshot")
        st.button(
            "🚀 Begin Gravity Slingshot",
            key="initiate_launch_sequence",
            type="primary",
            disabled=not launch_ready,
            on_click=_initiate_launch_sequence,
            use_container_width=True,
        )
        if not launch_ready:
            st.caption(
                "Select every spacecraft system and an engine that meets the "
                "required upthrust to unlock launch."
            )
    elif st.session_state.mission_phase == 3:
        route_bodies = trajectory_bodies(st.session_state.mission_destination)
        st.write(
            f"**Mission:** {st.session_state.selected_launch_site} → "
            f"{st.session_state.mission_destination}"
        )
        st.subheader("Phase 3 — Gravitational Trajectory Slingshot")
        st.caption(
            "Drag backward from the rocket to aim, then release to launch. "
            "The dotted preview uses a simplified arcade gravity model, not "
            "a physically accurate orbital calculation."
        )
        st.caption(
            "Flyby route: "
            + " → ".join(body["name"] for body in route_bodies)
        )
        slingshot_event = gravity_slingshot(
            destination=st.session_state.mission_destination,
            bodies=route_bodies,
            accent=theme["accent"],
            attempt_id=st.session_state.slingshot_attempt_id,
            attempts_remaining=max(
                0,
                SLINGSHOT_MAX_ATTEMPTS - st.session_state.slingshot_attempt_number,
            ),
            retry_allowed=(
                st.session_state.slingshot_attempt_number < SLINGSHOT_MAX_ATTEMPTS
            ),
            outcome=st.session_state.slingshot_outcome,
            key="gravity_slingshot",
            default=None,
        )
        if _process_slingshot_event(slingshot_event):
            st.rerun()

        slingshot_outcome = st.session_state.slingshot_outcome
        if slingshot_outcome and slingshot_outcome["status"] == "success":
            st.success(slingshot_outcome["reason"])
            st.button(
                "Continue to Phase 4 — Interplanetary Flight",
                key="continue_to_phase_four",
                type="primary",
                on_click=_continue_to_flight,
                use_container_width=True,
            )
        elif slingshot_outcome:
            if st.session_state.slingshot_attempt_number < SLINGSHOT_MAX_ATTEMPTS:
                st.warning(slingshot_outcome["reason"])
                st.caption("One retry remains. Adjust your launch angle and try again.")
            else:
                impact_speed = slingshot_outcome.get("impact_speed")
                telemetry = (
                    (
                        "Trajectory result",
                        f"{slingshot_outcome.get('bodies_orbited', 0)} gravity assists",
                    ),
                    (
                        "Terminal speed",
                        f"{impact_speed:.1f} units/s"
                        if isinstance(impact_speed, (int, float))
                        else "Not available",
                    ),
                    ("Attempts used", "2 / 2"),
                )
                _show_failure_scorecard(
                    "Phase 3 — Gravitational Trajectory Slingshot",
                    slingshot_outcome["reason"],
                    st.session_state.slingshot_attempt_number,
                    telemetry,
                )
        st.button(
            "← Back to Mission Assembly",
            key="back_to_assembly",
            on_click=_return_to_assembly,
        )
    else:
        st.write(
            f"**Mission:** {st.session_state.selected_launch_site} → "
            f"{st.session_state.mission_destination}"
        )
        st.button(
            "← Back to Mission Assembly",
            key="back_to_assembly",
            on_click=_return_to_assembly,
        )
        if st.session_state.flight_status == "in_flight":
            _scroll_page_to_top()
            st.subheader("Phase 4 — Interplanetary Flight")
            _run_trajectory_animation(
                st.session_state.mission_destination,
                theme,
            )
        if st.session_state.flight_status == "arrival":
            st.subheader("Phase 4 — Interplanetary Flight")
            _show_arrival_screen()
        elif st.session_state.flight_status in ("landing", "landed", "crashed"):
            st.subheader("Phase 5 — Landing Control")
            _show_landing_controls()

with status:
    _show_mission_status(selected_components, engine, fuel_tank)

pending_sound = st.session_state.pop("menu_sound_pending", None)
if pending_sound:
    volume = st.session_state.interface_volume
    if volume > 0:
        _render_menu_sound(volume, pending_sound)
