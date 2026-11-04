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

BASE = "https://luatvietnam.vn"
LIST = BASE + "/luat-su-tu-van/dan-su-65.html?page={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 16; Pixel 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36"
}

TOPICS = [
    # {
    #     "name": "Dân sự",
    #     "url": "https://luatvietnam.vn/luat-su-tu-van/dan-su-65.html?page={}",
    # },
    {
        "name": "Lao động - Tiền lương",
        "url": "https://luatvietnam.vn/luat-su-tu-van/lao-dong-tien-luong-7.html?page={}",
    },
    {
        "name": "Đất đai - Nhà ở",
        "url": "https://luatvietnam.vn/luat-su-tu-van/dat-dai-nha-o-3.html?page={}",
    },
    {
        "name": "Doanh nghiệp",
        "url": "https://luatvietnam.vn/luat-su-tu-van/doanh-nghiep-24.html?page={}",
    },
    {
        "name": "Hình sự",
        "url": "https://luatvietnam.vn/luat-su-tu-van/hinh-su-66.html?page={}",
    },
    {
        "name": "Hôn nhân - Gia đình",
        "url": "https://luatvietnam.vn/luat-su-tu-van/hon-nhan-gia-dinh-64.html?page={}",
    },
    {
        "name": "Bảo hiểm",
        "url": "https://luatvietnam.vn/luat-su-tu-van/bao-hiem-57.html?page={}",
    },
    {
        "name": "Giao thông",
        "url": "https://luatvietnam.vn/luat-su-tu-van/giao-thong-28.html?page={}",
    },
    {
        "name": "Thuế - Phí - Lệ phí",
        "url": "https://luatvietnam.vn/luat-su-tu-van/thue-phi-le-phi-4.html?page={}",
    },
    {
        "name": "Hành chính",
        "url": "https://luatvietnam.vn/luat-su-tu-van/hanh-chinh-27.html?page={}",
    },
]

# https://luatvietnam.vn/luat-su-tu-van/doanh-nghiep-24.html
# https://luatvietnam.vn/luat-su-tu-van/hinh-su-66.html
# https://luatvietnam.vn/luat-su-tu-van/hon-nhan-gia-dinh-64.html
# https://luatvietnam.vn/luat-su-tu-van/bao-hiem-57.html
# https://luatvietnam.vn/luat-su-tu-van/giao-thong-28.html
# https://luatvietnam.vn/luat-su-tu-van/thue-phi-le-phi-4.html
# https://luatvietnam.vn/luat-su-tu-van/hanh-chinh-27.html


def normalize(url):
    p = urlsplit(urljoin(BASE, url))
    return urlunsplit((p.scheme, p.netloc, p.path, "", ""))


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


def list_page(soup, page, topic):
    result = []
    for title in soup.select("h3.article-hoi-dap a[href]"):
        href = title.get("href", "")
        u = normalize(href)
        if not re.search(r"-\d+-faqs\.html$", urlsplit(u).path):
            continue
        row = title.find_parent("tr") or title.parent
        number = row.select_one(".hoi-dap-number") if row else None
        date = row.select_one("a.time-date") if row else None
        result.append(
            {
                "url": u,
                "title": clean_text(title),
                "question_number": clean_text(number).lstrip("#") or None,
                "listed_date": clean_text(date) or None,
                "listing_page": page,
                "source": "LuatVietnam",
                "topic": topic,
            }
        )
    return result


def extract_paragraphs(answer):
    # Xóa quảng cáo và thành phần không liên quan
    for node in answer.select(
        "script, style, iframe, video, audio, figure, "
        ".advHolder, .advsapa, .google-ads, "
        ".section-lvn, .uk-player, .ucp-close-btn"
    ):
        node.decompose()

    paragraphs = []

    # print(
    #     "Số thẻ p lồng nhau:",
    #     sum(p.find_parent("p") is not None for p in answer.select("p")),
    # )
    for p in answer.select("p"):
        text = p.get_text(" ", strip=True)

        if not text:
            continue

        if text.startswith("Xem thêm:"):
            continue

        if text.startswith("Trên đây là nội dung tư vấn"):
            continue

        paragraphs.append(text)

    return "\n\n".join(paragraphs)


