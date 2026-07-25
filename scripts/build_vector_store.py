from pathlib import Path 
import re
import chromadb
from sentence_transformers import SentenceTransformer

SOURCE_DIR = Path("data/pages/clean")
DB_DIR = "chroma_db"
COLLECTION_NAME = "xeer_chunks"

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

MIN_PAR_LEN = 40
MAX_CHUNK_LEN = 900
MIN_CHUNK_LEN = 120

# Seuils de détection du bruit d'OCR, appliqués PARAGRAPHE PAR PARAGRAPHE.
# Filtrer après fusion faisait perdre des blocs entiers de contenu légitime dès
# qu'un seul fragment illisible s'y trouvait (38 % du livre était écarté).
ALPHA_RATIO_MIN = 0.45      # part minimale de lettres
SYMBOL_DENSITY_MAX = 0.04   # densité maximale de symboles parasites
SHORT_WORD_RATIO_MAX = 0.5  # part maximale de « mots » de 1-2 caractères

SYMBOL_RE = re.compile(r"[#@_=<>\\/\[\]\{\}\|]")


def clean_text(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_noisy_paragraph(text: str) -> bool:
    """Vrai si le paragraphe est du bruit d'OCR plutôt que du texte.

    Ne juge PAS la longueur au-delà du minimum de paragraphe : un titre de
    chapitre court est du contenu légitime, il sera fusionné avec la suite.
    """
    stripped = text.strip()
    if len(stripped) < MIN_PAR_LEN:
        return True

    if sum(c.isalpha() for c in stripped) / len(stripped) < ALPHA_RATIO_MIN:
        return True

    if len(SYMBOL_RE.findall(stripped)) / len(stripped) > SYMBOL_DENSITY_MAX:
        return True

    # Le charabia d'OCR se reconnaît surtout à une majorité de lettres isolées
    # (« i” i if 4 ' II E I ] iq i! ») : du somali réel a des mots normaux.
    words = stripped.split()
    if words and sum(1 for w in words if len(w) <= 2) / len(words) > SHORT_WORD_RATIO_MAX:
        return True

    return False


def is_noisy(text: str) -> bool:
    """Contrôle final d'un bloc déjà constitué : longueur utile suffisante."""
    return len(text.strip()) < MIN_CHUNK_LEN


def split_paragraphs(text: str):
    """Découpe en paragraphes et écarte immédiatement ceux qui sont du bruit."""
    text = clean_text(text)
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if not is_noisy_paragraph(p)]


def merge_paragraphs(paragraphs, max_len=MAX_CHUNK_LEN):
    chunks = []
    current = ""

    for para in paragraphs:
        if not current:
            current = para
        elif len(current) + 2 + len(para) <= max_len:
            current += "\n\n" + para
        else:
            chunks.append(current.strip())
            current = para

    if current.strip():
        chunks.append(current.strip())

    return chunks


def load_chunks():
    documents = []
    metadatas = []
    ids = []

    page_files = sorted(SOURCE_DIR.glob("page_*.txt"))
    if not page_files:
        raise FileNotFoundError(f"Aucune page trouvée dans : {SOURCE_DIR}")

    total_chunks = 0
    skipped_chunks = 0

    for page_file in page_files:
        text = page_file.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue

        page_num = page_file.stem.split("_")[-1]
        paragraphs = split_paragraphs(text)
        chunks = merge_paragraphs(paragraphs)

        kept = 0
        for idx, chunk in enumerate(chunks, start=1):
            if is_noisy(chunk):
                skipped_chunks += 1
                continue

            # préfixe léger de contexte
            doc_text = f"Bogga {page_num} - Xeer Ciise\n{chunk}"

            chunk_id = f"so_page_{page_num}_chunk_{idx:03}"
            documents.append(doc_text)
            metadatas.append({
                "lang": "so",
                "page": page_num,
                "chunk_index": idx,
                "source_file": page_file.name,
            })
            ids.append(chunk_id)
            kept += 1

        total_chunks += kept
        print(f"Page {page_num}: {kept} chunks gardés")

    print(f"\nTotal chunks gardés : {total_chunks}")
    print(f"Chunks ignorés (bruit) : {skipped_chunks}")
    return documents, metadatas, ids


def main():
    print("Chargement du modèle d'embeddings...")
    model = SentenceTransformer(MODEL_NAME)

    print("Préparation des chunks...")
    documents, metadatas, ids = load_chunks()

    if not documents:
        raise ValueError("Aucun chunk trouvé à indexer.")

    print("\nCréation des embeddings...")
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    print("Connexion à ChromaDB...")
    client = chromadb.PersistentClient(path=DB_DIR)

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(name=COLLECTION_NAME)
    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    print("\n✅ Indexation terminée")
    print(f"Collection : {COLLECTION_NAME}")
    print(f"Documents indexés : {len(documents)}")


if __name__ == "__main__":
    main()