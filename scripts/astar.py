#!/usr/bin/env python3
"""A* maze solver with blind navigation.

Since the API doesn't return position (blind navigation), this solver:
1. Tracks its own position and facing direction
2. Builds an internal map of discovered walls
3. Uses A* to find paths to the goal

The goal is the center 2x2 cells of a 32x32 maze: (15,15), (15,16), (16,15), (16,16)
"""

import heapq
import requests
from rich.console import Console
from rich.live import Live
from rich.table import Table

BASE = "http://127.0.0.1:8000"
MOUSE = "astar"
MAZE_SIZE = 32
console = Console()

# Goal cells (center 2x2 of 32x32 maze)
GOAL_CELLS = {(15, 15), (15, 16), (16, 15), (16, 16)}

# Cardinal direction helpers for internal tracking
CARDINAL = ["north", "east", "south", "west"]
DELTA = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}
TURN_LEFT = {"north": "west", "west": "south", "south": "east", "east": "north"}
TURN_RIGHT = {"north": "east", "east": "south", "south": "west", "west": "north"}
TURN_BACK = {"north": "south", "south": "north", "east": "west", "west": "east"}

# Relative to cardinal conversion
REL_TO_CARD = {
    "forward": lambda f: f,
    "back": lambda f: TURN_BACK[f],
    "left": lambda f: TURN_LEFT[f],
    "right": lambda f: TURN_RIGHT[f],
}


class MazeMap:
    """Internal map of discovered maze walls."""

    def __init__(self):
        # walls[pos][direction] = True/False/None (None = unknown)
        self.walls = {}

    def get_wall(self, x, y, direction):
        """Get wall state: True (wall), False (open), None (unknown)."""
        return self.walls.get((x, y), {}).get(direction)

    def set_walls(self, x, y, facing, rel_walls):
        """Update walls at position from relative wall data."""
        if (x, y) not in self.walls:
            self.walls[(x, y)] = {}

        for rel_dir, has_wall in rel_walls.items():
            card_dir = REL_TO_CARD[rel_dir](facing)
            self.walls[(x, y)][card_dir] = has_wall

            # Also set the opposite wall in the adjacent cell
            dx, dy = DELTA[card_dir]
            nx, ny = x + dx, y + dy
            if (nx, ny) not in self.walls:
                self.walls[(nx, ny)] = {}
            self.walls[(nx, ny)][OPPOSITE[card_dir]] = has_wall

    def get_neighbors(self, x, y):
        """Get accessible neighbors (no wall blocking, or unknown)."""
        neighbors = []
        for direction in CARDINAL:
            wall = self.get_wall(x, y, direction)
            if wall is False:  # Confirmed open
                dx, dy = DELTA[direction]
                neighbors.append((x + dx, y + dy, direction))
        return neighbors

    def get_possible_neighbors(self, x, y):
        """Get neighbors that might be accessible (open or unknown)."""
        neighbors = []
        for direction in CARDINAL:
            wall = self.get_wall(x, y, direction)
            if wall is not True:  # Open or unknown
                dx, dy = DELTA[direction]
                nx, ny = x + dx, y + dy
                if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
                    neighbors.append((x + dx, y + dy, direction))
        return neighbors


