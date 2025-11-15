"""Function definitions for Groq function calling (OpenAI-compatible format).

Converts BaseTool definitions to OpenAI function calling schema.
This enables LLM to understand and call tools naturally without regex classification.
"""

from typing import Dict, List, Any
from agent.tools.base import BaseTool
from agent.tools.registry import get_registry
import logging

logger = logging.getLogger(__name__)


def tool_to_function_definition(tool: BaseTool) -> Dict[str, Any]:
    """Convert BaseTool to OpenAI function calling schema.

    Args:
        tool: BaseTool instance

    Returns:
        Dict in OpenAI function format:
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "What the tool does",
                "parameters": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }
        }
    """
    # Extract parameters from tool
    tool_params = tool.parameters

    # Build properties dict
    properties = {}
    required = []

    for param_name, param_info in tool_params.items():
        # Convert to OpenAI schema
        prop = {
            "type": param_info.get("type", "string"),
            "description": param_info.get("description", f"Parameter: {param_name}")
        }

        # Add enum if present
        if "enum" in param_info:
            prop["enum"] = param_info["enum"]

        properties[param_name] = prop

        # Track required params
        if param_info.get("required", False):
            required.append(param_name)

    # Build function definition
    function_def = {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }

    return function_def


def get_all_function_definitions() -> List[Dict[str, Any]]:
    """Get all registered tools as function definitions.

    Returns:
        List of function definitions in OpenAI format
    """
    registry = get_registry()
    tools = registry.list_tools()

    functions = []
    for tool in tools:
        try:
            func_def = tool_to_function_definition(tool)
            functions.append(func_def)
            logger.debug(f"Converted tool '{tool.name}' to function definition")
        except Exception as e:
            logger.warning(f"Failed to convert tool '{tool.name}': {e}")

    return functions


def get_function_definitions(tool_names: List[str]) -> List[Dict[str, Any]]:
    """Get specific tools as function definitions.

    Args:
        tool_names: List of tool names to include

    Returns:
        List of function definitions
    """
    registry = get_registry()
    functions = []

    for tool_name in tool_names:
        try:
            tool = registry.get(tool_name)
            func_def = tool_to_function_definition(tool)
            functions.append(func_def)
        except Exception as e:
            logger.warning(f"Failed to get tool '{tool_name}': {e}")

    return functions


def create_function_calling_system_prompt(functions: List[Dict[str, Any]]) -> str:
    """Create system prompt that describes available functions (Claude-like).

    Args:
        functions: List of function definitions

    Returns:
        System prompt string
    """
    prompt = """Kamu adalah Radira, AI assistant yang cerdas dan helpful.

Kamu memiliki akses ke tools berikut untuk membantu user:

"""

    # Describe each function
    for func in functions:
        func_info = func["function"]
        name = func_info["name"]
        desc = func_info["description"]
        params = func_info["parameters"]

        prompt += f"**{name}**\n"
        prompt += f"  Deskripsi: {desc}\n"
        prompt += f"  Parameters:\n"

        for param_name, param_info in params["properties"].items():
            required_marker = " (required)" if param_name in params.get("required", []) else " (optional)"
            param_desc = param_info.get("description", "")
            param_type = param_info.get("type", "string")

            prompt += f"    - {param_name} ({param_type}){required_marker}: {param_desc}\n"

        prompt += "\n"

    prompt += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  CRITICAL FUNCTION CALLING RULES - READ CAREFULLY ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚫 ABSOLUTELY FORBIDDEN - THESE ACTIONS WILL FAIL:
───────────────────────────────────────────────────────────
1. ❌ NEVER generate code/content directly in your response
2. ❌ NEVER write code blocks (```python```, ```javascript```, etc) in your response
3. ❌ NEVER explain code without calling the appropriate tool
4. ❌ NEVER skip function calls when action is required
5. ❌ NEVER say "Berikut kodenya..." or "Here's the code..."

✅ REQUIRED BEHAVIOR - YOU MUST DO THIS:
───────────────────────────────────────────────────────────
1. ✓ ALWAYS call tools/functions for ANY action
2. ✓ ALWAYS use file_system tool for creating/writing files
3. ✓ ALWAYS use code_generator tool if you need to generate code
4. ✓ ALWAYS wait for tool results before continuing
5. ✓ ALWAYS use function calling API, not text responses

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Cara berpikir (Claude-style reasoning):

1. **Pahami intent user TERLEBIH DAHULU**
   - Apa yang user minta?
   - Apakah perlu action (tool call) atau cukup jawaban?
   - Jika perlu action → WAJIB call tool

2. **Think step-by-step sebelum bertindak**
   - Breakdown task menjadi steps
   - Identifikasi tool yang dibutuhkan untuk SETIAP step
   - Rencanakan urutan eksekusi

