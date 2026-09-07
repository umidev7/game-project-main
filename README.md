# Neon Rift

Neon Rift is an asset-free Pygame space shooter with an authoritative online survival mode. The original single-player game remains available in `space_game.py` and the shared gameplay classes remain in `test.py`.

## For Players

1. Download the player ZIP.
2. Extract it anywhere on Windows.
3. Double-click `NeonRift.exe`.
4. Enter the server address supplied by the host, then connect.

Players do not need Python, Pygame, uv, pip, or VS Code. For a local game, the server address is `127.0.0.1:8765`.

Controls: `WASD` or arrow keys move, `Space` fires, `Esc` pauses the client, and `Enter` starts or restarts. The online HUD shows survival time, score, health, weapon level, alive players, and the live leaderboard.

## For Developers

Create the environment and install the pinned dependencies:

```powershell
uv venv
uv pip install -r requirements.txt
```

Start the authoritative server:

```powershell
uv run python server.py
```

Start one or more source clients in separate terminals:

```powershell
uv run python test.py
```

The client defaults to `127.0.0.1:8765`. Set `NEON_RIFT_SERVER`, or type another address in the online lobby. For example:

```powershell
$env:NEON_RIFT_SERVER = "192.168.1.20:8765"
uv run python test.py
```

### Server Configuration

Configuration is read from environment variables:

- `NEON_RIFT_HOST`: bind address, default `0.0.0.0`
- `NEON_RIFT_PORT`: port, default `8765`
- `NEON_RIFT_MAX_PLAYERS`: lobby capacity, default `8`
- `NEON_RIFT_DIFFICULTY`: spawn/speed multiplier, default `1.0`
- `NEON_RIFT_TICK_RATE`: server update rate, default `30`

Example:

```powershell
$env:NEON_RIFT_PORT = "9000"
$env:NEON_RIFT_MAX_PLAYERS = "4"
$env:NEON_RIFT_DIFFICULTY = "1.25"
uv run python server.py
```

For Internet play, run `server.py` or `NeonRiftServer.exe` on a Windows or Linux VPS, allow the configured TCP port through the VPS firewall, and give players the VPS public IP or DNS name plus port. WebSocket traffic is designed for direct Internet connections; production deployments should put it behind a TLS reverse proxy and use a `wss://` address.

### Build Windows Executables

```powershell
.\build.bat
```

The script builds both windowed client and console server executables. The client is `release/NeonRift.exe`; the server administrator executable is `server-release/NeonRiftServer.exe`. A player ZIP should contain only `NeonRift.exe` and `README.txt`. Keep the server executable in the separate `server-release/` host package.

### Project Structure

- `test.py`: packaged client entry point and preserved gameplay/rendering implementation.
- `space_game.py`: original source game implementation.
- `client/network.py`: threaded WebSocket client transport.
- `server.py`: authoritative lobby, simulation, combat, pickup, death, and leaderboard server.
- `build.bat`: builds the client and server with PyInstaller.
- `requirements.txt`: pygame, PyInstaller, and WebSocket dependencies.

The server validates movement bounds, fire cooldowns, enemy damage, player damage, pickup collection, health limits, weapon limits, score, deaths, and leaderboard state. Invalid JSON is ignored, full servers return a friendly error, and disconnects remove players from the session.