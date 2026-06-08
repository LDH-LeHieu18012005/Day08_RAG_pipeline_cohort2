# Bai Tap Nhom - RAG Evaluation Pipeline

## Muc Tieu

Nhom chon san pham **RAG Evaluation Pipeline** voi framework **DeepEval** de danh gia pipeline RAG ve phap luat ma tuy va tin tuc lien quan. Deliverable tap trung vao 4 metric bat buoc, golden dataset toi thieu 15 cap Q&A, so sanh A/B giua 2 cau hinh retrieval va bao cao ket qua.

## Thanh Vien

| Thanh vien | MSSV | Vai tro | Trang thai |
|-----------|------|---------|------------|
| Hieu Tran Minh Anh | 2A202600706 | Tich hop pipeline ca nhan, tong hop README va bao cao nhom | Hoan thanh |
| Hoang Hai Dang | 2A202600916 | Kiem tra golden dataset va cau hoi phap luat | Hoan thanh |
| Nguyen Huyen San | 2A202600835 | Phan tich metric faithfulness va answer relevance | Hoan thanh |
| Vu Dang Khiem | 2A202600727 | Phan tich context recall va context precision | Hoan thanh |
| Le Duong Hieu | 2A202600635 | Chuan bi A/B comparison va worst performers | Hoan thanh |
| Nguyen Truong Phuc | 2A202600767 | Kiem thu script evaluation va huong dan chay | Hoan thanh |

## Kien Truc He Thong

```text
data/landing
  -> data/standardized/*.md
  -> Task 4 chunking/indexing
  -> Task 5 semantic search
  -> Task 6 lexical BM25
  -> Task 7 reranking
  -> Task 9 retrieval pipeline
  -> Task 10 generation with citation
  -> group_project/evaluation/eval_pipeline.py
       -> golden_dataset.json
       -> A/B comparison
       -> results.md
```

## Cau Hinh Danh Gia

| Config | Mo ta | Muc dich |
|--------|------|----------|
| Config A - hybrid + rerank | Ket hop lexical/dense scoring offline va rerank bang overlap | Cau hinh de xuat cho demo |
| Config B - dense-only baseline | So khop char n-gram, khong rerank | Baseline de so sanh hoi quy |

## Metrics

| Metric | Y nghia |
|--------|---------|
| Faithfulness | Cau tra loi co bam vao context truy xuat khong |
| Answer Relevance | Cau tra loi co lien quan den cau hoi / expected answer khong |
| Context Recall | Context co lay du evidence mong doi khong |
| Context Precision | Ti le context top-k that su huu ich |

## Deliverables

| File | Noi dung | Trang thai |
|------|----------|------------|
| `group_project/evaluation/golden_dataset.json` | 15 cap Q&A voi expected answer va expected context | Hoan thanh |
| `group_project/evaluation/eval_pipeline.py` | Script evaluation offline, co A/B comparison | Hoan thanh |
| `group_project/evaluation/results.md` | Bang diem, worst performers va de xuat cai tien | Hoan thanh |

## Huong Dan Chay

Tu thu muc goc repository:

```bash
pip install -r requirements.txt
python group_project/evaluation/eval_pipeline.py
```

Sau khi chay, xem bao cao tai:

```bash
group_project/evaluation/results.md
```

Chay lai test ca nhan neu can kiem tra pipeline goc:

```bash
pytest tests/ -v
```

## Ghi Chu Demo

Nhom chon DeepEval lam framework danh gia. Script mac dinh dung che do local deterministic, DeepEval-compatible, de tranh loi quota OpenAI/Jina/PageIndex trong buoi trinh bay. Neu co API key va muon demo LLM-as-judge, co the thay phan cham diem local bang metric DeepEval online tren cung golden dataset.
