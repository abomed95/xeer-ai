from pathlib import Path 
import re

INPUT_PATH = Path("data/processed/xeer_ciise_raw.txt")
OUTPUT_PATH = Path("data/processed/xeer_ciise_clean.txt")


def clean_text(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" ?===== PAGE (\d+) ===== ?", r"\n\n===== PAGE \1 =====\n", text)
    text = re.sub(r" +\n", "\n", text)
    return text.strip()


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {INPUT_PATH}")

    raw_text = INPUT_PATH.read_text(encoding="utf-8")
    cleaned = clean_text(raw_text)

    OUTPUT_PATH.write_text(cleaned, encoding="utf-8")
    print(f"Texte nettoyé sauvegardé dans : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()