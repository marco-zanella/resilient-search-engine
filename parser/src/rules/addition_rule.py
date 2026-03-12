import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from .base_rule import BaseRule

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.witness_parser import split_variant_and_witnesses


ADDITION_SYMBOLS = {
    "+": "post",
    "pr": "ante",
    "bis scr": "repeat",
    "ter scr": "repeat",
    "addunt": "interpolated",
    "hab": "interpolated",
    "habent": "interpolated",
}


class AdditionRule(BaseRule):
    """
    Generalized Addition Rule (4.2)

    Supports:
    - +
    - pr
    - bis scr
    - ter scr
    - addunt
    - hab, habent
    """

    def can_parse(self, entry: str) -> bool:
        """
        Addition entries contain at least one keyword from ADDITION_SYMBOLS.
        They may appear:
        - after ']'
        - or directly after the base reading (negative entries)
        """
        if ']' in entry:
            right = entry.split(']', 1)[1].strip()
        else:
            right = entry.strip()

        for symbol in ADDITION_SYMBOLS:
            if right.startswith(symbol):
                return True

        # Also support patterns like: base + addunt ...
        if re.search(r"\b(addunt|hab|habent)\b", entry):
            return True

        return False

    def parse(self, entry: str) -> Optional[Dict[str, Any]]:
        if ']' in entry:
            base, rest = entry.split(']', 1)
            base = base.strip()
            rest = rest.strip()
        else:
            # negative entries like: "base + addunt ... "
            parts = entry.split("+", 1)
            if len(parts) < 2:
                return None
            base = parts[0].strip()
            rest = "+" + parts[1].strip()

        # Identify the symbol used
        symbol_used = None
        for symbol in sorted(ADDITION_SYMBOLS.keys(), key=lambda s: -len(s)):
            if rest.startswith(symbol):
                symbol_used = symbol
                break

        if not symbol_used:
            return None

        kind = ADDITION_SYMBOLS[symbol_used]

        # Remove the symbol
        payload = rest[len(symbol_used):].strip()

        # Parse textual addition (if any)
        insertion_text, witnesses = split_variant_and_witnesses(payload)

        result: Dict[str, Any] = {
            "rule_applied": self.rule_name,
            "base_reading": base,
            "variants": []
        }

        variant: Dict[str, Any] = {
            "type": "addition",
            "symbol": symbol_used,
            "witnesses": witnesses,
        }

        # Handle each case type
        if symbol_used == "+":
            variant["insert"] = insertion_text
            variant["position"] = "post"

        elif symbol_used == "pr":
            variant["insert"] = insertion_text
            variant["position"] = "ante"

        elif symbol_used == "bis scr":
            variant["repeat"] = 2
            variant["includeEditedText"] = True

        elif symbol_used == "ter scr":
            variant["repeat"] = 3
            variant["includeEditedText"] = True

        elif symbol_used in {"addunt", "hab", "habent"}:
            variant["isInterpolated"] = True
            variant["includeEditedText"] = True
            variant["insert"] = insertion_text if insertion_text else None

        else:
            return None

        result["variants"].append(variant)
        return result
