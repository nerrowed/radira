#!/usr/bin/env python3
"""CLI tool untuk Memory Management System.

Usage:
    python manage_memory.py list [context|experiences|lessons|strategies]
    python manage_memory.py view <id>
    python manage_memory.py delete <type> <id>
    python manage_memory.py add <type> [options]
    python manage_memory.py search <query>
    python manage_memory.py stats
    python manage_memory.py clear [context|all]
    python manage_memory.py export <file>
    python manage_memory.py import <file>
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory_manager import get_memory_manager


def print_section(title, char="="):
    """Print section header."""
    print(f"\n{char * 60}")
    print(f"{title.center(60)}")
    print(f"{char * 60}\n")


def format_timestamp(ts_str):
    """Format ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str


def cmd_list(args):
    """List memory items."""
    manager = get_memory_manager()
    memory_type = args.type

    if memory_type == "context":
        print_section("Context Memory")
        events = manager.list_context_memory(
            limit=args.limit,
            status_filter=args.status
        )

        if not events:
            print("No context events found.")
            return

        for i, event in enumerate(events[-args.limit:], 1):
            status_icon = {
                "success": "✓",
                "error": "✗",
                "completed": "✓",
                "incomplete": "○"
            }.get(event.get("status", ""), "?")

            print(f"{i}. [{format_timestamp(event.get('timestamp', ''))}] {status_icon}")
            print(f"   ID: {event.get('id', 'N/A')}")
            print(f"   Command: {event.get('user_command', 'N/A')[:60]}...")
            print(f"   Action: {event.get('ai_action', 'N/A')}")
            print(f"   Status: {event.get('status', 'N/A')}")
            print()

    elif memory_type == "experiences":
        print_section("Experiences")
        experiences = manager.list_experiences(
            limit=args.limit,
            success_only=args.success_only
        )

        if not experiences:
            print("No experiences found.")
            return

        for i, exp in enumerate(experiences, 1):
            success_icon = "✓" if exp.get("success") else "✗"
            print(f"{i}. [{format_timestamp(exp.get('timestamp', ''))}] {success_icon}")
            print(f"   Task: {exp.get('task', 'N/A')[:60]}...")
            print(f"   Actions: {exp.get('action_count', 0)} actions")
            print(f"   Outcome: {exp.get('outcome', 'N/A')[:60]}...")
            print()

    elif memory_type == "lessons":
        print_section("Lessons Learned")
        lessons = manager.list_lessons(
            limit=args.limit,
            category=args.category
        )

        if not lessons:
            print("No lessons found.")
            return

        for i, lesson in enumerate(lessons, 1):
            print(f"{i}. [{lesson.get('category', 'general')}]")
            print(f"   {lesson.get('lesson', 'N/A')[:80]}...")
            print(f"   Context: {lesson.get('context', 'N/A')[:60]}...")
            print(f"   Importance: {lesson.get('importance', 1.0):.1f}")
            print()

    elif memory_type == "strategies":
        print_section("Successful Strategies")
        strategies = manager.list_strategies(
            limit=args.limit,
            task_type=args.task_type
        )

        if not strategies:
            print("No strategies found.")
            return

        for i, strategy in enumerate(strategies, 1):
            print(f"{i}. {strategy.get('task_type', 'N/A')}")
            print(f"   Strategy: {strategy.get('strategy', 'N/A')[:70]}...")
            print(f"   Success Rate: {strategy.get('success_rate', 0):.0%}")
            print(f"   Usage: {strategy.get('usage_count', 1)} times")
            print()

    else:
        print(f"Unknown memory type: {memory_type}")
        print("Valid types: context, experiences, lessons, strategies")


def cmd_search(args):
    """Search across all memory."""
    print_section(f"Search Results for: '{args.query}'")

    manager = get_memory_manager()
    results = manager.search_all(args.query, n_results=args.limit)

    # Context results
    if results["context"]:
        print("\n[Context Memory]")
        for i, ctx in enumerate(results["context"][:5], 1):
            print(f"{i}. {ctx.get('ai_action', 'N/A')} - {ctx.get('user_command', '')[:50]}...")

    # Experience results
    if results["experiences"]:
        print("\n[Experiences]")
        for i, exp in enumerate(results["experiences"][:5], 1):
            success = "✓" if exp.get("success") else "✗"
            print(f"{i}. {success} {exp.get('task', 'N/A')[:50]}...")

    # Lesson results
    if results["lessons"]:
        print("\n[Lessons]")
        for i, lesson in enumerate(results["lessons"][:5], 1):
            print(f"{i}. {lesson.get('lesson', 'N/A')[:50]}...")

    # Strategy results
    if results["strategies"]:
        print("\n[Strategies]")
        for i, strategy in enumerate(results["strategies"][:5], 1):
            print(f"{i}. {strategy.get('strategy', 'N/A')[:50]}...")

    if not any(results.values()):
        print("No results found.")


