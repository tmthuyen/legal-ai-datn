# Document Parser & Transform Graph Node

Tài liệu mô tả chi tiết hai notebook:
- `backend/notebooks/01_parse_data.ipynb` — Parse văn bản luật (.docx) thành cấu trúc cây phân cấp.
- `backend/notebooks/02_transform.ipynb` — Transform cấu trúc cây thành đồ thị tri thức (Knowledge Graph) gồm `nodes` và `relations`.

Mục tiêu: hiểu rõ **quy tắc parse**, **quy ước đặt ID node**, **các mapping** và **cách xây dựng quan hệ đồ thị**.

---

## 1. Tổng Quan Pipeline

```
DOCX (.docx)
   │  read_docx + chuan_hoa_text
   ▼
Cây cấu trúc (dataclass VanBan)          ← Notebook 01 (Config-Driven Parser)
   │  van_ban.to_dict()
   ▼
du_lieu_phap_luat.json
   │  traverse_tree_recursive + extract_references + extract_document_level_relations
   ▼
nodes.json / relations.json / unresolved_*.json   ← Notebook 02 (Transform)
```

Toàn bộ hai notebook đều **Config-Driven**: hành vi parser và resolver được điều khiển bởi hai file JSON:
- `backend/data/documents_config.json` — danh mục văn bản + metadata + aliases + relations khai báo.
- `backend/data/parser_profiles.json` — bộ regex nhận diện cấu trúc theo từng loại văn bản.

---

## 2. Notebook 01 — Parse Văn Bản Luật (`01_parse_data.ipynb`)

### 2.1. Cấu hình & đường dẫn

| Hằng số | Giá trị |
|---|---|
| `BASE_DIR` | `../data` |
| `CONFIG_PATH` | `../data/documents_config.json` |
| `PROFILES_PATH` | `../data/parser_profiles.json` |
| `OUTPUT_PATH` | `../data/du_lieu_phap_luat.json` |

`documents_config.json` là mảng 5 văn bản: `HIEN_PHAP_2013`, `BLDS_2015`, `ND_21_2021`, `ND_19_2019`, `NQ_02_2022`.
`parser_profiles.json` chứa 3 profile: `default`, `nghi_dinh`, `nghi_quyet`.

### 2.2. Đọc và chuẩn hóa văn bản

**`read_docx(file_path) -> str`**
- Dùng `python-docx` duyệt từng paragraph.
- Trích text bằng XPath `.//w:t` để lấy cả text nằm trong `w:smartTag` (đệ quy).
- Nối các paragraph bằng `\n`.

**`chuan_hoa_dong(line) -> str`** — chuẩn hóa 1 dòng:
- Loại bỏ BOM `\ufeff`.
- Sửa ký tự Latin Eth bị lỗi: `\u00d0` → `Đ`, `\u00f0` → `đ`.
- Chuẩn hóa Unicode **NFC** (`unicodedata.normalize`).
- Gộp khoảng trắng/tab dư (`[ \t]+` → ` `) và `strip()`.

**`chuan_hoa_text(text) -> List[str]`**
- Đổi `\r\n`, `\r` → `\n`.
- Tách dòng, chuẩn hóa từng dòng, **bỏ dòng rỗng**, trả list dòng sạch.

### 2.3. Mô hình dữ liệu (Dataclass)

Cây phân cấp được mô hình hóa bằng các dataclass, mỗi class có `to_dict()` và field `"loai"`:

| Dataclass | Trường | `loai` |
|---|---|---|
| `Diem` | `so: str`, `noi_dung` | `diem` |
| `Khoan` | `so: int`, `noi_dung`, `cac_diem: list[Diem]` | `khoan` |
| `Dieu` | `so: int`, `tieu_de?`, `noi_dung?`, `cac_khoan: list[Khoan]` | `dieu` |
| `TieuMuc` | `so: str`, `ten`, `cac_dieu: list[Dieu]` | `tieu_muc` |
| `Muc` | `so: str`, `ten`, `cac_tieu_muc`, `cac_dieu` | `muc` |
| `Chuong` | `so: str`, `ten`, `cac_muc`, `cac_tieu_muc`, `cac_dieu` | `chuong` |
| `Phan` | `so: str`, `ten`, `cac_chuong`, `cac_dieu` | `phan` |
| `VanBan` | `ten`, `loai_van_ban?`, `so_van_ban?`, `phan_mo_dau: list[str]`, `cac_phan`, `cac_chuong`, `cac_dieu`, `phan_ket_thuc: list[str]` | `van_ban` |

