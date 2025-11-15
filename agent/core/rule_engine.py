"""Rule Engine - Deterministic rule checking and application.

This module implements a rule system that checks user input BEFORE LLM reasoning
and applies rules deterministically when triggered.
"""

import logging
import re
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Rule:
    """Represents a single user-defined rule."""

    def __init__(
        self,
        rule_id: str,
        trigger: str,
        response: str,
        trigger_type: str = "exact",  # exact, contains, regex
        priority: int = 0,
        created_at: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a rule.

        Args:
            rule_id: Unique rule identifier
            trigger: What triggers this rule
            response: What to respond when triggered
            trigger_type: How to match trigger (exact, contains, regex)
            priority: Rule priority (higher = checked first)
            created_at: Creation timestamp
            metadata: Additional rule metadata
        """
        self.rule_id = rule_id
        self.trigger = trigger.lower().strip()
        self.response = response
        self.trigger_type = trigger_type
        self.priority = priority
        self.created_at = created_at or datetime.now().isoformat()
        self.metadata = metadata or {}

        # Compile regex if needed
        if self.trigger_type == "regex":
            try:
                self.compiled_pattern = re.compile(self.trigger, re.IGNORECASE)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{self.trigger}': {e}")
                # Fallback to 'contains' matching
                self.trigger_type = "contains"
                self.compiled_pattern = None
        else:
            self.compiled_pattern = None

    def matches(self, user_input: str) -> bool:
        """Check if user input matches this rule's trigger.

        Args:
            user_input: User's input text

        Returns:
            True if matches, False otherwise
        """
        user_lower = user_input.lower().strip()

        if self.trigger_type == "exact":
            return user_lower == self.trigger
        elif self.trigger_type == "contains":
            return self.trigger in user_lower
        elif self.trigger_type == "regex" and self.compiled_pattern:
            return bool(self.compiled_pattern.search(user_input))

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization.

        Returns:
            Dict representation of rule
        """
        return {
            "rule_id": self.rule_id,
            "trigger": self.trigger,
            "response": self.response,
            "trigger_type": self.trigger_type,
            "priority": self.priority,
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Rule':
        """Create rule from dictionary.

        Args:
            data: Dict representation of rule

        Returns:
            Rule instance
        """
        return Rule(
            rule_id=data["rule_id"],
            trigger=data["trigger"],
            response=data["response"],
            trigger_type=data.get("trigger_type", "exact"),
            priority=data.get("priority", 0),
            created_at=data.get("created_at"),
            metadata=data.get("metadata", {})
        )


class RuleEngine:
    """Engine to manage and check user-defined rules.

    Rules are checked BEFORE LLM reasoning and applied deterministically.
    """

    def __init__(self, rules_file: Optional[str] = None):
        """Initialize rule engine.

        Args:
            rules_file: Path to JSON file for persisting rules
        """
        self.rules_file = Path(rules_file) if rules_file else Path("workspace/.memory/rules.json")
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)

        # Load rules from file
        self.rules: List[Rule] = []
        self._load_rules()

        logger.info(f"RuleEngine initialized with {len(self.rules)} rules")

    def add_rule(
        self,
        trigger: str,
        response: str,
        trigger_type: str = "contains",
        priority: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new rule.

        Args:
            trigger: What triggers this rule
            response: What to respond
            trigger_type: How to match (exact, contains, regex)
            priority: Rule priority
            metadata: Additional metadata

        Returns:
            Rule ID
        """
        rule_id = f"rule_{datetime.now().timestamp()}"

        rule = Rule(
            rule_id=rule_id,
            trigger=trigger,
            response=response,
            trigger_type=trigger_type,
            priority=priority,
            metadata=metadata
        )

        self.rules.append(rule)

        # Sort by priority (higher first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)

        # Save to file
        self._save_rules()

        logger.info(f"Added rule: '{trigger}' → '{response}'")
        return rule_id

    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID.

        Args:
            rule_id: Rule identifier

        Returns:
            True if removed, False if not found
        """
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r.rule_id != rule_id]

        if len(self.rules) < original_count:
            self._save_rules()
            logger.info(f"Removed rule: {rule_id}")
            return True

        return False

    def check_rules(self, user_input: str) -> Optional[str]:
        """Check if user input matches any rules and return response.

        This is the MAIN method - checks user input BEFORE LLM reasoning.

        Args:
            user_input: User's input text

        Returns:
            Rule response if matched, None otherwise
        """
        for rule in self.rules:
            if rule.matches(user_input):
                logger.info(f"Rule matched: {rule.rule_id} ('{rule.trigger}')")
                return rule.response

        return None

    def get_all_rules(self) -> List[Rule]:
        """Get all rules.

        Returns:
            List of Rule objects
        """
        return self.rules.copy()

    def get_rules_as_text(self) -> str:
        """Get all rules formatted as text for injection into system prompt.

        Returns:
            Formatted rules text
        """
        if not self.rules:
            return ""

        lines = ["## PERMANENT RULES (MUST ALWAYS FOLLOW):", ""]

        for i, rule in enumerate(self.rules, 1):
            if rule.trigger_type == "exact":
                condition = f"User says exactly: '{rule.trigger}'"
            elif rule.trigger_type == "contains":
                condition = f"User says something containing: '{rule.trigger}'"
            else:
                condition = f"User input matches pattern: {rule.trigger}"

            lines.append(f"{i}. **WHEN**: {condition}")
            lines.append(f"   **THEN**: {rule.response}")
            lines.append("")

        return "\n".join(lines)

    def get_rule_count(self) -> int:
        """Get number of active rules.

        Returns:
            Rule count
        """
        return len(self.rules)

    def clear_all_rules(self) -> int:
        """Clear all rules.

        Returns:
            Number of rules cleared
        """
        count = len(self.rules)
        self.rules = []
        self._save_rules()
        logger.info(f"Cleared all {count} rules")
        return count

    def _load_rules(self):
        """Load rules from JSON file."""
        if not self.rules_file.exists():
            logger.info("No rules file found, starting with empty rules")
            return

        try:
            with open(self.rules_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.rules = [Rule.from_dict(rule_data) for rule_data in data]

            # Sort by priority
            self.rules.sort(key=lambda r: r.priority, reverse=True)

            logger.info(f"Loaded {len(self.rules)} rules from {self.rules_file}")

        except Exception as e:
            logger.error(f"Failed to load rules: {e}")
            self.rules = []

    def _save_rules(self):
        """Save rules to JSON file."""
        try:
            data = [rule.to_dict() for rule in self.rules]

            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self.rules)} rules to {self.rules_file}")

        except Exception as e:
            logger.error(f"Failed to save rules: {e}")

    def export_rules(self, output_file: Path) -> bool:
        """Export rules to JSON file.

        Args:
            output_file: Path to export file

        Returns:
            True if successful
        """
        try:
            data = {
                "rules": [rule.to_dict() for rule in self.rules],
                "exported_at": datetime.now().isoformat(),
                "total_rules": len(self.rules)
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(self.rules)} rules to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
            return False

    def import_rules(self, input_file: Path) -> int:
        """Import rules from JSON file.

        Args:
            input_file: Path to import file

        Returns:
            Number of rules imported
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            imported_rules = data.get("rules", [])

            count = 0
            for rule_data in imported_rules:
                rule = Rule.from_dict(rule_data)
                self.rules.append(rule)
                count += 1

            # Sort and save
            self.rules.sort(key=lambda r: r.priority, reverse=True)
            self._save_rules()

            logger.info(f"Imported {count} rules from {input_file}")
            return count

        except Exception as e:
            logger.error(f"Failed to import rules: {e}")
            return 0


# Global instance
_rule_engine: Optional[RuleEngine] = None


def get_rule_engine() -> RuleEngine:
    """Get or create global rule engine instance.

    Returns:
        RuleEngine instance
    """
    global _rule_engine
    if _rule_engine is None:
        _rule_engine = RuleEngine()
    return _rule_engine
