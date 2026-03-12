"""
check_frequency.py

Script per calcolare la frequenza (in percentuale) di ogni regola negli apparati.
Questa versione usa DUE dizionari hardcoded con i nomi delle regole (NAME_REGEX_APP1, NAME_REGEX_APP2).
Ogni regola ha attualmente come regex un placeholder improbabile "11111" (cinque '1'),
così che non ci siano match e le frequenze risultino 0.00%.

Scopo: permetterti di sostituire *manualmente* la regex per ogni "Name" quando vuoi.
"""

from pathlib import Path
import re
from collections import defaultdict

# ------------------------------------------------------------------------
# DIZIONARI HARDCODED: mapping "Name" -> "Regex placeholder"
# Sostituisci per ogni entry il valore (stringa) con la regex desiderata.
# Attualmente tutte hanno il placeholder r"11111" (non corrisponderà ad alcun testo reale).
# ------------------------------------------------------------------------

PLACEHOLDER_REGEX = r"11111"

NAME_REGEX_APP1 = {
    "1.Critical Apparatus Structure": r"^(?:\d+:)?\d+[a-z]?\s+(?:[^|]|\(\|\))+(?:\|(?:[^|]|\(\|\))+)*$",
    "1.1 Range of Verses": r"^(?:\d+:)?\d+[a-z]?—\d+[a-z]?\s+(?:[^|]|\(\|\))+(?:\|(?:[^|]|\(\|\))+)*$",
    "1.2 Interpolated Verse Structure": r"^\[(?:\d+:)?\d+[a-z]?\]\s+(?:[^|]|\(\|\))+(?:\|(?:[^|]|\(\|\))+)*$",
    "2. Critical Apparatus Entry": r"^(?:(?P<lemma>.+?)\]\s+)?(?P<content>.+)$",
    "3. Critical Apparatus Entry Content: Main Structure": r"^(?:[^\[\]]+\]\s+[^;]+(?:;\s+[^;]+)*|[^\];]+)$",
    "3.1.1 Apparatus Entry Content Type: Positive": r"^[^\[\]]+\]\s+[^;]+(?:;\s+[^;]+)*$",
    "3.1.2 Apparatus Entry Content Type: Negative": r"^[^\];]+$",
    "3.2 Apparatus Entry Content: BaseReadingInApparatus": r"^[^\[\]]+\]",
    "3.3 Apparatus Entry Content: ReadingInApparatus": r"^[^\];]+$",
    "3.3.1 Multiple reading in one ReadingInApparatus": r"^[^\];]+\s(?:et|sed)\s[^\];]+$",
    "4. ReadingInApparatusType: general rule": r"^\s*(?P<type>bis\s+scr|ter\s+scr|semel\s+scr|non\s+hab|sup\s+ras|ex\s+corr|sub\s+(?:metob|÷|※|⸔|~)|pr\s+(?:ras|spat|÷|※|metob|⸔|~)|(?:\+|addunt)\s+(?:ras|n\s+litt|spat|÷|※|metob|⸔|~)|addunt|delebit|delebunt|rescr|metob|absc|litt|spat|ras|del|om|tr|pr|>|◠|÷|※|⸔|~|\+)",
    "4.1 ReadingInApparatusType: omission": PLACEHOLDER_REGEX,
    "4.1.1 Omission: >": PLACEHOLDER_REGEX,
    "4.1.2 Omission: om": PLACEHOLDER_REGEX,
    "4.1.2.1 Multiple omissions with \"om\": consecutive occurrences": PLACEHOLDER_REGEX,
    "4.1.2.2 Multiple omissions with \"om\": \"et\"": PLACEHOLDER_REGEX,
    "4.1.3 Omission: ◠": PLACEHOLDER_REGEX,
    "4.1.4 Omission: absc": PLACEHOLDER_REGEX,
    "4.1.5 Omission: semel scr": PLACEHOLDER_REGEX,
    "4.1.5 Omission: non hab": PLACEHOLDER_REGEX,
    "4.2 ReadingInApparatusType: addition": PLACEHOLDER_REGEX,
    "4.2.1 Addition: \"+\"": PLACEHOLDER_REGEX,
    "4.2.2 Addtion: pr": PLACEHOLDER_REGEX,
    "4.2.3 Addition: bis scr / ter scr": PLACEHOLDER_REGEX,
    "4.2.4 Addition: addunt": PLACEHOLDER_REGEX,
    "4.3 ReadingInApparatusType: transposition": r"^\s*(?:tr\b|.*?\b(?:ante|post|ad)\b.*?\btr\b)",
    "4.3.1Transposition: positive entry with \"/\"": PLACEHOLDER_REGEX,
    "4.3.2 Transposition: positive entry with \"ante\" and \"post\"": PLACEHOLDER_REGEX,
    "4.3.3 Transposition: positive entry with \"ad\" + init/fin": PLACEHOLDER_REGEX,
    "4.3.4 Transposition: negative entry with \"et\"": PLACEHOLDER_REGEX,
    "4.3.5 Transposition: negative entry with \"ante\" and \"post\"": PLACEHOLDER_REGEX,
    "4.3.6 Transposition: negative entry with \"ad\" + init/fin": PLACEHOLDER_REGEX,
    "4.3.7 Transposition: ordo commatum": PLACEHOLDER_REGEX,
    "4.4 ReadingInApparatusType: deletion": r"^\s*(?P<deletion_type>delebunt|delebit|del)\b",
    "4.5 ReadingInApparatusType: correction": PLACEHOLDER_REGEX,
    "4.5.1 ReadingInApparatusType correction\n\nParticular patterns: multiple ReadingStrings": PLACEHOLDER_REGEX,
    "5. Critical Text Passage": r"^(?P<base_reading>[^\]]+)\]",
    "5.1.1 Critical Text Passage Type: Sigle Location": PLACEHOLDER_REGEX,
    "5.1.2 Critical Text Passage Type: Range Location": PLACEHOLDER_REGEX,
    "5.1.3 Critical Text Passage Type: Multiple Locations": PLACEHOLDER_REGEX,
    "5.3.1 Critical Text Passage Type: Multiple EndSelectors": PLACEHOLDER_REGEX,
    "5.3.2 Critical Text Passage Type: Multiple occurrences": PLACEHOLDER_REGEX,
    "5.2.1 Critical Text Passage with Positive Entry": PLACEHOLDER_REGEX,
    "5.2.2 Critical Text Passage with Negative Critical Apparatus Entry": PLACEHOLDER_REGEX,
    "5.3 Critical Text Passage and Passage Selector Overview": PLACEHOLDER_REGEX,
    "5.3.1 Passage Quote Selector": PLACEHOLDER_REGEX,
    "5.3.2 Passage Position Selector": PLACEHOLDER_REGEX,
    "5.3.2.1 Passage Position Selector Type: init": PLACEHOLDER_REGEX,
    "5.3.2.2 Passage Position Selector Type: fin": PLACEHOLDER_REGEX,
    "5.3.2.3 Passage Position Selector Type: comma": PLACEHOLDER_REGEX,
    "5.3.2.3.1 Passage Position Selector Type: commata": PLACEHOLDER_REGEX,
    "5.3.2.4 Passage Position Selector Type: chapter and verse n:n": PLACEHOLDER_REGEX,
    "5.3.2.4.1 Passage Position Selector Type: interpolated chapter and verse [n:n]": PLACEHOLDER_REGEX,
    "5.3.2.5 Passage Position Selector Type: verse (n)": PLACEHOLDER_REGEX,
    "5.3.2.5.1 Passage Position Selector Type: interpolated verse [n]": PLACEHOLDER_REGEX,
    "5.3.2.6 Passage Position Selector Type: occurrence n°": PLACEHOLDER_REGEX,
    "5.3.2.6.1 Passage Position Selector Type: occurrence \"ult\"": PLACEHOLDER_REGEX,
    "6. Witness Management": r"^(?P<content>.*?)\s+(?P<witnesses>(?:(?<!°)\d|[A-Z]|𝔐).*)$",
    "6.1 Witnesses_string: order": PLACEHOLDER_REGEX,
    "6.2 Witnesses_string: management": PLACEHOLDER_REGEX,
    "6.2.1 Witnesses_string management:\n\"-\" symbol": PLACEHOLDER_REGEX,
    "6.2.2 Management of Witness Groups": PLACEHOLDER_REGEX,
    "6.2.2.1 Groups \"La\" and Old Versions": PLACEHOLDER_REGEX,
    "6.2.2.2 Handling Groups: Symbol Exception “−” (U+2212 Minus Sign)": PLACEHOLDER_REGEX,
    "6.2.2.3 Handling Groups: Symbol Exception “−” (U+2212 Minus Sign) with OldVersions": PLACEHOLDER_REGEX,
    "6.2.2.4 Groups \"La\" and Old Versions: verss": PLACEHOLDER_REGEX,
    "6.2.3 Handling Author Citations": PLACEHOLDER_REGEX,
    "6.2.3 Handling Author Citations: Nested Examples": PLACEHOLDER_REGEX,
    "6.2.4  Handling Author Citations: passim": PLACEHOLDER_REGEX,
    "6.2.4 Handling NT Citations": PLACEHOLDER_REGEX,
    "6.2.5 Handling Other_Versions": PLACEHOLDER_REGEX,
    "6.2.6. Handling Other_Versions: printed editions group \"edd\"": PLACEHOLDER_REGEX,
    "7. Handling Notes": r"(?P<note>\([^\)]+\)|(?:\b|(?<=\w))(?:c\s+pr\s+m|omn\s+codd|cf\s+(?:infra|supra)|ex\s+(?:corr|par)|s\s+(?:ind|nom)|c\s+var|pr\s+m|sup\s+lin|txtetmg|Latcodd|Latcod|superscr|relict|mutil|txt[c*]|mg[c*]|codd|rell|plur|sing|comm|mss|txt|Lat|cat|lem|vid|inc|cod|pap|praef|ss|pl|ms|te|ap|c[12]|s|c|\*|\?|\|\?|\|\|))",
    "7.1 Handling Notes in ReadingString": PLACEHOLDER_REGEX,
    "7.1.1 Handling Notes in ReadingString: ...] / [...": PLACEHOLDER_REGEX,
    "7.1.2 Handling Notes in ReadingString: Exception for ν (U+03BD)": PLACEHOLDER_REGEX,
    "7.3 Handling Notes After the Colon": PLACEHOLDER_REGEX,
    "8. ReadingInApparatusCause": r"(?::\s*(?P<cause_explicit>haplogr|homoiar|homoiot|dittogr|absc))|(?P<cause_symbol>◠|absc)",
    "9. Cross-Reference to Apparatus 2 (↓ Indicator)": r"(?P<cross_ref>↓)",
}

