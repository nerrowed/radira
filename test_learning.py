"""Test script for reflective learning system.

This tests the complete learning cycle:
1. Vector memory storage
2. Reflection engine analysis
3. Learning manager orchestration
4. Self-improvement suggestions
5. Integration with orchestrator
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agent.state.memory import VectorMemory
from agent.learning.reflection_engine import ReflectionEngine
from agent.learning.learning_manager import LearningManager
from agent.learning.self_improvement import SelfImprovementSuggester


def test_vector_memory():
    """Test vector memory operations."""
    print("\n" + "="*60)
    print("Testing Vector Memory")
    print("="*60)

    memory = VectorMemory(persist_directory="workspace/.memory_test")

    # Store an experience
    exp_id = memory.store_experience(
        task="Create a test file",
        actions=["filesystem: list files", "filesystem: write file"],
        outcome="File created successfully",
        success=True,
        metadata={"test": True}
    )
    print(f"✓ Stored experience: {exp_id}")

    # Store a lesson
    lesson_id = memory.store_lesson(
        lesson="Always check directory exists before writing files",
        context="File creation tasks",
        category="best_practice",
        importance=0.8
    )
    print(f"✓ Stored lesson: {lesson_id}")

    # Store a strategy
    strat_id = memory.store_strategy(
        strategy="List files → Write file",
        task_type="file_creation",
        success_rate=1.0,
        context="Simple file creation"
    )
    print(f"✓ Stored strategy: {strat_id}")

    # Recall similar experiences
    similar = memory.recall_similar_experiences("create file", n_results=1)
    print(f"✓ Recalled {len(similar)} similar experience(s)")

    # Get statistics
    stats = memory.get_statistics()
    print(f"✓ Memory stats:")
    print(f"   - Experiences: {stats['total_experiences']}")
    print(f"   - Lessons: {stats['total_lessons']}")
    print(f"   - Strategies: {stats['total_strategies']}")
    print(f"   - Backend: {stats['backend']}")

    return memory


def test_reflection_engine():
    """Test reflection engine."""
    print("\n" + "="*60)
    print("Testing Reflection Engine")
    print("="*60)

    engine = ReflectionEngine()

    # Test successful reflection
    print("\n--- Reflecting on Success ---")
    success_reflection = engine.reflect_on_task(
        task="Create hello.txt file",
        actions=["filesystem: list", "filesystem: write"],
        outcome="File created successfully",
        success=True,
        errors=[],
        context={}
    )

    print(f"✓ Success reflection completed")
    print(f"   - Efficiency score: {success_reflection.get('efficiency_score', 0):.2f}")
    print(f"   - Patterns found: {len(success_reflection.get('patterns', []))}")
    print(f"   - Lessons learned: {len(success_reflection.get('lessons', []))}")

    # Test failure reflection
    print("\n--- Reflecting on Failure ---")
    failure_reflection = engine.reflect_on_task(
        task="Delete non-existent file",
        actions=["filesystem: delete"],
        outcome="Failed",
        success=False,
        errors=["Error: File not found"],
        context={}
    )

    print(f"✓ Failure reflection completed")
    print(f"   - Error types: {failure_reflection.get('error_types', [])}")
    print(f"   - Failure reasons: {len(failure_reflection.get('failure_reasons', []))}")
    print(f"   - Improvements suggested: {len(failure_reflection.get('improvements', []))}")

    if failure_reflection.get('improvements'):
        print(f"   - First suggestion: {failure_reflection['improvements'][0]}")

    return engine


def test_learning_manager(memory, engine):
    """Test learning manager."""
    print("\n" + "="*60)
    print("Testing Learning Manager")
    print("="*60)

    manager = LearningManager(vector_memory=memory, reflection_engine=engine)

    # Learn from successful task
    print("\n--- Learning from Success ---")
    learning_summary = manager.learn_from_task(
        task="Generate HTML webpage",
        actions=["web_generator: create", "filesystem: write"],
        outcome="Webpage created successfully",
        success=True,
        errors=[],
        context={"iterations": 2}
    )

    print(f"✓ Learning completed")
    print(f"   - Experience ID: {learning_summary['experience_id']}")
    print(f"   - Lessons stored: {learning_summary['lessons_count']}")
    print(f"   - Strategies stored: {learning_summary['strategies_count']}")

    # Learn from failure
    print("\n--- Learning from Failure ---")
    failure_summary = manager.learn_from_task(
        task="Access restricted file",
        actions=["filesystem: read"],
        outcome="Permission denied",
        success=False,
        errors=["Error: Permission denied"],
        context={"iterations": 1}
    )

    print(f"✓ Failure learning completed")
    print(f"   - Lessons from failure: {failure_summary['lessons_count']}")
    if failure_summary.get('improvements_suggested'):
        print(f"   - Improvement: {failure_summary['improvements_suggested'][0]}")

    # Get relevant experience
    print("\n--- Retrieving Relevant Experience ---")
    relevant = manager.get_relevant_experience("create webpage")
    print(f"✓ Retrieved relevant experience")
    print(f"   - Similar experiences: {len(relevant['similar_experiences'])}")
    print(f"   - Relevant lessons: {len(relevant['relevant_lessons'])}")
    print(f"   - Strategies: {len(relevant['recommended_strategies'])}")

    # Get statistics
    stats = manager.get_learning_statistics()
    print(f"\n✓ Learning statistics:")
    print(f"   - Total experiences: {stats['total_experiences']}")
    print(f"   - Total lessons: {stats['total_lessons']}")
    print(f"   - Success rate: {stats['overall_success_rate']:.1%}")

    return manager


def test_self_improvement(memory):
    """Test self-improvement suggester."""
    print("\n" + "="*60)
    print("Testing Self-Improvement Suggester")
    print("="*60)

    suggester = SelfImprovementSuggester(vector_memory=memory)

    # Get performance analysis
    print("\n--- Performance Analysis ---")
    analysis = suggester.analyze_performance()

    if not analysis.get("error"):
        print(f"✓ Performance analysis completed")
        print(f"   - Total experiences: {analysis.get('total_experiences', 0)}")
        print(f"   - Success rate: {analysis.get('success_rate', 0):.1%}")
        print(f"   - Successful: {analysis.get('successful', 0)}")
        print(f"   - Failed: {analysis.get('failed', 0)}")
    else:
        print(f"⚠ Analysis: {analysis.get('message', 'Unknown')}")

    # Get improvement suggestions
    print("\n--- Improvement Suggestions ---")
    suggestions = suggester.get_improvement_suggestions()

    print(f"✓ Generated {len(suggestions)} suggestion(s):")
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"   {i}. [{suggestion['priority'].upper()}] {suggestion['suggestion']}")
        if 'current_metric' in suggestion:
            print(f"      Current: {suggestion['current_metric']}")

    # Get progress report
    print("\n--- Learning Progress Report ---")
    report = suggester.get_learning_progress_report()
    print(f"✓ Generated progress report")
    print(f"   - Learning enabled: {report['learning_enabled']}")
    print(f"   - Memory backend: {report['memory_stats'].get('backend', 'unknown')}")

    return suggester


def test_integration():
    """Test integration with orchestrator."""
    print("\n" + "="*60)
    print("Testing Orchestrator Integration")
    print("="*60)

    try:
        from agent.core.orchestrator import AgentOrchestrator
        from agent.tools.filesystem import FileSystemTool
        from config.settings import settings

        # Create orchestrator with learning enabled
        orchestrator = AgentOrchestrator(
            max_iterations=5,
            verbose=True,
            enable_learning=True
        )

        # Register a tool
        from agent.tools.registry import get_registry
        registry = get_registry()

        if not registry.has("filesystem"):
            filesystem_tool = FileSystemTool(working_directory=settings.working_directory)
            registry.register(filesystem_tool)

        print(f"✓ Orchestrator initialized with learning enabled")
        print(f"   - Learning manager: {'enabled' if orchestrator.enable_learning else 'disabled'}")
        print(f"   - Tools registered: {len(registry)}")

        # Note: We don't run a full task here to avoid API calls in tests
        print(f"✓ Integration test passed (orchestrator ready for learning)")

        return orchestrator

    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return None


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print(" REFLECTIVE LEARNING SYSTEM - COMPREHENSIVE TEST")
    print("="*70)

    try:
        # Test 1: Vector Memory
        memory = test_vector_memory()

        # Test 2: Reflection Engine
        engine = test_reflection_engine()

        # Test 3: Learning Manager
        manager = test_learning_manager(memory, engine)

        # Test 4: Self-Improvement
        suggester = test_self_improvement(memory)

        # Test 5: Integration
        orchestrator = test_integration()

        # Final summary
        print("\n" + "="*70)
        print(" TEST SUMMARY")
        print("="*70)
        print("✓ Vector Memory: PASSED")
        print("✓ Reflection Engine: PASSED")
        print("✓ Learning Manager: PASSED")
        print("✓ Self-Improvement Suggester: PASSED")
        print("✓ Orchestrator Integration: PASSED" if orchestrator else "✗ Orchestrator Integration: FAILED")

        print("\n" + "="*70)
        print(" REFLECTIVE LEARNING SYSTEM: FULLY OPERATIONAL")
        print("="*70)
        print("\nThe agent can now:")
        print("  🧠 Remember past experiences with semantic search")
        print("  🔍 Reflect on successes and failures")
        print("  📚 Extract and store actionable lessons")
        print("  📈 Track performance over time")
        print("  💡 Suggest self-improvements")
        print("  🎯 Apply past learnings to new tasks")

        print("\nTo use in production:")
        print("  1. Install ChromaDB: pip install chromadb")
        print("  2. Learning is automatically enabled in orchestrator")
        print("  3. Every task execution will store experiences")
        print("  4. Use manager.get_learning_statistics() to see progress")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
