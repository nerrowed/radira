#!/usr/bin/env python3
"""Quick test untuk interactive memory manager."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent.state.memory_manager import get_memory_manager

# Test basic functionality
print("Testing Memory Manager...")

manager = get_memory_manager()

# Test stats
print("\n1. Testing statistics...")
stats = manager.get_all_statistics()
print(f"✓ Context events: {stats['context']['total_events']}")

# Test list context
print("\n2. Testing list context...")
events = manager.list_context_memory(limit=5)
print(f"✓ Retrieved {len(events)} events")

# Test add lesson
print("\n3. Testing add lesson...")
lesson_id = manager.add_lesson(
    lesson="Test lesson from interactive mode",
    context="Testing",
    category="test",
    importance=0.5
)
print(f"✓ Added lesson: {lesson_id}")

# Test search
print("\n4. Testing search...")
results = manager.search_all("test", n_results=3)
print(f"✓ Search completed")

print("\n✓ All basic tests passed!")
print("\nInteractive mode is ready to use:")
print("  python manage_memory_interactive.py")
