#!/usr/bin/env python3
"""
Quick Training Dashboard - Show agent learning progress

Usage:
    python show_training_dashboard.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.learning.learning_manager import get_learning_manager
from agent.learning.self_improvement import get_self_improvement_suggester
from agent.state.memory_manager import get_memory_manager


def main():
    learning_mgr = get_learning_manager()
    suggester = get_self_improvement_suggester()
    mem_mgr = get_memory_manager()

    print("\n" + "=" * 70)
    print("AGENT TRAINING DASHBOARD")
    print("=" * 70 + "\n")

    # Memory Statistics
    stats = mem_mgr.get_all_statistics()
    vm = stats.get('vector_memory', {})

    print("📊 MEMORY STATISTICS")
    print("-" * 70)
    print(f"  Experiences:  {vm.get('total_experiences', 0):>6}")
    print(f"  Lessons:      {vm.get('total_lessons', 0):>6}")
    print(f"  Strategies:   {vm.get('total_strategies', 0):>6}")
    print(f"  Backend:      {vm.get('backend', 'unknown'):>6}")
    if vm.get('storage_path'):
        print(f"  Storage:      {vm.get('storage_path')}")

    # Performance Metrics
    learning_stats = learning_mgr.get_learning_statistics()

    print("\n🎯 PERFORMANCE METRICS")
    print("-" * 70)
    print(f"  Success Rate:     {learning_stats.get('overall_success_rate', 0):>6.1%}")
    print(f"  Learning Enabled: {learning_stats.get('learning_enabled', False)}")

    # Performance Analysis
    analysis = suggester.analyze_performance()
    if not analysis.get('error') and analysis.get('total_experiences', 0) > 0:
        efficiency = analysis.get('efficiency_metrics', {})
        if efficiency:
            print(f"  Avg Actions:      {efficiency.get('avg_actions_per_task', 0):>6.1f}")
            print(f"  Efficiency:       {efficiency.get('efficiency_rating', 'unknown'):>6}")

    # Top Suggestions
    suggestions = suggester.get_improvement_suggestions()

    print("\n💡 TOP IMPROVEMENT SUGGESTIONS")
    print("-" * 70)
    if suggestions:
        for i, sug in enumerate(suggestions[:5], 1):
            priority_icon = {
                "critical": "🔴",
                "high": "🟡",
                "medium": "🟢",
                "low": "⚪"
            }.get(sug['priority'], "⚪")

            print(f"\n  {i}. {priority_icon} [{sug['priority'].upper()}] {sug['category']}")
            print(f"     {sug['suggestion']}")
            if 'current_metric' in sug:
                print(f"     {sug['current_metric']}")
    else:
        print("  No suggestions available.")
        print("  Complete more tasks to generate insights.")

    # Error Summary
    error_summary = learning_mgr.get_error_summary()

    print("\n⚠️  ERROR SUMMARY")
    print("-" * 70)
    print(f"  {error_summary}")

    # Quick Actions
    print("\n⚡ QUICK ACTIONS")
    print("-" * 70)
    print("  Run error learning:")
    print("    python -c \"from agent.learning.learning_manager import get_learning_manager; get_learning_manager().learn_from_errors()\"")
    print("\n  Export backup:")
    print("    python -c \"from agent.state.memory_manager import get_memory_manager; from pathlib import Path; get_memory_manager().export_all_memory(Path('backup.json'))\"")
    print("\n  Run all examples:")
    print("    python examples/training_examples.py --example all")

    # Documentation
    print("\n📚 DOCUMENTATION")
    print("-" * 70)
    print("  Full Guide:       docs/CHROMADB_TRAINING_GUIDE.md")
    print("  Quick Reference:  docs/TRAINING_QUICK_REFERENCE.md")
    print("  README:           docs/TRAINING_README.md")
    print("  Examples:         examples/training_examples.py")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
