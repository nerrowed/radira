#!/usr/bin/env python3
"""Test script to verify all imports work without circular dependencies."""

import sys

def test_import(module_path, item=None):
    """Test importing a module or specific item from module."""
    try:
        if item:
            exec(f"from {module_path} import {item}")
            print(f"✅ from {module_path} import {item}")
        else:
            exec(f"import {module_path}")
            print(f"✅ import {module_path}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import {module_path}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  Error importing {module_path}: {e}")
        return False

def main():
    print("="*60)
    print("TESTING IMPORTS - Circular Dependency Check")
    print("="*60)
    print()

    tests = [
        # Test exceptions module (should be standalone)
        ("agent.core.exceptions", "RadiraException"),
        ("agent.core.exceptions", "LLMError"),
        ("agent.core.exceptions", "ToolError"),
        ("agent.core.exceptions", "RateLimitError"),

        # Test groq_client (was causing circular import)
        ("agent.llm.groq_client", "GroqClient"),
        ("agent.llm.groq_client", "get_groq_client"),

        # Test function orchestrator
        ("agent.core.function_orchestrator", "FunctionOrchestrator"),

        # Test tools
        ("agent.tools.base", "BaseTool"),
        ("agent.tools.registry", "ToolRegistry"),

        # Test settings
        ("config.settings", "settings"),
    ]

    passed = 0
    failed = 0

    for test in tests:
        if len(test) == 2:
            if test_import(test[0], test[1]):
                passed += 1
            else:
                failed += 1
        else:
            if test_import(test[0]):
                passed += 1
            else:
                failed += 1

    print()
    print("="*60)
    print("RESULTS")
    print("="*60)
    print(f"Passed: {passed}/{passed+failed}")
    print(f"Failed: {failed}/{passed+failed}")

    if failed == 0:
        print("\n🎉 All imports successful! No circular dependencies detected.")
        return 0
    else:
        print(f"\n❌ {failed} import(s) failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