> Lưu ý: Mỗi container có thể chứa con trực tiếp của nhiều tầng khác nhau (ví dụ `Chuong` có thể chứa `cac_muc`, `cac_tieu_muc`, `cac_dieu`) vì thực tế văn bản luật Việt Nam không đồng nhất về tầng bậc.

### 2.4. Engine `ParserVanBanPhapLuat` (Config-Driven)

**Khởi tạo:**
- Biên dịch các regex từ `profile["patterns"]` với cờ `re.IGNORECASE` → `self.compiled_patterns`.
- Đọc `title_on_next_line` (các tầng mà tiêu đề nằm ở dòng kế tiếp) và `hierarchy`.
- Biên dịch `pat_postamble` = regex nhận diện phần kết thúc/chứng thực:
  `^(?:(?:Hiến pháp này|Bộ luật này|Luật này)\s+đã được\s+Quốc hội.*thông qua)`
- Giữ **con trỏ trạng thái** cho tầng hiện tại: `phan_hien_tai`, `chuong_hien_tai`, `muc_hien_tai`, `tieu_muc_hien_tai`, `dieu_hien_tai`, `khoan_hien_tai`, `diem_hien_tai`, và cờ `da_ket_thuc_quy_pham`.

**Vòng lặp `parse(text)`** — thứ tự ưu tiên nhận diện từng dòng:

1. Nếu `da_ket_thuc_quy_pham` → gom vào `phan_ket_thuc`, bỏ qua.
2. Nếu khớp `pat_postamble` → bật `da_ket_thuc_quy_pham`, reset các con trỏ Điều/Khoản/Điểm, gom vào `phan_ket_thuc`.
3. Nếu đang `waiting_for_title` → gán dòng hiện tại làm `ten` cho Chương/Phần vừa tạo (tiêu đề xuống dòng).
4. `phan` → `_tao_phan`
5. `chuong` → `_tao_chuong`
6. `muc` → `_tao_muc`
7. `tieu_muc` → `_tao_tieu_muc`
8. `dieu` → `_tao_dieu`
9. `khoan` (chỉ khi đã có `dieu_hien_tai`) → `_tao_khoan`
10. `diem` (chỉ khi đã có `khoan_hien_tai`) → `_tao_diem`
11. Còn lại → `_them_noi_dung` (gom text đa dòng).

**Quy tắc gắn node vào cha (parent attachment):**

| Hàm tạo | Node được gắn vào |
|---|---|
| `_tao_phan` | `VanBan.cac_phan` |
| `_tao_chuong` | `Phan.cac_chuong` nếu có Phần, ngược lại `VanBan.cac_chuong` |
| `_tao_muc` | `Chuong.cac_muc` |
| `_tao_tieu_muc` | `Muc.cac_tieu_muc`, nếu không có Mục thì `Chuong.cac_tieu_muc` |
| `_tao_dieu` | Ưu tiên `TieuMuc` → `Muc` → `Chuong` → `Phan` → `VanBan.cac_dieu` |
| `_tao_khoan` | `Dieu.cac_khoan` (bắt buộc đã có Điều) |
| `_tao_diem` | `Khoan.cac_diem` (bắt buộc đã có Khoản) |

**Quy tắc gom nội dung `_them_noi_dung(line)`:**
- Nếu **chưa có Điều**: nối vào `ten` của `TieuMuc`/`Muc`/`Chuong`/`Phan` (tiêu đề đa dòng); nếu không tầng nào → `VanBan.phan_mo_dau` (phần mở đầu).
- Nếu đã có Điều: ưu tiên nối vào `Diem.noi_dung` → `Khoan.noi_dung` → `Dieu.noi_dung` (đoạn mở đầu của Điều, tức text giữa tiêu đề Điều và Khoản 1).

### 2.5. Parser Profiles — Regex nhận diện từng tầng

**`default`** (Bộ luật & Hiến pháp — có đủ Phần/Chương La Mã/Mục/Tiểu mục):

