# Tóm Tắt Thay Đổi (Code Changes)

- **Cấu hình hóa toàn bộ pipeline (Config-Driven):**
  Tách toàn bộ thông tin văn bản ra `documents_config.json` và quy tắc nhận diện cấu trúc ra `parser_profiles.json`.

- **Nâng cấp bộ giải mã liên kết & chặn liên kết ảo (`02_transform.ipynb`):**
  - Tự động nhận diện tên gọi tắt, số hiệu và ngữ cảnh theo file cấu hình.
  - Chặn false edge: Dẫn chiếu luật ngoài corpus (Luật Nhà ở, Luật Giao thông đường bộ...) được chuyển vào `unresolved_references.json` thay vì tự ý đoán mò trỏ sai node.
  - Quét dẫn chiếu trong tiêu đề Điều: Bổ sung đủ 11 liên kết pháp lý quan trọng từ các Điều của NQ 02/2022 sang BLDS 2015.

- **Chuẩn hóa quan hệ cấp văn bản theo Ontology:**
  Đảo chiều chuẩn ngữ nghĩa `BLDS_2015 -[:INTERPRETED_BY]-> NQ_02_2022` và gán nhãn `source_type: "MANUAL"` cho các quan hệ do cấu hình xác nhận.
