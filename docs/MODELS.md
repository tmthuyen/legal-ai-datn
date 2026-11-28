## Mô hình Sử dụng & Đánh giá Thực nghiệm

Hệ thống áp dụng kiến trúc **Single-Model Multi-Task** (dùng 1 mô hình duy nhất xử lý đồng thời cả 2 tác vụ: trích xuất cấu trúc `Rule - Predicate - Fact` sang JSON và hỏi đáp pháp lý), tối ưu huấn luyện 4-bit qua **Unsloth** và triển khai trên môi trường giới hạn RAM (Windows CPU 10GB RAM / Google Colab GPU).

### 1. Mô hình Chính thức (Production)

- **`Qwen/Qwen3-4B-Instruct-2507`**: Bản chuyên biệt _Non-thinking_, tuân thủ chỉ thị và xuất cấu trúc JSON/Prolog chuẩn xác nhất trong nhóm ≤ 4B mà không sinh thẻ suy nghĩ thừa. Sau khi nén GGUF (`Q4_K_M`), mô hình chỉ chiếm **~2.6 GB RAM**.

### 2. Danh sách các Mô hình Thực nghiệm (Model Comparison)

| Tên Mô hình (Hugging Face)        | Tham số  | Chế độ suy luận                     | RAM Local (GGUF Q4_K_M) | Mục đích sử dụng trong dự án                                                                                                 |
| :-------------------------------- | :------- | :---------------------------------- | :---------------------- | :--------------------------------------------------------------------------------------------------------------------------- |
| **`Qwen/Qwen3-4B-Instruct-2507`** | **4.0B** | **Non-thinking**                    | **~2.6 GB**             | **Mô hình chính thức.** Cân bằng tối ưu nhất giữa độ chính xác trích xuất logic, hỏi đáp luật và dung lượng RAM.             |
| **`Qwen/Qwen3-4B`**               | **4.0B** | **Hybrid** (`/think` & `/no_think`) | **~2.6 GB**             | **Thực nghiệm đối chiếu.** Đánh giá hiệu quả của cơ chế suy luận từng bước (`<think>`) khi giải tình huống pháp lý phức tạp. |
| **`Qwen/Qwen2.5-3B-Instruct`**    | **3.0B** | **Non-thinking**                    | **~2.0 GB**             | **Phương án dự phòng nhẹ hơn.** So sánh hiệu năng giữa thế hệ Qwen2.5 và Qwen3 ở phân khúc tầm trung.                        |
| **`Qwen/Qwen3-1.7B`**             | **1.7B** | **Hybrid** (`/no_think`)            | **~1.2 GB**             | **Ứng viên tối ưu tốc độ CPU.** Kiểm tra khả năng chạy mượt trên máy yếu và đánh đổi về độ chính xác.                        |
| **`Qwen/Qwen2.5-1.5B-Instruct`**  | **1.5B** | **Non-thinking**                    | **~1.1 GB**             | **Baseline (Mốc dưới).** Làm chuẩn so sánh tốc độ và chứng minh sự cải thiện chất lượng khi tăng tham số.                    |