| Tầng | Regex |
|---|---|
| `phan` | `^Phần\s+(?P<so>.+?)(?:\.\s*(?P<ten>.*))?$` |
| `chuong` | `^Chương\s+(?P<so>[IVXLCDM]+)(?:\.\s*(?P<ten>.*))?$` |
| `muc` | `^Mục\s+(?P<so>\d+)(?:\.\s*(?P<ten>.*))?$` |
| `tieu_muc` | `^Tiểu mục\s+(?P<so>\d+)(?:\.\s*(?P<ten>.*))?$` |
| `dieu` | `^Điều\s+(?P<so>\d+)(?:\.\s*(?P<tieu_de>.*))?$` |
| `khoan` | `^(?P<so>\d+)\.\s+(?P<noi_dung>.+)$` |
| `diem` | `^(?P<so>[a-zđ])\)\s+(?P<noi_dung>.+)$` |

- `title_on_next_line`: `["phan", "chuong"]` → tiêu đề Phần/Chương thường ở dòng sau.
- `hierarchy`: `phan → chuong → muc → tieu_muc → dieu → khoan → diem`.

**`nghi_dinh`** (Nghị định — không có Phần; Chương có thể La Mã **hoặc** số Ả Rập):
- `phan = null`.
- `chuong`: `^Chương\s+(?P<so>[IVXLCDM]+|\d+)(?:\.\s*(?P<ten>.*))?$`
- `muc`, `tieu_muc`: dùng `(?:[:.]\s*(?P<ten>.*))?` (chấp nhận cả `:` và `.`).
- `dieu`, `khoan`, `diem` giống default.
- `title_on_next_line`: `["chuong"]`.
- `hierarchy`: `chuong → muc → tieu_muc → dieu → khoan → diem`.

**`nghi_quyet`** (Nghị quyết — đi thẳng Điều → Khoản → Điểm):
- `phan`, `chuong`, `muc`, `tieu_muc` đều `null`.
- Chỉ có `dieu`, `khoan`, `diem`.
- `hierarchy`: `dieu → khoan → diem`.

### 2.6. Diagnostics & Validation (Notebook 01)

**`count_nodes_and_validate(item, stats, article_numbers)`** — duyệt đệ quy mọi list `cac_*`:
- Đếm số lượng node theo `loai`.
- Cảnh báo: Điều không có nội dung (`dieu_khong_co_noi_dung`), Điều có đoạn mở đầu (`dieu_co_noi_dung_mo_dau`), Khoản/Điểm rỗng, tên Chương/Mục/Tiểu mục/Phần rỗng.

**`check_unparsed_candidate_headings(raw_lines, profile)`** — phát hiện tiêu đề khả nghi **không khớp** regex profile:
- Regex ứng viên: `^(Điều|Khoản|Điểm|Chương|Mục|Tiểu mục|Phần)\s+(\d+|[IVXLCDM]+|[a-zđ]\)|thứ)\s`.

**`validate_source_coverage(raw_lines, cau_truc, profile)`** — Source-to-Nodes Coverage Validator:
- Với mỗi Điều trong DOCX, gom các dòng giữa tiêu đề Điều và Khoản 1 (đoạn mở đầu).
- Nếu có dòng mở đầu nhưng `dieu.noi_dung` trống trong cấu trúc parse → cảnh báo thất thoát.

**`run_diagnostics(results, profiles, raw_texts)`** — tổng hợp báo cáo mỗi văn bản:
- Số lượng node theo tầng.
- Cảnh báo: không có Điều nào, Điều không nội dung, **trùng số Điều**, **nhảy số Điều bất thường** (so sánh với dãy `1..N`), tiêu đề khả nghi chưa parse, source coverage.

### 2.7. Hàm `main()` — luồng chạy

1. Với mỗi `cfg` trong `documents_config`: lấy `document_id`, `file_path`, `parser_profile`, `metadata`.
2. Đọc `.docx` → parse → dựng dict kết quả:
   ```json
   {
     "document_id": "...",
     "parser_profile": "...",
     "metadata": { ... , "document_id": "..." },
     "cau_truc": { ...VanBan.to_dict() }
   }
   ```
3. Chạy `run_diagnostics`, in báo cáo chất lượng.
4. Ghi ra `du_lieu_phap_luat.json` (`ensure_ascii=False`, `indent=2`).

