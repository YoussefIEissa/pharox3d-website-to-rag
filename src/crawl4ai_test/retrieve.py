import sys

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


QDRANT_PATH = "qdrant_db"
COLLECTION_NAME = "pharox3d"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    query = " ".join(sys.argv[1:])

    if not query:
        print("Usage: uv run python retrieve.py \"your question\"")
        return

    print(f"Query: {query}")
    print()

    model = SentenceTransformer(MODEL_NAME)

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    client = QdrantClient(path=QDRANT_PATH)

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=5,
    ).points

    print("Top results:")
    print("=" * 80)

    for i, result in enumerate(results, start=1):
        payload = result.payload

        print(f"\nRESULT {i}")
        print(f"Score: {result.score:.4f}")
        print(f"Title: {payload['title']}")
        print(f"Type: {payload['type']}")
        print(f"File: {payload['filename']}")
        print("-" * 80)
        print(payload["text"])


if __name__ == "__main__":
    main()