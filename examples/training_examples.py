#!/usr/bin/env python3
"""
Contoh Praktis - Metode Training ChromaDB Agent
================================================

File ini berisi contoh-contoh praktis yang bisa langsung dijalankan
untuk melatih agent menggunakan berbagai metode.

Usage:
    python examples/training_examples.py --example <example_name>

Examples:
    - bootstrap       : Bootstrap agent dengan domain knowledge
    - learn_task      : Belajar dari task execution
    - error_learning  : Belajar dari error patterns
    - retrieval       : Retrieve pengalaman relevan
    - monitoring      : Monitor learning progress
    - backup          : Backup dan restore memory
    - dashboard       : Tampilkan learning dashboard
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce ChromaDB verbose logging
logging.getLogger("chromadb.api.segment").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)


def example_bootstrap():
    """Example 1: Bootstrap agent dengan domain knowledge"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Bootstrap Agent dengan Domain Knowledge")
    print("=" * 70 + "\n")

    from agent.state.memory_manager import get_memory_manager

    mem_mgr = get_memory_manager()

    # Inject lessons untuk web development
    print("📚 Injecting web development lessons...\n")

    lessons = [
        {
            "lesson": "Always validate HTML syntax before deployment",
            "context": "Web development - HTML files",
            "category": "quality_assurance",
            "importance": 0.9
        },
        {
            "lesson": "Include viewport meta tag for mobile responsiveness",
            "context": "Web development - Mobile-first design",
            "category": "best_practice",
            "importance": 0.8
        },
        {
            "lesson": "Sanitize user input to prevent XSS attacks",
            "context": "Web security - Input handling",
            "category": "security",
            "importance": 1.0
        },
        {
            "lesson": "Use semantic HTML5 tags for better SEO",
            "context": "Web development - SEO optimization",
            "category": "best_practice",
            "importance": 0.7
        },
        {
            "lesson": "Always check file existence before read/write operations",
            "context": "File operations - Error prevention",
            "category": "error_prevention",
            "importance": 0.95
        }
    ]

    for lesson_data in lessons:
        lesson_id = mem_mgr.add_lesson(**lesson_data)
        print(f"✓ Added lesson: {lesson_data['lesson'][:60]}...")
        print(f"  ID: {lesson_id}")
        print(f"  Category: {lesson_data['category']} | Importance: {lesson_data['importance']}\n")

    # Inject strategies
    print("\n🎯 Injecting successful strategies...\n")

    strategies = [
        {
            "strategy": "Create HTML structure → Add CSS styling → Add JavaScript → Test in browser",
            "task_type": "web_page_creation",
            "success_rate": 0.9,
            "context": "Standard web development workflow"
        },
        {
            "strategy": "Read file → Validate syntax → Make changes → Write file → Verify",
            "task_type": "file_modification",
            "success_rate": 0.95,
            "context": "Safe file editing workflow"
        },
        {
            "strategy": "Search documentation → Try solution → Verify result → Document learning",
            "task_type": "problem_solving",
            "success_rate": 0.85,
            "context": "General problem-solving approach"
        }
    ]

    for strategy_data in strategies:
        strategy_id = mem_mgr.add_strategy(**strategy_data)
        print(f"✓ Added strategy for: {strategy_data['task_type']}")
        print(f"  Strategy: {strategy_data['strategy']}")
        print(f"  Success Rate: {strategy_data['success_rate']:.0%}")
        print(f"  ID: {strategy_id}\n")

    # Show statistics
    stats = mem_mgr.get_all_statistics()
    print("\n📊 Updated Memory Statistics:")
    print(f"  Lessons: {stats['vector_memory'].get('total_lessons', 0)}")
    print(f"  Strategies: {stats['vector_memory'].get('total_strategies', 0)}")
    print("\n✓ Bootstrap completed successfully!\n")