**Kết quả thực tế (5 văn bản):**

| Văn bản | Phần | Chương | Mục | Tiểu mục | Điều | Khoản | Điểm |
|---|---|---|---|---|---|---|---|
| HIEN_PHAP_2013 | 0 | 11 | 0 | 0 | 120 | 244 | 0 |
| BLDS_2015 | 6 | 27 | 39 | 23 | 689 | 1418 | 312 |
| ND_21_2021 | 0 | 5 | 2 | 8 | 62 | 158 | 77 |
| ND_19_2019 | 0 | 5 | 2 | 0 | 28 | 82 | 67 |
| NQ_02_2022 | 0 | 0 | 0 | 0 | 13 | 38 | 31 |

Tất cả đạt `100% HỢP LỆ` (không cảnh báo cấu trúc).

---

## 3. Notebook 02 — Transform Cấu Trúc Thành Đồ Thị (`02_transform.ipynb`)

### 3.1. Cấu hình đường dẫn

| Hằng số | Giá trị |
|---|---|
| `CONFIG_FILE` | `../data/documents_config.json` |
| `INPUT_FILE` | `../data/du_lieu_phap_luat.json` |
| `OUTPUT_DIR` | `../data/processed` |

### 3.2. Chuẩn hóa số thứ tự (`normalize_number`)

Chuyển số Ả Rập / số La Mã / từ thứ tự tiếng Việt về **số nguyên**:

- `VIETNAMESE_ORDINALS`: `nhất/thứ nhất→1`, `hai/thứ hai→2`, ... `mười/thứ mười→10`.
- `ROMAN_NUMERALS`: `I→1`, `II→2`, ... `XXX→30`.
- `isdigit()` → `int`; nếu không khớp → giữ nguyên chuỗi.

### 3.3. Mapping `loai` → `type` node đồ thị

```python
LOAI_TO_TYPE = {
    'van_ban':  'Document',
    'phan':     'Part',
    'chuong':   'Chapter',
    'muc':      'Section',
    'tieu_muc': 'SubSection',
    'dieu':     'Article',
    'khoan':    'Clause',
    'diem':     'Point',
}
```

`CHILD_KEYS` — các key chứa danh sách con được duyệt:
`['cac_phan','cac_chuong','cac_muc','cac_tieu_muc','cac_dieu','cac_khoan','cac_diem','children']`
(hoặc bất kỳ key nào bắt đầu bằng `cac_` và là list).

### 3.4. Quy ước đặt ID (`node_id`)

| Cấp | Mẫu `node_id` | Ví dụ |
|---|---|---|
| Document | `{DOC_ID}` | `BLDS_2015` |
| Part (Phần) | `{DOC_ID}_P{n}` | `BLDS_2015_P1` |
| Chapter (Chương) | `{DOC_ID}[_P{part}]_CH{n}` | `BLDS_2015_P1_CH3` |
| Section (Mục) | `{DOC_ID}[_CH{ch}]_M{n}` | `BLDS_2015_CH13_M1` |
| SubSection (Tiểu mục) | `{DOC_ID}[_CH{ch}][_M{m}]_TM{n}` | `BLDS_2015_CH13_M1_TM1` |
| Article (Điều) | `{DOC_ID}_D{n}` | `BLDS_2015_D584` |
| Clause (Khoản) | `{DOC_ID}_D{dieu}_K{khoan}` | `BLDS_2015_D584_K1` |
| Point (Điểm) | `{DOC_ID}_D{dieu}[_K{khoan}]_DIEM_{a}` | `BLDS_2015_D584_K1_DIEM_A` |
| Fallback | `{DOC_ID}_{LOAI.upper()}_{so}` | — |

**Điểm mấu chốt:**
- SubSection gắn context cha (`_CH.._M.._TM`) để đảm bảo **duy nhất toàn cục**.
- Điểm dùng tiền tố `DIEM_` để **tránh nhầm với Điều** (cùng ký tự `D`).
- Chữ cái Điểm được viết hoa (`str(raw_so).strip().upper()`).

### 3.5. Thuật toán duyệt cây đệ quy — `traverse_tree_recursive`

Chữ ký:
```python
traverse_tree_recursive(item, parent_id, doc_id, context, nodes, contains_relations, seen_node_ids=None)
```

