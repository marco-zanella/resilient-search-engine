"""
Deletion Rule

ReadingInApparatusType: deletion

Handles entries where a special Latin TypeSymbol (delebit / delebunt / del)
indicates that the Critical Text Passage should be deleted for some witnesses.

Example:
    "ἐκτρίψω] contere AethFGR; delebit (-bunt BoA*) Co; occidetis Aug C Adim 17"

Output (simplified):
    {
        "rule_applied": "DeletionRule",
        "base_reading": "ἐκτρίψω",
        "variants": [
            {
                "type": "substitution",
                "text": "contere",
                "witnesses": ["AethFGR"]
            },
            {
                "type": "deletion",
                "text": "",
                "witnesses": ["Co"],
                "notes": "(-bunt BoA*)"
            },
            {
                "type": "substitution",
                "text": "occidetis",
                "witnesses": ["Aug", "C", "Adim", "17"]
            }
        ]
    }
"""

import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from .base_rule import BaseRule

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.witness_parser import split_variant_and_witnesses


class DeletionRule(BaseRule):
    """Parse deletion patterns marked by delebit / delebunt / del."""

    # We match only standalone tokens
    DELETION_RE = re.compile(r"\b(delebit|delebunt|del)\b", re.IGNORECASE)

    def can_parse(self, entry: str) -> bool:
        """
        Quick check:
        - we need a base reading (']')
        - and at least one deletion marker in the variant part
        """
        if ']' not in entry:
            return False

        _, variant_part = entry.split(']', 1)
        return bool(self.DELETION_RE.search(variant_part))

    def _parse_deletion_segment(self, segment: str) -> Dict[str, Any]:
        """
        Parse the single sub-reading that contains delebit/delebunt/del.

        Example segment:
            "delebit (-bunt BoA*) Co"

        We:
        - extract optional note in (...) as 'notes'
        - remove the deletion keyword (delebit/delebunt/del)
        - send the rest to split_variant_and_witnesses to get witnesses
        """

        # Extract note in parentheses, if any
        notes_match = re.search(r"\([^)]*\)", segment)
        notes = notes_match.group(0) if notes_match else None

        # Remove the note from the segment
        cleaned = re.sub(r"\([^)]*\)", "", segment).strip()

        # Remove the deletion keyword itself
        cleaned = self.DELETION_RE.sub("", cleaned).strip()

        # Whatever remains should be mostly witnesses
        _, witnesses = split_variant_and_witnesses(cleaned) if cleaned else ("", [])

        variant: Dict[str, Any] = {
            "type": "deletion",
            "text": "",  # deletion => the critical text passage is removed
            "witnesses": witnesses,
        }

        if notes:
            variant["notes"] = notes

        return variant

    def _parse_normal_segment(self, segment: str) -> Optional[Dict[str, Any]]:
        """
        Parse a non-deletion sub-reading as a standard substitution variant.

        Example:
            "contere AethFGR"
            "occidetis Aug C Adim 17"
        """
        variant_text, witnesses = split_variant_and_witnesses(segment.strip())
        if not variant_text:
            return None

        return {
            "type": "substitution",
            "text": variant_text,
            "witnesses": witnesses
        }

    def parse(self, entry: str) -> Optional[Dict[str, Any]]:
        """
        Full parsing of an entry containing a deletion reading.

        Typical pattern:
            base_reading] reading1 witnesses; delebit (...) witnesses; reading3 witnesses
        """

        if ']' not in entry:
            return None

        base_part, variant_part = entry.split(']', 1)
        base_reading = base_part.strip()
        variant_part = variant_part.strip()

        if not variant_part:
            return None

        # Split into sub-readings by semicolon
        segments = [s.strip() for s in variant_part.split(';') if s.strip()]

        variants: List[Dict[str, Any]] = []
        found_any = False

        for seg in segments:
            if self.DELETION_RE.search(seg):
                # This is the deletion reading
                deletion_variant = self._parse_deletion_segment(seg)
                variants.append(deletion_variant)
                found_any = True
            else:
                # Normal reading => treat as substitution
                normal_variant = self._parse_normal_segment(seg)
                if normal_variant is not None:
                    variants.append(normal_variant)

        if not found_any:
            # Should not happen if can_parse was True, but keep it safe
            return None

        return {
            "rule_applied": self.rule_name,
            "base_reading": base_reading,
            "variants": variants
        }
