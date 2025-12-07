"""Global game state management."""

from __future__ import annotations

from micromouse.maze import Maze

MAZE_SIZE = 32
START_POSITION = (0, 0)

# Global state
_maze: Maze | None = None
_mice: dict[str, tuple[int, int]] = {}


def init_maze(size: int = MAZE_SIZE) -> Maze:
    """Initialize the global maze."""
    global _maze
    _maze = Maze(size=size)
    return _maze


def get_maze() -> Maze:
    """Get the current maze, initializing if needed."""
    global _maze
    if _maze is None:
        _maze = Maze(size=MAZE_SIZE)
    return _maze


def get_mouse_position(name: str) -> tuple[int, int]:
    """Get a mouse's position, creating at start if new."""
    if name not in _mice:
        _mice[name] = START_POSITION
    return _mice[name]


def set_mouse_position(name: str, x: int, y: int):
    """Set a mouse's position."""
    _mice[name] = (x, y)


def reset_mouse(name: str):
    """Reset a mouse to the start position."""
    _mice[name] = START_POSITION


def get_all_mice() -> dict[str, tuple[int, int]]:
    """Get all mice and their positions."""
    return _mice.copy()
