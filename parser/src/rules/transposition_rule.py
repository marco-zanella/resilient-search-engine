"""
Transposition Rule

Handles apparatus entries where the reading type is a transposition,
marked by the TypeSymbol 'tr'.

Examples handled:

1) BaseReading] tr 664
2) BaseReading] tr post Reading 15 64
3) tr Reading1 ante/post Reading2 witnesses
4) BaseReading] ad fin tr 246
5) tr Reading1 et Reading2 witnesses

Outcome:
    {
        "rule_applied": "TranspositionRule",
        "base_reading": "...",
        "variants": [
            {
                "type": "transposition",
                "from": "...",     # Critical text passage moved FROM
                "to": "...",       # Critical text passage moved TO
                "position": "...", # switch | ante | post
                "reading": "...",  # full reading string ("tr post γῆς")
                "witnesses": [...]
            }
        ]
    }
"""

import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from .base_rule import BaseRule

# Allow witness extraction
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.witness_parser import split_variant_and_witnesses


class TranspositionRule(BaseRule):
    """Parse transposition readings marked with 'tr'."""

    TR_PATTERN = re.compile(r'\btr\b')

    def can_parse(self, entry: str) -> bool:
        """
        Quick test: transpositions always contain 'tr' as standalone token.
        """
        return bool(self.TR_PATTERN.search(entry))

    def parse(self, entry: str) -> Optional[Dict[str, Any]]:
        """
        General parsing approach:
        - Identify base reading when present before ']'
        - Identify reading string beginning with "tr"
        - Identify markers ante/post/switch/etc.
        - Extract 'from' and 'to' passages in a simplified form
        - Extract witnesses
        """

        # Optional base reading extraction
        base_reading = None
        reading_string = entry

        if ']' in entry:
            base_reading, reading_string = entry.split(']', 1)
            base_reading = base_reading.strip()
            reading_string = reading_string.strip()

        # Witness extraction (best effort)
        reading_text, witnesses = split_variant_and_witnesses(reading_string)

        # Identify the position markers we want to detect
        position = None
        if "post" in reading_text:
            position = "post"
        elif "ante" in reading_text:
            position = "ante"
        else:
            # Default type: simple switch
            position = "switch"

        # Readings of the form "tr ..." 
        # We store the whole reading text as-is.
        reading_clean = reading_text.strip()

        # Extract “from” and “to” using simple heuristics:
        # we cannot fully reconstruct the RDF complexity, so:
        # - FROM = base_reading, if present
        # - otherwise: from = first Greek/word after 'tr'
        # - TO = second meaningful token if a post/ante marker exists
        from_passage = None
        to_passage = None

        # If we have base reading:
        if base_reading:
            from_passage = base_reading

        # Now try to extract passages after markers
        tokens = reading_clean.split()

        if "post" in tokens:
            idx = tokens.index("post")
            if idx + 1 < len(tokens):
                to_passage = tokens[idx + 1]

        elif "ante" in tokens:
            idx = tokens.index("ante")
            if idx + 1 < len(tokens):
                to_passage = tokens[idx + 1]

        # If not found, leave None; the variant is still valid as a transposition reading.

        variant = {
            "type": "transposition",
            "reading": reading_clean,
            "position": position,
            "from": from_passage,
            "to": to_passage,
            "witnesses": witnesses
        }

        return {
            "rule_applied": self.rule_name,
            "base_reading": base_reading,
            "variants": [variant]
        }