NAME_REGEX_APP2 = {
    "1.Hexaplaric Apparatus Structure": r"^(?:(?P<chapter>\d+):)?(?P<verse>\d+[a-z]?)\s+(?P<content>(?:[^|\n]+)(?:\|[^|\n]+)*)$",
    "1.1 Range of Verses": PLACEHOLDER_REGEX,
    "1.2 Interpolated Verse Structure": PLACEHOLDER_REGEX,
    "2. Hexaplaric Apparatus Entry": r"^(?P<base_reading>[^\]]+)\]\s+(?P<hexaplaric_content>.+)$",
    "3. Hexaplaric Apparatus Entry Content: Main Structure": r"^\s*(?:α[′ʹ]|σ[′ʹ]|θ[′ʹ]|οἱ\s+[λγο][′ʹ]|ο̅|ὁ\s+ἑβρ[′ʹ]|τὸ\s+ἑβρ[′ʹ]|τὸ\s+σαμ[′ʹ]|ωρ[′ʹ]|ὁ\s+συρ[′ʹ]|τὸ\s+ἰουδ[′ʹ]|ιω[′ʹ]|γρ[′ʹ]|ἄλλος|ἄλλως|ἄλλοι|ἕτερος).+(?:;\s*(?:α[′ʹ]|σ[′ʹ]|θ[′ʹ]|οἱ\s+[λγο][′ʹ]|ο̅|ὁ\s+ἑβρ[′ʹ]|τὸ\s+ἑβρ[′ʹ]|τὸ\s+σαμ[′ʹ]|ωρ[′ʹ]|ὁ\s+συρ[′ʹ]|τὸ\s+ἰουδ[′ʹ]|ιω[′ʹ]|γρ[′ʹ]|ἄλλος|ἄλλως|ἄλλοι|ἕτερος).+)*$",
    "3.2 Hexaplaric Apparatus Entry Content: BaseReadingInApparatus": PLACEHOLDER_REGEX,
    "3.3 Hexaplaric Apparatus Entry Content: HexaplaricVariantInApparatus": PLACEHOLDER_REGEX,
    "3.3.1 Hexaplaric Apparatus Entry Content: HexaplaricVariantInApparatus": PLACEHOLDER_REGEX,
    "4. ReadingInApparatusType: general rule": r"^\s*(?P<type>bis\s+scr|ter\s+scr|semel\s+scr|non\s+hab|sup\s+ras|ex\s+corr|sub\s+(?:metob|÷|※|⸔|~)|pr\s+(?:ras|spat|÷|※|metob|⸔|~)|(?:\+|addunt)\s+(?:ras|n\s+litt|spat|÷|※|metob|⸔|~)|addunt|delebit|delebunt|rescr|metob|absc|litt|spat|ras|del|om|tr|pr|>|◠|÷|※|⸔|~|\+)",
    "4.1 ReadingInApparatusType: omission": r"^\s*(?P<omission_type>semel\s+scr|non\s+hab|absc|om|>|◠)",
    "4.1.1 Omission: >": PLACEHOLDER_REGEX,
    "4.1.2 Omission: om": PLACEHOLDER_REGEX,
    "4.1.2.1 Multiple omissions with \"om\": consecutive occurrences": PLACEHOLDER_REGEX,
    "4.1.2.2 Multiple omissions with \"om\": \"et\"": PLACEHOLDER_REGEX,
    "4.1.3 Omission: ◠": PLACEHOLDER_REGEX,
    "4.1.4 Omission: absc": PLACEHOLDER_REGEX,
    "4.1.5 Omission: semel scr": PLACEHOLDER_REGEX,
    "4.1.5 Omission: non hab": PLACEHOLDER_REGEX,
    "4.2 ReadingInApparatusType: addition": PLACEHOLDER_REGEX,
    "4.2.1 Addition: \"+\"": r"^\s*\+\s+(?P<insertion>.+?)(?=\s+(?:(?<!°)\d|[A-Z]|𝔐)|$)",
    "4.2.2 Addtion: pr": PLACEHOLDER_REGEX,
    "4.2.3 Addition: bis scr / ter scr": PLACEHOLDER_REGEX,
    "4.2.4 Addition: addunt": PLACEHOLDER_REGEX,
    "4.3 ReadingInApparatusType: transposition": PLACEHOLDER_REGEX,
    "4.3.1Transposition: positive entry with \"/\"": PLACEHOLDER_REGEX,
    "4.3.2 Transposition: positive entry with \"ante\" and \"post\"": PLACEHOLDER_REGEX,
    "4.3.3 Transposition: positive entry with \"ad\" + init/fin": PLACEHOLDER_REGEX,
    "4.3.4 Transposition: negative entry with \"et\"": PLACEHOLDER_REGEX,
    "4.3.5 Transposition: negative entry with \"ante\" and \"post\"": PLACEHOLDER_REGEX,
    "4.3.6 Transposition: negative entry with \"ad\" + init/fin": PLACEHOLDER_REGEX,
    "4.3.7 Transposition: ordo commatum": PLACEHOLDER_REGEX,
    "4.4 ReadingInApparatusType: deletion": PLACEHOLDER_REGEX,
    "4.5 ReadingInApparatusType: correction": PLACEHOLDER_REGEX,
    "4.5.1 ReadingInApparatusType correction\n\nParticular patterns: multiple ReadingStrings": PLACEHOLDER_REGEX,
    "5. Critical Text Passage": r"^(?P<base_reading>[^\]]+)\]",
    "5.1.1 Critical Text Passage Type: Sigle Location": PLACEHOLDER_REGEX,
    "5.1.2 Critical Text Passage Type: Range Location": PLACEHOLDER_REGEX,
    "5.1.3 Critical Text Passage Type: Multiple Locations": PLACEHOLDER_REGEX,
    "5.3.1 Critical Text Passage Type: Multiple EndSelectors": PLACEHOLDER_REGEX,
    "5.3.2 Critical Text Passage Type: Multiple occurrences": PLACEHOLDER_REGEX,
    "5.2.1 Critical Text Passage with Positive Entry": PLACEHOLDER_REGEX,
    "5.2.2 Critical Text Passage with Negative Critical Apparatus Entry": PLACEHOLDER_REGEX,
    "5.3 Critical Text Passage and Passage Selector Overview": PLACEHOLDER_REGEX,
    "5.3.1 Passage Quote Selector": PLACEHOLDER_REGEX,
    "5.3.2 Passage Position Selector": PLACEHOLDER_REGEX,
    "5.3.2.1 Passage Position Selector Type: init": PLACEHOLDER_REGEX,
    "5.3.2.2 Passage Position Selector Type: fin": PLACEHOLDER_REGEX,
    "5.3.2.3 Passage Position Selector Type: comma": PLACEHOLDER_REGEX,
    "5.3.2.3.1 Passage Position Selector Type: commata": PLACEHOLDER_REGEX,
    "5.3.2.4 Passage Position Selector Type: chapter and verse n:n": PLACEHOLDER_REGEX,
    "5.3.2.4.1 Passage Position Selector Type: interpolated chapter and verse [n:n]": PLACEHOLDER_REGEX,
    "5.3.2.5 Passage Position Selector Type: verse (n)": PLACEHOLDER_REGEX,
    "5.3.2.5.1 Passage Position Selector Type: interpolated verse [n]": PLACEHOLDER_REGEX,
    "5.3.2.6 Passage Position Selector Type: occurrence n°": PLACEHOLDER_REGEX,
    "5.3.2.6.1 Passage Position Selector Type: occurrence \"ult\"": PLACEHOLDER_REGEX,
    "6. Witness Management": r"^(?P<content>.*?)\s+(?P<witnesses>(?:(?<!°)\d|[A-Z]|𝔐).*)$",
    "6.1 Witnesses_string: order": PLACEHOLDER_REGEX,
    "6.2 Witnesses_string: management": PLACEHOLDER_REGEX,
    "6.2.1 Witnesses_string management:\n\"-\" symbol": PLACEHOLDER_REGEX,
    "6.2.2 Management of Witness Groups": PLACEHOLDER_REGEX,
    "6.2.2.1 Groups \"La\" and Old Versions": PLACEHOLDER_REGEX,
    "6.2.2.2 Handling Groups: Symbol Exception “−” (U+2212 Minus Sign)": PLACEHOLDER_REGEX,
    "6.2.2.3 Handling Groups: Symbol Exception “−” (U+2212 Minus Sign) with OldVersions": PLACEHOLDER_REGEX,
    "6.2.2.4 Groups \"La\" and Old Versions: verss": PLACEHOLDER_REGEX,
    "6.2.3 Handling Author Citations": PLACEHOLDER_REGEX,
    "6.2.3 Handling Author Citations: Nested Examples": PLACEHOLDER_REGEX,
    "6.2.4  Handling Author Citations: passim": PLACEHOLDER_REGEX,
    "6.2.4 Handling NT Citations": PLACEHOLDER_REGEX,
    "6.2.5 Handling Other_Versions": PLACEHOLDER_REGEX,
    "6.2.6. Handling Other_Versions: printed editions group \"edd\"": PLACEHOLDER_REGEX,
    "7. Handling Notes": r"(?P<note>\([^\)]+\)|(?:\b|(?<=\w))(?:c\s+pr\s+m|omn\s+codd|cf\s+(?:infra|supra)|ex\s+(?:corr|par)|s\s+(?:ind|nom)|c\s+var|pr\s+m|sup\s+lin|txtetmg|Latcodd|Latcod|superscr|relict|mutil|txt[c*]|mg[c*]|codd|rell|plur|sing|comm|mss|txt|Lat|cat|lem|vid|inc|cod|pap|praef|ss|pl|ms|te|ap|c[12]|s|c|\*|\?|\|\?|\|\|))",
    "7.1 Handling Notes in ReadingString": PLACEHOLDER_REGEX,
    "7.1.1 Handling Notes in ReadingString: ...] / [...": PLACEHOLDER_REGEX,
    "7.1.2 Handling Notes in ReadingString: Exception for ν (U+03BD)": PLACEHOLDER_REGEX,
    "7.3 Handling Notes After the Colon": PLACEHOLDER_REGEX,
    "8. ReadingInApparatusCause": r"(?:(?::\s*)(?P<cause_explicit>haplogr|homoiar|homoiot|dittogr|absc))|(?P<cause_symbol>◠|absc)",
    "9. Cross-Reference to Apparatus 2 (↓ Indicator)": r"(?P<cross_ref>↓)",
}

