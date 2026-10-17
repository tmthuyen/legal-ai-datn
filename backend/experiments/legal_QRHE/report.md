# Kết quả đánh giá task: Legal_QRHE

- Người thực hiện: Trần Minh Thuyên
- Thời gian: 15/10/2026
- Thông tin mô hình:

- Link dataset: [ViLegal-QRHE-Dataset](https://huggingface.co/datasets/tmtdev/ViLegal-QRHE-Dataset)

- Cách tạo dữ liệu:
  - Sinh từ cấu trúc trong các văn bản đã tách phân cấp
  - Duyệt và lựa chọn tổ hợp ngẫu nhiên

- Thống kê số lượng
  |Name|Size|
  |---|---|
  |train|8438|
  |val|1055 |
  |test|1055 |

- Kểt quả đánh giá trên tập test:
  |metric|score_percent| description|
  |---|---|---|
  |valid_json|100.00| Kiểm tra định dạng JSON của đầu ra |
  |correct_keys|100.00| Kiểm tra các khóa đúng trong đầu ra |
  |output_format_ok|100.00| Kiểm tra định dạng đầu ra |
  |output_exact_match|99.91| So khớp chính xác với đáp án |

- Phương pháp đánh giá:
  |method| performance|
  |---|---|
  |từng query lần lượt | Trung bình 8.0s/query |
  |Theo batch (batch_size=32) | Trung bình 0.5s/query |
