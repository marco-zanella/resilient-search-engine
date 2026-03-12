"""
Witness Expander

Expands witness abbreviations using the witnesses.csv documentation.
"""

import csv
from pathlib import Path
from typing import Dict, List, Optional


class WitnessExpander:
    """Expands witness abbreviations to full information"""

    def __init__(self, witnesses_csv: Path):
        self.witnesses_csv = witnesses_csv
        self.witness_map = {}  # {abbr: full_info_dict}
        self._load_witnesses()

    def _load_witnesses(self):
        """Load witness abbreviations from CSV"""
        print(f"Loading witnesses from {self.witnesses_csv}...")

        try:
            with open(self.witnesses_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    abbr = row.get("Rahlfs' Siglum", "").strip()
                    if not abbr:
                        continue

                    # Store full information
                    self.witness_map[abbr] = {
                        "abbreviation": abbr,
                        "place": row.get("Place", "").strip(),
                        "institution": row.get("Institution", "").strip(),
                        "shelfmark": row.get("Shelfmark", "").strip(),
                        "date": row.get("Date", "").strip(),
                        "description": row.get("Gottingen Description", "").strip()
                    }

            print(f"Loaded {len(self.witness_map)} witnesses")

        except Exception as e:
            print(f"Error loading witnesses CSV: {e}")
            # Continue with empty witness map

    def expand_witness(self, abbr: str) -> Dict[str, str]:
        """
        Expand a single witness abbreviation.

        Returns:
            {"abbr": "...", "name": "..."}
            If not found, name will be the same as abbr.
        """
        witness_info = self.witness_map.get(abbr)

        if witness_info:
            # Build a readable name from available info
            parts = []
            if witness_info.get("place"):
                parts.append(witness_info["place"])
            if witness_info.get("institution"):
                parts.append(witness_info["institution"])
            if witness_info.get("shelfmark"):
                parts.append(witness_info["shelfmark"])

            name = ", ".join(parts) if parts else abbr
        else:
            # Not found - use abbreviation as name
            name = abbr

        return {
            "abbr": abbr,
            "name": name
        }

    def expand_witnesses(self, witness_list: List[str]) -> List[Dict[str, str]]:
        """
        Expand a list of witness abbreviations.

        Args:
            witness_list: List of abbreviation strings

        Returns:
            List of {"abbr": "...", "name": "..."} dicts
        """
        return [self.expand_witness(w) for w in witness_list]

    def get_expansion_statistics(self, witness_list: List[str]) -> Dict:
        """
        Get statistics about witness expansion for a list.

        Returns:
            {
                "total": int,
                "found": int,
                "not_found": int,
                "found_rate": float
            }
        """
        total = len(witness_list)
        found = sum(1 for w in witness_list if w in self.witness_map)
        not_found = total - found
        found_rate = round(found / total * 100, 2) if total > 0 else 0

        return {
            "total": total,
            "found": found,
            "not_found": not_found,
            "found_rate": found_rate
        }


def main():
    """Test the witness expander"""
    witnesses_csv = Path("doc/witnesses.csv")

    expander = WitnessExpander(witnesses_csv)

    # Test with some examples
    test_witnesses = ["A", "B", "664", "Phil I 10.5", "unknown"]

    print("\nTest expansions:")
    for w in test_witnesses:
        result = expander.expand_witness(w)
        print(f"  {w:20} -> {result['name']}")

    # Statistics
    stats = expander.get_expansion_statistics(test_witnesses)
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    main()
