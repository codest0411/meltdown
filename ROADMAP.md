# 🗺️ MELTDOWN — Future Features & Design Roadmap

A structured blueprint for **MELTDOWN v3.0+**, covering new gameplay mechanics, UI/UX design, audio, multiplayer, progression, and technical improvements.

---

## 1. 🎮 Gameplay & Mechanics

### New Alarm Types
- **HEX / OCTAL**: Convert hexadecimal (`0x2F` → `47`) or octal values to decimal.
- **LOGIC GATE**: Solve quick boolean expressions (`1 AND 0`, `1 XOR 1`).
- **PING / PORT**: Match a target system port or IP fragment shown in a noisy log stream.
- **TYPO HUNT**: Spot and type the *one* misspelled word in a pair of station logs.
- **HOLD / MASH**: Rapidly tap a key or type a short word multiple times to vent pressure.

### Station Hazards & Status Effects
- **Overheat**: Input buffer occasionally drops a character unless cooled.
- **EMP Flicker**: Temporarily hides alarm labels (only the prompt remains visible).
- **Radiation Leak**: Hull slowly ticks down until a `PURGE` alarm is cleared.
- **Low Oxygen**: Stress rises faster until an `OXYGEN` alarm is resolved.

### Upgrade & Perk System (Between Levels)
Replace or expand static story choices with a **Reactor Bay Upgrade Draft** (pick 1 of 3):
- **Auto-Coolant**: Passive `-1.5` stress/sec when fewer than 2 alarms are active.
- **Reinforced Bulkhead**: Reduces hull damage per missed alarm by 5%.
- **Buffer Shield**: First wrong `Enter` per level does not break your combo.
- **Quick Fingers**: +15% score bonus for answers under 1.5 seconds.
- **Power-up Magnet**: Higher power-up spawn rate and longer `FREEZE` duration.

### New Game Modes
- **Boss Rush**: Fight all 3 bosses back-to-back with minimal recovery between fights.
- **Practice / Training Mode**: Pick any specific alarm type (e.g., `MORSE` or `BINARY`) and practice without hull/stress penalties.
- **Custom Sandbox**: Configure starting level, alarm types, spawn speed, TTL, and mutators, then share a **Seed + Config Code** with friends.
- **Mutators / Weekly Modifiers**:
  - *Glass Cannon*: 1 HP hull, 2x score.
  - *Blindfold*: All alarms hide after 1.5s.
  - *Turbo*: 1.5x speed, 1.5x combo multiplier.

---

## 2. 🎨 Terminal UI & Visual Design

### Layout & Dashboard Overhaul
Move from a single vertical list to a responsive **2-column cockpit layout** (when terminal width ≥ 100 cols, falling back to single-column on 80×24):
- **Left Panel**: Active alarms, sorted by urgency, with color-coded priority badges (`[CRIT]`, `[WARN]`, `[OK]`).
- **Right Panel**:
  - Live **ASCII Reactor Core** graphic that changes animation speed/color with stress & hull.
  - Active buffs/debuffs (`FREEZE 3.4s`, `OVERDRIVE x1.5`, `RADIATION`).
  - Mini-log of recent actions (`+240 COMBO x4`, `REPAIR +20 HULL`).

### Visual Polish & Feedback
- **Screen Shake**: Brief 1–2px horizontal offset on hull damage or boss hits (disabled when `Reduced Flashing` is ON).
- **Color Themes**: Unlockable or selectable terminal palettes:
  - *Classic Amber* (retro CRT)
  - *Cyber Cyan*
  - *Red Alert*
  - *Monochrome High-Contrast*
- **Unicode Progress Bars**: Upgrade `[###---]` to smooth block bars `[███▒▒▒]` with an optional ASCII fallback setting for older terminals.
- **Animated Transitions**: Warp-line or static-wipe transitions between levels and boss intros.

---

## 3. 🔊 Audio Design (Zero External Dependencies)

Upgrade beyond `curses.beep()` using built-in OS tools (with graceful fallback):
- **Windows**: `winsound.Beep(freq, ms)` in a background thread so gameplay never stutters.
- **macOS / Linux**: Synthesize tiny in-memory WAV tones via Python's `wave` + `math` modules and play via `afplay` / `aplay` / `paplay`.
- **Sound Events**:
  - Rising pitch chime on combo streaks (`x2`, `x5`, `x10`).
  - Low warning pulse when `STRESS > 80%` or `HULL < 25%`.
  - Distinct power-up activation and boss phase-break tones.
  - Optional **Volume / Mute** toggle in Settings.

---

## 4. 👥 Multiplayer & Community

- **LAN / Socket Co-op & Versus**: Play over local network (`socket` + `asyncio` or threads) on separate terminals instead of sharing one keyboard.
- **Ghost Replays**: Record timestamped run events to JSON and race against your personal best's "ghost" progress bar.
- **Shareable Run Cards**: Generate an ASCII/Markdown summary card at game over (score, level, accuracy, rank grade `S`/`A`/`B`/`C`) ready to copy-paste.

---

## 5. 🏆 Progression & Rank System

- **Operator Rank / Grade**: End-of-run grade (`S+`, `S`, `A`, `B`, `C`, `D`) based on accuracy, speed, and level reached.
- **Unlockable Console Skins**: Unlock new title banners and reactor ASCII art via achievements.
- **Alarm Encyclopedia / Field Manual**: An in-game `Help / Manual` menu showing examples and tips for all 10+ alarm types.

---

## 6. 🛠️ Technical & Packaging Improvements

- **Modular Package Structure**: Split `meltdown.py` into clean modules (`meltdown/alarms.py`, `meltdown/bosses.py`, `meltdown/ui.py`, `meltdown/save.py`, `meltdown/audio.py`) while keeping a single-command entry point.
- **PyPI Distribution**: Add `pyproject.toml` so users can install and launch globally via `pip install meltdown-terminal` → `meltdown`.
- **Automated Test Suite**: Add `pytest` / `unittest` tests for alarm generation, answer validation, scoring, save migration, and level scaling, plus GitHub Actions CI.
- **Auto-Resize Handling**: Handle `curses.KEY_RESIZE` cleanly and show a friendly `"Terminal too small (need 80x24)"` overlay if shrunk below minimum dimensions.
