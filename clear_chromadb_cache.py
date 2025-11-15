#!/usr/bin/env python3
"""
Script to clear ChromaDB cache and reinitialize with proper telemetry settings.
This will remove existing ChromaDB data to force recreation with new settings.

WARNING: This will delete all stored memories, errors, and context!
Make sure you have a backup if needed.
"""

import os
import shutil
from pathlib import Path

def clear_chromadb_cache(workspace_path: str = None):
    """Clear ChromaDB cache directories.

    Args:
        workspace_path: Path to workspace directory (default: workspace)
    """
    if workspace_path is None:
        workspace_path = "workspace"

    workspace = Path(workspace_path)

    # ChromaDB directories
    chromadb_dirs = [
        workspace / ".memory",
        workspace / ".errors" / "chromadb",
        workspace / ".context"
    ]

    print("🧹 ChromaDB Cache Cleaner")
    print("=" * 60)

    for chroma_dir in chromadb_dirs:
        if chroma_dir.exists():
            try:
                print(f"\n📁 Found: {chroma_dir}")

                # Count files for info
                file_count = sum(1 for _ in chroma_dir.rglob("*") if _.is_file())
                print(f"   Contains {file_count} files")

                # Remove directory
                shutil.rmtree(chroma_dir)
                print(f"   ✅ Removed successfully")

            except Exception as e:
                print(f"   ❌ Error removing {chroma_dir}: {e}")
        else:
            print(f"\n📁 Not found: {chroma_dir} (skipping)")

    print("\n" + "=" * 60)
    print("✨ Cache cleanup complete!")
    print("\nChromaDB will be recreated with proper settings on next run.")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Clear ChromaDB cache to force reinitialize with new settings"
    )
    parser.add_argument(
        "--workspace",
        default="workspace",
        help="Path to workspace directory (default: workspace)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    if not args.force:
        print("⚠️  WARNING: This will delete all ChromaDB data!")
        print("   (memories, errors, context)")
        response = input("\nContinue? [y/N]: ")
        if response.lower() not in ['y', 'yes']:
            print("Cancelled.")
            exit(0)

    clear_chromadb_cache(args.workspace)
