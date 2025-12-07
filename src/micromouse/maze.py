"""Maze generation using recursive backtracker algorithm."""

import random
from dataclasses import dataclass, field


@dataclass
class Cell:
    """A cell in the maze with walls in each direction."""
    north: bool = True
    south: bool = True
    east: bool = True
    west: bool = True


@dataclass
class Maze:
    """A 2D maze grid."""
    size: int
    cells: dict[tuple[int, int], Cell] = field(default_factory=dict)
    goal_cells: set[tuple[int, int]] = field(default_factory=set)

    def __post_init__(self):
        if not self.cells:
            self._generate()

    def _generate(self):
        """Generate maze using recursive backtracker (DFS)."""
        # Initialize all cells with all walls
        for x in range(self.size):
            for y in range(self.size):
                self.cells[(x, y)] = Cell()

        # Set goal cells (center 2x2)
        center = self.size // 2
        self.goal_cells = {
            (center - 1, center - 1),
            (center - 1, center),
            (center, center - 1),
            (center, center),
        }

        # Recursive backtracker from (0, 0)
        visited = set()
        stack = [(0, 0)]
        visited.add((0, 0))

        while stack:
            x, y = stack[-1]
            neighbors = self._unvisited_neighbors(x, y, visited)

            if neighbors:
                nx, ny, direction = random.choice(neighbors)
                self._remove_wall(x, y, nx, ny, direction)
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()

    def _unvisited_neighbors(
        self, x: int, y: int, visited: set
    ) -> list[tuple[int, int, str]]:
        """Get unvisited neighboring cells."""
        neighbors = []
        directions = [
            (0, 1, "north"),
            (0, -1, "south"),
            (1, 0, "east"),
            (-1, 0, "west"),
        ]

        for dx, dy, direction in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.size and 0 <= ny < self.size:
                if (nx, ny) not in visited:
                    neighbors.append((nx, ny, direction))

        return neighbors

    def _remove_wall(self, x: int, y: int, nx: int, ny: int, direction: str):
        """Remove wall between two adjacent cells."""
        opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}

        setattr(self.cells[(x, y)], direction, False)
        setattr(self.cells[(nx, ny)], opposite[direction], False)

    def get_walls(self, x: int, y: int) -> dict[str, bool]:
        """Get walls around a cell."""
        cell = self.cells.get((x, y))
        if cell is None:
            return {"north": True, "south": True, "east": True, "west": True}
        return {
            "north": cell.north,
            "south": cell.south,
            "east": cell.east,
            "west": cell.west,
        }

    def is_goal(self, x: int, y: int) -> bool:
        """Check if position is a goal cell."""
        return (x, y) in self.goal_cells
