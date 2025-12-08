#!/usr/bin/env python3
"""Simple A* maze solver with blind navigation."""

import heapq
import requests

BASE = "http://127.0.0.1:8000"
MOUSE = "astar"
SIZE = 32
GOAL = {(15, 15), (15, 16), (16, 15), (16, 16)}

DIRS = ["north", "east", "south", "west"]
DELTA = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}
TURN = {
    "forward": lambda f: f,
    "back": lambda f: OPPOSITE[f],
    "left": lambda f: DIRS[(DIRS.index(f) - 1) % 4],
    "right": lambda f: DIRS[(DIRS.index(f) + 1) % 4],
}

session = requests.Session()


class MazeMap:
    """Discovered maze walls. Decoupled from navigation."""

    def __init__(self, size=SIZE):
        self.size = size
        self.walls = {}  # {(x,y): {dir: bool}}

    def set_walls(self, x, y, facing, rel_walls):
        """Record walls at position from relative wall readings."""
        if (x, y) not in self.walls:
            self.walls[(x, y)] = {}
        for rel, blocked in rel_walls.items():
            card = TURN[rel](facing)
            self.walls[(x, y)][card] = blocked
            # Mirror to adjacent cell
            dx, dy = DELTA[card]
            nx, ny = x + dx, y + dy
            if (nx, ny) not in self.walls:
                self.walls[(nx, ny)] = {}
            self.walls[(nx, ny)][OPPOSITE[card]] = blocked

    def is_open(self, x, y, direction):
        """True if passage is confirmed open."""
        return self.walls.get((x, y), {}).get(direction) is False

    def neighbors(self, x, y):
        """Return confirmed open neighbors as (nx, ny, direction)."""
        for d in DIRS:
            if self.is_open(x, y, d):
                dx, dy = DELTA[d]
                yield (x + dx, y + dy, d)

    def render(self, path=None):
        """Render maze map using box-drawing characters."""
        path_set = set(path) if path else set()
        if not self.walls:
            return "No maze discovered"
        xs = [p[0] for p in self.walls]
        ys = [p[1] for p in self.walls]
        x0, x1 = min(xs), max(xs)
        y0, y1 = min(ys), max(ys)

        def wall(x, y, d):
            return self.walls.get((x, y), {}).get(d) is True

        def junction(x, y):
            """Get box char for junction at top-left corner of cell (x,y)."""
            up = wall(x, y, "west") or wall(x - 1, y, "east")
            down = wall(x, y - 1, "west") or wall(x - 1, y - 1, "east")
            left = wall(x - 1, y, "north") or wall(x - 1, y - 1, "south")
            right = wall(x, y, "north") or wall(x, y - 1, "south")
            key = (up, right, down, left)
            return {
                (1,1,1,1): "┼", (1,1,1,0): "├", (1,1,0,1): "┴", (1,0,1,1): "┤",
                (0,1,1,1): "┬", (1,1,0,0): "└", (1,0,0,1): "┘", (0,0,1,1): "┐",
                (0,1,1,0): "┌", (1,0,1,0): "│", (0,1,0,1): "─", (1,0,0,0): "╵",
                (0,1,0,0): "╶", (0,0,1,0): "╷", (0,0,0,1): "╴", (0,0,0,0): " ",
            }.get(key, " ")

        lines = []
        for y in range(y1, y0 - 1, -1):
            top = ""
            mid = ""
            for x in range(x0, x1 + 1):
                top += junction(x, y + 1)
                top += "───" if wall(x, y, "north") else "   "
                mid += "│" if wall(x, y, "west") else " "
                if (x, y) in GOAL:
                    mid += " G "
                elif (x, y) in path_set:
                    mid += " ◆ "
                else:
                    mid += "   "
            top += junction(x1 + 1, y + 1)
            mid += "│" if wall(x1, y, "east") else " "
            lines.append(top)
            lines.append(mid)
        bot = ""
        for x in range(x0, x1 + 1):
            bot += junction(x, y0)
            bot += "───" if wall(x, y0, "south") else "   "
        bot += junction(x1 + 1, y0)
        lines.append(bot)
        return "\n".join(lines)


