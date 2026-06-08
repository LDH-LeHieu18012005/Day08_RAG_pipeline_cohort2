"""
Task 9 — Retrieval Pipeline Hoàn Chỉnh.

Kết hợp semantic search + lexical search + reranking + PageIndex fallback
thành một pipeline thống nhất.

Logic:
    1. Chạy semantic_search + lexical_search song song
    2. Merge kết quả bằng RRF (Reciprocal Rank Fusion)
    3. Rerank bằng Jina Cross-Encoder (multilingual)
    4. Nếu top result score < threshold → fallback sang PageIndex
    5. Return top_k results
"""

from .task5_semantic_search import semantic_search
from .task6_lexical_search import lexical_search
from .task7_reranking import rerank, rerank_rrf
from .task8_pageindex_vectorless import pageindex_search


# =============================================================================
# CONFIGURATION
# =============================================================================

SCORE_THRESHOLD = 0.3   # Nếu best score < threshold → fallback PageIndex
DEFAULT_TOP_K = 5
RERANK_METHOD = "cross_encoder"  # Dùng Jina API thật


def retrieve(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = SCORE_THRESHOLD,
    use_reranking: bool = True,
) -> list[dict]:
    """
    Retrieval pipeline hoàn chỉnh với fallback logic.

    Pipeline:
        Query
          ├→ Semantic Search (ChromaDB + BAAI/bge-m3)  → results_dense
          ├→ Lexical Search  (BM25 từ corpus thực tế)  → results_sparse
          │
          ├→ Merge (RRF) → merged_results
          ├→ Rerank (Jina Cross-Encoder) → reranked_results
          │
          └→ If best_score < threshold:
                └→ PageIndex Vectorless → fallback_results

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả cuối cùng
        score_threshold: Ngưỡng điểm tối thiểu cho hybrid results
        use_reranking: Có áp dụng reranking hay không

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 1: Chạy song song semantic + lexical
    print(f"  [Retrieve] Semantic search...")
    dense_results = semantic_search(query, top_k=top_k * 2)

    print(f"  [Retrieve] Lexical search (BM25)...")
    sparse_results = lexical_search(query, top_k=top_k * 2)

    print(f"  [Retrieve] Dense: {len(dense_results)}, Sparse: {len(sparse_results)}")

    # Step 2: Merge bằng RRF
    merged = rerank_rrf([dense_results, sparse_results], top_k=top_k * 2)
    for item in merged:
        item["source"] = "hybrid"

    if not merged:
        print("  [Retrieve] Khong co ket qua hybrid -> Fallback PageIndex")
        try:
            return pageindex_search(query, top_k=top_k)
        except Exception as e:
            print(f"  [Retrieve] PageIndex loi: {e}. Tra ve ket qua rong.")
            return []

    # Step 3: Rerank bằng Jina Cross-Encoder
    if use_reranking and merged:
        print(f"  [Retrieve] Reranking {len(merged)} candidates...")
        final_results = rerank(query, merged, top_k=top_k, method=RERANK_METHOD)
    else:
        final_results = merged[:top_k]

    # Step 4: Check threshold → fallback PageIndex
    best_score = final_results[0]["score"] if final_results else 0.0
    if not final_results or best_score < score_threshold:
        print(f"  [Retrieve] Best score {best_score:.4f} < threshold {score_threshold}")
        print(f"  [Retrieve] Fallback -> PageIndex Vectorless")
        try:
            fallback = pageindex_search(query, top_k=top_k)
            if fallback:
                return fallback
        except Exception as e:
            print(f"  [Retrieve] PageIndex loi: {e}. Dung ket qua hybrid.")
        # Neu PageIndex cung loi, van tra ve hybrid results
        return final_results[:top_k] if final_results else merged[:top_k]

    print(f"  [Retrieve] Returning {len(final_results[:top_k])} results (best score: {best_score:.4f})")
    return final_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Nghệ sĩ nào bị bắt vì sử dụng ma tuý năm 2024",
        "Luật phòng chống ma tuý 2021 quy định gì về cai nghiện",
    ]

    for q in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {q}")
        print('-' * 60)
        results = retrieve(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.4f}] [{r['source']}] [{r['metadata'].get('source', '')}]")
            print(f"     {r['content'][:120]}...")
