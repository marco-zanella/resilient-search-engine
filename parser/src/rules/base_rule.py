"""
Base Rule Class

All parsing rules inherit from this base class.
Each rule attempts to parse an entry and returns either:
- None (rule doesn't apply)
- Dict with parsed data (rule successfully applied)
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class BaseRule(ABC):
    """Base class for all parsing rules"""

    def __init__(self):
        self.rule_name = self.__class__.__name__

    @abstractmethod
    def can_parse(self, entry: str) -> bool:
        """
        Quick check if this rule might apply to the entry.
        Should be fast - used for filtering.
        """
        pass

    @abstractmethod
    def parse(self, entry: str) -> Optional[Dict[str, Any]]:
        """
        Attempt to parse the entry.

        Returns:
            None if rule doesn't apply
            Dict with parsed data if successful:
                {
                    "rule_applied": str,
                    "base_reading": str (optional),
                    "variants": [
                        {
                            "type": "substitution" | "addition" | "deletion" | "omission",
                            "text": str,
                            "witnesses": [str],
                            "notes": str (optional)
                        }
                    ]
                }
        """
        pass

    def extract_witnesses(self, text: str) -> tuple[str, list[str]]:
        """
        Helper: Extract witnesses from the end of a variant string.

        Example:
            "+ ην 569 246 75 730 Phil I 10.5 Sev 435 La Bo Pal"
            -> ("+ ην", ["569", "246", "75", "730", "Phil I 10.5", "Sev 435", "La", "Bo", "Pal"])

        Returns:
            (variant_text, witnesses_list)
        """
        # This is a simplified version - witnesses can be complex
        # For now, we'll just split by spaces and consider everything after the first word as witnesses
        parts = text.strip().split(None, 1)  # Split on first whitespace
        if len(parts) == 1:
            return (parts[0], [])

        variant_part = parts[0]
        witnesses_part = parts[1]

        # Split witnesses by whitespace
        # Note: This is simplified - real witnesses can have internal spaces
        witnesses = witnesses_part.split()

        return (variant_part, witnesses)


class RuleRegistry:
    """Registry for all parsing rules"""

    def __init__(self):
        self.rules = []

    def register(self, rule: BaseRule, priority: int = 100):
        """Register a rule with a priority (lower = higher priority)"""
        self.rules.append((priority, rule))
        self.rules.sort(key=lambda x: x[0])  # Sort by priority

    def parse_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """
        Try to parse an entry using registered rules in priority order.

        Returns the result from the first rule that succeeds, or None.
        """
        for priority, rule in self.rules:
            if rule.can_parse(entry):
                result = rule.parse(entry)
                if result is not None:
                    return result
        return None

    def get_rule_count(self) -> int:
        """Get number of registered rules"""
        return len(self.rules)
