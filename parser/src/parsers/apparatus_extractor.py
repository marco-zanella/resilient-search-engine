"""
Phase 2: Apparatus Entry Extractor

Extracts all variant entries from apparatus files into a structured JSON format.
Handles:
- Chapter:verse identification
- Entry splitting by | (excluding parentheses)
- Verse range notation (e.g., 27—28)
- Interpolated verses [n]
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class ApparatusExtractor:
    """Extracts entries from apparatus files"""

    def __init__(self, apparatus_file: Path, book_name: str, apparatus_type: str = "apparatus-1"):
        self.apparatus_file = apparatus_file
        self.book_name = book_name
        self.apparatus_type = apparatus_type
        self.current_chapter = None

    def split_by_pipe_safe(self, line: str) -> List[str]:
        """
        Split by | but exclude pipes inside parentheses.

        Example:
            "entry1 (note|here) | entry2" -> ["entry1 (note|here) ", " entry2"]
        """
        entries = []
        current_entry = []
        paren_depth = 0

        for char in line:
            if char == '(':
                paren_depth += 1
                current_entry.append(char)
            elif char == ')':
                paren_depth -= 1
                current_entry.append(char)
            elif char == '|' and paren_depth == 0:
                # This is a separator, not a marker
                entries.append(''.join(current_entry))
                current_entry = []
            else:
                current_entry.append(char)

        # Don't forget the last entry
        if current_entry:
            entries.append(''.join(current_entry))

        return [e.strip() for e in entries if e.strip()]

    def parse_verse_identifier(self, text: str) -> Optional[Tuple[Optional[str], str, bool]]:
        """
        Parse verse identifier from the beginning of a line.

        Returns: (chapter, verse, is_interpolated)

        Examples:
            "1:1" -> ("1", "1", False)
            "2" -> (None, "2", False)  # chapter inherited
            "[25]" -> (None, "25", True)
            "27—28" -> (None, "27—28", False)  # range
            "1:[25]" -> ("1", "25", True)
        """
        # Pattern for chapter:verse or [chapter:verse]
        match = re.match(r'^\[?(\d+):(\d+[a-z]?)\]?', text)
        if match:
            chapter, verse = match.groups()
            is_interpolated = text.startswith('[')
            return (chapter, verse, is_interpolated)

        # Pattern for verse only or [verse]
        match = re.match(r'^\[?(\d+[a-z]?(?:—\d+[a-z]?)?)\]?', text)
        if match:
            verse = match.group(1)
            is_interpolated = text.startswith('[')
            return (None, verse, is_interpolated)

        return None

    def extract_entries(self) -> List[Dict]:
        """
        Extract all entries from the apparatus file.

        Returns a list of dictionaries, each representing one entry.
        """
        entries = []
        entry_counter = 0

        with open(self.apparatus_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                # Try to parse verse identifier at the start
                verse_info = self.parse_verse_identifier(line)

                if verse_info is None:
                    print(f"Warning: Could not parse verse identifier in line {line_num}: {line[:50]}...")
                    continue

                chapter, verse, is_interpolated = verse_info

                # Update current chapter if specified
                if chapter:
                    self.current_chapter = chapter

                # Extract the chapter:verse or verse part to find where entries start
                # We need to find where the actual entries begin
                if chapter:
                    prefix = f"{chapter}:{verse}"
                else:
                    prefix = verse

                if is_interpolated:
                    prefix = f"[{prefix}]"

                # Find where entries start (after the verse identifier)
                entries_part = line[len(prefix):].strip()

                # Split by | (safely, excluding parentheses)
                raw_entries = self.split_by_pipe_safe(entries_part)

                # Create entry objects
                for i, raw_entry in enumerate(raw_entries):
                    entry_counter += 1

                    # Build OSIS ID
                    osis_verse = verse.replace('—', '-')  # ranges use hyphen in some systems
                    osis_id = f"{self.book_name}.{self.current_chapter}.{osis_verse}"

                    entry_obj = {
                        "book": self.book_name,
                        "chapter": self.current_chapter,
                        "verse": verse,
                        "osis_id": osis_id,
                        "is_interpolated": is_interpolated,
                        "entry_number": entry_counter,
                        "entry_index_in_verse": i + 1,
                        "raw_entry": raw_entry,
                        "apparatus_type": self.apparatus_type,
                        "source_line": line_num
                    }

                    entries.append(entry_obj)

        return entries

    def extract_and_save(self, output_path: Path) -> int:
        """
        Extract entries and save to JSON file.

        Returns the number of entries extracted.
        """
        entries = self.extract_entries()

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

        print(f"Extracted {len(entries)} entries from {self.apparatus_file.name}")
        print(f"Saved to {output_path}")

        return len(entries)


def main():
    """Main entry point for testing"""
    # Example: Extract from Genesis apparatus-1
    apparatus_file = Path("sources/apparatus-1/GLXX_genesis.txt")
    output_file = Path("data/intermediate/genesis_app1_extracted.json")

    extractor = ApparatusExtractor(
        apparatus_file=apparatus_file,
        book_name="glxx_genesis",
        apparatus_type="apparatus-1"
    )

    num_entries = extractor.extract_and_save(output_file)
    print(f"\nTotal entries extracted: {num_entries}")


if __name__ == "__main__":
    main()
