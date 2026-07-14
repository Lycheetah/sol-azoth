"""
L-4: Semantic Memory / Knowledge Retrieval — AZOTH
===================================================
Lightweight TF-IDF + cosine similarity retrieval over KNOWLEDGE/ vault.
No external dependencies beyond numpy + scipy.

Design:
  - On boot: scan KNOWLEDGE/, chunk each file into passages (~500 chars)
  - Build TF-IDF matrix over all chunks
  - Query: tokenize, IDF-weight, cosine-sim against all chunks
  - Return top-k chunks with file source + relevance score

Upgrade path: swap TF-IDF for sentence-transformers embeddings when available.
"""

from __future__ import annotations
import os
import re
import math
import json
import hashlib
from collections import Counter
from typing import List, Tuple, Optional

import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial.distance import cosine as cosine_distance

# ── Config ──────────────────────────────────────────────────────────────────────
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "KNOWLEDGE")
CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".retrieval_cache.json")
CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 100    # overlap between chunks
TOP_K = 5              # default results

# ── Stopwords (minimal — LAMAGUE domain terms are significant) ──────────────────
_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "shall", "should", "may", "might", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "because", "but", "and",
    "or", "if", "while", "that", "this", "these", "those", "it", "its",
}

# ── Tokenizer ───────────────────────────────────────────────────────────────────
def tokenize(text: str) -> List[str]:
    """Lowercase, split on non-alphanumeric, filter stopwords + short tokens."""
    tokens = re.findall(r"[a-zA-Z]\w{2,}", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) > 2]


# ── Chunking ────────────────────────────────────────────────────────────────────
def chunk_text(text: str, source_file: str) -> List[dict]:
    """Split text into overlapping chunks. Each chunk has content + metadata."""
    chunks = []
    # Split on paragraph boundaries first (respect structure)
    paragraphs = re.split(r"\n\s*\n", text)
    
    current_chunk = ""
    current_start = 0
    chunk_index = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        if len(current_chunk) + len(para) > CHUNK_SIZE and current_chunk:
            # Finalize current chunk
            chunks.append({
                "content": current_chunk.strip(),
                "source": source_file,
                "index": chunk_index,
                "start_char": current_start,
            })
            chunk_index += 1
            # Start new chunk with overlap from previous
            words = current_chunk.split()
            overlap_text = " ".join(words[-20:]) if len(words) > 20 else current_chunk
            current_chunk = overlap_text + "\n\n" + para
            current_start = max(0, current_start + len(current_chunk) - len(overlap_text) - len(para))
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
                current_start = 0
    
    # Final chunk
    if current_chunk.strip():
        chunks.append({
            "content": current_chunk.strip(),
            "source": source_file,
            "index": chunk_index,
            "start_char": current_start,
        })
    
    return chunks