def parse_article(html, url, meta=None):
    soup = BeautifulSoup(html, "html5lib")
    h = soup.select_one("article.the-article h1.the-article-title")
    q = soup.select_one(".entry-title-ls .entry-hoidap-ls")
    answer = soup.select_one(
        ".entry-hoi-dap .the-article-body.entry"
    ) or soup.select_one(".entry-hoi-dap .the-article-body")
    if not (h and q and answer):
        raise ValueError("Missing required article title/question/answer selectors")
    for n in q.select("strong"):
        n.decompose()
    for n in answer.select(
        "script,style,iframe,video,audio,figure,.advHolder,.advsapa,.google-ads,.section-lvn,.uk-player,.ucp-close-btn"
    ):
        n.decompose()

    question = clean_text(q)
    answer_text = extract_paragraphs(answer)
    # print("Answer text length:", len(answer_text))
    related = []
    for a in soup.select("section.section-related a[href]"):
        if a.find_parent("section") and "Văn bản liên quan" in clean_text(
            a.find_parent("section").select_one("h2")
        ):
            x = {"title": clean_text(a), "url": normalize(a.get("href"))}
            if x not in related:
                related.append(x)
    # Citation candidates are *unverified mentions*; they are not statements of current validity.
    pattern = re.compile(
        r"(?:(?:khoản\s+\d+\s+)?Điều\s+\d+(?:\s*,\s*\d+)?(?:\s+(?:của|Bộ luật|Luật|Nghị quyết)[^,.;:\n]{0,110})?)",
        re.I,
    )
    citation = list(
        dict.fromkeys(m.group().strip() for m in pattern.finditer(answer_text))
    )
    lawyer = soup.select_one(".block-tuvan .text-tuvan")
    meta = meta or {}
    raw_num = soup.select_one(".item-t1-ls")
    date = soup.select_one(".the-article-meta")
    return {
        "id": hashlib.sha256(normalize(url).encode()).hexdigest()[:20],
        "url": normalize(url),
        "source": "LuatVietnam",
        "title": clean_text(h),
        "question_number": clean_text(raw_num).lstrip("#")
        or meta.get("question_number"),
        "published_at_raw": clean_text(date) or meta.get("listed_date"),
        "question": question,
        "answer": answer_text,
        "content": question + "\n\n" + answer_text,
        "citation": citation,
        "citation_verified": False,
        "related_legal_documents": related,
        "lawyer": clean_text(lawyer) or None,
        "listing_page": meta.get("listing_page"),
        "extraction_status": "full_qa",
        "content_sha256": hashlib.sha256(
            (question + "\n" + answer_text).encode()
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

    # file_path with date
    date_str = datetime.now().strftime("%Y-%m-%d")
    url_file_path = out / f"article_urls_{date_str}.csv"
    url_file_path_jsonl = out / f"article_urls_{date_str}.jsonl"

    # PHASE 1: collect ALL article URLs from ALL pages before fetching details.
    for topic in TOPICS:
        name = topic["name"]
        topic_url = topic["url"]
        print(f"[TOPIC] {name} {topic_url}", flush=True)
        for page in range(1, args.max_pages + 1):
            print(f"[PAGE] {name} page={page}", flush=True)
            u = topic_url.format(page)
            try:
                html = get(s, u, args.delay)
                soup = BeautifulSoup(html, "html5lib")
                links = list_page(soup, page, name)
                if not links:
                    empty += 1
                    print(f"[EMPTY] page={page} url={u}", flush=True)
                    issues.append(
                        {
                            "stage": "listing",
                            "page": page,
                            "url": u,
                            "error": "No matching article links",
                            "topic": name,
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
                write_csv(url_file_path, list(seen.values()))
            except Exception as e:
                issues.append(
                    {
                        "stage": "listing",
                        "page": page,
                        "url": u,
                        "error": str(e),
                        "topic": name,
                    }
                )
                print(f"[ERROR] listing page={page}: {e}", flush=True)
                # A failed page may mean temporary network issues. Never silently mark crawl complete.
                if not args.continue_on_error:
                    break

        print(
            f"[TOPIC COMPLETE] {name} pages={pages} unique_total={len(seen)}",
            flush=True,
        )

    rows = list(seen.values())
    write_csv(url_file_path, rows)
    write_jsonl(url_file_path_jsonl, rows)
    print(
        f"[LINK COLLECTION COMPLETE] pages={pages}, unique_urls={len(rows)}", flush=True
    )
    # PHASE 2: crawl detail URLs; incremental saving supports resuming after interruption.
    details_path = out / f"legal_qa_{date_str}.jsonl"
    completed = set()
    if details_path.exists() and not args.fresh:
        for line in details_path.read_text(encoding="utf-8").splitlines():
            try:
                completed.add(json.loads(line)["url"])
            except (ValueError, KeyError):
                pass
    if args.fresh:
        details_path.write_text("", encoding="utf-8")
    with details_path.open("a", encoding="utf-8") as f:
        for i, meta in enumerate(rows, 1):
            u = meta["url"]
            if u in completed:
                continue
            try:
                html = get(s, u, args.delay)
                data = parse_article(html, u, meta)
                data["topic"] = meta.get("topic")
                data["category"] = meta.get("topic")  # map topic to category
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                f.flush()
                print(f"[DETAIL] {i}/{len(rows)} {u}", flush=True)
            except Exception as e:
                issues.append({"stage": "detail", "url": u, "error": str(e)})
                print(f"[ERROR] detail {u}: {e}", flush=True)
    (out / f"crawl_errors_{date_str}.json").write_text(
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
    p.add_argument("--fresh", action="store_true")
    run(p.parse_args())

# python crawl_luatvietnam.py --max-pages 50 --delay 2.5 --out output/luatvietnam
# python crawl_luatvietnam.py --max-pages 50 --delay 2.5 --out output/luatvietnam --continue-on-error --fresh
