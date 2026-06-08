"""
Task 8 — PageIndex Vectorless RAG.

Đăng ký tài khoản tại: https://pageindex.ai/
SDK & sample code: https://github.com/VectifyAI/PageIndex

PageIndex cho phép RAG mà không cần vector store — sử dụng
structural understanding của document thay vì embedding.

Cài đặt:
    pip install pageindex

Tài khoản: lấy PAGEINDEX_API_KEY từ .env
"""

import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"

# PageIndex API base URL
PAGEINDEX_BASE_URL = "https://api.pageindex.ai"


def _get_headers() -> dict:
    return {
        "Authorization": f"Bearer {PAGEINDEX_API_KEY}",
        "Content-Type": "application/json"
    }


def upload_documents() -> list[str]:
    """
    Upload toàn bộ markdown documents lên PageIndex.

    Returns:
        List of document IDs đã upload.
    """
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY chưa được đặt trong .env")

    doc_ids = []
    for md_file in STANDARDIZED_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_type = "legal" if "legal" in str(md_file) else "news"

        payload = {
            "content": content,
            "metadata": {
                "filename": md_file.name,
                "type": doc_type
            }
        }

        resp = requests.post(
            f"{PAGEINDEX_BASE_URL}/documents",
            headers=_get_headers(),
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        doc_id = resp.json().get("id", "")
        doc_ids.append(doc_id)
        print(f"  + Uploaded: {md_file.name} (id={doc_id})")

    return doc_ids


def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval sử dụng PageIndex.
    Dùng làm fallback khi hybrid search không có kết quả tốt.

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa

    Returns:
        List of {
            'content': str,
            'score': float,
            'metadata': dict,
            'source': 'pageindex'   # Đánh dấu nguồn retrieval
        }
    """
    if not PAGEINDEX_API_KEY:
        raise ValueError("PAGEINDEX_API_KEY chưa được đặt trong .env")

    payload = {
        "query": query,
        "top_k": top_k
    }

    resp = requests.post(
        f"{PAGEINDEX_BASE_URL}/search",
        headers=_get_headers(),
        json=payload,
        timeout=30
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "content": item.get("text", item.get("content", "")),
            "score": float(item.get("score", 0.0)),
            "metadata": item.get("metadata", {}),
            "source": "pageindex"
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    if not PAGEINDEX_API_KEY:
        print("WARNING: Hay set PAGEINDEX_API_KEY trong file .env")
        print("  Dang ky tai: https://pageindex.ai/")
    else:
        print("Uploading documents...")
        upload_documents()

        print("\nTest query:")
        results = pageindex_search("hinh phat su dung ma tuy", top_k=3)
        for r in results:
            print(f"[{r['score']:.4f}] {r['content'][:100]}...")
