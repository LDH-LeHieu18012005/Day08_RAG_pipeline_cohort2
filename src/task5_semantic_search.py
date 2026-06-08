"""
Task 5 — Semantic Search (Dense Retrieval).

Pipeline:
    1. Nhận query string
    2. Embed query bằng cùng model đã dùng ở Task 4 (BAAI/bge-m3)
    3. Query ChromaDB theo cosine similarity
    4. Trả về top_k kết quả có score và metadata

Lý do chọn BAAI/bge-m3:
    - Multilingual: hỗ trợ tiếng Việt tốt, trained trên 100+ ngôn ngữ
    - Dimension 1024: đủ phong phú để capture ngữ nghĩa
    - BGE-M3 là SOTA cho tiếng Việt (theo benchmark MTEB)
"""

from pathlib import Path

# Phải dùng cùng model đã index ở Task 4
EMBEDDING_MODEL = "BAAI/bge-m3"
DB_PATH = str(Path(__file__).parent.parent / "data" / "vectorstore")
COLLECTION_NAME = "RAG_Docs"

# ===========================================================================
# Singleton cache — chỉ load model và ChromaDB client một lần duy nhất
# tránh crash khi gọi nhiều lần trong cùng process (vd: trong pytest)
# ===========================================================================
_model = None
_chroma_client = None
_collection = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=DB_PATH)
        _collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    return _collection


def semantic_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Tìm kiếm semantic dựa trên độ tương đồng vector (cosine similarity).

    Args:
        query: Câu truy vấn tự nhiên
        top_k: Số kết quả trả về

    Returns:
        List of {
            'content': str,
            'score': float,       # cosine similarity score (0-1)
            'metadata': dict,
            'source': 'semantic'
        }
    """
    # 1. Embed query (dùng singleton model)
    model = _get_model()
    query_embedding = model.encode(query).tolist()

    # 2. Kết nối ChromaDB (dùng singleton client)
    collection = _get_collection()

    # 3. Query ChromaDB
    n_results = min(top_k, collection.count())
    if n_results == 0:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    # 4. Chuyển distance sang similarity score
    output = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        # ChromaDB cosine distance: 0=giống nhau, 2=khác nhau hoàn toàn
        # Chuyển thành score [0, 1]
        score = float(1.0 - dist / 2.0) if dist <= 2 else 0.0
        output.append({
            "content": doc,
            "score": round(score, 4),
            "metadata": meta,
            "source": "semantic"
        })

    # Đảm bảo sắp xếp giảm dần theo score
    output.sort(key=lambda x: x["score"], reverse=True)
    return output


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý",
        "Cai nghiện bắt buộc theo luật",
    ]
    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 60)
        results = semantic_search(q, top_k=3)
        for i, r in enumerate(results, 1):
            print(f"  {i}. [{r['score']:.4f}] [{r['metadata'].get('source', '')}] {r['content'][:120]}...")