def example_learn_from_task():
    """Example 2: Belajar dari task execution"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Belajar dari Task Execution")
    print("=" * 70 + "\n")

    from agent.learning.learning_manager import get_learning_manager

    learning_mgr = get_learning_manager()

    # Simulate successful task
    print("📝 Simulating successful task execution...\n")

    task_data = {
        "task": "Create responsive landing page with hero section and contact form",
        "actions": [
            "create_file: landing.html",
            "add_html_structure: HTML5 boilerplate",
            "create_file: styles.css",
            "add_css_styling: Responsive grid layout",
            "add_viewport_meta: Mobile optimization",
            "add_hero_section: Hero with background image",
            "add_contact_form: Form with validation",
            "test_responsiveness: Desktop and mobile",
            "validate_html: W3C validator"
        ],
        "outcome": "Successfully created responsive landing page. All validations passed. Works on desktop, tablet, and mobile.",
        "success": True,
        "errors": [],
        "context": {
            "task_type": "web_development",
            "complexity": "medium",
            "technologies": ["HTML5", "CSS3"],
            "duration_minutes": 15
        }
    }

    summary = learning_mgr.learn_from_task(**task_data)

    print("✓ Task learning completed!\n")
    print("📊 Learning Summary:")
    print(f"  Experience ID: {summary['experience_id']}")
    print(f"  Lessons Learned: {summary['lessons_count']}")
    print(f"  Strategies Stored: {summary['strategies_count']}")
    print(f"  Timestamp: {summary['timestamp']}")

    if summary.get('improvements_suggested'):
        print("\n💡 Suggested Improvements:")
        for improvement in summary['improvements_suggested']:
            print(f"  - {improvement}")

    # Simulate failed task
    print("\n" + "-" * 70)
    print("📝 Simulating failed task execution...\n")

    failed_task_data = {
        "task": "Deploy website to production server",
        "actions": [
            "connect_to_server: SSH connection",
            "upload_files: FTP transfer",
            "restart_server: Nginx restart"
        ],
        "outcome": "Failed to deploy. Permission denied error.",
        "success": False,
        "errors": [
            "Permission denied: /var/www/html",
            "SSH connection timed out after retry"
        ],
        "context": {
            "task_type": "deployment",
            "complexity": "high",
            "error_type": "permission_error"
        }
    }

    summary2 = learning_mgr.learn_from_task(**failed_task_data)

    print("✓ Failed task learning completed!\n")
    print("📊 Learning Summary:")
    print(f"  Experience ID: {summary2['experience_id']}")
    print(f"  Lessons Learned: {summary2['lessons_count']}")

    print("\n✓ Learning from both success and failure completed!\n")


def example_error_learning():
    """Example 3: Belajar dari error patterns"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Error-Driven Learning")
    print("=" * 70 + "\n")

    from agent.learning.learning_manager import get_learning_manager

    learning_mgr = get_learning_manager()

    # Analyze error patterns
    print("🔍 Analyzing error patterns from last 30 days...\n")

    error_analysis = learning_mgr.analyze_error_patterns(
        tool_name=None,  # All tools
        time_window_days=30
    )

    print("📊 Error Analysis Results:")
    print(f"  Total Errors: {error_analysis.get('total_errors', 0)}")

    if error_analysis.get('top_error_types'):
        print("\n  Top Error Types:")
        for error_type, count in error_analysis['top_error_types'].items():
            print(f"    - {error_type}: {count} occurrences")

    if error_analysis.get('recommendations'):
        print("\n  Recommendations:")
        for i, rec in enumerate(error_analysis['recommendations'][:5], 1):
            print(f"\n  {i}. [{rec.get('severity', 'unknown').upper()}] {rec.get('message', '')}")
            if rec.get('action'):
                print(f"     Action: {rec['action']}")

    # Learn from errors
    print("\n" + "-" * 70)
    print("📚 Converting error patterns into lessons...\n")

    learning_result = learning_mgr.learn_from_errors()

    print("✓ Error learning completed!\n")
    print("📊 Results:")
    print(f"  Lessons Created: {learning_result.get('lessons_created', 0)}")
    print(f"  Prevention Strategies: {learning_result.get('strategies_created', 0)}")
    print(f"  Errors Analyzed: {learning_result.get('total_errors_analyzed', 0)}")

    # Get error summary
    print("\n" + "-" * 70)
    print("📋 Error Memory Summary:\n")
    error_summary = learning_mgr.get_error_summary()
    print(error_summary)

    print("\n✓ Error-driven learning completed!\n")


