"""Claude-like Function Calling Orchestrator.

Pure LLM reasoning without regex classification.
Let the LLM decide what tools to use naturally.

ENHANCED with:
- Rule Engine (deterministic rule checking BEFORE reasoning)
- Memory Filter (smart filtering of what gets stored)
- Enhanced Retrieval (type-based memory search)
- Meta-Memory System Prompt
"""

import logging
from pathlib import Path
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
from agent.core.exceptions import ContextOverflowError, TokenLimitExceededError
from config.settings import settings

# NEW: Import enhanced memory components
from agent.core.rule_engine import get_rule_engine
from agent.state.memory_filter import get_memory_filter, MemoryType
from agent.state.retrieval import get_enhanced_retrieval
from agent.learning.task_importance_filter import get_task_importance_filter

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

        # NEW: Enhanced memory components
        self.rule_engine = None
        self.memory_filter = None
        self.enhanced_retrieval = None

        # Learning manager (lazy load)
        self.learning_manager = None
        if enable_memory:
            try:
                from agent.learning.learning_manager import get_learning_manager
                self.learning_manager = get_learning_manager()

                # Initialize enhanced memory components
                self.rule_engine = get_rule_engine()
                self.memory_filter = get_memory_filter()
                self.enhanced_retrieval = get_enhanced_retrieval()

                if self.verbose:
                    print("📚 Enhanced memory system enabled:")
                    print(f"   - Rule Engine: {self.rule_engine.get_rule_count()} rules loaded")
                    print(f"   - Memory Filter: Active")
                    print(f"   - Enhanced Retrieval: Active")
            except Exception as e:
                logger.warning(f"Failed to initialize memory components: {e}")
                self.enable_memory = False

        # Get function definitions
        self.functions = get_all_function_definitions()

        # Load meta-memory system prompt
        self.base_system_prompt = self._load_meta_memory_prompt()
        self.system_prompt = self.base_system_prompt

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

        # Context management
        self.max_context_messages = settings.history_keep_last_n * 2  # User + Assistant pairs
        self.max_tokens_per_task = settings.max_total_tokens_per_task
        self.current_token_usage = 0

        # Stats
        self.total_iterations = 0
        self.total_tool_calls = 0
        self.tools_executed = []  # Track for experience storage
        self.total_tokens_used = 0

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
        # RESET TOKEN USAGE AT START OF EACH TASK (prevent accumulation across tasks)
        self.current_token_usage = 0
        self.total_tokens_used = 0
        self.llm.reset_token_stats()

        if self.verbose:
            print(f"📥 User: {user_input}\n")

        # STEP 1: Check rules FIRST (deterministic, before LLM)
        if self.enable_memory and self.rule_engine:
            rule_response = self.rule_engine.check_rules(user_input)
            if rule_response:
                if self.verbose:
                    print(f"🔴 RULE TRIGGERED: Responding deterministically")
                    print(f"   Response: {rule_response}\n")

                # Store this as a successful rule application
                if self.learning_manager:
                    try:
                        self.learning_manager.vector_memory.store_experience(
                            task=user_input,
                            actions=["rule_triggered"],
                            outcome=rule_response,
                            success=True,
                            metadata={"type": "rule_application"}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to store rule application: {e}")

                return rule_response

        # STEP 2: Retrieve memory context (RULES, FACTS, EXPERIENCES)
        enriched_system_prompt = self.base_system_prompt
        if self.enable_memory and self.enhanced_retrieval:
            try:
                # Get all relevant memory
                retrieved = self.enhanced_retrieval.retrieve_for_task(user_input)

                # Format and inject into prompt
                memory_section = self.enhanced_retrieval.format_for_prompt(retrieved)
                if memory_section:
                    # Inject BEFORE the task
                    enriched_system_prompt = self.base_system_prompt + "\n" + memory_section

                if self.verbose and (retrieved.get("facts") or retrieved.get("experiences")):
                    print(f"🧠 Memory retrieved:")
                    if retrieved.get("facts"):
                        print(f"   - {len(retrieved['facts'])} fact(s)")
                    if retrieved.get("experiences"):
                        print(f"   - {len(retrieved['experiences'])} experience(s)")
                    if retrieved.get("lessons"):
                        print(f"   - {len(retrieved['lessons'])} lesson(s)")
                    print()

            except Exception as e:
                logger.warning(f"Memory retrieval failed: {e}")
                enriched_system_prompt = self.base_system_prompt

        # STEP 3: Maintain conversation history (don't reset every time)
        #
        # IMPORTANT: This maintains context across turns BUT with safeguards:
        # 1. Token counter is RESET at start of each run() (line 133-136)
        # 2. Old messages are auto-truncated by _manage_context_window()
        # 3. Max context = history_keep_last_n * 2 (default: 10 messages)
        # 4. Token budget per task prevents overflow (max_total_tokens_per_task)
        #
        # Trade-off: More context = better AI understanding, but higher token usage per call
        if not self.messages or len(self.messages) == 0:
            # First conversation - initialize with system prompt
            self.messages = [
                {"role": "system", "content": enriched_system_prompt},
                {"role": "user", "content": user_input}
            ]
        else:
            # Ongoing conversation - update system prompt and append user message
            self.messages[0] = {"role": "system", "content": enriched_system_prompt}
            self.messages.append({"role": "user", "content": user_input})

        # STEP 4: Run LLM reasoning loop
        try:
            final_response = self._reasoning_loop()

            # STEP 5: Add assistant response to conversation history
            self.messages.append({
                "role": "assistant",
                "content": final_response
            })

            # STEP 6: Intelligently store memory (with filtering)
            if self.enable_memory:
                self._store_intelligently(user_input, final_response)

            # Reset token usage after task completion
            self.current_token_usage = 0
            self.total_tokens_used = 0
            self.llm.reset_token_stats()

            return final_response

        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            # Reset token usage after task completion
            self.current_token_usage = 0
            self.total_tokens_used = 0
            self.llm.reset_token_stats()
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

            # Manage context window before making request
            self._manage_context_window()

            # Call LLM with functions
            # Lower temperature for more deterministic function calling
            # Sufficient max_tokens for complete function arguments (including long code)
            response = self.llm.chat_with_functions(
                messages=self.messages,
                functions=self.functions,
                temperature=0.1,  # Very low temperature for strict function calling
                max_tokens=3072,  # Enough for complete function calls with long code arguments
                tool_choice="auto"
            )

            # Track token usage
            usage = response.get("usage", {})
            tokens_used = usage.get("total_tokens", 0)
            self.current_token_usage += tokens_used
            self.total_tokens_used += tokens_used

            # Check token budget
            if self.current_token_usage > self.max_tokens_per_task:
                logger.warning(
                    f"Token budget exceeded: {self.current_token_usage}/{self.max_tokens_per_task}"
                )
                raise TokenLimitExceededError(
                    f"Task token budget exceeded",
                    token_count=self.current_token_usage,
                    limit=self.max_tokens_per_task,
                    details={"iteration": iteration}
                )

            # Check if LLM wants to call tools
            tool_calls = response.get("tool_calls")

            # Check if this was a failed_generation fallback
            is_failed_generation = response.get("failed_generation", False)

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

            elif is_failed_generation and response.get("content"):
                # LLM failed to call function - RETRY with stricter prompt
                if self.verbose:
                    print(f"\n⚠️  LLM generated text instead of calling function")
                    print(f"   Attempting retry with stricter instructions...")

                # Add correction message to force function calling
                correction_msg = """
🚨 ERROR: You just generated text/code directly instead of calling a function!

This is WRONG and will cause API errors. You MUST:
1. Use function calling for ALL actions (write file, read file, etc)
2. NEVER write code blocks in your response
3. NEVER explain what you would do - DO IT by calling the tool

Please try again and CALL THE APPROPRIATE FUNCTION this time.
Remember: Your interface is FUNCTION CALLING, not text generation!
"""

                self.messages.append({
                    "role": "user",
                    "content": correction_msg
                })

                # Retry with even stricter settings
                if self.verbose:
                    print(f"   🔄 Retrying with stricter settings...")

                try:
                    retry_response = self.llm.chat_with_functions(
                        messages=self.messages,
                        functions=self.functions,
                        temperature=0.05,  # Even lower temperature for retry
                        max_tokens=3072,   # Same as initial attempt
                        tool_choice="auto"  # Force tool use if possible
                    )

                    # Check if retry succeeded with tool calls
                    retry_tool_calls = retry_response.get("tool_calls")
                    if retry_tool_calls:
                        if self.verbose:
                            print(f"   ✅ Retry successful! LLM is now calling {len(retry_tool_calls)} tool(s)")

                        # Add assistant message with tool calls
                        self.messages.append({
                            "role": "assistant",
                            "content": retry_response.get("content") or "",
                            "tool_calls": retry_tool_calls
                        })

                        # Execute tool calls
                        for tool_call in retry_tool_calls:
                            self._execute_tool_call(tool_call)

                        # Continue loop
                        continue
                    else:
                        # Retry also failed - fallback
                        if self.verbose:
                            print(f"   ⚠️  Retry failed - using fallback response")
                        final_content = retry_response.get("content") or response.get("content")
                        return final_content or "Task completed (with fallback due to function calling failure)."

                except Exception as retry_error:
                    logger.warning(f"Retry failed: {retry_error}")
                    if self.verbose:
                        print(f"   ❌ Retry error: {str(retry_error)}")
                    # Use original partial response
                    final_content = response.get("content")
                    return final_content or "Task completed (with fallback)."

            else:
                # LLM returned final response (no more tools)
                final_content = response.get("content")

                if self.verbose:
                    print(f"\n✅ LLM finished reasoning (no more tools needed)")
                    print(f"   Total iterations: {iteration}")
                    print(f"   Total tool calls: {self.total_tool_calls}")

                # Reset token usage will be done in run() method
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

        # Reset token usage will be done in run() method
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

    def _manage_context_window(self) -> None:
        """Manage context window to prevent overflow.

        Strategy:
        1. Keep system message (always first)
        2. Keep last N conversation turns (configurable)
        3. Truncate long tool results to summaries
        """
        if len(self.messages) <= 2:
            # Only system + first user message, nothing to manage
            return

        # Calculate current context size
        estimated_tokens = self._estimate_context_tokens()

        # If under limit and message count reasonable, no action needed
        max_messages = self.max_context_messages + 1  # +1 for system
        if len(self.messages) <= max_messages and estimated_tokens < (self.max_tokens_per_task * 0.7):
            return

        if self.verbose:
            logger.info(
                f"Managing context window: {len(self.messages)} messages, "
                f"~{estimated_tokens} tokens"
            )

        # Strategy: Keep system (0) and last N conversation messages
        system_msg = self.messages[0]
        conversation = self.messages[1:]

        # Keep only last N conversation messages
        keep_last_n = self.max_context_messages
        if len(conversation) > keep_last_n:
            truncated = conversation[-keep_last_n:]
            if self.verbose:
                logger.info(
                    f"Truncated conversation from {len(conversation)} to {len(truncated)} messages"
                )
            conversation = truncated

        # Rebuild messages list
        self.messages = [system_msg] + conversation

        # Truncate long tool results
        self._truncate_tool_results()

    def _estimate_context_tokens(self) -> int:
        """Estimate total tokens in current context.

        Returns:
            Estimated token count
        """
        total = 0
        for msg in self.messages:
            content = msg.get("content", "")
            if content:
                total += GroqClient.count_tokens_estimate(str(content))

            # Add tokens for tool calls
            if "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    total += 50  # Rough estimate for tool call structure

        return total

    def _truncate_tool_results(self, max_length: int = 500) -> None:
        """Truncate long tool results to prevent context overflow.

        Args:
            max_length: Maximum length for tool result content (default for most tools)
        """
        # Tools that produce large outputs and should NOT be truncated aggressively
        # (user needs full results for saving to files, analysis, etc.)
        LARGE_OUTPUT_TOOLS = {
            "enhanced_pentest": 20000,   # Pentest scans can have 100+ results
            "pentest": 20000,            # Legacy pentest tool
            "web_search": 5000,          # Search results need context
            "filesystem_read": 10000,    # File contents may be long
        }

        for msg in self.messages:
            if msg.get("role") == "tool":
                tool_name = msg.get("name", "")
                content = msg.get("content", "")

                # Determine max length based on tool type
                tool_max_length = LARGE_OUTPUT_TOOLS.get(tool_name, max_length)

                if len(content) > tool_max_length:
                    # Truncate and add indicator
                    truncated = content[:tool_max_length] + f"\n\n[...truncated {len(content) - tool_max_length} chars for context management. Full results are available in the tool's working directory.]"
                    msg["content"] = truncated

                    if self.verbose:
                        logger.debug(
                            f"Truncated {tool_name} result: {len(content)} → {tool_max_length} chars"
                        )

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

    def _load_meta_memory_prompt(self) -> str:
        """Load the meta-memory system prompt (NEW METHOD).

        Returns:
            System prompt string
        """
        prompt_file = Path("prompts/meta_memory_system_prompt.txt")

        if prompt_file.exists():
            try:
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load meta-memory prompt: {e}")

        # Fallback to basic prompt if file not found
        logger.warning("Meta-memory prompt file not found, using fallback")
        return create_function_calling_system_prompt(self.functions)

    def _store_intelligently(self, user_input: str, agent_response: str) -> None:
        """Intelligently store memory with filtering (NEW METHOD).

        Uses memory filter to classify and store only valuable information.

        Args:
            user_input: User's input
            agent_response: Agent's response
        """
        if not self.memory_filter or not self.learning_manager:
            return

        try:
            # Classify memory type
            metadata = {
                "tool_count": len(self.tools_executed),
                "iteration_count": self.total_iterations,
            }

            memory_type = self.memory_filter.classify_memory(
                user_input=user_input,
                agent_response=agent_response,
                task_success=True,
                metadata=metadata
            )

            if memory_type == MemoryType.USELESS:
                if self.verbose:
                    print(f"   ⏭️  Memory not stored (classified as useless)")
                return

            # Store based on type
            if memory_type == MemoryType.RULE:
                # Extract rule components
                rule_components = self.memory_filter.extract_rule_components(user_input)
                if rule_components and self.rule_engine:
                    trigger = rule_components["trigger"]
                    response = rule_components["response"]

                    # Store as rule
                    rule_id = self.rule_engine.add_rule(
                        trigger=trigger,
                        response=response,
                        trigger_type="contains",
                        priority=0
                    )

                    if self.verbose:
                        print(f"\n🔴 RULE STORED:")
                        print(f"   Trigger: '{trigger}'")
                        print(f"   Response: '{response}'")

            elif memory_type == MemoryType.FACT:
                # Extract fact info
                fact_info = self.memory_filter.extract_fact_info(user_input)
                if fact_info:
                    category = fact_info["category"]
                    value = fact_info["value"]

                    # Store as fact
                    fact_id = self.learning_manager.vector_memory.store_fact(
                        fact=value,
                        category=category,
                        metadata={"source": "user_input"}
                    )

                    if self.verbose:
                        print(f"\n📋 FACT STORED:")
                        print(f"   Category: {category}")
                        print(f"   Value: {value[:60]}...")

            elif memory_type == MemoryType.EXPERIENCE:
                # Store as experience (using existing logic)
                success = "error" not in agent_response.lower()
                actions = [f"{t['tool']}.{t.get('operation', 'execute')}" for t in self.tools_executed]

                # TASK IMPORTANCE FILTER: Check if experience is worthy of learning
                importance_filter = get_task_importance_filter()
                should_learn, importance_level, reason = importance_filter.should_learn(
                    task=user_input,
                    actions=actions,
                    outcome=agent_response[:500],
                    success=success,
                    errors=None,
                    context=metadata
                )

                if not should_learn:
                    logger.debug(f"Skipping learning for trivial experience: {reason}")
                    if self.verbose:
                        print(f"   ⏭️  Experience not stored (importance: {importance_level.value})")
                    return

                learning_summary = self.learning_manager.learn_from_task(
                    task=user_input,
                    actions=actions,
                    outcome=agent_response[:500],
                    success=success,
                    errors=None,
                    context={**metadata, "importance_level": importance_level.value}
                )

                if self.verbose:
                    lessons_count = learning_summary.get("lessons_count", 0)
                    print(f"\n💭 EXPERIENCE STORED (importance: {importance_level.value}):")
                    print(f"   Success: {success}")
                    if lessons_count > 0:
                        print(f"   Lessons: {lessons_count}")

        except Exception as e:
            logger.warning(f"Failed to store memory intelligently: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics.

        Returns:
            Dict with stats
        """
        return {
            "total_iterations": self.total_iterations,
            "total_tool_calls": self.total_tool_calls,
            "messages_in_history": len(self.messages),
            "functions_available": len(self.functions),
            "total_tokens_used": self.total_tokens_used,
            "current_token_usage": self.current_token_usage,
            "estimated_context_tokens": self._estimate_context_tokens(),
            "token_budget_remaining": max(0, self.max_tokens_per_task - self.current_token_usage)
        }

    def reset(self):
        """Reset conversation and stats."""
        self.messages = []
        self.total_iterations = 0
        self.total_tool_calls = 0
        self.total_tokens_used = 0
        self.current_token_usage = 0
        self.tools_executed = []

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
