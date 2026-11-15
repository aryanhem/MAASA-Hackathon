# MAASA-Hackathon
The repository for team MAASA's entry for the 2026 annual NASA Hackathon

## Mission design foundation

`mission_design.py` contains the team-notes choices and typed calculation functions. Mission mass sums one choice from each spacecraft component category, the engine, and the fuel tank; required upthrust applies both the launch-site and destination modifiers. The success and progress calculations are arcade-game rules, not a physical rocket simulation. The Heavy-Duty Deep Space Pod uses the 800 kg value from the research notes.

Run the interactive game with `streamlit run app.py`. Phase 1 provides an interactive Plotly world map with selectable launch-site markers, a synced launch-site selector, and destination selection; confirming the location advances to Phase 2, where the spacecraft is assembled. A complete build that meets its required upthrust unlocks Phase 3, a drag-to-aim gravitational slingshot: pull backward from the rocket to preview a dotted gravity-curved route, release to launch, and reach the target landing zone while avoiding flyby hazards. The responsive canvas reports its full rendered height so the scene is not clipped. Its route varies with the destination: the Moon shows satellites and debris, while outer-planet missions add the intervening planets in order (for example, Neptune's route passes Mars, Jupiter, Saturn, and Uranus). A deterministic, simplified arcade gravity model powers both the canvas preview and server-side result; it is not a physically accurate orbital simulation. A miss or collision shows a failure overlay with a retry control, while success unlocks Phase 4. Phase 4 animates a starfield journey from an Earth globe with land/ocean details to a destination-specific planetary surface; transit duration scales with orbital distance and distance, ETA, and fuel telemetry update in flight. A distinct arrival transition leads to Phase 5, an animated HTML5 Canvas landing minigame with destination-specific planetary skies and terrain, an animated rocket descent, retro-thrust exhaust, and vertical altitude and touchdown-speed gauges with a marked ≤6 m/s safe zone. Hold the single retro-thrust control to spend fuel and decelerate; releasing it returns the spacecraft to a destination-gravity descent with a gentler gravity ramp below 6 m/s. Touchdown is evaluated at 4 m above the drawn surface; successful touchdown and crash/fuel failure have distinct canvas animations, with a restart control for either outcome. Landing starts at 180 m and 8 m/s. The canvas syncs a validated physics snapshot to Streamlit when landing ends, avoiding reruns during the interactive descent so other controls remain responsive. Players can return to assembly from flight or landing. The sidebar offers Aurora, Solar Flare, and Arctic Pulse dark gradients plus three bright, high-contrast light gradients—Solaris, Botanical, and Daybreak—a 0–100% interface sound volume slider, Beginner Moon and Hardcore Jupiter presets, a mission reset, and a short NASA Space Apps explainer; set the volume to 0 to mute sounds. Native Streamlit dropdowns do not expose an event for merely opening the menu, so their selection cue plays when an option is chosen. Components, engine, and fuel tank start unselected and contribute 0 kg or 0 upthrust until chosen. The right-hand mission panel and upthrust progress bar remain visible throughout the mission.

Phase 2 includes a live inline-SVG spacecraft schematic that updates with component, engine, fuel tank, and theme selections. Selected-part descriptions appear alongside the drawing, with matching hover tooltips on the drawn parts; the mission readiness panel remains beside the schematic. Hull material changes the fuselage appearance, selected solar equipment adds arrays, thermal protection adds a striped insulation texture, avionics add a circuit-board detail, instruments add an optical sensor motif, and the engine and tank are drawn at the base.

Destination difficulty values are Moon 0.7, Mars 1.0, Mercury 1.2, Venus 1.7, Saturn 2.0, Neptune 1.8, Jupiter 2.1, and Uranus 1.6. Hull minimums follow the team hazard notes: Moon/Mars require Lightweight Aluminum Frame, Mercury/Venus require Carbon-Composite Shell, and Uranus/Saturn/Jupiter require Reinforced Titanium-Alloy Hull. Neptune is assigned the reinforced hull minimum as a conservative extension for the unlisted ice giant. The Hardcore Jupiter preset uses the screenshot's reinforced hull, standard solar arrays, basic sensors, passive MLI insulation, optical imaging suite, heavy-duty engine cluster, and deep-space fuel pod.

Each minigame allows two attempts total. A second slingshot miss or landing crash displays a failure scorecard with phase-specific diagnostics and a return-to-design control. A successful landing displays the victory scorecard: research points from selected systems, a launch-site risk multiplier, a slingshot multiplier of `1 + (0.2 × gravity-assist encounters)`, and fuel-efficiency points (remaining fuel as a percentage of tank capacity). Each gravity-assist encounter costs 4% of tank capacity before transit, making route complexity a fuel trade-off. The score is `(research × launch risk × slingshot multiplier) + fuel-efficiency points`. Landing now begins at 9 m/s with 1.05× destination gravity to make descent slightly faster and harder; the safe touchdown limit remains 6 m/s.



## How the Mission Works

We structured the game into five distinct phases, keeping a live mission readiness panel and upthrust progress bar visible on the right side of the screen throughout the entire run.

Phase 1: Launch & Destination Selection

* Players pick their launch site using an interactive Plotly world map (synced with a dropdown selector) and choose their target planet or moon.

Phase 2: Spacecraft Assembly

* Players select their hull, solar equipment, thermal protection, avionics, instruments, engine, and fuel tank. We built a live inline-SVG schematic that updates dynamically as parts are added (changing fuselage textures, adding solar arrays, or showing circuit-board details—complete with hover tooltips). Once the build meets the required upthrust, Phase 3 unlocks.

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
We used Super Intelligence (SI/AI) tool assistance for the hackathon to help speed up making a boilerplate UI layout, SVG generation, and code structuring. All game design, balancing, research, and final implementation were built and verified by Team MAASA. This disclosure supports transparency and hackathon-guideline compliance; the team remains responsible for confirming and following all applicable event rules.
