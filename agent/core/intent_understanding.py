"""Intent Understanding System.

Sistem untuk memahami maksud user secara mendalam sebelum AI mengambil action.
Menggunakan LLM untuk semantic understanding, BUKAN regex!

Mengatasi masalah:
- AI tidak memahami intent user dengan baik
- AI langsung action tanpa validasi intent
- AI tidak reflect sebelum execute
- Action mismatch dengan ekspektasi user
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """User intent types."""
    # Information seeking
    QUESTION = "question"  # User bertanya informasi
    CLARIFICATION = "clarification"  # User minta klarifikasi

    # File operations
    READ_FILE = "read_file"  # User mau baca file
    WRITE_FILE = "write_file"  # User mau buat/tulis file
    MODIFY_FILE = "modify_file"  # User mau edit file
    DELETE_FILE = "delete_file"  # User mau hapus file
    LIST_FILES = "list_files"  # User mau list files

    # Execution
    RUN_COMMAND = "run_command"  # User mau jalankan command
    EXECUTE_CODE = "execute_code"  # User mau execute code

    # Creation
    CREATE_PROJECT = "create_project"  # User mau buat project
    GENERATE_CODE = "generate_code"  # User mau generate code

    # Analysis
    ANALYZE = "analyze"  # User mau analyze something
    DEBUG = "debug"  # User mau debug issue

    # Conversation
    GREETING = "greeting"  # User say hi/hello
    THANKS = "thanks"  # User say thanks
    CASUAL = "casual"  # Casual conversation

    # Meta
    FEEDBACK = "feedback"  # User give feedback
    HELP = "help"  # User butuh help

    # Unknown
    UNCLEAR = "unclear"  # Intent tidak jelas


class ExpectedOutcome:
    """Expected outcome from user's perspective."""

    def __init__(
        self,
        what: str,
        why: str,
        success_criteria: str,
        failure_behavior: str
    ):
        """Initialize expected outcome.

        Args:
            what: What user expects to happen
            why: Why user wants this
            success_criteria: How to know if successful
            failure_behavior: What should happen if it fails
        """
        self.what = what
        self.why = why
        self.success_criteria = success_criteria
        self.failure_behavior = failure_behavior


class IntentAnalysis:
    """Analysis of user intent."""

    def __init__(
        self,
        intent: UserIntent,
        confidence: float,
        target_object: Optional[str],
        expected_outcome: ExpectedOutcome,
        prerequisites: List[str],
        potential_issues: List[str],
        recommended_action: str
    ):
        """Initialize intent analysis.

        Args:
            intent: Detected intent
            confidence: Confidence score (0-1)
            target_object: Object being acted upon (file, command, etc)
            expected_outcome: What user expects
            prerequisites: Things to check before action
            potential_issues: Potential problems
            recommended_action: Recommended action to take
        """
        self.intent = intent
        self.confidence = confidence
        self.target_object = target_object
        self.expected_outcome = expected_outcome
        self.prerequisites = prerequisites
        self.potential_issues = potential_issues
        self.recommended_action = recommended_action


