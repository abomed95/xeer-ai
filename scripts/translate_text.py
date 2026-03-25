from pathlib import Path 
from deep_translator import GoogleTranslator
import time
import re

# === CONFIG ===
CLEAN_PAGES_DIR = Path("data/pages/clean")
FR_PAGES_DIR = Path("data/pages/fr")
EN_PAGES_DIR = Path("data/pages/en")

OUTPUT_FR = Path("data/processed/xeer_ciise_fr.txt")
OUTPUT_EN = Path("data/processed/xeer_ciise_en.txt")

MAX_CHUNK_SIZE = 1800


# === NORMALISATION AVANT TRADUCTION ===
def normalize_text(text: str) -> str:
    replacements = {
        "Ciisaha": "Ciise",
        "ciisaha": "Ciise",
        "Ciise": "Ciise",
        "ciise": "Ciise",
        "Xeerka": "Xeer",
        "xeerka": "xeer",
        "Xeer": "Xeer",
        "xeer": "xeer",
    }

    for key, value in replacements.items():
        text = text.replace(key, value)

    return text


# === CORRECTION APRÈS TRADUCTION ===
def post_process_translation(text: str, target_lang: str) -> str:
    if target_lang == "fr":
        replacements = {
            "Jésus": "Ciise",
            "Jesus": "Ciise",
            "Code-Jésus": "Xeer Ciise",
            "Lois de Jésus": "Xeer Ciise",
            "droit coutumier Jésus": "Xeer Ciise",
            "Jésus (clan)": "Ciise (clan)",
            "Une partie de Jésus": "Une partie du clan Ciise",
            "Droit coutumier - Jésus": "Droit coutumier - Ciise",
            "Droit coutumier - Ciise Ciise": "Droit coutumier - Ciise",
            "Xeer (droit coutumier) - Jésus": "Xeer Ciise",
            "Xeer (droit coutumier) - Clise": "Xeer Ciise",
            "Xeer (droit coutumier)": "Droit coutumier",
            "xeer (customary law)": "droit coutumier",
            "Xeer": "Droit coutumier",
            "Citse": "Ciise",
            "Clise": "Ciise",
        }
    else:
        replacements = {
            "Jesus": "Ciise",
            "Law of Jesus": "Xeer Ciise",
            "Customary law of Jesus": "Xeer Ciise",
            "Jesus (clan)": "Ciise (clan)",
            "Xeer (customary law)": "Customary law",
            "xeer (customary law)": "customary law",
            "Citse": "Ciise",
            "Clise": "Ciise",
        }

    for key, value in replacements.items():
        text = text.replace(key, value)

    return text


# === NETTOYAGE DES RÉPÉTITIONS ===
def clean_repetitions(text: str) -> str:
    text = re.sub(r'Ciise\s*\(clan\)(\s*\(clan\))+', 'Ciise (clan)', text)
    text = re.sub(r'\(clan\)(\s*\(clan\))+', '(clan)', text)
    text = re.sub(r'\(droit coutumier\)(\s*\(droit coutumier\))+', '(droit coutumier)', text)
    text = re.sub(r'\(customary law\)(\s*\(customary law\))+', '(customary law)', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()


# === DÉCOUPAGE DU TEXTE ===
def split_text(text: str, max_len: int = MAX_CHUNK_SIZE):
    chunks = []
    start = 0

    while start < len(text):
        chunks.append(text[start:start + max_len])
        start += max_len

    return chunks


# === TRADUCTION D'UNE PAGE ===
def translate_text(text: str, target_lang: str) -> str:
    if not text.strip():
        return ""

    text = normalize_text(text)
    translator = GoogleTranslator(source="so", target=target_lang)
    chunks = split_text(text)

    translated_chunks = []

    for i, chunk in enumerate(chunks, start=1):
        try:
            translated = translator.translate(chunk)
            translated = translated if translated else ""
            translated = post_process_translation(translated, target_lang)
            translated = clean_repetitions(translated)

            translated_chunks.append(translated)

            print(f"{target_lang.upper()} chunk {i}/{len(chunks)} OK")
            time.sleep(1)

        except Exception as e:
            print(f"Erreur chunk {i} ({target_lang}) : {e}")
            translated_chunks.append(f"[ERREUR {target_lang} CHUNK {i}]")

    return "\n".join(translated_chunks)


# === RECONSTRUCTION DU FICHIER GLOBAL ===
def build_combined_file(source_dir: Path, output_file: Path):
    all_pages = []

    for page_file in sorted(source_dir.glob("page_*.txt")):
        page_num = page_file.stem.split("_")[-1]
        content = page_file.read_text(encoding="utf-8", errors="ignore").strip()
        all_pages.append(f"===== PAGE {page_num} =====\n{content}\n")

    output_file.write_text("\n".join(all_pages), encoding="utf-8")


# === MAIN ===
def main():
    if not CLEAN_PAGES_DIR.exists():
        raise FileNotFoundError(f"Dossier introuvable : {CLEAN_PAGES_DIR}")

    FR_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    EN_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_FR.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_EN.parent.mkdir(parents=True, exist_ok=True)

    pages = sorted(CLEAN_PAGES_DIR.glob("page_*.txt"))

    if not pages:
        raise FileNotFoundError(f"Aucune page trouvée dans : {CLEAN_PAGES_DIR}")

    print(f"{len(pages)} pages à traduire...\n")

    for i, page_file in enumerate(pages, start=1):
        print(f"Page {i}/{len(pages)} : {page_file.name}")

        text = page_file.read_text(encoding="utf-8", errors="ignore")

        fr_text = translate_text(text, "fr")
        (FR_PAGES_DIR / page_file.name).write_text(fr_text, encoding="utf-8")

        en_text = translate_text(text, "en")
        (EN_PAGES_DIR / page_file.name).write_text(en_text, encoding="utf-8")

    build_combined_file(FR_PAGES_DIR, OUTPUT_FR)
    build_combined_file(EN_PAGES_DIR, OUTPUT_EN)

    print("\nTraduction terminée")
    print(f"FR : {OUTPUT_FR}")
    print(f"EN : {OUTPUT_EN}")


if __name__ == "__main__":
    main() 