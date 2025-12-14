#!/usr/bin/env python3
"""Optimal maze solver using precomputed shortest path."""

from collections import deque
from math import ceil

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

BASE = "http://127.0.0.1:80"
MOUSE = "optimal"
console = Console()
session = requests.Session()

# Direction deltas
DELTA = {"north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0)}
OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def get_full_maze():
    """Fetch complete maze data including all walls."""
    return session.get(f"{BASE}/maze/full").json()


def move(direction):
    """Send move command to API."""
    return session.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()


def parse_maze(data):
    """Parse maze data into a usable format."""
    size = data["size"]
    goal_cells = {tuple(g) for g in data["goal_cells"]}

    # Parse cells: "x,y" -> walls dict
    walls = {}
    for key, cell in data["cells"].items():
        x, y = map(int, key.split(","))
        walls[(x, y)] = cell

    return size, goal_cells, walls


def find_shortest_path(size, goal_cells, walls):
    """Use BFS to find shortest path from (0,0) to any goal cell."""
    start = (0, 0)
    queue = deque([(start, [start])])
    visited = {start}

    while queue:
        (x, y), path = queue.popleft()

        if (x, y) in goal_cells:
            return path

        cell_walls = walls.get((x, y), {})

        for direction, (dx, dy) in DELTA.items():
            # Check if wall blocks this direction
            if cell_walls.get(direction, True):
                continue

            nx, ny = x + dx, y + dy
            if 0 <= nx < size and 0 <= ny < size and (nx, ny) not in visited:
                visited.add((nx, ny))
                queue.append(((nx, ny), path + [(nx, ny)]))

    return None  # No path found


def path_to_directions(path):
    """Convert path coordinates to cardinal directions."""
    directions = []
    for i in range(len(path) - 1):
        x1, y1 = path[i]
        x2, y2 = path[i + 1]
        dx, dy = x2 - x1, y2 - y1

        for direction, (ddx, ddy) in DELTA.items():
            if dx == ddx and dy == ddy:
                directions.append(direction)
                break

    return directions


def cardinal_to_relative(cardinal, facing):
    """Convert cardinal direction to relative direction based on current facing."""
    if cardinal == facing:
        return "forward"
    if cardinal == OPPOSITE[facing]:
        return "back"

    # Left/right depends on facing
    left_map = {"north": "west", "west": "south", "south": "east", "east": "north"}
    if cardinal == left_map[facing]:
        return "left"
    return "right"


def calculate_dimensions(maze_size: int) -> tuple[int, float]:
    """Calculate output dimensions to fill terminal width as a square."""
    width, _ = console.size
    available_width = width - 4

    # Use float for precise scaling to fill the width
    pixels_per_cell = max(1.0, (available_width * 2) / maze_size)

    return available_width, pixels_per_cell


def render_map(size, visited_cells, pos, goal_cells, optimal_path, pixels_per_cell):
    """Render the map with braille dots showing visited cells and optimal path."""
    BRAILLE_BASE = 0x2800
    DOT_BITS = [(0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80)]

    optimal_set = set(optimal_path)
    vsize = size * pixels_per_cell
    char_rows = ceil(vsize / 4)
    char_cols = ceil(vsize / 2)

    lines = []
    for char_y in range(char_rows - 1, -1, -1):
        row = ""
        for char_x in range(char_cols):
            path_bits = 0
            optimal_bits = 0
            pos_bit = 0
            has_goal = False

            for dot_row in range(4):
                vy = char_y * 4 + (3 - dot_row)
                for dot_col in range(2):
                    vx = char_x * 2 + dot_col
                    dot_bit = DOT_BITS[dot_row][dot_col]

                    # Float division for precise mapping
                    mx = int(vx / pixels_per_cell)
                    my = int(vy / pixels_per_cell)

                    if mx >= size or my >= size:
                        continue

                    if (mx, my) == pos and pos_bit == 0:
                        pos_bit = dot_bit
                    elif (mx, my) in visited_cells:
                        path_bits |= dot_bit
                    elif (mx, my) in optimal_set:
                        optimal_bits |= dot_bit

                    if (mx, my) in goal_cells:
                        has_goal = True

            if pos_bit:
                char = chr(BRAILLE_BASE + (path_bits | pos_bit))
                row += f"[bold cyan]{char}[/bold cyan]"
            elif path_bits:
                char = chr(BRAILLE_BASE + path_bits)
                if has_goal:
                    row += f"[bold green]{char}[/bold green]"
                else:
                    row += f"[yellow]{char}[/yellow]"
            elif optimal_bits:
                # Show remaining optimal path in dim
                char = chr(BRAILLE_BASE + optimal_bits)
                row += f"[dim magenta]{char}[/dim magenta]"
            elif has_goal:
                row += "[dim green]·[/dim green]"
            else:
                row += " "
        lines.append(row)

    return "\n".join(lines)


def solve():
    """Fetch maze, compute optimal path, and execute it."""
    session.post(f"{BASE}/mouse/{MOUSE}/reset")

    console.print("[bold]Fetching maze data...[/bold]")
    maze_data = get_full_maze()
    size, goal_cells, walls = parse_maze(maze_data)

    console.print("[bold]Computing optimal path...[/bold]")
    optimal_path = find_shortest_path(size, goal_cells, walls)

    if not optimal_path:
        console.print("[bold red]No path found![/bold red]")
        return

    console.print(f"[bold green]Found path with {len(optimal_path) - 1} moves[/bold green]")

    # Convert to directions
    cardinal_directions = path_to_directions(optimal_path)

    # Calculate display dimensions
    _, pixels_per_cell = calculate_dimensions(size)

    # Execute path with visualization
    x, y = 0, 0
    facing = "north"
    steps = 0
    visited_cells = {(0, 0)}

    with Live(console=console, refresh_per_second=15) as live:
        for cardinal in cardinal_directions:
            # Convert to relative direction
            relative = cardinal_to_relative(cardinal, facing)

            # Move
            result = move(relative)
            steps += 1

            # Update position and facing
            dx, dy = DELTA[cardinal]
            x, y = x + dx, y + dy
            facing = cardinal
            visited_cells.add((x, y))

            # Render
            map_text = render_map(size, visited_cells, (x, y), goal_cells, optimal_path, pixels_per_cell)
            panel = Panel(
                Text.from_markup(map_text),
                title=f"[bold]Step {steps}/{len(cardinal_directions)}[/bold]",
                subtitle=f"[dim]Position: ({x}, {y}) | Optimal path length: {len(optimal_path) - 1}[/dim]",
                border_style="green",
            )
            live.update(panel)

            if result["goal_reached"]:
                live.stop()
                console.print(f"\n[bold green]Goal reached in {steps} optimal steps![/bold green]")
                if result.get("flag"):
                    console.print(f"[bold yellow]FLAG: {result['flag']}[/bold yellow]")
                return


@click.command()
@click.option("--host", default="127.0.0.1", help="Server host")
@click.option("--port", default=80, help="Server port")
def main(host, port):
    """Run the optimal maze solver with path visualization."""
    global BASE
    BASE = f"http://{host}:{port}"
    solve()


if __name__ == "__main__":
    main()
