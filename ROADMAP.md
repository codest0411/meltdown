# 🗺️ MELTDOWN — v4.0.0 Roadmap

> **v3.0.0 is shipped** on [PyPI](https://pypi.org/project/meltdown-terminal/) and [GitHub](https://github.com/codest0411/meltdown/releases/tag/v3.0.0).  
> Below is the blueprint for **MELTDOWN v4.0.0**.

---

## 1. 🧩 Community Mods & Custom Content

- **Custom Word Packs (`~/.meltdown/words.txt`)**: Load player-defined word lists (e.g., Python keywords, cybersecurity terms, medical terms, or custom languages) right from Settings.
- **Custom Alarm Plugin API**: Drop a `.py` file into `~/.meltdown/plugins/` to register new alarm types without editing the core package.
- **Weekly Seeded Mutator Rotation**: Automatic ISO-week seed (`YYYY-Www`) pairing a fixed mutator + level ruleset with a dedicated weekly leaderboard.

---

## 2. 📖 Story Campaign 2.0 (Branching Sectors)

- **Sector Map Selection**: Between levels, choose between 2–3 station sectors (e.g., *Cryo Bay* with slower stress vs. *Reactor Spine* with 1.5x score).
- **Dynamic Boss Dialogue & Weaknesses**: Bosses react to your accuracy, perks, and current hull, with phase-specific mechanics (e.g., EMP burst phase, speed-round phase).
- **Ending Variations**: Multiple victory/epilogue endings at Level 7+ based on hull remaining, perks installed, and bosses defeated.

---

## 3. 🧠 New Alarm Types (Targeting 20 Total)

- **REGEX MATCH**: Type a short string that matches a shown pattern (`^[a-z]{3}[0-9]{2}$`).
- **COLOR / SYMBOL CODE**: Match a flashing ANSI/symbol sequence (`▲ ◆ ● ▲`).
- **CHECKSUM**: Sum the digits of a packet ID (`4819 -> 22`).
- **CIPHER (CAESAR +1 / ROT13)**: Decode a shifted 4-letter station callsign.
- **DUAL-LOCK**: Two linked prompts that must be cleared back-to-back within 3 seconds.

---

## 4. 🌐 Online / Relay Multiplayer & Replays

- **Online Relay Versus**: Lightweight optional WebSocket/TCP relay room codes (`JOIN ABC123`) so friends can play Versus across different networks without port-forwarding.
- **Full Run Replay Theater**: Record keystrokes and timestamps to `~/.meltdown/replays/` and watch past runs play back at `1x` / `2x` / `4x` speed in the terminal.
- **Live Ghost Bar**: Visual side-by-side progress bar racing against your personal best ghost in real time.

---

## 5. 🎨 Terminal UI & Audio Polish

- **Live Terminal GIF / SVG Recorder**: Built-in `--record` flag or post-run export to save an animated SVG replay of your run.
- **Smooth Status Animations**: Animated hazard borders during `RADIATION` / `LOW O2` and crisp level-clear fanfare screens.
- **Multi-Tone Audio Chords**: Short 2–3 note arpeggios for level clear, rank `S+` achievement, and boss defeat.

---

## 6. 🛠️ Engineering & Distribution

- **Automated PTY / Headless Terminal Tests**: End-to-end tests driving `meltdown` inside a pseudo-terminal (`pty` / `pexpect`) in CI.
- **Homebrew Tap & Scoop Manifest**: One-line install via `brew install meltdown-terminal` (macOS/Linux) and `scoop install meltdown` (Windows).
- **Zero-Config Windows Launcher**: Signed/trusted launcher options or automatic PATH/PowerShell helper (`meltdown setup-shell`) to avoid unsigned `.exe` wrapper blocks.