# ------------------------------------------------------------------------
# Fine del blocco hardcoded
# ------------------------------------------------------------------------

APP1_DIR = Path("sources/apparatus-1")
APP2_DIR = Path("sources/apparatus-2")


def load_all_notes(folder: Path):
    """
    Legge tutti i .txt nella cartella e ritorna una lista contenente
    TUTTE le righe (annotazioni) dell'apparato critico.
    Ogni riga è una stringa indipendente.
    """
    notes = []

    if not folder.exists():
        return notes

    for p in sorted(folder.rglob("*.txt")):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            try:
                text = p.read_text(encoding="latin-1")
            except Exception:
                text = ""

        # Splitta per righe — ogni riga è un’annotazione indipendente
        for line in text.splitlines():
            line = line.strip()
            if line:
                notes.append(line)

    return notes


def compile_pattern(pat_str: str):
    """
    Compila la regex in modalità DOTALL e IGNORECASE.
    Ritorna None se non valida.
    """
    try:
        return re.compile(pat_str, flags=re.DOTALL | re.IGNORECASE)
    except re.error:
        return None


def compute_freq_for_dict(name_regex: dict, notes: list):
    """
    Calcola per ogni regola la percentuale di righe dell'apparato
    in cui è presente ALMENO un match della regex.
    """
    total_notes = len(notes)
    results = {}

    for name, pat in name_regex.items():
        if total_notes == 0:
            results[name] = 0.0
            continue

        compiled = compile_pattern(pat)
        if compiled is None:
            results[name] = 0.0
            continue

        matches = 0
        for line in notes:
            if compiled.search(line):
                matches += 1

        percent = (matches / total_notes) * 100
        results[name] = percent

    return results