# ── Corpus Builder ──────────────────────────────────────────────────────────────
class KnowledgeCorpus:
    """Scans KNOWLEDGE/, builds chunk index + TF-IDF matrix."""
    
    def __init__(self, knowledge_dir: str = KNOWLEDGE_DIR):
        self.knowledge_dir = knowledge_dir
        self.chunks: List[dict] = []
        self.vocab: dict = {}          # term -> index
        self.idf: dict = {}            # term -> idf score
        self.tfidf_matrix: Optional[csr_matrix] = None
        self._built = False
    
    def scan(self) -> int:
        """Scan KNOWLEDGE/ directory and chunk all markdown files."""
        if not os.path.isdir(self.knowledge_dir):
            print(f"[retrieval] KNOWLEDGE dir not found: {self.knowledge_dir}")
            return 0
        
        all_chunks = []
        for fname in sorted(os.listdir(self.knowledge_dir)):
            if not fname.endswith((".md", ".txt")):
                continue
            fpath = os.path.join(self.knowledge_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    text = f.read()
                chunks = chunk_text(text, fname)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"[retrieval] Error reading {fname}: {e}")
        
        self.chunks = all_chunks
        return len(all_chunks)
    
    def build(self) -> None:
        """Build TF-IDF matrix from scanned chunks."""
        if not self.chunks:
            self.scan()
        
        # Build vocabulary
        term_doc_count = Counter()
        doc_terms = []
        
        for chunk in self.chunks:
            terms = set(tokenize(chunk["content"]))
            doc_terms.append(list(terms))
            for t in terms:
                term_doc_count[t] += 1
        
        # Filter: terms appearing in at least 2 chunks (meaningful signal)
        # but cap at 90% of chunks (not universal)
        N = len(self.chunks)
        vocab_terms = sorted([
            t for t, count in term_doc_count.items()
            if count >= 2 and count <= N * 0.9
        ])
        
        self.vocab = {t: i for i, t in enumerate(vocab_terms)}
        self.idf = {
            t: math.log((N + 1) / (term_doc_count[t] + 1)) + 1
            for t in vocab_terms
        }
        
        # Build sparse TF-IDF matrix
        V = len(vocab_terms)
        D = len(self.chunks)
        
        rows, cols, data = [], [], []
        
        for d_idx, chunk in enumerate(self.chunks):
            term_counts = Counter(tokenize(chunk["content"]))
            max_tf = max(term_counts.values()) if term_counts else 1
            
            for term, count in term_counts.items():
                if term in self.vocab:
                    tf = count / max_tf  # normalized term frequency
                    tfidf = tf * self.idf[term]
                    rows.append(d_idx)
                    cols.append(self.vocab[term])
                    data.append(tfidf)
        
        self.tfidf_matrix = csr_matrix((data, (rows, cols)), shape=(D, V))
        self._built = True
    
    def query(self, query_text: str, top_k: int = TOP_K) -> List[dict]:
        """Return top-k chunks most relevant to query_text."""
        if not self._built:
            self.build()
        
        if not self.chunks or self.tfidf_matrix is None:
            return []
        
        # Vectorize query
        query_terms = Counter(tokenize(query_text))
        if not query_terms:
            return []
        
        max_qf = max(query_terms.values())
        q_vec = np.zeros(self.tfidf_matrix.shape[1])
        for term, count in query_terms.items():
            if term in self.vocab:
                tf = count / max_qf
                q_vec[self.vocab[term]] = tf * self.idf.get(term, 1)
        
        # Cosine similarity
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_unit = q_vec / q_norm
        
        # Dot product with all document vectors (rows of TF-IDF matrix)
        # Each row is already TF-IDF weighted
        doc_norms = np.sqrt((self.tfidf_matrix.multiply(self.tfidf_matrix)).sum(axis=1)).A1
        doc_norms = np.maximum(doc_norms, 1e-10)
        
        scores = self.tfidf_matrix.dot(q_unit) / doc_norms
        
        # Get top-k
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(scores[idx])
            if score < 0.05:
                continue
            chunk = self.chunks[idx]
            results.append({
                "score": round(score, 4),
                "source": chunk["source"],
                "content": chunk["content"][:500],  # trim for display
                "index": chunk["index"],
            })
        
        return results
    
    def query_formatted(self, query_text: str, top_k: int = TOP_K) -> str:
        """Return formatted string of results for system prompt injection."""
        results = self.query(query_text, top_k)
        if not results:
            return ""
        
        lines = ["[KNOWLEDGE RETRIEVAL]"]
        for r in results:
            lines.append(f"  [{r['source']}] (score: {r['score']})")
            lines.append(f"  {r['content'][:300]}")
            lines.append("")
        return "\n".join(lines)


# ── Singleton ────────────────────────────────────────────────────────────────────
_CORPUS: Optional[KnowledgeCorpus] = None

def get_corpus() -> KnowledgeCorpus:
    """Get or create the singleton corpus."""
    global _CORPUS
    if _CORPUS is None:
        _CORPUS = KnowledgeCorpus()
    return _CORPUS

def retrieve(query: str, top_k: int = TOP_K) -> List[dict]:
    """Convenience: retrieve top-k chunks for query."""
    return get_corpus().query(query, top_k)

def retrieve_formatted(query: str, top_k: int = TOP_K) -> str:
    """Convenience: retrieve formatted string for prompt injection."""
    return get_corpus().query_formatted(query, top_k)


# ── CLI Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    corpus = get_corpus()
    n = corpus.scan()
    print(f"[retrieval] Scanned {n} chunks from KNOWLEDGE/")
    corpus.build()
    print(f"[retrieval] Vocabulary: {len(corpus.vocab)} terms")
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nQuery: {query}")
        print(corpus.query_formatted(query))
    else:
        # Demo queries
        for q in ["truth pressure", "LAMAGUE symbol", "albedo", "constitution"]:
            print(f"\n{'='*60}")
            print(f"Query: {q}")
            print(corpus.query_formatted(q))