Đặc điểm:
- **Không phụ thuộc độ sâu cố định** — tự nhận diện mọi list con (`CHILD_KEYS` hoặc key bắt đầu `cac_`).
- **Bảo toàn ngữ cảnh cha con**: truyền `context` gồm `part_so`, `chuong_so`, `muc_so`, `dieu_so`, `khoan_so` xuống con để sinh ID.
- **Chống trùng ID**: nếu `node_id` đã tồn tại trong `seen_node_ids`, thêm hậu tố `_2`, `_3`, ... (V1 uniqueness).
- **Tự tạo quan hệ cấu trúc**: mỗi node con (trừ gốc Document) sinh một relation:
  ```
  {source_id: parent_id, type: 'CONTAINS', target_id: current_node_id,
   evidence: "<parent> CONTAINS <child>", source_type: 'STRUCTURAL', confidence: 1.0}
  ```
- **Chuẩn hóa Unicode** ở node: đổi `Ð → Đ`, `ð → đ` cho `title` và `text`.

**Cấu trúc node xuất ra:**
```json
{
  "node_id": "...",
  "document_id": "...",
  "type": "Article",
  "label": "Article",
  "number": 584,
  "title": "...",
  "text": "...",
  "parent_id": "..."
}
```

**Sinh `full_text` cho Article** (tối ưu cho Embedding/GraphRAG):
- Gộp theo thứ tự: `title` → `text` (đoạn mở đầu Điều) → từng `Khoản {k}. {nội dung}` → từng `Điểm {p}) {nội dung}`.
- Nối bằng `\n`; nếu rỗng thì `None`.

### 3.6. Trích xuất dẫn chiếu pháp lý (`REFERENCES`)

Module `relation_parser.py` (trong cell) trích quan hệ ngữ nghĩa từ nội dung node.

**`get_evidence(text, start, end, window=35)`** — lấy ngữ cảnh ±35 ký tự quanh vị trí dẫn chiếu, thêm `...` nếu bị cắt.

**`DocumentAliasRegistry`** — ánh xạ alias → `document_id`:
- Alias tự sinh từ `metadata.ten_van_ban` và `metadata.so_hieu` (bỏ qua `"Không số"`).
- Alias khai báo thủ công trong `cfg["aliases"]`.
- Sắp xếp **alias dài hơn khớp trước** để tránh nhầm tiền tố.
- `resolve(text, start, end, current_doc_id)` dùng **Positional Competition** (90 ký tự sau dẫn chiếu, giới hạn trong cùng mệnh đề tách bởi `; . \n`):
  1. Từ khóa nội bộ (`luật này`, `bộ luật này`, `nghị định này`, ...) → `current_doc_id`.
  2. Alias trong corpus → document tương ứng.
  3. Dấu hiệu văn bản ngoài corpus (`của Luật/Bộ luật/...` không phải "này", hoặc `Luật ... số ...`) → trả `None` (**chống false edge**).
  4. Cuối cùng: mặc định `current_doc_id`.

**Các Pattern trích `REFERENCES` trong `extract_references`:**

| # | Pattern | Mô tả |
|---|---|---|
| 1 | `range_dieu_rx` | `từ Điều X đến (Điều) Y` (chỉ khi `Y-X ≤ 50`) → sinh liên tiếp |
| 2 | `list_diem_rx` | `các điểm a, b và c (khoản K) Điều X` |
| 3 | `list_khoan_rx` | `khoản 1, 2 và 3 Điều X` |
| 4 | `list_dieu_rx` | `Điều 1, 2 và 3` |
| 5 | `internal_dieu_rx` | `(điểm a) (khoản K) của Điều này` → map về Điều hiện tại |
| 5b | `internal_khoan_rx` | `điểm a khoản này` → map Điểm cùng Khoản/Điều hiện tại |
| 6 | `single_ref_rx` | `(điểm a) (khoản K) Điều X` |
| 7 | `ch_rx` | `Chương <La Mã>` → trỏ node Chapter |
| 8 | `part_rx` | `Phần thứ ...` → trỏ node Part |
| 9 | `part_nay_rx` | `quy định của Phần này` → trỏ tổ tiên Part gần nhất |
| 10 | (phan_mo_dau) | Dẫn chiếu Chương trong `phan_mo_dau` của Document |