def example_retrieval():
    """Example 4: Retrieve pengalaman relevan"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Retrieval-Augmented Learning")
    print("=" * 70 + "\n")

    from agent.learning.learning_manager import get_learning_manager

    learning_mgr = get_learning_manager()

    # Query for relevant experience
    queries = [
        "Create a website with HTML and CSS",
        "Fix permission error on Linux server",
        "Validate user input in web form"
    ]

    for query in queries:
        print(f"🔍 Query: '{query}'\n")

        insights = learning_mgr.get_relevant_experience(
            current_task=query,
            n_results=3
        )

        # Similar experiences
        if insights.get('similar_experiences'):
            print("  📚 Similar Past Experiences:")
            for i, exp in enumerate(insights['similar_experiences'], 1):
                print(f"\n    {i}. {exp.get('task', 'Unknown task')[:60]}...")
                print(f"       Success: {'✓' if exp.get('success') else '✗'}")
                print(f"       Actions: {exp.get('action_count', 0)}")

        # Relevant lessons
        if insights.get('relevant_lessons'):
            print("\n  💡 Relevant Lessons:")
            for i, lesson in enumerate(insights['relevant_lessons'][:3], 1):
                print(f"\n    {i}. {lesson.get('lesson', '')[:60]}...")
                print(f"       Category: {lesson.get('category', 'unknown')}")
                print(f"       Importance: {lesson.get('importance', 0):.1f}")

        # Recommended strategies
        if insights.get('recommended_strategies'):
            print("\n  🎯 Recommended Strategies:")
            for i, strategy in enumerate(insights['recommended_strategies'][:2], 1):
                print(f"\n    {i}. {strategy.get('strategy', '')[:60]}...")
                print(f"       Success Rate: {strategy.get('success_rate', 0):.0%}")

        # Experience summary
        summary = insights.get('experience_summary', {})
        if summary and summary.get('total_count', 0) > 0:
            print("\n  📊 Experience Summary:")
            print(f"    Total Similar: {summary.get('total_count', 0)}")
            print(f"    Success Rate: {summary.get('success_rate', 0):.0%}")

        print("\n" + "-" * 70 + "\n")

    print("✓ Retrieval examples completed!\n")


def example_monitoring():
    """Example 5: Monitor learning progress"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: Monitoring Learning Progress")
    print("=" * 70 + "\n")

    from agent.learning.learning_manager import get_learning_manager
    from agent.learning.self_improvement import get_self_improvement_suggester

    learning_mgr = get_learning_manager()
    suggester = get_self_improvement_suggester()

    # Get statistics
    print("📊 Learning Statistics:\n")

    stats = learning_mgr.get_learning_statistics()

    print(f"  Total Experiences: {stats.get('total_experiences', 0)}")
    print(f"  Total Lessons: {stats.get('total_lessons', 0)}")
    print(f"  Total Strategies: {stats.get('total_strategies', 0)}")
    print(f"  Overall Success Rate: {stats.get('overall_success_rate', 0):.1%}")
    print(f"  Learning Enabled: {stats.get('learning_enabled', False)}")
    print(f"  Backend: {stats.get('memory_backend', 'unknown')}")

    # Performance analysis
    print("\n" + "-" * 70)
    print("🎯 Performance Analysis:\n")

    analysis = suggester.analyze_performance()

    if not analysis.get('error') and analysis.get('total_experiences', 0) > 0:
        print(f"  Total Experiences: {analysis['total_experiences']}")
        print(f"  Successful: {analysis.get('successful', 0)}")
        print(f"  Failed: {analysis.get('failed', 0)}")
        print(f"  Success Rate: {analysis.get('success_rate', 0):.1%}")

        # Efficiency metrics
        efficiency = analysis.get('efficiency_metrics', {})
        if efficiency:
            print(f"\n  Efficiency Metrics:")
            print(f"    Avg Actions per Task: {efficiency.get('avg_actions_per_task', 0):.1f}")
            print(f"    Avg Actions (Success): {efficiency.get('avg_actions_when_successful', 0):.1f}")
            print(f"    Avg Actions (Failed): {efficiency.get('avg_actions_when_failed', 0):.1f}")
            print(f"    Efficiency Rating: {efficiency.get('efficiency_rating', 'unknown').upper()}")
    else:
        print("  Not enough data for analysis. Complete more tasks to see insights.")

    # Improvement suggestions
    print("\n" + "-" * 70)
    print("💡 Improvement Suggestions:\n")

    suggestions = suggester.get_improvement_suggestions()

    if suggestions:
        for i, sug in enumerate(suggestions, 1):
            priority_icon = {
                "critical": "🔴",
                "high": "🟡",
                "medium": "🟢",
                "low": "⚪"
            }.get(sug['priority'], "⚪")

            print(f"  {i}. {priority_icon} [{sug['priority'].upper()}] {sug['category']}")
            print(f"     {sug['suggestion']}")
            if 'current_metric' in sug:
                print(f"     Current: {sug['current_metric']}")
            if 'occurrences' in sug:
                print(f"     Occurrences: {sug['occurrences']}")
            print()
    else:
        print("  No specific suggestions at this time.")

    print("✓ Monitoring completed!\n")


