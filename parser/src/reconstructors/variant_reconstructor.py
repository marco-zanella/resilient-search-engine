"""
Phase 5: Variant Reconstructor

Takes parsed variants and OSIS XML to reconstruct full variant texts.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from lxml import etree
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class VariantReconstructor:
    """Reconstructs full variant texts from parsed entries and OSIS XML"""

    def __init__(self, osis_file: Path):
        self.osis_file = osis_file
        self.verses = {}  # Cache: {osis_id: verse_text}
        self._load_osis()

    def _load_osis(self):
        """Load and parse OSIS XML file, extracting verse texts"""
        print(f"Loading OSIS file: {self.osis_file}...")

        try:
            tree = etree.parse(str(self.osis_file))
            root = tree.getroot()

            # OSIS namespace
            ns = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}

            # Find all verse elements
            # OSIS structure: <verse sID="..."/> text <verse eID="..."/>
            for verse_start in root.xpath('//osis:verse[@sID]', namespaces=ns):
                osis_id = verse_start.get('sID')

                # Get text - it's in the tail of the sID element
                text_parts = []

                # Start with the tail of sID element
                if verse_start.tail:
                    text_parts.append(verse_start.tail)

                # Then follow siblings until we hit eID
                current = verse_start.getnext()
                while current is not None:
                    # Check if we've reached the end marker
                    if current.tag == f"{{{ns['osis']}}}verse" and current.get('eID') == osis_id:
                        break

                    # Extract text and tail
                    if current.text:
                        text_parts.append(current.text)
                    if current.tail:
                        text_parts.append(current.tail)

                    current = current.getnext()

                verse_text = ''.join(text_parts).strip()
                self.verses[osis_id] = verse_text

            print(f"Loaded {len(self.verses)} verses from OSIS")

        except Exception as e:
            print(f"Error loading OSIS file: {e}")
            # Continue with empty verses dict

    def get_verse_text(self, osis_id: str) -> Optional[str]:
        """Get the base text for a verse"""
        return self.verses.get(osis_id)

    def reconstruct_variant(self, base_text: str, base_reading: str, operation: Dict) -> Optional[str]:
        """
        Reconstruct a single variant by applying an operation to the base text.

        Args:
            base_text: The full verse text
            base_reading: The word/phrase in the apparatus
            operation: Dict with 'type', 'text', 'witnesses'

        Returns:
            The reconstructed variant text, or None if reconstruction failed
        """
        op_type = operation['type']
        variant_text = operation.get('text', '')

        # Find the base_reading in the base_text
        if base_reading and base_reading in base_text:
            if op_type == 'substitution':
                # Replace base_reading with variant_text
                return base_text.replace(base_reading, variant_text, 1)

            elif op_type == 'addition':
                # Add variant_text after base_reading
                return base_text.replace(base_reading, f"{base_reading} {variant_text}", 1)

            elif op_type == 'omission':
                # Remove base_reading
                return base_text.replace(base_reading, '', 1).strip()

        # If we can't find base_reading, we can't reconstruct
        return None

    def reconstruct_entries(self, parsed_entries: List[Dict]) -> List[Dict]:
        """
        Reconstruct all variants from parsed entries.

        Returns a list of reconstructed variants with full texts.
        """
        reconstructed = []

        for entry in parsed_entries:
            osis_id = entry.get('osis_id')
            base_text = self.get_verse_text(osis_id)

            if base_text is None:
                # Can't reconstruct without base text
                continue

            base_reading = entry.get('base_reading', '')
            variants = entry.get('variants', [])

            for variant in variants:
                reconstructed_text = self.reconstruct_variant(base_text, base_reading, variant)

                if reconstructed_text:
                    reconstructed_variant = {
                        "book": entry['book'],
                        "chapter": entry['chapter'],
                        "verse": entry['verse'],
                        "osis_id": osis_id,
                        "base_text": base_text,
                        "base_reading": base_reading,
                        "operation_type": variant['type'],
                        "variant_reading": variant.get('text', ''),
                        "reconstructed_text": reconstructed_text,
                        "witnesses": variant.get('witnesses', []),
                        "raw_entry": entry.get('raw_entry', ''),
                        "rule_applied": entry.get('rule_applied', '')
                    }
                    reconstructed.append(reconstructed_variant)

        return reconstructed

    def reconstruct_and_save(self, parsed_file: Path, output_file: Path) -> int:
        """
        Load parsed entries, reconstruct variants, and save.

        Returns the number of reconstructed variants.
        """
        # Load parsed entries
        print(f"\nLoading parsed entries from {parsed_file}...")
        with open(parsed_file, 'r', encoding='utf-8') as f:
            parsed_entries = json.load(f)

        print(f"Loaded {len(parsed_entries)} parsed entries")
        print("Reconstructing variants...")

        # Reconstruct
        reconstructed_variants = self.reconstruct_entries(parsed_entries)

        # Save
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(reconstructed_variants, f, ensure_ascii=False, indent=2)

        print(f"\nSaved {len(reconstructed_variants)} reconstructed variants to {output_file}")

        # Calculate success rate
        total_operations = sum(len(e.get('variants', [])) for e in parsed_entries)
        success_rate = round(len(reconstructed_variants) / total_operations * 100, 2) if total_operations > 0 else 0

        print(f"Reconstruction success rate: {success_rate}% ({len(reconstructed_variants)}/{total_operations})")

        return len(reconstructed_variants)


def main():
    """Main entry point for testing"""
    osis_file = Path("sources/text/GLXX_genesis.xml")
    parsed_file = Path("data/intermediate/genesis_app1_parsed.json")
    output_file = Path("data/output/genesis_app1_reconstructed.json")

    reconstructor = VariantReconstructor(osis_file)
    num_variants = reconstructor.reconstruct_and_save(parsed_file, output_file)

    print(f"\n{'='*60}")
    print(f"RECONSTRUCTION COMPLETE")
    print(f"{'='*60}")
    print(f"Total reconstructed variants: {num_variants}")
    print(f"Output file: {output_file}")


if __name__ == "__main__":
    main()
