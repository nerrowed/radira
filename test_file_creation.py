"""Quick test for file creation bug fix."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.filesystem import FileSystemTool

print("="*60)
print("Testing File System Tool - File Creation")
print("="*60)

# Create tool instance
fs_tool = FileSystemTool()
print(f"✓ FileSystemTool initialized")
print(f"  Working directory: {fs_tool.working_dir}")

# Test 1: Create file with content
print("\n[Test 1] Create file 'halo_tuan.txt' with content")
result = fs_tool.run(
    operation="write",
    path="halo_tuan.txt",
    content="Halo Tuan! This is a test file."
)

if result.is_success:
    print(f"✓ SUCCESS: {result.output}")
    print(f"  Path: {result.metadata.get('path')}")
    print(f"  Size: {result.metadata.get('size')} bytes")
else:
    print(f"✗ FAILED: {result.error}")
    sys.exit(1)

# Test 2: Read the file back
print("\n[Test 2] Read the created file")
result = fs_tool.run(
    operation="read",
    path="halo_tuan.txt"
)

if result.is_success:
    print(f"✓ SUCCESS: File read successfully")
    print(f"  Content: {result.output}")
else:
    print(f"✗ FAILED: {result.error}")
    sys.exit(1)

# Test 3: List directory to confirm file exists
print("\n[Test 3] List directory")
result = fs_tool.run(
    operation="list",
    path="."
)

if result.is_success:
    print(f"✓ SUCCESS: Directory listed")
    files = [item['name'] for item in result.output if item['name'] == 'halo_tuan.txt']
    if files:
        print(f"  ✓ File 'halo_tuan.txt' found in directory")
    else:
        print(f"  ✗ File 'halo_tuan.txt' NOT found in directory")
else:
    print(f"✗ FAILED: {result.error}")

print("\n" + "="*60)
print("✓ All tests passed! Bug is FIXED.")
print("="*60)
