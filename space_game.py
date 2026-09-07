"""Neon Rift: an asset-free 2D space shooter made with Pygame."""

import math
import random
from array import array

import pygame

WIDTH, HEIGHT, FPS = 1100, 700, 60
BG = (7, 10, 27)
WHITE, CYAN, BLUE = (240, 248, 255), (61, 230, 255), (74, 117, 255)
PINK, ORANGE, RED = (255, 77, 172), (255, 157, 66), (255, 79, 91)
GREEN, PURPLE = (86, 235, 155), (174, 91, 255)


def text(surface, value, font, color, pos, center=False):
	image = font.render(str(value), True, color)
	rect = image.get_rect(center=pos) if center else image.get_rect(topleft=pos)
	surface.blit(image, rect)
	return rect


def clamp(value, low, high):
	return max(low, min(high, value))


class Audio:
	def __init__(self):
		self.sounds = {}
		try:
			pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
			for name, frequency, duration in (("shoot", 660, .07), ("hit", 180, .12), ("explode", 75, .28), ("warning", 120, .55), ("gameover", 90, .8)):
				self.sounds[name] = self.tone(frequency, duration)
			self.music = self.tone(55, 2.4)
			self.music.set_volume(.06)
			self.music.play(-1)
			self.ambient_music = self.space_music(8)
			self.ambient_music.set_volume(.025)
			self.ambient_music.play(-1)
		except pygame.error:
			pass

	def tone(self, frequency, duration):
		rate, count = 44100, int(44100 * duration)
		samples = array("h")
		for index in range(count):
			fade = min(1.0, index / 500, (count - index) / 1800)
			samples.append(int(32767 * .25 * fade * math.sin(2 * math.pi * frequency * index / rate)))
		return pygame.mixer.Sound(buffer=samples.tobytes())

	def space_music(self, duration):
		rate, count = 44100, int(44100 * duration)
		samples = array("h")
		for index in range(count):
			time = index / rate
			fade = min(1.0, index / 900, (count - index) / 900)
			pulse = .5 + .5 * math.sin(2 * math.pi * time / 4)
			value = (
				.32 * math.sin(2 * math.pi * 55 * time)
				+ .16 * math.sin(2 * math.pi * 82.5 * time)
				+ .11 * math.sin(2 * math.pi * 110 * time + pulse)
				+ .06 * math.sin(2 * math.pi * 220 * time)
			) * (.5 + pulse * .5)
			samples.append(int(32767 * .18 * fade * value))
		return pygame.mixer.Sound(buffer=samples.tobytes())

	def play(self, name):
		if name in self.sounds:
			self.sounds[name].play()


class Star:
	def __init__(self):
		self.x, self.y = random.randrange(WIDTH), random.randrange(HEIGHT)
		self.speed = random.uniform(18, 110)
		self.size = random.choice((1, 1, 1, 2, 2, 3))
		self.brightness = random.randint(75, 210)

	def update(self, dt):
		self.y += self.speed * dt
		if self.y > HEIGHT:
			self.x, self.y = random.randrange(WIDTH), -4

	def draw(self, surface):
		color = (self.brightness // 2, self.brightness // 2, self.brightness)
		pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.size)


class Particle:
	def __init__(self, position, color, power=1):
		self.position = pygame.Vector2(position)
		self.velocity = pygame.Vector2(0, 0)
		self.velocity.from_polar((random.uniform(35, 180) * power, random.randrange(360)))
		self.life = self.max_life = random.uniform(.3, .8) * power
		self.color, self.radius = color, random.uniform(1.5, 4) * power

	def update(self, dt):
		self.position += self.velocity * dt
		self.velocity *= .93 ** (dt * 60)
		self.life -= dt

	def draw(self, surface):
		if self.life > 0:
			radius = max(1, int(self.radius * self.life / self.max_life))
			pygame.draw.circle(surface, self.color, self.position, radius)


