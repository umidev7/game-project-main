# Neon Rift

Neon Rift is a single-player Pygame space shooter with an original dark sci-fi soundtrack.

## Run From Source

```powershell
uv venv
uv pip install -r requirements.txt
uv run python space_game.py
```

Controls: `WASD` or arrow keys move, `Space` fires, `Esc` pauses, and `Enter` starts or restarts.

## Build Windows Executable

```powershell
.\build.bat
```

The script builds the single-player executable at `release/NeonRift.exe`.

## Project Structure

- `space_game.py`: single-player game source.
- `build.bat`: builds the Windows executable.
- `requirements.txt`: Pygame and the build tool dependency.