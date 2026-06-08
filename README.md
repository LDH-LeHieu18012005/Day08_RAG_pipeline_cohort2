# Day08 RAG Pipeline Cohort 2

Du an xay dung pipeline Retrieval-Augmented Generation (RAG) cho mien du lieu **phap luat Viet Nam ve ma tuy** va **tin tuc nghe si lien quan den ma tuy**. Repo gom 10 task ca nhan va deliverable bai tap nhom theo huong **RAG Evaluation Pipeline**.

## Thong Tin Nhom

| Thanh vien | MSSV |
|-----------|------|
| Hieu Tran Minh Anh | 2A202600706 |
| Hoang Hai Dang | 2A202600916 |
| Nguyen Huyen San | 2A202600835 |
| Vu Dang Khiem | 2A202600727 |
| Le Duong Hieu | 2A202600635 |
| Nguyen Truong Phuc | 2A202600767 |

## Cau Truc Du An

```text
.
|-- data/
|   |-- landing/              # Du lieu goc: legal docs va news JSON
|   |-- standardized/         # Markdown da chuan hoa
|   |-- vectorstore/          # ChromaDB local
|   `-- pageindex_doc_ids.json
|-- src/
|   |-- task1_collect_legal_docs.py
|   |-- task2_crawl_news.py
|   |-- task3_convert_markdown.py
|   |-- task4_chunking_indexing.py
|   |-- task5_semantic_search.py
|   |-- task6_lexical_search.py
|   |-- task7_reranking.py
|   |-- task8_pageindex_vectorless.py
|   |-- task9_retrieval_pipeline.py
|   `-- task10_generation.py
|-- group_project/
|   |-- README.md
|   `-- evaluation/
|       |-- golden_dataset.json
|       |-- eval_pipeline.py
|       `-- results.md
|-- tests/
|-- REPORT.md
|-- requirements.txt
`-- .env.example
```

## Pipeline Ca Nhan

| Task | Noi dung | Trang thai |
|------|----------|------------|
| 1 | Thu thap 3 van ban phap luat ve ma tuy | Hoan thanh |
| 2 | Crawl 5 bai bao lien quan nghe si va ma tuy | Hoan thanh |
| 3 | Convert du lieu sang Markdown bang MarkItDown | Hoan thanh |
| 4 | Chunking va indexing vao vector store | Hoan thanh |
| 5 | Semantic search | Hoan thanh |
| 6 | Lexical search BM25 | Hoan thanh |
| 7 | Reranking | Hoan thanh |
| 8 | PageIndex vectorless fallback | Hoan thanh |
| 9 | Retrieval pipeline hybrid + fallback | Hoan thanh |
| 10 | Generation co citation va reorder context | Hoan thanh |

## Bai Tap Nhom

Nhom chon deliverable **RAG Evaluation Pipeline** voi framework **DeepEval**.

| Hang muc | File | Trang thai |
|----------|------|------------|
| Golden dataset >= 15 Q&A | `group_project/evaluation/golden_dataset.json` | Hoan thanh |
| Evaluation script voi 4 metrics | `group_project/evaluation/eval_pipeline.py` | Hoan thanh |
| A/B comparison 2 configs | `group_project/evaluation/results.md` | Hoan thanh |
| Bao cao worst performers va de xuat cai tien | `group_project/evaluation/results.md` | Hoan thanh |

Chi tiet kien truc va phan cong nam trong `group_project/README.md`.

## Cai Dat

```bash
pip install -r requirements.txt
```

Tao file `.env` tu mau neu can chay cac module co goi API:

```bash
copy .env.example .env
```

## Chay Test Ca Nhan

```bash
pytest tests/ -v
```

## Chay Evaluation Nhom

```bash
python group_project/evaluation/eval_pipeline.py
```

Ket qua duoc ghi vao:

```text
group_project/evaluation/results.md
```

## Ghi Chu

Evaluation nhom chon DeepEval va mac dinh chay che do local deterministic, DeepEval-compatible, de tranh phu thuoc quota OpenAI/Jina/PageIndex trong luc demo. Pipeline ca nhan van giu cac module API/fallback theo dung yeu cau ban dau.
