"""Threaded WebSocket transport used by the Pygame client."""

import asyncio
import json
import queue
import threading

import websockets


class NetworkClient:
	def __init__(self, address, name="Player"):
		self.address = address.strip()
		if not self.address.startswith(("ws://", "wss://")):
			self.address = "ws://" + self.address
		self.name = name[:16] or "Player"
		self.incoming = queue.Queue()
		self.outgoing = queue.Queue()
		self.connected = False
		self.closed = False
		self.error = ""
		self.player_id = None
		self.thread = threading.Thread(target=self._thread_main, daemon=True)

	def start(self):
		self.thread.start()

	def send(self, message):
		if not self.closed:
			self.outgoing.put(message)

	def poll(self):
		messages = []
		while True:
			try:
				messages.append(self.incoming.get_nowait())
			except queue.Empty:
				return messages

	def close(self):
		self.closed = True

	def _thread_main(self):
		try:
			asyncio.run(self._run())
		except Exception as error:
			self.error = str(error)
			self.incoming.put({"type": "error", "message": self.error})
		finally:
			self.connected = False

	async def _run(self):
		async with websockets.connect(self.address, open_timeout=5, close_timeout=2, max_size=1_000_000) as websocket:
			await websocket.send(json.dumps({"type": "hello", "name": self.name}))
			self.connected = True
			while not self.closed:
				try:
					while True:
						message = self.outgoing.get_nowait()
						await websocket.send(json.dumps(message))
				except queue.Empty:
					pass
				try:
					raw_message = await asyncio.wait_for(websocket.recv(), timeout=.05)
				except asyncio.TimeoutError:
					continue
				if isinstance(raw_message, str):
					try:
						message = json.loads(raw_message)
					except json.JSONDecodeError:
						continue
					if message.get("type") == "welcome":
						self.player_id = message.get("player_id")
					self.incoming.put(message)
