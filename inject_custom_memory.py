#!/usr/bin/env python3
"""
Custom Memory Injection Tool
=============================

Tool untuk inject memory custom (lessons, strategies, experiences) ke ChromaDB.

Usage:
    # Interactive mode
    python inject_custom_memory.py

    # Direct injection
    python inject_custom_memory.py --type lesson --data '{"lesson": "...", "context": "..."}'

    # From JSON file
    python inject_custom_memory.py --from-file custom_memory.json
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory_manager import get_memory_manager


def inject_lesson_interactive():
    """Inject lesson secara interaktif"""
    print("\n" + "=" * 70)
    print("INJECT LESSON")
    print("=" * 70 + "\n")

    lesson = input("Lesson text: ").strip()
    if not lesson:
        print("❌ Lesson tidak boleh kosong!")
        return None

    context = input("Context (dimana lesson ini berlaku): ").strip()
    if not context:
        context = "General"

    print("\nCategories: error_prevention, best_practice, security, quality_assurance, optimization, general")
    category = input("Category [general]: ").strip() or "general"

    importance_str = input("Importance (0.0 - 1.0) [0.8]: ").strip() or "0.8"
    try:
        importance = float(importance_str)
        if not 0.0 <= importance <= 1.0:
            importance = 0.8
    except ValueError:
        importance = 0.8

    mem_mgr = get_memory_manager()
    lesson_id = mem_mgr.add_lesson(
        lesson=lesson,
        context=context,
        category=category,
        importance=importance
    )

    print(f"\n✅ Lesson berhasil di-inject!")
    print(f"   ID: {lesson_id}")
    print(f"   Category: {category}")
    print(f"   Importance: {importance}")

    return lesson_id


def inject_strategy_interactive():
    """Inject strategy secara interaktif"""
    print("\n" + "=" * 70)
    print("INJECT STRATEGY")
    print("=" * 70 + "\n")

    strategy = input("Strategy description: ").strip()
    if not strategy:
        print("❌ Strategy tidak boleh kosong!")
        return None

    print("\nTask types: web_development, file_modification, debugging, testing, deployment, security, general")
    task_type = input("Task type [general]: ").strip() or "general"

    success_rate_str = input("Success rate (0.0 - 1.0) [0.9]: ").strip() or "0.9"
    try:
        success_rate = float(success_rate_str)
        if not 0.0 <= success_rate <= 1.0:
            success_rate = 0.9
    except ValueError:
        success_rate = 0.9

    context = input("Additional context (optional): ").strip() or None

    mem_mgr = get_memory_manager()
    strategy_id = mem_mgr.add_strategy(
        strategy=strategy,
        task_type=task_type,
        success_rate=success_rate,
        context=context
    )

    print(f"\n✅ Strategy berhasil di-inject!")
    print(f"   ID: {strategy_id}")
    print(f"   Task Type: {task_type}")
    print(f"   Success Rate: {success_rate:.0%}")

    return strategy_id


def inject_experience_interactive():
    """Inject experience secara interaktif"""
    print("\n" + "=" * 70)
    print("INJECT EXPERIENCE")
    print("=" * 70 + "\n")

    task = input("Task description: ").strip()
    if not task:
        print("❌ Task tidak boleh kosong!")
        return None

    print("\nActions (pisahkan dengan koma, contoh: action1, action2, action3)")
    actions_str = input("Actions: ").strip()
    actions = [a.strip() for a in actions_str.split(',') if a.strip()]

    outcome = input("Outcome: ").strip()
    if not outcome:
        outcome = "Task completed"

    success_str = input("Success? (y/n) [y]: ").strip().lower() or "y"
    success = success_str in ['y', 'yes', 'true', '1']

    # Optional metadata
    print("\nOptional metadata (tekan Enter untuk skip):")
    category = input("  Category: ").strip() or None
    complexity = input("  Complexity (low/medium/high): ").strip() or None

    metadata = {}
    if category:
        metadata['category'] = category
    if complexity:
        metadata['complexity'] = complexity

    mem_mgr = get_memory_manager()
    exp_id = mem_mgr.add_experience(
        task=task,
        actions=actions,
        outcome=outcome,
        success=success,
        metadata=metadata if metadata else None
    )

    print(f"\n✅ Experience berhasil di-inject!")
    print(f"   ID: {exp_id}")
    print(f"   Actions: {len(actions)}")
    print(f"   Success: {success}")

    return exp_id


def inject_from_dict(data_type, data):
    """Inject memory dari dictionary"""
    mem_mgr = get_memory_manager()

    if data_type == "lesson":
        required = ["lesson", "context"]
        if not all(k in data for k in required):
            raise ValueError(f"Lesson requires: {required}")

        lesson_id = mem_mgr.add_lesson(
            lesson=data["lesson"],
            context=data["context"],
            category=data.get("category", "general"),
            importance=data.get("importance", 0.8)
        )
        print(f"✅ Lesson injected: {lesson_id}")
        return lesson_id

    elif data_type == "strategy":
        required = ["strategy", "task_type"]
        if not all(k in data for k in required):
            raise ValueError(f"Strategy requires: {required}")

        strategy_id = mem_mgr.add_strategy(
            strategy=data["strategy"],
            task_type=data["task_type"],
            success_rate=data.get("success_rate", 0.9),
            context=data.get("context")
        )
        print(f"✅ Strategy injected: {strategy_id}")
        return strategy_id

    elif data_type == "experience":
        required = ["task", "actions", "outcome", "success"]
        if not all(k in data for k in required):
            raise ValueError(f"Experience requires: {required}")

        exp_id = mem_mgr.add_experience(
            task=data["task"],
            actions=data["actions"],
            outcome=data["outcome"],
            success=data["success"],
            metadata=data.get("metadata")
        )
        print(f"✅ Experience injected: {exp_id}")
        return exp_id

    else:
        raise ValueError(f"Unknown type: {data_type}")


def inject_from_file(filepath):
    """Inject memory dari JSON file"""
    print(f"\n📂 Loading from: {filepath}\n")

    with open(filepath) as f:
        data = json.load(f)

    counts = {
        "lessons": 0,
        "strategies": 0,
        "experiences": 0
    }

    # Inject lessons
    if "lessons" in data:
        print("📚 Injecting lessons...")
        for lesson_data in data["lessons"]:
            try:
                inject_from_dict("lesson", lesson_data)
                counts["lessons"] += 1
            except Exception as e:
                print(f"  ❌ Failed to inject lesson: {e}")

    # Inject strategies
    if "strategies" in data:
        print("\n🎯 Injecting strategies...")
        for strategy_data in data["strategies"]:
            try:
                inject_from_dict("strategy", strategy_data)
                counts["strategies"] += 1
            except Exception as e:
                print(f"  ❌ Failed to inject strategy: {e}")

    # Inject experiences
    if "experiences" in data:
        print("\n📝 Injecting experiences...")
        for exp_data in data["experiences"]:
            try:
                inject_from_dict("experience", exp_data)
                counts["experiences"] += 1
            except Exception as e:
                print(f"  ❌ Failed to inject experience: {e}")

    print("\n" + "=" * 70)
    print("INJECTION SUMMARY")
    print("=" * 70)
    print(f"  Lessons:     {counts['lessons']}")
    print(f"  Strategies:  {counts['strategies']}")
    print(f"  Experiences: {counts['experiences']}")
    print()

    return counts


def interactive_menu():
    """Menu interaktif"""
    while True:
        print("\n" + "=" * 70)
        print("CUSTOM MEMORY INJECTION")
        print("=" * 70)
        print("\n1. Inject Lesson")
        print("2. Inject Strategy")
        print("3. Inject Experience")
        print("4. Inject from JSON file")
        print("5. Show current statistics")
        print("6. Exit")

        choice = input("\nPilih (1-6): ").strip()

        if choice == "1":
            inject_lesson_interactive()
        elif choice == "2":
            inject_strategy_interactive()
        elif choice == "3":
            inject_experience_interactive()
        elif choice == "4":
            filepath = input("JSON file path: ").strip()
            if Path(filepath).exists():
                inject_from_file(filepath)
            else:
                print(f"❌ File not found: {filepath}")
        elif choice == "5":
            mem_mgr = get_memory_manager()
            stats = mem_mgr.get_all_statistics()
            vm = stats.get('vector_memory', {})
            print("\n📊 Current Statistics:")
            print(f"  Lessons:     {vm.get('total_lessons', 0)}")
            print(f"  Strategies:  {vm.get('total_strategies', 0)}")
            print(f"  Experiences: {vm.get('total_experiences', 0)}")
        elif choice == "6":
            print("\nGoodbye! 👋\n")
            break
        else:
            print("❌ Invalid choice!")


def create_template_file(filepath="custom_memory_template.json"):
    """Create template JSON file"""
    template = {
        "lessons": [
            {
                "lesson": "Always validate input before processing",
                "context": "Security - Input handling",
                "category": "security",
                "importance": 0.9
            },
            {
                "lesson": "Check file existence before read/write operations",
                "context": "File operations - Error prevention",
                "category": "error_prevention",
                "importance": 0.95
            }
        ],
        "strategies": [
            {
                "strategy": "Read file → Validate → Edit → Write → Verify",
                "task_type": "file_modification",
                "success_rate": 0.95,
                "context": "Safe file editing workflow"
            },
            {
                "strategy": "Test locally → Review → Deploy → Monitor",
                "task_type": "deployment",
                "success_rate": 0.9,
                "context": "Production deployment workflow"
            }
        ],
        "experiences": [
            {
                "task": "Fix authentication bug in login system",
                "actions": [
                    "check_logs",
                    "identify_token_expiry",
                    "refresh_token_logic",
                    "verify_auth_success"
                ],
                "outcome": "Successfully fixed auth by implementing token refresh",
                "success": true,
                "metadata": {
                    "category": "debugging",
                    "complexity": "medium",
                    "domain": "authentication"
                }
            }
        ]
    }

    with open(filepath, 'w') as f:
        json.dump(template, f, indent=2)

    print(f"✅ Template created: {filepath}")
    print(f"   Edit this file and use: python {sys.argv[0]} --from-file {filepath}")


def main():
    parser = argparse.ArgumentParser(
        description="Inject custom memory ke ChromaDB agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--type',
        choices=['lesson', 'strategy', 'experience'],
        help='Type of memory to inject'
    )

    parser.add_argument(
        '--data',
        help='JSON string with memory data'
    )

    parser.add_argument(
        '--from-file',
        help='Path to JSON file with memory data'
    )

    parser.add_argument(
        '--create-template',
        action='store_true',
        help='Create template JSON file'
    )

    args = parser.parse_args()

    try:
        if args.create_template:
            create_template_file()

        elif args.from_file:
            inject_from_file(args.from_file)

        elif args.type and args.data:
            data = json.loads(args.data)
            inject_from_dict(args.type, data)

        else:
            # Interactive mode
            interactive_menu()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye! 👋\n")
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
