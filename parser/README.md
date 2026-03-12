# Septuagint Apparatus Converter

Converter for the Septuagint critical apparatus (Göttingen edition from Logos) into structured JSON format with reconstructed textual variants.

## Overview

This project converts Septuagint critical apparatus data from unstructured text files into structured JSON format with reconstructed textual variants. The pipeline extracts apparatus entries, applies parsing rules, reconstructs full variant texts, and expands witness abbreviations.

## Quick Start

### 1. Setup

Activate the virtual environment:

```bash
source venv/bin/activate
```

### 2. Run Pipeline

**Process a single book:**

```bash
python run_pipeline.py genesis
python run_pipeline.py exodus --apparatus apparatus-2
```

**Process all books automatically:**

```bash
python run_pipeline.py --all
```

This will:
- Discover all available books in `sources/text/`
- Process each book with both apparatus-1 and apparatus-2 (when available)
- Display global statistics upon completion

### 3. View Results

Output files are saved in `data/output/`:
- `{book}_app1_reconstructed_expanded.json` - Final reconstructed variants with expanded witnesses (apparatus-1)
- `{book}_app2_reconstructed_expanded.json` - Final reconstructed variants with expanded witnesses (apparatus-2)
- `data/intermediate/{book}_app1_unparsed.json` - Entries that couldn't be parsed (for analysis)

## Current Results

### Pentateuch (Completed)

**Apparatus-1:**
| Book | Extracted | Parsed | Parse Rate | Reconstructed |
|------|-----------|--------|------------|---------------|
| Genesis | 14,076 | 10,091 | 71.68% | 9,484 |
| Exodus | 18,151 | 13,376 | 73.69% | 10,768 |
| Leviticus | 11,429 | 8,835 | 77.30% | 8,151 |
| Numbers | 15,750 | 11,723 | 74.43% | 12,150 |
| Deuteronomy | 14,550 | 10,634 | 73.09% | 9,255 |
| **TOTAL** | **73,956** | **54,659** | **73.89%** | **49,808** |

**Apparatus-2 (Hexaplaric):**
| Book | Extracted | Parsed | Parse Rate | Reconstructed |
|------|-----------|--------|------------|---------------|
| Genesis | 302 | 300 | 99.34% | 241 |
| Exodus | 1,346 | 1,336 | 99.26% | 1,060 |
| Leviticus | 1,013 | 1,008 | 99.51% | 815 |
| Numbers | 582 | 575 | 98.80% | 362 |
| Deuteronomy | 973 | 968 | 99.49% | 619 |
| **TOTAL** | **4,216** | **4,187** | **99.31%** | **3,097** |

### Full Corpus Statistics

Running `python run_pipeline.py --all` processes the entire Septuagint:

- **42 books** with apparatus-1: 177,624 entries, 70.08% parse rate, 64,194 variants
- **29 books** with apparatus-2: 13,991 entries, 97.76% parse rate, 3,788 variants
- **Grand Total**: 191,615 entries extracted, 140,375 parsed (81.38%), 67,982 variants reconstructed

## Pipeline Stages

### Phase 2: Entry Extraction
Extracts apparatus entries from raw text files, handling verse identification, interpolations, and safe separator splitting.

### Phase 3-4: Rule Application
Applies parsing rules to convert entries into structured format. Currently implements 3 rules:
- **SimpleSubstitutionRule**: `word] variant witnesses`
- **AdditionRule**: `word] + text witnesses`
- **OmissionRule**: `word] > witnesses` or `om word witnesses`

### Phase 5: Variant Reconstruction
Reconstructs full variant texts by applying operations (substitution/addition/omission) to OSIS XML base text.

### Phase 6: Witness Expansion
Expands witness abbreviations using `doc/witnesses.csv` (242 witnesses currently documented).

## Output Format

### Reconstructed Variant Example

```json
{
  "book": "glxx_genesis",
  "chapter": "1",
  "verse": "1",
  "osis_id": "glxx_genesis.1.1",
  "base_text": "Ἐν ἀρχῇ ἐποίησεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν.",
  "base_reading": "ἐποίησεν",
  "operation_type": "substitution",
  "variant_reading": "επλασεν",
  "reconstructed_text": "Ἐν ἀρχῇ επλασεν ὁ θεὸς τὸν οὐρανὸν καὶ τὴν γῆν.",
  "witnesses": [
    {
      "abbr": "664",
      "name": "Vatican City, BAV, Reg. gr. Pio II 20"
    }
  ],
  "raw_entry": "ἐποίησεν] επλασεν 664",
  "rule_applied": "SimpleSubstitutionRule"
}
```

## Extending the System

### Adding New Rules

1. Create a new file in `src/rules/`
2. Inherit from `BaseRule`
3. Implement `can_parse()` and `parse()` methods
4. Register in `src/converters/entry_converter.py`

Example:

```python
from src.rules.base_rule import BaseRule

class MyNewRule(BaseRule):
    def can_parse(self, entry: str) -> bool:
        return 'pattern' in entry

    def parse(self, entry: str) -> Optional[Dict]:
        # Parse logic here
        return {
            "rule_applied": self.rule_name,
            "base_reading": "...",
            "variants": [...]
        }
```

### Processing Additional Books

The system is designed to handle any book:

```bash
# Single book
python run_pipeline.py joshua
python run_pipeline.py isaiah --apparatus apparatus-2

# All books
python run_pipeline.py --all
```

## Key Implementation Details

### Multi-word Variant Handling

The system uses intelligent witness detection (`src/utils/witness_parser.py`) to correctly parse multi-word variants. It recognizes witness patterns (manuscript numbers, abbreviations, version names) to split variant text from witness lists.

### Safe Separator Handling

The entry extractor safely splits on `|` separators while respecting parentheses (Greek text within parentheses may contain `|` as punctuation, not separator).

### Expandable Architecture

The rule-based system is designed for easy expansion. New parsing patterns can be added without modifying existing code.

## Next Steps

1. **Improve parse rates**: Analyze `data/intermediate/*_unparsed.json` to identify missing patterns
2. **Expand witness database**: Add more witnesses to `doc/witnesses.csv`
3. **Improve reconstruction**: Implement fuzzy matching for base readings
4. **Add complex rules**: Transposition (`tr`), prefix (`pr`), complex patterns

## Project Structure

```
/
├── src/
│   ├── parsers/           # Entry extraction
│   ├── rules/             # Parsing rules (expandable)
│   ├── converters/        # Rule application
│   ├── reconstructors/    # Variant reconstruction
│   └── utils/             # Witness parser, expander
├── data/
│   ├── intermediate/      # Extracted and parsed entries
│   └── output/            # Final reconstructed variants
├── sources/
│   ├── apparatus-1/       # Main apparatus files
│   ├── apparatus-2/       # Hexaplaric apparatus files
│   └── text/              # OSIS XML base texts
├── doc/                   # Documentation (witnesses.csv)
├── run_pipeline.py        # Master script
└── CLAUDE.md              # Technical documentation for AI
```

## Dependencies

- Python 3.12.3+
- lxml (for XML parsing)

Install: `pip install -r requirements.txt`

## Troubleshooting

### Low parse rate?
Check `data/intermediate/{book}_app1_unparsed.json` to see what patterns are missing. Implement new rules for common patterns.

### Reconstruction failures?
Verify that:
- OSIS XML file exists and is well-formed
- Base readings in apparatus match text in OSIS
- OSIS verse IDs match the expected format

### No output files?
Ensure:
- Source files exist in `sources/apparatus-1/`, `sources/apparatus-2/`, and `sources/text/`
- Virtual environment is activated
- All dependencies are installed
