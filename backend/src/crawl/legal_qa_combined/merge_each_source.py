from pathlib import Path

import pandas as pd

from src.crawl.legal_qa_combined.utils import FileUtils


def merge_vnexpress(
    output_path: str, recovered_path: str, prefix_final_file_name: str = "all_legal_qa"
):
    output_path = Path(output_path)
    recovered_path = Path(recovered_path)

    final_csv_path = output_path / f"{prefix_final_file_name}.csv"
    final_jsonl_path = output_path / f"{prefix_final_file_name}.jsonl"
    final_url_csv_path = output_path / f"{prefix_final_file_name}_urls.csv"

    # glob all CSV and JSONL files in the output_path and recovered_path: prefix = "legal_qa"
    jsonl_files = list(output_path.glob("legal_qa*.jsonl")) + list(
        recovered_path.glob("recovered_qa*.jsonl")
    )

    csv_files = list(output_path.glob("legal_qa*.csv")) + list(
        recovered_path.glob("recovered_qa*.csv")
    )

    url_files = list(output_path.glob("article_urls*.csv"))

    legal_qa_csv_rows = []
    legal_qa_jsonl_rows = []
    url_rows = []

    columns = set()
    for jsonl_file in jsonl_files:
        rows = FileUtils.read_jsonl(path=jsonl_file)
        legal_qa_jsonl_rows.extend(rows)
        columns.update(rows[0].keys() if rows else [])

    for csv_file in csv_files:
        rows = FileUtils.read_csv(path=csv_file)
        legal_qa_csv_rows.extend(rows)
        columns.update(rows[0].keys() if rows else [])

    for url_file in url_files:
        rows = FileUtils.read_csv(path=url_file)
        url_rows.extend(rows)

    print(f"[INFO] {len(url_rows)} rows from {len(url_files)} URL CSV files")

    # loại bỏ hàng trùng với url
    before_all_rows = legal_qa_csv_rows + legal_qa_jsonl_rows

    all_legal_qa_rows = []

    # before csv + jsonl
    length = len(before_all_rows)
    print(
        f"[INFO] Merging {length} rows from {len(csv_files)} CSV files and {len(jsonl_files)} JSONL files"
    )

    url_set = set()

    for row in before_all_rows:

        # chuyển category: Hôn nhân gia đình, Hôn nhân và Gia đình thành category: Hôn nhân - Gia đình
        for cate in ["Hôn nhân gia đình", "Hôn nhân và Gia đình"]:
            category: str = row.get("category", "").strip()
            if category.lower() == cate.lower():
                row["category"] = "Hôn nhân - Gia đình"

        if row.get("url") not in url_set:
            all_legal_qa_rows.append(row)
        url_set.add(row.get("url"))

    length_after = len(all_legal_qa_rows)
    print(f"[INFO] After removing duplicates with URL CSV, {length_after} rows remain")

    # write merged CSV and JSONL files
    columns_list = list(columns)
    print("[INFO] Columns: ", columns_list)
    FileUtils.write_csv(
        path=final_csv_path, rows=all_legal_qa_rows, columns=columns_list
    )
    FileUtils.write_jsonl(path=final_jsonl_path, rows=all_legal_qa_rows)
    FileUtils.write_csv(
        path=final_url_csv_path,
        rows=url_rows,
        columns=url_rows[0].keys() if url_rows else [],
    )

    print(
        f"[INFO] Merged CSV written to {final_csv_path}, JSONL written to {final_jsonl_path}, URL CSV written to {final_url_csv_path}"
    )

    # pandas
    # statistics: category,
    df = pd.DataFrame(all_legal_qa_rows)
    print("Số danh mục: ", df.groupby("category").size())


def merge_lvn(output_path: str, prefix_final_file_name: str = "all_legal_qa"):

    output_path = Path(output_path)

    final_csv_path = output_path / f"{prefix_final_file_name}.csv"
    final_jsonl_path = output_path / f"{prefix_final_file_name}.jsonl"
    final_url_csv_path = output_path / f"{prefix_final_file_name}_urls.csv"

    # glob all CSV and JSONL files in the output_path and recovered_path: prefix = "legal_qa"
    jsonl_files = list(output_path.glob("legal_qa*.jsonl"))

    csv_files = list(output_path.glob("legal_qa*.csv"))

    url_files = list(output_path.glob("article_urls*.csv"))

    legal_qa_csv_rows = []
    legal_qa_jsonl_rows = []
    url_rows = []

    columns = set()
    for jsonl_file in jsonl_files:
        rows = FileUtils.read_jsonl(path=jsonl_file)
        legal_qa_jsonl_rows.extend(rows)
        columns.update(rows[0].keys() if rows else [])

    for csv_file in csv_files:
        rows = FileUtils.read_csv(path=csv_file)
        legal_qa_csv_rows.extend(rows)
        columns.update(rows[0].keys() if rows else [])

    for url_file in url_files:
        rows = FileUtils.read_csv(path=url_file)
        url_rows.extend(rows)

    print(f"[INFO] {len(url_rows)} rows from {len(url_files)} URL CSV files")

    # loại bỏ hàng trùng với url
    before_all_rows = legal_qa_csv_rows + legal_qa_jsonl_rows

    all_legal_qa_rows = []

    # before csv + jsonl
    length = len(before_all_rows)
    print(
        f"[INFO] Merging {length} rows from {len(csv_files)} CSV files and {len(jsonl_files)} JSONL files"
    )

    url_set = set()

    for row in before_all_rows:
        # map topic và category là thành category, nếu chưa có topic thì dùng category, nếu chưa có category thì dùng topic
        if row.get("topic") and not row.get("category"):
            row["category"] = row.get("topic")
        elif not row.get("topic") and row.get("category"):
            row["topic"] = row.get("category")

        # map lại vì category hardcode là "Dân sự" nên sẽ bị mất category, nên map lại từ topic
        row["category"] = row.get("topic")

        # remove duplicate rows based on URL
        if row.get("url") not in url_set:
            all_legal_qa_rows.append(row)
        url_set.add(row.get("url"))

    length_after = len(all_legal_qa_rows)
    print(f"[INFO] After removing duplicates with URL CSV, {length_after} rows remain")

    # write merged CSV and JSONL files
    columns_list = list(columns)
    print("[INFO] Columns: ", columns_list)
    FileUtils.write_csv(
        path=final_csv_path, rows=all_legal_qa_rows, columns=columns_list
    )
    FileUtils.write_jsonl(path=final_jsonl_path, rows=all_legal_qa_rows)

    url_columns = list(dict.fromkeys(key for row in url_rows for key in row.keys()))

    FileUtils.write_csv(path=final_url_csv_path, rows=url_rows, columns=url_columns)

    print(
        f"[INFO] Merged CSV written to {final_csv_path}, JSONL written to {final_jsonl_path}, URL CSV written to {final_url_csv_path}"
    )

    # pandas
    # statistics: category,
    df = pd.DataFrame(all_legal_qa_rows)
    print("Số danh mục: ", df.groupby("category").size())


if __name__ == "__main__":

    print("[INFO] Merging VNExpress and LuatVietnam data", flush=True)
    merge_vnexpress(
        output_path="output/vnexpress",
        recovered_path="output/vnexpress_recovered",
        prefix_final_file_name="all_legal_qa",
    )

    print("[INFO] Merging LuatVietnam data", flush=True)
    merge_lvn(
        output_path="output/luatvietnam",
        prefix_final_file_name="all_legal_qa",
    )


# run: python merge_vnexpress.py
