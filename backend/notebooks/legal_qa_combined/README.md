# Thu thập hỏi đáp dân sự: VnExpress + LuatVietnam

## VnExpress (infinite scroll)

```
pip install -r requirements.txt
python -m playwright install chromium
python crawl_vnexpress.py --max-scrolls 150 --delay 2 --out output/vnexpress
```

- Duyệt danh sách `#list-news article.item-news h4.title-news a[href]`, cuộn cuối trang và chờ số lượng bài tăng. Dừng sau 3 lần liên tiếp không có URL mới (hoặc `--max-scrolls`). Lưu URL liên tục trước khi vào trang chi tiết.
- Chi tiết: `article.fck_detail`, `h1.title-detail`, `p.description`, các `p.Normal` trực tiếp thuộc article; phân tách ở `Luật sư tư vấn:`. Không lấy khảo sát, bảng, quảng cáo hay bình luận.
- `citation` được trích bằng regex từ câu trả lời, chỉ là ứng viên (`verified=false`). Regex không đảm bảo nhận diện mọi cách viện dẫn; cần bước NER + liên kết văn bản luật và kiểm chứng sau.
- `relevant_law` để [] khi VnExpress không có khối văn bản luật liên quan; không tự suy diễn từ trích dẫn.
- Giữ chuyên mục website và nhãn `civil_code_2015_scope=not_reviewed` để sau này loại các nội dung ngoài phạm vi nghiên cứu.
- `article_urls.jsonl/csv`, `legal_qa.jsonl/csv`, `crawl_errors.jsonl` có thể được dùng để kiểm tra lỗi hoặc chạy lại.

## LuatVietnam

```
python crawl_luatvietnam.py --max-pages 100 --delay 2.5 --out output/luatvietnam
```

Phần này giữ nguyên crawler riêng từ lần trước. Khi nhập kho dữ liệu thống nhất cần normalize schema giữa hai nguồn; với LuatVietnam lưu `relevant_law` từ mục `Văn bản liên quan` riêng, và `citation` từ phần tư vấn.

## Lưu ý

Crawler VnExpress chưa được chạy end-to-end trên website trong môi trường này (Python không có đường mạng); đã kiểm tra logic parser trên HTML người dùng cung cấp. Không thể khẳng định số lượng bài lấy được cho đến khi chạy trên máy có Internet. Tuân thủ robots, điều khoản sử dụng, giới hạn tốc độ và quyền tác giả; không vượt biện pháp chống bot.
