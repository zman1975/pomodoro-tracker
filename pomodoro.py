"""Main CLI application for Pomodoro Tracker."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from dateutil import parser as dateparser

from timer import run_timer
from categorizer import categorize_task, CATEGORIES
from storage import load_config, save_config, load_sessions, save_session

console = Console()


@click.group()
def cli():
    """Pomodoro Tracker - Focus timer with smart task tracking."""
    pass


@cli.command()
@click.argument("task")
@click.option("--minutes", "-m", default=None, type=int, help="Override timer length.")
@click.option(
    "--category", "-c", default=None, type=click.Choice(CATEGORIES, case_sensitive=False),
    help="Manually set category instead of using AI.",
)
def start(task: str, minutes: int | None, category: str | None):
    """Start a pomodoro session for TASK."""
    config = load_config()
    duration = minutes or config["pomodoro_minutes"]

    if category is None:
        console.print("[dim]Categorizing task...[/dim]")
        category = categorize_task(task)
    console.print(f"[bold]Task:[/bold] {task}  [bold]Category:[/bold] [cyan]{category}[/cyan]")
    console.print(f"[bold]Duration:[/bold] {duration} minutes\n")

    elapsed, completed = run_timer(task, duration)
    record = save_session(task, category, elapsed, completed)

    status = "[green]completed[/green]" if completed else "[yellow]stopped early[/yellow]"
    console.print(f"\nSession #{record['id']} {status} ({elapsed // 60}m {elapsed % 60}s)")

    if completed:
        break_len = config["short_break_minutes"]
        sessions = load_sessions()
        focus_count = sum(
            1 for s in sessions if s["completed"] and s["category"] != "break"
        )
        if focus_count % config["sessions_before_long_break"] == 0:
            break_len = config["long_break_minutes"]
            console.print(f"[bold cyan]Long break earned! ({break_len} min)[/bold cyan]")
        else:
            console.print(f"[dim]Short break: {break_len} min[/dim]")

        if click.confirm("Start break timer?", default=True):
            run_timer("Break", break_len, is_break=True)


@cli.command()
@click.option("--last", "-n", default=10, help="Number of recent sessions to show.")
def history(last: int):
    """Show recent pomodoro sessions."""
    sessions = load_sessions()
    if not sessions:
        console.print("[dim]No sessions yet. Run 'start' to begin![/dim]")
        return

    table = Table(title="Recent Sessions")
    table.add_column("#", style="dim", width=4)
    table.add_column("Task", min_width=20)
    table.add_column("Category", style="cyan")
    table.add_column("Duration")
    table.add_column("Status")
    table.add_column("Date", style="dim")

    for s in sessions[-last:]:
        m, sec = divmod(s["duration_seconds"], 60)
        status = "[green]Done[/green]" if s["completed"] else "[yellow]Stopped[/yellow]"
        dt = dateparser.parse(s["started_at"])
        date_str = dt.strftime("%b %d %H:%M") if dt else s["started_at"]
        table.add_row(str(s["id"]), s["task"], s["category"], f"{m}m {sec}s", status, date_str)

    console.print(table)


@cli.command()
def stats():
    """Show summary statistics."""
    sessions = load_sessions()
    if not sessions:
        console.print("[dim]No sessions yet.[/dim]")
        return

    total = len(sessions)
    completed = sum(1 for s in sessions if s["completed"])
    total_minutes = sum(s["duration_seconds"] for s in sessions) // 60

    category_counts: dict[str, int] = {}
    for s in sessions:
        cat = s["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    console.print(f"\n[bold]Total sessions:[/bold] {total}")
    console.print(f"[bold]Completed:[/bold] {completed}/{total}")
    console.print(f"[bold]Total focus time:[/bold] {total_minutes} minutes\n")

    table = Table(title="Sessions by Category")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")

    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        table.add_row(cat, str(count))

    console.print(table)


@cli.command()
def gui():
    """Launch the desktop GUI."""
    from gui import main as gui_main
    gui_main()


@cli.command()
@click.argument("key")
@click.argument("value")
def config(key: str, value: str):
    """Update a config setting (e.g., pomodoro_minutes 30)."""
    cfg = load_config()
    if key not in cfg:
        console.print(f"[red]Unknown setting: {key}[/red]")
        console.print(f"[dim]Available: {', '.join(cfg.keys())}[/dim]")
        return
    if key == "anthropic_api_key":
        cfg[key] = value
    else:
        cfg[key] = int(value)
    save_config(cfg)
    console.print(f"[green]Set {key} = {value}[/green]")


if __name__ == "__main__":
    cli()
