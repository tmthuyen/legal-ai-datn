# Báo Cáo Thực Nghiệm Đánh Giá Retrieval (Ablation Study)

- **Thời gian thực nghiệm:** 2026-10-30 12:57:57
- **Tập dữ liệu:** `zalo_blds_scope.json` (65 câu hỏi)
- **Phân bố độ phức tạp:** `{'MULTI_HOP_CROSS_DOC': 5, 'MULTI_HOP_INTRA_BLDS': 2, 'SINGLE_HOP': 58}`
- **Ngưỡng cắt Top-K:** 10

## 1. Bảng So Sánh Hiệu Năng Tổng Thể (Overall Performance)

| Phương pháp | Hit@1 (%) | Hit@5 (%) | Hit@10 (%) | Recall@1 (%) | Recall@5 (%) | Recall@10 (%) | MRR@10 | NDCG@10 | Latency TB (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| BM25 (Lexical) | 60.0% | 80.0% | 81.54% | 54.87% | 76.92% | 77.69% | 0.6827 | 0.6875 | 12.05 ms |
| Dense Semantic (vnlegal-lal) | 69.23% | 90.77% | 93.85% | 64.1% | 86.15% | 91.54% | 0.7900 | 0.8028 | 1203.82 ms |
| **Hybrid (BM25 + Semantic RRF)** | 70.77% | 84.62% | 93.85% | 65.64% | 80.77% | 91.28% | 0.7715 | 0.7876 | 1195.02 ms |

## 2. Phân Tích Chi Tiết Theo Hop Type (Độ phức tạp truy xuất)

### Nhóm: `MULTI_HOP_CROSS_DOC`

| Phương pháp | Hit@1 (%) | Hit@5 (%) | Hit@10 (%) | Recall@5 (%) | Recall@10 (%) | MRR@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| BM25 | 100.0% | 100.0% | 100.0% | 73.33% | 73.33% | 1.0000 |
| Semantic | 100.0% | 100.0% | 100.0% | 56.67% | 70.0% | 1.0000 |
| **Hybrid RRF** | 100.0% | 100.0% | 100.0% | 73.33% | 73.33% | 1.0000 |

### Nhóm: `MULTI_HOP_INTRA_BLDS`

| Phương pháp | Hit@1 (%) | Hit@5 (%) | Hit@10 (%) | Recall@5 (%) | Recall@10 (%) | MRR@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| BM25 | 50.0% | 50.0% | 100.0% | 16.66% | 41.66% | 0.5715 |
| Semantic | 50.0% | 100.0% | 100.0% | 58.34% | 100.0% | 0.7500 |
| **Hybrid RRF** | 50.0% | 100.0% | 100.0% | 41.66% | 83.34% | 0.6000 |

### Nhóm: `SINGLE_HOP`

| Phương pháp | Hit@1 (%) | Hit@5 (%) | Hit@10 (%) | Recall@5 (%) | Recall@10 (%) | MRR@10 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| BM25 | 56.9% | 79.31% | 79.31% | 79.31% | 79.31% | 0.6592 |
| Semantic | 67.24% | 89.66% | 93.1% | 89.66% | 93.1% | 0.7733 |
| **Hybrid RRF** | 68.97% | 82.76% | 93.1% | 82.76% | 93.1% | 0.7577 |

## 3. Nhận Xét & Kết Luận Khoa Học

- **BM25:** Kết quả và độ trễ được đo trên tập câu hỏi này; không suy rộng sang mọi truy vấn.
- **Dense Semantic:** So sánh các metric trong bảng; cần kiểm thử thêm để kết luận khả năng xử lý diễn đạt khác từ khóa.
- **Hybrid so với Semantic – hit@1:** cao hơn (70.77 so với 69.23).
- **Hybrid so với Semantic – hit@5:** thấp hơn (84.62 so với 90.77).
- **Hybrid so với Semantic – recall@5:** thấp hơn (80.77 so với 86.15).
- **Hybrid so với Semantic – recall@10:** thấp hơn (91.28 so với 91.54).
- **Hybrid so với Semantic – mrr@10:** thấp hơn (0.7715 so với 0.79).
- **Lưu ý:** Đây là kết quả retrieval trước graph traversal. Không thể suy ra Hybrid vượt trội trên mọi tình huống chỉ từ benchmark này.
