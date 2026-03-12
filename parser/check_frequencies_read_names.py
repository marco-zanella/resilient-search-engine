import csv
import os
from pathlib import Path
from collections import defaultdict

APP1_CSV = "sources/WP8_Parser_Dictionary_-_App1.csv"
APP2_CSV = "sources/WP8_Parser_Dictionary_-_App2.csv"

APP1_DIR = "sources/apparatus-1"
APP2_DIR = "sources/apparatus-2"


def load_rule_names(csv_path: str) -> list[str]:
    """
    Carica i nomi delle regole dalla colonna 'Name',
    ignorando la prima e la seconda riga (header + descrizione).
    """
    names = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # DictReader già salta l'header, quindi dobbiamo saltare manualmente la seconda riga
        next(reader, None)  # Skip second descriptive row
        for row in reader:
            if row["Name"].strip():
                names.append(row["Name"].strip())
    return names


def load_apparatus_texts(folder: str) -> list[str]:
    """
    Legge tutti i file TXT in una cartella e sottocartelle.
    Ritorna la lista dei testi completi.
    """
    texts = []
    for path in Path(folder).rglob("*.txt"):
        with open(path, "r", encoding="utf-8") as f:
            texts.append(f.read())
    return texts


def compute_frequencies(rule_names: list[str], texts: list[str]) -> dict:
    """
    Placeholder: ritorna frequenze = 0 per ogni regola.
    Qui in futuro inseriremo le regex vere per riconoscere le regole negli apparati.
    """
    frequencies = defaultdict(float)

    # Placeholder per il futuro parsing
    for rule in rule_names:
        frequencies[rule] = 0.0

    return frequencies


def print_frequency_table(title: str, frequencies: dict):
    """
    Stampa una tabella ordinata per frequenza in ordine decrescente.
    """
    print(f"\nTabella di {title}:")
    print("Rank | Regola | Frequenza")

    sorted_items = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)

    for idx, (rule, freq) in enumerate(sorted_items, start=1):
        print(f"{idx} | {rule} | {freq:.2f}%")


def main():
    print("Caricamento delle regole...")

    rules_app1 = load_rule_names(APP1_CSV)
    rules_app2 = load_rule_names(APP2_CSV)

    print(f"Regole apparato 1: {len(rules_app1)}")
    print(f"Regole apparato 2: {len(rules_app2)}")

    print("Caricamento testi degli apparati...")
    texts_app1 = load_apparatus_texts(APP1_DIR)
    texts_app2 = load_apparatus_texts(APP2_DIR)

    print("Calcolo frequenze (placeholder)...")
    freq_app1 = compute_frequencies(rules_app1, texts_app1)
    freq_app2 = compute_frequencies(rules_app2, texts_app2)

    print_frequency_table("apparato 1", freq_app1)
    print_frequency_table("apparato 2", freq_app2)


if __name__ == "__main__":
    main()
