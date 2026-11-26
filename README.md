<div align="center">

# ☢️ MELTDOWN v2.0

### A stressful, fast-typing survival game that runs entirely in your terminal.

![Python](https://img.shields.io/badge/python-3.8%2B-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

<br>

<img src="screenshot.svg" alt="MELTDOWN gameplay in a terminal" width="720">

<sub>Illustration of the game screen (Level 4: Solar Flare).</sub>

</div>

---

## 🚨 The Story

The space station is failing. Every other operator is gone. You are the last one at the console.

Alarms keep firing, the timers keep shrinking, and your stress keeps rising. Answer every alarm before it expires, or the hull will not hold. **How many levels can you survive?**

## ✨ Features

- 🎮 **7 handcrafted levels** that get faster and meaner, then **endless mode** after that
- ⏱️ **Multiple alarms at once**, each with its own countdown
- 🧠 **10 alarm types**: type, reverse, solve, unscramble, memorize, sequence, binary, morse, decode, seq lock
- 😰 **Stress and hull meters** — lose either one and the station is lost
- 🔥 **Combo multiplier** for streaks, wiped out by one mistake
- 📺 **Random events**: corrupted displays and alarm surges
- 🔋 **Power-ups**: freeze time, repair hull, calm stress, clear all alarms
- 👾 **3 boss fights**: The Sentinel, The Guardian, The Core
- ⚙️ **3 difficulty modes**: Casual, Operator, Nightmare
- 📖 **Story events**: narrative transmissions and strategic choices between levels
- 👥 **Two-player modes**: Co-op and Versus
- 🏆 **Top-10 leaderboard** with daily challenge rankings
- 🎖️ **19 achievements** to unlock
- 📊 **Detailed statistics**: accuracy, response times, longest combo, and more
- 💾 **Save & resume**: quit mid-run and continue later
- ♿ **Accessibility options**: reduced flash, colorblind mode, large UI, timer numbers
- 🔊 **Sound effects** (toggle-able terminal beeps)
- 📦 **Zero dependencies**: only Python's standard library

## 🕹️ Alarm Types

| Alarm | What to do | Example |
|---|---|---|
| `TYPE` | Type the word shown | `REACTOR` → `reactor` |
| `REVERSE` | Type the word backwards | `CORE` → `eroc` |
| `SOLVE` | Type the answer to the math | `7 + 5` → `12` |
| `UNSCRAMBLE` | Rearrange the scrambled letters | `TCRAOER` → `reactor` |
| `MEMORIZE` | Remember the code before `*****` appears | `48213` → `48213` |
| `SEQUENCE` | Find the next number in the pattern | `2, 5, 8, 11, ?` → `14` |
| `BINARY` | Convert binary to decimal | `10110` → `22` |
| `MORSE` | Decode the morse code | `.-  .-.  -.-.` → `arc` |
| `DECODE` | Identify the word from two corrupted versions | `R#CT$R \| R$@CT#R` → `reactor` |
| `SEQ LOCK` | Remember the direction sequence before it hides | `UDLRU` → `udlru` |

Capital letters do not matter. Answer in any order: your input is matched against all active alarms.

## 📈 Levels

| # | Level | New twist |
|---|---|---|
| 1 | Boot Sequence | Just typing words. Warm up. |
| 2 | Coolant Leak | Reversed words appear |
| 3 | Pressure Spike | Math problems and sequences |
| — | **BOSS: The Sentinel** | *First boss fight* |
| 4 | Solar Flare | Scrambled words, binary, and **corrupted displays** |
| 5 | Blackout | Memorize codes and morse that vanish |
| — | **BOSS: The Guardian** | *Second boss fight with stress attacks* |
| 6 | Core Breach | Decode corrupted words, **alarm surges** |
| 7 | Total Meltdown | All 10 alarm types, everything at once |
| — | **BOSS: The Core** | *Final boss fight* |
| ∞ | Endless Dread | It never stops getting harder |

## 🔋 Power-ups

Power-ups spawn randomly during gameplay. Type the keyword to activate:

| Power-up | Keyword | Effect |
|---|---|---|
| ⏸️ Freeze | `freeze` | Freezes all alarm timers for 5 seconds |
| 🔧 Repair | `repair` | Restores 20 hull integrity |
| 😌 Calm | `calm` | Reduces stress by 30 |
| 💥 Clear | `clear` | Removes all active alarms |

## 👾 Boss Fights

Bosses appear after levels 3, 5, and 7. Each boss has:
- **Multi-phase codes** you must type to damage the boss
- A **Boss HP bar** — deplete it to win
- **Regular alarms** that keep spawning as distractions
- Later bosses have **stress attacks** that raise your stress periodically

## ⚙️ Difficulty Modes

| Mode | Spawns | Timer | Stress | Hull Damage | Power-ups |
|---|---|---|---|---|---|
| Casual | 50% slower | 40% more time | 40% less | 10% per miss | Frequent |
| Operator | Normal | Normal | Normal | 15% per miss | Regular |
| Nightmare | 30% faster | 25% less time | 40% more | 20% per miss | Rare |

## 👥 Two-Player Modes

### Co-op
Both players share the screen and alarms. Press **Tab** to switch the active player. Each player has their own combo counter; hull and stress are shared.

### Versus
Players take turns playing the same levels with the same alarm sequence (same random seed). Scores are compared at the end. May the best operator win.

## 📅 Daily Challenge

A seeded 5-level challenge that is the same for everyone on the same day. Access it from the main menu. Your daily high score is tracked separately on the leaderboard.

## 🎖️ Achievements

19 achievements to unlock, including:

| Achievement | How to unlock |
|---|---|
| First Clear | Clear your first level |
| No Mistakes | Clear a level with zero wrong answers |
| Perfect Level | Clear a level without hull damage |
| Speed Solver | Answer an alarm within 1 second |
| Combo x20 | Reach a combo of 20 |
| Endless Survivor | Enter endless mode |
| Boss Slayer | Defeat any boss |
| Core Crusher | Defeat all 3 bosses |
| Nightmare Fuel | Clear level 1 on Nightmare |
| Polyglot | Answer every alarm type in one run |

## 💀 How You Lose

- **STRESS** goes up while alarms are active and every time you answer wrong. At **100%**, you crack.
- **HULL** drops with every alarm that runs out of time. At **0%**, the station breaks apart.
- Clearing alarms lowers stress, and finishing a level repairs a little hull.

## 📖 Story Events

Between levels, receive transmissions from Control and make strategic choices:
- **Reroute power** to shields, sensors, or weapons
- **Emergency protocols** for stress relief, score boost, or hull repair
- **Final stand** options before the ultimate levels

Your choices affect gameplay for the next level.

## ♿ Accessibility

Toggle from the Settings menu:

| Option | Effect |
|---|---|
| Reduced Flashing | Disables screen shake, glitch effects, panic flashing |
| Show Timer Numbers | Shows numeric seconds remaining alongside bars |
| Colorblind Mode | Adds `!`/`~`/`+` symbols alongside colors |
| Large UI | Increases spacing between alarms |

## 📊 Statistics

After each game, see a detailed mission report:
- Accuracy percentage
- Average and fastest response times
- Longest combo
- Most missed alarm type
- Power-ups collected
- Survival time

Lifetime stats are tracked across all games.

## 💾 Save System

- **Auto-save** after each level clear
- **Save & quit** from the pause menu (ESC)
- **Continue** from the main menu to resume your run
- Leaderboard, achievements, settings, and lifetime stats are all persistent

Save data is stored in `~/.meltdown/data.json`.

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/codest0411/meltdown.git
cd meltdown
```

### 2. Run it

**macOS / Linux**

```bash
python3 meltdown.py
```

**Windows**

```bash
pip install windows-curses
python meltdown.py
```

> 💡 Use a terminal window of at least **80 × 24** so every alarm fits on screen.

## 🎛️ Controls

| Key | Action |
|---|---|
| Letters / numbers | Type your answer |
| `Enter` | Submit the answer |
| `Backspace` | Fix a typo |
| `Escape` | Pause menu |
| `Tab` | Switch player (co-op mode) |
| `Ctrl + C` | Quit |

## 🎛️ Main Menu

```
M E L T D O W N
├── New Game → Difficulty → Mode → Play
├── Continue (resume saved game)
├── Daily Challenge
├── Leaderboard
├── Achievements
├── Statistics
├── Settings
└── Quit
```

## 🔧 Customization

All difficulty settings live in the `LEVELS` table and `DIFFICULTY` presets at the top of `meltdown.py`:

```python
# name, flavour, quota, spawn_secs, alarm_ttl, max_active, pressure, kinds, glitch, surge
("CORE BREACH", "...", 16, 1.7, 8, 5, 1.4, [...], True, True),
```

| Setting | Meaning |
|---|---|
| `quota` | Alarms to clear to finish the level |
| `spawn_secs` | Average seconds between new alarms (lower is harder) |
| `alarm_ttl` | Seconds you get per alarm (lower is harder) |
| `max_active` | Most alarms on screen at the same time |
| `pressure` | How fast stress builds per active alarm |
| `kinds` | Which alarm types can appear |
| `glitch` / `surge` | Enable corrupted displays or alarm surges |

Add your own words to the `WORDS` list to make it your own.

## 🤝 Contributing

Ideas and pull requests are welcome. Fork the repo, create a branch, and open a PR. New alarm types are the easiest way to add something fun: add one in the `Alarm` class and list it in a level's `kinds`.

## 📄 License

Released under the [MIT License](LICENSE).

---

<div align="center">

**Think you can survive Total Meltdown?** ⭐ Star the repo if you made it.

</div>
