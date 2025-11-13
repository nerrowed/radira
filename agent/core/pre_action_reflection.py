"""Pre-Action Reflection System.

Sistem untuk membuat AI "berpikir" dan reflect sebelum mengambil action.
Mencegah action mismatch dengan intent user.

Contoh masalah yang dicegah:
- User: "baca file X" → AI langsung buat file (SALAH!)
- Seharusnya: Check file exists dulu, kalau tidak ada → report error

Dengan reflection:
1. AI understand intent: "user mau BACA file"
2. AI check prerequisite: "file harus exist untuk dibaca"
3. AI validate: "apakah file exist?"
4. Jika tidak exist: "report error, jangan buat file baru!"
5. Jika exist: "proceed dengan read"
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Type of action to be taken."""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    MODIFY_FILE = "modify_file"
    DELETE_FILE = "delete_file"
    RUN_COMMAND = "run_command"
    SEARCH = "search"
    ANALYZE = "analyze"
    RESPOND = "respond"
    ASK_CLARIFICATION = "ask_clarification"


class ReflectionResult:
    """Result of pre-action reflection."""

    def __init__(
        self,
        should_proceed: bool,
        reasoning: str,
        alternative_action: Optional[str] = None,
        questions_for_user: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ):
        """Initialize reflection result.

        Args:
            should_proceed: Whether to proceed with planned action
            reasoning: Reasoning behind decision
            alternative_action: Suggested alternative if not proceeding
            questions_for_user: Questions to ask user for clarification
            warnings: Warnings about potential issues
        """
        self.should_proceed = should_proceed
        self.reasoning = reasoning
        self.alternative_action = alternative_action
        self.questions_for_user = questions_for_user or []
        self.warnings = warnings or []