def print_table(title: str, freq_map: dict):
    print(f"\nTabella di {title}:")
    print("Rank | Regola | Frequenza")
    sorted_items = sorted(freq_map.items(), key=lambda kv: kv[1], reverse=True)
    for idx, (name, pct) in enumerate(sorted_items, start=1):
        print(f"{idx} | {name} | {pct:.2f}%")


def main():
    print("Caricamento delle regole (hardcoded)...")
    n1 = len(NAME_REGEX_APP1)
    n2 = len(NAME_REGEX_APP2)
    print(f"Regole apparato 1: {n1}")
    print(f"Regole apparato 2: {n2}")

    print("Caricamento annotazioni degli apparati...")
    notes1 = load_all_notes(APP1_DIR)
    notes2 = load_all_notes(APP2_DIR)
    print(f"Annotazioni trovate in apparato 1: {len(notes1)}")
    print(f"Annotazioni trovate in apparato 2: {len(notes2)}")

    print("Calcolo frequenze...")
    freq1 = compute_freq_for_dict(NAME_REGEX_APP1, notes1)
    freq2 = compute_freq_for_dict(NAME_REGEX_APP2, notes2)

    print_table("apparato 1", freq1)
    print_table("apparato 2", freq2)


if __name__ == "__main__":
    main()

