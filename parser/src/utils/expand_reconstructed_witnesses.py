"""
Expand Witnesses in Reconstructed Variants

Takes reconstructed variants JSON and expands witness abbreviations.
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.witness_expander import WitnessExpander


def expand_reconstructed_witnesses(
    input_file: Path,
    output_file: Path,
    witnesses_csv: Path
):
    """
    Expand witnesses in reconstructed variants file.

    Args:
        input_file: Input JSON with reconstructed variants
        output_file: Output JSON with expanded witnesses
        witnesses_csv: Path to witnesses.csv
    """
    print(f"Loading reconstructed variants from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        variants = json.load(f)

    print(f"Loaded {len(variants)} variants")

    # Initialize expander
    expander = WitnessExpander(witnesses_csv)

    # Track statistics
    all_witnesses = []
    expanded_variants = []

    print("Expanding witnesses...")
    for variant in variants:
        # Get witness list
        witnesses = variant.get("witnesses", [])
        all_witnesses.extend(witnesses)

        # Expand witnesses
        expanded_witnesses = expander.expand_witnesses(witnesses)

        # Create new variant with expanded witnesses
        expanded_variant = {
            **variant,  # Copy all original fields
            "witnesses": expanded_witnesses  # Replace with expanded version
        }

        expanded_variants.append(expanded_variant)

    # Calculate statistics
    stats = expander.get_expansion_statistics(all_witnesses)

    # Count most common unexpanded witnesses
    unexpanded = [w for w in all_witnesses if w not in expander.witness_map]
    most_common_unexpanded = Counter(unexpanded).most_common(20)

    # Save output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(expanded_variants, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(expanded_variants)} variants with expanded witnesses to {output_file}")

    # Print statistics
    print("\n" + "="*70)
    print("WITNESS EXPANSION STATISTICS")
    print("="*70)
    print(f"Total witness occurrences:  {stats['total']}")
    print(f"Found in witnesses.csv:     {stats['found']} ({stats['found_rate']}%)")
    print(f"Not found:                  {stats['not_found']}")

    if most_common_unexpanded:
        print(f"\nTop 20 unexpanded witnesses:")
        for witness, count in most_common_unexpanded:
            print(f"  {witness:30} ({count} occurrences)")

    print("="*70)

    return stats


def main():
    """Main entry point"""
    input_file = Path("data/output/genesis_app1_reconstructed.json")
    output_file = Path("data/output/genesis_app1_reconstructed_expanded.json")
    witnesses_csv = Path("doc/witnesses.csv")

    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    if not witnesses_csv.exists():
        print(f"Error: Witnesses CSV not found: {witnesses_csv}")
        sys.exit(1)

    stats = expand_reconstructed_witnesses(input_file, output_file, witnesses_csv)


if __name__ == "__main__":
    main()