def cmd_delete(args):
    """Delete memory item."""
    manager = get_memory_manager()
    memory_type = args.type
    item_id = args.id

    print(f"Deleting {memory_type} with ID: {item_id}...")

    success = False
    if memory_type == "context":
        success = manager.delete_context_by_id(item_id)
    elif memory_type == "experience":
        success = manager.delete_experience(item_id)
    elif memory_type == "lesson":
        success = manager.delete_lesson(item_id)
    elif memory_type == "strategy":
        success = manager.delete_strategy(item_id)
    else:
        print(f"Unknown type: {memory_type}")
        return

    if success:
        print(f"✓ Successfully deleted {memory_type}: {item_id}")
    else:
        print(f"✗ Failed to delete {memory_type}: {item_id}")


def cmd_add(args):
    """Add new memory item."""
    manager = get_memory_manager()
    memory_type = args.type

    if memory_type == "experience":
        if not args.task or not args.outcome:
            print("Error: --task and --outcome are required for experiences")
            return

        actions = args.actions.split(",") if args.actions else []
        exp_id = manager.add_experience(
            task=args.task,
            actions=actions,
            outcome=args.outcome,
            success=args.success,
            metadata={}
        )
        print(f"✓ Added experience: {exp_id}")

    elif memory_type == "lesson":
        if not args.lesson or not args.context:
            print("Error: --lesson and --context are required")
            return

        lesson_id = manager.add_lesson(
            lesson=args.lesson,
            context=args.context,
            category=args.category or "general",
            importance=args.importance or 1.0
        )
        print(f"✓ Added lesson: {lesson_id}")

    elif memory_type == "strategy":
        if not args.strategy or not args.task_type:
            print("Error: --strategy and --task-type are required")
            return

        strategy_id = manager.add_strategy(
            strategy=args.strategy,
            task_type=args.task_type,
            success_rate=args.success_rate or 1.0,
            context=args.context
        )
        print(f"✓ Added strategy: {strategy_id}")

    else:
        print(f"Unknown type: {memory_type}")
        print("Valid types: experience, lesson, strategy")


def cmd_stats(args):
    """Show memory statistics."""
    print_section("Memory Statistics")

    manager = get_memory_manager()
    stats = manager.get_all_statistics()

    # Context stats
    if "context" in stats:
        ctx_stats = stats["context"]
        print("[Context Memory]")
        print(f"  Total Events: {ctx_stats.get('total_events', 0)}")
        print(f"  ChromaDB: {'Available' if ctx_stats.get('chromadb_available') else 'Not Available'}")

        if "status_breakdown" in ctx_stats:
            print("  Status Breakdown:")
            for status, count in ctx_stats["status_breakdown"].items():
                print(f"    • {status}: {count}")

        if "most_common_actions" in ctx_stats:
            print("  Most Common Actions:")
            for action, count in list(ctx_stats["most_common_actions"].items())[:5]:
                print(f"    • {action}: {count}")

    # Vector memory stats
    if "vector_memory" in stats and stats["vector_memory"]:
        vm_stats = stats["vector_memory"]
        print("\n[Vector Memory]")
        print(f"  Experiences: {vm_stats.get('total_experiences', 0)}")
        print(f"  Lessons: {vm_stats.get('total_lessons', 0)}")
        print(f"  Strategies: {vm_stats.get('total_strategies', 0)}")
        print(f"  Backend: {vm_stats.get('backend', 'N/A')}")
        print(f"  Storage: {vm_stats.get('storage_path', 'N/A')}")


