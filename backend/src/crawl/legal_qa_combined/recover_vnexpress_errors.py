"""Recover split-page VnExpress Q&A in a separate dataset, without touching successful crawl.
Usage: python recover_vnexpress_errors.py --input-dir output/vnexpress --out output/vnexpress_recovered
"""

import argparse
import csv
import json
import random
import re
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from crawl_vnexpress import canonical, clean, parse_article, write_csv, write_jsonl

ARTICLE_ID = re.compile(r"-(\d{6,9})(?:-p\d+)?\.html$", re.I)
LEGAL_RE = re.compile(
    r"(?:(?:các?\s+)?(?:khoản\s+\d+(?:\s*[,và]+\s*khoản\s*\d+)*\s*)?(?:điểm\s+[a-zđ]\s+)?Điều\s+\d+(?:\s*[,và]+\s*Điều\s*\d+)*)\s+(?:của\s+)?(?:Bộ luật|Luật|Nghị định|Nghị quyết|Thông tư)[^\n.;:]{0,125}",
    re.I,
)


def base_url(url):
    url = canonical(url)
    return re.sub(r"-p\d+\.html$", ".html", url, flags=re.I)


def id_of(url):
    m = ARTICLE_ID.search(canonical(url))
    return m.group(1) if m else None


def read_records(path):
    if not path.exists():
        return []
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"[WARN] Invalid JSONL row in {path}")
    return rows


def load_successes(folder):
    # If a previous recovery was performed, its records can also be excluded.
    seen = set()
    for filename in ("legal_qa.jsonl", "legal_qa.csv", "recovered_qa.jsonl"):
        for row in read_records(folder / filename):
            if row.get("extraction_status") not in ("full_qa", "recovered_split_pages"):
                continue
            if not row.get("question") or not row.get("answer"):
                continue
            article_id = id_of(row.get("url", ""))
            if article_id:
                seen.add(article_id)
    return seen


def extract_question(html):
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("article.fck_detail")
    if root is None:
        raise ValueError("Trang gốc thiếu article.fck_detail")
    title = root.select_one("h1.title-detail")
    desc = root.select_one("p.description")
    content = []
    if desc and clean(desc.get_text(" ", strip=True)):
        content.append(clean(desc.get_text(" ", strip=True)))
    for p in root.find_all("p", recursive=False):
        s = clean(p.get_text(" ", strip=True))
        if not s or re.match(r"^Luật sư tư vấn\s*:", s, re.I):
            break
        content.append(s)
    # Remove attribution, if present as the last paragraph.
    if content and re.match(r"^(Độc giả|Bạn đọc)\b", content[-1], re.I):
        content.pop()
    content = list(dict.fromkeys(content))
    return clean(title.get_text(" ", strip=True)) if title else None, "\n".join(content)


def extract_answer(html):
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one("article.fck_detail")
    if root is None:
        raise ValueError("Trang p2 thiếu article.fck_detail")
    # p2 often has paragraphs without a 'Luật sư tư vấn:' marker.
    paragraphs = [
        clean(p.get_text(" ", strip=True)) for p in root.find_all("p", recursive=False)
    ]
    paragraphs = [x for x in paragraphs if x]
    start = next(
        (
            i + 1
            for i, s in enumerate(paragraphs)
            if re.match(r"^Luật sư tư vấn\s*:", s, re.I)
        ),
        0,
    )
    paragraphs = paragraphs[start:]
    lawyer = None
    if paragraphs and re.search(r"^(?:Luật sư|LS\.)\s+", paragraphs[-1], re.I):
        lawyer = paragraphs.pop()
    if not paragraphs:
        raise ValueError("Trang p2 không có đoạn câu trả lời hợp lệ")
    return "\n".join(paragraphs), lawyer


def possible_p2_links(html, url):
    soup = BeautifulSoup(html, "html.parser")
    wanted_id = id_of(url)
    links = []
    for a in soup.select("a[href]"):
        href = canonical(urljoin(url, a.get("href", "")))
        if id_of(href) == wanted_id and re.search(r"-p2\.html$", href, re.I):
            links.append(href)
    predicted = re.sub(r"\.html$", "-p2.html", base_url(url), flags=re.I)
    links.append(predicted)
    return list(dict.fromkeys(links))


def find_citations(answer):
    matches = []
    for match in LEGAL_RE.finditer(answer):
        raw = clean(match.group())
        if raw and raw.lower() not in [m["raw_text"].lower() for m in matches]:
            matches.append(
                {
                    "raw_text": raw,
                    "source_field": "answer",
                    "extraction_method": "regex",
                    "verified": False,
                    "verification_status": "not_verified",
                    "char_start": match.start(),
                    "char_end": match.end(),
                }
            )
    return matches


def fetch(session, url, timeout):
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    if "html" not in response.headers.get("Content-Type", "text/html").lower():
        raise ValueError(
            f'Unexpected content type: {response.headers.get("Content-Type")}'
        )
    return response.text


