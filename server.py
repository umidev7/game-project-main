"""Authoritative WebSocket server for Neon Rift online survival."""

import asyncio
import json
import math
import os
import random
import time
from dataclasses import dataclass, field

import websockets

WIDTH, HEIGHT = 1100, 700
MAX_HEALTH = 100
MAX_WEAPON_LEVEL = 4


@dataclass
class ServerConfig:
	host: str = os.getenv("NEON_RIFT_HOST", "0.0.0.0")
	port: int = int(os.getenv("NEON_RIFT_PORT", "8765"))
	max_players: int = int(os.getenv("NEON_RIFT_MAX_PLAYERS", "8"))
	difficulty: float = float(os.getenv("NEON_RIFT_DIFFICULTY", "1.0"))
	tick_rate: int = int(os.getenv("NEON_RIFT_TICK_RATE", "30"))


@dataclass
class PlayerState:
	player_id: str
	name: str
	x: float = WIDTH / 2
	y: float = HEIGHT - 82
	health: int = MAX_HEALTH
	weapon_level: int = 1
	score: int = 0
	alive: bool = True
	dx: float = 0
	dy: float = 0
	shooting: bool = False
	cooldown: float = 0
	death_time: float | None = None


@dataclass
class EnemyState:
	enemy_id: int
	kind: str
	x: float
	y: float
	health: int
	max_health: int
	width: int
	speed: float
	phase: float = 0
	cooldown: float = 1.5


@dataclass
class BulletState:
	bullet_id: int
	x: float
	y: float
	vx: float
	vy: float
	owner_id: str | None
	friendly: bool
	damage: int


@dataclass
class PickupState:
	pickup_id: int
	kind: str
	x: float
	y: float
	vy: float


