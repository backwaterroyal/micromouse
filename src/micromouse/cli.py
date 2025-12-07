"""CLI commands for micromouse."""

import click
import uvicorn
from rich.console import Console

from micromouse import state

console = Console()


@click.group()
def cli():
    """Micromouse maze navigation server."""
    pass


@cli.group()
def server():
    """Server commands."""
    pass


@server.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--size", default=32, type=int, help="Size of the maze (NxN)")
@click.option("--ctf", default=None, help="CTF flag to reveal when maze is solved")
def start(host: str, port: int, size: int, ctf: str | None):
    """Start the micromouse server."""
    # Initialize maze before starting
    maze = state.init_maze(size=size)

    if ctf:
        state.set_ctf_flag(ctf)

    console.print(f"[bold green]Micromouse Server[/bold green]")
    console.print(f"  Maze size: {maze.size}x{maze.size}")
    console.print(f"  Goal: center cells {sorted(maze.goal_cells)}")
    console.print(f"  Start: (0, 0)")
    console.print()
    console.print(f"[bold]Starting server at http://{host}:{port}[/bold]")
    console.print()

    uvicorn.run("micromouse.api:app", host=host, port=port)


if __name__ == "__main__":
    cli()
