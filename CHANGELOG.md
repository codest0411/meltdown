# Changelog

All notable changes to **MELTDOWN** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-11-27

### Added
- **Modular Package Architecture**: Split game into `alarms.py`, `audio.py`, `bosses.py`, `lan.py`, `save.py`, `themes.py`, and `game.py`.
- **5 New Alarm Types** (15 total): `HEX/OCTAL`, `LOGIC GATE`, `PING/PORT`, `TYPO HUNT`, and `VENT MASH` (`x3`).
- **Station Hazards**: `Overheat`, `EMP Flicker`, `Radiation Leak` (`PURGE`), and `Low Oxygen` (`OXYGEN`).
- **Reactor Bay Upgrade Draft (Perks)**: `Auto-Coolant`, `Reinforced Bulkhead`, `Buffer Shield`, `Quick Fingers`, and `Power-up Magnet`.
- **New Modes & Mutators**: `Boss Rush`, `Practice / Training`, `Custom Sandbox` (`SBX-...` shareable codes), `LAN Versus` (TCP sockets), plus `Glass Cannon`, `Blindfold`, and `Turbo` mutators.
- **Cross-Platform Audio Engine**: Non-blocking `winsound.Beep` on Windows and synthesized WAV playback via `afplay`/`aplay`/`paplay` on macOS/Linux with combo chimes and warning pulses.
- **Themes, Skins & Visual Polish**: `Cyber Cyan`, `Classic Amber`, `Red Alert`, and `Monochrome High-Contrast` themes; unlockable Reactor Core skins; screen shake; animated transitions; ASCII bar fallback; and `KEY_RESIZE` / small-terminal overlay.
- **Progression & Social**: Operator Rank grades (`S+`–`D`), personal-best **Ghost Replay** tracker, exportable **Run Cards** (`~/.meltdown/last_run_card.md`), and in-game **Field Manual**.

## [2.3.0] - 2026-11-27

### Added
- **CRT Hazard Box Game Over Screen**: Retro double-bordered `STATION LOST` screen with caution hazard stripes, symmetrical fractured reactor core symbol, `[ * NEW HIGH SCORE! * ]` badge, and inner `RUN SUMMARY` card.
- **Idempotent PyPI Publishing**: Enabled `skip-existing: true` in `.github/workflows/publish.yml` so re-running the publish workflow on an already-uploaded version succeeds cleanly instead of failing.

## [2.2.0] - 2026-11-26

### Added
- **ORBITAL COMMAND OS UI/UX**:
  - Double-line `╔═╗║╚╝` cockpit frames across all menus, settings, leaderboard, achievements, statistics, mission debrief, and callsign entry.
  - Main menu `MELTDOWN` ASCII banner with live `BEST`, `MEDALS`, and `[SAVED RUN READY]` status strip plus contextual option hints.
  - `[ * ON ]` / `[ o OFF ]` toggle pills in Settings and progress bar in Station Commendations.
  - Updated PNG screenshots in `screenshots/`.

## [2.1.0] - 2026-11-26

### Added
- **Reactor Cockpit UI/UX Redesign**:
  - Responsive 2-column cockpit layout on terminals ≥ 96×22 (`INCOMING ALARMS` + `REACTOR TELEMETRY`) with automatic compact fallback on 80×24.
  - Live animated ASCII **Reactor Core** that shifts color and symbol with stress, hull, and cryo-freeze status.
  - Smooth Unicode block progress bars (`█░`), urgency badges (`[SAFE]`, `[WARN]`, `[CRIT]`, `[PWR]`, `[BOSS]`), and a live `COMMS LOG`.
  - Box-drawn menus (`MELTDOWN v2.1 :: REACTOR CONSOLE`) and modal screens.
- **Level-Scaled Words & Calculations**:
  - Tiered word pools (`WORDS_EASY`, `WORDS_MED`, `WORDS_HARD`) that progress with level.
  - Non-repeating prompt history across levels and boss fights.
  - Scaling difficulty for `SOLVE` math, `SEQUENCE` (including descending sequences), `BINARY`, `MEMORIZE`, and `SEQ LOCK`.

## [2.0.0] - 2026-11-26

### Added
- **Installable CLI package** (`meltdown-terminal`) using `src/`-layout and `pyproject.toml`.
- **`meltdown` CLI command** with `--help`, `--version`, and `python -m meltdown` support.
- **Power-ups**: `FREEZE`, `REPAIR`, `CALM`, and `CLEAR`.
- **3 Boss Fights**: *The Sentinel*, *The Guardian*, and *The Core* with multi-phase codes and boss HP bars.
- **5 New Alarm Types**: `SEQUENCE`, `BINARY`, `MORSE`, `DECODE`, and `SEQ LOCK` (10 total).
- **Difficulty Modes**: `Casual`, `Operator`, and `Nightmare`.
- **Two-Player Modes**: Shared-screen `Co-op` (`Tab` to switch) and seeded `Versus`.
- **Daily Challenge**: Date-seeded 5-level run with separate daily high score tracking.
- **19 Achievements** with persistent unlocks and in-game notifications.
- **Top-10 Leaderboard** with 3-letter initials and mission report statistics.
- **Story Events & Choices** between levels.
- **Accessibility Options**: Reduced Flashing, Show Timer Numbers, Colorblind Mode, and Large UI.
- **Save & Resume**: Auto-save in `~/.meltdown/data.json` (override with `MELTDOWN_DATA_DIR`).
- **Automated Test Suite** (`pytest`) and GitHub Actions CI/PyPI Trusted Publishing workflows.

### Fixed
- `SaveManager` now deep-copies default data structures to prevent shared mutable state.
- Pausing (`Esc`) and `FREEZE` power-ups now properly shift alarm timers so alarms do not expire prematurely.
- `CLEAR` power-up now properly credits cleared alarms toward level quota.
- Returning to main menu from the pause screen no longer exits the application.

## [1.0.0] - Initial Release

### Added
- 7 handcrafted levels plus endless mode.
- 5 alarm types (`TYPE`, `REVERSE`, `SOLVE`, `UNSCRAMBLE`, `MEMORIZE`).
- Stress, hull, combo multiplier, display glitches, and alarm surges.
- Single high-score persistence in `~/.meltdown_highscore.json`.
