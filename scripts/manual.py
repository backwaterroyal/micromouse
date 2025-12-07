#!/usr/bin/env python3
"""Manual control for micromouse - pass a direction to move."""

import sys
import requests

BASE = "http://127.0.0.1:8000"
MOUSE = "manual"


def get_walls():
    return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()


def move(direction):
    return requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()


def reset():
    return requests.post(f"{BASE}/mouse/{MOUSE}/reset").json()


def main():
    if len(sys.argv) < 2:
        print("Usage: python manual.py <direction>")
        print("Directions: forward, back, left, right, reset, walls")
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "reset":
        result = reset()
        print(f"Reset: {result['message']}")
        walls = get_walls()
        print(f"Walls: {walls}")
    elif cmd == "walls":
        walls = get_walls()
        print(f"Walls: {walls}")
    elif cmd in ("forward", "back", "left", "right"):
        result = move(cmd)
        print(f"Move {cmd}: success={result['success']}, goal={result['goal_reached']}")
        if result.get("flag"):
            print(f"FLAG: {result['flag']}")
        walls = get_walls()
        print(f"Walls: {walls}")
    else:
        print(f"Unknown command: {cmd}")
        print("Directions: forward, back, left, right, reset, walls")
        sys.exit(1)


if __name__ == "__main__":
    main()
