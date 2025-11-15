#!/usr/bin/env python3
"""Quick script to show current memory statistics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory import get_vector_memory
from rich.console import Console
from rich.table import Table
import logging

logging.basicConfig(level=logging.WARNING)

console = Console()

def main():
    console.print("\n[bold cyan]📊 Radira Memory Statistics[/bold cyan]\n")

    memory = get_vector_memory()
    stats = memory.get_statistics()

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Collection", style="cyan", width=20)
    table.add_column("Count", style="yellow", width=10)

    table.add_row("Experiences", str(stats['total_experiences']))
    table.add_row("Lessons", str(stats['total_lessons']))
    table.add_row("Strategies", str(stats['total_strategies']))
    table.add_row("User Facts", str(stats['total_facts']))

    total = (
        stats['total_experiences'] +
        stats['total_lessons'] +
        stats['total_strategies'] +
        stats['total_facts']
    )

    table.add_row("", "")  # Separator
    table.add_row("[bold]TOTAL[/bold]", f"[bold]{total}[/bold]")

    console.print(table)
    console.print(f"\n[dim]Storage: {stats['storage_path']}[/dim]")
    console.print(f"[dim]Backend: {stats['backend'].upper()}[/dim]\n")

    if total == 0:
        console.print("[yellow]💡 No data stored yet. Memory is empty.[/yellow]")
    else:
        console.print(f"[green]✅ Total {total} entries in memory[/green]")
        console.print("\n[cyan]To manage memory, run:[/cyan] [bold]python3 memory_manager.py[/bold]")

if __name__ == "__main__":
    main()
