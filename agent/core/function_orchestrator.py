"""Claude-like Function Calling Orchestrator.

Pure LLM reasoning without regex classification.
Let the LLM decide what tools to use naturally.
"""

import logging
from typing import List, Dict, Any, Optional
from agent.llm.groq_client import GroqClient, get_groq_client
from agent.llm.function_definitions import (
    get_all_function_definitions,
    create_function_calling_system_prompt,
    format_tool_call_result
)
from agent.tools.registry import get_registry
from agent.tools.base import ToolResult
from agent.core.confirmation_manager import ConfirmationManager, ConfirmationMode
from config.settings import settings

logger = logging.getLogger(__name__)


class FunctionOrchestrator:
    """Claude-like orchestrator using function calling (no regex!)."""

    def __init__(
        self,
        llm_client: Optional[GroqClient] = None,
        max_iterations: int = 10,
        verbose: bool = True,
        enable_learning: bool = True,
        enable_memory: bool = False,
        confirmation_mode: str = "auto"
    ):
        """Initialize function orchestrator.

        Args:
            llm_client: Groq client instance
            max_iterations: Maximum tool calling iterations
            verbose: Print detailed logs
            enable_learning: Enable learning system
            enable_memory: Enable ChromaDB semantic memory
            confirmation_mode: Confirmation mode (yes/no/auto)
        """
        self.llm = llm_client or get_groq_client()
        self.tool_registry = get_registry()
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.enable_learning = enable_learning
        self.enable_memory = enable_memory

        # Confirmation manager
        conf_mode = ConfirmationMode(confirmation_mode.lower())
        self.confirmation_manager = ConfirmationManager(mode=conf_mode, verbose=verbose)

        # Learning manager (lazy load)
        self.learning_manager = None
        if enable_memory:
            try:
                from agent.learning.learning_manager import get_learning_manager
                self.learning_manager = get_learning_manager()
                if self.verbose:
                    print("📚 Semantic memory enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize learning manager: {e}")
                self.enable_memory = False

        # Get function definitions
        self.functions = get_all_function_definitions()
        self.system_prompt = create_function_calling_system_prompt(self.functions)

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

        # Stats
        self.total_iterations = 0
        self.total_tool_calls = 0
        self.tools_executed = []  # Track for experience storage

        if self.verbose:
            print(f"\n🤖 Function Orchestrator initialized")
            print(f"   Functions available: {len(self.functions)}")
            print(f"   Tools: {', '.join([f['function']['name'] for f in self.functions])}")
            print(f"   Memory: {'✓ Enabled' if self.enable_memory else '✗ Disabled'}")
            print(f"   Confirmation: {confirmation_mode}\n")

    def run(self, user_input: str) -> str:
        """Run orchestrator with user input (main entry point).

        Args:
            user_input: User's request

        Returns:
            Final response string
        """
        if self.verbose:
            print(f"📥 User: {user_input}\n")

        # Get semantic context from ChromaDB if memory enabled
        enriched_system_prompt = self.system_prompt
        if self.enable_memory and self.learning_manager:
            semantic_context = self._get_semantic_context(user_input)
            if semantic_context:
                enriched_system_prompt = self._inject_context_to_prompt(semantic_context)

        # Initialize conversation
        self.messages = [
            {"role": "system", "content": enriched_system_prompt},
            {"role": "user", "content": user_input}
        ]

        # Run reasoning loop
        try:
            final_response = self._reasoning_loop()

            # Store experience if memory enabled
            if self.enable_memory and self.learning_manager:
                self._store_experience(user_input, final_response)

            return final_response

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            return f"Maaf, terjadi error: {str(e)}"

    def _reasoning_loop(self) -> str:
        """Main reasoning loop (Claude-like).

        Claude's pattern:
        1. LLM thinks about the task
        2. LLM decides if tools needed
        3. If tools → execute → observe → repeat
        4. If done → return response

        Returns:
            Final response string
        """
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            self.total_iterations += 1

            if self.verbose:
                print(f"💭 [Iteration {iteration}/{self.max_iterations}] LLM thinking...")

            # Call LLM with functions
            response = self.llm.chat_with_functions(
                messages=self.messages,
                functions=self.functions,
                temperature=0.5,  # Balanced creativity
                max_tokens=2048,
                tool_choice="auto"
            )

            # Check if LLM wants to call tools
            tool_calls = response.get("tool_calls")

            if tool_calls:
                # LLM wants to use tools
                if self.verbose:
                    print(f"🔧 LLM decided to call {len(tool_calls)} tool(s)")

                # Add assistant message with tool calls
                self.messages.append({
                    "role": "assistant",
                    "content": response.get("content") or "",
                    "tool_calls": tool_calls
                })

                # Execute each tool call
                for tool_call in tool_calls:
                    self._execute_tool_call(tool_call)

                # Continue loop to get next LLM response
                continue

            else:
                # LLM returned final response (no more tools)
                final_content = response.get("content")

                if self.verbose:
                    print(f"\n✅ LLM finished reasoning (no more tools needed)")
                    print(f"   Total iterations: {iteration}")
                    print(f"   Total tool calls: {self.total_tool_calls}")

                return final_content or "Task completed."

        # Max iterations reached
        if self.verbose:
            print(f"\n⚠️  Max iterations ({self.max_iterations}) reached")

        # Try to get final response
        self.messages.append({
            "role": "user",
            "content": "Berikan ringkasan hasil yang sudah didapat sejauh ini."
        })

        response = self.llm.chat_with_functions(
            messages=self.messages,
            functions=self.functions,
            temperature=0.3,
            max_tokens=1024,
            tool_choice="none"  # Force text response
        )

        return response.get("content") or "Task completed with max iterations."

    def _execute_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """Execute a single tool call and add result to messages.

        Args:
            tool_call: Tool call dict from LLM
        """
        # Parse tool call
        parsed = self.llm.parse_function_call(tool_call)
        function_name = parsed["function_name"]
        arguments = parsed["arguments"]
        call_id = parsed["call_id"]

        self.total_tool_calls += 1

        if self.verbose:
            print(f"   🔧 Calling: {function_name}")
            print(f"      Args: {arguments}")

        # Check confirmation before executing
        operation = arguments.get("operation") if "operation" in arguments else None
        should_execute = self.confirmation_manager.should_execute_tool(
            tool_name=function_name,
            operation=operation,
            arguments=arguments
        )

        if not should_execute:
            # User declined execution
            result_content = "Tool execution cancelled by user."
            if self.verbose:
                print(f"      ⏭️  Skipped: User declined")

            # Add cancellation to conversation
            self.messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "name": function_name,
                "content": result_content
            })
            return

        # Execute tool
        try:
            tool = self.tool_registry.get(function_name)
            result = tool.run(**arguments)

            # Track successful execution
            if result.is_success:
                self.tools_executed.append({
                    "tool": function_name,
                    "operation": operation,
                    "args": arguments
                })

            # Format result
            if result.is_success:
                if self.verbose:
                    output_preview = str(result.output)[:100]
                    print(f"      ✅ Success: {output_preview}{'...' if len(str(result.output)) > 100 else ''}")

                result_content = format_tool_call_result(function_name, result)
            else:
                if self.verbose:
                    print(f"      ❌ Error: {result.error}")

                result_content = f"Error: {result.error}"

        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            if self.verbose:
                print(f"      ❌ Exception: {str(e)}")

            result_content = f"Tool execution failed: {str(e)}"

        # Add tool result to conversation
        self.messages.append({
            "role": "tool",
            "tool_call_id": call_id,
            "name": function_name,
            "content": result_content
        })

    def run_with_learning(self, user_input: str) -> str:
        """Run with learning system integration (deprecated - use run with enable_memory=True).

        Args:
            user_input: User's request

        Returns:
            Final response
        """
        return self.run(user_input)

    def _get_semantic_context(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Query ChromaDB for relevant semantic context.

        Args:
            user_input: User's task

        Returns:
            Dict with experiences, lessons, strategies or None
        """
        if not self.learning_manager:
            return None

        try:
            # Query with cost-efficient settings
            context = self.learning_manager.get_relevant_experience(
                current_task=user_input,
                n_results=3  # Limit to top 3 for cost efficiency
            )

            # Check similarity threshold (0.80 for cost efficiency)
            if context.get("similar_experiences"):
                # Filter by similarity score if available
                filtered = []
                for exp in context["similar_experiences"]:
                    # ChromaDB returns distance, lower is better
                    # We want high similarity (low distance)
                    if "distance" in exp and exp["distance"] < 0.5:  # Similarity > 0.5
                        filtered.append(exp)
                    elif "distance" not in exp:
                        # No distance info, include it
                        filtered.append(exp)

                if filtered:
                    if self.verbose:
                        print(f"📚 Found {len(filtered)} relevant past experience(s)")
                    context["similar_experiences"] = filtered
                    return context
                else:
                    if self.verbose:
                        print("   (No highly relevant experiences found)")
                    return None

            return None

        except Exception as e:
            logger.warning(f"Failed to get semantic context: {e}")
            return None

    def _inject_context_to_prompt(self, context: Dict[str, Any]) -> str:
        """Inject semantic context into system prompt.

        Args:
            context: Semantic context from ChromaDB

        Returns:
            Enriched system prompt
        """
        # Start with base system prompt
        enriched = self.system_prompt

        # Build context section
        context_section = "\n\n📚 SEMANTIC MEMORY CONTEXT:\n"
        context_section += "=" * 60 + "\n"

        # Add past experiences
        if context.get("similar_experiences"):
            context_section += "\n💭 Past Similar Tasks:\n"
            for i, exp in enumerate(context["similar_experiences"][:2], 1):  # Limit to 2
                task = exp.get("task", "")[:100]
                outcome = exp.get("outcome", "")[:100]
                success = "✅" if exp.get("success") else "❌"
                context_section += f"{i}. {success} Task: {task}\n"
                context_section += f"   Result: {outcome}\n"

        # Add lessons learned
        if context.get("relevant_lessons"):
            context_section += "\n💡 Lessons Learned:\n"
            for i, lesson_data in enumerate(context["relevant_lessons"][:2], 1):  # Limit to 2
                lesson = lesson_data.get("lesson", "") if isinstance(lesson_data, dict) else str(lesson_data)
                context_section += f"{i}. {lesson[:150]}\n"

        # Add strategies
        if context.get("recommended_strategies"):
            context_section += "\n⚡ Proven Strategies:\n"
            for i, strategy_data in enumerate(context["recommended_strategies"][:2], 1):  # Limit to 2
                strategy = strategy_data.get("strategy", "") if isinstance(strategy_data, dict) else str(strategy_data)
                context_section += f"{i}. {strategy[:150]}\n"

        context_section += "\n" + "=" * 60
        context_section += "\n\nUse the above context to inform your decisions, but don't be constrained by it.\n"

        # Inject before the task description
        enriched += context_section

        return enriched

    def _store_experience(self, task: str, result: str) -> None:
        """Store task experience to ChromaDB for future learning.

        Args:
            task: User's task
            result: Final response/result
        """
        if not self.learning_manager:
            return

        try:
            # Determine success based on result
            success = "error" not in result.lower() and "failed" not in result.lower()

            # Build actions list from executed tools
            actions = [f"{t['tool']}.{t.get('operation', 'execute')}" for t in self.tools_executed]

            # Use learn_from_task method (complete learning cycle)
            learning_summary = self.learning_manager.learn_from_task(
                task=task,
                actions=actions,
                outcome=result[:500],  # Limit for cost efficiency
                success=success,
                errors=None,  # No errors in this context
                context={
                    "tool_count": len(self.tools_executed),
                    "iteration_count": self.total_iterations,
                    "tools_used": [t["tool"] for t in self.tools_executed]
                }
            )

            if self.verbose:
                lessons_count = learning_summary.get("lessons_count", 0)
                print(f"\n💾 Experience stored to semantic memory")
                if lessons_count > 0:
                    print(f"   📝 {lessons_count} lesson(s) learned")

        except Exception as e:
            logger.warning(f"Failed to store experience: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics.

        Returns:
            Dict with stats
        """
        return {
            "total_iterations": self.total_iterations,
            "total_tool_calls": self.total_tool_calls,
            "messages_in_history": len(self.messages),
            "functions_available": len(self.functions)
        }

    def reset(self):
        """Reset conversation and stats."""
        self.messages = []
        self.total_iterations = 0
        self.total_tool_calls = 0

        if self.verbose:
            print("🔄 Orchestrator reset\n")


# Singleton instance
_orchestrator: Optional[FunctionOrchestrator] = None


def get_function_orchestrator(
    llm_client: Optional[GroqClient] = None,
    **kwargs
) -> FunctionOrchestrator:
    """Get or create singleton function orchestrator.

    Args:
        llm_client: Optional LLM client
        **kwargs: Additional orchestrator arguments

    Returns:
        FunctionOrchestrator instance
    """
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = FunctionOrchestrator(llm_client=llm_client, **kwargs)
    return _orchestrator


def run_with_function_calling(user_input: str, verbose: bool = True) -> str:
    """Quick function to run with function calling mode.

    Args:
        user_input: User's request
        verbose: Print logs

    Returns:
        Response string
    """
    orchestrator = get_function_orchestrator(verbose=verbose)
    return orchestrator.run(user_input)


if __name__ == "__main__":
    # Test the orchestrator
    print("="*60)
    print("Testing Function Orchestrator (Claude-like)")
    print("="*60)

    # Test case 1: File operation
    print("\n[Test 1] File operation")
    response = run_with_function_calling("baca file README.md")
    print(f"\n📤 Response: {response}\n")

    # Test case 2: Code generation (user's failing example!)
    print("\n[Test 2] Code generation")
    response = run_with_function_calling("buatkan aplikasi kalkulator dengan nama kal.py")
    print(f"\n📤 Response: {response}\n")

    # Test case 3: Conversational (should not use tools)
    print("\n[Test 3] Conversational")
    response = run_with_function_calling("halo apa kabar?")
    print(f"\n📤 Response: {response}\n")
