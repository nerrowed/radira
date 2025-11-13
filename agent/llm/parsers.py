"""Response parsing utilities for LLM outputs."""

import re
import json
from typing import Dict, Any, Optional, Tuple


class ReActParser:
    """Parser for ReAct (Reasoning + Acting) pattern responses."""

    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parse ReAct formatted response.

        Expected format:
        Thought: [reasoning]
        Action: [tool_name]
        Action Input: [json_input]

        Or for final answer:
        Thought: [reasoning]
        Final Answer: [answer]

        Args:
            text: LLM response text

        Returns:
            Dict with 'thought', 'action', 'action_input', or 'final_answer'
        """
        result = {}

        # Extract thought
        thought_match = re.search(r'Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|$)', text, re.DOTALL)
        if thought_match:
            result['thought'] = thought_match.group(1).strip()

        # Check for final answer
        final_answer_match = re.search(r'Final Answer:\s*(.+?)$', text, re.DOTALL)
        if final_answer_match:
            result['final_answer'] = final_answer_match.group(1).strip()
            return result

        # Extract action
        action_match = re.search(r'Action:\s*(.+?)(?=\n|$)', text)
        if action_match:
            result['action'] = action_match.group(1).strip()

        # Extract action input
        action_input_match = re.search(r'Action Input:\s*(.+?)$', text, re.DOTALL)
        if action_input_match:
            action_input_str = action_input_match.group(1).strip()
            # Try to parse as JSON
            try:
                result['action_input'] = json.loads(action_input_str)
            except json.JSONDecodeError:
                # If not JSON, treat as plain string
                result['action_input'] = action_input_str

        return result

    @staticmethod
    def is_final_answer(parsed: Dict[str, Any]) -> bool:
        """Check if response contains final answer.

        Args:
            parsed: Parsed response dict

        Returns:
            True if final answer present
        """
        return 'final_answer' in parsed

    @staticmethod
    def validate(parsed: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate parsed response.

        Args:
            parsed: Parsed response dict

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not parsed:
            return False, "Empty response"

        if 'thought' not in parsed:
            return False, "Missing 'Thought' section"

        # Either has final answer or action
        has_final = 'final_answer' in parsed
        has_action = 'action' in parsed

        if not has_final and not has_action:
            return False, "Missing both 'Final Answer' and 'Action'"

        if has_action and 'action_input' not in parsed:
            return False, "Action specified but missing 'Action Input'"

        return True, None


class JSONParser:
    """Parser for JSON outputs."""

    @staticmethod
    def extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from text that may contain markdown or other formatting.

        Args:
            text: Text containing JSON

        Returns:
            Parsed JSON dict or None
        """
        # Try direct parsing first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from code block
        json_block_match = re.search(r'```(?:json)?\s*(\{.+?\})\s*```', text, re.DOTALL)
        if json_block_match:
            try:
                return json.loads(json_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object
        json_match = re.search(r'\{.+\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def parse_list(text: str) -> Optional[list]:
        """Extract JSON list from text.

        Args:
            text: Text containing JSON list

        Returns:
            Parsed list or None
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to extract from code block
        list_block_match = re.search(r'```(?:json)?\s*(\[.+?\])\s*```', text, re.DOTALL)
        if list_block_match:
            try:
                return json.loads(list_block_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON list
        list_match = re.search(r'\[.+\]', text, re.DOTALL)
        if list_match:
            try:
                return json.loads(list_match.group(0))
            except json.JSONDecodeError:
                pass

        return None


class CodeParser:
    """Parser for code blocks in responses."""

    @staticmethod
    def extract_code_blocks(text: str) -> list:
        """Extract all code blocks from text.

        Args:
            text: Text containing code blocks

        Returns:
            List of dicts with 'language' and 'code'
        """
        pattern = r'```(\w+)?\n(.+?)```'
        matches = re.findall(pattern, text, re.DOTALL)

        blocks = []
        for language, code in matches:
            blocks.append({
                'language': language or 'text',
                'code': code.strip()
            })

        return blocks

    @staticmethod
    def extract_single_code_block(text: str, language: Optional[str] = None) -> Optional[str]:
        """Extract first code block, optionally filtering by language.

        Args:
            text: Text containing code blocks
            language: Optional language to filter by

        Returns:
            Code string or None
        """
        blocks = CodeParser.extract_code_blocks(text)

        if not blocks:
            return None

        if language:
            for block in blocks:
                if block['language'] == language:
                    return block['code']
            return None

        return blocks[0]['code']

    @staticmethod
    def remove_code_blocks(text: str) -> str:
        """Remove code blocks from text, keeping only surrounding text.

        Args:
            text: Text with code blocks

        Returns:
            Text without code blocks
        """
        return re.sub(r'```\w*\n.+?```', '', text, flags=re.DOTALL).strip()


def parse_response(text: str, format_type: str = "react") -> Dict[str, Any]:
    """Parse response based on expected format.

    Args:
        text: Response text
        format_type: Expected format ('react', 'json', 'code')

    Returns:
        Parsed response dict
    """
    if format_type == "react":
        return ReActParser.parse(text)
    elif format_type == "json":
        return {"data": JSONParser.extract_json(text)}
    elif format_type == "code":
        return {"blocks": CodeParser.extract_code_blocks(text)}
    else:
        return {"text": text}
