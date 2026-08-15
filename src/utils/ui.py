"""Rich terminal UI helpers."""

from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel

console = Console()


def make_progress() -> Progress:
    """Create a standard progress bar."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def print_account_table(accounts: list[dict], title: str = "Accounts") -> None:
    """Print accounts as a rich table."""
    table = Table(title=title, show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Username", style="cyan")
    table.add_column("Email", style="green")
    table.add_column("Status", style="bold")
    table.add_column("Created", style="dim")

    status_colors = {
        "created": "yellow",
        "verified": "green",
        "failed": "red",
        "pending": "blue",
    }

    for i, acc in enumerate(accounts, 1):
        status = acc.get("status", "unknown")
        color = status_colors.get(status, "white")
        table.add_row(
            str(i),
            acc.get("username", "?"),
            acc.get("email", "?"),
            f"[{color}]{status}[/{color}]",
            acc.get("created_at", "?")[:10],
        )

    console.print(table)


def print_summary(
    total: int, success: int, failed: int, elapsed: float
) -> None:
    """Print batch summary panel."""
    content = (
        f"[bold green]Success:[/bold green] {success}\n"
        f"[bold red]Failed:[/bold red] {failed}\n"
        f"[bold]Total:[/bold] {total}\n"
        f"[dim]Elapsed:[/dim] {elapsed:.1f}s"
    )
    console.print(Panel(content, title="Batch Summary", border_style="blue"))
