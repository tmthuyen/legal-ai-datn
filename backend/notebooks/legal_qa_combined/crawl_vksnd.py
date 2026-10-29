#!/usr/bin/env python3
"""Collect every category page's article links first, then crawl each detail page."""

import argparse
import csv
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE = "https://vksndtc.gov.vn/hoidap/Pages/hoi-dap.aspx"
TOPIC_ID = 2
LIST = BASE + "?IdChuDeHoiDap=" + str(TOPIC_ID) + "&Page={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36"
}
SOURCE = "VIỆN KIỂM SÁT NHÂN DÂN TỐI CAO"


def normalize(url):
    p = urlsplit(urljoin(BASE, url))
    url = urlunsplit((p.scheme, p.netloc, p.path, p.query, ""))
    return url


def clean_text(node):
    return node.get_text(" ", strip=True) if node else ""


def session():
    s = requests.Session()
    s.headers.update(HEADERS)
    retry = Retry(
        total=3,
        backoff_factor=1.3,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def get(s: requests.Session, u: str, delay: float = 0.0) -> str:
    time.sleep(delay)
    r = s.get(u, timeout=30)
    r.raise_for_status()

    if r.encoding is None:
        r.encoding = r.apparent_encoding

    return r.text


def list_page(soup: BeautifulSoup, page: int):
    result = []

    rows = soup.select("table.library tbody tr")
    for r in rows:
        a = r.select_one('td[data-label="Câu hỏi"] a[href]')

        if not a:
            continue

        title = clean_text(a)
        href = a.get("href", "")
        u = normalize(href)
        result.append(
            {
                "url": u,
                "title": title,
                "question_number": None,
                "listed_date": None,
                "listing_page": page,
                "source": SOURCE,
            }
        )
    return result


def extract_question(soup: BeautifulSoup):
    paragraphs = []
    for p in soup.select("p"):
        text = p.get_text(" ", strip=True)

        if not text:
            continue

        paragraphs.append(text)

    return "\n".join(paragraphs)


def extract_answer(soup: BeautifulSoup):
    citations = []
    paragraphs = []

    for p in soup.select("p"):
        text = p.get_text(" ", strip=True)

        if not text:
            continue

        pattern = re.compile(
            r"(?:điểm\s+[a-zđ]\s+)?(?:khoản\s+\d+\s+)?Điều\s+\d+", re.I
        )
        citation = list(
            dict.fromkeys(m.group().strip() for m in pattern.finditer(text))
        )

        citations.extend(citation)

        paragraphs.append(text)

    return "\n".join(paragraphs), citations


def parse_article(html, url, meta=None):
    soup = BeautifulSoup(html, "html5lib")

    html_content = soup.select_one(".content-detail")

    if not html_content:
        raise ValueError("Không tìm thấy nội dung bài viết")

    title = clean_text(html_content.select_one("h3"))

    question_node = html_content.select_one(".noidung")
    question_text = extract_question(question_node)

    answer_node = html_content.select_one(".hdtraloi .hdtraloiitem .noidung")
    answer_text, citations = extract_answer(answer_node)

    return {
        "id": hashlib.sha256(normalize(url).encode()).hexdigest()[:20],
        "url": normalize(url),
        "source": SOURCE,
        "category": "Dân sự",
        "title": title,
        "question_number": None,
        "published_at_raw": None,
        "question": question_text,
        "answer": answer_text,
        "content": question_text + "\n\n" + answer_text,
        "citation": citations,
        "citation_verified": False,
        "related_legal_documents": None,
        "lawyer": None,
        "listing_page": meta.get("listing_page"),
        "extraction_status": "full_qa",
        "content_sha256": hashlib.sha256(
            (question_text + "\n" + answer_text).encode()
        ).hexdigest(),
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run(args):
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    s = session()
    seen = {}
    issues = []
    empty = 0
    pages = 0
    # PHASE 1: collect ALL article URLs from ALL pages before fetching details.
    for page in range(1, args.max_pages + 1):
        u = LIST.format(page)
        try:
            html = get(s, u, args.delay)
            soup = BeautifulSoup(html, "html5lib")
            links = list_page(soup, page)
            if not links:
                empty += 1
                issues.append(
                    {
                        "stage": "listing",
                        "page": page,
                        "url": u,
                        "error": "No matching article links",
                    }
                )
                if empty >= args.stop_after_empty:
                    break
                continue
            empty = 0
            pages += 1
            for row in links:
                seen.setdefault(row["url"], row)
            print(
                f"[LIST] page={page} entries={len(links)} unique_total={len(seen)}",
                flush=True,
            )
            write_csv(out / "article_urls.csv", list(seen.values()))
        except Exception as e:
            issues.append({"stage": "listing", "page": page, "url": u, "error": str(e)})
            print(f"[ERROR] listing page={page}: {e}", flush=True)
            # A failed page may mean temporary network issues. Never silently mark crawl complete.
            if not args.continue_on_error:
                break
    rows = list(seen.values())
    write_csv(out / "article_urls.csv", rows)
    write_jsonl(out / "article_urls.jsonl", rows)
    print(
        f"[LINK COLLECTION COMPLETE] pages={pages}, unique_urls={len(rows)}", flush=True
    )
    # PHASE 2: crawl detail URLs; incremental saving supports resuming after interruption.
    details_path = out / "legal_qa.jsonl"
    completed = set()

    with details_path.open("a", encoding="utf-8") as f:
        for i, meta in enumerate(rows, 1):
            u = meta["url"]
            if u in completed:
                continue
            try:
                html = get(s, u, args.delay)
                data = parse_article(html, u, meta)
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[DETAIL] {i}/{len(rows)} {u}", flush=True)
            except Exception as e:
                issues.append({"stage": "detail", "url": u, "error": str(e)})
                print(f"[ERROR] detail {u}: {e}", flush=True)
    (out / "crawl_errors.json").write_text(
        json.dumps(issues, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        f"DONE: {len(rows)} URLs identified. Detail results: {details_path}. Errors: {len(issues)}"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--max-pages", type=int, default=100)
    p.add_argument("--delay", type=float, default=2.5)
    p.add_argument("--out", default="output")
    p.add_argument("--stop-after-empty", type=int, default=2)
    p.add_argument("--continue-on-error", action="store_true")
    run(p.parse_args())

# python crawl_vksnd.py --max-pages 50 --delay 2.5 --out output/vksnd
# python crawl_vksnd.py --max-pages 50 --delay 2.5 --out output/luatvietnam --continue-on-error --fresh