def recover(
    input_dir: str = None,
    out: str = None,
    errors_file: str = None,
    successes: str = None,
    delay: float = 2.0,
    timeout: int = 30,
    category: str = "Dân sự",
):
    if not category:
        raise ValueError("Category cannot be empty")
    input_dir = Path(input_dir)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    errors_path = input_dir / errors_file if errors_file else None
    date_str = datetime.now().strftime("%Y-%m-%d")
    recovered_file = out / f"recovered_qa_{date_str}.jsonl"
    recovered_csv_file = out / f"recovered_qa_{date_str}.csv"

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    if errors_path and not errors_path.exists():
        raise FileNotFoundError(f"Errors file does not exist: {errors_path}")

    errors = read_records(errors_path) if errors_path else []

    seen = load_successes(input_dir) | load_successes(out)
    if successes:
        for row in read_records(Path(successes)):
            if row.get("answer") and row.get("question"):
                aid = id_of(row.get("url", ""))
                if aid:
                    seen.add(aid)
    # Avoid successful articles, duplicated IDs, and repeat attempts within input errors.
    pending = {}
    for item in errors:
        u = item.get("url", "")
        aid = id_of(u)
        if aid and aid not in seen:
            pending.setdefault(aid, base_url(u))
    previous = read_records(recovered_file) if recovered_file.exists() else []
    results = list(previous)
    recovered_ids = {id_of(row.get("url", "")) for row in results}
    failures = []
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; AcademicLegalResearch/1.0)",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.7",
        }
    )
    for i, (aid, url) in enumerate(pending.items(), start=1):
        if aid in recovered_ids:
            print(f"[SKIP] {aid} already recovered")
            continue
        try:
            main_html = fetch(session, url, timeout)
            title, question = extract_question(main_html)
            if not question:
                raise ValueError("Trang gốc không có question")
            answer = lawyer = answer_url = None
            attempt_errors = []
            for candidate in possible_p2_links(main_html, url):
                try:
                    p2_html = fetch(session, candidate, timeout)
                    answer, lawyer = extract_answer(p2_html)
                    answer_url = candidate
                    break
                except Exception as ex:
                    attempt_errors.append(f"{candidate}: {ex}")
            if not answer:
                raise ValueError(
                    "Không tìm thấy trả lời trong p2. " + "; ".join(attempt_errors)
                )
            # Preserve identical field structure from original crawler.
            from datetime import datetime, timezone
            from hashlib import sha256

            content = question + "\n\n" + answer
            row = {
                "id": "vne_" + aid,
                "url": url,
                "title": title,
                "source": "VnExpress",
                "category": category,
                "published_at_raw": None,
                "question": question,
                "answer": answer,
                "content": content,
                "citation": find_citations(answer),
                "relevant_law": [],
                "lawyer": lawyer,
                "citation_verified": False,
                "extraction_status": "full_qa",
                "civil_code_2015_scope": "not_reviewed",
                "content_sha256": sha256(content.encode()).hexdigest(),
                "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                "answer_url": answer_url,
                "recovery_method": "split_page_p2",
            }
            results.append(row)
            recovered_ids.add(aid)
            print(f"[RECOVERED] {i}/{len(pending)} {aid} -> {answer_url}")
        except Exception as e:
            failures.append({"url": url, "error": str(e), "recovery_status": "failed"})
            print(f"[FAIL] {i}/{len(pending)} {url}: {e}")
        write_jsonl(recovered_file, results)
        write_jsonl(out / "recovery_errors.jsonl", failures)
        time.sleep(delay + random.uniform(0, 0.2))
    columns = [
        "id",
        "url",
        "answer_url",
        "title",
        "source",
        "category",
        "published_at_raw",
        "question",
        "answer",
        "content",
        "citation",
        "relevant_law",
        "lawyer",
        "extraction_status",
        "civil_code_2015_scope",
        "content_sha256",
        "recovery_method",
    ]
    write_csv(recovered_csv_file, results, columns)
    print(
        f"DONE: pending={len(pending)}, recovered_total={len(results)}, failed_this_run={len(failures)}, skipped_successful={len(seen)}"
    )


def recover_errors_url(
    input_dir: str = "output/vnexpress",
    out: str = "output/vnexpress_recovered",
    errors_file: str = None,
    category: str = None,
    successes: str = None,
    delay: float = 2.0,
    timeout: int = 30,
):
    # // check

    if not input_dir or not out or not category or not errors_file:
        raise ValueError(
            "Missing required arguments: input_dir, out, errors_file, category"
        )

    recover(
        input_dir=input_dir,
        out=out,
        errors_file=errors_file,
        successes=successes,
        delay=delay,
        timeout=timeout,
        category=category,
    )


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(
        description="Recover split-page VnExpress Q&A in a separate dataset."
    )

    arg_parser.add_argument(
        "--input-dir", default="output/vnexpress", help="Input directory"
    )
    arg_parser.add_argument(
        "--out", default="output/vnexpress_recovered", help="Output directory"
    )
    arg_parser.add_argument("--errors-file", help="Errors file")
    arg_parser.add_argument("--category", help="Category")
    arg_parser.add_argument("--successes", help="Successes file")
    arg_parser.add_argument(
        "--delay", type=float, default=2.0, help="Delay between requests"
    )
    arg_parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout for each request"
    )

    args = arg_parser.parse_args()

    # // check
    if not args.category:
        print(f"Category: {args.category}")
        raise ValueError("Missing required arguments: --category")

    # run:  python recover_vnexpress_errors.py --input-dir output/vnexpress --out output/vnexpress_recovered --errors-file crawl_errors_20230915.jsonl --category "Hôn nhân và gia đình"
    # run:  python recover_vnexpress_errors.py --category "Hôn nhân và gia đình"

    date_str = datetime.now().strftime("%Y-%m-%d")
    input_dir = args.input_dir or "output/vnexpress"
    out = args.out or "output/vnexpress_recovered"
    errors_file = args.errors_file or f"crawl_errors_{date_str}.jsonl"
    category = args.category
    successes = None
    delay = 2.0
    timeout = 30

    recover_errors_url(
        input_dir=input_dir,
        out=out,
        errors_file=errors_file,
        category=category,
        successes=successes,
        delay=delay,
        timeout=timeout,
    )
