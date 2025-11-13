"""Main entry point for the AI Autonomous Agent."""

import sys
import logging
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from rich.prompt import Prompt

from agent.llm.groq_client import get_groq_client
from agent.tools.registry import get_registry
from config.settings import settings

# Import orchestrator based on settings
if settings.use_dual_orchestrator:
    from agent.core.dual_orchestrator import DualOrchestrator as AgentOrchestrator
    ORCHESTRATOR_TYPE = "Dual Orchestrator (Anti-Looping)"
else:
    from agent.core.orchestrator import AgentOrchestrator
    ORCHESTRATOR_TYPE = "Classic Orchestrator"
from agent.tools.filesystem import FileSystemTool
from agent.tools.terminal import TerminalTool
from agent.tools.web_generator import WebGeneratorTool
from agent.tools.web_search import WebSearchTool
from agent.tools.pentest import PentestTool
from agent.utils.workspace import setup_workspace

# Setup rich console
console = Console()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, console=console)]
)
logger = logging.getLogger(__name__)


def setup_tools():
    """Register all available tools."""
    # Setup workspace directories
    workspace_dirs = setup_workspace()
    logger.info(f"Workspace ready: {workspace_dirs['base']}")

    registry = get_registry()

    # Register tools
    tools = [
        FileSystemTool(working_directory=settings.working_directory),
        TerminalTool(working_directory=settings.working_directory),
        WebGeneratorTool(output_directory=settings.working_directory),
        WebSearchTool(max_results=5),
        PentestTool(working_directory=settings.working_directory)
    ]

    for tool in tools:
        registry.register(tool)
        logger.info(f"Registered tool: {tool.name}")

    return registry


def print_banner():
    """Print welcome banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║           RADIRA                                          ║
    ║           Created By Nerrow                               ║
    ║                                                           ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")


def print_config():
    """Print current configuration."""
    config_info = f"""
    [bold]Configuration:[/bold]
    • Orchestrator: [cyan]{ORCHESTRATOR_TYPE}[/cyan]
    • Model: {settings.groq_model}
    • Working Directory: {settings.working_directory}
    • Sandbox Mode: {settings.sandbox_mode}
    • Max Iterations: {settings.max_iterations}
    • Task Classification: {'✓ Enabled' if settings.enable_task_classification else '✗ Disabled'}
    • Answer Validation: {'✓ Enabled' if settings.enable_answer_validation else '✗ Disabled'}
    • Command Timeout: {settings.command_timeout_seconds}s
    """
    console.print(Panel(config_info, title="Settings", border_style="green"))


def run_interactive():
    """Run agent in interactive mode."""
    print_banner()
    print_config()

    # Setup
    try:
        registry = setup_tools()
        agent = AgentOrchestrator(verbose=True)
        console.print("\n✓ Agent initialized successfully!", style="bold green")
        console.print(f"✓ Loaded {len(registry)} tools\n", style="bold green")
    except Exception as e:
        console.print(f"\n✗ Failed to initialize agent: {e}", style="bold red")
        return

    # Interactive loop
    console.print("[bold yellow]Interactive Mode[/bold yellow]")
    console.print("Enter your task or command. Type 'exit' to quit, 'help' for commands.\n")

    while True:
        try:
            # Get user input
            task = Prompt.ask("\n[bold cyan]Task[/bold cyan]")

            if not task:
                continue

            # Handle special commands
            if task.lower() in ['exit', 'quit', 'q']:
                console.print("\nGoodbye! 👋", style="bold yellow")
                break

            elif task.lower() == 'help':
                print_help()
                continue

            elif task.lower() == 'tools':
                list_tools(registry)
                continue

            elif task.lower() == 'stats':
                print_stats(agent)
                continue

            elif task.lower() == 'reset':
                agent.reset()
                console.print("✓ Agent state reset", style="bold green")
                continue

            elif task.lower() == 'config':
                print_config()
                continue

            # Execute task
            console.print()  # Blank line
            result = agent.run(task)

            # Show result
            console.print("\n" + "="*60)
            console.print(Panel(result, title="Result", border_style="green"))

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted by user[/yellow]")
            if Prompt.ask("Exit?", choices=["y", "n"], default="n") == "y":
                break
            continue

        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}")
            logger.exception("Unexpected error")


def run_single_task(task: str):
    """Run a single task and exit."""
    console.print(f"[bold]Task:[/bold] {task}\n")

    try:
        registry = setup_tools()
        agent = AgentOrchestrator(verbose=True)
    except Exception as e:
        console.print(f"[bold red]Failed to initialize:[/bold red] {e}")
        sys.exit(1)

    # Run task
    try:
        result = agent.run(task)
        console.print("\n" + "="*60)
        console.print(Panel(result, title="Result", border_style="green"))
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        logger.exception("Task failed")
        sys.exit(1)


def print_help():
    """Print help information."""
    help_text = """
    [bold]Available Commands:[/bold]

    [cyan]Interactive Commands:[/cyan]
    • help      - Show this help message
    • tools     - List available tools
    • stats     - Show agent statistics
    • config    - Show current configuration
    • reset     - Reset agent state
    • exit/quit - Exit the program

    [cyan]Task Examples:[/cyan]
    • "Create a landing page for a coffee shop"
    • "List all Python files in the current directory"
    • "Run git status"
    • "Create a new directory called 'projects'"
    • "Generate a React todo app"

    [cyan]Tools Available:[/cyan]
    • file_system  - Read, write, list files
    • terminal     - Execute shell commands
    • web_generator - Generate web applications
    """
    console.print(Panel(help_text, border_style="yellow"))


def list_tools(registry):
    """List all available tools."""
    tools = registry.list_tools()

    console.print("\n[bold]Available Tools:[/bold]\n")
    for tool in tools:
        console.print(f"[cyan]• {tool.name}[/cyan]")
        console.print(f"  {tool.description}")
        console.print(f"  Category: {tool.category}")
        if tool.is_dangerous:
            console.print(f"  [red]⚠ Dangerous operation[/red]")
        console.print()


def print_stats(agent):
    """Print agent statistics."""
    state = agent.get_state()

    stats_text = f"""
    [bold]Agent Statistics:[/bold]

    Current Task: {state['current_task'] or 'None'}
    Iteration: {state['iteration']}/{state['max_iterations']}
    Actions Taken: {len(state['history'])}

    [bold]Token Usage:[/bold]
    • Total: {state['token_stats']['total_tokens']}
    • Prompt: {state['token_stats']['prompt_tokens']}
    • Completion: {state['token_stats']['completion_tokens']}

    [bold]Tool Usage:[/bold]
    """

    for tool_name, stats in state['tool_stats'].items():
        if stats['execution_count'] > 0:
            stats_text += f"\n• {tool_name}: {stats['execution_count']} times "
            stats_text += f"(avg: {stats['average_execution_time']:.2f}s)"

    console.print(Panel(stats_text, border_style="blue"))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AI Autonomous Agent - Execute tasks autonomously with AI"
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="Task to execute (if not provided, runs in interactive mode)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum iterations (default from config)"
    )
    parser.add_argument(
        "--working-dir",
        help="Working directory (default from config)"
    )

    args = parser.parse_args()

    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Update settings if provided
    if args.max_iterations:
        settings.max_iterations = args.max_iterations
    if args.working_dir:
        settings.working_directory = args.working_dir

    # Run mode
    if args.task:
        # Single task mode
        task = " ".join(args.task)
        run_single_task(task)
    else:
        # Interactive mode
        run_interactive()


if __name__ == "__main__":
    main()
