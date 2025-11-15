"""Test script for V2 tools."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.filesystem_v2 import (
    ReadFileTool,
    WriteFileTool,
    ListDirectoryTool,
    CreateDirectoryTool,
    SearchFilesTool,
    CheckFileExistsTool
)
from agent.tools.terminal_v2 import TerminalToolV2
from config.settings import settings


def test_filesystem_tools():
    """Test file system tools."""
    print("\n" + "=" * 60)
    print("Testing File System Tools V2")
    print("=" * 60)

    # Create working directory for tests
    test_dir = Path("./test_workspace_v2")
    test_dir.mkdir(exist_ok=True)

    # Test 1: Write file
    print("\n[TEST 1] Write File Tool")
    write_tool = WriteFileTool(working_directory=str(test_dir))
    print(f"Tool name: {write_tool.name}")
    print(f"Description: {write_tool.description[:100]}...")
    result = write_tool.execute(path="test_file.txt", content="Hello from V2 tools!")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    # Test 2: Read file
    print("\n[TEST 2] Read File Tool")
    read_tool = ReadFileTool(working_directory=str(test_dir))
    print(f"Tool name: {read_tool.name}")
    print(f"Description: {read_tool.description[:100]}...")
    result = read_tool.execute(path="test_file.txt")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    # Test 3: List directory
    print("\n[TEST 3] List Directory Tool")
    list_tool = ListDirectoryTool(working_directory=str(test_dir))
    print(f"Tool name: {list_tool.name}")
    print(f"Description: {list_tool.description[:100]}...")
    result = list_tool.execute(path=".")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    # Test 4: Create directory
    print("\n[TEST 4] Create Directory Tool")
    mkdir_tool = CreateDirectoryTool(working_directory=str(test_dir))
    print(f"Tool name: {mkdir_tool.name}")
    print(f"Description: {mkdir_tool.description[:100]}...")
    result = mkdir_tool.execute(path="test_subdir")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    # Test 5: Search files
    print("\n[TEST 5] Search Files Tool")
    search_tool = SearchFilesTool(working_directory=str(test_dir))
    print(f"Tool name: {search_tool.name}")
    print(f"Description: {search_tool.description[:100]}...")
    result = search_tool.execute(path=".", pattern="*.txt")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    # Test 6: Check file exists
    print("\n[TEST 6] Check File Exists Tool")
    exists_tool = CheckFileExistsTool(working_directory=str(test_dir))
    print(f"Tool name: {exists_tool.name}")
    print(f"Description: {exists_tool.description[:100]}...")
    result = exists_tool.execute(path="test_file.txt")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")
    print(f"Metadata: {result.metadata}")

    # Test 7: Error handling - read non-existent file
    print("\n[TEST 7] Error Handling - Read Non-Existent File")
    result = read_tool.execute(path="nonexistent.txt")
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")

    print("\n" + "=" * 60)
    print("File System Tools V2: All tests completed")
    print("=" * 60)


def test_terminal_tool():
    """Test terminal tool."""
    print("\n" + "=" * 60)
    print("Testing Terminal Tool V2")
    print("=" * 60)

    terminal = TerminalToolV2()

    # Test 1: Simple command
    print("\n[TEST 1] Simple Command - ls")
    print(f"Tool name: {terminal.name}")
    print(f"Description: {terminal.description[:150]}...")
    result = terminal.execute(command="ls -la")
    print(f"Status: {result.status}")
    print(f"Output: {result.output[:200] if result.output else 'None'}...")

    # Test 2: Git command
    print("\n[TEST 2] Git Command - git status")
    result = terminal.execute(command="git status")
    print(f"Status: {result.status}")
    if result.status.value == "success":
        print(f"Output: {result.output[:200]}...")
    else:
        print(f"Error: {result.error[:200]}...")

    # Test 3: Python version
    print("\n[TEST 3] Python Version")
    result = terminal.execute(command="python --version")
    print(f"Status: {result.status}")
    print(f"Output: {result.output}")

    # Test 4: Blocked command
    print("\n[TEST 4] Blocked Command - rm")
    result = terminal.execute(command="rm -rf /")
    print(f"Status: {result.status}")
    print(f"Error: {result.error}")

    # Test 5: Unknown command
    print("\n[TEST 5] Unknown Command")
    result = terminal.execute(command="unknown_command_12345")
    print(f"Status: {result.status}")
    print(f"Error: {result.error[:200]}...")

    print("\n" + "=" * 60)
    print("Terminal Tool V2: All tests completed")
    print("=" * 60)


def test_tool_parameters():
    """Test tool parameter definitions."""
    print("\n" + "=" * 60)
    print("Testing Tool Parameters (for LLM function calling)")
    print("=" * 60)

    tools = [
        ReadFileTool(),
        WriteFileTool(),
        ListDirectoryTool(),
        CreateDirectoryTool(),
        SearchFilesTool(),
        TerminalToolV2()
    ]

    for tool in tools:
        print(f"\n{tool.name}:")
        print(f"  Description: {tool.description[:80]}...")
        print(f"  Parameters:")
        for param_name, param_info in tool.parameters.items():
            required = "required" if param_info.get("required") else "optional"
            print(f"    - {param_name} ({param_info['type']}, {required})")
            print(f"      {param_info['description'][:60]}...")

    print("\n" + "=" * 60)
    print("Tool Parameters: All checks completed")
    print("=" * 60)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("V2 Tools Test Suite")
    print("=" * 60)

    try:
        test_filesystem_tools()
        test_terminal_tool()
        test_tool_parameters()

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
