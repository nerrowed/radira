#!/usr/bin/env python3
"""Debug script untuk check tool registration."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.registry import get_registry
from agent.tools.filesystem import FileSystemTool
from agent.tools.terminal import TerminalTool
from agent.tools.web_generator import WebGeneratorTool
from agent.tools.web_search import WebSearchTool
from agent.tools.pentest import PentestTool
from agent.core.task_classifier import get_task_classifier, TaskType
from agent.llm.groq_client import get_groq_client
from config.settings import settings
from rich.console import Console
from rich.table import Table

console = Console()


def check_tool_names():
    """Check tool names dari class definition."""
    console.print("\n[bold cyan]1. Tool Names dari Class Definition[/bold cyan]")

    tools = [
        ("FileSystemTool", FileSystemTool(working_directory=settings.working_directory)),
        ("TerminalTool", TerminalTool(working_directory=settings.working_directory)),
        ("WebGeneratorTool", WebGeneratorTool(output_directory=settings.working_directory)),
        ("WebSearchTool", WebSearchTool(max_results=5)),
        ("PentestTool", PentestTool(working_directory=settings.working_directory))
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Class Name", style="cyan")
    table.add_column("Tool Name (.name)", style="yellow")

    for class_name, tool in tools:
        table.add_row(class_name, tool.name)

    console.print(table)


def check_registry():
    """Check apa yang registered di global registry."""
    console.print("\n[bold cyan]2. Tools di Global Registry[/bold cyan]")

    registry = get_registry()

    if len(registry) == 0:
        console.print("[red]❌ Registry KOSONG! Tools belum di-register.[/red]")
        return

    console.print(f"[green]✓ Registry has {len(registry)} tools[/green]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Tool Name", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Status", style="green")

    for tool in registry.list_tools():
        table.add_row(tool.name, tool.category, "✓ Registered")

    console.print(table)


def check_task_classifier():
    """Check task classifier tool mapping."""
    console.print("\n[bold cyan]3. Task Classifier Tool Mapping[/bold cyan]")

    llm = get_groq_client()
    classifier = get_task_classifier(llm)

    task_types = [
        TaskType.CONVERSATIONAL,
        TaskType.SIMPLE_QA,
        TaskType.FILE_OPERATION,
        TaskType.WEB_SEARCH,
        TaskType.CODE_GENERATION,
        TaskType.PENTEST,
        TaskType.TERMINAL_COMMAND,
        TaskType.COMPLEX_MULTI_STEP
    ]

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Task Type", style="cyan")
    table.add_column("Required Tools", style="yellow")

    for task_type in task_types:
        tools = classifier.get_required_tools(task_type)
        tools_str = str(tools) if tools else "[]"
        table.add_row(task_type.value, tools_str)

    console.print(table)


def test_file_operation_flow():
    """Test full flow untuk file operation task."""
    console.print("\n[bold cyan]4. Test File Operation Flow[/bold cyan]")

    llm = get_groq_client()
    classifier = get_task_classifier(llm)
    registry = get_registry()

    # Classify task
    task = "coba baca file radira.txt"
    task_type, confidence = classifier.classify(task)

    console.print(f"Task: [yellow]{task}[/yellow]")
    console.print(f"Classification: [cyan]{task_type.value}[/cyan] (confidence: {confidence:.2f})")

    # Get required tools
    required_tools = classifier.get_required_tools(task_type)
    console.print(f"Required tools from classifier: [yellow]{required_tools}[/yellow]")

    # Check if tools available in registry
    console.print(f"\nRegistry check:")
    for tool_name in required_tools:
        if registry.has(tool_name):
            console.print(f"  ✓ [green]{tool_name}[/green] - FOUND")
        else:
            console.print(f"  ❌ [red]{tool_name}[/red] - NOT FOUND")

    # Try filter
    available_tools = [t for t in registry.list_tools() if t.name in required_tools]
    console.print(f"\nFiltered tools: [yellow]{[t.name for t in available_tools]}[/yellow]")

    if not available_tools:
        console.print("[red]❌ PROBLEM: No tools available after filtering![/red]")
        console.print(f"[red]   Required: {required_tools}[/red]")
        console.print(f"[red]   Available in registry: {registry.list_tool_names()}[/red]")
    else:
        console.print(f"[green]✓ {len(available_tools)} tools available[/green]")


def main():
    """Run all debug checks."""
    console.print("\n[bold green]═══════════════════════════════════════[/bold green]")
    console.print("[bold green]   Tool Registration Debug Script[/bold green]")
    console.print("[bold green]═══════════════════════════════════════[/bold green]")

    # 1. Check tool names
    check_tool_names()

    # 2. Check registry (before setup_tools)
    console.print("\n[bold yellow]Note: Registry might be empty before setup_tools() is called[/bold yellow]")
    check_registry()

    # 3. Check classifier mapping
    check_task_classifier()

    # 4. Test full flow
    test_file_operation_flow()

    console.print("\n[bold green]═══════════════════════════════════════[/bold green]")
    console.print("[bold cyan]Recommendations:[/bold cyan]")
    console.print("1. If registry is empty, run setup_tools() in main.py first")
    console.print("2. Check if tool names match between classifier and registry")
    console.print("3. Verify singleton pattern is working (same registry instance)")
    console.print("[bold green]═══════════════════════════════════════[/bold green]\n")


if __name__ == '__main__':
    main()
