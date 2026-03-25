from pathlib import Path 
import io
import fitz
import pytesseract
from PIL import Image, ImageOps, ImageFilter

PDF_PATH = Path("data/raw/Xeer dhaqameed xeer ciise.pdf")
OUTPUT_RAW_TEXT = Path("data/processed/xeer_ciise_raw.txt")
OUTPUT_PAGES_DIR = Path("data/pages/raw")

# Mets ici le bon chemin Tesseract sur ton PC
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def preprocess_image(img: Image.Image) -> Image.Image:
    # niveaux de gris
    img = img.convert("L")

    # améliore le contraste
    img = ImageOps.autocontrast(img)

    # légère netteté
    img = img.filter(ImageFilter.SHARPEN)

    # seuillage simple noir/blanc
    img = img.point(lambda x: 0 if x < 180 else 255, mode="1")

    return img


def ocr_page(page) -> str:
    pix = page.get_pixmap(dpi=300)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img = preprocess_image(img)

    text = pytesseract.image_to_string(
        img,
        lang="eng",
        config="--oem 3 --psm 6"
    )
    return text


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF introuvable : {PDF_PATH}")

    OUTPUT_RAW_TEXT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PAGES_DIR.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(PDF_PATH)
    all_pages = []

    for i, page in enumerate(doc, start=1):
        text = ocr_page(page).strip()

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