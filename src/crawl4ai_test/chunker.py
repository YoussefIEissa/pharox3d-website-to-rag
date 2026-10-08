from pathlib import Path
import json
import re


# ============================================================
# PATHS
# ============================================================

INPUT_DIR = Path.cwd() / "cleaned"
OUTPUT_DIR = Path.cwd() / "chunks"

CHUNKS_FILE = OUTPUT_DIR / "chunks.json"


# ============================================================
# CHUNK SETTINGS
# ============================================================

# Approximate maximum characters per chunk.
# We use characters for now because this keeps the implementation
# simple and easy to understand.
CHUNK_SIZE = 1200

# Number of characters to overlap between neighboring chunks.
CHUNK_OVERLAP = 200


# ============================================================
# DOCUMENT TYPE
# ============================================================

def get_document_type(filename: str) -> str:
    """Determine document type from the Crawl4AI filename."""

    if "_agents_md" in filename:
        return "agent_infrastructure"

    if "_products_" in filename:
        return "product"

    if "_collections_" in filename:
        return "collection"

    if "_pages_" in filename:
        return "page"

    if "_blogs_" in filename:
        return "blog"

    if "_policies_" in filename:
        return "policy"

    return "other"


# ============================================================
# TITLE
# ============================================================

def extract_title(text: str, filename: str) -> str:
    """Extract the first Markdown H1."""

    for line in text.splitlines():
        line = line.strip()

        if line.startswith("# "):
            return line[2:].strip()

    # Fallback
    name = filename.replace(".md", "")
    name = re.sub(r"^\d+_", "", name)

    return (
        name
        .replace("_", " ")
        .replace("-", " ")
        .strip()
    )


# ============================================================
# TEXT CLEANUP
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize whitespace without destroying Markdown structure."""

    # Normalize spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ============================================================
# SECTION SPLITTING
# ============================================================

def split_into_sections(text: str) -> list[str]:
    """
    Split a document around Markdown headings.

    Example:

        # Product

        description

        ## Features

        feature 1
        feature 2

    becomes separate logical sections.
    """

    lines = text.splitlines()

    sections = []
    current = []

    for line in lines:

        # Start a new section at an H1/H2/H3
        if re.match(r"^#{1,3}\s+", line):

            if current:
                section = "\n".join(current).strip()

                if section:
                    sections.append(section)

            current = [line]

        else:
            current.append(line)

    # Last section
    if current:
        section = "\n".join(current).strip()

        if section:
            sections.append(section)

    return sections


# ============================================================
# TEXT CHUNKING
# ============================================================

def split_large_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split large text into overlapping chunks.

    We prefer splitting at paragraph boundaries.
    """

    if len(text) <= chunk_size:
        return [text]

    paragraphs = text.split("\n\n")

    chunks = []
    current = ""

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if not paragraph:
            continue

        # If adding this paragraph still fits
        candidate = (
            f"{current}\n\n{paragraph}"
            if current
            else paragraph
        )

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        # Save current chunk
        if current:
            chunks.append(current.strip())

        # Paragraph itself is too large
        if len(paragraph) > chunk_size:

            start = 0

            while start < len(paragraph):

                end = start + chunk_size

                piece = paragraph[start:end].strip()

                if piece:
                    chunks.append(piece)

                start += chunk_size - overlap

            current = ""

        else:
            current = paragraph

    # Save final chunk
    if current:
        chunks.append(current.strip())

    return chunks


# ============================================================
# CREATE CHUNKS
# ============================================================

def create_chunks(
    text: str,
    filename: str,
) -> list[dict]:
    """
    Create semantic chunks from one document.
    """

    document_type = get_document_type(filename)

    title = extract_title(
        text,
        filename,
    )

    sections = split_into_sections(text)

    chunks = []

    for section in sections:

        section = normalize_text(section)

        if not section:
            continue

        # Split only if the section is too large
        pieces = split_large_text(section)

        for piece in pieces:

            chunks.append(
                {
                    "text": piece,
                    "title": title,
                    "type": document_type,
                    "source": "pharox3d.com",
                    "filename": filename,
                }
            )

    return chunks


# ============================================================
# PROCESS ALL DOCUMENTS
# ============================================================

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    files = sorted(
        INPUT_DIR.glob("*.md")
    )

    print(f"📂 Input: {INPUT_DIR}")
    print(f"📂 Output: {OUTPUT_DIR}")
    print(f"📄 Documents: {len(files)}")
    print()

    all_chunks = []

    # --------------------------------------------------------
    # Process every document
    # --------------------------------------------------------

    for file_path in files:

        text = file_path.read_text(
            encoding="utf-8"
        )

        chunks = create_chunks(
            text,
            file_path.name,
        )

        # Add chunk IDs
        for chunk in chunks:

            chunk["chunk_id"] = len(all_chunks)

            all_chunks.append(chunk)

        print(
            f"✅ {file_path.name} "
            f"→ {len(chunks)} chunks"
        )

    # --------------------------------------------------------
    # Save chunks
    # --------------------------------------------------------

    CHUNKS_FILE.write_text(
        json.dumps(
            all_chunks,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("🎉 Chunking complete!")
    print(f"📄 Documents: {len(files)}")
    print(f"🧩 Total chunks: {len(all_chunks)}")
    print(f"💾 Saved to: {CHUNKS_FILE}")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()