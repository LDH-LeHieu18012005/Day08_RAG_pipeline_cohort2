# RAG Evaluation Results

## Framework used

DeepEval is the selected framework. This report was produced with the local deterministic DeepEval-compatible runner so the demo can run without external LLM/API quota, while keeping the required metrics: faithfulness, answer relevance, context recall, and context precision.

## Overall Scores

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Delta |
|--------|----------------------------|-----------------------|-------|
| Faithfulness | 0.9713 | 0.9660 | +0.0053 |
| Answer Relevance | 0.5711 | 0.5286 | +0.0425 |
| Context Recall | 1.0000 | 1.0000 | +0.0000 |
| Context Precision | 0.8533 | 0.8000 | +0.0533 |
| Average | 0.8489 | 0.8236 | +0.0253 |

## A/B Comparison Analysis

**Config A:** Local hybrid lexical retrieval with overlap reranking.

**Config B:** Character n-gram similarity baseline without reranking.

**Conclusion:** Config A - hybrid + rerank performs better on the current golden dataset. The hybrid configuration is expected to be stronger for legal questions because exact terms such as article numbers and offence names are important signals.

## Worst Performers (Bottom 3)

| # | Question | Avg | Faithfulness | Relevance | Recall | Precision | Likely Root Cause |
|---|----------|-----|--------------|-----------|--------|-----------|-------------------|
| 1 | Trong retrieval pipeline, nguon nao duoc uu tien khi hybrid search khong du diem? | 0.5816 | 0.9833 | 0.1429 | 1.0000 | 0.2000 | Top-k context contains noisy or broad chunks. |
| 2 | Generation co citation su dung chien luoc nao de tranh lost in the middle? | 0.7172 | 0.9833 | 0.2857 | 1.0000 | 0.6000 | Generated answer snippet needs stronger citation formatting. |
| 3 | Nhom tai lieu legal trong corpus gom nhung van ban nao? | 0.7530 | 0.9833 | 0.4286 | 1.0000 | 0.6000 | Generated answer snippet needs stronger citation formatting. |

## Recommendations

### Improvement 1
**Action:** Expand the standardized legal corpus with full official texts and article-level metadata.
**Expected impact:** Higher context recall for questions that mention specific articles or legal procedures.

### Improvement 2
**Action:** Store chunk metadata as `document`, `article`, `year`, and `source_url`, then show those fields in citations.
**Expected impact:** Better faithfulness auditing and clearer source display during the demo.

### Improvement 3
**Action:** Keep Config A as the default retrieval path, but use dense-only as a regression baseline in every evaluation run.
**Expected impact:** Makes future retrieval changes measurable instead of anecdotal.

## Per-question Results (Config A)

| # | Question | Sources | Avg |
|---|----------|---------|-----|
| 1 | Hinh phat co ban cho toi san xuat trai phep chat ma tuy theo Dieu 248 la gi? | bo-luat-hinh-su-2015-chuong-xx.md, luat-phong-chong-ma-tuy-2021.md, nghi-dinh-105-2021-nd-cp.md, article_01.md, article_05.md | 0.9741 |
| 2 | Dieu 248 quy dinh khung tang nang 07 den 15 nam tu trong nhung truong hop nao? | bo-luat-hinh-su-2015-chuong-xx.md, nghi-dinh-105-2021-nd-cp.md, luat-phong-chong-ma-tuy-2021.md, article_05.md, article_03.md | 0.8958 |
| 3 | Toi tang tru trai phep chat ma tuy theo Dieu 249 co muc phat co ban nao? | bo-luat-hinh-su-2015-chuong-xx.md, luat-phong-chong-ma-tuy-2021.md, nghi-dinh-105-2021-nd-cp.md, article_01.md, article_05.md | 0.8864 |
| 4 | Dieu 249 de cap den nhung toi nao lien quan lam can cu tai pham hoac chua xoa an tich? | bo-luat-hinh-su-2015-chuong-xx.md, nghi-dinh-105-2021-nd-cp.md, article_01.md, luat-phong-chong-ma-tuy-2021.md, article_04.md | 0.7879 |
| 5 | Pham vi dieu chinh cua Luat Phong chong ma tuy 2021 gom nhung noi dung nao? | nghi-dinh-105-2021-nd-cp.md, luat-phong-chong-ma-tuy-2021.md, bo-luat-hinh-su-2015-chuong-xx.md, article_05.md, article_04.md | 0.9236 |
| 6 | Theo Luat Phong chong ma tuy 2021, chat ma tuy duoc hieu nhu the nao? | luat-phong-chong-ma-tuy-2021.md, nghi-dinh-105-2021-nd-cp.md, bo-luat-hinh-su-2015-chuong-xx.md, article_04.md, article_01.md | 0.8580 |
| 7 | Theo Luat Phong chong ma tuy 2021, nguoi nghien ma tuy la ai? | luat-phong-chong-ma-tuy-2021.md, nghi-dinh-105-2021-nd-cp.md, bo-luat-hinh-su-2015-chuong-xx.md, article_04.md, article_01.md | 0.9501 |
| 8 | Nghi dinh 105/2021/ND-CP huong dan nhung nhom noi dung nao cua Luat Phong chong ma tuy? | nghi-dinh-105-2021-nd-cp.md, luat-phong-chong-ma-tuy-2021.md, bo-luat-hinh-su-2015-chuong-xx.md, article_04.md, article_01.md | 0.9705 |
| 9 | Doi tuong ap dung cua Nghi dinh 105/2021/ND-CP la nhung ai? | nghi-dinh-105-2021-nd-cp.md, luat-phong-chong-ma-tuy-2021.md, article_03.md, article_05.md, article_04.md | 0.8968 |
| 10 | Nguon cua bai bao article_01 ve ca si Chi Dan va nguoi mau An Tay la trang nao? | article_04.md, article_01.md, article_03.md, article_05.md, article_02.md | 0.9114 |
| 11 | article_01 duoc crawl vao ngay nao? | bo-luat-hinh-su-2015-chuong-xx.md, luat-phong-chong-ma-tuy-2021.md, article_05.md, article_03.md, article_01.md | 0.7815 |
| 12 | Nhom tai lieu legal trong corpus gom nhung van ban nao? | bo-luat-hinh-su-2015-chuong-xx.md, nghi-dinh-105-2021-nd-cp.md, luat-phong-chong-ma-tuy-2021.md, article_01.md, article_05.md | 0.7530 |
| 13 | Pipeline ca nhan dung nhung nhom tai lieu nao de tra loi cau hoi RAG? | nghi-dinh-105-2021-nd-cp.md, bo-luat-hinh-su-2015-chuong-xx.md, article_01.md, luat-phong-chong-ma-tuy-2021.md, article_03.md | 0.8461 |
| 14 | Trong retrieval pipeline, nguon nao duoc uu tien khi hybrid search khong du diem? | bo-luat-hinh-su-2015-chuong-xx.md, luat-phong-chong-ma-tuy-2021.md, nghi-dinh-105-2021-nd-cp.md, article_04.md, article_05.md | 0.5816 |
| 15 | Generation co citation su dung chien luoc nao de tranh lost in the middle? | bo-luat-hinh-su-2015-chuong-xx.md, nghi-dinh-105-2021-nd-cp.md, luat-phong-chong-ma-tuy-2021.md, article_05.md | 0.7172 |
