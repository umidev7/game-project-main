"""Create the original Neon Rift instrumental soundtrack as a seamless WAV loop."""

import math
import random
import struct
import wave
from pathlib import Path


RATE = 44100
DURATION = 144
BAR = 4.0
TAU = math.tau
NOTES = (55.0, 65.41, 73.42, 82.41, 98.0, 110.0)


def envelope(position, length, attack=0.02, release=0.08):
	return min(1.0, position / attack, (length - position) / release)


def render_sample(time, noise):
	cycle = time % (BAR * 2)
	beat = time % 1.0
	value = 0.0

	pad = 0.5 + 0.5 * math.sin(TAU * time / 16.0)
	for frequency in (55.0, 82.41, 110.0):
		value += math.sin(TAU * frequency * time + pad * 0.8) * (0.018 if frequency != 55.0 else 0.035)

	if beat < 0.22:
		bass_note = NOTES[int(time // BAR) % len(NOTES)]
		value += math.sin(TAU * bass_note * time) * envelope(beat, 0.22, 0.01, 0.12) * 0.13

	step = int(time * 2) % 8
	arp_note = NOTES[(step + int(cycle // BAR)) % len(NOTES)] * 2
	arp_position = (time * 2) % 1.0
	value += math.sin(TAU * arp_note * time) * envelope(arp_position, 0.5, 0.025, 0.16) * 0.045

	if beat < 0.16:
		value += math.sin(TAU * (72.0 - beat * 260.0) * beat) * (1.0 - beat / 0.16) * 0.12
	if 0.5 < beat < 0.62:
		value += noise * (1.0 - (beat - 0.5) / 0.12) * 0.035

	return max(-1.0, min(1.0, value))


def main():
	output = Path(__file__).resolve().parents[1] / "assets" / "neon_rift_soundtrack.wav"
	output.parent.mkdir(parents=True, exist_ok=True)
	rng = random.Random(1977)
	frames = bytearray()
	for index in range(RATE * DURATION):
		time = index / RATE
		frames.extend(struct.pack("<h", int(render_sample(time, rng.uniform(-1.0, 1.0)) * 32767)))
	with wave.open(str(output), "wb") as soundtrack:
		soundtrack.setnchannels(1)
		soundtrack.setsampwidth(2)
		soundtrack.setframerate(RATE)
		soundtrack.writeframes(frames)
	print(output)


if __name__ == "__main__":
	main()