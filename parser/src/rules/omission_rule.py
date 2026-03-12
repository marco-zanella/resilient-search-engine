"""
Omission Rule (generalized for 4.1)

Supports omission markers:
- ">"
- "om"
- "◠"
- "absc"
- "semel scr"
- "non hab"

Handles patterns like:
    base] > witnesses
    base] om X witnesses
    base] absc witnesses
    ... ; om X witnesses
    om X witnesses
    καί 2°◠3° witnesses
"""

import re
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
from .base_rule import BaseRule

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.utils.witness_parser import split_variant_and_witnesses


OMISSION_SYMBOLS = {
    ">": "full",          # omission of whole critical passage
    "om": "partial",      # omission of a part/string
    "◠": "range",         # range omission (often excluding end selector)
    "absc": "full",       # abstracted omission (whole passage)
    "semel scr": "full",  # written once only
    "non hab": "full",    # "does not have" -> omission
}


class OmissionRule(BaseRule):
    """Parse omission patterns according to rule 4.1"""

    def can_parse(self, entry: str) -> bool:
        """
        Check if the entry contains omission markers in any of the supported
        forms (positive or negative).
        """
        s = entry.strip()

        # Simple fast checks
        if s.startswith("om "):
            return True
        if "◠" in s:
            return True

        # Cases with base] marker + omission keyword
        if "]" in s:
            right = s.split("]", 1)[1]
        else:
            right = s

        markers = [">", " om ", " absc", " semel scr", " non hab"]
        return any(m in right for m in markers)

    def parse(self, entry: str) -> Optional[Dict[str, Any]]:
        """
        Supported formats (non esaustivo ma pratico):

        1) base] > witnesses
        2) base] om X witnesses
        3) base] absc witnesses
        4) base] ... ; om X witnesses ; ... (multi-segment)
        5) base] ... ; ◠end witnesses (range omission)
        6) om X witnesses          (negative entry)
        7) X◠Y witnesses           (range omission without ])
        """
        entry = entry.strip()
        variants: List[Dict[str, Any]] = []

        # Case A: entries with ']' (positive entries per 4.1)
        if "]" in entry:
            base_part, rest = entry.split("]", 1)
            base_reading = base_part.strip()
            rest = rest.strip()

            # Segment the right part on ';' to allow multiple omissions
            segments = [seg.strip() for seg in rest.split(";") if seg.strip()]

            for seg in segments:
                # 1) Pure ">" omission: "> witnesses"
                if seg.startswith(">"):
                    witnesses_str = seg[1:].strip()
                    _, witnesses = split_variant_and_witnesses(witnesses_str) if witnesses_str else ("", [])
                    variants.append({
                        "type": "omission",
                        "symbol": ">",
                        "text": "",
                        "omit_scope": "all",
                        "omitted_text": None,
                        "witnesses": witnesses,
                    })
                    continue

                # 2) "om X witnesses": partial omission inside base_reading
                if seg.startswith("om "):
                    content = seg[3:].strip()
                    if not content:
                        continue
                    omitted_text, witnesses = split_variant_and_witnesses(content)
                    variants.append({
                        "type": "omission",
                        "symbol": "om",
                        "text": "",
                        "omit_scope": "portion",
                        "omitted_text": omitted_text,
                        "witnesses": witnesses,
                    })
                    continue

                # 3) "absc", "semel scr", "non hab" after ']'
                for symbol in ("absc", "semel scr", "non hab"):
                    if seg.startswith(symbol):
                        payload = seg[len(symbol):].strip()
                        _, witnesses = split_variant_and_witnesses(payload) if payload else ("", [])
                        variants.append({
                            "type": "omission",
                            "symbol": symbol,
                            "text": "",
                            "omit_scope": "all",
                            "omitted_text": None,
                            "witnesses": witnesses,
                        })
                        break
                else:
                    # 4) Segment starting with "◠..." -> range omission
                    if seg.startswith("◠"):
                        content = seg[1:].strip()
                        end_selector, witnesses = split_variant_and_witnesses(content)
                        variants.append({
                            "type": "omission",
                            "symbol": "◠",
                            "text": "",
                            "omit_scope": "range",
                            "omitted_text": None,
                            "range_end": end_selector,
                            "witnesses": witnesses,
                        })

            if not variants:
                return None

            return {
                "rule_applied": self.rule_name,
                "base_reading": base_reading,
                "variants": variants,
            }

        # Case B: negative entries starting with "om "
        if entry.startswith("om "):
            content = entry[3:].strip()
            if not content:
                return None

            omitted_text, witnesses = split_variant_and_witnesses(content)

            # In questo caso la stringa dopo "om" è la Critical Text Passage stessa:
            # la trattiamo come omissione "all" di quel segmento.
            base_reading = omitted_text

            return {
                "rule_applied": self.rule_name,
                "base_reading": base_reading,
                "variants": [{
                    "type": "omission",
                    "symbol": "om",
                    "text": "",
                    "omit_scope": "all",
                    "omitted_text": omitted_text,
                    "witnesses": witnesses,
                }],
            }

        # Case C: range omission without ']' e con "◠", es. "καί 2°◠3° 414 Iust ..."
        if "◠" in entry:
            range_text, witnesses = split_variant_and_witnesses(entry)
            base_reading = range_text  # approssimazione: l’intervallo stesso

            return {
                "rule_applied": self.rule_name,
                "base_reading": base_reading,
                "variants": [{
                    "type": "omission",
                    "symbol": "◠",
                    "text": "",
                    "omit_scope": "range",
                    "omitted_text": None,
                    "witnesses": witnesses,
                }],
            }

        return None
