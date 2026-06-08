"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k=5, top_p=0.9, temperature=0.3 (giải thích lý do bên dưới)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "Tôi không thể xác minh thông tin này"
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k = 5: Đủ evidence để trả lời nhiều góc độ, nhưng không quá dài
# gây hiện tượng "lost in the middle" (LLM quên thông tin ở giữa context)
TOP_K = 5

# top_p = 0.9 (nucleus sampling): Chỉ chọn token từ 90% xác suất tích luỹ
# → Giảm token ngẫu nhiên, giữ câu trả lời tự nhiên nhưng không quá random
TOP_P = 0.9

# temperature = 0.3: RAG cần trả lời factual, không cần sáng tạo
# → 0.3 đủ để văn phong tự nhiên mà vẫn bám sát facts
TEMPERATURE = 0.3


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý pháp luật thông minh, trả lời câu hỏi bằng tiếng Việt.

NGUYÊN TẮC BẮT BUỘC:
1. Chỉ sử dụng thông tin từ Context được cung cấp phía dưới.
2. Mỗi luận điểm hoặc dữ kiện PHẢI có citation trong ngoặc vuông, ví dụ:
   - [Bộ luật Hình sự 2015, Điều 248]
   - [Luật Phòng chống ma tuý 2021, Điều 32]
   - [VnExpress, 2024]
3. Nếu thông tin không có trong Context, hãy nói rõ:
   "Tôi không thể xác minh thông tin này từ các nguồn hiện có."
   TUYỆT ĐỐI không được đoán mò hoặc bịa đặt.
4. Trả lời rõ ràng, có cấu trúc, dùng đoạn văn hoặc bullet points.
5. Cuối câu trả lời, liệt kê tất cả nguồn đã sử dụng dưới dạng:
   **Nguồn tham khảo:**
   - [tên nguồn]"""


# =============================================================================
# DOCUMENT REORDERING (tránh "lost in the middle")
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM có xu hướng nhớ tốt thông tin ở ĐẦU và CUỐI prompt,
    trong khi thường "quên" hoặc bỏ qua thông tin ở GIỮA.

    Strategy (Lost in the Middle paper, Liu et al. 2023):
        Input: [rank1, rank2, rank3, rank4, rank5]  (score giảm dần)
        Output: [rank1, rank3, rank5, rank4, rank2]
        → Chunk quan trọng nhất ở đầu, quan trọng nhì ở cuối,
          chunk kém nhất ở giữa.

    Args:
        chunks: List sorted by score descending (từ retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return chunks

    # Tách thành odd index (0, 2, 4...) và even index (1, 3, 5...)
    # Odd → đầu danh sách, Even → cuối danh sách (đảo ngược)
    odds = chunks[::2]    # index 0, 2, 4... (rank 1, 3, 5...)
    evens = chunks[1::2]  # index 1, 3, 5... (rank 2, 4...)

    # Odd ở đầu, Even ở cuối (reversed = kém nhất ở giữa)
    reordered = odds + list(reversed(evens))
    return reordered


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string có label nguồn cho LLM cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string với source labels.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"Source {i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        score = chunk.get("score", 0.0)
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type} | Score: {score:.4f}]\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.

    Pipeline:
        1. Retrieve relevant chunks (semantic + lexical + rerank + fallback)
        2. Reorder để tránh lost in the middle (Liu et al. 2023)
        3. Format context với source labels rõ ràng
        4. Build prompt: system + context + query
        5. Gọi OpenAI gpt-4o-mini (temperature=0.3, top_p=0.9)
        6. Return answer + sources used

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY chưa được đặt trong .env")

    # Step 1: Retrieve
    print(f"\n[Generation] Query: {query}")
    chunks = retrieve(query, top_k=top_k)
    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ các nguồn hiện có. Không tìm thấy tài liệu liên quan.",
            "sources": [],
            "retrieval_source": "none"
        }

    # Step 2: Reorder (tránh lost in the middle)
    reordered = reorder_for_llm(chunks)

    # Step 3: Format context
    context = format_context(reordered)

    # Step 4: Build prompt
    user_message = f"""Dựa vào Context sau đây để trả lời câu hỏi:

Context:
{context}

---

Câu hỏi: {query}"""

    # Step 5: Gọi OpenAI
    client = OpenAI(api_key=api_key)
    print(f"[Generation] Calling OpenAI gpt-4o-mini (temperature={TEMPERATURE}, top_p={TOP_P})...")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )

    answer = response.choices[0].message.content

    # Step 6: Return
    retrieval_source = chunks[0].get("source", "hybrid") if chunks else "none"
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source
    }


if __name__ == "__main__":
    test_queries = [
        "Hình phạt cho tội tàng trữ trái phép chất ma tuý theo pháp luật Việt Nam?",
        "Những nghệ sĩ nào đã bị bắt vì liên quan tới ma tuý?",
        "Quy trình cai nghiện bắt buộc theo Luật Phòng chống ma tuý 2021?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
