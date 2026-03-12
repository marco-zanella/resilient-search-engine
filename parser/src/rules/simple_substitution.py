"""
Simple Substitution Rule

Handles entries like:
    "word] variant witnesses"

Example:
    "ἐποίησεν] επλασεν 664"
    -> base_reading: "ἐποίησεν", variant: "επλασεν", witnesses: ["664"]
"""

import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from .base_rule import BaseRule

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.witness_parser import split_variant_and_witnesses


class SimpleSubstitutionRule(BaseRule):
    """Parse simple substitution: word] variant witnesses"""

    def can_parse(self, entry: str) -> bool:
        """Check if entry contains ']' pattern"""
        return ']' in entry

    def parse(self, entry: str) -> Optional[Dict[str, Any]]:
        """
        Parse simple substitution pattern.

        Format: base_reading] variant witnesses
        """
        # Check for the ] separator
        if ']' not in entry:
            return None

        # Split on ]
        parts = entry.split(']', 1)
        if len(parts) != 2:
            return None

        base_reading = parts[0].strip()
        variant_part = parts[1].strip()

        # If variant_part is empty, this might be an omission
        if not variant_part:
            return None

        # Check for special markers that indicate this isn't a simple substitution
        non_substitution_regex = re.compile(
            r"""^(
                >                           |   # omission symbol
                om\b|om[\.·,]               |   # omission: om, om., om·
                tr\b|tr[\.·]                |   # transposition: tr, tr., tr·
                pr\b|pr[\.·]                |   # prefix/addition
                \+                          |   # simple addition: +ην
                bis\ scr\b                 |   # repeated: bis scr
                ter\ scr\b                 |   # repeated: ter scr
                absc\b                     |   # abscission
                ◠                          |   # segment omission
                addunt\b                   |   # interpolations
                hab\b|habent\b                 # interpolations
            )""",
            re.VERBOSE | re.IGNORECASE
        )

        if non_substitution_regex.match(variant_part):
            return None

        # Split by semicolon to get multiple variants
        variant_strings = [v.strip() for v in variant_part.split(';') if v.strip()]

        variants = []
        for var_str in variant_strings:
            if not var_str:
                continue

            # Use smart witness parser to split variant from witnesses
            variant_text, witnesses = split_variant_and_witnesses(var_str)

            if not variant_text:
                continue

            variants.append({
                "type": "substitution",
                "text": variant_text,
                "witnesses": witnesses
            })

        if not variants:
            return None

        return {
            "rule_applied": self.rule_name,
            "base_reading": base_reading,
            "variants": variants
        }
