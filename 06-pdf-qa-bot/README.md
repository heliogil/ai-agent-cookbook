# 06 — PDF Q&A Bot

Ask questions about any PDF. Keyword-ranked chunking, no vector database, no embeddings API.

## Setup

```bash
pip install -r requirements.txt
export MINIMAX_API_KEY=your_key
python main.py contract.pdf
```

## Usage

```
Loading contract.pdf...
Loaded: 24,832 chars → 5 chunks

Question: What is the payment term?
Net 30 days from invoice date, as stated in Section 4.2: "Payment shall be due..."

Question: Who are the parties?
Acme Corp (Contractor) and XYZ Ltd (Client), defined in the preamble.
```

## How it works

1. Extract text with `pypdf`
2. Split into 6,000-char chunks with 500-char overlap
3. For each question: rank chunks by keyword overlap (no embedding cost)
4. Top 3 chunks → MiniMax M3 answers with citation

## Extend it

**Add vision for scanned PDFs:** If the PDF has images instead of text, use MiniMax vision on each page image instead of `pypdf`.

**Add a web interface:** Replace the CLI loop with a FastAPI endpoint + simple HTML upload form.

**Add semantic search:** Replace keyword ranking with embeddings from `minimax-py` for better recall on long documents.
