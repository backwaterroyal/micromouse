#!/usr/bin/env python3
"""Simple left-wall follower maze solver."""

import requests

BASE = "http://127.0.0.1:8000"
MOUSE = "solver"

# Left-wall following: try left, forward, right, back
DIRECTIONS = ["north", "east", "south", "west"]
LEFT = {"north": "west", "west": "south", "south": "east", "east": "north"}
RIGHT = {"north": "east", "east": "south", "south": "west", "west": "north"}
BACK = {"north": "south", "south": "north", "east": "west", "west": "east"}


def get_walls():
    return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()


def move(direction):
    r = requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction})
    return r.json()


def solve():
    requests.post(f"{BASE}/mouse/{MOUSE}/reset")
    facing = "north"
    steps = 0

    while True:
        walls = get_walls()

        # Left-wall follow: try left, forward, right, back
        for turn in [LEFT[facing], facing, RIGHT[facing], BACK[facing]]:
            if not walls[turn]:
                result = move(turn)
                steps += 1
                facing = turn
                print(f"Step {steps}: moved {turn} -> ({result['position']['x']}, {result['position']['y']})")

                if result["goal_reached"]:
                    print(f"Goal reached in {steps} steps!")
                    return
                break


if __name__ == "__main__":
    solve()
