import requests

BASE = "http://127.0.0.1:8000"
MOUSE = "tom"

def get_walls():
    return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()

def move(direction):
    return requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()

def solve():
    requests.post(f"{BASE}/mouse/{MOUSE}/reset")


print(r)
