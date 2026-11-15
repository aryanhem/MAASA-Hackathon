# MAASA-Hackathon
**Team MAASA's entry for the 2026 NASA International Space Apps Challenge.**

We built an interactive, five-phase spacecraft design and mission simulator in Python and Streamlit. Players have to choose a launch site, engineer a rocket that meets destination-specific requirements, slingshot it across the solar system, and land it safely without running out of fuel.

### To Start Our Game:

> [!IMPORTANT]
> 1. Clone this repository or download this project folder to your computer and install the dependencies (`streamlit`, `plotly`, etc.).
> 2. Launch the app by running `streamlit run app.py` in your terminal.


## How the Mission Works

We structured the game into five distinct phases, keeping a live mission readiness panel and upthrust progress bar visible on the right side of the screen throughout the entire run.

Phase 1: Launch & Destination Selection

* Players pick their launch site using an interactive Plotly world map (synced with a dropdown selector) and choose their target planet or moon.

Phase 2: Spacecraft Assembly

* Players select their hull, solar equipment, thermal protection, avionics, instruments, engine, and fuel tank. We built a live inline-SVG schematic that updates dynamically as parts are added (changing fuselage textures, adding solar arrays, or showing circuit-board details complete with hover tooltips). Once the build meets the required upthrust, Phase 3 unlocks.

Phase 3: Gravitational Slingshot

* An interactive drag-to-aim launch mechanic. You pull back from the rocket to preview a dotted, gravity-curved trajectory and release to launch. Depending on your destination, you'll have to dodge satellites and debris (for the Moon) or dodge past intervening planets in order (for example, a Neptune run passes Mars, Jupiter, Saturn, and Uranus).

Phase 4: Interplanetary Transit

* An animated starfield journey from Earth to your target world. Transit time scales with orbital distance while live distance, ETA, and fuel telemetry update in flight.

Phase 5: Planetary Landing

* An HTML5 Canvas landing minigame featuring destination-specific skies and terrain. Starting at 180 m altitude and 9 m/s descent speed, you hold the retro-thrust control to burn fuel and decelerate, aiming for a touchdown speed at or below the 6 m/s safe zone (evaluated at 4 m above the surface).


## Extra Features We Added

Themes & Audio: Six custom UI themes (three dark gradients: Aurora, Solar Flare, Arctic Pulse; three high-contrast light gradients: Solaris, Botanical, Daybreak) plus a 0–100% UI sound volume slider. (Note: Since native Streamlit dropdowns don't trigger events just by opening, our selection audio cue plays as soon as you lock in an option).

Quick-Play Presets: Sidebar presets for a Beginner Moon run or a Hardcore Jupiter challenge, alongside a mission reset button and a quick Space Apps explainer.

Responsive Canvas Physics: To keep the Streamlit UI responsive and avoid laggy reruns during the landing minigame, the HTML5 canvas runs the descent locally and syncs a validated physics snapshot back to Python once you touch down or crash.

## Game Rules, Scoring & Balance

All of our core math, typed calculation functions, and part stats live in `mission_design.py`. Parts start unselected (contributing 0 kg and 0 upthrust) until you build your ship.

## Destination Modifiers & Hull Requirements

To reflect the hazards of different environments in our research notes, we enforced minimum hull tiers and difficulty multipliers for each destination:

| Destination | Difficulty Modifier | Minimum Required Hull |
| :--- | :---: | :--- |
| **Moon** | 0.7 | Lightweight Aluminum Frame |
| **Mars** | 1.0 | Lightweight Aluminum Frame |
| **Mercury** | 1.2 | Carbon-Composite Shell |
| **Uranus** | 1.6 | Reinforced Titanium-Alloy Hull |
| **Venus** | 1.7 | Carbon-Composite Shell |
| **Neptune** | 1.8 | Reinforced Titanium-Alloy Hull *(extended for ice giants)* |
| **Saturn** | 2.0 | Reinforced Titanium-Alloy Hull |
| **Jupiter** | 2.1 | Reinforced Titanium-Alloy Hull |

*(Note: Our Heavy-Duty Deep Space Pod uses the 800 kg mass value from our team research notes, and the Hardcore Jupiter preset comes pre-loaded with the reinforced hull, standard solar arrays, basic sensors, passive MLI insulation, optical imaging suite, heavy-duty engine cluster, and deep-space fuel pod).*

## Attempts & Victory Scoring

Players get **two attempts total** per minigame. A second slingshot miss or landing crash brings up a failure scorecard with diagnostics on what went wrong and a button to head back to the assembly bay.

If the player lands safely without crashing, their final score is calculated as:

`(research × launch risk × slingshot multiplier) + fuel-efficiency points`

* **Slingshot Multiplier:** `1 + (0.2 × gravity-assist encounters)`. Every gravity assist the player pulls off boosts their score, **but** each encounter drains 4% of their fuel tank capacity before transit. This forces the player to balance higher multipliers against having enough fuel left to land.
* **Fuel Efficiency Points:** Equal to the percentage of fuel remaining in their tank at touchdown.

  
## Simulation Fidelity & Engineering Assumptions

We designed this project as an educational arcade game rather than an aerospace flight-design tool, so we intentionally simplified the physics to keep gameplay fun and predictable:

* Atmospheric Drag & Staging: Real launches deal with multi-stage separation, changing mass, and atmospheric drag `F_D = ½ ρ v² C_D A`. Our build phase uses total static mass and combined upthrust modifiers instead.
  
* Orbital Mechanics: Real trajectories account for N-body perturbations, non-spherical gravity, and solar radiation pressure. Our slingshot phase uses a deterministic 2D arcade gravity model so the trajectory preview line matches the actual flight path every time.

* Propulsion & Landing: Ideal rocket propulsion follows the Tsiolkovsky rocket equation `Δv = I_sp g_0 ln(m_0 / m_f)`. In Phase 5, we swapped variable mass-flow math for a fixed retro-thrust deceleration rate and scaled destination gravity (1.05×) with a gentler gravity ramp below 6 m/s so players can fine-tune their final approach.

## Research & References
Here are the resources our team used while designing the game mechanics and educational tooltips:

* [ESA & CNES — Guiana Space Centre (Europe's Spaceport)](https://centrespatialguyanais.cnes.fr/en) — Reference data for our equatorial launch-site modifiers.
  
* [NASA Glenn Research Center — Ideal Rocket Equation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/ideal-rocket-equation/) — Background on specific impulse, mass ratios, and ideal change in velocity.
  
* [NASA — Introduction to Orbital Mechanics and Spacecraft Attitudes](https://tfaws.nasa.gov/wp-content/uploads/Rickman-Presentation.pdf) — Reference for Kepler's laws, gravity assists, and thermal considerations.
  
* [NASA JPL — Basics of Space Flight: Gravity & Mechanics](https://science.nasa.gov/learn/basics-of-space-flight/chapter3-1/) — Reference for inverse-square gravity and elliptical orbits.


## Disclosure:
We used Super Intelligence (SI/AI) tool assistance for the hackathon to help speed up making a boilerplate UI layout, SVG generation, and code structuring. All game design, balancing, research, and final implementation were built and verified by Team MAASA.
