"""
PDF Q&A — upload a PDF, ask questions about it.
Run: pip install -r requirements.txt && python main.py report.pdf
"""
import os, sys
from pathlib import Path
from openai import OpenAI

MINIMAX_KEY  = os.environ["MINIMAX_API_KEY"]
BASE_URL     = os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/anthropic/v1")
CHUNK_CHARS  = 6000
OVERLAP      = 500

ai = OpenAI(api_key=MINIMAX_KEY, base_url=BASE_URL)


def extract_text(pdf_path: str) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    except ImportError:
        raise SystemExit("Install pypdf: pip install pypdf")


def chunk(text: str, size: int = CHUNK_CHARS, overlap: int = OVERLAP) -> list[str]:
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        start += size - overlap
    return chunks


def find_relevant(chunks: list[str], question: str, top_k: int = 3) -> list[str]:
    """Simple keyword overlap ranking — no embeddings needed."""
    words = set(question.lower().split())
    scored = [(sum(w in c.lower() for w in words), c) for c in chunks]
    return [c for _, c in sorted(scored, reverse=True)[:top_k]]


def answer(context_chunks: list[str], question: str) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    resp = ai.chat.completions.create(
        model="MiniMax-M3",
        messages=[
            {"role": "system", "content":
                "You are a precise document analyst. Answer based ONLY on the provided context. "
                "If the answer is not in the context, say so clearly. "
                "Quote the relevant passage when possible."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python main.py <path/to/file.pdf>")

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        raise SystemExit(f"File not found: {pdf_path}")

    print(f"Loading {pdf_path}...")
    text   = extract_text(pdf_path)
    chunks = chunk(text)
    print(f"Loaded: {len(text):,} chars → {len(chunks)} chunks\n")

    while True:
        try:
            q = input("Question (or 'quit'): ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q or q.lower() == "quit":
            break

        relevant = find_relevant(chunks, q)
        reply    = answer(relevant, q)
        print(f"\n{reply}\n")


if __name__ == "__main__":
    main()
