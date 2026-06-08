"""
Task 6 — Lexical Search (BM25 Sparse Retrieval).

Pipeline:
    1. Load toàn bộ chunks từ thư mục standardized (hoặc đọc lại từ ChromaDB)
    2. Xây dựng BM25 index từ corpus thực tế
    3. Với mỗi query, tính điểm BM25 cho từng document
    4. Trả về top_k documents có điểm cao nhất

Lý do chọn BM25:
    - Tìm kiếm từ khóa chính xác (exact keyword matching)
    - Không cần GPU/embedding model
    - Đặc biệt hiệu quả với tên điều luật, số hiệu văn bản (Điều 248, Nghị định 105...)
    - Bổ sung cho semantic search (hybrid retrieval)

Thư viện: rank-bm25
"""

from pathlib import Path
from typing import Optional

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"


def _load_corpus_from_disk() -> list[dict]:
    """Load tất cả nội dung markdown từ thư mục standardized."""
    documents = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"
        # Chia nhỏ theo đoạn (paragraph) để BM25 hoạt động đúng
        paragraphs = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 50]
        for i, para in enumerate(paragraphs):
            documents.append({
                "content": para,
                "metadata": {
                    "source": md_file.name,
                    "type": doc_type,
                    "chunk_index": i
                }
            })
    return documents


def _tokenize(text: str) -> list[str]:
    """Tokenize đơn giản: lowercase và tách từ theo dấu cách + dấu câu."""
    import re
    text = text.lower()
    tokens = re.findall(r'\w+', text)
    return tokens


def lexical_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Tìm kiếm BM25 dựa trên tần suất từ khóa.

    Args:
        query: Câu truy vấn
        top_k: Số kết quả trả về

    Returns:
        List of {
            'content': str,
            'score': float,       # BM25 score (0-1 sau khi normalize)
            'metadata': dict,
            'source': 'lexical'
        }
    """
    from rank_bm25 import BM25Okapi

    # 1. Load corpus từ disk thực tế
    corpus = _load_corpus_from_disk()
    if not corpus:
        return []

    # 2. Tokenize corpus
    tokenized_corpus = [_tokenize(doc["content"]) for doc in corpus]

    # 3. Build BM25 index
    bm25 = BM25Okapi(tokenized_corpus)

    # 4. Tokenize query và tính điểm
    tokenized_query = _tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # 5. Lấy top_k indexes có điểm cao nhất
    import numpy as np
    top_indices = np.argsort(scores)[::-1][:top_k]

    # 6. Normalize điểm về [0, 1]
    max_score = float(scores[top_indices[0]]) if scores[top_indices[0]] > 0 else 1.0

    results = []
    for idx in top_indices:
        raw_score = float(scores[idx])
        if raw_score <= 0:
            continue
        normalized_score = raw_score / max_score
        results.append({
            "content": corpus[idx]["content"],
            "score": round(normalized_score, 4),
            "metadata": corpus[idx]["metadata"],
            "source": "lexical"
        })

    # Đảm bảo sắp xếp giảm dần
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Điều 248 tàng trữ ma tuý",
        "hình phạt cai nghiện bắt buộc",
        "Nghị định 105 2021",
    ]
    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = lexical_search(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.4f}] [{r['metadata'].get('source', '')}] {r['content'][:120]}...")