class AStarSolver:
    """A* solver with internal position tracking."""

    def __init__(self):
        self.x = 0
        self.y = 0
        self.facing = "north"
        self.maze = MazeMap()
        self.steps = 0
        self.path_history = [(0, 0)]

    def get_walls(self):
        return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()

    def move(self, direction):
        return requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()

    def reset(self):
        requests.post(f"{BASE}/mouse/{MOUSE}/reset")
        self.x = 0
        self.y = 0
        self.facing = "north"
        self.path_history = [(0, 0)]

    def sense_and_update(self):
        """Sense walls and update internal map."""
        walls = self.get_walls()
        self.maze.set_walls(self.x, self.y, self.facing, walls)
        return walls

    def move_direction(self, rel_dir):
        """Move in a relative direction and update internal state."""
        result = self.move(rel_dir)
        if result["success"]:
            # Update facing
            self.facing = REL_TO_CARD[rel_dir](self.facing)
            # Update position
            dx, dy = DELTA[self.facing]
            self.x += dx
            self.y += dy
            self.path_history.append((self.x, self.y))
            self.steps += 1
        return result

    def turn_to_face(self, target_cardinal):
        """Return the relative direction to face a cardinal direction."""
        if self.facing == target_cardinal:
            return "forward"
        elif TURN_LEFT[self.facing] == target_cardinal:
            return "left"
        elif TURN_RIGHT[self.facing] == target_cardinal:
            return "right"
        else:
            return "back"

    def heuristic(self, x, y):
        """Manhattan distance to nearest goal cell."""
        return min(abs(x - gx) + abs(y - gy) for gx, gy in GOAL_CELLS)

    def astar_path(self, start, goals):
        """Find path from start to any goal cell using A*."""
        sx, sy = start
        open_set = [(self.heuristic(sx, sy), 0, sx, sy, [])]
        visited = set()

        while open_set:
            _, cost, x, y, path = heapq.heappop(open_set)

            if (x, y) in visited:
                continue
            visited.add((x, y))

            if (x, y) in goals:
                return path

            for nx, ny, direction in self.maze.get_neighbors(x, y):
                if (nx, ny) not in visited:
                    new_path = path + [(nx, ny, direction)]
                    new_cost = cost + 1
                    priority = new_cost + self.heuristic(nx, ny)
                    heapq.heappush(open_set, (priority, new_cost, nx, ny, new_path))

        return None  # No path found

    def find_nearest_unexplored(self):
        """Find path to nearest cell with unknown walls."""
        open_set = [(0, self.x, self.y, [])]
        visited = set()

        while open_set:
            cost, x, y, path = heapq.heappop(open_set)

            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Check if this cell has unexplored directions
            for direction in CARDINAL:
                wall = self.maze.get_wall(x, y, direction)
                if wall is None:
                    return path  # Found unexplored area

            for nx, ny, direction in self.maze.get_neighbors(x, y):
                if (nx, ny) not in visited:
                    new_path = path + [(nx, ny, direction)]
                    heapq.heappush(open_set, (cost + 1, nx, ny, new_path))

        return None  # Everything explored

    def follow_path(self, path, live):
        """Follow a path, returning True if goal reached."""
        for target_x, target_y, direction in path:
            # Sense current position
            self.sense_and_update()

            # Determine relative direction to move
            rel_dir = self.turn_to_face(direction)

            # Check if we can actually move (wall might block)
            walls = self.get_walls()
            if walls[rel_dir]:
                return False, False  # Path blocked

            result = self.move_direction(rel_dir)
            self.update_display(live)

            if result["goal_reached"]:
                return True, result.get("flag")

        return False, False

    def update_display(self, live):
        """Update the live display."""
        table = Table(title=f"A* Solver - Step {self.steps}")
        table.add_column("Position", style="cyan")
        table.add_column("Facing", style="green")
        table.add_column("Explored", style="yellow")
        table.add_row(
            f"({self.x}, {self.y})",
            self.facing,
            str(len(self.maze.walls))
        )
        live.update(table)

    def solve(self):
        """Main solving loop using A* with exploration."""
        self.reset()

        with Live(console=console, refresh_per_second=10) as live:
            while True:
                # Sense current position
                self.sense_and_update()
                self.update_display(live)

                # Try to find path to goal
                path = self.astar_path((self.x, self.y), GOAL_CELLS)

                if path:
                    # Found path to goal, follow it
                    goal_reached, flag = self.follow_path(path, live)
                    if goal_reached:
                        live.stop()
                        console.print(f"[bold green]Goal reached in {self.steps} steps![/bold green]")
                        console.print(f"[cyan]Explored {len(self.maze.walls)} cells[/cyan]")
                        if flag:
                            console.print(f"[bold yellow]FLAG: {flag}[/bold yellow]")
                        return
                    # Path was blocked, continue exploring
                else:
                    # No known path to goal, explore more
                    explore_path = self.find_nearest_unexplored()
                    if explore_path:
                        self.follow_path(explore_path, live)
                    else:
                        # Try moving to an adjacent unexplored cell
                        walls = self.get_walls()
                        moved = False
                        for rel_dir in ["forward", "left", "right", "back"]:
                            if not walls[rel_dir]:
                                self.move_direction(rel_dir)
                                self.update_display(live)
                                moved = True
                                break
                        if not moved:
                            live.stop()
                            console.print("[bold red]Stuck! No moves available.[/bold red]")
                            return


def main():
    solver = AStarSolver()
    solver.solve()


if __name__ == "__main__":
    main()
