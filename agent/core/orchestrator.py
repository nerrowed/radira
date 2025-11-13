"""Agent orchestrator - the brain of the autonomous agent."""

import logging
import time
from typing import List, Dict, Any, Optional
from agent.llm.groq_client import GroqClient, get_groq_client
from agent.llm.prompts import create_system_prompt, create_react_prompt
from agent.llm.parsers import ReActParser
from agent.tools.registry import ToolRegistry, get_registry
from agent.tools.base import ToolResult, ToolStatus
from agent.state.session import SessionManager, get_session_manager
from agent.learning.learning_manager import LearningManager, get_learning_manager
from config.settings import settings

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Main orchestrator for the autonomous agent using ReAct pattern."""

    def __init__(
        self,
        llm_client: Optional[GroqClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_iterations: Optional[int] = None,
        verbose: bool = True,
        enable_persistence: bool = True,
        session_manager: Optional[SessionManager] = None,
        enable_learning: bool = True,
        learning_manager: Optional[LearningManager] = None
    ):
        """Initialize agent orchestrator.

        Args:
            llm_client: LLM client (defaults to global GroqClient)
            tool_registry: Tool registry (defaults to global registry)
            max_iterations: Maximum iterations before stopping (default from settings)
            verbose: Whether to print detailed logs
            enable_persistence: Enable state persistence
            session_manager: Session manager (defaults to global)
            enable_learning: Enable reflective learning system
            learning_manager: Learning manager (defaults to global)
        """
        self.llm = llm_client or get_groq_client()
        self.registry = tool_registry or get_registry()
        self.max_iterations = max_iterations or settings.max_iterations
        self.verbose = verbose
        self.enable_persistence = enable_persistence
        self.enable_learning = enable_learning
        self.session_manager = session_manager or (get_session_manager() if enable_persistence else None)
        self.learning_manager = learning_manager or (get_learning_manager() if enable_learning else None)

        # Agent state
        self.history: List[tuple[str, str]] = []
        self.current_task: Optional[str] = None
        self.iteration = 0
        self.errors_encountered: List[str] = []

        logger.info(f"Agent initialized with {len(self.registry)} tools")
        if self.enable_learning:
            logger.info("Reflective learning system enabled")

    def run(self, task: str) -> str:
        """Run agent on a task using ReAct pattern.

        Args:
            task: User task/question to accomplish

        Returns:
            Final answer from agent
        """
        self.current_task = task
        self.history = []
        self.iteration = 0
        self.errors_encountered = []

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"Task: {task}")
            print(f"{'='*60}\n")

        # Get available tools
        tools = self.registry.list_tools()
        if not tools:
            logger.warning("No tools available in registry")
            return "Error: No tools available to complete the task."

        # Retrieve relevant past experiences (if learning enabled)
        if self.enable_learning and self.learning_manager:
            try:
                relevant_experience = self.learning_manager.get_relevant_experience(task, n_results=2)

                if relevant_experience["similar_experiences"]:
                    success_count = sum(1 for e in relevant_experience["similar_experiences"] if e.get("success", False))
                    if self.verbose:
                        print(f"💡 Found {len(relevant_experience['similar_experiences'])} similar past experiences")
                        print(f"   {success_count} successful, {len(relevant_experience['similar_experiences']) - success_count} failed")

                        # Show relevant lessons
                        if relevant_experience["relevant_lessons"]:
                            print(f"📚 Relevant lessons learned:")
                            for lesson in relevant_experience["relevant_lessons"][:2]:
                                print(f"   • {lesson['lesson'][:80]}...")
                        print()
            except Exception as e:
                logger.warning(f"Could not retrieve past experiences: {e}")

        # Create system prompt
        system_prompt = create_system_prompt(tools)

        # ReAct loop
        while self.iteration < self.max_iterations:
            self.iteration += 1

            # Rate limiting: add delay between iterations (except first one)
            if self.iteration > 1 and settings.iteration_delay_seconds > 0:
                if self.verbose:
                    print(f"⏱️  Rate limit delay: {settings.iteration_delay_seconds}s\n")
                time.sleep(settings.iteration_delay_seconds)

            if self.verbose:
                print(f"--- Iteration {self.iteration}/{self.max_iterations} ---\n")

            # Trim history to save tokens (keep only last N iterations)
            trimmed_history = self.history[-settings.history_keep_last_n:] if len(self.history) > settings.history_keep_last_n else self.history

            # Create prompt with current context
            prompt = create_react_prompt(
                question=task,
                tools=tools,
                history=trimmed_history,
                current_iteration=self.iteration,
                max_iterations=self.max_iterations
            )

            # Get LLM response with retry logic for rate limits
            max_retries = 3
            retry_count = 0
            response_text = None

            while retry_count < max_retries:
                try:
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                    response = self.llm.chat(
                        messages=messages,
                        temperature=0.3,
                        max_tokens=settings.max_tokens_per_response
                    )
                    response_text = response["content"]

                    # Check token budget
                    total_tokens_used = self.llm.get_token_stats()["total_tokens"]
                    if total_tokens_used > settings.max_total_tokens_per_task:
                        logger.warning(f"Token budget exceeded: {total_tokens_used}/{settings.max_total_tokens_per_task}")
                        if self.verbose:
                            print(f"⚠️  Token budget exceeded: {total_tokens_used}/{settings.max_total_tokens_per_task}\n")
                        return f"Task stopped: Token budget exceeded ({total_tokens_used} tokens used, limit: {settings.max_total_tokens_per_task})"

                    if self.verbose:
                        print(f"Agent Response:\n{response_text}\n")
                        # Show token usage per iteration
                        tokens_this_iteration = response["usage"]["total_tokens"]
                        print(f"📊 Tokens this iteration: {tokens_this_iteration} | Total: {total_tokens_used}/{settings.max_total_tokens_per_task}\n")

                    break  # Success, exit retry loop

                except Exception as e:
                    error_msg = str(e).lower()

                    # Check if it's a rate limit error
                    if "429" in error_msg or "rate limit" in error_msg or "too many requests" in error_msg:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                            logger.warning(f"Rate limit hit. Retrying in {wait_time}s... (attempt {retry_count}/{max_retries})")
                            if self.verbose:
                                print(f"⚠️  Rate limit (429). Waiting {wait_time}s before retry...\n")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Max retries reached for rate limit")
                            return f"Error: Rate limit exceeded after {max_retries} retries. Please wait and try again."
                    else:
                        # Other errors, fail immediately
                        logger.error(f"LLM error: {e}")
                        return f"Error: Failed to get response from LLM: {str(e)}"

            if response_text is None:
                return "Error: Failed to get response after retries"

            # Parse response
            parsed = ReActParser.parse(response_text)

            # Validate response
            is_valid, error_msg = ReActParser.validate(parsed)
            if not is_valid:
                logger.error(f"Invalid response: {error_msg}")
                if self.verbose:
                    print(f"⚠️  Invalid response: {error_msg}\n")
                # Try to continue with next iteration
                continue

            # Check for final answer
            if ReActParser.is_final_answer(parsed):
                final_answer = parsed["final_answer"]
                if self.verbose:
                    print(f"\n{'='*60}")
                    print(f"✓ Final Answer: {final_answer}")
                    print(f"{'='*60}\n")
                    print(f"Completed in {self.iteration} iterations")
                    self._print_stats()

                # Learn from this successful task
                if self.enable_learning and self.learning_manager:
                    self._learn_from_execution(
                        success=True,
                        outcome=final_answer
                    )

                return final_answer

            # Execute action
            action = parsed["action"]
            action_input = parsed.get("action_input", {})

            # Detect infinite loops (same action repeated)
            if len(self.history) >= 2:
                recent_actions = [a for a, _ in self.history[-3:]]  # Last 3 actions
                if recent_actions.count(action) >= 2:
                    logger.warning(f"Loop detected: '{action}' repeated {recent_actions.count(action)} times")
                    if self.verbose:
                        print(f"⚠️  Loop detected: Action '{action}' being repeated. Trying to break the loop...\n")

                    # Give agent a hint to try different approach
                    observation = f"Loop detected: You've already tried '{action}' multiple times with no progress. Try a different approach or provide Final Answer if task is complete."
                    if self.verbose:
                        print(f"← Observation: {observation}\n")
                    self.history.append((action, observation))
                    continue

            if self.verbose:
                print(f"→ Action: {action}")
                print(f"→ Input: {action_input}\n")

            # Execute tool
            observation = self._execute_action(action, action_input)

            if self.verbose:
                print(f"← Observation: {observation}\n")

            # Add to history
            self.history.append((action, observation))

        # Max iterations reached
        outcome = f"Task incomplete: Maximum iterations ({self.max_iterations}) reached. Last observation: {self.history[-1][1] if self.history else 'None'}"

        if self.verbose:
            print(f"\n⚠️  Max iterations ({self.max_iterations}) reached without final answer\n")
            self._print_stats()

        # Learn from this incomplete task
        if self.enable_learning and self.learning_manager:
            self._learn_from_execution(
                success=False,
                outcome=outcome
            )

        return outcome

    def _execute_action(self, action: str, action_input: Any) -> str:
        """Execute a tool action.

        Args:
            action: Tool name
            action_input: Tool input (dict or string)

        Returns:
            Observation string
        """
        try:
            # Check if tool exists
            if not self.registry.has(action):
                available = ", ".join(self.registry.list_tool_names())
                error_msg = f"Error: Tool '{action}' not found. Available tools: {available}"
                self.errors_encountered.append(error_msg)
                return error_msg

            # Get tool
            tool = self.registry.get(action)

            # Check if dangerous and needs confirmation
            if tool.is_dangerous and tool.requires_confirmation:
                logger.warning(f"Dangerous tool '{action}' requires confirmation")
                # In a real implementation, this would ask user for confirmation
                # For now, we'll allow it but log it
                pass

            # Prepare input
            if isinstance(action_input, dict):
                kwargs = action_input
            elif isinstance(action_input, str):
                # Try to use as single parameter
                # This is a simplified approach - real implementation might be smarter
                kwargs = {"input": action_input}
            else:
                kwargs = {}

            # Execute tool
            result: ToolResult = self.registry.execute(action, **kwargs)

            # Format observation
            if result.is_success:
                observation = str(result.output)
            else:
                error_msg = f"Error: {result.error}"
                self.errors_encountered.append(error_msg)
                observation = error_msg

            return observation

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            error_msg = f"Error executing tool '{action}': {str(e)}"
            self.errors_encountered.append(error_msg)
            return error_msg

    def _learn_from_execution(self, success: bool, outcome: str):
        """Learn from task execution.

        Args:
            success: Whether task was successful
            outcome: Final outcome
        """
        if not self.enable_learning or not self.learning_manager:
            return

        try:
            # Extract actions from history
            actions = [action for action, _ in self.history]

            # Get task
            task = self.current_task or "Unknown task"

            if self.verbose:
                print(f"\n🧠 Reflecting on execution...")

            # Learn from task
            learning_summary = self.learning_manager.learn_from_task(
                task=task,
                actions=actions,
                outcome=outcome,
                success=success,
                errors=self.errors_encountered,
                context={
                    "iterations": self.iteration,
                    "max_iterations": self.max_iterations
                }
            )

            if self.verbose:
                lessons_count = learning_summary.get("lessons_count", 0)
                strategies_count = learning_summary.get("strategies_count", 0)

                print(f"   ✓ Stored experience: {learning_summary['experience_id']}")
                if lessons_count > 0:
                    print(f"   ✓ Learned {lessons_count} lesson(s)")
                if strategies_count > 0:
                    print(f"   ✓ Recorded {strategies_count} successful strategy(ies)")

                # Show improvements
                improvements = learning_summary.get("improvements_suggested", [])
                if improvements:
                    print(f"   💡 Improvement suggestions:")
                    for imp in improvements[:2]:
                        print(f"      • {imp}")

                print()

        except Exception as e:
            logger.error(f"Failed to learn from execution: {e}")
            if self.verbose:
                print(f"   ⚠️  Learning failed: {e}\n")

    def _print_stats(self):
        """Print agent statistics."""
        if not self.verbose:
            return

        print(f"\n--- Agent Statistics ---")
        print(f"Iterations: {self.iteration}")
        print(f"Actions taken: {len(self.history)}")

        # Token stats
        token_stats = self.llm.get_token_stats()
        print(f"Total tokens used: {token_stats['total_tokens']}")
        print(f"  - Prompt: {token_stats['prompt_tokens']}")
        print(f"  - Completion: {token_stats['completion_tokens']}")

        # Tool stats
        tool_stats = self.registry.get_stats()
        if tool_stats:
            print(f"\nTool Usage:")
            for tool_name, stats in tool_stats.items():
                if stats['execution_count'] > 0:
                    print(f"  - {tool_name}: {stats['execution_count']} times "
                          f"(avg: {stats['average_execution_time']:.2f}s)")

    def reset(self):
        """Reset agent state."""
        self.history = []
        self.current_task = None
        self.iteration = 0
        self.llm.reset_token_stats()
        logger.info("Agent state reset")

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state.

        Returns:
            Dict with agent state
        """
        return {
            "current_task": self.current_task,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "history": self.history,
            "token_stats": self.llm.get_token_stats(),
            "tool_stats": self.registry.get_stats()
        }


class SimpleAgent:
    """Simplified agent for quick single-action tasks."""

    def __init__(self, llm_client: Optional[GroqClient] = None):
        """Initialize simple agent.

        Args:
            llm_client: LLM client
        """
        self.llm = llm_client or get_groq_client()

    def ask(self, question: str, context: Optional[str] = None) -> str:
        """Ask a question without tool usage.

        Args:
            question: Question to ask
            context: Optional context

        Returns:
            Answer string
        """
        if context:
            prompt = f"Context: {context}\n\nQuestion: {question}"
        else:
            prompt = question

        response = self.llm.quick_chat(prompt)
        return response

    def generate_code(self, description: str, language: str = "python") -> str:
        """Generate code from description.

        Args:
            description: Code description
            language: Programming language

        Returns:
            Generated code
        """
        prompt = f"Generate {language} code for: {description}\n\nProvide only the code, no explanations."
        response = self.llm.chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response["content"]
