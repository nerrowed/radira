"""Test script untuk Context Chain Tracking System.

Script ini mendemonstrasikan cara kerja sistem context tracking
dan bagaimana AI bisa mengingat urutan tindakan yang diambil.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.state.context_tracker import ContextTracker


def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"{title.center(60)}")
    print(f"{'='*60}\n")


def test_basic_tracking():
    """Test dasar context tracking."""
    print_section("Test 1: Basic Context Tracking")

    # Initialize tracker
    tracker = ContextTracker()

    # Simulasi beberapa event
    tracker.add_event(
        user_command="Baca file report.txt",
        ai_action="file_system",
        result="Error: File not found",
        status="error"
    )

    tracker.add_event(
        user_command="Baca file report.txt",
        ai_action="file_system",
        result="File created successfully",
        status="success",
        metadata={"operation": "create"}
    )

    tracker.add_event(
        user_command="Kenapa kamu buat file?",
        ai_action="Final Answer",
        result="Saya membuat file karena file report.txt tidak ditemukan sebelumnya",
        status="completed"
    )

    # Ambil aksi terakhir
    last_action = tracker.get_last_action()
    print("Last Action:")
    print(f"  User Command: {last_action['user_command']}")
    print(f"  AI Action: {last_action['ai_action']}")
    print(f"  Result: {last_action['result']}")
    print(f"  Status: {last_action['status']}\n")

    # Ringkasan aksi terakhir
    summary = tracker.summarize_recent_actions(n=3)
    print("Summary of Recent Actions:")
    print(summary)

    # Penjelasan aksi terakhir
    explanation = tracker.explain_last_action()
    print("\nExplanation of Last Action:")
    print(explanation)


def test_semantic_search():
    """Test semantic search untuk context yang relevan."""
    print_section("Test 2: Semantic Search for Related Context")

    tracker = ContextTracker()

    # Tambahkan berbagai event
    events = [
        {
            "user_command": "Buat file config.json",
            "ai_action": "file_system",
            "result": "File created successfully",
            "status": "success"
        },
        {
            "user_command": "Baca file config.json",
            "ai_action": "file_system",
            "result": "File content: {...}",
            "status": "success"
        },
        {
            "user_command": "Hapus file config.json",
            "ai_action": "file_system",
            "result": "File deleted successfully",
            "status": "success"
        },
        {
            "user_command": "Jalankan test",
            "ai_action": "terminal",
            "result": "Tests passed: 10/10",
            "status": "success"
        }
    ]

    for event in events:
        tracker.add_event(**event)

    # Cari konteks terkait file operations
    print("Searching for: 'file operations'\n")
    related = tracker.find_related_context("file operations", n_results=3)

    for i, context in enumerate(related, 1):
        print(f"{i}. {context.get('ai_action', 'N/A')}")
        print(f"   Command: {context.get('user_command', 'N/A')}")
        print(f"   Status: {context.get('status', 'N/A')}\n")


def test_statistics():
    """Test statistik context tracking."""
    print_section("Test 3: Context Tracking Statistics")

    tracker = ContextTracker()

    # Tambahkan banyak event untuk statistik
    for i in range(10):
        status = "success" if i % 3 != 0 else "error"
        tracker.add_event(
            user_command=f"Task {i+1}",
            ai_action="file_system" if i % 2 == 0 else "terminal",
            result=f"Result {i+1}",
            status=status
        )

    # Dapatkan statistik
    stats = tracker.get_statistics()

    print(f"Total Events: {stats['total_events']}")
    print(f"ChromaDB Available: {stats['chromadb_available']}")
    print(f"Storage Path: {stats['storage_path']}\n")

    print("Status Breakdown:")
    for status, count in stats['status_breakdown'].items():
        print(f"  • {status}: {count}")

    print("\nMost Common Actions:")
    for action, count in stats['most_common_actions'].items():
        print(f"  • {action}: {count}")


def test_action_chain():
    """Test action chain untuk melihat urutan lengkap."""
    print_section("Test 4: Action Chain Tracking")

    tracker = ContextTracker()

    # Simulasi urutan aksi untuk satu task
    chain = [
        ("Buat aplikasi web sederhana", "web_generator", "Starting web generation...", "success"),
        ("Buat aplikasi web sederhana", "file_system", "Created index.html", "success"),
        ("Buat aplikasi web sederhana", "file_system", "Created style.css", "success"),
        ("Buat aplikasi web sederhana", "file_system", "Created script.js", "success"),
        ("Buat aplikasi web sederhana", "Final Answer", "Web app created successfully", "completed"),
    ]

    for cmd, action, result, status in chain:
        tracker.add_event(cmd, action, result, status)

    # Dapatkan chain lengkap
    full_chain = tracker.get_action_chain()

    print("Complete Action Chain:\n")
    for i, event in enumerate(full_chain, 1):
        status_icon = "✓" if event['status'] in ['success', 'completed'] else "✗"
        print(f"{i}. {status_icon} {event['ai_action']} → {event['result'][:50]}...")


def main():
    """Jalankan semua test."""
    print("\n" + "="*60)
    print("Context Chain Tracking System Test".center(60))
    print("="*60)

    try:
        test_basic_tracking()
        test_semantic_search()
        test_statistics()
        test_action_chain()

        print("\n" + "="*60)
        print("✓ All tests completed successfully!".center(60))
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Test failed: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
