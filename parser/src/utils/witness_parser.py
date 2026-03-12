"""
Witness Parser Utilities

Helper functions to intelligently separate variant text from witnesses.
"""

import re
from typing import Tuple, List


def looks_like_witness(token: str) -> bool:
    """
    Determine if a token looks like a witness abbreviation.

    Witness patterns:
    - Pure numbers: 664, 72, 130
    - Numbers with suffixes: 46s, 76′, 121txt, 664*
    - Capital letters: A, B, M, L
    - Abbreviated names: Hipp, Phil, Chr, Eus, Arm, Bo, La, etc.
    - Ranges: 72-135, 46-76
    - Groups: lI, cII, d, s, t, etc.
    """
    # Empty or single character greek lowercase - likely part of text
    if not token or (len(token) == 1 and token.islower() and ord(token) > 127):
        return False

    # Pure number
    if re.match(r'^\d+$', token):
        return True

    # Number with suffix/prefix
    if re.match(r'^[\d\-′*]+[a-z]*$', token):
        return True

    # Number range
    if re.match(r'^\d+[-–]\d+', token):
        return True

    # Single capital letter (manuscript sigla)
    if len(token) == 1 and token.isupper():
        return True

    # Known manuscript/witness abbreviations (shortened list)
    known_witnesses = {
        'A', 'B', 'D', 'F', 'G', 'L', 'M', 'S', 'V', 'O', 'W',
        'Arm', 'Arab', 'Aeth', 'Bo', 'La', 'Syh', 'Sa', 'Co', 'Pal',
        'Hipp', 'Phil', 'Chr', 'Eus', 'Tht', 'Cyr', 'Or', 'Bas',
        'Iust', 'Clem', 'Adam', 'Procop', 'Epiph', 'Ambr', 'Aug',
        'Hi', 'Vulg', 'Compl', 'Ald', 'Sixt', 'Ra', 'Spec',
        'Field', 'Rahlfs', 'Ios', 'Sev', 'Genn', 'Nil', 'Ath',
        'Didymus', 'GregNys', 'Mac', 'Meth', 'Tert', 'Iren',
        'LaA', 'LaC', 'LaE', 'Bs', 'Ac', 'Fa', 'Fb', 'Fc',
        'AethP', 'AethCR', 'AethM', 'BoK', 'BoL'
    }

    # Check if it's a known witness
    if token in known_witnesses:
        return True

    # Starts with known witness prefix
    for witness in known_witnesses:
        if token.startswith(witness):
            return True

    # Lowercase group sigla
    if token in ['lI', 'lII', 'cII', 'd', 's', 't', 'b', 'f', 'n', 'y', 'z']:
        return True

    # Has manuscript-like structure with apostrophes/diacritics
    if re.match(r"^[\d]+[′'*]+", token):
        return True

    return False


def split_variant_and_witnesses(content: str) -> Tuple[str, List[str]]:
    """
    Intelligently split variant text from witnesses.

    Args:
        content: The content after '] +' or ']' (without the +)

    Returns:
        (variant_text, witnesses_list)

    Example:
        "+ ο ην υπερανω του στερεωματος Hipp II 228"
        -> ("ο ην υπερανω του στερεωματος", ["Hipp", "II", "228"])
    """
    tokens = content.split()

    if not tokens:
        return ("", [])

    # Find the first token that looks like a witness
    witness_start_idx = None
    for i, token in enumerate(tokens):
        if looks_like_witness(token):
            witness_start_idx = i
            break

    if witness_start_idx is None:
        # No clear witness found - assume entire thing is variant
        return (content, [])

    # Split at the witness boundary
    variant_tokens = tokens[:witness_start_idx]
    witness_tokens = tokens[witness_start_idx:]

    variant_text = ' '.join(variant_tokens)

    return (variant_text, witness_tokens)


def main():
    """Test the witness parser"""
    test_cases = [
        "+ ο ην υπερανω του στερεωματος Hipp II 228",
        "+ ην 569 246 75 730 Phil I 10.5",
        "+ και 75 508",
        "επλασεν 664",
        "εκτισεν Ios I 27 ↓",
        "του 125",
    ]

    print("Testing witness parser:\n")
    for test in test_cases:
        # Remove leading + if present
        content = test.strip()
        if content.startswith('+'):
            content = content[1:].strip()

        variant, witnesses = split_variant_and_witnesses(content)
        print(f"Input:     {test}")
        print(f"Variant:   '{variant}'")
        print(f"Witnesses: {witnesses}")
        print()


if __name__ == "__main__":
    main()
