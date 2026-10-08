import json
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


INPUT_FILE = Path("chunks/embedded_chunks.json")
QDRANT_PATH = Path("qdrant_db")
COLLECTION_NAME = "pharox3d"

VECTOR_SIZE = 384


def main():
    print("Loading embedded chunks...")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"Loaded {len(chunks)} chunks")

    print("Starting Qdrant...")
    client = QdrantClient(path=str(QDRANT_PATH))

    print(f"Creating collection: {COLLECTION_NAME}")

    if client.collection_exists(COLLECTION_NAME):
        print("Collection already exists. Recreating it...")
        client.delete_collection(COLLECTION_NAME)

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    points = []

    for chunk in chunks:
        points.append(
            PointStruct(
                id=chunk["chunk_id"],
                vector=chunk["embedding"],
                payload={
                    "text": chunk["text"],
                    "title": chunk["title"],
                    "type": chunk["type"],
                    "source": chunk["source"],
                    "filename": chunk["filename"],
                    "chunk_id": chunk["chunk_id"],
                },
            )
        )

    print(f"Uploading {len(points)} vectors...")

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    collection_info = client.get_collection(COLLECTION_NAME)

    print()
    print("🎉 Qdrant setup complete!")
    print(f"📦 Collection: {COLLECTION_NAME}")
    print(f"📄 Vectors: {collection_info.points_count}")
    print(f"📐 Vector size: {VECTOR_SIZE}")
    print(f"📏 Distance: COSINE")
    print(f"💾 Database: {QDRANT_PATH}")


if __name__ == "__main__":
    main()