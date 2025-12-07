"""FastAPI routes for micromouse."""

from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel

from micromouse import state

app = FastAPI(title="Micromouse API", version="0.1.0")


class Direction(str, Enum):
    north = "north"
    south = "south"
    east = "east"
    west = "west"


class MoveRequest(BaseModel):
    direction: Direction


class Position(BaseModel):
    x: int
    y: int


class SurroundingsResponse(BaseModel):
    north: bool
    south: bool
    east: bool
    west: bool


class MoveResponse(BaseModel):
    success: bool
    position: Position
    goal_reached: bool
    flag: str | None = None


class ResetResponse(BaseModel):
    position: Position


# Direction vectors
DIRECTION_DELTA = {
    Direction.north: (0, 1),
    Direction.south: (0, -1),
    Direction.east: (1, 0),
    Direction.west: (-1, 0),
}


@app.get("/mouse/{name}/surroundings", response_model=SurroundingsResponse)
def get_surroundings(name: str) -> SurroundingsResponse:
    """Get the walls around the mouse's current position."""
    x, y = state.get_mouse_position(name)
    maze = state.get_maze()
    walls = maze.get_walls(x, y)
    return SurroundingsResponse(**walls)


@app.post("/mouse/{name}/move", response_model=MoveResponse)
def move_mouse(name: str, request: MoveRequest) -> MoveResponse:
    """Move the mouse in a direction."""
    x, y = state.get_mouse_position(name)
    maze = state.get_maze()

    walls = maze.get_walls(x, y)
    direction = request.direction

    # Check if wall blocks movement
    if walls[direction.value]:
        return MoveResponse(
            success=False,
            position=Position(x=x, y=y),
            goal_reached=maze.is_goal(x, y),
        )

    # Move the mouse
    dx, dy = DIRECTION_DELTA[direction]
    new_x, new_y = x + dx, y + dy
    state.set_mouse_position(name, new_x, new_y)

    goal_reached = maze.is_goal(new_x, new_y)
    flag = state.get_ctf_flag() if goal_reached else None

    return MoveResponse(
        success=True,
        position=Position(x=new_x, y=new_y),
        goal_reached=goal_reached,
        flag=flag,
    )


@app.post("/mouse/{name}/reset", response_model=ResetResponse)
def reset_mouse(name: str) -> ResetResponse:
    """Reset the mouse to the starting position."""
    state.reset_mouse(name)
    x, y = state.get_mouse_position(name)
    return ResetResponse(position=Position(x=x, y=y))