class SurvivalGame:
	def __init__(self, config):
		self.config = config
		self.players = {}
		self.enemies = {}
		self.bullets = {}
		self.pickups = {}
		self.next_id = 1
		self.phase = "lobby"
		self.level = 1
		self.elapsed = 0.0
		self.spawn_timer = 0.0
		self.pickup_timer = 8.0
		self.boss_id = None

	def add_player(self, name):
		if len(self.players) >= self.config.max_players:
			return None
		player_id = f"p{len(self.players) + 1}"
		while player_id in self.players:
			player_id = f"p{random.randint(1000, 9999)}"
		self.players[player_id] = PlayerState(player_id, name[:16] or player_id)
		return self.players[player_id]

	def remove_player(self, player_id):
		self.players.pop(player_id, None)
		if not self.players:
			self.reset()

	def reset(self):
		self.phase = "lobby"
		self.level = 1
		self.elapsed = 0.0
		self.spawn_timer = 0.0
		self.pickup_timer = 8.0
		self.enemies.clear()
		self.bullets.clear()
		self.pickups.clear()
		self.boss_id = None
		self.boss_spawned_level = 0
		for player in self.players.values():
			player.x, player.y = WIDTH / 2, HEIGHT - 82
			player.health, player.weapon_level, player.score = MAX_HEALTH, 1, 0
			player.alive, player.death_time = True, None

	def start(self):
		if self.players:
			self.reset()
			self.phase = "playing"

	def restart(self):
		self.start()

	def _new_id(self):
		value = self.next_id
		self.next_id += 1
		return value

	def _spawn_enemy(self):
		level = self.level
		kind = random.choices(("scout", "fighter", "tank"), (6, 3 + level * .2, max(1, level - 3)))[0]
		width, max_health, points = {"scout": (24, 1, 100), "fighter": (31, 2, 170), "tank": (39, 4, 300)}[kind]
		enemy_id = self._new_id()
		self.enemies[enemy_id] = EnemyState(
			enemy_id, kind, random.randint(45, WIDTH - 45), -35,
			max_health + level // 4, max_health + level // 4,
			width, random.uniform(75, 120) + level * 8 * self.config.difficulty,
			random.uniform(0, math.tau), random.uniform(1, 2.8),
		)

	def _spawn_boss(self):
		health = 90 + self.level * 18
		boss_id = self._new_id()
		self.boss_id = boss_id
		self.enemies[boss_id] = EnemyState(boss_id, "boss", WIDTH / 2, -100, health, health, 100, 90 + self.level * 4, 0, 1.3)

	def _spawn_pickup(self):
		kind = "heart" if random.random() < .55 else "weapon"
		pickup_id = self._new_id()
		self.pickups[pickup_id] = PickupState(pickup_id, kind, random.randint(35, WIDTH - 35), -25, random.uniform(70, 115))

	def _shoot(self, player):
		if not player.alive or player.cooldown > 0:
			return
		player.cooldown = max(.1, .22 - player.weapon_level * .025)
		count = min(MAX_WEAPON_LEVEL, player.weapon_level)
		spread = 55
		for index in range(count):
			offset = (index - (count - 1) / 2) * spread
			bullet_id = self._new_id()
			self.bullets[bullet_id] = BulletState(bullet_id, player.x + offset / 12, player.y - 25, offset, -780, player.player_id, True, max(1, player.weapon_level // 2))

	def _damage_player(self, player, damage):
		if not player.alive:
			return
		player.health -= damage
		if player.health <= 0:
			player.health = 0
			player.alive = False
			player.death_time = self.elapsed

	def update(self, dt):
		if self.phase != "playing":
			return
		self.elapsed += dt
		self.level = 1 + int(self.elapsed // 26)
		for player in self.players.values():
			if not player.alive:
				continue
			length = math.hypot(player.dx, player.dy) or 1
			player.x = max(32, min(WIDTH - 32, player.x + player.dx / length * 390 * dt))
			player.y = max(HEIGHT * .52, min(HEIGHT - 35, player.y + player.dy / length * 390 * dt))
			player.cooldown = max(0, player.cooldown - dt)
			if player.shooting:
				self._shoot(player)

		self.spawn_timer -= dt
		if self.boss_id is None and self.spawn_timer <= 0:
			self.spawn_timer = max(.24, (1 - self.level * .075) / self.config.difficulty)
			self._spawn_enemy()
		if self.boss_id is None and self.level % 5 == 0 and self.elapsed > 0 and self.boss_spawned_level != self.level and not any(enemy.kind == "boss" for enemy in self.enemies.values()):
			self._spawn_boss()
			self.boss_spawned_level = self.level
		self.pickup_timer -= dt
		if self.pickup_timer <= 0:
			self.pickup_timer = random.uniform(9, 16)
			self._spawn_pickup()

		for enemy in list(self.enemies.values()):
			if enemy.kind == "boss":
				enemy.y = min(130, enemy.y + 80 * dt)
				enemy.x += (1 if int(self.elapsed * .5) % 2 == 0 else -1) * enemy.speed * dt
				enemy.x = max(170, min(WIDTH - 170, enemy.x))
			else:
				enemy.phase += dt * (2 + self.level * .05)
				enemy.y += enemy.speed * dt
				enemy.x += math.sin(enemy.phase * (.8 if enemy.kind == "fighter" else 1)) * (85 if enemy.kind == "fighter" else 45) * dt
				enemy.x = max(25, min(WIDTH - 25, enemy.x))
			if enemy.y > HEIGHT + 40:
				del self.enemies[enemy.enemy_id]
				continue
			enemy.cooldown -= dt
			if enemy.cooldown <= 0 and enemy.y > 20:
				enemy.cooldown = (max(.35, 1.05 - self.level * .015) if enemy.kind == "boss" else random.uniform(1.3, 2.8)) / min(2.1, 1 + self.level * .05)
				targets = [p for p in self.players.values() if p.alive]
				if targets:
					target = min(targets, key=lambda p: (p.x - enemy.x) ** 2 + (p.y - enemy.y) ** 2)
					if enemy.kind == "boss":
						for angle in (-.3, -.12, 0, .12, .3):
							self._enemy_bullet(enemy, target, angle)
					else:
						self._enemy_bullet(enemy, target, 0)

		for bullet_id, bullet in list(self.bullets.items()):
			bullet.x += bullet.vx * dt
			bullet.y += bullet.vy * dt
			if bullet.y < -30 or bullet.y > HEIGHT + 30 or bullet.x < -40 or bullet.x > WIDTH + 40:
				del self.bullets[bullet_id]
				continue
			if bullet.friendly:
				for enemy in list(self.enemies.values()):
					if (bullet.x - enemy.x) ** 2 + (bullet.y - enemy.y) ** 2 < enemy.width ** 2:
						enemy.health -= bullet.damage
						del self.bullets[bullet_id]
						if enemy.health <= 0:
							owner = self.players.get(bullet.owner_id)
							if owner:
								owner.score += (500 if enemy.kind == "boss" else {"scout": 100, "fighter": 170, "tank": 300}[enemy.kind]) * self.level
								if enemy.kind == "boss":
									owner.weapon_level = min(MAX_WEAPON_LEVEL, owner.weapon_level + 1)
							if enemy.enemy_id == self.boss_id:
								self.boss_id = None
							del self.enemies[enemy.enemy_id]
						break
			else:
				for player in self.players.values():
					if player.alive and (bullet.x - player.x) ** 2 + (bullet.y - player.y) ** 2 < 24 ** 2:
						self._damage_player(player, bullet.damage)
						del self.bullets[bullet_id]
						break

		for enemy in list(self.enemies.values()):
			for player in self.players.values():
				if player.alive and (enemy.x - player.x) ** 2 + (enemy.y - player.y) ** 2 < (enemy.width + 20) ** 2:
					self._damage_player(player, 18)
					if enemy.enemy_id in self.enemies:
						del self.enemies[enemy.enemy_id]
					break
		for pickup_id, pickup in list(self.pickups.items()):
			pickup.y += pickup.vy * dt
			if pickup.y > HEIGHT + 30:
				del self.pickups[pickup_id]
				continue
			for player in self.players.values():
				if player.alive and (pickup.x - player.x) ** 2 + (pickup.y - player.y) ** 2 < 34 ** 2:
					if pickup.kind == "heart":
						player.health = min(MAX_HEALTH, player.health + 25)
					else:
						player.weapon_level = min(MAX_WEAPON_LEVEL, player.weapon_level + 1)
					del self.pickups[pickup_id]
					break

		if self.players and all(not player.alive for player in self.players.values()):
			self.phase = "ended"

	def _enemy_bullet(self, enemy, target, angle):
		vector_x, vector_y = target.x - enemy.x, target.y - enemy.y
		length = math.hypot(vector_x, vector_y) or 1
		cosine, sine = math.cos(angle), math.sin(angle)
		dx, dy = vector_x / length, vector_y / length
		vx, vy = dx * cosine - dy * sine, dx * sine + dy * cosine
		speed = (245 + self.level * 6) if enemy.kind == "boss" else (200 + self.level * 7)
		bullet_id = self._new_id()
		self.bullets[bullet_id] = BulletState(bullet_id, enemy.x, enemy.y + enemy.width / 2, vx * speed, vy * speed, None, False, 12 if enemy.kind == "boss" else 5)

	def snapshot(self):
		leaderboard = sorted(({
			"id": p.player_id, "name": p.name, "time": round(p.death_time if p.death_time is not None else self.elapsed, 1), "score": p.score, "alive": p.alive,
		} for p in self.players.values()), key=lambda item: (-item["time"], -item["score"]))
		return {
			"type": "state", "phase": self.phase, "time": round(self.elapsed, 1), "level": self.level, "max_players": self.config.max_players,
			"players": [{"id": p.player_id, "name": p.name, "x": round(p.x, 1), "y": round(p.y, 1), "health": p.health, "weapon": p.weapon_level, "score": p.score, "alive": p.alive} for p in self.players.values()],
			"enemies": [{"id": e.enemy_id, "kind": e.kind, "x": round(e.x, 1), "y": round(e.y, 1), "health": e.health, "max_health": e.max_health, "width": e.width} for e in self.enemies.values()],
			"bullets": [{"id": b.bullet_id, "x": round(b.x, 1), "y": round(b.y, 1), "friendly": b.friendly, "owner": b.owner_id, "damage": b.damage} for b in self.bullets.values()],
			"pickups": [{"id": p.pickup_id, "kind": p.kind, "x": round(p.x, 1), "y": round(p.y, 1)} for p in self.pickups.values()],
			"leaderboard": leaderboard,
		}


class NeonRiftServer:
	def __init__(self, config=None):
		self.config = config or ServerConfig()
		self.game = SurvivalGame(self.config)
		self.connections = {}

	async def handler(self, websocket):
		player = None
		try:
			async for raw_message in websocket:
				try:
					message = json.loads(raw_message)
				except (json.JSONDecodeError, TypeError):
					continue
				if not isinstance(message, dict):
					continue
				if message.get("type") == "hello" and player is None:
					player = self.game.add_player(str(message.get("name", "Player")))
					if player is None:
						await websocket.send(json.dumps({"type": "error", "message": "Server is full."}))
						return
					self.connections[websocket] = player.player_id
					await websocket.send(json.dumps({"type": "welcome", "player_id": player.player_id, "max_players": self.config.max_players}))
				elif player is not None:
					self._message(player, message)
		except websockets.ConnectionClosed:
			pass
		finally:
			if player is not None:
				self.connections.pop(websocket, None)
				self.game.remove_player(player.player_id)

	def _message(self, player, message):
		message_type = message.get("type")
		if message_type == "input":
			try:
				player.dx = max(-1, min(1, float(message.get("dx", 0))))
				player.dy = max(-1, min(1, float(message.get("dy", 0))))
			except (TypeError, ValueError):
				player.dx, player.dy = 0, 0
		elif message_type == "shoot":
			player.shooting = bool(message.get("down", True))
		elif message_type == "start":
			self.game.start()
		elif message_type == "restart":
			self.game.restart()

	async def broadcast(self):
		if not self.connections:
			return
		payload = json.dumps(self.game.snapshot())
		results = await asyncio.gather(*(connection.send(payload) for connection in self.connections), return_exceptions=True)
		for connection, result in zip(list(self.connections), results):
			if isinstance(result, Exception):
				self.connections.pop(connection, None)

	async def run(self):
		server = await websockets.serve(self.handler, self.config.host, self.config.port, max_size=1_000_000)
		print(f"Neon Rift server listening on {self.config.host}:{self.config.port} (max players: {self.config.max_players})")
		last = time.monotonic()
		try:
			while True:
				now = time.monotonic()
				dt = min(.1, now - last)
				last = now
				self.game.update(dt)
				await self.broadcast()
				await asyncio.sleep(1 / max(1, self.config.tick_rate))
		finally:
			server.close()
			await server.wait_closed()


def main():
	try:
		asyncio.run(NeonRiftServer().run())
	except KeyboardInterrupt:
		print("Server stopped.")


if __name__ == "__main__":
	main()
