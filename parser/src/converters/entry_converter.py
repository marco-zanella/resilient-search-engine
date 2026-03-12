"""
Phase 4: Entry Converter

Applies parsing rules to extracted entries to create structured variants.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rules.base_rule import RuleRegistry
from src.rules.simple_substitution import SimpleSubstitutionRule
from src.rules.addition_rule import AdditionRule
from src.rules.omission_rule import OmissionRule
from src.rules.transposition_rule import TranspositionRule
from src.rules.deletion_rule import DeletionRule


class EntryConverter:
    """Converts extracted entries using parsing rules"""

    def __init__(self):
        self.registry = RuleRegistry()
        self._register_rules()

    def _register_rules(self):
        """Register all available rules with priorities"""
        # Lower priority = tried first
        self.registry.register(AdditionRule(), priority=10)
        self.registry.register(OmissionRule(), priority=20)
        self.registry.register(TranspositionRule(), priority=25)
        self.registry.register(DeletionRule(), priority=27)
        self.registry.register(SimpleSubstitutionRule(), priority=30)

    def convert_entries(self, entries: List[Dict]) -> Dict[str, Any]:
        """
        Convert a list of extracted entries into parsed variants.

        Returns:
            {
                "parsed_entries": [...],
                "unparsed_entries": [...],
                "statistics": {...}
            }
        """
        parsed_entries = []
        unparsed_entries = []

        for entry in entries:
            raw_entry = entry.get("raw_entry", "")

            # Try to parse the entry
            parse_result = self.registry.parse_entry(raw_entry)

            if parse_result is not None:
                # Successfully parsed
                parsed_entry = {
                    **entry,  # Include all original metadata
                    "parsed": True,
                    **parse_result  # Add parsed data
                }
                parsed_entries.append(parsed_entry)
            else:
                # Could not parse
                unparsed_entry = {
                    **entry,
                    "parsed": False,
                    "reason": "No matching rule found"
                }
                unparsed_entries.append(unparsed_entry)

        # Calculate statistics
        total = len(entries)
        parsed_count = len(parsed_entries)
        unparsed_count = len(unparsed_entries)

        # Count by rule type
        rule_counts = {}
        for entry in parsed_entries:
            rule_name = entry.get("rule_applied", "Unknown")
            rule_counts[rule_name] = rule_counts.get(rule_name, 0) + 1

        statistics = {
            "total_entries": total,
            "parsed_count": parsed_count,
            "unparsed_count": unparsed_count,
            "parse_rate": round(parsed_count / total * 100, 2) if total > 0 else 0,
            "rules_used": rule_counts,
            "registered_rules": self.registry.get_rule_count()
        }

        return {
            "parsed_entries": parsed_entries,
            "unparsed_entries": unparsed_entries,
            "statistics": statistics
        }

    def convert_and_save(self, input_path: Path, output_parsed: Path, output_unparsed: Path) -> Dict[str, Any]:
        """
        Load entries, convert them, and save results.

        Returns statistics dictionary.
        """
        # Load extracted entries
        print(f"Loading entries from {input_path}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            entries = json.load(f)

        print(f"Loaded {len(entries)} entries")
        print(f"Converting with {self.registry.get_rule_count()} registered rules...")

        # Convert
        results = self.convert_entries(entries)

        # Save parsed entries
        output_parsed.parent.mkdir(parents=True, exist_ok=True)
        with open(output_parsed, 'w', encoding='utf-8') as f:
            json.dump(results["parsed_entries"], f, ensure_ascii=False, indent=2)

        print(f"Saved {len(results['parsed_entries'])} parsed entries to {output_parsed}")

        # Save unparsed entries for future work
        output_unparsed.parent.mkdir(parents=True, exist_ok=True)
        with open(output_unparsed, 'w', encoding='utf-8') as f:
            json.dump(results["unparsed_entries"], f, ensure_ascii=False, indent=2)

        print(f"Saved {len(results['unparsed_entries'])} unparsed entries to {output_unparsed}")

        # Print statistics
        stats = results["statistics"]
        print("\n" + "="*60)
        print("CONVERSION STATISTICS")
        print("="*60)
        print(f"Total entries:        {stats['total_entries']}")
        print(f"Parsed successfully:  {stats['parsed_count']} ({stats['parse_rate']}%)")
        print(f"Unparsed:             {stats['unparsed_count']}")
        print(f"\nRules used:")
        for rule_name, count in stats['rules_used'].items():
            percentage = round(count / stats['total_entries'] * 100, 2)
            print(f"  {rule_name:30} {count:6} ({percentage:5.2f}%)")
        print("="*60)

        return stats


def main():
    """Main entry point for testing"""
    input_file = Path("data/intermediate/genesis_app1_extracted.json")
    output_parsed = Path("data/intermediate/genesis_app1_parsed.json")
    output_unparsed = Path("data/intermediate/genesis_app1_unparsed.json")

    converter = EntryConverter()
    stats = converter.convert_and_save(input_file, output_parsed, output_unparsed)


if __name__ == "__main__":
    main()
