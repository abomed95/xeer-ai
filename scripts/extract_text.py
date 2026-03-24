from pathlib import Path 
import fitz
import pytesseract
from PIL import Image
import io

PDF_PATH = Path("data/raw/Xeer dhaqameed xeer ciise.pdf")
OUTPUT_PATH = Path("data/processed/xeer_ciise_raw.txt")

# À adapter selon ton PC Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_pdf_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    pages_text = []

    for i in range(len(doc)):
        page = doc[i]
        pix = page.get_pixmap(dpi=250)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img)
        pages_text.append(f"\n\n===== PAGE {i + 1} =====\n{text}")
        print(f"Page {i + 1}/{len(doc)} terminée")

    return "".join(pages_text)


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF introuvable : {PDF_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    text = extract_pdf_text(PDF_PATH)
    OUTPUT_PATH.write_text(text, encoding="utf-8")
    print(f"Texte brut sauvegardé dans : {OUTPUT_PATH}")


if __name__ == "__main__":
    main()