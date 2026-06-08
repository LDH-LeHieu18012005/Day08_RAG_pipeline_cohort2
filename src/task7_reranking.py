"""
Task 7 — Reranking Module.

Chọn phương pháp: Cross-encoder reranker (Jina Reranker v2 qua API)
    - Lý do: Cross-encoder đọc CÙNG LÚC cả query và document (không embed riêng)
      nên nắm bắt được mối quan hệ tinh tế giữa câu hỏi và nội dung tốt hơn
      bi-encoder nhiều.
    - Jina Reranker v2 là multilingual → hỗ trợ tiếng Việt
    - Nếu không có API key, fallback sang RRF.

Cũng implement thêm MMR và RRF để có thể dùng khi cần.
"""

import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY", "")


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Tính cosine similarity giữa 2 vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a ** 2 for a in vec_a) ** 0.5
    norm_b = sum(b ** 2 for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def rerank_cross_encoder(
    query: str, candidates: list[dict], top_k: int = 5
) -> list[dict]:
    """
    Rerank candidates sử dụng Jina Reranker v2 API (cross-encoder).

    Cross-encoder hoạt động bằng cách đưa (query, document) vào CÙNG LÚC
    qua mô hình để tính relevance score — khác với bi-encoder tạo embedding riêng.

    Args:
        query: Câu truy vấn
        candidates: List of {'content': str, 'score': float, 'metadata': dict}
        top_k: Số lượng kết quả sau rerank

    Returns:
        List of top_k candidates, re-scored và sorted by rerank_score descending.
    """
    import requests

    if not JINA_API_KEY:
        raise ValueError("JINA_API_KEY chưa được đặt trong .env")

    # Chuẩn bị documents (chỉ lấy content text)
    documents = [c["content"] for c in candidates]

    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "jina-reranker-v2-base-multilingual",
            "query": query,
            "documents": documents,
            "top_n": top_k
        },
        timeout=30
    )
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data["results"]:
        original_idx = item["index"]
        score = item["relevance_score"]
        candidate = candidates[original_idx].copy()
        candidate["score"] = round(float(score), 4)
        results.append(candidate)

    # Đã được sort từ API nhưng sort lại để chắc chắn
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance — chọn candidates vừa relevant vừa diverse.

    MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Lý do dùng MMR: Tránh trả về nhiều chunks giống nhau từ cùng 1 đoạn văn bản.
    lambda_param = 0.7: Ưu tiên relevance (70%) hơn diversity (30%).

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content': str, 'score': float, 'embedding': list, 'metadata': dict}
        top_k: Số lượng kết quả
        lambda_param: Trade-off giữa relevance (1.0) và diversity (0.0)

    Returns:
        List of top_k candidates selected by MMR.
    """
    if not candidates:
        return []
    if len(candidates) <= top_k:
        return candidates

    selected_indices = []
    remaining_indices = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_idx = None
        best_score = float('-inf')

        for idx in remaining_indices:
            # Relevance to query
            emb = candidates[idx].get("embedding", [])
            if not emb:
                relevance = candidates[idx].get("score", 0.0)
            else:
                relevance = _cosine_similarity(query_embedding, emb)

            # Max similarity to already selected docs
            max_sim_to_selected = 0.0
            for sel_idx in selected_indices:
                sel_emb = candidates[sel_idx].get("embedding", [])
                cur_emb = candidates[idx].get("embedding", [])
                if sel_emb and cur_emb:
                    sim = _cosine_similarity(cur_emb, sel_emb)
                    max_sim_to_selected = max(max_sim_to_selected, sim)

            # MMR score
            mmr_score = lambda_param * relevance - (1 - lambda_param) * max_sim_to_selected

            if mmr_score > best_score:
                best_score = mmr_score
                best_idx = idx

        if best_idx is not None:
            selected_indices.append(best_idx)
            remaining_indices.remove(best_idx)

    return [candidates[i] for i in selected_indices]


def rerank_rrf(
    ranked_lists: list[list[dict]], top_k: int = 5, k: int = 60
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

    RRF(d) = Σ 1 / (k + rank_r(d))

    Lý do dùng RRF:
    - Kết hợp điểm từ semantic search và BM25 mà không cần normalize
    - k=60 là giá trị tối ưu từ paper gốc (Cormack et al. 2009)
    - Robust với điểm số khác thang đo từ các model khác nhau

    Args:
        ranked_lists: List of ranked result lists (mỗi list từ 1 ranker)
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60)

    Returns:
        List of top_k candidates sorted by RRF score descending.
    """
    rrf_scores: dict[str, float] = {}
    content_map: dict[str, dict] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, 1):
            key = item["content"]
            rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
            content_map[key] = item

    # Sort by RRF score
    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

    results = []
    for content, score in sorted_items[:top_k]:
        item = content_map[content].copy()
        item["score"] = round(score, 6)
        results.append(item)

    return results


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
    method: str = "cross_encoder",  # "cross_encoder" | "mmr" | "rrf"
) -> list[dict]:
    """
    Unified reranking interface.

    Ưu tiên cross_encoder (Jina API) vì chất lượng tốt nhất cho multilingual.
    Fallback sang RRF nếu không có API key hoặc lỗi mạng.

    Args:
        query: Câu truy vấn
        candidates: Danh sách candidates từ retrieval
        top_k: Số lượng kết quả sau rerank
        method: Phương pháp reranking

    Returns:
        List of top_k reranked candidates.
    """
    if method == "cross_encoder":
        if JINA_API_KEY:
            try:
                return rerank_cross_encoder(query, candidates, top_k)
            except Exception as e:
                print(f"  [Rerank] Jina API error: {e}. Fallback sang RRF.")
                return rerank_rrf([candidates], top_k=top_k)
        else:
            print("  [Rerank] JINA_API_KEY not found. Dùng RRF thay thế.")
            return rerank_rrf([candidates], top_k=top_k)
    elif method == "mmr":
        raise ValueError("Với MMR, hãy gọi rerank_mmr() trực tiếp và truyền query_embedding.")
    elif method == "rrf":
        raise ValueError("Với RRF, hãy gọi rerank_rrf() trực tiếp và truyền ranked_lists.")
    else:
        raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dummy_candidates = [
        {"content": "Điều 248: Tội tàng trữ trái phép chất ma tuý, hình phạt từ 2-7 năm tù.", "score": 0.8, "metadata": {"source": "bo-luat-hinh-su.md"}},
        {"content": "Nghệ sĩ X bị bắt vì sử dụng ma tuý tại nhà riêng.", "score": 0.7, "metadata": {"source": "article_01.md"}},
        {"content": "Hình phạt tù từ 2-7 năm cho tội tàng trữ theo Bộ luật Hình sự.", "score": 0.6, "metadata": {"source": "bo-luat-hinh-su.md"}},
        {"content": "Chương XX quy định về các tội phạm ma tuý.", "score": 0.55, "metadata": {"source": "bo-luat-hinh-su.md"}},
    ]
    print("Reranking with Jina Cross-Encoder...")
    results = rerank("hình phạt tàng trữ ma tuý", dummy_candidates, top_k=3)
    for r in results:
        print(f"[{r['score']:.4f}] {r['content'][:80]}")