def heuristic(x, y):
    """Manhattan distance to nearest goal."""
    return min(abs(x - gx) + abs(y - gy) for gx, gy in GOAL)


def astar(maze, start, goals):
    """A* pathfinding. Returns list of (x, y, direction) or None."""
    sx, sy = start
    heap = [(heuristic(sx, sy), 0, sx, sy, [])]
    seen = set()

    while heap:
        _, cost, x, y, path = heapq.heappop(heap)
        if (x, y) in seen:
            continue
        seen.add((x, y))
        if (x, y) in goals:
            return path
        for nx, ny, d in maze.neighbors(x, y):
            if (nx, ny) not in seen:
                new_path = path + [(nx, ny, d)]
                heapq.heappush(heap, (cost + 1 + heuristic(nx, ny), cost + 1, nx, ny, new_path))
    return None


def find_unexplored(maze, start):
    """BFS to nearest cell with unknown walls."""
    sx, sy = start
    heap = [(0, sx, sy, [])]
    seen = set()

    while heap:
        cost, x, y, path = heapq.heappop(heap)
        if (x, y) in seen:
            continue
        seen.add((x, y))
        # Has unknown walls?
        cell = maze.walls.get((x, y), {})
        if len(cell) < 4:
            return path
        for nx, ny, d in maze.neighbors(x, y):
            if (nx, ny) not in seen:
                heapq.heappush(heap, (cost + 1, nx, ny, path + [(nx, ny, d)]))
    return None


class Solver:
    """A* solver with position tracking."""

    def __init__(self):
        self.x, self.y = 0, 0
        self.facing = "north"
        self.maze = MazeMap()
        self.steps = 0
        self.path = [(0, 0)]

    def api_walls(self):
        return session.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()

    def api_move(self, direction):
        return session.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()

    def api_reset(self):
        session.post(f"{BASE}/mouse/{MOUSE}/reset")

    def sense(self):
        """Read walls and update map."""
        walls = self.api_walls()
        self.maze.set_walls(self.x, self.y, self.facing, walls)
        return walls

    def rel_dir(self, target_cardinal):
        """Get relative direction to face a cardinal direction."""
        if self.facing == target_cardinal:
            return "forward"
        if TURN["left"](self.facing) == target_cardinal:
            return "left"
        if TURN["right"](self.facing) == target_cardinal:
            return "right"
        return "back"

    def move(self, rel):
        """Move and update state."""
        result = self.api_move(rel)
        if result["success"]:
            self.facing = TURN[rel](self.facing)
            dx, dy = DELTA[self.facing]
            self.x += dx
            self.y += dy
            self.path.append((self.x, self.y))
            self.steps += 1
        return result

    def follow(self, path):
        """Follow path. Returns (goal_reached, flag)."""
        for tx, ty, d in path:
            self.sense()
            rel = self.rel_dir(d)
            walls = self.api_walls()
            if walls[rel]:
                return False, None
            result = self.move(rel)
            if result["goal_reached"]:
                return True, result.get("flag")
        return False, None

    def solve(self):
        """Main loop."""
        self.api_reset()
        print(f"Starting A* solver...")

        while True:
            self.sense()
            print(f"\r  Step {self.steps}: ({self.x},{self.y}) facing {self.facing}, {len(self.maze.walls)} cells mapped", end="")

            # Try path to goal
            path = astar(self.maze, (self.x, self.y), GOAL)
            if path:
                reached, flag = self.follow(path)
                if reached:
                    print(f"\n\nGoal reached in {self.steps} steps!")
                    if flag:
                        print(f"FLAG: {flag}")
                    print(f"\nDiscovered maze:\n{self.maze.render(self.path)}")
                    return
            else:
                # Explore
                exp = find_unexplored(self.maze, (self.x, self.y))
                if exp:
                    self.follow(exp)
                else:
                    # Try any open direction
                    walls = self.api_walls()
                    for rel in ["forward", "left", "right", "back"]:
                        if not walls[rel]:
                            self.move(rel)
                            break
                    else:
                        print("\n\nStuck!")
                        print(f"\nDiscovered maze:\n{self.maze.render(self.path)}")
                        return


if __name__ == "__main__":
    Solver().solve()
