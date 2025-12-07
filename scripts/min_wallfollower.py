#!/usr/bin/env python3

import requests

BASE = "http://127.0.0.1:8000"
MOUSE = "jerry"

def get_walls():
    return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()

def move(direction):
    return requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()

def main():
    requests.post(f"{BASE}/mouse/{MOUSE}/reset")
    while True:
        walls = get_walls()

        for direction in ["left", "forward", "right", "back"]:
            if not walls[direction]:
                result = move(direction)

                if result["goal_reached"]:
                    print(f"Cheese found: {result['flag']}")
                    return
                break

if __name__ == "__main__":
    main()
