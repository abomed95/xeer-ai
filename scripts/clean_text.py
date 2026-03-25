from pathlib import Path 
import re

RAW_TEXT_PATH = Path("data/processed/xeer_ciise_raw.txt")
CLEAN_TEXT_PATH = Path("data/processed/xeer_ciise_clean.txt")

RAW_PAGES_DIR = Path("data/pages/raw")
CLEAN_PAGES_DIR = Path("data/pages/clean")


def clean_text(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = text.replace("|", "I")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" ?===== PAGE (\d+) ===== ?", r"\n\n===== PAGE \1 =====\n", text)
    text = re.sub(r" +\n", "\n", text)
    return text.strip()


def main():
    if not RAW_TEXT_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {RAW_TEXT_PATH}")

    CLEAN_TEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLEAN_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    raw_text = RAW_TEXT_PATH.read_text(encoding="utf-8", errors="ignore")
    clean_global = clean_text(raw_text)
    CLEAN_TEXT_PATH.write_text(clean_global, encoding="utf-8")

    for page_file in sorted(RAW_PAGES_DIR.glob("page_*.txt")):
        page_text = page_file.read_text(encoding="utf-8", errors="ignore")
        cleaned = clean_text(page_text)
        out_file = CLEAN_PAGES_DIR / page_file.name
        out_file.write_text(cleaned, encoding="utf-8")

    print(f"Texte nettoyé global : {CLEAN_TEXT_PATH}")
    print(f"Pages nettoyées : {CLEAN_PAGES_DIR}")


if __name__ == "__main__":
    main()