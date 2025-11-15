#!/usr/bin/env python3
"""Interactive Memory Management Tool for Radira.

Provides user-friendly interface to manage ChromaDB vector memory:
- View statistics
- Cleanup old entries
- Limit collection sizes
- Export/Import memory
- Reset all data
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory import get_vector_memory
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm, IntPrompt
import logging

# Optional: Memory monitor (requires psutil)
try:
    from agent.utils.memory_monitor import get_memory_monitor
    MEMORY_MONITOR_AVAILABLE = True
except ImportError:
    MEMORY_MONITOR_AVAILABLE = False

# Suppress logs for cleaner output
logging.basicConfig(level=logging.WARNING)

console = Console()


def print_banner():
    """Print welcome banner."""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           RADIRA MEMORY MANAGER                           ║
║           Interactive Memory Management Tool              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def show_statistics():
    """Show memory statistics."""
    console.print("\n[bold cyan]📊 Memory Statistics[/bold cyan]\n")

    memory = get_vector_memory()
    stats = memory.get_statistics()

    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=30)
    table.add_column("Value", style="yellow", width=20)

    table.add_row("Total Experiences", str(stats['total_experiences']))
    table.add_row("Total Lessons", str(stats['total_lessons']))
    table.add_row("Total Strategies", str(stats['total_strategies']))
    table.add_row("Total User Facts", str(stats['total_facts']))
    table.add_row("Storage Path", stats['storage_path'])
    table.add_row("Backend", stats['backend'].upper())

    console.print(table)

    # Memory usage (if available)
    if MEMORY_MONITOR_AVAILABLE:
        monitor = get_memory_monitor()
        mem_stats = monitor.get_current_stats()

        console.print(f"\n[bold yellow]💾 Process Memory:[/bold yellow] {mem_stats.process_memory_mb:.1f} MB")
        console.print(f"[bold yellow]🖥️  System Memory:[/bold yellow] {mem_stats.system_memory_percent:.1f}%")
        console.print(f"[bold yellow]📈 Memory Trend:[/bold yellow] {monitor.get_memory_trend()}")
    else:
        console.print(f"\n[dim]Note: Install 'psutil' for memory monitoring[/dim]")


def cleanup_old_entries():
    """Cleanup old memory entries."""
    console.print("\n[bold cyan]🧹 Cleanup Old Entries[/bold cyan]\n")

    # Get parameters
    max_age_days = IntPrompt.ask(
        "[yellow]Delete entries older than how many days?[/yellow]",
        default=30
    )

    keep_successful = Confirm.ask(
        "[yellow]Keep successful experiences even if old?[/yellow]",
        default=True
    )

    # Confirm
    if not Confirm.ask(
        f"\n[bold red]⚠️  Delete entries older than {max_age_days} days?[/bold red]",
        default=False
    ):
        console.print("[yellow]Cleanup cancelled.[/yellow]")
        return

    # Execute cleanup
    console.print("\n[yellow]Cleaning up old entries...[/yellow]")
    memory = get_vector_memory()

    result = memory.cleanup_old_entries(
        max_age_days=max_age_days,
        keep_successful=keep_successful
    )

    console.print(f"\n[bold green]✅ Cleanup complete![/bold green]")
    console.print(f"   Deleted: {result['deleted']} entries")
    console.print(f"   Cutoff date: {result['cutoff_date']}")


def limit_collection_sizes():
    """Limit collection sizes."""
    console.print("\n[bold cyan]📏 Limit Collection Sizes[/bold cyan]\n")

    # Get current stats
    memory = get_vector_memory()
    stats = memory.get_statistics()

    console.print(f"[yellow]Current sizes:[/yellow]")
    console.print(f"  Experiences: {stats['total_experiences']}")
    console.print(f"  Lessons: {stats['total_lessons']}")
    console.print(f"  Strategies: {stats['total_strategies']}\n")

    # Get limits
    max_experiences = IntPrompt.ask(
        "[yellow]Max experiences to keep?[/yellow]",
        default=1000
    )

    max_lessons = IntPrompt.ask(
        "[yellow]Max lessons to keep?[/yellow]",
        default=500
    )

    max_strategies = IntPrompt.ask(
        "[yellow]Max strategies to keep?[/yellow]",
        default=300
    )

    # Calculate deletions
    to_delete_exp = max(0, stats['total_experiences'] - max_experiences)
    to_delete_les = max(0, stats['total_lessons'] - max_lessons)
    to_delete_str = max(0, stats['total_strategies'] - max_strategies)
    total_to_delete = to_delete_exp + to_delete_les + to_delete_str

    if total_to_delete == 0:
        console.print("\n[green]No entries need to be deleted (all within limits).[/green]")
        return

    # Confirm
    console.print(f"\n[bold red]⚠️  This will delete {total_to_delete} entries:[/bold red]")
    console.print(f"   Experiences: {to_delete_exp}")
    console.print(f"   Lessons: {to_delete_les}")
    console.print(f"   Strategies: {to_delete_str}")

    if not Confirm.ask("\n[bold red]Proceed with deletion?[/bold red]", default=False):
        console.print("[yellow]Size limiting cancelled.[/yellow]")
        return

    # Execute
    console.print("\n[yellow]Limiting collection sizes...[/yellow]")
    result = memory.limit_collection_size(
        max_experiences=max_experiences,
        max_lessons=max_lessons,
        max_strategies=max_strategies
    )

    console.print(f"\n[bold green]✅ Size limiting complete![/bold green]")
    console.print(f"   Pruned: {result['pruned']} entries")


def export_memory():
    """Export memory to JSON file."""
    console.print("\n[bold cyan]💾 Export Memory[/bold cyan]\n")

    output_file = console.input("[yellow]Output filename (default: memory_export.json): [/yellow]") or "memory_export.json"

    # Execute export
    console.print(f"\n[yellow]Exporting memory to {output_file}...[/yellow]")
    memory = get_vector_memory()

    try:
        memory.export_memory(Path(output_file))
        console.print(f"\n[bold green]✅ Export complete![/bold green]")
        console.print(f"   File: {output_file}")
    except Exception as e:
        console.print(f"\n[bold red]❌ Export failed: {e}[/bold red]")


def clear_all_memories():
    """Clear all memories (DANGEROUS!)."""
    console.print("\n[bold red]⚠️  CLEAR ALL MEMORIES ⚠️[/bold red]\n")

    # Show current stats
    memory = get_vector_memory()
    stats = memory.get_statistics()

    console.print("[yellow]Current data:[/yellow]")
    console.print(f"  Experiences: {stats['total_experiences']}")
    console.print(f"  Lessons: {stats['total_lessons']}")
    console.print(f"  Strategies: {stats['total_strategies']}")
    console.print(f"  User Facts: {stats['total_facts']}")

    total_entries = (
        stats['total_experiences'] +
        stats['total_lessons'] +
        stats['total_strategies'] +
        stats['total_facts']
    )

    console.print(f"\n[bold red]This will DELETE ALL {total_entries} entries![/bold red]")
    console.print("[bold red]This action CANNOT be undone![/bold red]\n")

    # Triple confirmation
    if not Confirm.ask("[bold red]Are you ABSOLUTELY sure?[/bold red]", default=False):
        console.print("[green]Cancelled. No data was deleted.[/green]")
        return

    if not Confirm.ask("[bold red]Type YES to confirm deletion[/bold red]", default=False):
        console.print("[green]Cancelled. No data was deleted.[/green]")
        return

    # Final confirmation with typing
    confirmation = console.input("[bold red]Type 'DELETE ALL' to proceed: [/bold red]")
    if confirmation != "DELETE ALL":
        console.print("[green]Cancelled. No data was deleted.[/green]")
        return

    # Execute deletion
    console.print("\n[yellow]Clearing all memories...[/yellow]")
    success = memory.clear_all_memories(confirm=True)

    if success:
        console.print(f"\n[bold green]✅ All memories cleared![/bold green]")
        console.print(f"   Deleted {total_entries} total entries")
        console.print("   Collections have been recreated (empty)")
    else:
        console.print("\n[bold red]❌ Failed to clear memories[/bold red]")


def check_memory_health():
    """Check memory health status."""
    console.print("\n[bold cyan]🏥 Memory Health Check[/bold cyan]\n")

    if not MEMORY_MONITOR_AVAILABLE:
        console.print("[bold yellow]⚠️  Memory monitoring not available[/bold yellow]")
        console.print("[yellow]Install psutil: pip install psutil[/yellow]\n")
        return

    monitor = get_memory_monitor()
    health = monitor.check_memory_health()

    if health["healthy"]:
        console.print("[bold green]✅ Memory is healthy![/bold green]\n")
    else:
        console.print("[bold red]⚠️  Memory issues detected![/bold red]\n")

        console.print("[bold yellow]Issues:[/bold yellow]")
        for issue in health["issues"]:
            console.print(f"  - {issue}")

        console.print("\n[bold yellow]Recommendations:[/bold yellow]")
        for rec in health["recommendations"]:
            console.print(f"  ⚡ {rec}")

    # Show current stats
    stats = health["stats"]
    console.print(f"\n[yellow]Current Status:[/yellow]")
    console.print(f"  Process Memory: {stats.process_memory_mb:.1f} MB")
    console.print(f"  System Memory: {stats.system_memory_percent:.1f}%")
    console.print(f"  Available Memory: {stats.available_memory_mb:.1f} MB")


def show_menu():
    """Show main menu."""
    panel = Panel(
        """[cyan]1.[/cyan] View Statistics
