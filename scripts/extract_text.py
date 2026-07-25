"""Moteur ROC (OCR) : extrait le texte du PDF Xeer Ciise page par page.

Multiplateforme (Windows / Linux / macOS) — nécessaire pour un pipeline
reproductible en local comme sur DigitalOcean. Configurable via variables
d'environnement :

  PDF_PATH      chemin du PDF source
  OCR_OUTPUT    fichier texte brut global
  OCR_PAGES_DIR dossier des pages extraites
  OCR_LANG      langues Tesseract (défaut : "eng+ara+som", repli auto sur "eng")
  TESSERACT_CMD chemin explicite vers le binaire tesseract (facultatif)
"""
import io
import os
import shutil
import sys
from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageFilter, ImageOps

PDF_PATH = Path(os.getenv("PDF_PATH", "data/raw/Xeer dhaqameed xeer ciise.pdf"))
OUTPUT_RAW_TEXT = Path(os.getenv("OCR_OUTPUT", "data/processed/xeer_ciise_raw.txt"))
OUTPUT_PAGES_DIR = Path(os.getenv("OCR_PAGES_DIR", "data/pages/raw"))
OCR_LANG = os.getenv("OCR_LANG", "eng+ara+som")


def configure_tesseract() -> None:
    """Localise le binaire tesseract, quel que soit le système d'exploitation."""
    # 1) Chemin explicite fourni par l'utilisateur
    explicit = os.getenv("TESSERACT_CMD")
    if explicit and Path(explicit).exists():
        pytesseract.pytesseract.tesseract_cmd = explicit
        return

    # 2) Binaire présent dans le PATH (cas normal sous Linux / DigitalOcean / macOS)
    found = shutil.which("tesseract")
    if found:
        pytesseract.pytesseract.tesseract_cmd = found
        return

    # 3) Emplacement Windows par défaut
    win_default = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if Path(win_default).exists():
        pytesseract.pytesseract.tesseract_cmd = win_default
        return

    raise RuntimeError(
        "Tesseract introuvable. Installe-le puis réessaie :\n"
        "  • Debian/Ubuntu (DigitalOcean) : "
        "sudo apt-get install -y tesseract-ocr tesseract-ocr-ara\n"
        "  • macOS : brew install tesseract\n"
        "  • Windows : https://github.com/UB-Mannheim/tesseract/wiki\n"
        "Ou définis TESSERACT_CMD vers le binaire."
    )


def resolve_lang(requested: str) -> str:
    """Garde uniquement les langues réellement installées, repli sur 'eng'."""
    try:
        available = set(pytesseract.get_languages(config=""))
    except Exception:
        return requested  # laisse Tesseract signaler lui-même une langue absente

    wanted = [code for code in requested.split("+") if code]
    usable = [code for code in wanted if code in available]
    if not usable:
        if "eng" in available:
            print(
                f"[OCR] Aucune des langues '{requested}' n'est installée — "
                "repli sur 'eng'.",
                file=sys.stderr,
            )
            return "eng"
        raise RuntimeError(
            f"Aucune donnée de langue Tesseract disponible pour '{requested}'. "
            "Installe p.ex. tesseract-ocr-ara / tesseract-ocr-som."
        )
    if len(usable) != len(wanted):
        missing = sorted(set(wanted) - set(usable))
        print(f"[OCR] Langues absentes ignorées : {'+'.join(missing)}", file=sys.stderr)
    return "+".join(usable)


def preprocess_image(img: Image.Image) -> Image.Image:
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)
    img = img.point(lambda x: 0 if x < 180 else 255, mode="1")
    return img


def ocr_page(page, lang: str) -> str:
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img = preprocess_image(img)
    return pytesseract.image_to_string(img, lang=lang, config="--oem 3 --psm 6")


def main():
    configure_tesseract()
    lang = resolve_lang(OCR_LANG)
    print(f"[OCR] Binaire : {pytesseract.pytesseract.tesseract_cmd}")
    print(f"[OCR] Langues : {lang}")

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF introuvable : {PDF_PATH}")

    OUTPUT_RAW_TEXT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF_PATH)
    all_pages = []

    for i, page in enumerate(doc, start=1):
        text = ocr_page(page, lang).strip()

        page_marker = f"===== PAGE {i} ====="
        all_pages.append(f"{page_marker}\n{text}\n")

        page_file = OUTPUT_PAGES_DIR / f"page_{i:03}.txt"
        page_file.write_text(text, encoding="utf-8")

        print(f"Page {i}/{len(doc)} extraite")

    OUTPUT_RAW_TEXT.write_text("\n".join(all_pages), encoding="utf-8")
    print(f"\nTexte brut global sauvegardé dans : {OUTPUT_RAW_TEXT}")
    print(f"Pages brutes sauvegardées dans : {OUTPUT_PAGES_DIR}")


if __name__ == "__main__":
    main()
