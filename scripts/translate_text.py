from pathlib import Path 
from deep_translator import GoogleTranslator
import time

INPUT_PATH = Path("data/processed/xeer_ciise_clean.txt")
OUTPUT_FR = Path("data/processed/xeer_ciise_fr.txt")
OUTPUT_EN = Path("data/processed/xeer_ciise_en.txt")

CHUNK_SIZE = 2000


def split_text(text: str, chunk_size: int = 2000):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size])
        start += chunk_size
    return chunks


def translate_chunks(chunks, target_lang: str):
    translator = GoogleTranslator(source="auto", target=target_lang)
    translated_chunks = []

    for i, chunk in enumerate(chunks, start=1):
        try:
            translated = translator.translate(chunk)
            translated_chunks.append(translated if translated else "")
            print(f"{target_lang} : chunk {i}/{len(chunks)} traduit")
            time.sleep(1)
        except Exception as e:
            print(f"Erreur chunk {i} ({target_lang}) : {e}")
            translated_chunks.append(f"\n[ERREUR TRADUCTION CHUNK {i}]\n")

    return "\n\n".join(translated_chunks)


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Fichier introuvable : {INPUT_PATH}")

    text = INPUT_PATH.read_text(encoding="utf-8")
    chunks = split_text(text, CHUNK_SIZE)

    print("Traduction FR...")
    text_fr = translate_chunks(chunks, "fr")
    OUTPUT_FR.write_text(text_fr, encoding="utf-8")

    print("Traduction EN...")
    text_en = translate_chunks(chunks, "en")
    OUTPUT_EN.write_text(text_en, encoding="utf-8")

    print("Terminé.")


if __name__ == "__main__":
    main()