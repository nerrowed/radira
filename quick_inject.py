#!/usr/bin/env python3
"""
Quick Inject - Inject memory dengan satu baris command

Usage:
    # Inject lesson
    python quick_inject.py lesson "Always validate input" "Security"

    # Inject strategy
    python quick_inject.py strategy "Step1 → Step2 → Step3" "web_dev"

    # Inject experience
    python quick_inject.py exp "Fixed bug" "check,fix,test" "Success" --success

Examples:
    python quick_inject.py lesson "Use HTTPS in production" "Web security" --category security --importance 1.0
    python quick_inject.py strategy "Test → Deploy → Monitor" "deployment" --rate 0.9
    python quick_inject.py exp "Create login page" "design,code,test" "Page created" --success
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory_manager import get_memory_manager


def inject_lesson(lesson, context, category="general", importance=0.8):
    """Quick inject lesson"""
    mem_mgr = get_memory_manager()

    lesson_id = mem_mgr.add_lesson(
        lesson=lesson,
        context=context,
        category=category,
        importance=float(importance)
    )

    print(f"✅ Lesson injected: {lesson_id}")
    print(f"   Text: {lesson[:60]}...")
    print(f"   Context: {context}")
    print(f"   Category: {category}")
    print(f"   Importance: {importance}")

    return lesson_id


def inject_strategy(strategy, task_type, success_rate=0.9, context=None):
    """Quick inject strategy"""
    mem_mgr = get_memory_manager()

    strategy_id = mem_mgr.add_strategy(
        strategy=strategy,
        task_type=task_type,
        success_rate=float(success_rate),
        context=context
    )

    print(f"✅ Strategy injected: {strategy_id}")
    print(f"   Strategy: {strategy[:60]}...")
    print(f"   Task Type: {task_type}")
    print(f"   Success Rate: {success_rate:.0%}")

    return strategy_id


def inject_experience(task, actions_str, outcome, success=True, category=None):
    """Quick inject experience"""
    mem_mgr = get_memory_manager()

    # Parse actions
    actions = [a.strip() for a in actions_str.split(',')]

    # Build metadata
    metadata = {}
    if category:
        metadata['category'] = category

    exp_id = mem_mgr.add_experience(
        task=task,
        actions=actions,
        outcome=outcome,
        success=success,
        metadata=metadata if metadata else None
    )

    print(f"✅ Experience injected: {exp_id}")
    print(f"   Task: {task[:60]}...")
    print(f"   Actions: {len(actions)}")
    print(f"   Success: {success}")

    return exp_id


def main():
    parser = argparse.ArgumentParser(
        description="Quick inject memory ke ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Type of memory to inject')

    # Lesson command
    lesson_parser = subparsers.add_parser('lesson', help='Inject lesson')
    lesson_parser.add_argument('lesson', help='Lesson text')
    lesson_parser.add_argument('context', help='Context where this applies')
    lesson_parser.add_argument('--category', default='general', help='Category (default: general)')
    lesson_parser.add_argument('--importance', type=float, default=0.8, help='Importance 0.0-1.0 (default: 0.8)')

    # Strategy command
    strategy_parser = subparsers.add_parser('strategy', help='Inject strategy')
    strategy_parser.add_argument('strategy', help='Strategy description')
    strategy_parser.add_argument('task_type', help='Task type')
    strategy_parser.add_argument('--rate', type=float, default=0.9, help='Success rate 0.0-1.0 (default: 0.9)')
    strategy_parser.add_argument('--context', help='Additional context')

    # Experience command
    exp_parser = subparsers.add_parser('exp', help='Inject experience')
    exp_parser.add_argument('task', help='Task description')
    exp_parser.add_argument('actions', help='Actions (comma-separated)')
    exp_parser.add_argument('outcome', help='Outcome description')
    exp_parser.add_argument('--success', action='store_true', help='Mark as successful')
    exp_parser.add_argument('--failed', action='store_true', help='Mark as failed')
    exp_parser.add_argument('--category', help='Category')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'lesson':
            inject_lesson(
                args.lesson,
                args.context,
                args.category,
                args.importance
            )

        elif args.command == 'strategy':
            inject_strategy(
                args.strategy,
                args.task_type,
                args.rate,
                args.context
            )

        elif args.command == 'exp':
            # Default success=True unless --failed specified
            success = not args.failed if args.failed else True

            inject_experience(
                args.task,
                args.actions,
                args.outcome,
                success,
                args.category
            )

        print("\n✓ Done!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
