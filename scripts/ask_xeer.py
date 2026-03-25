import sys
import chromadb
from sentence_transformers import SentenceTransformer

DB_DIR = "chroma_db"
COLLECTION_NAME = "xeer_chunks"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def is_bad_result(text: str) -> bool:
    text = text.lower()

    # trop court
    if len(text) < 120:
        return True

    # trop de chiffres ou listes
    digits = sum(c.isdigit() for c in text)
    if digits > 20:
        return True

    # trop de noms (liste)
    if text.count(")") > 10:
        return True

    # mots inutiles
    bad_words = ["daabacaad", "xuquuqda", "isbn", "tifaftirka"]
    if any(word in text for word in bad_words):
        return True

    return False


def keyword_score(query: str, text: str) -> int:
    score = 0
    query_words = query.lower().split()

    for word in query_words:
        if word in text.lower():
            score += 1

    return score


def search_xeer(query: str, n_results: int = 12):
    model = SentenceTransformer(MODEL_NAME)
    query_embedding = model.encode([query]).tolist()[0]

    client = chromadb.PersistentClient(path=DB_DIR)
    collection = client.get_collection(COLLECTION_NAME)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    final_results = []

    for doc, meta, dist, doc_id in zip(docs, metas, distances, ids):
        if is_bad_result(doc):
            continue

        score = keyword_score(query, doc)

        final_results.append({
            "doc": doc,
            "meta": meta,
            "dist": dist,
            "id": doc_id,
            "score": score
        })

    # tri intelligent
    final_results = sorted(
        final_results,
        key=lambda x: (x["dist"], -x["score"])
    )

    return final_results[:5]


def main():
    if len(sys.argv) < 2:
        print('Usage: python scripts/ask_xeer.py "ta question ici"')
        return

    query = " ".join(sys.argv[1:])
    results = search_xeer(query)

    print(f"\nQuestion : {query}\n")
    print("Top résultats intelligents :\n")

    if not results:
        print("Aucun bon résultat trouvé.")
        return

    for i, r in enumerate(results, start=1):
        print(f"--- Résultat {i} ---")
        print(f"ID       : {r['id']}")
        print(f"Page     : {r['meta'].get('page')}")
        print(f"Score    : {r['score']}")
        print(f"Distance : {r['dist']}")
        print("Contenu  :")
        print(r["doc"])
        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()