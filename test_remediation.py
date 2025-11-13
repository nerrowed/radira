#!/usr/bin/env python3
"""Test script for Auto-Remediation System."""

from agent.state.error_memory import ErrorMemory
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def test_remediation_patterns():
    """Test remediation suggestion generation for various error types."""

    em = ErrorMemory()

    # Test cases: (tool, operation, error, metadata)
    test_cases = [
        {
            'name': 'File Does Not Exist',
            'error': {
                'tool_name': 'file_system',
                'operation': 'read',
                'error': 'File does not exist: /workspace/config.txt',
                'metadata': {'path': '/workspace/config.txt'}
            }
        },
        {
            'name': 'File Too Large',
            'error': {
                'tool_name': 'file_system',
                'operation': 'read',
                'error': 'File too large: 15.3MB (max: 10MB)',
                'metadata': {
                    'path': '/workspace/bigfile.dat',
                    'file_size': 16000000,
                    'max_size': 10485760
                }
            }
        },
        {
            'name': 'Extension Not Allowed',
            'error': {
                'tool_name': 'file_system',
                'operation': 'write',
                'error': "File extension '.exe' not allowed",
                'metadata': {
                    'path': '/workspace/program.exe',
                    'extension': '.exe'
                }
            }
        },
        {
            'name': 'Permission Denied',
            'error': {
                'tool_name': 'file_system',
                'operation': 'read',
                'error': "Access to '/blocked/secret' is blocked for safety",
                'metadata': {'path': '/blocked/secret'}
            }
        },
        {
            'name': 'Not a Directory',
            'error': {
                'tool_name': 'file_system',
                'operation': 'list',
                'error': 'Not a directory: /workspace/file.txt',
                'metadata': {'path': '/workspace/file.txt'}
            }
        },
        {
            'name': 'Binary File',
            'error': {
                'tool_name': 'file_system',
                'operation': 'read',
                'error': 'File is not text-readable (binary file?)',
                'metadata': {'path': '/workspace/image.png', 'file_size': 5000}
            }
        },
        {
            'name': 'Command Not Found',
            'error': {
                'tool_name': 'terminal',
                'operation': 'execute',
                'error': 'nmap: command not found',
                'metadata': {}
            }
        },
        {
            'name': 'Network Error',
            'error': {
                'tool_name': 'web_search',
                'operation': 'fetch',
                'error': 'Connection refused: network unreachable',
                'metadata': {}
            }
        },
    ]

    console.print("\n[bold cyan]🧪 Auto-Remediation Pattern Tests[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Test Case", style="cyan", width=20)
    table.add_column("Severity", width=10)
    table.add_column("Action Type", width=15)
    table.add_column("Suggestion", width=60)

    for test in test_cases:
        error_record = test['error']
        remediation = em.get_remediation_suggestion(error_record)

        if remediation:
            severity_color = {
                'high': 'red',
                'medium': 'yellow',
                'low': 'green'
            }.get(remediation['severity'], 'white')

            severity_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(remediation['severity'], '⚪')

            auto_fix = " ✨" if remediation.get('auto_fixable') else ""

            table.add_row(
                test['name'],
                f"[{severity_color}]{severity_emoji} {remediation['severity']}[/{severity_color}]",
                remediation['action_type'],
                remediation['suggestion'][:60] + "..." + auto_fix if len(remediation['suggestion']) > 60 else remediation['suggestion'] + auto_fix
            )
        else:
            table.add_row(
                test['name'],
                "[red]❌ NONE[/red]",
                "N/A",
                "No remediation found"
            )

    console.print(table)

    # Statistics
    total = len(test_cases)
    with_remediation = sum(1 for t in test_cases if em.get_remediation_suggestion(t['error']))
    coverage = with_remediation / total * 100

    stats_panel = Panel(
        f"""[bold]Coverage:[/bold] {with_remediation}/{total} tests ({coverage:.1f}%)
[bold]Pattern Library Size:[/bold] {len(em._get_remediation_patterns())} patterns
[bold]Status:[/bold] {'✅ Excellent' if coverage >= 90 else '⚠️ Needs Improvement'}""",
        title="[bold green]Statistics[/bold green]",
        border_style="green"
    )
    console.print("\n", stats_panel)


def test_detailed_example():
    """Show detailed example with actual error flow."""

    console.print("\n[bold cyan]📋 Detailed Example: File Does Not Exist[/bold cyan]\n")

    em = ErrorMemory()

    # Simulate actual error
    error_id = em.log_error(
        tool_name="file_system",
        operation="read",
        error_message="File does not exist: /workspace/missing.txt",
        path="/workspace/missing.txt"
    )

    # Retrieve logged error
    error_record = next((e for e in em.errors if e['id'] == error_id), None)

    if error_record:
        console.print("[bold]Original Error:[/bold]")
        console.print(f"  {error_record['error']}\n")

        if 'remediation' in error_record:
            remediation = error_record['remediation']

            severity_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(remediation['severity'], '⚪')

            console.print(f"[bold]{severity_emoji} Remediation Suggestion ({remediation['action_type'].title()}):[/bold]")
            console.print(f"  [cyan]{remediation['suggestion']}[/cyan]\n")

            console.print(f"[bold]Details:[/bold]")
            console.print(f"  • Severity: {remediation['severity']}")
            console.print(f"  • Category: {remediation['category']}")
            console.print(f"  • Auto-fixable: {'Yes ✨' if remediation.get('auto_fixable') else 'No'}")

            if remediation.get('auto_fixable'):
                console.print("\n  [green]This error may be automatically fixed in future versions![/green]")


def show_pattern_library():
    """Display the complete remediation pattern library."""

    em = ErrorMemory()
    patterns = em._get_remediation_patterns()

    console.print(f"\n[bold cyan]📚 Remediation Pattern Library ({len(patterns)} patterns)[/bold cyan]\n")

    # Group by category
    from collections import defaultdict
    by_category = defaultdict(list)

    for pattern in patterns:
        by_category[pattern.get('category', 'general')].append(pattern)

    for category, pats in sorted(by_category.items()):
        console.print(f"[bold yellow]{category.upper()}[/bold yellow] ({len(pats)} patterns)")

        for pattern in pats:
            severity_emoji = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(pattern['severity'], '⚪')

            keywords_str = ', '.join(f'"{k}"' for k in pattern['keywords'][:3])
            if len(pattern['keywords']) > 3:
                keywords_str += ', ...'

            auto_fix = " ✨" if pattern.get('auto_fixable') else ""

            console.print(f"  {severity_emoji} Keywords: {keywords_str}")
            console.print(f"     → {pattern['suggestion'][:70]}...{auto_fix}" if len(pattern['suggestion']) > 70 else f"     → {pattern['suggestion']}{auto_fix}")
            console.print()


def main():
    """Run all tests."""

    console.print(Panel.fit(
        "[bold cyan]Auto-Remediation System Test Suite[/bold cyan]\n"
        "Testing error pattern matching and suggestion generation",
        border_style="cyan"
    ))

    # Test 1: Pattern matching
    test_remediation_patterns()

    # Test 2: Detailed example
    test_detailed_example()

    # Test 3: Show library
    show_pattern_library()

    console.print("\n[bold green]✅ All tests completed![/bold green]\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error during testing: {e}[/red]")
        import traceback
        traceback.print_exc()
