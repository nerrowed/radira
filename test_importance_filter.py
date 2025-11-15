#!/usr/bin/env python3
"""Test script for Task Importance Filter.

This script tests various task scenarios to ensure the filter correctly
identifies trivial vs. meaningful tasks.
"""

from agent.learning.task_importance_filter import get_task_importance_filter, ImportanceLevel


def test_trivial_tasks():
    """Test that trivial tasks are correctly filtered."""
    filter = get_task_importance_filter()

    print("=" * 70)
    print("TESTING TRIVIAL TASKS (should NOT trigger learning)")
    print("=" * 70)

    trivial_tasks = [
        # Short confirmations
        ("ya", [], "OK", True, []),
        ("oke", [], "Baik", True, []),
        ("lanjut", [], "Melanjutkan", True, []),
        ("no 1 menarik", [], "Pilihan 1 dipilih", True, []),

        # Greetings
        ("halo", [], "Halo! Ada yang bisa saya bantu?", True, []),
        ("hello", [], "Hello! How can I help?", True, []),
        ("terima kasih", [], "Sama-sama!", True, []),

        # Simple yes/no
        ("yes", [], "Understood", True, []),
        ("no", [], "OK", True, []),

        # Very short tasks
        ("ok", [], "OK", True, []),
        ("gas", [], "Lanjut", True, []),
    ]

    for task, actions, outcome, success, errors in trivial_tasks:
        should_learn, importance, reason = filter.should_learn(
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            errors=errors
        )

        status = "✓ PASS" if not should_learn else "✗ FAIL"
        print(f"\n{status}: '{task}'")
        print(f"  Should Learn: {should_learn}")
        print(f"  Importance: {importance.value}")
        print(f"  Reason: {reason}")


def test_meaningful_tasks():
    """Test that meaningful tasks are correctly identified."""
    filter = get_task_importance_filter()

    print("\n" + "=" * 70)
    print("TESTING MEANINGFUL TASKS (SHOULD trigger learning)")
    print("=" * 70)

    meaningful_tasks = [
        # Multi-step tasks
        (
            "Create a web page with login form",
            ["create_file", "write_html", "write_css"],
            "Created login.html with form and styling",
            True,
            []
        ),

        # Complex problem solving
        (
            "Fix the authentication bug in user_service.py",
            ["read_file", "analyze_code", "write_file", "test"],
            "Bug fixed: JWT token validation now works",
            True,
            []
        ),

        # Tasks with errors (learning opportunity)
        (
            "Install missing dependencies",
            ["terminal_pip_install"],
            "Failed to install",
            False,
            ["Permission denied"]
        ),

        # Multi-sentence complex task
        (
            "Search for the latest security vulnerabilities in our codebase. "
            "Then create a report with recommendations.",
            ["search", "analyze", "create_file", "write_report"],
            "Security report created with 5 recommendations",
            True,
            []
        ),

        # Technical task with multiple actions
        (
            "Implement binary search algorithm in Python",
            ["create_file", "write_code", "test", "refactor"],
            "Binary search implemented and tested",
            True,
            []
        ),
    ]

    for task, actions, outcome, success, errors in meaningful_tasks:
        should_learn, importance, reason = filter.should_learn(
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            errors=errors
        )

        status = "✓ PASS" if should_learn else "✗ FAIL"
        print(f"\n{status}: '{task[:60]}...'")
        print(f"  Should Learn: {should_learn}")
        print(f"  Importance: {importance.value}")
        print(f"  Reason: {reason}")
        print(f"  Actions: {len(actions)}")


def test_edge_cases():
    """Test edge cases."""
    filter = get_task_importance_filter()

    print("\n" + "=" * 70)
    print("TESTING EDGE CASES")
    print("=" * 70)

    edge_cases = [
        # Short technical task (should learn due to technical content)
        (
            "fix bug",
            ["edit_file"],
            "Bug fixed",
            True,
            [],
            True  # Should learn
        ),

        # Simple QA with no actions (should NOT learn)
        (
            "what is python?",
            [],
            "Python is a programming language",
            True,
            [],
            False  # Should NOT learn
        ),

        # Conversational with technical term (borderline)
        (
            "explain how API works",
            [],
            "API explanation...",
            True,
            [],
            False  # Should NOT learn (no actions)
        ),

        # Task with errors (should learn)
        (
            "read config.json",
            ["read_file"],
            "File not found",
            False,
            ["FileNotFoundError"],
            True  # Should learn from error
        ),
    ]

    for task, actions, outcome, success, errors, expected in edge_cases:
        should_learn, importance, reason = filter.should_learn(
            task=task,
            actions=actions,
            outcome=outcome,
            success=success,
            errors=errors
        )

        status = "✓ PASS" if (should_learn == expected) else "✗ FAIL"
        print(f"\n{status}: '{task}'")
        print(f"  Expected: {expected}, Got: {should_learn}")
        print(f"  Importance: {importance.value}")
        print(f"  Reason: {reason}")


def main():
    """Run all tests."""
    print("\n🧪 TASK IMPORTANCE FILTER TEST SUITE\n")

    test_trivial_tasks()
    test_meaningful_tasks()
    test_edge_cases()

    print("\n" + "=" * 70)
    print("✅ TEST SUITE COMPLETE")
    print("=" * 70)
    print("\nManually review the results above to ensure:")
    print("1. Trivial tasks (confirmations, greetings) are NOT learned")
    print("2. Meaningful tasks (multi-step, technical) ARE learned")
    print("3. Edge cases behave as expected")
    print()


if __name__ == "__main__":
    main()
