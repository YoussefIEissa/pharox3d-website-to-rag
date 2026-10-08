import sys
import requests

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


QDRANT_PATH = "qdrant_db"
COLLECTION_NAME = "pharox3d"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL = "google/gemma-4-e4b"

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

TOP_K = 5


def retrieve(query, model, client):
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=TOP_K,
    ).points

    return results


def generate_answer(query, results):
    context_parts = []

    for i, result in enumerate(results, start=1):
        payload = result.payload

        context_parts.append(
            f"""SOURCE {i}
Title: {payload['title']}
Type: {payload['type']}
Content:
{payload['text']}
"""
        )

    context = "\n\n".join(context_parts)

    prompt = f"""You are a helpful customer support assistant for Pharox3D.

Answer the user's question using ONLY the information provided in the context.

If the answer is not contained in the context, say:
"I couldn't find that information in the Pharox3D knowledge base."

Do not invent prices, products, features, policies, or other information.

Context:
{context}

User question:
{query}

Answer:
"""

    response = requests.post(
        LM_STUDIO_URL,
        json={
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.2,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


def main():
    query = " ".join(sys.argv[1:])

    if not query:
        print('Usage: uv run python src/crawl4ai_test/rag.py "your question"')
        return

    print(f"\nQuestion: {query}")
    print("=" * 80)

    print("Loading embedding model...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    client = QdrantClient(path=QDRANT_PATH)

    print("Retrieving relevant documents...")
    results = retrieve(query, embedding_model, client)

    print(f"Retrieved {len(results)} chunks")

    print("Generating answer with Gemma...")
    answer = generate_answer(query, results)

    print("\nANSWER")
    print("=" * 80)
    print(answer)


if __name__ == "__main__":
    main()