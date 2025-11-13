"""Dual-mode orchestrator dengan routing cerdas.

Orchestrator baru yang:
- Classify task sebelum masuk ReAct loop
- Route simple tasks ke direct response
- Route complex tasks ke ReAct loop dengan control ketat
- Auto-stop saat jawaban sudah cukup
- Prevent looping dengan multiple mechanisms
"""

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
from agent.core.task_classifier import TaskClassifier, TaskType, get_task_classifier
from agent.core.answer_validator import AnswerValidator, get_answer_validator
from config.settings import settings

logger = logging.getLogger(__name__)


class DualOrchestrator:
    """Orchestrator dengan dual-mode routing dan anti-looping."""

    def __init__(
        self,
        llm_client: Optional[GroqClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        task_classifier: Optional[TaskClassifier] = None,
        answer_validator: Optional[AnswerValidator] = None,
        max_iterations: Optional[int] = None,
        verbose: bool = True,
        enable_persistence: bool = True,
        enable_learning: bool = True,
        session_manager: Optional[SessionManager] = None,
        learning_manager: Optional[LearningManager] = None
    ):
        """Initialize dual orchestrator.

        Args:
            llm_client: LLM client (defaults to global)
            tool_registry: Tool registry (defaults to global)
            task_classifier: Task classifier (defaults to global)
            answer_validator: Answer validator (defaults to global)
            max_iterations: Maximum iterations before stopping
            verbose: Whether to print detailed logs
            enable_persistence: Enable state persistence
            enable_learning: Enable reflective learning
            session_manager: Session manager (defaults to global)
            learning_manager: Learning manager (defaults to global)
        """
        self.llm = llm_client or get_groq_client()
        self.registry = tool_registry or get_registry()
        self.classifier = task_classifier or get_task_classifier(self.llm)
        self.validator = answer_validator or get_answer_validator()
        self.max_iterations = max_iterations or settings.max_iterations
        self.verbose = verbose
        self.enable_persistence = enable_persistence
        self.enable_learning = enable_learning
        self.session_manager = session_manager or (get_session_manager() if enable_persistence else None)
        self.learning_manager = learning_manager or (get_learning_manager() if enable_learning else None)

        # Agent state
        self.history: List[tuple[str, str]] = []
        self.current_task: Optional[str] = None
        self.task_type: Optional[TaskType] = None
        self.iteration = 0
        self.errors_encountered: List[str] = []

        logger.info(f"Dual orchestrator initialized with {len(self.registry)} tools")
        if self.enable_learning:
            logger.info("Reflective learning system enabled")

    def run(self, task: str) -> str:
        """Run agent on task with intelligent routing.

        Args:
            task: User task/question

        Returns:
            Final answer
        """
        self.current_task = task
        self.history = []
        self.iteration = 0
        self.errors_encountered = []

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"Task: {task}")
            print(f"{'='*70}\n")

        # ===== LAYER 1: TASK CLASSIFICATION =====
        task_type, confidence = self.classifier.classify(task)
        self.task_type = task_type

        if self.verbose:
            print(f"🔍 Task Classification: {task_type.value} (confidence: {confidence:.2f})")
            print(f"📊 Routing decision...")

        # ===== LAYER 2: INTELLIGENT ROUTING =====

        # Route 1: Conversational (no tools, direct response)
        if task_type == TaskType.CONVERSATIONAL:
            if self.verbose:
                print(f"✓ Route: DIRECT_RESPONSE (conversational)\n")
            return self._handle_conversational(task)

        # Route 2: Simple QA (no tools, but more context)
        if task_type == TaskType.SIMPLE_QA and confidence >= 0.7:
            if self.verbose:
                print(f"✓ Route: SIMPLE_QA (knowledge-based)\n")
            return self._handle_simple_qa(task)

        # Route 3: Complex tasks (ReAct loop with tools)
        if self.verbose:
            print(f"✓ Route: REACT_LOOP (tool-based)\n")

        # Get recommended settings from classifier
        required_tools = self.classifier.get_required_tools(task_type)
        temperature = self.classifier.get_temperature(task_type)
        max_iter = self.classifier.get_max_iterations(task_type)

        if self.verbose:
            print(f"🔧 Tools allowed: {required_tools if required_tools else 'ALL'}")
            print(f"🌡️  Temperature: {temperature}")
            print(f"🔄 Max iterations: {max_iter}\n")

        return self._react_loop(
            task=task,
            allowed_tools=required_tools,
            temperature=temperature,
            max_iterations=max_iter
        )

    def _handle_conversational(self, task: str) -> str:
        """Handle conversational tasks (greetings, casual chat).

        Args:
            task: Task text

        Returns:
            Direct response
        """
        # Check memory for similar conversations
        memory_context = ""
        if self.enable_learning and self.learning_manager:
            try:
                relevant = self.learning_manager.get_relevant_experience(task, n_results=3)

                if relevant["similar_experiences"]:
                    if self.verbose:
                        print(f"💭 Found {len(relevant['similar_experiences'])} similar past conversations\n")

                    # Build memory context
                    memory_context = "\n\nKonteks dari percakapan sebelumnya:\n"
                    for i, exp in enumerate(relevant["similar_experiences"][:2], 1):
                        memory_context += f"{i}. User: {exp.get('task', '')[:100]}\n"
                        memory_context += f"   Response: {exp.get('outcome', '')[:100]}\n"

            except Exception as e:
                logger.debug(f"Memory recall failed: {e}")

        # Ultra-simple conversational prompt with memory
        prompt = f"""Kamu adalah Radira, AI assistant yang ramah.{memory_context}

User berkata: "{task}"

Berikan respons natural dan ramah dalam 1-2 kalimat. Jika user menanyakan percakapan sebelumnya dan ada konteks di atas, gunakan informasi tersebut. Jangan gunakan tools atau format khusus."""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Deterministic
                max_tokens=200  # Short response
            )

            answer = response["content"].strip()

            if self.verbose:
                print(f"💬 Response: {answer}\n")
                print(f"📊 Tokens used: {response['usage']['total_tokens']}\n")

            # Learn from this simple task
            if self.enable_learning and self.learning_manager:
                self._learn_from_simple_task(task, answer, success=True)

            return answer

        except Exception as e:
            logger.error(f"Conversational handling failed: {e}")
            return "Maaf, ada error saat memproses permintaan kamu."

    def _handle_simple_qa(self, task: str) -> str:
        """Handle simple Q&A without tools.

        Args:
            task: Question

        Returns:
            Answer
        """
        # Check memory for similar questions
        memory_context = ""
        if self.enable_learning and self.learning_manager:
            try:
                relevant = self.learning_manager.get_relevant_experience(task, n_results=3)

                if relevant["similar_experiences"]:
                    if self.verbose:
                        print(f"💭 Found {len(relevant['similar_experiences'])} similar past questions\n")

                    # Build memory context
                    memory_context = "\n\nKonteks dari pertanyaan serupa sebelumnya:\n"
                    for i, exp in enumerate(relevant["similar_experiences"][:2], 1):
                        memory_context += f"{i}. Q: {exp.get('task', '')[:100]}\n"
                        memory_context += f"   A: {exp.get('outcome', '')[:100]}\n"

            except Exception as e:
                logger.debug(f"Memory recall failed: {e}")

        prompt = f"""Kamu adalah Radira, AI assistant yang knowledgeable.{memory_context}

Pertanyaan: {task}

Jawab dengan jelas dan ringkas berdasarkan pengetahuanmu. Jika ada konteks di atas dan relevan, gunakan informasi tersebut. Jika tidak tahu, katakan dengan jujur."""

        try:
            response = self.llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Mostly deterministic
                max_tokens=800  # Moderate length
            )

            answer = response["content"].strip()

            if self.verbose:
                print(f"💡 Answer: {answer}\n")
                print(f"📊 Tokens used: {response['usage']['total_tokens']}\n")

            # Learn from this
            if self.enable_learning and self.learning_manager:
                self._learn_from_simple_task(task, answer, success=True)

            return answer

        except Exception as e:
            logger.error(f"Simple QA handling failed: {e}")
            return f"Maaf, ada error: {str(e)}"

    def _react_loop(
        self,
        task: str,
        allowed_tools: List[str],
        temperature: float,
        max_iterations: int
    ) -> str:
        """Execute ReAct loop with strict controls.

        Args:
            task: Task to execute
            allowed_tools: List of allowed tool names
            temperature: LLM temperature
            max_iterations: Max iterations

        Returns:
            Final answer
        """
        # Filter tools if restrictions specified
        if allowed_tools:
            tools = [t for t in self.registry.list_tools() if t.name in allowed_tools]
        else:
            tools = self.registry.list_tools()

        if not tools:
            logger.warning("No tools available")
            return "Error: No tools available for this task."

        # Retrieve relevant past experiences
        if self.enable_learning and self.learning_manager:
            try:
                relevant_experience = self.learning_manager.get_relevant_experience(task, n_results=2)

                if relevant_experience["similar_experiences"] and self.verbose:
                    success_count = sum(1 for e in relevant_experience["similar_experiences"] if e.get("success", False))
                    print(f"💡 Found {len(relevant_experience['similar_experiences'])} similar past experiences")
                    print(f"   {success_count} successful, {len(relevant_experience['similar_experiences']) - success_count} failed")

                    if relevant_experience["relevant_lessons"]:
                        print(f"📚 Relevant lessons:")
                        for lesson in relevant_experience["relevant_lessons"][:2]:
                            print(f"   • {lesson['lesson'][:70]}...")
                    print()
            except Exception as e:
                logger.warning(f"Could not retrieve past experiences: {e}")

        # Create system prompt with tool guidance
        system_prompt = self._create_enhanced_system_prompt(tools)

        # ===== MAIN REACT LOOP =====
        while self.iteration < max_iterations:
            self.iteration += 1

            # Rate limiting delay
            if self.iteration > 1 and settings.iteration_delay_seconds > 0:
                if self.verbose:
                    print(f"⏱️  Rate limit delay: {settings.iteration_delay_seconds}s\n")
                time.sleep(settings.iteration_delay_seconds)

            if self.verbose:
                print(f"--- Iteration {self.iteration}/{max_iterations} ---\n")

            # Trim history to save tokens
            trimmed_history = self.history[-settings.history_keep_last_n:] if len(self.history) > settings.history_keep_last_n else self.history

            # Create ReAct prompt
            prompt = create_react_prompt(
                question=task,
                tools=tools,
                history=trimmed_history,
                current_iteration=self.iteration,
                max_iterations=max_iterations
            )

            # Get LLM response
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
                        temperature=temperature,
                        max_tokens=settings.max_tokens_per_response
                    )
                    response_text = response["content"]

                    # Check token budget
                    total_tokens_used = self.llm.get_token_stats()["total_tokens"]
                    if total_tokens_used > settings.max_total_tokens_per_task:
                        logger.warning(f"Token budget exceeded: {total_tokens_used}/{settings.max_total_tokens_per_task}")
                        if self.verbose:
                            print(f"⚠️  Token budget exceeded: {total_tokens_used}/{settings.max_total_tokens_per_task}\n")
                        return self._force_conclusion(task)

                    if self.verbose:
                        print(f"Agent Response:\n{response_text}\n")
                        tokens_this_iteration = response["usage"]["total_tokens"]
                        print(f"📊 Tokens: {tokens_this_iteration} | Total: {total_tokens_used}/{settings.max_total_tokens_per_task}\n")

                    break  # Success

                except Exception as e:
                    error_msg = str(e).lower()

                    if "429" in error_msg or "rate limit" in error_msg:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 2 ** retry_count
                            logger.warning(f"Rate limit hit. Retrying in {wait_time}s...")
                            if self.verbose:
                                print(f"⚠️  Rate limit. Waiting {wait_time}s...\n")
                            time.sleep(wait_time)
                        else:
                            logger.error(f"Max retries reached")
                            return f"Error: Rate limit exceeded after {max_retries} retries."
                    else:
                        logger.error(f"LLM error: {e}")
                        return f"Error: {str(e)}"

            if response_text is None:
                return "Error: Failed to get response"

            # Parse response
            parsed = ReActParser.parse(response_text)

            # Validate response
            is_valid, error_msg = ReActParser.validate(parsed)
            if not is_valid:
                logger.error(f"Invalid response: {error_msg}")
                if self.verbose:
                    print(f"⚠️  Invalid response: {error_msg}\n")
                continue

            # Check for final answer
            if ReActParser.is_final_answer(parsed):
                final_answer = parsed["final_answer"]
                if self.verbose:
                    print(f"\n{'='*70}")
                    print(f"✓ Final Answer: {final_answer}")
                    print(f"{'='*70}\n")
                    print(f"Completed in {self.iteration} iterations")
                    self._print_stats()

                # Learn from success
                if self.enable_learning and self.learning_manager:
                    self._learn_from_execution(success=True, outcome=final_answer)

                return final_answer

            # Execute action
            action = parsed["action"]
            action_input = parsed.get("action_input", {})

            # ===== ANTI-LOOPING MECHANISMS =====

            # 1. Check for loop
            if self._is_looping(action):
                if self.verbose:
                    print(f"⚠️  Loop detected: '{action}' repeated. Breaking loop...\n")

                # Force final answer if we have sufficient observation
                if self.history:
                    last_obs = self.history[-1][1]
                    if len(last_obs) > 50 and not self._is_error(last_obs):
                        return self._force_conclusion(task, last_obs)

                # Give strong hint
                observation = f"STOP: You're repeating '{action}'. Either provide Final Answer with current information or try completely different approach."
                if self.verbose:
                    print(f"← Observation: {observation}\n")
                self.history.append((action, observation))
                continue

            # 2. Check if should force final answer
            should_force, reason = self.validator.should_force_final_answer(
                iteration=self.iteration,
                max_iterations=max_iterations,
                history=self.history,
                last_observation=self.history[-1][1] if self.history else ""
            )

            if should_force:
                if self.verbose:
                    print(f"🛑 Forcing Final Answer: {reason}\n")
                return self._force_conclusion(task)

            if self.verbose:
                print(f"→ Action: {action}")
                print(f"→ Input: {action_input}\n")

            # Execute tool
            observation = self._execute_action(action, action_input)

            if self.verbose:
                print(f"← Observation: {observation}\n")

            # Add to history
            self.history.append((action, observation))

            # 3. Check if answer is sufficient (auto-stop)
            thought = parsed.get("thought", "")
            is_sufficient, suff_reason = self.validator.is_sufficient(
                task=task,
                observation=observation,
                thought=thought,
                history=self.history
            )

            if is_sufficient:
                if self.verbose:
                    print(f"✓ Answer validator: Sufficient! ({suff_reason})\n")
                    print(f"🎯 Auto-extracting final answer...\n")

                return self._force_conclusion(task, observation)

        # Max iterations reached
        return self._force_conclusion(task)

    def _create_enhanced_system_prompt(self, tools: List) -> str:
        """Create system prompt with enhanced guidance.

        Args:
            tools: Available tools

        Returns:
            System prompt
        """
        base_prompt = create_system_prompt(tools)

        # Add enhanced guidance
        enhanced = base_prompt + """

## ⚠️  CRITICAL: When to Use Tools vs Direct Answer

**Use Tools ONLY when:**
- Task explicitly requires file operations (read, write, create)
- Task needs web search for current/real-time information
- Task requires terminal commands or system operations
- Task needs security testing (pentest tools)

**Provide Direct Answer (Final Answer) when:**
- Task is conversational (greetings, thanks, casual chat)
- You can answer from knowledge without verification
- You already have sufficient information from previous observations
- Task is simple Q&A about concepts, definitions, explanations

## 🛑 When to STOP (Provide Final Answer)

**MUST provide Final Answer immediately when:**
- You have successfully completed the operation (file created, command executed)
- Observation contains the answer to user's question
- You're about to repeat a tool you already used
- You have enough information to answer
- You see "successfully", "completed", "done" in observation

**Example - WRONG (loops unnecessarily):**
```
Thought: File created successfully. Let me verify by reading it again.
Action: file_system
```

**Example - CORRECT (stops appropriately):**
```
Thought: File created successfully. Task complete.
Final Answer: File halo.txt has been created successfully with the content you requested.
```

## 🎯 Quality Over Quantity

- Do NOT use tools "just to verify" or "to be sure"
- Do NOT repeat successful operations
- Do NOT search when you already know the answer
- **Provide Final Answer as soon as task is complete**
"""

        return enhanced

    def _is_looping(self, current_action: str) -> bool:
        """Check if agent is in a loop.

        Args:
            current_action: Current action being attempted

        Returns:
            True if looping detected
        """
        if len(self.history) < 2:
            return False

        # Check last 4 actions
        recent_actions = [action for action, _ in self.history[-4:]]

        # Count occurrences of current action
        count = recent_actions.count(current_action)

        # Loop if same action 2+ times in last 4
        return count >= 2

    def _is_error(self, observation: str) -> bool:
        """Check if observation is an error.

        Args:
            observation: Observation text

        Returns:
            True if error
        """
        obs_lower = observation.lower()
        return any(err in obs_lower for err in ["error:", "failed", "could not", "unable"])

    def _force_conclusion(self, task: str, last_observation: Optional[str] = None) -> str:
        """Force conclusion when agent is stuck or max iterations reached.

        Args:
            task: Original task
            last_observation: Last observation (optional)

        Returns:
            Forced conclusion
        """
        if self.verbose:
            print(f"\n🎯 Forcing conclusion...\n")

        # If we have a valid last observation, use it
        if last_observation and len(last_observation) > 20:
            answer = self.validator.extract_answer_from_observation(last_observation, task)

            if self.verbose:
                print(f"✓ Extracted answer from observation\n")

            # Learn from this
            if self.enable_learning and self.learning_manager:
                self._learn_from_execution(success=True, outcome=answer)

            return answer

        # Otherwise, summarize what we've done
        if self.history:
            actions_taken = [action for action, _ in self.history]
            last_obs = self.history[-1][1] if self.history else "None"

            outcome = f"Task incomplete after {self.iteration} iterations. Actions attempted: {', '.join(actions_taken)}. Last result: {last_obs[:200]}"
        else:
            outcome = f"Task could not be completed. No actions were successfully executed."

        # Learn from incomplete task
        if self.enable_learning and self.learning_manager:
            self._learn_from_execution(success=False, outcome=outcome)

        return outcome

    def _execute_action(self, action: str, action_input: Any) -> str:
        """Execute a tool action.

        Args:
            action: Tool name
            action_input: Tool input

        Returns:
            Observation string
        """
        try:
            if not self.registry.has(action):
                available = ", ".join(self.registry.list_tool_names())
                error_msg = f"Error: Tool '{action}' not found. Available: {available}"
                self.errors_encountered.append(error_msg)
                return error_msg

            tool = self.registry.get(action)

            if tool.is_dangerous and tool.requires_confirmation:
                logger.warning(f"Dangerous tool '{action}' requires confirmation")

            # Prepare input
            if isinstance(action_input, dict):
                kwargs = action_input
            elif isinstance(action_input, str):
                kwargs = {"input": action_input}
            else:
                kwargs = {}

            # Check error prevention strategy
            if self.enable_learning and self.learning_manager:
                operation = kwargs.get("operation", "unknown")
                prevention = self.learning_manager.get_error_prevention_strategy(
                    tool_name=action,
                    operation=operation,
                    params=kwargs
                )

                if prevention and self.verbose:
                    warnings = prevention.get("warnings", [])
                    validations = prevention.get("recommended_validations", [])

                    if warnings:
                        print(f"⚠️  Error Prevention Warnings:")
                        for warning in warnings:
                            print(f"   • {warning}")

                    if validations:
                        print(f"📋 Recommended validations: {', '.join(validations)}")

                    confidence = prevention.get("confidence", 0)
                    if confidence > 0.7:
                        print(f"   Confidence: {confidence:.0%} (based on {prevention.get('similar_error_count', 0)} past errors)\n")

            # Execute tool
            result: ToolResult = self.registry.execute(action, **kwargs)

            if result.is_success:
                observation = str(result.output)
            else:
                error_msg = f"Error: {result.error}"
                self.errors_encountered.append(error_msg)
                observation = error_msg

                # Display remediation info if available and verbose
                if self.verbose and result.metadata and 'remediation' in result.metadata:
                    remediation = result.metadata['remediation']
                    if remediation:
                        severity_emoji = {
                            'high': '🔴',
                            'medium': '🟡',
                            'low': '🟢'
                        }.get(remediation.get('severity', 'medium'), '🟡')

                        action_type_label = {
                            'create': 'Create/Add',
                            'validate': 'Validate',
                            'config': 'Configuration',
                            'permission': 'Permissions',
                            'install': 'Installation',
                            'manual': 'Manual Fix'
                        }.get(remediation.get('action_type', 'manual'), 'Action')

                        print(f"\n{severity_emoji} Remediation Suggestion ({action_type_label}):")
                        print(f"   {remediation['suggestion']}")

                        if remediation.get('auto_fixable'):
                            print(f"   ✨ This error may be auto-fixable in future versions\n")

            return observation

        except Exception as e:
            logger.error(f"Action execution error: {e}")
            error_msg = f"Error executing '{action}': {str(e)}"
            self.errors_encountered.append(error_msg)
            return error_msg

    def _learn_from_simple_task(self, task: str, answer: str, success: bool):
        """Learn from simple task (conversational/QA).

        Args:
            task: Task
            answer: Answer
            success: Success status
        """
        if not self.enable_learning or not self.learning_manager:
            return

        try:
            self.learning_manager.learn_from_task(
                task=task,
                actions=["direct_response"],
                outcome=answer,
                success=success,
                errors=[],
                context={"task_type": self.task_type.value if self.task_type else "unknown"}
            )
        except Exception as e:
            logger.warning(f"Failed to learn from simple task: {e}")

    def _learn_from_execution(self, success: bool, outcome: str):
        """Learn from ReAct execution.

        Args:
            success: Success status
            outcome: Outcome
        """
        if not self.enable_learning or not self.learning_manager:
            return

        try:
            actions = [action for action, _ in self.history]
            task = self.current_task or "Unknown task"

            if self.verbose:
                print(f"\n🧠 Reflecting on execution...\n")

            learning_summary = self.learning_manager.learn_from_task(
                task=task,
                actions=actions,
                outcome=outcome,
                success=success,
                errors=self.errors_encountered,
                context={
                    "iterations": self.iteration,
                    "task_type": self.task_type.value if self.task_type else "unknown"
                }
            )

            if self.verbose:
                lessons_count = learning_summary.get("lessons_count", 0)
                strategies_count = learning_summary.get("strategies_count", 0)

                print(f"   ✓ Stored experience: {learning_summary['experience_id']}")
                if lessons_count > 0:
                    print(f"   ✓ Learned {lessons_count} lesson(s)")
                if strategies_count > 0:
                    print(f"   ✓ Recorded {strategies_count} strategy(ies)")

                improvements = learning_summary.get("improvements_suggested", [])
                if improvements:
                    print(f"   💡 Improvements:")
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
        print(f"Task Type: {self.task_type.value if self.task_type else 'unknown'}")
        print(f"Iterations: {self.iteration}")
        print(f"Actions taken: {len(self.history)}")

        token_stats = self.llm.get_token_stats()
        print(f"Total tokens: {token_stats['total_tokens']}")
        print(f"  - Prompt: {token_stats['prompt_tokens']}")
        print(f"  - Completion: {token_stats['completion_tokens']}")

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
        self.task_type = None
        self.iteration = 0
        self.errors_encountered = []
        self.llm.reset_token_stats()
        logger.info("Agent state reset")

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state.

        Returns:
            State dict
        """
        return {
            "current_task": self.current_task,
            "task_type": self.task_type.value if self.task_type else None,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "history": self.history,
            "token_stats": self.llm.get_token_stats(),
            "tool_stats": self.registry.get_stats()
        }