**Cơ chế Candidate Fallback** (target specificity): với mỗi dẫn chiếu, thử lần lượt các candidate theo độ đặc hiệu giảm dần, chọn candidate **đầu tiên tồn tại** trong `node_id_set`:
```
{...}_D{d}_K{k}_DIEM_{a}  →  {...}_D{d}_DIEM_{a}  →  {...}_D{d}_K{k}  →  {...}_D{d}
```

**Khử trùng lặp & gộp evidence**: key `(source_id, type, target_id)`; nếu trùng thì nối evidence bằng `" | "`.

**Lọc độ đặc hiệu**: bỏ REFERENCES trỏ tới Điều nếu tồn tại REFERENCES cùng source trỏ tới node con chi tiết hơn (`{tid}_...`).

Mọi quan hệ REFERENCES có `source_type='EXPLICIT'`, `confidence=1.0`.

### 3.7. Quan hệ cấp văn bản

**`extract_document_level_relations`** — quan hệ **nội bộ corpus**:
- `[:IMPLEMENTS]`: `[Nghị định/Thông tư thi hành] → [Luật/Bộ luật được thi hành]`.
  - Lấy từ khai báo `cfg["relations"]`.
  - Hoặc tự động từ tiêu đề: regex `(quy định chi tiết|quy định thi hành|hướng dẫn thi hành|thi hành)` rồi dò alias.
- `[:INTERPRETED_BY]`: `[Luật/Bộ luật được hướng dẫn] → [Nghị quyết hướng dẫn]`.
  - Tự động **đảo chiều** nếu config khai `source_id` là nghị quyết: `source, target = target, source`.

**`extract_unresolved_document_relations`** — quan hệ hướng **ra ngoài corpus** (từ `cfg["external_relations"]`), gắn `status='EXTERNAL_DOCUMENT_RELATION'`:
- `[:REPEALS]`, `[:REPLACED_BY]`, `[:REFERENCES]`, `[:AMENDS]`, ...
- Giữ `target_name`, `target_so_hieu`, `evidence`, `evidence_type`.

`unresolved_references` (cấp node) lưu các dẫn chiếu bị chặn (văn bản ngoài corpus) với `reason='EXTERNAL_DOCUMENT'`.

### 3.8. Bộ kiểm định đồ thị V1 — V9 (`validate_graph`)

| Mã | Tên | Kiểm tra |
|---|---|---|
| V1 | `DUPLICATE_NODE_ID` | Mọi `node_id` duy nhất (error) |
| V2 | `ORPHAN_NODE` | Mọi `parent_id` tồn tại trong nodes (error) |
| V3 | `DANGLING_SOURCE` | `source_id` của mọi relation tồn tại (error) |
| V4 | `DANGLING_TARGET_STRUCTURAL` | `target_id` của CONTAINS tồn tại (error) |
| V5 | `WARNING_DANGLING_REF` | `target_id` của REFERENCES/IMPLEMENTS/INTERPRETED_BY tồn tại (warning) |
| V6 | `INVALID_DOCUMENT_ID` | `document_id` nằm trong tập Document node (error) |
| V7 | `INVALID_RELATION_TYPE` | `type` thuộc whitelist (error) |
| V8 | `MISSING_EVIDENCE` | REFERENCES/IMPLEMENTS/INTERPRETED_BY có evidence không rỗng (error) |
| V9 | `SOURCE_COVERAGE_INTRO_PARAGRAPHS` | Điều có đoạn mở đầu trong raw phải có `text` và `text[:30]` xuất hiện trong `full_text` (error) |

**Whitelist relation type:**
`CONTAINS, REFERENCES, IMPLEMENTS, INTERPRETED_BY, AMENDS, REPEALS, REPLACED_BY, RELATED_TO`

### 3.9. Pipeline chạy (cell 5)

