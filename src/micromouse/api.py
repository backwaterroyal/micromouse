"""FastAPI routes for micromouse."""

from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel

from micromouse import state
from micromouse.state import CardinalDirection

app = FastAPI(title="Micromouse API", version="0.1.0")


class Direction(str, Enum):
    """Relative directions for mouse movement."""

    forward = "forward"
    back = "back"
    left = "left"
    right = "right"


class MoveRequest(BaseModel):
    direction: Direction


class SurroundingsResponse(BaseModel):
    """Walls around the mouse relative to its facing direction."""

    forward: bool
    back: bool
    left: bool
    right: bool


class MoveResponse(BaseModel):
    """Response from a move attempt. Position is not returned (blind navigation)."""

    success: bool
    goal_reached: bool
    flag: str | None = None


class ResetResponse(BaseModel):
    """Response from a reset. Mouse returns to start facing north."""

    message: str = "Mouse reset to starting position facing north"


# Rotation tables for converting relative to cardinal directions
TURN_LEFT = {
    CardinalDirection.north: CardinalDirection.west,
    CardinalDirection.west: CardinalDirection.south,
    CardinalDirection.south: CardinalDirection.east,
    CardinalDirection.east: CardinalDirection.north,
}

TURN_RIGHT = {
    CardinalDirection.north: CardinalDirection.east,
    CardinalDirection.east: CardinalDirection.south,
    CardinalDirection.south: CardinalDirection.west,
    CardinalDirection.west: CardinalDirection.north,
}

TURN_BACK = {
    CardinalDirection.north: CardinalDirection.south,
    CardinalDirection.south: CardinalDirection.north,
    CardinalDirection.east: CardinalDirection.west,
    CardinalDirection.west: CardinalDirection.east,
}

# Cardinal direction deltas
CARDINAL_DELTA = {
    CardinalDirection.north: (0, 1),
    CardinalDirection.south: (0, -1),
    CardinalDirection.east: (1, 0),
    CardinalDirection.west: (-1, 0),
}


def relative_to_cardinal(
    relative: Direction, facing: CardinalDirection
) -> CardinalDirection:
    """Convert a relative direction to a cardinal direction based on facing."""
    if relative == Direction.forward:
        return facing
    elif relative == Direction.back:
        return TURN_BACK[facing]
    elif relative == Direction.left:
        return TURN_LEFT[facing]
    elif relative == Direction.right:
        return TURN_RIGHT[facing]
    raise ValueError(f"Unknown direction: {relative}")


@app.get("/mouse/{name}/surroundings", response_model=SurroundingsResponse)
def get_surroundings(name: str) -> SurroundingsResponse:
    """Get the walls around the mouse relative to its facing direction."""
    x, y = state.get_mouse_position(name)
    facing = state.get_mouse_facing(name)
    maze = state.get_maze()
    walls = maze.get_walls(x, y)

    # Convert cardinal walls to relative walls
    return SurroundingsResponse(
        forward=walls[facing.value],
        back=walls[TURN_BACK[facing].value],
        left=walls[TURN_LEFT[facing].value],
        right=walls[TURN_RIGHT[facing].value],
    )


@app.post("/mouse/{name}/move", response_model=MoveResponse)
def move_mouse(name: str, request: MoveRequest) -> MoveResponse:
    """Move the mouse in a relative direction."""
    x, y = state.get_mouse_position(name)
    facing = state.get_mouse_facing(name)
    maze = state.get_maze()

    # Convert relative direction to cardinal
    cardinal_direction = relative_to_cardinal(request.direction, facing)

    walls = maze.get_walls(x, y)

    # Check if wall blocks movement - do NOT update facing on failure
    if walls[cardinal_direction.value]:
        return MoveResponse(
            success=False,
            goal_reached=maze.is_goal(x, y),
        )

    # Move the mouse and update facing to match movement direction
    dx, dy = CARDINAL_DELTA[cardinal_direction]
    new_x, new_y = x + dx, y + dy
    state.set_mouse_state(name, new_x, new_y, cardinal_direction)

    goal_reached = maze.is_goal(new_x, new_y)
    flag = state.get_ctf_flag() if goal_reached else None

    return MoveResponse(
        success=True,
        goal_reached=goal_reached,
        flag=flag,
    )


@app.post("/mouse/{name}/reset", response_model=ResetResponse)
def reset_mouse(name: str) -> ResetResponse:
    """Reset the mouse to the starting position facing north."""
    state.reset_mouse(name)
    return ResetResponse()