def example_backup():
    """Example 6: Backup dan restore memory"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Backup & Restore Memory")
    print("=" * 70 + "\n")

    from agent.state.memory_manager import get_memory_manager

    mem_mgr = get_memory_manager()

    # Create backups directory
    backup_dir = Path("backups")
    backup_dir.mkdir(exist_ok=True)

    # Export all memory
    print("💾 Exporting all memory...\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"agent_memory_{timestamp}.json"

    success = mem_mgr.export_all_memory(backup_file)

    if success:
        print(f"✓ Memory exported successfully!")
        print(f"  File: {backup_file}")
        print(f"  Size: {backup_file.stat().st_size / 1024:.1f} KB")

        # Show what was exported
        import json
        with open(backup_file) as f:
            data = json.load(f)

        print(f"\n  Exported:")
        print(f"    Experiences: {len(data.get('experiences', []))}")
        print(f"    Lessons: {len(data.get('lessons', []))}")
        print(f"    Strategies: {len(data.get('strategies', []))}")
        print(f"    Export Time: {data.get('exported_at', 'unknown')}")
    else:
        print("✗ Export failed!")

    # Import example (commented out to avoid duplication)
    print("\n" + "-" * 70)
    print("📥 Import Example (not executed):\n")
    print("  To import from backup:")
    print(f"  counts = mem_mgr.import_memory(Path('{backup_file}'))")
    print(f"  print(f\"Imported: {{counts['experiences']}} experiences\")")

    print("\n✓ Backup example completed!\n")


def example_dashboard():
    """Example 7: Learning dashboard"""
    print("\n" + "=" * 70)
    print("AGENT LEARNING DASHBOARD")
    print("=" * 70 + "\n")

    from agent.learning.learning_manager import get_learning_manager
    from agent.learning.self_improvement import get_self_improvement_suggester
    from agent.state.memory_manager import get_memory_manager

    learning_mgr = get_learning_manager()
    suggester = get_self_improvement_suggester()
    mem_mgr = get_memory_manager()

    # Memory Statistics
    stats = mem_mgr.get_all_statistics()
    vm = stats.get('vector_memory', {})

    print("📊 MEMORY STATISTICS")
    print("-" * 70)
    print(f"  Experiences:  {vm.get('total_experiences', 0):>6}")
    print(f"  Lessons:      {vm.get('total_lessons', 0):>6}")
    print(f"  Strategies:   {vm.get('total_strategies', 0):>6}")
    print(f"  Backend:      {vm.get('backend', 'unknown'):>6}")
    print(f"  Storage:      {vm.get('storage_path', 'unknown')}")

    # Performance Metrics
    learning_stats = learning_mgr.get_learning_statistics()

    print("\n🎯 PERFORMANCE METRICS")
    print("-" * 70)
    print(f"  Success Rate:     {learning_stats.get('overall_success_rate', 0):>6.1%}")
    print(f"  Learning Enabled: {learning_stats.get('learning_enabled', False)}")

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
        print("  No suggestions available. Complete more tasks to generate insights.")

    # Error Summary
    error_summary = learning_mgr.get_error_summary()

    print("\n⚠️  ERROR SUMMARY")
    print("-" * 70)
    print(f"  {error_summary}")

    # Quick Actions
    print("\n⚡ QUICK ACTIONS")
    print("-" * 70)
    print("  1. Run error learning:  learning_mgr.learn_from_errors()")
    print("  2. Export backup:       mem_mgr.export_all_memory(Path('backup.json'))")
    print("  3. View statistics:     learning_mgr.get_learning_statistics()")
    print("  4. Get suggestions:     suggester.get_improvement_suggestions()")

    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="ChromaDB Training Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--example',
        choices=[
            'bootstrap',
            'learn_task',
            'error_learning',
            'retrieval',
            'monitoring',
            'backup',
            'dashboard',
            'all'
        ],
        default='dashboard',
        help='Which example to run (default: dashboard)'
    )

    args = parser.parse_args()

    examples = {
        'bootstrap': example_bootstrap,
        'learn_task': example_learn_from_task,
        'error_learning': example_error_learning,
        'retrieval': example_retrieval,
        'monitoring': example_monitoring,
        'backup': example_backup,
        'dashboard': example_dashboard
    }

    if args.example == 'all':
        # Run all examples
        for name, func in examples.items():
            try:
                func()
                input("\nPress Enter to continue to next example...")
            except KeyboardInterrupt:
                print("\n\nExamples interrupted by user.")
                sys.exit(0)
            except Exception as e:
                logger.error(f"Error in {name}: {e}")
                import traceback
                traceback.print_exc()
    else:
        # Run specific example
        try:
            examples[args.example]()
        except Exception as e:
            logger.error(f"Error running example: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