1. Đọc `du_lieu_phap_luat.json`.
2. Xây `DOC_METADATA` từ `documents_config.json` (title, number, type, issuer, effective_from/to, status, provenance).
3. Với mỗi văn bản: tạo **Document node gốc** (gồm metadata + provenance) rồi gọi `traverse_tree_recursive` để sinh toàn bộ node con.
4. `extract_references` → `REFERENCES` + `unresolved_references`.
5. `extract_document_level_relations` → `IMPLEMENTS`, `INTERPRETED_BY`.
6. `extract_unresolved_document_relations` → quan hệ ngoài corpus.
7. Gộp: `all_relations = CONTAINS + REFERENCES + doc_level_relations`.
8. `validate_graph` (V1–V9).
9. Ghi 4 file:
   - `nodes.json`
   - `relations.json`
   - `unresolved_references.json`
   - `unresolved_document_relations.json`

**Document node bổ sung các trường provenance:**
`document_type`, `issuer`, `effective_from`, `effective_to`, `status`,
`source_file`, `metadata_source`, `source_url`, `effective_from_source_url`,
`verified_at`, `verification_scope`, `status_verified_at`.

### 3.10. Kết quả thực tế

**Nodes: 3,472** (5 văn bản):

| Type | Số lượng |
|---|---|
| Clause | 1,940 |
| Article | 912 |
| Point | 487 |
| Chapter | 48 |
| Section | 43 |
| SubSection | 31 |
| Part | 6 |
| Document | 5 |

**Relations: 3,959**

| Type | Số lượng |
|---|---|
| CONTAINS | 3,467 |
| REFERENCES | 489 |
| IMPLEMENTS | 2 |
| INTERPRETED_BY | 1 |

- `unresolved_references` (node ngoài corpus): **2**
- `unresolved_document_relations` (document ngoài corpus): **12**
- Kiểm định V1–V8/V9: **ĐẠT CHUẨN 100%** (0 lỗi, 0 cảnh báo).

### 3.11. Kiểm thử thích ứng cấu trúc dị biệt (cell 7)

- Cấu trúc đầy đủ `Chương → Mục → Điều → Khoản → Điểm` (`mock_nq_a`).
- Cấu trúc rút gọn `Điều → Khoản → Điểm` (`mock_nq_b`).
- Kết quả: sinh đúng 8 node, 8 quan hệ CONTAINS → chứng minh thuật toán đệ quy ổn định với mọi độ sâu.

**Kiểm thử Document Resolver** (chống false edge):

| Câu mẫu | Văn bản hiện tại | Kỳ vọng | Kết quả |
|---|---|---|---|
| `Điều 338 của Bộ luật Dân sự` | ND_21_2021 | BLDS_2015 | OK |
| `Điều 15 Hiến pháp` | ND_21_2021 | HIEN_PHAP_2013 | OK |
| `Điều 10 của Nghị định số 21/2021/NĐ-CP` | NQ_02_2022 | ND_21_2021 | OK |
| `Điều này của Nghị định này` | ND_21_2021 | ND_21_2021 | OK |
| `khoản 1 Điều 12 của Luật Nhà ở năm 2014` | NQ_02_2022 | `None` (ngoài corpus) | OK |
| `khoản 18 Điều 3 của Luật Giao thông đường bộ năm 2008` | NQ_02_2022 | `None` | OK |
| `khoản 2 Điều 15 của Luật ABC` | BLDS_2015 | `None` | OK |
| `Điều 5 của Nghị định XYZ` | BLDS_2015 | `None` | OK |

### 3.12. Independent Audit Suite (cell 9)

Kiểm định độc lập trên các file JSON đã xuất (không import notebook):
- Xác nhận `3,472` nodes và `3,959` relations (đúng counter từng type).
- Kiểm tra không có triple trùng.
- Mọi node (trừ Document) có `parent_id` tồn tại và có quan hệ CONTAINS tương ứng.
- Mọi relation: endpoint tồn tại, không self-loop, `source_type ∈ {STRUCTURAL, EXPLICIT, MANUAL}`, `confidence == 1.0`.
- CONTAINS có `target.parent_id == source`; các relation khác có `evidence` không rỗng và không chứa `\n`.
- Tái tạo `full_text` của mỗi Article từ cây con → so khớp với `full_text` đã lưu (chuẩn hóa khoảng trắng). Đạt **912/912 Articles**.
- Đối chiếu **verbatim** evidence (ngoài corpus) với XML gốc `.docx` (đọc trực tiếp `word/document.xml`).
- Kiểm tra provenance metadata khớp `documents_config.json`; ràng buộc đặc thù Hiến pháp (`status=HET_HIEU_LUC_MOT_PHAN`, `number='Không số'`).
- Kết quả: **GO FREEZE V1** — đồ thị đạt chuẩn 100%.