3. **Execute dengan FUNCTION CALLS (MANDATORY!)**
   - Panggil tool yang sesuai
   - Tunggu hasil dari tool
   - Observasi hasil sebelum lanjut

4. **Respond naturally**
   - Jelaskan apa yang kamu lakukan
   - Gunakan bahasa Indonesia natural
   - Friendly dan helpful

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📚 EXAMPLES - STUDY THESE CAREFULLY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Example 1: User asks to create code file
───────────────────────────────────────────────────────────
User: "buatkan aplikasi kalkulator dengan nama kal.py"

✅ CORRECT APPROACH:
[Your thinking]
- User wants Python calculator in file kal.py
- Need to: 1) Generate calculator code, 2) Write to file
- Required tool: file_system with operation=write

[Your action - FUNCTION CALL]
{
  "name": "file_system",
  "arguments": {
    "operation": "write",
    "path": "kal.py",
    "content": "def tambah(a, b):\\n    return a + b\\n\\ndef kurang(a, b):\\n    return a - b\\n\\nif __name__ == '__main__':\\n    print('Kalkulator sederhana')\\n    ..."
  }
}

❌ WRONG APPROACH (DO NOT DO THIS):
"Berikut kode kalkulator:

```python
def tambah(a, b):
    return a + b

def kurang(a, b):
    return a - b
```

Simpan ke file kal.py"

^ THIS IS COMPLETELY WRONG! THIS WILL CAUSE API ERROR!

Example 2: User asks to read file
───────────────────────────────────────────────────────────
User: "baca file README.md"

✅ CORRECT:
{
  "name": "file_system",
  "arguments": {
    "operation": "read",
    "path": "README.md"
  }
}

❌ WRONG:
"Saya tidak bisa membaca file secara langsung..."
^ Just call the tool!

Example 3: Conversational (no action needed)
───────────────────────────────────────────────────────────
User: "halo apa kabar?"

✅ CORRECT:
[No tool call needed - just respond]
"Halo! Saya baik, terima kasih. Ada yang bisa saya bantu?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 DECISION TREE - USE THIS EVERY TIME:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Does user request require ACTION?
├─ YES → CALL APPROPRIATE TOOL (file_system, code_generator, terminal, etc)
│        └─ Wait for result
│        └─ Observe output
│        └─ Continue or finish
│
└─ NO  → Respond directly with text
         └─ Answer questions
         └─ Explain concepts
         └─ Casual conversation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  REMEMBER: Your primary interface is FUNCTION CALLING, not text generation!
⚠️  When in doubt: CALL THE TOOL instead of explaining what you would do!
⚠️  API will ERROR if you generate code directly in response!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return prompt


def format_tool_call_result(tool_name: str, result: Any) -> str:
    """Format tool call result for LLM observation.

    Args:
        tool_name: Name of tool that was called
        result: ToolResult from execution

    Returns:
        Formatted observation string
    """
    from agent.tools.base import ToolResult

    if not isinstance(result, ToolResult):
        return f"[{tool_name}] Result: {result}"

    if result.is_success:
        output = result.output
        # Truncate long outputs
        if isinstance(output, str) and len(output) > 500:
            output = output[:500] + "... (truncated)"

        return f"[{tool_name}] ✓ Success: {output}"
    else:
        return f"[{tool_name}] ✗ Error: {result.error}"


# Example usage functions for testing
def print_function_definitions():
    """Print all function definitions (for debugging)."""
    functions = get_all_function_definitions()

    print(f"\n{'='*60}")
    print(f"Available Functions: {len(functions)}")
    print(f"{'='*60}\n")

    for func in functions:
        func_info = func["function"]
        print(f"Function: {func_info['name']}")
        print(f"Description: {func_info['description']}")
        print(f"Parameters: {list(func_info['parameters']['properties'].keys())}")
        print(f"Required: {func_info['parameters'].get('required', [])}")
        print()


def get_function_calling_config() -> Dict[str, Any]:
    """Get complete config for function calling mode.

    Returns:
        Dict with:
        - functions: List of function definitions
        - system_prompt: Claude-like system prompt
        - tool_choice: How to select tools ("auto", "required", "none")
    """
    functions = get_all_function_definitions()
    system_prompt = create_function_calling_system_prompt(functions)

    return {
        "functions": functions,
        "system_prompt": system_prompt,
        "tool_choice": "auto",  # Let LLM decide
        "parallel_tool_calls": False  # One tool at a time (safer for now)
    }


if __name__ == "__main__":
    # Test: print all function definitions
    print_function_definitions()

    # Test: create system prompt
    config = get_function_calling_config()
    print("\n" + "="*60)
    print("System Prompt Preview:")
    print("="*60)
    print(config["system_prompt"][:500] + "...\n")