class IntentUnderstanding:
    """System untuk memahami maksud user dengan mendalam."""

    def __init__(self, llm_client):
        """Initialize intent understanding.

        Args:
            llm_client: LLM client untuk semantic understanding
        """
        self.llm = llm_client

    def understand_intent(self, user_message: str, context: Optional[str] = None) -> IntentAnalysis:
        """Understand user's intent deeply using LLM.

        Args:
            user_message: User's message
            context: Optional context (previous messages, etc)

        Returns:
            IntentAnalysis with deep understanding
        """
        # Create prompt for LLM to analyze intent
        analysis_prompt = self._create_intent_prompt(user_message, context)

        try:
            # Use LLM to understand intent (NOT regex!)
            response = self.llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at understanding user intentions. Analyze the user's message deeply."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent analysis
                max_tokens=500
            )

            # Parse LLM response into structured analysis
            analysis = self._parse_intent_response(response["content"], user_message)

            logger.info(f"Intent understood: {analysis.intent.value} (confidence: {analysis.confidence:.2f})")
            return analysis

        except Exception as e:
            logger.error(f"Intent understanding failed: {e}")
            # Fallback to basic analysis
            return self._basic_intent_analysis(user_message)

    def _create_intent_prompt(self, user_message: str, context: Optional[str]) -> str:
        """Create prompt for intent analysis."""
        prompt = f"""Analyze this user message deeply and understand their TRUE intention:

User message: "{user_message}"
"""

        if context:
            prompt += f"\nContext: {context}\n"

        prompt += """
Answer these questions about the user's intent:

1. PRIMARY INTENT: What does the user ACTUALLY want to achieve?
   - Is it: question, read_file, write_file, modify_file, delete_file, run_command, create_project, greeting, help, etc.

2. TARGET OBJECT: What specific thing are they referring to?
   - File name? Command? Project? Concept?

3. EXPECTED OUTCOME: What does the user EXPECT to happen?
   - What result do they want to see?
   - Why do they want this?

4. SUCCESS CRITERIA: How will we know if we succeeded?
   - What should the response contain?
   - What should be the state after action?

5. FAILURE HANDLING: If we CAN'T do what they ask, what should we do?
   - Report the issue clearly?
   - Suggest alternatives?
   - Ask for clarification?

6. PREREQUISITES: What needs to exist/be true before we can act?
   - Does file need to exist?
   - Does directory need to exist?
   - Does permission need to be granted?

7. POTENTIAL ISSUES: What could go wrong?
   - File not found?
   - Permission denied?
   - Invalid input?

8. RECOMMENDED ACTION: What's the RIGHT action to take?
   - Which tool to use?
   - What parameters?
   - What to check first?

9. CONFIDENCE: How confident are you about this intent? (0.0 to 1.0)

Format your answer as:
INTENT: [intent_type]
CONFIDENCE: [0.0-1.0]
TARGET: [object or N/A]
EXPECTED: [what user expects]
WHY: [user's motivation]
SUCCESS: [success criteria]
FAILURE: [how to handle failure]
PREREQUISITES: [list of prerequisites]
ISSUES: [potential issues]
ACTION: [recommended action]
"""
        return prompt

    def _parse_intent_response(self, llm_response: str, original_message: str) -> IntentAnalysis:
        """Parse LLM response into IntentAnalysis."""
        lines = llm_response.strip().split('\n')

        # Extract fields
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
                # Continuation of previous field
                data[current_key] += " " + line.strip()

        # Map intent string to enum
        intent_str = data.get('INTENT', 'unclear').lower()
        intent = self._map_intent_string(intent_str)

        # Parse confidence
        try:
            confidence = float(data.get('CONFIDENCE', '0.5'))
        except:
            confidence = 0.5

        # Extract target
        target = data.get('TARGET', 'N/A')
        if target == 'N/A':
            target = None

        # Create expected outcome
        expected_outcome = ExpectedOutcome(
            what=data.get('EXPECTED', 'Unknown'),
            why=data.get('WHY', 'Unknown'),
            success_criteria=data.get('SUCCESS', 'Unknown'),
            failure_behavior=data.get('FAILURE', 'Report error clearly')
        )

        # Parse prerequisites and issues
        prerequisites = self._parse_list(data.get('PREREQUISITES', ''))
        potential_issues = self._parse_list(data.get('ISSUES', ''))

        # Recommended action
        recommended_action = data.get('ACTION', 'Ask for clarification')

        return IntentAnalysis(
            intent=intent,
            confidence=confidence,
            target_object=target,
            expected_outcome=expected_outcome,
            prerequisites=prerequisites,
            potential_issues=potential_issues,
            recommended_action=recommended_action
        )

    def _map_intent_string(self, intent_str: str) -> UserIntent:
        """Map intent string to UserIntent enum."""
        intent_mapping = {
            'question': UserIntent.QUESTION,
            'clarification': UserIntent.CLARIFICATION,
            'read_file': UserIntent.READ_FILE,
            'read': UserIntent.READ_FILE,
            'write_file': UserIntent.WRITE_FILE,
            'write': UserIntent.WRITE_FILE,
            'create': UserIntent.WRITE_FILE,
            'modify_file': UserIntent.MODIFY_FILE,
            'modify': UserIntent.MODIFY_FILE,
            'edit': UserIntent.MODIFY_FILE,
            'delete_file': UserIntent.DELETE_FILE,
            'delete': UserIntent.DELETE_FILE,
            'list_files': UserIntent.LIST_FILES,
            'list': UserIntent.LIST_FILES,
            'run_command': UserIntent.RUN_COMMAND,
            'run': UserIntent.RUN_COMMAND,
            'execute': UserIntent.EXECUTE_CODE,
            'create_project': UserIntent.CREATE_PROJECT,
            'generate': UserIntent.GENERATE_CODE,
            'analyze': UserIntent.ANALYZE,
            'debug': UserIntent.DEBUG,
            'greeting': UserIntent.GREETING,
            'hello': UserIntent.GREETING,
            'hi': UserIntent.GREETING,
            'thanks': UserIntent.THANKS,
            'casual': UserIntent.CASUAL,
            'feedback': UserIntent.FEEDBACK,
            'help': UserIntent.HELP,
        }

        for key, intent in intent_mapping.items():
            if key in intent_str.lower():
                return intent

        return UserIntent.UNCLEAR

    def _parse_list(self, text: str) -> List[str]:
        """Parse comma or newline separated list."""
        if not text or text == 'None' or text == 'N/A':
            return []

        # Try comma separation first
        if ',' in text:
            items = [item.strip() for item in text.split(',')]
        # Try dash/bullet points
        elif '-' in text or '•' in text:
            items = [
                item.strip().lstrip('-').lstrip('•').strip()
                for item in text.split('\n')
                if item.strip()
            ]
        else:
            items = [text.strip()]

        return [item for item in items if item and item != 'None']

    def _basic_intent_analysis(self, user_message: str) -> IntentAnalysis:
        """Basic intent analysis as fallback."""
        message_lower = user_message.lower()

        # Very basic intent detection
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            intent = UserIntent.GREETING
        elif any(word in message_lower for word in ['read', 'show', 'display', 'cat']):
            intent = UserIntent.READ_FILE
        elif any(word in message_lower for word in ['create', 'make', 'write', 'new']):
            intent = UserIntent.WRITE_FILE
        elif any(word in message_lower for word in ['run', 'execute', 'perform']):
            intent = UserIntent.RUN_COMMAND
        else:
            intent = UserIntent.UNCLEAR

        return IntentAnalysis(
            intent=intent,
            confidence=0.3,  # Low confidence for fallback
            target_object=None,
            expected_outcome=ExpectedOutcome(
                what="Unknown",
                why="Unknown",
                success_criteria="Unknown",
                failure_behavior="Report error"
            ),
            prerequisites=[],
            potential_issues=["Intent unclear"],
            recommended_action="Ask for clarification"
        )

    def validate_prerequisites(self, analysis: IntentAnalysis) -> tuple[bool, List[str]]:
        """Validate prerequisites are met.

        Args:
            analysis: Intent analysis with prerequisites

        Returns:
            (all_met, missing_prerequisites)
        """
        # This would check actual prerequisites
        # For now, return True (implement based on your needs)
        missing = []

        for prereq in analysis.prerequisites:
            # Check if prerequisite is met
            # This is where you'd add actual checks
            pass

        return len(missing) == 0, missing


# Global instance
_intent_understanding: Optional[IntentUnderstanding] = None


def get_intent_understanding(llm_client=None) -> IntentUnderstanding:
    """Get or create global intent understanding instance.

    Args:
        llm_client: LLM client (required on first call)

    Returns:
        IntentUnderstanding instance
    """
    global _intent_understanding
    if _intent_understanding is None:
        if llm_client is None:
            from agent.llm.groq_client import get_groq_client
            llm_client = get_groq_client()
        _intent_understanding = IntentUnderstanding(llm_client)
    return _intent_understanding
