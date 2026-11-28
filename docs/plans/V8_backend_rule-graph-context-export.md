# V8 — Đọc rule và lấy thông tin node liên quan từ Graph

> **Trạng thái:** Hoàn thành; script đã được chạy kiểm tra với Neo4j.
> **Người thực hiện:** Copilot
> **Thời gian:** 2026-11-28
> **Phạm vi:** Chỉ một script trong `backend/scripts/`; không sửa source code trong `backend/src/`.

## Mục tiêu

Tạo đầu ra JSON đầy đủ, có thể dùng để chuẩn bị dữ liệu huấn luyện, giữ nguyên liên kết giữa rule và các node luật được rule tham chiếu. Script chỉ đọc dữ liệu; không thực thi suy luận, không sinh kết luận pháp lý, không huấn luyện model và không sửa rule/Graph.

## Yêu cầu script

**File dự kiến:** `backend/scripts/inspect_legal_rules.py`

Script hỗ trợ hai chế độ:

1. **Đọc toàn bộ rule** (`--all`): đọc các rule trong `backend/data/rules/*.json`; với mỗi rule, giữ nguyên JSON rule và lấy các node liên quan theo `source.node_ids` cùng `links[].source_node_id`. Đầu ra ánh xạ từng rule tới dữ liệu node và citation lấy từ Neo4j. Không bổ sung phần diễn giải predicate/catalog vào chế độ này.
2. **Đọc một rule** (`--rule-id <ID>`): trả rule được chọn với đầy đủ cấu trúc `when`, `unless`, `then`, `links`, `source` và metadata; kèm định nghĩa các predicate rule sử dụng từ `catalogs/predicates.json`, mô tả `kind`/`effect` từ `catalogs/effects.json`, các explanation templates từ `catalogs/explanations.json`, và thông tin/citation các node liên quan từ Neo4j.

Hai chế độ ghi JSON ra file đích do người dùng chọn; nếu không chỉ định thì chế độ đọc tất cả và đọc một rule dùng hai file mặc định riêng trong `backend/data/processed/` để không ghi đè đầu ra của nhau. Node ID trùng chỉ truy vấn một lần. Node không tìm thấy phải được giữ trong output và đánh dấu rõ, không tự đoán nội dung. Script dùng các graph client/repository/service hiện có để đọc Graph, lấy backend directory từ `FileUtil.get_project_root()` và mô tả cách chạy, ví dụ, options cùng tham số trong `--help`.

Script dùng các graph client/repository/service hiện có để tra cứu. Toàn bộ phần đọc rule, ghép dữ liệu và CLI được đặt trong script; không nạp embedding/model.

## Các phase

| Phase | Công việc | Trạng thái |
|---|---|---|
| 0 | Khảo sát toàn bộ rule files, catalogs, schemas và API graph hiện có | Hoàn thành |
| 1 | Chốt cấu trúc JSON đầu ra và cách chọn rule (`--all` / `--rule-id`) | Hoàn thành |
| 2 | Viết script cho chế độ đọc toàn bộ rule, map rule nguyên bản với node/citation | Hoàn thành |
| 3 | Bổ sung chế độ một rule, predicate/kind/effect descriptions và explanation templates | Hoàn thành |
| 4 | Kiểm thử output/missing node và smoke test khi Neo4j khả dụng | Hoàn thành; live run tìm thấy 20 tham chiếu thiếu thuộc 14 node HNGĐ trong graph hiện tại |

Đã chạy `scripts/test_reasoning.py`: 45/45 rule validation và 76/76 fixture. Smoke test Neo4j cho hai chế độ được ghi nhận ở trên.

## Tiêu chí nghiệm thu

- Chế độ `--all` giữ nguyên từng rule và gắn đúng node/citation theo ID nguồn và link.
- Chế độ `--rule-id` xuất đầy đủ rule, predicate definitions liên quan, mô tả kind/effects, explanation templates và node data.
- Cả hai chế độ xuất JSON có cấu trúc; node không tồn tại được đánh dấu; không thay đổi rule/Graph và không tự suy luận kết luận.
- Hướng dẫn `--help` nêu rõ cách chạy, từng option, giá trị mặc định và ví dụ.
- Đã chạy live với Neo4j: chế độ một rule lấy đủ 6/6 node cho `BLDS_D117_K1_01`; chế độ toàn bộ xử lý 45 rule, đánh dấu rõ các node tham chiếu HNGĐ không tồn tại trong graph hiện tại.

## Ngoài phạm vi

- Đánh giá/thi hành `when` hoặc `unless`, fact extraction, counterfactual, sinh tư vấn hay kết luận pháp lý.
- Huấn luyện model hoặc tạo thêm script audit/export riêng.
