#!/usr/bin/env python3
"""
Septuagint Apparatus Converter - Full Pipeline

Runs the complete pipeline from apparatus extraction to variant reconstruction.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parsers.apparatus_extractor import ApparatusExtractor
from src.converters.entry_converter import EntryConverter
from src.reconstructors.variant_reconstructor import VariantReconstructor
from src.utils.expand_reconstructed_witnesses import expand_reconstructed_witnesses


def run_pipeline(book_name: str, apparatus_type: str = "apparatus-1", quiet: bool = False):
    """
    Run the complete pipeline for a book.

    Args:
        book_name: Name of the book (e.g., "genesis", "exodus")
        apparatus_type: "apparatus-1" or "apparatus-2"
        quiet: If True, suppress detailed output (for batch processing)

    Returns:
        dict: Statistics about the processing, or None if failed
    """
    if not quiet:
        print("="*70)
        print(f"SEPTUAGINT APPARATUS CONVERTER - FULL PIPELINE")
        print(f"Book: {book_name.upper()}")
        print(f"Apparatus: {apparatus_type}")
        print("="*70)
    else:
        print(f"\nProcessing {book_name.upper()} - {apparatus_type}...")

    # File paths
    if apparatus_type == "apparatus-1":
        apparatus_file = Path(f"sources/apparatus-1/GLXX_{book_name}.txt")
    else:
        apparatus_file = Path(f"sources/apparatus-2/GLXX_{book_name}.txt")

    osis_file = Path(f"sources/text/GLXX_{book_name}.xml")

    book_id = f"glxx_{book_name}"
    app_suffix = "app1" if apparatus_type == "apparatus-1" else "app2"

    extracted_file = Path(f"data/intermediate/{book_name}_{app_suffix}_extracted.json")
    parsed_file = Path(f"data/intermediate/{book_name}_{app_suffix}_parsed.json")
    unparsed_file = Path(f"data/intermediate/{book_name}_{app_suffix}_unparsed.json")
    output_file = Path(f"data/output/{book_name}_{app_suffix}_reconstructed.json")
    expanded_file = Path(f"data/output/{book_name}_{app_suffix}_reconstructed_expanded.json")
    witnesses_csv = Path("doc/witnesses.csv")

    # Check if files exist
    if not apparatus_file.exists():
        if not quiet:
            print(f"❌ Error: Apparatus file not found: {apparatus_file}")
        return None

    if not osis_file.exists():
        if not quiet:
            print(f"❌ Error: OSIS file not found: {osis_file}")
        return None

    # Phase 2: Extract entries
    if not quiet:
        print(f"\n{'='*70}")
        print("PHASE 2: EXTRACTING ENTRIES")
        print("="*70)

    extractor = ApparatusExtractor(
        apparatus_file=apparatus_file,
        book_name=book_id,
        apparatus_type=apparatus_type
    )
    num_entries = extractor.extract_and_save(extracted_file)

    # Phase 4: Convert entries
    if not quiet:
        print(f"\n{'='*70}")
        print("PHASE 4: CONVERTING ENTRIES (APPLYING RULES)")
        print("="*70)

    converter = EntryConverter()
    stats = converter.convert_and_save(extracted_file, parsed_file, unparsed_file)

    # Phase 5: Reconstruct variants
    if not quiet:
        print(f"\n{'='*70}")
        print("PHASE 5: RECONSTRUCTING VARIANTS")
        print("="*70)

    reconstructor = VariantReconstructor(osis_file)
    num_variants = reconstructor.reconstruct_and_save(parsed_file, output_file)

    # Phase 6: Expand witnesses
    if not quiet:
        print(f"\n{'='*70}")
        print("PHASE 6: EXPANDING WITNESSES")
        print("="*70)

    expand_reconstructed_witnesses(output_file, expanded_file, witnesses_csv)

    # Final summary
    if not quiet:
        print(f"\n{'='*70}")
        print("PIPELINE COMPLETE - FINAL SUMMARY")
        print("="*70)
        print(f"Book:                  {book_name.upper()}")
        print(f"Apparatus:             {apparatus_type}")
        print(f"\nResults:")
        print(f"  Entries extracted:   {num_entries}")
        print(f"  Entries parsed:      {stats['parsed_count']} ({stats['parse_rate']}%)")
        print(f"  Entries unparsed:    {stats['unparsed_count']}")
        print(f"  Variants generated:  {num_variants}")
        print(f"\nOutput files:")
        print(f"  Reconstructed:       {output_file}")
        print(f"  Expanded:            {expanded_file}")
        print(f"  Unparsed entries:    {unparsed_file}")
        print("="*70)

    return {
        "book": book_name,
        "apparatus": apparatus_type,
        "extracted": num_entries,
        "parsed": stats["parsed_count"],
        "unparsed": stats["unparsed_count"],
        "parse_rate": stats["parse_rate"],
        "reconstructed": num_variants
    }


def discover_books():
    """
    Discover all available books by scanning the sources directory.

    Returns:
        list: List of book names that have source files
    """
    sources_dir = Path("sources/text")
    if not sources_dir.exists():
        return []

    books = []
    for xml_file in sources_dir.glob("GLXX_*.xml"):
        book_name = xml_file.stem.replace("GLXX_", "")
        books.append(book_name)

    return sorted(books)


def run_all_books():
    """
    Run pipeline on all available books (both apparatus-1 and apparatus-2).

    Returns:
        list: List of result dictionaries for each processed book/apparatus
    """
    print("="*80)
    print("SEPTUAGINT APPARATUS CONVERTER - BATCH PROCESSING")
    print("="*80)

    books = discover_books()
    if not books:
        print("❌ No books found in sources/text/")
        return []

    print(f"\nDiscovered {len(books)} books:")
    print(f"  {', '.join(books)}")
    print(f"\nProcessing all books with apparatus-1 and apparatus-2 (when available)...")
    print("="*80)

    results = []

    for book in books:
        # Try apparatus-1
        result = run_pipeline(book, "apparatus-1", quiet=True)
        if result:
            results.append(result)
            print(f"  ✓ {book} (apparatus-1): {result['parsed']}/{result['extracted']} parsed ({result['parse_rate']:.1f}%)")
        else:
            print(f"  ⊘ {book} (apparatus-1): not available")

        # Try apparatus-2
        result = run_pipeline(book, "apparatus-2", quiet=True)
        if result:
            results.append(result)
            print(f"  ✓ {book} (apparatus-2): {result['parsed']}/{result['extracted']} parsed ({result['parse_rate']:.1f}%)")
        else:
            print(f"  ⊘ {book} (apparatus-2): not available")

    # Print global statistics
    print("\n" + "="*80)
    print("GLOBAL STATISTICS")
    print("="*80)

    if not results:
        print("No books were successfully processed.")
        return results

    # Separate by apparatus type
    app1_results = [r for r in results if r["apparatus"] == "apparatus-1"]
    app2_results = [r for r in results if r["apparatus"] == "apparatus-2"]

    print(f"\n{'Book':<20} {'Apparatus':<15} {'Extracted':<12} {'Parsed':<12} {'Parse Rate':<12} {'Reconstructed'}")
    print("-"*80)

    for r in results:
        print(f"{r['book'].capitalize():<20} {r['apparatus']:<15} {r['extracted']:<12} "
              f"{r['parsed']:<12} {r['parse_rate']:>6.2f}%     {r['reconstructed']}")

    # Apparatus-1 totals
    if app1_results:
        total_extracted_1 = sum(r["extracted"] for r in app1_results)
        total_parsed_1 = sum(r["parsed"] for r in app1_results)
        total_reconstructed_1 = sum(r["reconstructed"] for r in app1_results)
        avg_parse_rate_1 = sum(r["parse_rate"] for r in app1_results) / len(app1_results)

        print("-"*80)
        print(f"{'TOTAL (apparatus-1)':<20} {'':<15} {total_extracted_1:<12} "
              f"{total_parsed_1:<12} {avg_parse_rate_1:>6.2f}%     {total_reconstructed_1}")

    # Apparatus-2 totals
    if app2_results:
        total_extracted_2 = sum(r["extracted"] for r in app2_results)
        total_parsed_2 = sum(r["parsed"] for r in app2_results)
        total_reconstructed_2 = sum(r["reconstructed"] for r in app2_results)
        avg_parse_rate_2 = sum(r["parse_rate"] for r in app2_results) / len(app2_results)

        print(f"{'TOTAL (apparatus-2)':<20} {'':<15} {total_extracted_2:<12} "
              f"{total_parsed_2:<12} {avg_parse_rate_2:>6.2f}%     {total_reconstructed_2}")

    # Grand totals
    total_extracted = sum(r["extracted"] for r in results)
    total_parsed = sum(r["parsed"] for r in results)
    total_reconstructed = sum(r["reconstructed"] for r in results)
    avg_parse_rate = sum(r["parse_rate"] for r in results) / len(results)

    print("-"*80)
    print(f"{'GRAND TOTAL':<20} {'':<15} {total_extracted:<12} "
          f"{total_parsed:<12} {avg_parse_rate:>6.2f}%     {total_reconstructed}")

    print("="*80)
    print(f"\nProcessed {len(app1_results)} books with apparatus-1")
    print(f"Processed {len(app2_results)} books with apparatus-2")
    print(f"Total: {len(results)} book/apparatus combinations")
    print(f"\nAll output files saved in: data/output/")
    print("="*80)

    return results


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Septuagint Apparatus Converter pipeline"
    )
    parser.add_argument(
        "book",
        nargs="?",
        help="Book name (e.g., genesis, exodus, amos). Use --all to process all books."
    )
    parser.add_argument(
        "--apparatus",
        choices=["apparatus-1", "apparatus-2"],
        default="apparatus-1",
        help="Apparatus type (default: apparatus-1)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all available books (both apparatus-1 and apparatus-2)"
    )

    args = parser.parse_args()

    if args.all:
        results = run_all_books()
        sys.exit(0 if results else 1)
    elif args.book:
        result = run_pipeline(args.book, args.apparatus)
        sys.exit(0 if result else 1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
