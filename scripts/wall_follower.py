#!/usr/bin/env python3
"""Simple left-wall follower maze solver."""

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.text import Text

BASE = "http://127.0.0.1:8000"
MOUSE = "jerry"
console = Console()

# Left-wall following: try left, forward, right, back
DIRECTIONS = ["north", "east", "south", "west"]
LEFT = {"north": "west", "west": "south", "south": "east", "east": "north"}
RIGHT = {"north": "east", "east": "south", "south": "west", "west": "north"}
BACK = {"north": "south", "south": "north", "east": "west", "west": "east"}


def get_walls():
    return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()


def move(direction):
    return requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()


def solve():
    requests.post(f"{BASE}/mouse/{MOUSE}/reset")
    facing = "north"
    steps = 0

    with Live(console=console, refresh_per_second=10) as live:
        while True:
            walls = get_walls()

            # Left-wall follow: try left, forward, right, back
            for turn in [LEFT[facing], facing, RIGHT[facing], BACK[facing]]:
                if not walls[turn]:
                    result = move(turn)
                    steps += 1
                    facing = turn

                    text = Text()
                    text.append(f"Step {steps}: ", style="bold cyan")
                    text.append(f"moved {turn} -> ", style="white")
                    text.append(f"({result['position']['x']}, {result['position']['y']})", style="green")
                    live.update(text)

                    if result["goal_reached"]:
                        live.stop()
                        console.print(f"[bold green]Goal reached in {steps} steps![/bold green]")
                        return
                    break


@click.command()
def main():
    """Run the left-wall follower maze solver."""
    solve()


if __name__ == "__main__":
    main()
