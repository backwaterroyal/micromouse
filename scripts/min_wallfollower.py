#!/usr/bin/env python3

import requests

BASE = "http://127.0.0.1:80"
MOUSE = "jerry"
session = requests.Session()

def main():
    session.post(f"{BASE}/mouse/{MOUSE}/reset")
    while True:
        walls = session.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()

        for direction in ["left", "forward", "right", "back"]:
            if not walls[direction]:
                result = session.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()

                if result["goal_reached"]:
                    print(f"Cheese found: {result['flag']}")
                    return
                break

if __name__ == "__main__":
    main()
