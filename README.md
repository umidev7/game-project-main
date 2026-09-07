# Neon Rift

Neon Rift is an asset-free 2D space shooter built with Python and Pygame. This README is for developers. Players should use the packaged ZIP from the `release/` folder.

## Developer Setup

From the project folder, create the virtual environment:

   ```powershell
   uv venv
   ```

Install the dependencies, including the PyInstaller build tool:

   ```powershell
   uv pip install -r requirements.txt
   ```

Run the game from source:

   ```powershell
   uv run python test.py
   ```

## Build the Windows Executable

Run the build script from the project folder:

```powershell
.\build.bat
```

The script builds `test.py` as a windowed, standalone executable and copies it to `release/NeonRift.exe`. The complete player distribution is the `release/` folder, which contains the executable and the player `README.txt`.

The game has no external graphics, sound, or font files. Its graphics and sound effects are generated at runtime, so PyInstaller does not need additional asset files.

## Troubleshooting

If you see `ModuleNotFoundError: No module named 'pygame'`, install the dependencies in the uv environment:

```powershell
uv pip install -r requirements.txt
```

If you see `externally-managed-environment`, do not install packages into the system Python. Use `uv venv` and the commands above instead.

## Project Structure

- `README.md`: developer setup, source-running, and build instructions.
- `build.bat`: builds the standalone Windows executable and release folder.
- `requirements.txt`: pinned Python dependencies.
- `test.py`: main game entry point; run this file to start Neon Rift.
- `space_game.py`: game implementation, including menus, levels, combat, sounds, and rendering.
- `release/README.txt`: short instructions included with the player distribution.
- `.gitignore`: generated files excluded from Git.

## Controls

- `WASD` or arrow keys: move
- `Space`: fire
- `Esc`: pause or resume
- `Enter`: start or restart from keyboard
- Mouse: use the menu buttons

The game stores the high score in the user's writable application-data folder rather than beside the executable. This allows the game to run from any extracted folder without requiring administrator permission.