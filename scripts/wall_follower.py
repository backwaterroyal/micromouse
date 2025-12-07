#!/usr/bin/env python3
"""Simple left-wall follower maze solver using relative directions."""

import click
import requests
from rich.console import Console
from rich.live import Live
from rich.text import Text

BASE = "http://127.0.0.1:8000"
MOUSE = "jerry"
console = Console()


def get_walls():
    return requests.get(f"{BASE}/mouse/{MOUSE}/surroundings").json()


def move(direction):
    return requests.post(f"{BASE}/mouse/{MOUSE}/move", json={"direction": direction}).json()


def solve():
    requests.post(f"{BASE}/mouse/{MOUSE}/reset")
    steps = 0

    with Live(console=console, refresh_per_second=10) as live:
        while True:
            walls = get_walls()

            # Left-wall follow: try left, forward, right, back
            for direction in ["left", "forward", "right", "back"]:
                if not walls[direction]:
                    result = move(direction)
                    steps += 1

                    text = Text()
                    text.append(f"Step {steps}: ", style="bold cyan")
                    text.append(f"moved {direction}", style="white")
                    live.update(text)

                    if result["goal_reached"]:
                        live.stop()
                        console.print(f"[bold green]Goal reached in {steps} steps![/bold green]")
                        if result.get("flag"):
                            console.print(f"[bold yellow]FLAG: {result['flag']}[/bold yellow]")
                        return
                    break


@click.command()
def main():
    """Run the left-wall follower maze solver."""
    solve()


if __name__ == "__main__":
    main()