def cmd_clear(args):
    """Clear memory."""
    manager = get_memory_manager()

    if args.type == "all":
        print("⚠️  WARNING: This will delete ALL memory!")
        confirm = input("Type 'yes' to confirm: ")

        if confirm.lower() != "yes":
            print("Cancelled.")
            return

        print("Clearing all memory...")
        results = manager.clear_all_memory()

        for mem_type, success in results.items():
            icon = "✓" if success else "✗"
            print(f"{icon} {mem_type}: {'Cleared' if success else 'Failed'}")

    elif args.type == "context":
        print("Clearing context memory...")
        if manager.clear_all_context():
            print("✓ Context memory cleared")
        else:
            print("✗ Failed to clear context memory")

    else:
        print(f"Unknown type: {args.type}")
        print("Valid types: context, all")


def cmd_export(args):
    """Export memory to file."""
    manager = get_memory_manager()
    output_file = Path(args.file)

    print(f"Exporting memory to {output_file}...")

    if manager.export_all_memory(output_file):
        print(f"✓ Memory exported to {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024:.1f} KB")
    else:
        print(f"✗ Failed to export memory")


def cmd_import(args):
    """Import memory from file."""
    manager = get_memory_manager()
    input_file = Path(args.file)

    if not input_file.exists():
        print(f"✗ File not found: {input_file}")
        return

    print(f"Importing memory from {input_file}...")

    counts = manager.import_memory(input_file)

    print("✓ Import complete:")
    print(f"   Experiences: {counts['experiences']}")
    print(f"   Lessons: {counts['lessons']}")
    print(f"   Strategies: {counts['strategies']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Memory Management System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List context memory
  python manage_memory.py list context --limit 10

  # Search across all memory
  python manage_memory.py search "file operations"

  # Delete a context event
  python manage_memory.py delete context evt_123456

  # Add a new lesson
  python manage_memory.py add lesson --lesson "Always check file exists" --context "file operations"

  # Show statistics
  python manage_memory.py stats

  # Export memory
  python manage_memory.py export memory_backup.json

  # Clear all memory (WARNING!)
  python manage_memory.py clear all
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    list_parser = subparsers.add_parser("list", help="List memory items")
    list_parser.add_argument("type", choices=["context", "experiences", "lessons", "strategies"])
    list_parser.add_argument("--limit", type=int, default=10, help="Limit results")
    list_parser.add_argument("--status", help="Filter context by status")
    list_parser.add_argument("--success-only", action="store_true", help="Only successful experiences")
    list_parser.add_argument("--category", help="Filter lessons by category")
    list_parser.add_argument("--task-type", help="Filter strategies by task type")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search all memory")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Results per type")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete memory item")
    delete_parser.add_argument("type", choices=["context", "experience", "lesson", "strategy"])
    delete_parser.add_argument("id", help="Item ID")

    # Add command
    add_parser = subparsers.add_parser("add", help="Add memory item")
    add_parser.add_argument("type", choices=["experience", "lesson", "strategy"])
    add_parser.add_argument("--task", help="Task (for experience)")
    add_parser.add_argument("--actions", help="Actions comma-separated (for experience)")
    add_parser.add_argument("--outcome", help="Outcome (for experience)")
    add_parser.add_argument("--success", action="store_true", help="Mark as successful")
    add_parser.add_argument("--lesson", help="Lesson text")
    add_parser.add_argument("--context", help="Context")
    add_parser.add_argument("--category", help="Category (for lesson)")
    add_parser.add_argument("--importance", type=float, help="Importance 0-1")
    add_parser.add_argument("--strategy", help="Strategy description")
    add_parser.add_argument("--task-type", help="Task type (for strategy)")
    add_parser.add_argument("--success-rate", type=float, help="Success rate 0-1")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear memory")
    clear_parser.add_argument("type", choices=["context", "all"])

    # Export command
    export_parser = subparsers.add_parser("export", help="Export memory")
    export_parser.add_argument("file", help="Output file")

    # Import command
    import_parser = subparsers.add_parser("import", help="Import memory")
    import_parser.add_argument("file", help="Input file")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    try:
        if args.command == "list":
            cmd_list(args)
        elif args.command == "search":
            cmd_search(args)
        elif args.command == "delete":
            cmd_delete(args)
        elif args.command == "add":
            cmd_add(args)
        elif args.command == "stats":
            cmd_stats(args)
        elif args.command == "clear":
            cmd_clear(args)
        elif args.command == "export":
            cmd_export(args)
        elif args.command == "import":
            cmd_import(args)
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