class PreActionReflection:
    """System for reflecting before taking action."""

    def __init__(self, llm_client):
        """Initialize pre-action reflection.

        Args:
            llm_client: LLM client for reflection
        """
        self.llm = llm_client

    def reflect_before_action(
        self,
        user_intent: str,
        planned_action: str,
        action_parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ReflectionResult:
        """Reflect on planned action before execution.

        Args:
            user_intent: What user wants (from intent understanding)
            planned_action: Action AI plans to take
            action_parameters: Parameters for the action
            context: Additional context (file exists, etc)

        Returns:
            ReflectionResult with decision
        """
        # Create reflection prompt
        reflection_prompt = self._create_reflection_prompt(
            user_intent,
            planned_action,
            action_parameters,
            context
        )

        try:
            # Use LLM to reflect
            response = self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that carefully reflects before taking action. Think deeply about whether the planned action matches user's intent."
                    },
                    {
                        "role": "user",
                        "content": reflection_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=400
            )

            # Parse reflection result
            result = self._parse_reflection(response["content"])

            logger.info(f"Reflection: proceed={result.should_proceed}, reason={result.reasoning[:50]}...")
            return result

        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            # Fallback: allow action but with warning
            return ReflectionResult(
                should_proceed=True,
                reasoning="Reflection system error, proceeding with caution",
                warnings=["Reflection system encountered an error"]
            )

    def _create_reflection_prompt(
        self,
        user_intent: str,
        planned_action: str,
        action_parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Create prompt for reflection."""
        prompt = f"""CRITICAL REFLECTION: Before executing action, think carefully!

USER'S INTENT: {user_intent}

PLANNED ACTION: {planned_action}
PARAMETERS: {action_parameters}
"""

        if context:
            prompt += f"\nCONTEXT: {context}\n"

        prompt += """
IMPORTANT QUESTIONS TO CONSIDER:

1. INTENT MATCH: Does this action ACTUALLY fulfill the user's intent?
   - If user said "read file", should we CREATE file? NO!
   - If user said "show content", should we DELETE? NO!
   - Does the action match what user asked for?

2. PREREQUISITES: Are all prerequisites met?
   - If reading file, does file EXIST?
   - If modifying file, does file EXIST?
   - If running command, do we have permission?
   - If prerequisites NOT met, should we FAIL or CREATE?

3. EXPECTED OUTCOME: Will this action produce expected outcome?
   - What will happen after action?
   - Is that what user wants?
   - Could this cause unexpected side effects?

4. FAILURE HANDLING: If something is wrong, what should we do?
   - Report error clearly?
   - Ask for clarification?
   - Suggest alternative?
   - Automatically fix? (Be careful!)

5. SAFETY: Is this action safe?
   - Will it destroy data?
   - Will it cause harm?
   - Should we ask confirmation?

REFLECTION RULES:
- If user wants READ but file doesn't exist → DON'T CREATE, report error!
- If user wants DELETE but file doesn't exist → Report "already deleted/not found"
- If prerequisites not met → STOP and report, don't auto-fix unless explicitly asked!
- If action doesn't match intent → STOP and ask clarification!
- If unsure → ASK USER, don't guess!

Your reflection answer format:
PROCEED: [yes/no]
REASONING: [why you decided this]
ALTERNATIVE: [alternative action if not proceeding]
QUESTIONS: [questions for user, if any]
WARNINGS: [any warnings about this action]
"""
        return prompt

    def _parse_reflection(self, llm_response: str) -> ReflectionResult:
        """Parse LLM reflection response."""
        lines = llm_response.strip().split('\n')

        data = {}
        current_key = None
        for line in lines:
            if ':' in line:
                parts = line.split(':', 1)
                key = parts[0].strip().upper()
                value = parts[1].strip() if len(parts) > 1 else ""
                data[key] = value
                current_key = key
            elif current_key and line.strip():
                data[current_key] += " " + line.strip()

        # Parse proceed decision
        proceed_str = data.get('PROCEED', 'no').lower()
        should_proceed = proceed_str in ['yes', 'true', 'proceed']

        # Extract fields
        reasoning = data.get('REASONING', 'No reasoning provided')
        alternative = data.get('ALTERNATIVE', None)
        if alternative and (alternative == 'None' or alternative == 'N/A'):
            alternative = None

        # Parse questions
        questions_str = data.get('QUESTIONS', '')
        questions = self._parse_list(questions_str)

        # Parse warnings
        warnings_str = data.get('WARNINGS', '')
        warnings = self._parse_list(warnings_str)

        return ReflectionResult(
            should_proceed=should_proceed,
            reasoning=reasoning,
            alternative_action=alternative,
            questions_for_user=questions,
            warnings=warnings
        )

    def _parse_list(self, text: str) -> List[str]:
        """Parse comma or dash separated list."""
        if not text or text.lower() in ['none', 'n/a', 'no']:
            return []

        # Try dash/bullet separation
        if '-' in text or '•' in text:
            items = [
                item.strip().lstrip('-').lstrip('•').strip()
                for item in text.split('\n')
                if item.strip()
            ]
        # Try comma separation
        elif ',' in text:
            items = [item.strip() for item in text.split(',')]
        else:
            items = [text.strip()]

        return [item for item in items if item and item.lower() not in ['none', 'n/a']]

    def quick_reflection(
        self,
        user_wants: str,
        ai_plans: str,
        file_exists: Optional[bool] = None
    ) -> ReflectionResult:
        """Quick reflection for common cases.

        Args:
            user_wants: What user wants (e.g., "read file")
            ai_plans: What AI plans to do (e.g., "create file")
            file_exists: Whether target file exists

        Returns:
            ReflectionResult
        """
        user_lower = user_wants.lower()
        plan_lower = ai_plans.lower()

        # CRITICAL: User wants READ but AI plans CREATE/WRITE
        if ('read' in user_lower or 'show' in user_lower or 'display' in user_lower):
            if ('create' in plan_lower or 'write' in plan_lower):
                if file_exists is False:
                    # WRONG! User wants read, file doesn't exist, AI shouldn't create!
                    return ReflectionResult(
                        should_proceed=False,
                        reasoning="User wants to READ file, but file doesn't exist. Should report 'file not found', NOT create new file!",
                        alternative_action="Report error: 'File not found. Did you mean to create a new file?'",
                        warnings=["Action mismatch: User wants read but planned action is create"]
                    )

        # User wants CREATE but file already exists
        if ('create' in user_lower or 'new' in user_lower):
            if file_exists is True:
                return ReflectionResult(
                    should_proceed=False,
                    reasoning="User wants to create NEW file, but file already exists. Should ask if they want to overwrite or use different name.",
                    questions_for_user=["File already exists. Do you want to overwrite it or use a different name?"],
                    warnings=["File already exists"]
                )

        # User wants DELETE but file doesn't exist
        if 'delete' in user_lower or 'remove' in user_lower:
            if file_exists is False:
                return ReflectionResult(
                    should_proceed=False,
                    reasoning="User wants to delete file, but file doesn't exist. Should report 'file not found' or 'already deleted'.",
                    alternative_action="Report: 'File not found or already deleted.'",
                    warnings=["File doesn't exist"]
                )

        # Default: proceed
        return ReflectionResult(
            should_proceed=True,
            reasoning="Quick reflection passed, action seems appropriate"
        )


# Global instance
_pre_action_reflection: Optional[PreActionReflection] = None


def get_pre_action_reflection(llm_client=None) -> PreActionReflection:
    """Get or create global pre-action reflection instance.

    Args:
        llm_client: LLM client (required on first call)

    Returns:
        PreActionReflection instance
    """
    global _pre_action_reflection
    if _pre_action_reflection is None:
        if llm_client is None:
            from agent.llm.groq_client import get_groq_client
            llm_client = get_groq_client()
        _pre_action_reflection = PreActionReflection(llm_client)
    return _pre_action_reflection
