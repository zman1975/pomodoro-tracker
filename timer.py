"""Timer logic and TUI using Rich."""

import time
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.align import Align


console = Console()


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    m, s = divmod(seconds, 60)
    return f"{m:02d}:{s:02d}"


def build_timer_display(task: str, remaining: int, total: int, is_break: bool) -> Panel:
    """Build the Rich panel for the timer display."""
    fraction = remaining / total if total > 0 else 0
    bar_width = 30
    filled = int(bar_width * fraction)
    empty = bar_width - filled

    time_str = format_time(remaining)
    bar = f"[green]{'█' * filled}[/green][dim]{'░' * empty}[/dim]"

    label = "[cyan]BREAK[/cyan]" if is_break else "[red]FOCUS[/red]"
    title = f"  {label}  {time_str}  "

    body = Text.from_markup(
        f"\n{bar}\n\n"
        f"[bold]{task}[/bold]\n\n"
        f"[dim]Press Ctrl+C to stop[/dim]\n"
    )
    body.justify = "center"

    panel = Panel(
        Align.center(body),
        title=title,
        border_style="green" if is_break else "red",
        width=50,
        padding=(1, 2),
    )
    return panel


def run_timer(task: str, minutes: int, is_break: bool = False) -> tuple[int, bool]:
    """Run a countdown timer. Returns (elapsed_seconds, completed)."""
    total = minutes * 60
    remaining = total
    start = time.time()

    try:
        with Live(
            build_timer_display(task, remaining, total, is_break),
            console=console,
            refresh_per_second=4,
            transient=True,
        ) as live:
            while remaining > 0:
                elapsed = int(time.time() - start)
                remaining = max(0, total - elapsed)
                live.update(build_timer_display(task, remaining, total, is_break))
                time.sleep(0.25)
    except KeyboardInterrupt:
        elapsed = int(time.time() - start)
        console.print("\n[yellow]Timer stopped early.[/yellow]")
        return elapsed, False

    console.print("\n[bold green]Time's up![/bold green] 🔔")
    return total, True
