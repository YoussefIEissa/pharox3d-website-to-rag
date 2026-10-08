import json
from pathlib import Path

from sentence_transformers import SentenceTransformer


INPUT_FILE = Path("chunks/chunks.json")
OUTPUT_FILE = Path("chunks/embedded_chunks.json")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def main():
    print(f"Loading embedding model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Loading chunks...")
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks")

    texts = [chunk["text"] for chunk in chunks]

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    embedded_chunks = []

    for chunk, embedding in zip(chunks, embeddings):
        embedded_chunks.append(
            {
                **chunk,
                "embedding": embedding.tolist(),
            }
        )

    print(f"Saving embeddings to: {OUTPUT_FILE}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(embedded_chunks, f, ensure_ascii=False)

    print()
    print("🎉 Embedding complete!")
    print(f"📄 Chunks: {len(embedded_chunks)}")
    print(f"📐 Vector dimensions: {len(embedded_chunks[0]['embedding'])}")
    print(f"💾 Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()