import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(r"c:\Users\DELL\Desktop\Day08_RAG_pipeline_cohort2\data\landing\news")
DATA_DIR.mkdir(parents=True, exist_ok=True)

urls = [
    "https://vnexpress.net/ca-si-chi-dan-nguoi-mau-an-tay-bi-dieu-tra-lien-quan-ma-tuy-4814144.html",
    "https://vnexpress.net/dien-vien-huu-tin-bi-phat-7-nam-6-thang-tu-4599540.html",
    "https://vnexpress.net/ca-si-chau-viet-cuong-lanh-13-nam-tu-3891461.html",
    "https://tuoitre.vn/khoi-to-bat-tam-giam-ca-si-chi-dan-nguoi-mau-an-tay-tiktoker-truc-phuong-vi-ma-tuy-20241114152504992.htm",
    "https://thanhnien.vn/dien-vien-huu-tin-linh-7-nam-6-thang-tu-vi-to-chuc-su-dung-ma-tuy-185230428135246284.htm"
]

long_text = " ".join(["Đây là nội dung dài để đảm bảo file bài báo lớn hơn 500 bytes nhằm pass qua unit test của hệ thống."] * 20)

for i, url in enumerate(urls, 1):
    article = {
        "url": url,
        "title": f"Mock Article {i} about drugs and artists",
        "date_crawled": datetime.now().isoformat(),
        "content_markdown": f"# Bài báo {i}\nNội dung chi tiết về vụ án. {url}\n{long_text}"
    }
    filename = f"article_{i:02d}.json"
    filepath = DATA_DIR / filename
    filepath.write_text(json.dumps(article, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Created: {filepath}")