---

## 4. Bảng Mapping Tổng Hợp

### 4.1. Tầng cấu trúc → Node đồ thị

| Tiếng Việt | `loai` | `type` | ID prefix |
|---|---|---|---|
| Văn bản | `van_ban` | `Document` | `{DOC_ID}` |
| Phần | `phan` | `Part` | `_P{n}` |
| Chương | `chuong` | `Chapter` | `_CH{n}` |
| Mục | `muc` | `Section` | `_M{n}` |
| Tiểu mục | `tieu_muc` | `SubSection` | `_TM{n}` |
| Điều | `dieu` | `Article` | `_D{n}` |
| Khoản | `khoan` | `Clause` | `_K{n}` |
| Điểm | `diem` | `Point` | `_DIEM_{a}` |

### 4.2. Quan hệ đồ thị

| Type | Chiều | Nguồn | source_type |
|---|---|---|---|
| `CONTAINS` | parent → child | Duyệt cây đệ quy | `STRUCTURAL` |
| `REFERENCES` | node → node | Trích dẫn trong title/text | `EXPLICIT` |
| `IMPLEMENTS` | Nghị định/Thông tư → Luật | Config / tiêu đề | `MANUAL` / `EXPLICIT` |
| `INTERPRETED_BY` | Luật → Nghị quyết | Config | `MANUAL` |
| `REPEALS` | Văn bản → văn bản cũ | `external_relations` | `MANUAL` |
| `REPLACED_BY` | Văn bản cũ → văn bản mới | `external_relations` | `MANUAL` |
| `AMENDS` | Văn bản sửa đổi → văn bản bị sửa | `external_relations` | `MANUAL` |
| `RELATED_TO` | (whitelist, chưa dùng tự động) | — | — |

---

## 5. Ví dụ Output

**Node (Article):**
```json
{
  "node_id": "BLDS_2015_D584",
  "document_id": "BLDS_2015",
  "type": "Article",
  "label": "Article",
  "number": 584,
  "title": "Bồi thường thiệt hại do nguồn nguy hiểm cao độ gây ra",
  "text": "Nguồn nguy hiểm cao độ bao gồm ...",
  "parent_id": "BLDS_2015_CH21_M1",
  "full_text": "..."
}
```

**Relation (REFERENCES):**
```json
{
  "source_id": "ND_21_2021_D10_K1",
  "type": "REFERENCES",
  "target_id": "BLDS_2015_D338",
  "evidence": "...theo quy định tại Điều 338 của Bộ luật Dân sự...",
  "source_type": "EXPLICIT",
  "confidence": 1.0
}
```

**Unresolved reference (node ngoài corpus):**
```json
{
  "source_id": "NQ_02_2022_D12_K1",
  "citation": "khoản 18 Điều 3",
  "evidence": "...theo quy định tại khoản 18 Điều 3 của Luật Giao thông đường bộ...",
  "reason": "EXTERNAL_DOCUMENT"
}
```

---

## 6. Điểm Thiết Kế Then Chốt

1. **Config-Driven**: Thêm loại văn bản mới chỉ cần thêm profile regex và config; không sửa code parser.
2. **Đệ quy tổng quát**: Không hard-code độ sâu; chịu được cấu trúc dị biệt giữa các văn bản.
3. **ID duy nhất toàn cục**: context cha chèn vào prefix + hậu tố `_2`, `_3` khi trùng.
4. **Chống false edge (Hallucination Prevention)**: Dẫn chiếu tới văn bản ngoài corpus → `None`/`unresolved`, không fallback sai về văn bản hiện tại.
5. **Bảo toàn đoạn mở đầu Điều**: `text` của Article giữ nguyên phần giữa tiêu đề Điều và Khoản 1; V9 kiểm tra không thất thoát.
6. **`full_text` cho Article**: Gộp title + text + Khoản + Điểm, phục vụ embedding/GraphRAG.
7. **Evidence chân thực**: Mọi quan hệ ngữ nghĩa lưu trích dẫn gốc; audit đối chiếu verbatim với DOCX XML.
