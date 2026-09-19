"""
RAG knowledge layer: chunks the curated source documents (app/data/sources/*.txt),
embeds them with ChromaDB's built-in ONNX MiniLM embedding function, and stores
them in a persistent ChromaDB collection. Retrieval returns chunks WITH their
source metadata so the API can
surface a "sources used" panel (retrieval transparency) rather than hiding the
knowledge step inside an opaque LLM call.
"""
import os
import glob
import chromadb
from chromadb.utils import embedding_functions

from app.config import settings

SOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sources")
COLLECTION_NAME = "darukaa_knowledge"

# Deliberately NOT sentence-transformers here: that package pulls in full
# PyTorch, which alone can push a process over Render's free-tier 512MB RAM
# limit once combined with FastAPI/chromadb/etc (confirmed live — the app
# OOM'd on startup with it). ChromaDB's built-in default embedding function
# uses the same all-MiniLM-L6-v2 model but runs it through onnxruntime
# instead of torch — same embedding quality, a fraction of the memory.
_embedding_function = embedding_functions.DefaultEmbeddingFunction()


def _chunk_text(text: str, source_file: str) -> list[dict]:
    """
    Paragraph-based chunking. The source docs are already written as short,
    self-contained paragraphs (title/source/region header + one paragraph per
    finding), so splitting on blank lines keeps each chunk coherent instead of
    cutting a stat off from the sentence that explains it.
    """
    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    # Keep the header block (TITLE/SOURCE/REGION) attached to every chunk from
    # this file so a retrieved chunk is still self-explanatory on its own.
    header_lines = [l for l in raw_paragraphs[0].split("\n")] if raw_paragraphs else []
    header = "\n".join(header_lines)

    for i, para in enumerate(raw_paragraphs[1:], start=1):
        chunks.append(
            {
                "id": f"{source_file}::chunk_{i}",
                "text": f"{header}\n\n{para}",
                "source_file": source_file,
            }
        )
    return chunks


def load_and_chunk_sources() -> list[dict]:
    chunks = []
    for path in sorted(glob.glob(os.path.join(SOURCES_DIR, "*.txt"))):
        source_file = os.path.basename(path)
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        chunks.extend(_chunk_text(text, source_file))
    return chunks


def get_chroma_client():
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def build_index(force_rebuild: bool = False):
    """Run once at startup (or via a CLI command) to (re)populate the collection."""
    client = get_chroma_client()

    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        if not force_rebuild:
            return client.get_collection(COLLECTION_NAME, embedding_function=_embedding_function)
        client.delete_collection(COLLECTION_NAME)

    collection = client.create_collection(COLLECTION_NAME, embedding_function=_embedding_function)

    chunks = load_and_chunk_sources()
    if not chunks:
        return collection

    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source_file": c["source_file"]} for c in chunks],
    )
    return collection


def retrieve(query: str, top_k: int = 3) -> list[dict]:
    """
    Returns a list of {text, source_file, distance} — the raw retrieval result.
    Callers (the LangGraph flow) are responsible for deciding whether a result
    is relevant enough to use (see guardrails.py's no-match-no-claim check),
    never for inventing content when nothing relevant comes back.

    Deliberately fault-tolerant: the reasoning chain (connections.json) is the
    system's primary source of truth — RAG is a supplementary evidence layer.
    If the embedding model/network/DB isn't reachable, that should degrade to
    "no extra sources shown" (empty list), never take down the whole
    /api/chat response. A no-match-no-claim guardrail failure and a network
    hiccup are different things and shouldn't look the same to the caller,
    but neither should crash the request.
    """
    try:
        client = get_chroma_client()
        try:
            collection = client.get_collection(COLLECTION_NAME, embedding_function=_embedding_function)
        except ValueError:
            collection = build_index()

        results = collection.query(query_texts=[query], n_results=top_k)

        hits = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for text, meta, dist in zip(docs, metas, dists):
            hits.append(
                {
                    "text": text,
                    "source_file": meta.get("source_file"),
                    "distance": dist,
                }
            )
        return hits
    except Exception:
        return []


if __name__ == "__main__":
    # `python -m app.services.rag` — builds/rebuilds the index from source files.
    col = build_index(force_rebuild=True)
    print(f"Indexed collection '{COLLECTION_NAME}' with {col.count()} chunks.")
