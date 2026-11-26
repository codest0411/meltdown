# Changelog

All notable changes to **MELTDOWN** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
