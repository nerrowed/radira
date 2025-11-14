#!/usr/bin/env python3
"""Test script untuk verify task classifier improvements."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.core.task_classifier import get_task_classifier, TaskType
from rich.console import Console
from rich.table import Table

console = Console()


def test_classification():
    """Test classifier dengan user's exact examples."""

    classifier = get_task_classifier()

    # Test cases dari user
    test_cases = [
        # User's failed examples
        ("coba buatkan aplikasi kalkulator dengan nama kal.py", TaskType.CODE_GENERATION),
        ("buatkan saya kalkulator python sederhana", TaskType.CODE_GENERATION),
        ("buatkan saya halaman login dengan htmll dan css seperti milik tokopedia.com", TaskType.WEB_GENERATION),

        # Additional test cases
        ("buat file config.json", TaskType.FILE_OPERATION),
        ("baca file radira.txt", TaskType.FILE_OPERATION),
        ("halo apa kabar", TaskType.CONVERSATIONAL),
        ("cari berita terbaru", TaskType.WEB_SEARCH),
        ("buatkan aplikasi todo list", TaskType.CODE_GENERATION),
        ("buatkan website toko online", TaskType.WEB_GENERATION),
        ("tulis program python untuk sort array", TaskType.CODE_GENERATION),
        ("buat halaman landing page", TaskType.WEB_GENERATION),
        ("jalankan npm install", TaskType.TERMINAL_COMMAND),
    ]

    console.print("\n[bold green]═══════════════════════════════════════[/bold green]")
    console.print("[bold green]   Task Classifier Test Results[/bold green]")
    console.print("[bold green]═══════════════════════════════════════[/bold green]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Task", style="cyan", width=50)
    table.add_column("Expected", style="yellow", width=20)
    table.add_column("Actual", style="green", width=20)
    table.add_column("Confidence", style="blue", width=10)
    table.add_column("Status", style="white", width=10)

    passed = 0
    failed = 0

    for task, expected_type in test_cases:
        actual_type, confidence = classifier.classify(task)

        status = "✅ PASS" if actual_type == expected_type else "❌ FAIL"
        status_style = "[green]" if actual_type == expected_type else "[red]"

        if actual_type == expected_type:
            passed += 1
        else:
            failed += 1

        table.add_row(
            task[:50],
            expected_type.value,
            actual_type.value,
            f"{confidence:.2f}",
            f"{status_style}{status}[/]"
        )

    console.print(table)

    console.print(f"\n[bold cyan]Test Summary:[/bold cyan]")
    console.print(f"  [green]✓ Passed:[/green] {passed}/{len(test_cases)}")
    console.print(f"  [red]✗ Failed:[/red] {failed}/{len(test_cases)}")

    if failed == 0:
        console.print(f"\n[bold green]🎉 All tests passed! Classifier is working correctly.[/bold green]")
    else:
        console.print(f"\n[bold yellow]⚠️  Some tests failed. Check patterns if needed.[/bold yellow]")

    console.print("\n[bold green]═══════════════════════════════════════[/bold green]\n")

    # Show tool requirements for user's examples
    console.print("[bold cyan]Tool Requirements for User's Examples:[/bold cyan]\n")

    user_examples = [
        "coba buatkan aplikasi kalkulator dengan nama kal.py",
        "buatkan saya kalkulator python sederhana",
        "buatkan saya halaman login dengan htmll dan css seperti milik tokopedia.com",
    ]

    for task in user_examples:
        task_type, confidence = classifier.classify(task)
        tools = classifier.get_required_tools(task_type)
        temp = classifier.get_temperature(task_type)
        max_iter = classifier.get_max_iterations(task_type)

        console.print(f"[yellow]Task:[/yellow] {task[:60]}...")
        console.print(f"  [cyan]Type:[/cyan] {task_type.value} (confidence: {confidence:.2f})")
        console.print(f"  [green]Tools:[/green] {tools}")
        console.print(f"  [blue]Temperature:[/blue] {temp}, [blue]Max Iterations:[/blue] {max_iter}\n")


if __name__ == '__main__':
    test_classification()
