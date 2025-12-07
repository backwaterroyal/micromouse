"""Global game state management."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from micromouse.maze import Maze

MAZE_SIZE = 32
START_POSITION = (0, 0)


class CardinalDirection(str, Enum):
    """Cardinal directions used internally by the server."""

    north = "north"
    south = "south"
    east = "east"
    west = "west"


START_FACING = CardinalDirection.north


@dataclass
class MouseState:
    """State of a mouse including position and facing direction."""

    x: int
    y: int
    facing: CardinalDirection


# Global state
_maze: Maze | None = None
_mice: dict[str, MouseState] = {}
_ctf_flag: str | None = None


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
        _mice[name] = MouseState(x=0, y=0, facing=START_FACING)
    state = _mice[name]
    return (state.x, state.y)


def get_mouse_facing(name: str) -> CardinalDirection:
    """Get a mouse's facing direction, creating at start if new."""
    if name not in _mice:
        _mice[name] = MouseState(x=0, y=0, facing=START_FACING)
    return _mice[name].facing


def set_mouse_state(name: str, x: int, y: int, facing: CardinalDirection):
    """Set a mouse's complete state."""
    _mice[name] = MouseState(x=x, y=y, facing=facing)


def reset_mouse(name: str):
    """Reset a mouse to the start position facing north."""
    _mice[name] = MouseState(x=0, y=0, facing=START_FACING)


def get_all_mice() -> dict[str, MouseState]:
    """Get all mice and their states."""
    return _mice.copy()


def set_ctf_flag(flag: str):
    """Set the CTF flag."""
    global _ctf_flag
    _ctf_flag = flag


def get_ctf_flag() -> str | None:
    """Get the CTF flag if set."""
    return _ctf_flag