class Explosion:
	def __init__(self, position, color=ORANGE, power=1):
		self.position = pygame.Vector2(position)
		self.particles = [Particle(position, color, power) for _ in range(int(18 * power))]
		self.color, self.life, self.ring = color, .55 * power, 8 * power

	def update(self, dt):
		self.life -= dt
		self.ring += 130 * dt
		for particle in self.particles:
			particle.update(dt)

	def draw(self, surface):
		for particle in self.particles:
			particle.draw(surface)
		if self.life > 0:
			pygame.draw.circle(surface, self.color, self.position, int(self.ring), 2)


class Bullet:
	def __init__(self, position, velocity, color, damage=1, radius=4):
		self.position, self.velocity = pygame.Vector2(position), pygame.Vector2(velocity)
		self.color, self.damage, self.radius, self.alive = color, damage, radius, True

	def update(self, dt):
		self.position += self.velocity * dt
		self.alive = -30 < self.position.y < HEIGHT + 30

	def draw(self, surface):
		direction = self.velocity.normalize()
		pygame.draw.line(surface, self.color, self.position - direction * 14, self.position, self.radius)
		pygame.draw.circle(surface, WHITE, self.position, max(1, self.radius // 2))


class PlayerBullet(Bullet):
	def __init__(self, position, velocity, color=CYAN, damage=1, radius=4):
		super().__init__(position, velocity, color, damage, radius)


class EnemyBullet(Bullet):
	def __init__(self, position, velocity, color, damage=1, radius=4):
		super().__init__(position, velocity, color, damage, radius)


class Pickup:
	SPEED = 125

	def __init__(self, kind):
		self.kind = kind
		self.position = pygame.Vector2(random.randint(35, WIDTH - 35), -30)
		self.alive = True

	def update(self, dt):
		self.position.y += self.SPEED * dt
		if self.position.y > HEIGHT + 35:
			self.alive = False

	def draw(self, surface):
		x, y = self.position
		if self.kind == "heart":
			pygame.draw.circle(surface, RED, (int(x - 8), int(y - 5)), 9)
			pygame.draw.circle(surface, RED, (int(x + 8), int(y - 5)), 9)
			pygame.draw.polygon(surface, RED, ((x - 17, y - 2), (x + 17, y - 2), (x, y + 20)))
			pygame.draw.circle(surface, (255, 170, 190), (int(x - 5), int(y - 7)), 3)
			text(surface, "+25 HP", pygame.font.Font(None, 18), WHITE, (x, y + 30), True)
		elif self.kind == "weapon":
			box = pygame.Rect(int(x - 17), int(y - 17), 34, 34)
			pygame.draw.rect(surface, (84, 40, 20), box)
			pygame.draw.rect(surface, ORANGE, box, 3)
			pygame.draw.line(surface, (255, 220, 120), box.midtop, box.midbottom, 3)
			pygame.draw.line(surface, (255, 220, 120), box.midleft, box.midright, 3)
			text(surface, "W", pygame.font.Font(None, 20), WHITE, (x, y), True)
		else:
			pygame.draw.circle(surface, (28, 28, 42), (int(x), int(y)), 15)
			pygame.draw.circle(surface, (210, 220, 235), (int(x - 5), int(y - 5)), 4)
			pygame.draw.circle(surface, (210, 220, 235), (int(x + 5), int(y - 5)), 4)
			pygame.draw.arc(surface, RED, (int(x - 8), int(y - 1), 16, 12), math.pi, math.tau, 2)
			pygame.draw.line(surface, ORANGE, (x, y - 15), (x + 5, y - 24), 3)
			pygame.draw.circle(surface, (255, 220, 120), (int(x + 6), int(y - 25)), 3)


class Player:
	def __init__(self):
		self.position, self.speed = pygame.Vector2(WIDTH / 2, HEIGHT - 82), 390
		self.health = self.max_health = 100
		self.cooldown, self.weapon_level, self.invulnerable = 0, 1, 0

	def update(self, dt, keys):
		direction = pygame.Vector2(int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(keys[pygame.K_a] or keys[pygame.K_LEFT]), int(keys[pygame.K_s] or keys[pygame.K_DOWN]) - int(keys[pygame.K_w] or keys[pygame.K_UP]))
		if direction.length_squared():
			self.position += direction.normalize() * self.speed * dt
		self.position.x = clamp(self.position.x, 32, WIDTH - 32)
		self.position.y = clamp(self.position.y, HEIGHT * .52, HEIGHT - 35)
		self.cooldown, self.invulnerable = max(0, self.cooldown - dt), max(0, self.invulnerable - dt)

	def shoot(self):
		if self.cooldown > 0:
			return []
		self.cooldown = max(.1, .22 - self.weapon_level * .025)
		spread = {
			1: (0,),
			2: (-.045, .045),
			3: (-.07, 0, .07),
			4: (-.095, -.032, .032, .095),
			5: (-.12, -.06, 0, .06, .12),
			6: (-.14, -.084, -.028, .028, .084, .14),
			7: (-.15, -.1, -.05, 0, .05, .1, .15),
			8: (-.16, -.114, -.069, -.023, .023, .069, .114, .16),
			9: (-.17, -.1275, -.085, -.0425, 0, .0425, .085, .1275, .17),
		}[self.weapon_level]
		return [PlayerBullet((self.position.x + angle * 85, self.position.y - 25), (angle * 260, -780), BLUE if angle else CYAN) for angle in spread]

	def hit(self, damage):
		if self.invulnerable > 0:
			return False
		self.health -= damage
		self.invulnerable = .8
		return True

	def draw(self, surface):
		if self.invulnerable > 0 and int(self.invulnerable * 14) % 2 == 0:
			return
		x, y = self.position
		pygame.draw.polygon(surface, (20, 45, 93), ((x, y - 34), (x - 27, y + 23), (x, y + 14), (x + 27, y + 23)))
		pygame.draw.polygon(surface, CYAN, ((x, y - 34), (x - 19, y + 20), (x, y + 11), (x + 19, y + 20)))
		pygame.draw.polygon(surface, (154, 245, 255), ((x, y - 19), (x - 7, y + 3), (x + 7, y + 3)))
		pygame.draw.circle(surface, (255, 210, 90), (x - 10, y + 25), 4)
		pygame.draw.circle(surface, (255, 210, 90), (x + 10, y + 25), 4)


class Enemy:
	TYPES = {"scout": (24, RED, 1, 100), "fighter": (31, ORANGE, 2, 170), "tank": (39, PURPLE, 4, 300)}

	def __init__(self, level):
		kind = random.choices(("scout", "fighter", "tank"), (6, 3 + level * .2, max(1, level - 3)))[0]
		self.kind = kind
		self.width, self.color, self.max_health, self.points = self.TYPES[kind]
		self.position = pygame.Vector2(random.randint(45, WIDTH - 45), -35)
		self.speed = random.uniform(75, 120) + level * 8
		self.health, self.cooldown = self.max_health + level // 4, random.uniform(1, 2.8)
		self.phase, self.alive = random.uniform(0, math.tau), True

	def update(self, dt, target, level):
		self.phase += dt * (2 + level * .05)
		self.position.y += self.speed * dt
		self.position.x += math.sin(self.phase * (.8 if self.kind == "fighter" else 1)) * (85 if self.kind == "fighter" else 45) * dt
		self.position.x = clamp(self.position.x, 25, WIDTH - 25)
		self.cooldown -= dt
		shots = []
		if self.cooldown <= 0 and self.position.y > 20:
			self.cooldown = random.uniform(1.3, 2.8) / min(2.1, 1 + level * .05)
			vector = pygame.Vector2(target) - self.position
			if vector.length_squared():
				shots.append(EnemyBullet(self.position + (0, self.width / 2), vector.normalize() * (200 + level * 7), self.color, 8 if self.kind == "tank" else 5))
		if self.position.y > HEIGHT + 40:
			self.alive = False
		return shots

	def draw(self, surface):
		x, y = self.position
		if self.kind == "scout":
			points = ((x, y + 18), (x - 25, y - 12), (x - 7, y - 9), (x, y - 22), (x + 7, y - 9), (x + 25, y - 12))
		elif self.kind == "fighter":
			points = ((x, y + 22), (x - 32, y - 12), (x - 9, y - 8), (x - 23, y - 24), (x, y - 13), (x + 23, y - 24), (x + 9, y - 8), (x + 32, y - 12))
		else:
			points = ((x - 35, y - 18), (x + 35, y - 18), (x + 27, y + 22), (x - 27, y + 22))
		pygame.draw.polygon(surface, (34, 22, 59), points)
		pygame.draw.lines(surface, self.color, True, points, 3)
		pygame.draw.circle(surface, self.color, (x, y), 10 if self.kind == "tank" else 6)
		if self.health < self.max_health:
			pygame.draw.rect(surface, (30, 20, 42), (x - 25, y - 34, 50, 4))
			pygame.draw.rect(surface, self.color, (x - 25, y - 34, 50 * self.health / self.max_health, 4))


class Boss:
	def __init__(self, level):
		self.level, self.position = level, pygame.Vector2(WIDTH / 2, -100)
		self.max_health, self.health = 90 + level * 18, 90 + level * 18
		self.speed, self.direction, self.cooldown, self.alive = 90 + level * 4, 1, 1.3, True

	def update(self, dt):
		if self.position.y < 130:
			self.position.y += 80 * dt
		self.position.x += self.direction * self.speed * dt
		if self.position.x < 170 or self.position.x > WIDTH - 170:
			self.direction *= -1
		self.cooldown -= dt
		shots = []
		if self.cooldown <= 0:
			self.cooldown = max(.25, 1.05 - self.level * .02)
			angles = (-.3, -.12, 0, .12, .3)
			if self.level >= 5:
				angles = (-.38, -.25, -.12, 0, .12, .25, .38)
			for angle in angles:
				shots.append(EnemyBullet(self.position + (0, 45), (math.sin(angle), math.cos(angle)), PINK, 12, 5))
				shots[-1].velocity *= 245 + self.level * 6
		return shots

	def draw(self, surface):
		x, y = self.position
		body = ((x - 100, y - 25), (x - 58, y - 55), (x + 58, y - 55), (x + 100, y - 25), (x + 65, y + 48), (x - 65, y + 48))
		pygame.draw.polygon(surface, (48, 18, 60), body)
		pygame.draw.lines(surface, PINK, True, body, 4)
		pygame.draw.circle(surface, (255, 140, 220), (x, y), 20)
		pygame.draw.circle(surface, (44, 10, 54), (x, y), 10)
		pygame.draw.rect(surface, (38, 15, 45), (x - 115, y - 78, 230, 8))
		pygame.draw.rect(surface, PINK, (x - 115, y - 78, 230 * max(0, self.health) / self.max_health, 8))


class Game:
	def __init__(self):
		pygame.init()
		self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
		pygame.display.set_caption("NEON RIFT")
		self.clock = pygame.time.Clock()
		self.font, self.small = pygame.font.Font(None, 26), pygame.font.Font(None, 20)
		self.title, self.heading = pygame.font.Font(None, 92), pygame.font.Font(None, 50)
		self.audio = Audio()
		self.stars = [Star() for _ in range(90)]
		self.high_score = self.load_high_score()
		self.state = "menu"
		self.reset()

	def load_high_score(self):
		try:
			with open("neon_rift_high_score.txt", "r", encoding="ascii") as file:
				return int(file.read().strip() or 0)
		except (OSError, ValueError):
			return 0

	def save_high_score(self):
		try:
			with open("neon_rift_high_score.txt", "w", encoding="ascii") as file:
				file.write(str(self.high_score))
		except OSError:
			pass

	def reset(self):
		self.player, self.bullets, self.enemies = Player(), [], []
		self.pickups = []
		self.boss, self.explosions = None, []
		self.score, self.level, self.spawn_timer, self.level_timer = 0, 1, 0, 0
		self.boss_warning, self.shake = 0, 0
		self.pickup_timer = random.uniform(5, 9)
		self.temporary_bullets = []

	def start(self):
		self.reset()
		self.state = "playing"

	def explode(self, position, color=ORANGE, power=1):
		self.explosions.append(Explosion(position, color, power))

	def update(self, dt):
		for star in self.stars:
			star.update(dt)
		for explosion in self.explosions:
			explosion.update(dt)
		self.explosions = [e for e in self.explosions if e.life > 0 or any(p.life > 0 for p in e.particles)]
		if self.state != "playing":
			return
		keys = pygame.key.get_pressed()
		self.player.update(dt, keys)
		self.temporary_bullets = [remaining - dt for remaining in self.temporary_bullets if remaining - dt > 0]
		self.player.weapon_level = 1 + len(self.temporary_bullets)
		if keys[pygame.K_SPACE]:
			shots = self.player.shoot()
			if shots:
				self.audio.play("shoot")
				self.bullets.extend(shots)
		self.level_timer += dt
		if self.level_timer > 26 and self.boss is None:
			self.level += 1
			self.level_timer = 0
			if self.level % 5 == 0:
				self.boss = Boss(self.level)
				self.boss_warning = 2.7
				self.audio.play("warning")
		self.boss_warning = max(0, self.boss_warning - dt)
		if self.boss is None:
			self.spawn_timer -= dt
			if self.spawn_timer <= 0:
				late_round = max(0, self.level - 4)
				self.spawn_timer = max(.18, 1 - self.level * .075 - late_round * .06)
				spawn_count = 1 + (1 if self.level >= 5 and random.random() < .35 else 0)
				self.enemies.extend(Enemy(self.level) for _ in range(spawn_count))
		self.pickup_timer -= dt
		if self.pickup_timer <= 0:
			late_round = max(0, self.level - 4)
			self.pickup_timer = random.uniform(max(5, 7 - late_round * .25), max(8, 12 - late_round * .35))
			self.pickups.append(Pickup(random.choices(("heart", "weapon", "bomb"), (5, 4, 2 + late_round))[0]))
		for bullet in self.bullets:
			bullet.update(dt)
		for pickup in self.pickups:
			pickup.update(dt)
		for enemy in self.enemies:
			self.bullets.extend(enemy.update(dt, self.player.position, self.level))
		if self.boss:
			self.bullets.extend(self.boss.update(dt))
		self.collisions()
		self.bullets = [b for b in self.bullets if b.alive]
		self.enemies = [e for e in self.enemies if e.alive]
		self.pickups = [pickup for pickup in self.pickups if pickup.alive]
		if self.player.health <= 0:
			self.audio.play("gameover")
			self.explode(self.player.position, CYAN, 1.4)
			self.high_score = max(self.high_score, self.score)
			self.save_high_score()
			self.state = "gameover"

	def collisions(self):
		for bullet in self.bullets:
			if isinstance(bullet, EnemyBullet):
				if bullet.position.distance_to(self.player.position) < 24:
					bullet.alive = False
					if self.player.hit(bullet.damage):
						self.audio.play("hit")
						self.explode(self.player.position, RED, .45)
				continue
			if not isinstance(bullet, PlayerBullet):
				continue
			for enemy in self.enemies:
				if enemy.alive and bullet.position.distance_to(enemy.position) < enemy.width:
					bullet.alive = False
					enemy.health -= bullet.damage
					self.explode(bullet.position, enemy.color, .25)
					if enemy.health <= 0:
						enemy.alive = False
						self.score += enemy.points * self.level
						self.audio.play("explode")
						self.explode(enemy.position, enemy.color, .8)
					break
			if self.boss and self.boss.alive and bullet.alive and bullet.position.distance_to(self.boss.position) < 100:
				bullet.alive = False
				self.boss.health -= bullet.damage
				self.explode(bullet.position, PINK, .2)
				if self.boss.health <= 0:
					self.score += 500 * self.level
					self.audio.play("explode")
					self.explode(self.boss.position, PINK, 2.4)
					self.shake, self.boss = 1.3, None
					self.level += 1
					self.level_timer = 0
		for enemy in self.enemies:
			if enemy.alive and enemy.position.distance_to(self.player.position) < enemy.width + 20:
				enemy.alive = False
				if self.player.hit(18):
					self.audio.play("hit")
					self.explode(enemy.position, RED, .7)
		for pickup in self.pickups:
			if pickup.alive and pickup.position.distance_to(self.player.position) < 34:
				pickup.alive = False
				if pickup.kind == "heart":
					self.player.health = min(self.player.max_health, self.player.health + 25)
				elif pickup.kind == "weapon":
					if len(self.temporary_bullets) < 8:
						self.temporary_bullets.append(20)
						self.player.weapon_level = 1 + len(self.temporary_bullets)
				else:
					self.player.health = 0
					self.explode(self.player.position, RED, 1.4)
					return

	def background(self):
		self.screen.fill(BG)
		for star in self.stars:
			star.draw(self.screen)
		for y in range(0, HEIGHT, 70):
			pygame.draw.line(self.screen, (10, 18, 42), (0, y), (WIDTH, y))

	def hud(self):
		pygame.draw.rect(self.screen, (10, 17, 40), (0, 0, WIDTH, 64))
		pygame.draw.line(self.screen, (28, 65, 115), (0, 63), (WIDTH, 63), 2)
		text(self.screen, f"SCORE  {self.score:06d}", self.font, WHITE, (28, 18))
		text(self.screen, f"HIGH  {max(self.high_score, self.score):06d}", self.small, (130, 190, 220), (28, 42))
		text(self.screen, f"LEVEL  {self.level}", self.font, CYAN, (WIDTH // 2, 21), True)
		text(self.screen, f"WEAPON: x{self.player.weapon_level}", self.small, BLUE, (WIDTH // 2 + 100, 22), True)
		text(self.screen, "HULL", self.small, WHITE, (WIDTH - 210, 14))
		pygame.draw.rect(self.screen, (39, 25, 48), (WIDTH - 210, 37, 172, 10))
		color = GREEN if self.player.health > 45 else ORANGE if self.player.health > 20 else RED
		pygame.draw.rect(self.screen, color, (WIDTH - 210, 37, 172 * max(0, self.player.health) / 100, 10))
		text(self.screen, f"{max(0, self.player.health)}%", self.small, WHITE, (WIDTH - 31, 14), True)

	def world(self):
		for bullet in self.bullets:
			bullet.draw(self.screen)
		for enemy in self.enemies:
			enemy.draw(self.screen)
		if self.boss:
			self.boss.draw(self.screen)
		for pickup in self.pickups:
			pickup.draw(self.screen)
		self.player.draw(self.screen)
		for explosion in self.explosions:
			explosion.draw(self.screen)

	def panel(self, rect, border=CYAN):
		pygame.draw.rect(self.screen, (11, 19, 43), rect)
		pygame.draw.rect(self.screen, border, rect, 2)

	def button(self, label, rect, selected=False):
		pygame.draw.rect(self.screen, (18, 32, 66), rect)
		pygame.draw.rect(self.screen, CYAN if selected else (25, 52, 88), rect, 2)
		text(self.screen, label, self.font, CYAN if selected else WHITE, rect.center, True)

	def menu(self):
		self.background()
		text(self.screen, "NEON RIFT", self.title, CYAN, (WIDTH // 2, 170), True)
		text(self.screen, "A FAST-PACED NEON SPACE SHOOTER", self.small, (125, 170, 230), (WIDTH // 2, 235), True)
		self.panel(pygame.Rect(WIDTH // 2 - 190, 285, 380, 210), BLUE)
		self.button("START MISSION", pygame.Rect(WIDTH // 2 - 140, 320, 280, 52), True)
		self.button("QUIT", pygame.Rect(WIDTH // 2 - 140, 390, 280, 52))
		text(self.screen, f"BEST SCORE  {self.high_score:06d}", self.small, (150, 190, 220), (WIDTH // 2, 535), True)
		text(self.screen, "Created by Umidjon", self.small, (180, 220, 255), (WIDTH // 2, HEIGHT - 60), True)
		text(self.screen, "WASD / ARROWS  MOVE     SPACE  FIRE     ESC  PAUSE", self.small, (105, 135, 180), (WIDTH // 2, HEIGHT - 30), True)

	def overlay(self, title, border, restart=False):
		shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
		shade.fill((3, 7, 20, 190))
		self.screen.blit(shade, (0, 0))
		self.panel(pygame.Rect(WIDTH // 2 - 225, 190 if restart else 225, 450 if restart else 380, 330 if restart else 250), border)
		text(self.screen, title, self.heading, border, (WIDTH // 2, 245 if restart else 275), True)
		if restart:
			text(self.screen, f"SCORE  {self.score:06d}", self.font, WHITE, (WIDTH // 2, 305), True)
			text(self.screen, f"BEST   {self.high_score:06d}", self.small, (180, 205, 225), (WIDTH // 2, 335), True)
			self.button("RESTART", pygame.Rect(WIDTH // 2 - 140, 380, 280, 52), True)
			self.button("QUIT TO MENU", pygame.Rect(WIDTH // 2 - 140, 445, 280, 52))
		else:
			self.button("RESUME", pygame.Rect(WIDTH // 2 - 140, 325, 280, 52), True)
			self.button("QUIT TO MENU", pygame.Rect(WIDTH // 2 - 140, 395, 280, 52))

	def draw(self):
		if self.state == "menu":
			self.menu()
			return
		self.background()
		if self.shake > 0:
			scene = pygame.Surface((WIDTH, HEIGHT))
			old_screen = self.screen
			self.screen = scene
			self.background()
			self.world()
			self.screen = old_screen
			offset = (random.uniform(-self.shake, self.shake) * 13, random.uniform(-self.shake, self.shake) * 13)
			self.screen.blit(scene, offset)
		else:
			self.world()
		self.hud()
		self.shake = max(0, self.shake - self.clock.get_time() / 1000)
		if self.boss_warning > 0:
			text(self.screen, "WARNING: BOSS INBOUND", self.heading, PINK, (WIDTH // 2, 105), True)
		if self.state == "paused":
			self.overlay("PAUSED", CYAN)
		elif self.state == "gameover":
			self.overlay("MISSION FAILED", RED, True)

	def click(self, position):
		_, y = position
		if self.state == "menu":
			if 320 <= y <= 372:
				self.start()
			elif 390 <= y <= 442:
				pygame.event.post(pygame.event.Event(pygame.QUIT))
		elif self.state == "paused":
			if 325 <= y <= 377:
				self.state = "playing"
			elif 395 <= y <= 447:
				self.reset()
				self.state = "menu"
		elif self.state == "gameover":
			self.start() if 380 <= y <= 432 else None
			if 445 <= y <= 497:
				self.reset()
				self.state = "menu"

	def run(self):
		running = True
		while running:
			dt = min(self.clock.tick(FPS) / 1000, .05)
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					running = False
				elif event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						self.state = "paused" if self.state == "playing" else "playing" if self.state == "paused" else self.state
					elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and self.state == "menu":
						self.start()
					elif event.key == pygame.K_RETURN and self.state == "gameover":
						self.start()
				elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
					self.click(event.pos)
			self.update(dt)
			self.draw()
			pygame.display.flip()
		pygame.quit()


if __name__ == "__main__":
	Game().run()
