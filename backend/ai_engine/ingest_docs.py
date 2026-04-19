"""
Document Ingestion Script
--------------------------
Run once to index all PDFs in ./data/business_guides/ into ChromaDB.

Usage:
    python ai_engine/ingest_docs.py

Place your business guide PDFs in:
    backend/data/business_guides/
"""
import os
import sys
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCS_PATH = os.getenv("DOCS_PATH", "./data/business_guides")
CHUNK_SIZE = 500     # characters per chunk
CHUNK_OVERLAP = 50  # overlap between chunks


def load_text_from_pdf(path: str) -> str:
    """Extract text from a PDF using PyMuPDF (fitz) or fallback to raw read."""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        return "\n".join(page.get_text() for page in doc)
    except ImportError:
        logger.warning("PyMuPDF not installed. Trying pdfminer...")
        try:
            from pdfminer.high_level import extract_text
            return extract_text(path)
        except ImportError:
            logger.error("Neither PyMuPDF nor pdfminer found. Install: pip install pymupdf")
            return ""


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end].strip())
        start += size - overlap
    return [c for c in chunks if len(c) > 50]  # skip tiny chunks


def ingest_all():
    """Ingest documents into ChromaDB with proper error handling."""
    try:
        from ai_engine.embeddings import embed_batch
        from ai_engine.vector_store import add_documents, count_documents
    except ImportError as e:
        logger.error(f"Failed to import AI modules: {e}")
        raise

    os.makedirs(DOCS_PATH, exist_ok=True)
    pdf_files = [f for f in os.listdir(DOCS_PATH) if f.endswith(".pdf")]

    if not pdf_files:
        logger.warning(f"No PDFs found in {DOCS_PATH}. Adding sample text...")
        # Add some built-in sample knowledge
        sample_chunks = [
            "A startup feasibility study must cover market size, competition, cost structure, and revenue model.",
            "The lean startup methodology focuses on build-measure-learn cycles to validate ideas quickly.",
            "Digital marketing for small businesses includes SEO, social media, email marketing, and paid ads.",
            "Common startup funding stages: Bootstrapping → Seed → Series A → Series B → IPO.",
            "A minimum viable product (MVP) is the simplest version of a product that can be released to test a hypothesis.",
            "Business model canvas covers key partners, activities, resources, value propositions, channels, customer segments, cost structure, and revenue streams.",
            "Cash flow management is critical for startups — most fail due to running out of cash, not lack of product-market fit.",
            "SWOT analysis: Strengths, Weaknesses, Opportunities, Threats — a foundational framework for business planning.",
        ]
        ids = [str(uuid.uuid4()) for _ in sample_chunks]
        embeddings = embed_batch(sample_chunks)
        add_documents(ids, sample_chunks, embeddings)
        logger.info(f"Indexed {len(sample_chunks)} sample knowledge chunks.")
        return

    all_chunks, all_ids, all_meta = [], [], []

    for filename in pdf_files:
        filepath = os.path.join(DOCS_PATH, filename)
        logger.info(f"Processing: {filename}")
        text = load_text_from_pdf(filepath)
        if not text:
            continue
        chunks = chunk_text(text)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_ids.append(str(uuid.uuid4()))
            all_meta.append({"source": filename})

    if all_chunks:
        embeddings = embed_batch(all_chunks)
        add_documents(all_ids, all_chunks, embeddings, all_meta)
        logger.info(f"Total indexed: {count_documents()} chunks.")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    ingest_all()
