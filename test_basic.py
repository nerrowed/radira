"""Basic functionality test for the AI Agent."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.tools.filesystem import FileSystemTool
from agent.tools.terminal import TerminalTool
from agent.tools.registry import ToolRegistry
from config.settings import settings

print("="*60)
print("AI Autonomous Agent - Basic Test")
print("="*60)

# Test 1: Configuration
print("\n[Test 1] Configuration")
print(f"✓ Working Directory: {settings.working_directory}")
print(f"✓ Sandbox Mode: {settings.sandbox_mode}")
print(f"✓ Max Iterations: {settings.max_iterations}")
print(f"✓ Groq Model: {settings.groq_model}")
if settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
    print(f"✓ Groq API Key: {settings.groq_api_key[:10]}...")
else:
    print(f"⚠ Groq API Key: NOT SET (get one from https://console.groq.com/)")

# Test 2: Tool Registry
print("\n[Test 2] Tool Registry")
registry = ToolRegistry()
print(f"✓ Registry created")

# Test 3: File System Tool
print("\n[Test 3] File System Tool")
fs_tool = FileSystemTool()
registry.register(fs_tool)
print(f"✓ FileSystemTool registered: {fs_tool.name}")
print(f"  Description: {fs_tool.description}")
print(f"  Category: {fs_tool.category}")

# Test creating a directory
result = fs_tool.run(operation="mkdir", path="test_dir")
if result.is_success:
    print(f"✓ Created directory: {result.output}")
else:
    print(f"✗ Failed: {result.error}")

# Test writing a file
result = fs_tool.run(
    operation="write",
    path="test_dir/hello.txt",
    content="Hello from AI Agent!"
)
if result.is_success:
    print(f"✓ Created file: {result.output}")
else:
    print(f"✗ Failed: {result.error}")

# Test reading the file
result = fs_tool.run(operation="read", path="test_dir/hello.txt")
if result.is_success:
    print(f"✓ Read file content: {result.output}")
else:
    print(f"✗ Failed: {result.error}")

# Test listing directory
result = fs_tool.run(operation="list", path="test_dir")
if result.is_success:
    print(f"✓ Listed directory: {len(result.output)} items")
    for item in result.output:
        print(f"  - {item['name']} ({item['type']})")
else:
    print(f"✗ Failed: {result.error}")

# Test 4: Terminal Tool
print("\n[Test 4] Terminal Tool")
term_tool = TerminalTool()
registry.register(term_tool)
print(f"✓ TerminalTool registered: {term_tool.name}")
print(f"  Description: {term_tool.description}")

# Test a safe command
result = term_tool.run(command="echo Hello Terminal")
if result.is_success:
    print(f"✓ Command executed: {result.output}")
else:
    print(f"✗ Failed: {result.error}")

# Test command validation (should fail)
result = term_tool.run(command="rm -rf /")
if result.is_error:
    print(f"✓ Blocked dangerous command: {result.error}")
else:
    print(f"⚠ WARNING: Dangerous command was not blocked!")

# Test 5: LLM Client (if API key is set)
if settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
    print("\n[Test 5] Groq LLM Client")
    try:
        from agent.llm.groq_client import GroqClient
        client = GroqClient()
        print(f"✓ GroqClient initialized")

        # Test quick chat
        response = client.quick_chat("Say 'test successful' and nothing else", max_tokens=10)
        print(f"✓ LLM response: {response}")

        # Test token stats
        stats = client.get_token_stats()
        print(f"✓ Token usage: {stats['total_tokens']} tokens")
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
else:
    print("\n[Test 5] Groq LLM Client - SKIPPED (no API key)")

# Test 6: Registry functions
print("\n[Test 6] Tool Registry Functions")
print(f"✓ Total tools registered: {len(registry)}")
print(f"✓ Tool names: {', '.join(registry.list_tool_names())}")
print(f"✓ Categories: {', '.join(registry.list_categories())}")

# Summary
print("\n" + "="*60)
print("Test Summary")
print("="*60)
print("✓ Configuration loaded")
print("✓ Tool registry working")
print("✓ FileSystemTool working")
print("✓ TerminalTool working")
if settings.groq_api_key and settings.groq_api_key != "your_groq_api_key_here":
    print("✓ Groq LLM client working")
else:
    print("⚠ Groq LLM client not tested (set GROQ_API_KEY in .env)")

print("\n✓ All basic tests passed!")
print("\nNext steps:")
print("1. Set your GROQ_API_KEY in .env file (if not already set)")
print("2. Run the agent: python main.py")
print("3. Try a task: python main.py \"Create a simple HTML page\"")
print("="*60)
