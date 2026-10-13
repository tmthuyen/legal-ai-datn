# V1 — Truy xuất theo trích dẫn cấu trúc luật (Target Parsing → Validate → Graph Retrieval)

> Trạng thái: **Draft — chờ duyệt**
> Người thực hiện: dev
> Phạm vi: Bước 1 — từ câu hỏi có trích dẫn (Điều/Khoản/Điểm/Chương...) → parse cấu trúc → validate → truy vấn đồ thị lấy nội dung + luật liên quan + nguồn gốc tài liệu.

---

## 1. Mục tiêu

Cho câu hỏi tự nhiên có trích dẫn vị trí luật, hệ thống phải:

1. **Parse** câu hỏi thành cấu trúc JSON chuẩn hoá (document, part, chapter, section, subsection, article, clause, point)
2. **Validate** cấu trúc: có `document`, đúng thứ bậc cha ↔ con, giá trị từng cấp hợp lệ.
3. **Resolve** Đưa output (Nếu hợp lệ) xuống một node thực trên đồ thị Neo4j.
4. **Truy vấn nội dung luật** tại node đích (kèm tổ tiên/hậu duệ: Điều → Khoản → Điểm).
5. **Truy vấn luật liên quan** qua các quan hệ pháp lý (`REFERENCES`, `IMPLEMENTS`, `INTERPRETED_BY`, `AMENDS`, `RELATED_TO`...).
6. **Truy vết nguồn gốc tài liệu** (document gốc: file, số hiệu, ngày hiệu lực, trạng thái, URL nguồn) lấy trực tiếp từ node `Document` trên đồ thị.

### Ví dụ đầu vào / đầu ra mong muốn

Đầu vào (đã parse):

```json
{
  "input": "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
  "output": {
    "part": null,
    "chapter": "I",
    "section": null,
    "subsection": null,
    "article": null,
    "clause": null,
    "point": null,
    "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
  }
}
```

Đầu ra mong muốn (định hướng):

---

## 2. Phạm vi

**Trong phạm vi (V1):**

- Parse + validate + resolve + retrieval + provenance cho bộ 5 văn bản đang có trong corpus.
- Trả về cấu trúc JSON qua notebook (chưa cần API).
- Bao phủ các đường dẫn phân cấp: chương-only, điều-only, khoản, điểm, và tổ hợp.

**Ngoài phạm vi (để V2+):**

- Gọi LLM sinh câu trả lời cuối + diễn giải (đó là Bước 2 — reasoning).
- Kiểm chứng phản ví dụ / NLI / confidence (Bước 3).
- Fine-tune model parse câu hỏi (nếu chọn hướng LLM).
- Truy xuất semantic/vector (BGE-M3 + ChromaDB) — có thể thêm sau, V1 ưu tiên graph.

---

## 3. Luồng xử lý (Pipeline)

- Câu hỏi người dùng truy vấn luật (có trích dẫn vị trí luật)
- Model Legal Query Reference & Hierarchy Extraction sẽ trích xuất thông tin luật tham chiếu (tài liệu, chương, điều, khoản, điểm) ra JSON
- Kiểm trả cấu trúc phân cấp có hợp lệ hay không
- Nếu không hợp lệ chuyển sang quy trình khác để tìm kiếm tài liệu liên quan bằng các phương pháp khác
- Nếu có cấu trúc nhưng không thể xác định vị trí loại văn bản đã lưu trong Graph thì trả kết quả không tìm thấy thống tin. Cấm bịa đặt thông tin luật
- Nếu hợp lệ sẽ duyệt Graph tìm node tương ứng và liên quan, các mối quan hệ và đường dẫn thông tin luật rõ ràng: Luật nào, điều khoản điểm mục tiểu mục chương phần nào
- Trả kết quả truy vấn Graph đúng format và gửi cho model sau sử lý thông tin. Thông tin các node sẽ làm tin cậy kết quả phản hồi của hệ thống khi có trích dẫn rõ ràng
- Cấu trúc truy vấn graph trả về:

```json
{
  "input": "Chương I của Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013 quy định về vấn đề gì?",
  "extracted_hierarchy": {
    "part": null,
    "chapter": "I",
    "section": null,
    "subsection": null,
    "article": null,
    "clause": null,
    "point": null,
    "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
  },
  "related_documents": [
    {
      "document_id": "HIEN_PHAP_2013",
      "document_name": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
      "source_file": "...",
      "source_url": "...",
      "so_hieu": "...",
      "issuer": "...",
      "effective_from": "...",
      "effective_to": "...",
      "status": "...",
      "metadata_source": "...",
      "verified_at": "..."
      // các thông tin quan trọng khác
    }
  ],
  "related_nodes": [
    {
      "node_id": "HIEN_PHAP_2013_CH1",
      "parent_id": null,
      "level_path": "", // đường dẫn từ document đến node này (ví dụ: Part 1 | Chapter I | Section 1 | Subsection 1 | Article 1 | Clause 1 | Point 1)
      "level_node_id": "", // "HIEN_PHAP_2013 | HIEN_PHAP_2013_CH1 | HIEN_PHAP_2013_CH1_M1 | HIEN_PHAP_2013_CH1_M1_TM1 | HIEN_PHAP_2013_CH1_M1_TM1_D1 | HIEN_PHAP_2013_CH1_M1_TM1_D1_K1 | HIEN_PHAP_2013_CH1_M1_TM1_D1_K1_DIEM_A"
      "document_node_id": "HIEN_PHAP_2013",
      "document_name": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
      "type": "Chapter",
      "number": "I",
      "title": "Chương I: Những quy định chung",
      "content": "...",
      "metadata_source": "...",
      "verified_at": "..."
      // các  thông tin quan trọng khác
    }
  ]
}
```

---

## 4. Hiện trạng code (As-is)

| Thành phần                              | File                                                                             | Trạng thái                                  |
| --------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------- |
| Schema phân cấp + validate              | `src/common/schemas.py` (`LegalHierarchy`, `LegalHierarchyPatterns`, `validate`) | **Có** — validate cơ bản                    |
| Kết nối Neo4j                           | `src/graph/neo4j_client.py`                                                      | **Có**                                      |
| Repository/service graph                | `src/graph/graph_repository.py`, `graph_service.py`                              | **Có** — chỉ find-all & relationship cơ bản |
| Import graph                            | `graph/import_neo4j.py`                                                          | **Có** (đã nạp được)                        |
| Alias + provenance nguồn                | `data/documents_config.json` (aliases, metadata)                                 | **Có dữ liệu**, chưa có code đọc            |
| Resolve doc/node, retrieval, provenance | —                                                                                | **Chưa có**                                 |
| Notebook 04                             | `notebooks/04_retrieval.ipynb`                                                   | Đang sinh dataset truy xuất, chưa nối graph |

### Đặc điểm dữ liệu quan trọng (ràng buộc thiết kế)

- **node_id convention:** `HIEN_PHAP_2013`, `..._P1`, `..._CH1`, `..._CH3_M1`, `..._CH13_M1_TM1`, `..._D1`, `..._D2_K1`, `..._D27_K1_DIEM_A`.
- **CẢNH BÁO:** Chapter `number = "I"` nhưng `node_id = "..._CH1"` (đánh số tuần tự, KHÔNG theo số La Mã). ⇒ **Không nên tái tạo node_id bằng chuỗi**; phải resolve qua đồ thị.
- **Kiểu `number` không nhất quán:** `Article`/`Clause` là **int**, còn `Chapter`/`Section`/`SubSection`/`Point` là **string**. Cần chuẩn hoá khi so khớp.
- Quan hệ `CONTAINS` thể hiện cây phân cấp; node con có `parent_id`, node `Document` có `document_id`.
- Document node chứa đầy đủ provenance: `source_file`, `source_url`, `so_hieu`, `issuer`, `effective_from`, `effective_to`, `status`, `metadata_source`, `verified_at`.

---

## 5: Công việc (Task)

- Từ câu hỏi truy vấn người dùng, phân tích cấu trúc phân cấp
- Gửi query_text (input) và hierarchy (nếu có) xuống tầng tiếp theo
- Truy vấn graph từ cấu trúc phân cấp đã trích dẫn.
  - Tìm văn bản liên quan khớp document. Để dễ dàng truy vấn có node thuộc văn bản đỏ. Thu hẹp phạm vị tìm kiến. Trả về có trương related_documents
  - Nếu không ra document nào bắt buộc trả False | Lỗi | Cách tìm khác như Semantic Search với vector, ...
  - Xây dụng các Rule để thiết kế lại node_id cho phù hợp với cấu trúc đồ thị sau khi đã chọn document liên quan. Trả về related_nodes. Có path rõ ràng từ Document đến Node đó và Node cha (parent_id)
  - Từ các node liên quan mở rộng ra theo relationship hoặc truy xuống dưới các node con của mỗi node
  - Mỗi node sẽ có thêm relationships với các node_id khác và tên loại quan hệ
  - Trả về đúng format: input, extracted_hierarchy, related_documents, related_nodes (có relationships với nodes khác, và path cụ thể từ document đến node)
