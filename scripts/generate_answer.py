import sys
import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION_NAME = "xeer_chunks"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def search_xeer(query, n_results=5):
    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query]).tolist()[0]

    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    return results["documents"][0]


def generate_answer(query, docs):
    context = "\n\n".join(docs)

    prompt = f"""
Su'aal: {query}

Macluumaadka:
{context}

Fadlan ka jawaab su'aasha si cad oo kooban.
"""

    return prompt


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_answer.py 'question'")
        return

    query = " ".join(sys.argv[1:])

    docs = search_xeer(query)

    answer = generate_answer(query, docs)

    print("\n===== JAWAAB =====\n")
    print(answer)


if __name__ == "__main__":
    main()