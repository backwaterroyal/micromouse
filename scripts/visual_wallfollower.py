#!/usr/bin/env python3
"""Left-wall follower with path visualization."""

from math import ceil

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

BASE = "http://127.0.0.1:80"
MOUSE = "pathfinder"
console = Console()
session = requests.Session()

# Direction deltas and turning
DELTA = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}
TURN = {
    "forward": lambda f: f,
    "back": lambda f: OPPOSITE[f],
    "left": lambda f: {"north": "west", "west": "south", "south": "east", "east": "north"}[f],
    "right": lambda f: {"north": "east", "east": "south", "south": "west", "west": "north"}[f],
}


def get_metadata():
    return session.get(f"{BASE}/maze/metadata").json()


def get_walls():
    return session.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()


def move(direction):
    return session.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()


def calculate_dimensions(maze_size: int) -> tuple[int, float]:
    """Calculate output dimensions to fill terminal width as a square.

    Returns (char_cols, pixels_per_cell) where pixels_per_cell is a float for precise scaling.
    """
    width, _ = console.size
    available_width = width - 4  # panel borders

    # We want char_cols = available_width
    # char_cols = maze_size * pixels_per_cell / 2
    # So: pixels_per_cell = available_width * 2 / maze_size
    pixels_per_cell = max(1.0, (available_width * 2) / maze_size)

    return available_width, pixels_per_cell


def render_map(size, path_connections, pos, goal_cells, pixels_per_cell):
    """Render the map with braille dots, upscaled to fill terminal."""
    # Braille dot bits: each char is 2 wide x 4 tall
    BRAILLE_BASE = 0x2800
    DOT_BITS = [(0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80)]

    # Virtual pixel grid (upscaled maze) - use float for precise scaling
    vsize = size * pixels_per_cell
    char_rows = ceil(vsize / 4)
    char_cols = ceil(vsize / 2)

    lines = []
    for char_y in range(char_rows - 1, -1, -1):
        row = ""
        for char_x in range(char_cols):
            path_bits = 0
            pos_bit = 0
            has_goal = False

            # Check each dot position in this braille char
            for dot_row in range(4):
                vy = char_y * 4 + (3 - dot_row)  # virtual y (flip for top-down)
                for dot_col in range(2):
                    vx = char_x * 2 + dot_col  # virtual x
                    dot_bit = DOT_BITS[dot_row][dot_col]

                    # Map virtual pixel back to maze cell (float division)
                    mx = int(vx / pixels_per_cell)
                    my = int(vy / pixels_per_cell)

                    if mx >= size or my >= size:
                        continue

                    if (mx, my) == pos and pos_bit == 0:
                        pos_bit = dot_bit
                    elif (mx, my) in path_connections:
                        path_bits |= dot_bit

                    if (mx, my) in goal_cells:
                        has_goal = True

            # Combine path and mouse position
            if pos_bit:
                char = chr(BRAILLE_BASE + (path_bits | pos_bit))
                row += f"[bold cyan]{char}[/bold cyan]"
            elif path_bits:
                char = chr(BRAILLE_BASE + path_bits)
                if has_goal:
                    row += f"[bold green]{char}[/bold green]"
                else:
                    row += f"[yellow]{char}[/yellow]"
            elif has_goal:
                row += "[dim green]·[/dim green]"
            else:
                row += " "
        lines.append(row)

    return "\n".join(lines)


def solve():
    session.post(f"{BASE}/mouse/{MOUSE}/reset")

    meta = get_metadata()
    size = meta["size"]
    goal_cells = {tuple(g) for g in meta["goal_cells"]}

    # Calculate dimensions to fill terminal
    char_cols, pixels_per_cell = calculate_dimensions(size)

    # Track position and facing (start at 0,0 facing north)
    x, y = 0, 0
    facing = "north"
    steps = 0

    # Track connections at each cell for drawing lines
    path_connections: dict[tuple[int, int], set[str]] = {}

    with Live(console=console, refresh_per_second=15) as live:
        while True:
            walls = get_walls()

            for direction in ["left", "forward", "right", "back"]:
                if not walls[direction]:
                    # Calculate new facing and movement
                    new_facing = TURN[direction](facing)
                    dx, dy = DELTA[new_facing]

                    # Record exit direction from current cell
                    if (x, y) not in path_connections:
                        path_connections[(x, y)] = set()
                    path_connections[(x, y)].add(new_facing)

                    # Move
                    result = move(direction)
                    steps += 1
                    x, y = x + dx, y + dy
                    facing = new_facing

                    # Record entry direction to new cell
                    if (x, y) not in path_connections:
                        path_connections[(x, y)] = set()
                    path_connections[(x, y)].add(OPPOSITE[new_facing])

                    # Render
                    map_text = render_map(size, path_connections, (x, y), goal_cells, pixels_per_cell)
                    panel = Panel(
                        Text.from_markup(map_text),
                        title=f"[bold]Step {steps}[/bold]",
                        subtitle=f"[dim]Position: ({x}, {y}) Facing: {facing}[/dim]",
                        border_style="blue",
                    )
                    live.update(panel)

                    if result["goal_reached"]:
                        live.stop()
                        console.print(f"\n[bold green]Goal reached in {steps} steps![/bold green]")
                        if result.get("flag"):
                            console.print(f"[bold yellow]FLAG: {result['flag']}[/bold yellow]")
                        return
                    break


@click.command()
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--port", default=80, help="Server port")
def main(host, port):
    """Run the left-wall follower with path visualization."""
    global BASE
    BASE = f"http://{host}:{port}"
    solve()


if __name__ == "__main__":
    main()
