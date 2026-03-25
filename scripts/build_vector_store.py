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


def clean_text(text: str) -> str:
    text = text.replace("\x0c", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_noisy(text: str) -> bool:
    if len(text.strip()) < MIN_CHUNK_LEN:
        return True

    letters = sum(c.isalpha() for c in text)
    total = len(text)
    if total == 0:
        return True

    alpha_ratio = letters / total
    if alpha_ratio < 0.45:
        return True

    weird = len(re.findall(r"[#@_=<>\\/\[\]\{\}\|]", text))
    if weird > 8:
        return True

    return False


def split_paragraphs(text: str):
    text = clean_text(text)
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if len(p.strip()) >= MIN_PAR_LEN]


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