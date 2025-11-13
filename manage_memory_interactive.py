#!/usr/bin/env python3
"""Interactive Memory Management System.

Interactive CLI untuk mengelola memory AI agent dengan menu-driven interface.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory_manager import get_memory_manager


# ANSI Color codes
class Colors:
    """ANSI color codes untuk terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def clear_screen():
    """Clear terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text):
    """Print colored header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.ENDC}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def format_timestamp(ts_str):
    """Format ISO timestamp."""
    try:
        dt = datetime.fromisoformat(ts_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ts_str


def pause():
    """Pause and wait for user input."""
    input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.ENDC}")


def confirm(message):
    """Ask for confirmation."""
    response = input(f"{Colors.YELLOW}{message} (y/n): {Colors.ENDC}").lower()
    return response == 'y'


class InteractiveMemoryManager:
    """Interactive memory management interface."""

    def __init__(self):
        """Initialize interactive manager."""
        self.manager = get_memory_manager()
        self.running = True

    def show_main_menu(self):
        """Show main menu."""
        clear_screen()
        print_header("RADIRA - Memory Management System")

        print(f"{Colors.BOLD}Main Menu:{Colors.ENDC}\n")
        print(f"  {Colors.CYAN}1.{Colors.ENDC} List Memory")
        print(f"  {Colors.CYAN}2.{Colors.ENDC} Search Memory")
        print(f"  {Colors.CYAN}3.{Colors.ENDC} Add Memory")
        print(f"  {Colors.CYAN}4.{Colors.ENDC} Delete Memory")
        print(f"  {Colors.CYAN}5.{Colors.ENDC} Statistics")
        print(f"  {Colors.CYAN}6.{Colors.ENDC} Export/Import")
        print(f"  {Colors.CYAN}7.{Colors.ENDC} Clear Memory")
        print(f"  {Colors.CYAN}8.{Colors.ENDC} Help")
        print(f"  {Colors.RED}9.{Colors.ENDC} Exit")

        choice = input(f"\n{Colors.BOLD}Select option (1-9): {Colors.ENDC}")
        return choice

    def list_memory_menu(self):
        """List memory menu."""
        clear_screen()
        print_header("List Memory")

        print(f"{Colors.BOLD}Memory Types:{Colors.ENDC}\n")
        print(f"  {Colors.CYAN}1.{Colors.ENDC} Context Memory")
        print(f"  {Colors.CYAN}2.{Colors.ENDC} Experiences")
        print(f"  {Colors.CYAN}3.{Colors.ENDC} Lessons Learned")
        print(f"  {Colors.CYAN}4.{Colors.ENDC} Strategies")
        print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back")

        choice = input(f"\n{Colors.BOLD}Select type (0-4): {Colors.ENDC}")

        if choice == "1":
            self.list_context()
        elif choice == "2":
            self.list_experiences()
        elif choice == "3":
            self.list_lessons()
        elif choice == "4":
            self.list_strategies()

    def list_context(self):
        """List context memory."""
        clear_screen()
        print_header("Context Memory")

        # Ask for filters
        limit = input(f"Limit (default 10): ") or "10"
        status = input(f"Filter by status (success/error/completed/all): ") or "all"

        status_filter = None if status == "all" else status

        try:
            events = self.manager.list_context_memory(
                limit=int(limit),
                status_filter=status_filter
            )

            if not events:
                print_warning("No context events found.")
            else:
                print(f"\n{Colors.BOLD}Found {len(events)} events:{Colors.ENDC}\n")

                for i, event in enumerate(events, 1):
                    status_icon = {
                        "success": f"{Colors.GREEN}✓{Colors.ENDC}",
                        "error": f"{Colors.RED}✗{Colors.ENDC}",
                        "completed": f"{Colors.GREEN}✓{Colors.ENDC}",
                        "incomplete": f"{Colors.YELLOW}○{Colors.ENDC}"
                    }.get(event.get("status", ""), "?")

                    timestamp = format_timestamp(event.get('timestamp', ''))

                    print(f"{Colors.BOLD}{i}. [{timestamp}] {status_icon}{Colors.ENDC}")
                    print(f"   ID: {Colors.CYAN}{event.get('id', 'N/A')}{Colors.ENDC}")
                    print(f"   Command: {event.get('user_command', 'N/A')[:60]}...")
                    print(f"   Action: {Colors.YELLOW}{event.get('ai_action', 'N/A')}{Colors.ENDC}")
                    print(f"   Status: {event.get('status', 'N/A')}")
                    print()

        except Exception as e:
            print_error(f"Failed to list context: {e}")

        pause()

    def list_experiences(self):
        """List experiences."""
        clear_screen()
        print_header("Experiences")

        limit = input(f"Limit (default 10): ") or "10"
        success_only = input(f"Success only? (y/n, default n): ").lower() == 'y'

        try:
            experiences = self.manager.list_experiences(
                limit=int(limit),
                success_only=success_only
            )

            if not experiences:
                print_warning("No experiences found.")
            else:
                print(f"\n{Colors.BOLD}Found {len(experiences)} experiences:{Colors.ENDC}\n")

                for i, exp in enumerate(experiences, 1):
                    success_icon = f"{Colors.GREEN}✓{Colors.ENDC}" if exp.get("success") else f"{Colors.RED}✗{Colors.ENDC}"
                    timestamp = format_timestamp(exp.get('timestamp', ''))

                    print(f"{Colors.BOLD}{i}. [{timestamp}] {success_icon}{Colors.ENDC}")
                    print(f"   Task: {exp.get('task', 'N/A')[:60]}...")
                    print(f"   Actions: {exp.get('action_count', 0)} actions")
                    print(f"   Outcome: {exp.get('outcome', 'N/A')[:60]}...")
                    print()

        except Exception as e:
            print_error(f"Failed to list experiences: {e}")

        pause()

    def list_lessons(self):
        """List lessons."""
        clear_screen()
        print_header("Lessons Learned")

        limit = input(f"Limit (default 10): ") or "10"
        category = input(f"Category filter (leave empty for all): ") or None

        try:
            lessons = self.manager.list_lessons(
                limit=int(limit),
                category=category
            )

            if not lessons:
                print_warning("No lessons found.")
            else:
                print(f"\n{Colors.BOLD}Found {len(lessons)} lessons:{Colors.ENDC}\n")

                for i, lesson in enumerate(lessons, 1):
                    print(f"{Colors.BOLD}{i}. [{Colors.CYAN}{lesson.get('category', 'general')}{Colors.ENDC}{Colors.BOLD}]{Colors.ENDC}")
                    print(f"   {lesson.get('lesson', 'N/A')[:80]}...")
                    print(f"   Context: {lesson.get('context', 'N/A')[:60]}...")
                    print(f"   Importance: {Colors.YELLOW}{lesson.get('importance', 1.0):.1f}{Colors.ENDC}")
                    print()

        except Exception as e:
            print_error(f"Failed to list lessons: {e}")

        pause()

    def list_strategies(self):
        """List strategies."""
        clear_screen()
        print_header("Successful Strategies")

        limit = input(f"Limit (default 10): ") or "10"
        task_type = input(f"Task type filter (leave empty for all): ") or None

        try:
            strategies = self.manager.list_strategies(
                limit=int(limit),
                task_type=task_type
            )

            if not strategies:
                print_warning("No strategies found.")
            else:
                print(f"\n{Colors.BOLD}Found {len(strategies)} strategies:{Colors.ENDC}\n")

                for i, strategy in enumerate(strategies, 1):
                    print(f"{Colors.BOLD}{i}. {Colors.CYAN}{strategy.get('task_type', 'N/A')}{Colors.ENDC}")
                    print(f"   Strategy: {strategy.get('strategy', 'N/A')[:70]}...")
                    print(f"   Success Rate: {Colors.GREEN}{strategy.get('success_rate', 0):.0%}{Colors.ENDC}")
                    print(f"   Usage: {strategy.get('usage_count', 1)} times")
                    print()

        except Exception as e:
            print_error(f"Failed to list strategies: {e}")

        pause()

    def search_memory(self):
        """Search memory."""
        clear_screen()
        print_header("Search Memory")

        query = input(f"{Colors.BOLD}Enter search query: {Colors.ENDC}")

        if not query:
            print_warning("Query cannot be empty.")
            pause()
            return

        limit = input(f"Results per type (default 5): ") or "5"

        try:
            print(f"\n{Colors.CYAN}Searching...{Colors.ENDC}\n")
            results = self.manager.search_all(query, n_results=int(limit))

            # Context results
            if results["context"]:
                print(f"\n{Colors.BOLD}{Colors.BLUE}[Context Memory]{Colors.ENDC}")
                for i, ctx in enumerate(results["context"][:5], 1):
                    print(f"{i}. {Colors.YELLOW}{ctx.get('ai_action', 'N/A')}{Colors.ENDC} - {ctx.get('user_command', '')[:50]}...")

            # Experience results
            if results["experiences"]:
                print(f"\n{Colors.BOLD}{Colors.BLUE}[Experiences]{Colors.ENDC}")
                for i, exp in enumerate(results["experiences"][:5], 1):
                    success = f"{Colors.GREEN}✓{Colors.ENDC}" if exp.get("success") else f"{Colors.RED}✗{Colors.ENDC}"
                    print(f"{i}. {success} {exp.get('task', 'N/A')[:50]}...")

            # Lesson results
            if results["lessons"]:
                print(f"\n{Colors.BOLD}{Colors.BLUE}[Lessons]{Colors.ENDC}")
                for i, lesson in enumerate(results["lessons"][:5], 1):
                    print(f"{i}. {lesson.get('lesson', 'N/A')[:50]}...")

            # Strategy results
            if results["strategies"]:
                print(f"\n{Colors.BOLD}{Colors.BLUE}[Strategies]{Colors.ENDC}")
                for i, strategy in enumerate(results["strategies"][:5], 1):
                    print(f"{i}. {strategy.get('strategy', 'N/A')[:50]}...")

            if not any(results.values()):
                print_warning("No results found.")

        except Exception as e:
            print_error(f"Search failed: {e}")

        pause()

    def add_memory_menu(self):
        """Add memory menu."""
        clear_screen()
        print_header("Add Memory")

        print(f"{Colors.BOLD}Memory Types:{Colors.ENDC}\n")
        print(f"  {Colors.CYAN}1.{Colors.ENDC} Add Experience")
        print(f"  {Colors.CYAN}2.{Colors.ENDC} Add Lesson")
        print(f"  {Colors.CYAN}3.{Colors.ENDC} Add Strategy")
        print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back")

        choice = input(f"\n{Colors.BOLD}Select type (0-3): {Colors.ENDC}")

        if choice == "1":
            self.add_experience()
        elif choice == "2":
            self.add_lesson()
        elif choice == "3":
            self.add_strategy()

    def add_experience(self):
        """Add experience."""
        clear_screen()
        print_header("Add Experience")

        task = input(f"Task description: ")
        if not task:
            print_warning("Task cannot be empty.")
            pause()
            return

        actions = input(f"Actions (comma-separated, optional): ")
        actions_list = [a.strip() for a in actions.split(",")] if actions else []

        outcome = input(f"Outcome: ")
        if not outcome:
            print_warning("Outcome cannot be empty.")
            pause()
            return

        success = input(f"Success? (y/n): ").lower() == 'y'

        try:
            exp_id = self.manager.add_experience(
                task=task,
                actions=actions_list,
                outcome=outcome,
                success=success,
                metadata={}
            )
            print_success(f"Added experience: {exp_id}")
        except Exception as e:
            print_error(f"Failed to add experience: {e}")

        pause()

    def add_lesson(self):
        """Add lesson."""
        clear_screen()
        print_header("Add Lesson")

        lesson = input(f"Lesson text: ")
        if not lesson:
            print_warning("Lesson cannot be empty.")
            pause()
            return

        context = input(f"Context: ")
        if not context:
            print_warning("Context cannot be empty.")
            pause()
            return

        category = input(f"Category (default 'general'): ") or "general"
        importance = input(f"Importance 0-1 (default 1.0): ") or "1.0"

        try:
            lesson_id = self.manager.add_lesson(
                lesson=lesson,
                context=context,
                category=category,
                importance=float(importance)
            )
            print_success(f"Added lesson: {lesson_id}")
        except Exception as e:
            print_error(f"Failed to add lesson: {e}")

        pause()

    def add_strategy(self):
        """Add strategy."""
        clear_screen()
        print_header("Add Strategy")

        strategy = input(f"Strategy description: ")
        if not strategy:
            print_warning("Strategy cannot be empty.")
            pause()
            return

        task_type = input(f"Task type: ")
        if not task_type:
            print_warning("Task type cannot be empty.")
            pause()
            return

        success_rate = input(f"Success rate 0-1 (default 1.0): ") or "1.0"
        context = input(f"Context (optional): ") or None

        try:
            strategy_id = self.manager.add_strategy(
                strategy=strategy,
                task_type=task_type,
                success_rate=float(success_rate),
                context=context
            )
            print_success(f"Added strategy: {strategy_id}")
        except Exception as e:
            print_error(f"Failed to add strategy: {e}")

        pause()

    def delete_memory_menu(self):
        """Delete memory menu."""
        clear_screen()
        print_header("Delete Memory")

        print(f"{Colors.BOLD}Memory Types:{Colors.ENDC}\n")
        print(f"  {Colors.CYAN}1.{Colors.ENDC} Delete Context Event")
        print(f"  {Colors.CYAN}2.{Colors.ENDC} Delete Experience")
        print(f"  {Colors.CYAN}3.{Colors.ENDC} Delete Lesson")
        print(f"  {Colors.CYAN}4.{Colors.ENDC} Delete Strategy")
        print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back")

        choice = input(f"\n{Colors.BOLD}Select type (0-4): {Colors.ENDC}")

        if choice == "0":
            return

        item_id = input(f"\n{Colors.BOLD}Enter item ID: {Colors.ENDC}")

        if not item_id:
            print_warning("ID cannot be empty.")
            pause()
            return

        if not confirm(f"Delete {item_id}?"):
            print_info("Cancelled.")
            pause()
            return

        try:
            success = False
            if choice == "1":
                success = self.manager.delete_context_by_id(item_id)
            elif choice == "2":
                success = self.manager.delete_experience(item_id)
            elif choice == "3":
                success = self.manager.delete_lesson(item_id)
            elif choice == "4":
                success = self.manager.delete_strategy(item_id)

            if success:
                print_success(f"Deleted: {item_id}")
            else:
                print_error(f"Failed to delete: {item_id}")

        except Exception as e:
            print_error(f"Delete failed: {e}")

        pause()

    def show_statistics(self):
        """Show statistics."""
        clear_screen()
        print_header("Memory Statistics")

        try:
            stats = self.manager.get_all_statistics()

            # Context stats
            if "context" in stats:
                ctx_stats = stats["context"]
                print(f"{Colors.BOLD}{Colors.BLUE}[Context Memory]{Colors.ENDC}")
                print(f"  Total Events: {Colors.CYAN}{ctx_stats.get('total_events', 0)}{Colors.ENDC}")
                print(f"  ChromaDB: {Colors.GREEN if ctx_stats.get('chromadb_available') else Colors.RED}{'Available' if ctx_stats.get('chromadb_available') else 'Not Available'}{Colors.ENDC}")

                if "status_breakdown" in ctx_stats:
                    print(f"  Status Breakdown:")
                    for status, count in ctx_stats["status_breakdown"].items():
                        print(f"    • {status}: {count}")

                if "most_common_actions" in ctx_stats:
                    print(f"  Most Common Actions:")
                    for action, count in list(ctx_stats["most_common_actions"].items())[:5]:
                        print(f"    • {action}: {count}")

            # Vector memory stats
            if "vector_memory" in stats and stats["vector_memory"]:
                vm_stats = stats["vector_memory"]
                print(f"\n{Colors.BOLD}{Colors.BLUE}[Vector Memory]{Colors.ENDC}")
                print(f"  Experiences: {Colors.CYAN}{vm_stats.get('total_experiences', 0)}{Colors.ENDC}")
                print(f"  Lessons: {Colors.CYAN}{vm_stats.get('total_lessons', 0)}{Colors.ENDC}")
                print(f"  Strategies: {Colors.CYAN}{vm_stats.get('total_strategies', 0)}{Colors.ENDC}")
                print(f"  Backend: {vm_stats.get('backend', 'N/A')}")
                print(f"  Storage: {vm_stats.get('storage_path', 'N/A')}")

        except Exception as e:
            print_error(f"Failed to get statistics: {e}")

        pause()

    def export_import_menu(self):
        """Export/import menu."""
        clear_screen()
        print_header("Export/Import Memory")

        print(f"{Colors.BOLD}Options:{Colors.ENDC}\n")
        print(f"  {Colors.CYAN}1.{Colors.ENDC} Export Memory")
        print(f"  {Colors.CYAN}2.{Colors.ENDC} Import Memory")
        print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back")

        choice = input(f"\n{Colors.BOLD}Select option (0-2): {Colors.ENDC}")

        if choice == "1":
            self.export_memory()
        elif choice == "2":
            self.import_memory()

    def export_memory(self):
        """Export memory."""
        clear_screen()
        print_header("Export Memory")

        filename = input(f"Output filename (default: memory_backup.json): ") or "memory_backup.json"
        output_file = Path(filename)

        try:
            print(f"\n{Colors.CYAN}Exporting...{Colors.ENDC}")
            if self.manager.export_all_memory(output_file):
                file_size = output_file.stat().st_size / 1024
                print_success(f"Exported to {output_file}")
                print_info(f"File size: {file_size:.1f} KB")
            else:
                print_error("Export failed")

        except Exception as e:
            print_error(f"Export failed: {e}")

        pause()

    def import_memory(self):
        """Import memory."""
        clear_screen()
        print_header("Import Memory")

        filename = input(f"Input filename: ")
        if not filename:
            print_warning("Filename cannot be empty.")
            pause()
            return

        input_file = Path(filename)

        if not input_file.exists():
            print_error(f"File not found: {input_file}")
            pause()
            return

        if not confirm("Import memory? This will add to existing memory."):
            print_info("Cancelled.")
            pause()
            return

        try:
            print(f"\n{Colors.CYAN}Importing...{Colors.ENDC}")
            counts = self.manager.import_memory(input_file)

            print_success("Import complete:")
            print(f"  Experiences: {Colors.CYAN}{counts['experiences']}{Colors.ENDC}")
            print(f"  Lessons: {Colors.CYAN}{counts['lessons']}{Colors.ENDC}")
            print(f"  Strategies: {Colors.CYAN}{counts['strategies']}{Colors.ENDC}")

        except Exception as e:
            print_error(f"Import failed: {e}")

        pause()

    def clear_memory_menu(self):
        """Clear memory menu."""
        clear_screen()
        print_header("Clear Memory")

        print(f"{Colors.RED}{Colors.BOLD}⚠ WARNING: This operation cannot be undone!{Colors.ENDC}\n")

        print(f"{Colors.BOLD}Options:{Colors.ENDC}\n")
        print(f"  {Colors.CYAN}1.{Colors.ENDC} Clear Context Memory")
        print(f"  {Colors.RED}2.{Colors.ENDC} Clear ALL Memory")
        print(f"  {Colors.YELLOW}0.{Colors.ENDC} Back")

        choice = input(f"\n{Colors.BOLD}Select option (0-2): {Colors.ENDC}")

        if choice == "1":
            if confirm("Clear all context memory?"):
                try:
                    if self.manager.clear_all_context():
                        print_success("Context memory cleared")
                    else:
                        print_error("Failed to clear context memory")
                except Exception as e:
                    print_error(f"Clear failed: {e}")
            else:
                print_info("Cancelled.")

        elif choice == "2":
            print_warning("\nThis will delete ALL memory!")
            if confirm("Type 'yes' to confirm"):
                try:
                    results = self.manager.clear_all_memory()
                    print()
                    for mem_type, success in results.items():
                        if success:
                            print_success(f"{mem_type}: Cleared")
                        else:
                            print_error(f"{mem_type}: Failed")
                except Exception as e:
                    print_error(f"Clear failed: {e}")
            else:
                print_info("Cancelled.")

        pause()

    def show_help(self):
        """Show help."""
        clear_screen()
        print_header("Help")

        help_text = f"""
{Colors.BOLD}Memory Management System - Help{Colors.ENDC}

{Colors.CYAN}What is this?{Colors.ENDC}
This tool manages all memory stored by the AI agent, including:
- Context Memory: Tracking of AI actions and decisions
- Experiences: Task execution history
- Lessons Learned: Knowledge extracted from experiences
- Strategies: Successful approaches to tasks

{Colors.CYAN}Main Features:{Colors.ENDC}
1. List Memory - View memory with filters
2. Search Memory - Semantic search across all types
3. Add Memory - Manually add experiences, lessons, strategies
4. Delete Memory - Remove specific memory items
5. Statistics - View memory statistics
6. Export/Import - Backup and restore memory
7. Clear Memory - Remove old or all memory

{Colors.CYAN}Tips:{Colors.ENDC}
- Export memory regularly for backup
- Use search to find specific information
- Clear old context to save space
- Review statistics to monitor memory usage

{Colors.CYAN}Keyboard Shortcuts:{Colors.ENDC}
- Ctrl+C: Cancel current operation
- Enter: Continue after viewing results
        """

        print(help_text)
        pause()

    def run(self):
        """Run interactive interface."""
        try:
            while self.running:
                choice = self.show_main_menu()

                if choice == "1":
                    self.list_memory_menu()
                elif choice == "2":
                    self.search_memory()
                elif choice == "3":
                    self.add_memory_menu()
                elif choice == "4":
                    self.delete_memory_menu()
                elif choice == "5":
                    self.show_statistics()
                elif choice == "6":
                    self.export_import_menu()
                elif choice == "7":
                    self.clear_memory_menu()
                elif choice == "8":
                    self.show_help()
                elif choice == "9":
                    if confirm("Exit Memory Management System?"):
                        self.running = False
                        clear_screen()
                        print_success("Goodbye!")
                        print()
                else:
                    print_warning("Invalid option. Please try again.")
                    pause()

        except KeyboardInterrupt:
            clear_screen()
            print_warning("\nInterrupted by user. Exiting...")
            print()


def main():
    """Main entry point."""
    app = InteractiveMemoryManager()
    app.run()


if __name__ == "__main__":
    main()
