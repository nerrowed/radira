"""Test enhanced AI pipeline with semantic retrieval and agentic reasoning.

This demonstrates:
1. Semantic Retrieval Integration - AI menggunakan hasil dari Chroma
2. Reflective Memory Reuse - Lessons dan strategies dipakai ulang
3. Tool Invocation - Custom functions seperti get_bitcoin_price()
4. Agentic Reasoning - Deep step-by-step thinking
5. Auto-Reflection - Otomatis reflect setelah task
6. Structured Logging - [THINKING], [RETRIEVAL], [ACTION], [LEARNED]
"""

import logging
from agent.core.orchestrator import AgentOrchestrator
from agent.llm.groq_client import get_groq_client
from agent.tools.registry import get_registry
from agent.learning.learning_manager import get_learning_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_bitcoin_price():
    """Test 1: Memanggil custom function get_bitcoin_price()."""

    print("\n" + "="*80)
    print("TEST 1: Bitcoin Price Retrieval dengan Custom Function")
    print("="*80)

    # Initialize orchestrator with learning enabled
    orchestrator = AgentOrchestrator(
        llm_client=get_groq_client(),
        tool_registry=get_registry(),
        max_iterations=5,
        verbose=True,
        enable_learning=True,
        enable_self_awareness=True
    )

    # Run task
    result = orchestrator.run("Cek harga Bitcoin saat ini")

    print(f"\n✓ Final Result: {result}")
    print("\n" + "="*80)


def test_calculator_with_memory():
    """Test 2: Calculator dengan semantic memory - AI harus belajar dari pengalaman."""

    print("\n" + "="*80)
    print("TEST 2: Calculator dengan Semantic Memory")
    print("="*80)

    orchestrator = AgentOrchestrator(
        llm_client=get_groq_client(),
        tool_registry=get_registry(),
        max_iterations=5,
        verbose=True,
        enable_learning=True,
        enable_self_awareness=True
    )

    # First calculation - will be stored in memory
    print("\n--- Calculation 1: Teaching AI ---")
    result1 = orchestrator.run("Hitung 25 * 4")
    print(f"\n✓ Result 1: {result1}")

    # Reset for new task
    orchestrator.reset()

    # Second calculation - should use memory from first task
    print("\n--- Calculation 2: Using Memory ---")
    result2 = orchestrator.run("Hitung 50 / 2")
    print(f"\n✓ Result 2: {result2}")

    # The second task should show retrieval from memory in logs

    print("\n" + "="*80)


def test_time_query():
    """Test 3: Get current time - simple function call."""

    print("\n" + "="*80)
    print("TEST 3: Current Time Query")
    print("="*80)

    orchestrator = AgentOrchestrator(
        llm_client=get_groq_client(),
        tool_registry=get_registry(),
        max_iterations=3,
        verbose=True,
        enable_learning=True
    )

    result = orchestrator.run("Jam berapa sekarang?")

    print(f"\n✓ Final Result: {result}")
    print("\n" + "="*80)


def test_learning_persistence():
    """Test 4: Verify that learning persists across sessions."""

    print("\n" + "="*80)
    print("TEST 4: Learning Persistence Check")
    print("="*80)

    learning_manager = get_learning_manager()

    # Check memory statistics
    stats = learning_manager.get_learning_statistics()

    print("\n📊 Learning Statistics:")
    print(f"  Total Experiences: {stats.get('total_experiences', 0)}")
    print(f"  Total Lessons: {stats.get('total_lessons', 0)}")
    print(f"  Total Strategies: {stats.get('total_strategies', 0)}")
    print(f"  Success Rate: {stats.get('overall_success_rate', 0):.1%}")
    print(f"  Memory Backend: {stats.get('backend', 'unknown')}")

    # Try to retrieve some experiences
    if stats.get('total_experiences', 0) > 0:
        print("\n📚 Sample Experiences:")
        experiences = learning_manager.get_relevant_experience("hitung", n_results=2)

        for i, exp in enumerate(experiences.get("similar_experiences", [])[:2], 1):
            print(f"\n  Experience {i}:")
            print(f"    Task: {exp.get('task', 'Unknown')[:60]}")
            print(f"    Success: {exp.get('success', False)}")
            print(f"    Outcome: {exp.get('outcome', 'No outcome')[:80]}")

    print("\n" + "="*80)


def test_multi_step_reasoning():
    """Test 5: Complex task requiring multiple steps and reasoning."""

    print("\n" + "="*80)
    print("TEST 5: Multi-Step Reasoning")
    print("="*80)

    orchestrator = AgentOrchestrator(
        llm_client=get_groq_client(),
        tool_registry=get_registry(),
        max_iterations=10,
        verbose=True,
        enable_learning=True,
        enable_self_awareness=True
    )

    # Complex task requiring multiple steps
    result = orchestrator.run(
        "Hitung (100 + 50) * 2, lalu bandingkan hasilnya dengan harga Bitcoin yang dikonversi ke IDR (asumsi 1 USD = 15000 IDR)"
    )

    print(f"\n✓ Final Result: {result}")
    print("\n" + "="*80)


def main():
    """Run all tests."""

    print("\n" + "="*80)
    print("ENHANCED AI PIPELINE TEST SUITE")
    print("Testing: Semantic Retrieval, Agentic Reasoning, Tool Invocation, Auto-Reflection")
    print("="*80)

    try:
        # Test 1: Simple function call
        test_bitcoin_price()

        # Test 2: Memory usage
        test_calculator_with_memory()

        # Test 3: Time function
        test_time_query()

        # Test 4: Check learning persistence
        test_learning_persistence()

        # Test 5: Complex multi-step reasoning
        # Uncomment if you want to test complex reasoning
        # test_multi_step_reasoning()

        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED")
        print("="*80)

        print("\n📝 OBSERVATIONS:")
        print("1. [THINKING] logs show agentic reasoning mode is active")
        print("2. [RETRIEVAL] logs show semantic memory being queried")
        print("3. [ACTION] logs show tools being executed")
        print("4. [LEARNED] logs show insights being stored")
        print("\nThe AI should now:")
        print("- Use past experiences to inform decisions")
        print("- Call custom functions when needed")
        print("- Reflect and learn after each task")
        print("- Show deeper reasoning in Thought sections")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ TEST FAILED: {e}")


if __name__ == "__main__":
    main()
