# Phục hồi các bài VnExpress có câu hỏi và trả lời ở hai trang

File mới `recover_vnexpress_errors.py` là script độc lập, dùng `requests` và `BeautifulSoup`, **không cần Playwright/Chromium**. Mã tái sử dụng các hàm ghi JSONL/CSV và chuẩn URL của `crawl_vnexpress.py`; do đó đặt hai file cùng thư mục.

## Chạy

```powershell
pip install -r requirements.txt
python recover_vnexpress_errors.py --input-dir output/vnexpress --out output/vnexpress_recovered --delay 2
```

Các file cần có trong `output/vnexpress` từ lần chạy trước:

- `crawl_errors.jsonl` (hoặc `crawl_errors.json`): danh sách `{ "url": "...", "error": "..." }`
- `legal_qa.jsonl`: bài thành công để tránh phục hồi trùng ID. Nếu có nhiều file thành công, chỉ định thêm `--successes path/to/another.jsonl`.

Nếu file lỗi được lưu nơi khác, thêm `--errors path/to/crawl_errors.jsonl`.

## Kết quả độc lập

- `output/vnexpress_recovered/recovered_qa.jsonl`: dữ liệu Q&A phục hồi thành công, cùng các key của crawler trước, có thêm `answer_url`, `recovery_method`.
- `output/vnexpress_recovered/recovered_qa.csv`: cùng dữ liệu ở dạng bảng.
- `output/vnexpress_recovered/recovery_errors.jsonl`: những URL không phục hồi được hoặc lỗi HTTP.

Không chỉnh sửa `output/vnexpress/legal_qa.jsonl`, không ghi đè các URL đã thành công. Script loại trùng theo ID số trong URL (ví dụ `4939371`), chứ không chỉ so sánh chuỗi URL, vì `4939371.html` và `4939371-p2.html` là **một bài**.

**Luồng:** đọc errors -> loại ID thành công -> tải trang câu hỏi -> tìm link `-p2.html` trong HTML (nếu không thấy thì thử URL suy ra) -> tải p2 -> tách câu trả lời -> ghép với câu hỏi gốc -> xuất JSONL/CSV riêng.

## Ghi chú nghiên cứu

`citation` trích bằng regex từ `answer`, không phải căn cứ đã kiểm chứng. `relevant_law` vẫn là mảng rỗng đối với VnExpress nếu không có dữ liệu văn bản liên quan được công bố trong trang. Phải đối chiếu luật gốc nếu dùng làm nhãn huấn luyện.

Không phải tất cả `crawl_errors` đều xuất phát từ bài tách hai trang. Các lỗi mạng, bài không tồn tại, hoặc layout khác sẽ nằm trong `recovery_errors.jsonl` thay vì tạo ra Q&A giả. Tôn trọng điều khoản sử dụng của nguồn, tốc độ truy vấn hợp lý và quyền sử dụng nội dung.
