# Contributing to MELTDOWN

Thank you for your interest in contributing to **MELTDOWN**!

## Development Setup

1. Fork and clone the repository:
   ```bash
   git clone https://github.com/codest0411/meltdown.git
   cd meltdown
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```
3. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

Run the full test suite before submitting a pull request:

```bash
pytest
```

To also verify packaging and wheel installation:

```bash
python -m build
twine check dist/*
```

## Code Guidelines

- Keep runtime dependencies minimal (standard library only, plus `windows-curses` on Windows).
- Ensure all terminal output uses bounds-checked helpers (`put`, `center`) so small terminals do not crash.
- Keep user save data outside the package directory (`~/.meltdown/data.json` or `MELTDOWN_DATA_DIR`).
- Add tests in `tests/` for any new alarm types, mechanics, or CLI options.
- Update `CHANGELOG.md` and `README.md` when adding user-facing features.

## Pull Request Process

1. Create a feature branch from `main`.
2. Make your changes and add/update tests.
3. Verify `pytest` passes on your machine.
4. Open a Pull Request using the repository template.
