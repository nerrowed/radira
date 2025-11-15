"""Test script for superuser mode functionality."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test environment before importing
os.environ["GROQ_API_KEY"] = "test_key_for_validation_12345678901234567890"
os.environ["SUPERUSER_MODE"] = "false"  # Start with disabled

from agent.tools.terminal_v2 import TerminalToolV2
from config.settings import settings


def test_superuser_disabled():
    """Test that sudo commands are blocked when superuser mode is disabled."""
    print("\n" + "=" * 60)
    print("TEST 1: Superuser Mode DISABLED (default)")
    print("=" * 60)

    terminal = TerminalToolV2()

    print(f"\nSuperuser mode: {settings.superuser_mode}")
    print(f"Tool description includes: {'ENABLED' if settings.superuser_mode else 'DISABLED'}")

    # Test 1: Try sudo command (should be blocked)
    print("\n[TEST 1.1] Try sudo apt update (should be blocked)")
    result = terminal.execute(command="sudo apt update")
    print(f"Status: {result.status}")
    print(f"Error: {result.error[:150]}...")
    assert result.status.value == "error", "Sudo should be blocked when disabled"
    assert "SUPERUSER_MODE" in result.error, "Error should mention SUPERUSER_MODE"

    # Test 2: Try sudo with dangerous command (should be blocked)
    print("\n[TEST 1.2] Try sudo rm -rf / (should be blocked - dangerous)")
    result = terminal.execute(command="sudo rm -rf /")
    print(f"Status: {result.status}")
    print(f"Error: {result.error[:150]}...")
    assert result.status.value == "error", "Dangerous command should be blocked"

    # Test 3: Regular command should work
    print("\n[TEST 1.3] Try regular command: ls (should work)")
    result = terminal.execute(command="ls")
    print(f"Status: {result.status}")
    if result.status.value == "success":
        print(f"Output: {result.output[:100] if result.output else 'None'}...")
    else:
        print(f"Error: {result.error[:150]}...")

    print("\n✅ Superuser disabled tests passed")


def test_superuser_enabled():
    """Test that sudo commands work when superuser mode is enabled."""
    print("\n" + "=" * 60)
    print("TEST 2: Superuser Mode ENABLED (Simulation)")
    print("=" * 60)

    print("\nNote: Testing validation logic directly since settings are loaded at import time.")
    print("In production, SUPERUSER_MODE is set in .env before app starts.")

    # For testing, we'll manually check validation logic by temporarily modifying settings
    from config import settings as settings_module
    original_superuser_mode = settings_module.settings.superuser_mode

    # Temporarily enable for testing
    settings_module.settings.superuser_mode = True
    print(f"\nSuperuser mode (test override): {settings_module.settings.superuser_mode}")

    terminal = TerminalToolV2()

    # Test 1: Sudo with allowed command (validation should pass)
    print("\n[TEST 2.1] Validate sudo apt update (should pass validation)")
    is_safe, reason = terminal._validate_command("sudo apt update")
    print(f"Is safe: {is_safe}")
    if not is_safe:
        print(f"Reason: {reason}")
    assert is_safe, "sudo apt should be allowed when superuser mode enabled"

    # Test 2: Sudo with systemctl (validation should pass)
    print("\n[TEST 2.2] Validate sudo systemctl status nginx (should pass)")
    is_safe, reason = terminal._validate_command("sudo systemctl status nginx")
    print(f"Is safe: {is_safe}")
    if not is_safe:
        print(f"Reason: {reason}")
    assert is_safe, "sudo systemctl should be allowed"

    # Test 3: Sudo with chmod (validation should pass)
    print("\n[TEST 2.3] Validate sudo chmod 755 file.txt (should pass)")
    is_safe, reason = terminal._validate_command("sudo chmod 755 file.txt")
    print(f"Is safe: {is_safe}")
    if not is_safe:
        print(f"Reason: {reason}")
    assert is_safe, "sudo chmod should be allowed"

    # Test 4: Sudo with dangerous command (should still be blocked)
    print("\n[TEST 2.4] Validate sudo rm -rf / (should be BLOCKED - always dangerous)")
    is_safe, reason = terminal._validate_command("sudo rm -rf /")
    print(f"Is safe: {is_safe}")
    print(f"Reason: {reason}")
    assert not is_safe, "Dangerous commands should be blocked even with sudo"
    assert "NEVER" in reason.upper(), "Should indicate NEVER allowed"

    # Test 5: Sudo with unknown command (should be blocked)
    print("\n[TEST 2.5] Validate sudo unknown_command (should be blocked)")
    is_safe, reason = terminal._validate_command("sudo unknown_command")
    print(f"Is safe: {is_safe}")
    print(f"Reason: {reason}")
    assert not is_safe, "Unknown commands should be blocked"

    # Test 6: Sudo without actual command (should be blocked)
    print("\n[TEST 2.6] Validate just 'sudo' (should be blocked)")
    is_safe, reason = terminal._validate_command("sudo")
    print(f"Is safe: {is_safe}")
    print(f"Reason: {reason}")
    assert not is_safe, "Incomplete sudo should be blocked"

    # Restore original setting
    settings_module.settings.superuser_mode = original_superuser_mode

    print("\n✅ Superuser enabled tests passed")


def test_command_suggestions():
    """Test that helpful suggestions are provided."""
    print("\n" + "=" * 60)
    print("TEST 3: Command Suggestions")
    print("=" * 60)

    # Test with superuser disabled
    os.environ["SUPERUSER_MODE"] = "false"
    from config.settings import reload_settings
    reload_settings()

    terminal = TerminalToolV2()

    # Test 1: Sudo suggestion when disabled
    print("\n[TEST 3.1] Get suggestion for sudo when disabled")
    suggestion = terminal._get_command_suggestion("sudo apt install nginx")
    print(f"Suggestion: {suggestion[:150]}...")
    assert suggestion is not None, "Should provide suggestion"
    assert "SUPERUSER_MODE" in suggestion, "Should mention how to enable"

    # Test 2: chmod suggestion
    print("\n[TEST 3.2] Get suggestion for chmod")
    suggestion = terminal._get_command_suggestion("chmod 755 file.txt")
    print(f"Suggestion: {suggestion}")
    assert suggestion is not None, "Should provide suggestion"

    # Test 3: systemctl suggestion
    print("\n[TEST 3.3] Get suggestion for systemctl")
    suggestion = terminal._get_command_suggestion("systemctl start nginx")
    print(f"Suggestion: {suggestion}")
    assert suggestion is not None, "Should provide suggestion"

    print("\n✅ Command suggestion tests passed")


def test_examples_dynamic():
    """Test that examples change based on superuser mode."""
    print("\n" + "=" * 60)
    print("TEST 4: Dynamic Examples Logic")
    print("=" * 60)

    print("\nNote: Testing the examples generation logic")
    print("In production, examples will include sudo commands when SUPERUSER_MODE=true in .env")

    from config import settings as settings_module
    original_superuser_mode = settings_module.settings.superuser_mode

    # Create terminal with current settings
    terminal = TerminalToolV2()

    print("\n[TEST 4.1] Verify examples structure")
    examples = terminal.examples
    print(f"Number of examples: {len(examples)}")
    print("Sample examples:")
    for ex in examples[:3]:
        print(f"  - {ex}")

    # Verify all examples are properly formatted
    for ex in examples:
        assert "command" in ex, "Each example should contain 'command' key"

    print(f"\nCurrent mode: {settings_module.settings.superuser_mode}")
    has_sudo = any("sudo" in ex for ex in examples)
    print(f"Has sudo examples: {has_sudo}")

    if settings_module.settings.superuser_mode:
        print("ℹ️  Superuser mode is ON, sudo examples should be present")
        # In production with SUPERUSER_MODE=true, sudo examples will be added
    else:
        print("ℹ️  Superuser mode is OFF, no sudo examples expected")
        assert not has_sudo, "Should not have sudo examples when disabled"

    # Restore original
    settings_module.settings.superuser_mode = original_superuser_mode

    print("\n✅ Examples structure tests passed")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SUPERUSER MODE TEST SUITE")
    print("=" * 60)

    try:
        test_superuser_disabled()
        test_superuser_enabled()
        test_command_suggestions()
        test_examples_dynamic()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSuperuser mode is working correctly:")
        print("  ✅ Blocks sudo when disabled")
        print("  ✅ Allows safe sudo when enabled")
        print("  ✅ Always blocks dangerous commands")
        print("  ✅ Provides helpful suggestions")
        print("  ✅ Dynamic examples based on mode")
        print("\n" + "=" * 60)

        return 0

    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