[cyan]2.[/cyan] Check Memory Health
[cyan]3.[/cyan] Cleanup Old Entries
[cyan]4.[/cyan] Limit Collection Sizes
[cyan]5.[/cyan] Export Memory to JSON
[cyan]6.[/cyan] [bold red]Clear All Memories (DANGEROUS!)[/bold red]
[cyan]0.[/cyan] Exit""",
        title="[bold magenta]Main Menu[/bold magenta]",
        border_style="cyan"
    )
    console.print(panel)


def main():
    """Main interactive loop."""
    print_banner()

    while True:
        console.print()
        show_menu()

        try:
            choice = console.input("\n[bold yellow]Select option: [/bold yellow]")

            if choice == "1":
                show_statistics()
            elif choice == "2":
                check_memory_health()
            elif choice == "3":
                cleanup_old_entries()
            elif choice == "4":
                limit_collection_sizes()
            elif choice == "5":
                export_memory()
            elif choice == "6":
                clear_all_memories()
            elif choice == "0":
                console.print("\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
                break
            else:
                console.print("[red]Invalid option. Please try again.[/red]")

            # Pause before showing menu again
            if choice in ["1", "2", "3", "4", "5", "6"]:
                console.input("\n[dim]Press Enter to continue...[/dim]")

        except KeyboardInterrupt:
            console.print("\n\n[bold cyan]Goodbye! 👋[/bold cyan]\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]")
            console.input("\n[dim]Press Enter to continue...[/dim]")


if __name__ == "__main__":
    main()
