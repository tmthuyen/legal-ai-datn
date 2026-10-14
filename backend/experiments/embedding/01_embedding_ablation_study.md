# Báo Cáo Thực Nghiệm Bóc Tách Mô Hình Embedding (Ablation Study)
> **Thời điểm thực nghiệm:** 2026-10-14 11:46:52
> **Tập dữ liệu kiểm thử:** `data/eval/benchmark_queries.json` (25 câu hỏi thực tế)
> **Tổng số Article nodes trong kho ngữ liệu:** 912 điều luật (Hiến pháp 2013, BLDS 2015, NĐ 21/2021, NĐ 19/2019, NQ 02/2022)

## 1. Thiết Kế Thí Nghiệm (Ablation Methodology)

Thực nghiệm được thiết kế theo phương pháp **Ablation Study (Nghiên cứu bóc tách)** nhằm kiểm chứng 2 giả thuyết khoa học:
1. **Giả thuyết 1 (Hiệu ứng Ngữ cảnh):** Việc bổ sung nhãn phả hệ `[Document > Chapter > Section > Article]` trước nội dung có giúp cải thiện độ chính xác truy xuất so với việc chỉ dùng văn bản thô (plain text)?
2. **Giả thuyết 2 (Hiệu ứng Miền chuyên biệt):** Mô hình được tinh chỉnh chuyên sâu cho văn bản pháp luật Việt Nam (`darklethelong/vnlegal-lal`) có vượt trội hơn mô hình đa ngôn ngữ tổng quát (`BAAI/bge-m3`) khi cùng sử dụng ngữ cảnh phân cấp?

Ba cấu hình được đưa vào so sánh đối đầu:
- **Cấu hình 1 (Baseline):** `BAAI/bge-m3` + `Plain Text`
- **Cấu hình 2 (Context Effect):** `BAAI/bge-m3` + `Context-Enriched`
- **Cấu hình 3 (Domain Model Effect):** `darklethelong/vnlegal-lal` + `Context-Enriched`

## 2. Bảng Tổng Hợp Chỉ Số Định Lượng

| Cấu hình Thực nghiệm | Model Embedding | Dạng Văn bản | Hit@1 (%) | Hit@3 (%) | Hit@5 (%) | MRR | NDCG@5 | Độ trễ TB (ms) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **BGE-M3 (Plain Text)** | `BAAI/bge-m3` | `plain` | **84.0%** | 100.0% | 100.0% | **0.9133** | **0.8962** | 514.6 ms |
| **BGE-M3 (Context-Enriched)** | `BAAI/bge-m3` | `enriched` | **92.0%** | 100.0% | 100.0% | **0.9600** | **0.9196** | 514.1 ms |
| **VNLegal-LAL (Context-Enriched)** | `darklethelong/vnlegal-lal` | `enriched` | **96.0%** | 100.0% | 100.0% | **0.9800** | **0.9509** | 870.0 ms |

---

## 3. Phân Tích Chi Tiết Từng Câu Hỏi

| ID | Chủ đề pháp lý | Expected Article | Cấu hình 1 (BGE-M3 Plain) | Cấu hình 2 (BGE-M3 Enriched) | Cấu hình 3 (VNLegal-LAL Enriched) |
| :---: | :--- | :--- | :---: | :---: | :---: |
| Q01 | Hợp đồng vay - Lãi suất thỏa thuận | `BLDS_2015_D468` | Top 1 (0.7277) | Top 1 (0.7166) | Top 1 (0.7732) |
| Q02 | Bồi thường ngoài hợp đồng - Nguồn nguy hiểm cao độ | `NQ_02_2022_D12, BLDS_2015_D601` | Top 1 (0.7165) | Top 1 (0.7209) | Top 1 (0.7373) |
| Q03 | Biện pháp bảo đảm - Thế chấp tài sản (Điều 322, 323 BLDS) | `BLDS_2015_D323, BLDS_2015_D322` | Top 2 (0.7404) | Top 1 (0.7634) | Top 1 (0.7051) |
| Q04 | Giao dịch họ, hụi, biêu, phường | `ND_19_2019_D23, ND_19_2019_D1, BLDS_2015_D471` | Top 1 (0.5843) | Top 1 (0.6147) | Top 1 (0.5001) |
| Q05 | Hợp đồng vay - Không kỳ hạn và không lãi | `BLDS_2015_D463, BLDS_2015_D469, BLDS_2015_D470` | Top 1 (0.7006) | Top 1 (0.7154) | Top 1 (0.6376) |
| Q06 | Biện pháp bảo đảm - Đặt cọc | `BLDS_2015_D328` | Top 1 (0.7481) | Top 1 (0.701) | Top 1 (0.6928) |
| Q07 | Biện pháp bảo đảm - Cầm cố tài sản | `BLDS_2015_D309, BLDS_2015_D314` | Top 1 (0.771) | Top 1 (0.7777) | Top 1 (0.7433) |
| Q08 | Biện pháp bảo đảm - Bảo lãnh | `BLDS_2015_D335, BLDS_2015_D336` | Top 1 (0.7461) | Top 1 (0.7683) | Top 1 (0.7601) |
| Q09 | Hợp đồng tặng cho tài sản có điều kiện | `BLDS_2015_D462` | Top 1 (0.7571) | Top 1 (0.7401) | Top 1 (0.6639) |
| Q10 | Thừa kế theo pháp luật - Hàng thừa kế | `BLDS_2015_D651` | Top 1 (0.7442) | Top 1 (0.7299) | Top 1 (0.6464) |
| Q11 | Thừa kế theo di chúc - Di chúc hợp pháp | `BLDS_2015_D630` | Top 1 (0.7653) | Top 1 (0.7757) | Top 1 (0.6693) |
| Q12 | Thừa kế - Từ chối nhận di sản | `BLDS_2015_D620` | Top 1 (0.7104) | Top 1 (0.7244) | Top 1 (0.666) |
| Q13 | Thừa kế - Thời hiệu thừa kế | `BLDS_2015_D623` | Top 1 (0.724) | Top 1 (0.7369) | Top 1 (0.6399) |
| Q14 | Bồi thường thiệt hại do súc vật gây ra | `BLDS_2015_D603` | Top 1 (0.6392) | Top 1 (0.6419) | Top 1 (0.6219) |
| Q15 | Bồi thường do người chưa thành niên gây ra | `BLDS_2015_D599` | Top 1 (0.7384) | Top 1 (0.7516) | Top 1 (0.6692) |
| Q16 | Bồi thường thiệt hại do tính mạng bị xâm phạm | `BLDS_2015_D591` | Top 2 (0.7719) | Top 2 (0.7634) | Top 1 (0.7297) |
| Q17 | Chấm dứt hợp đồng - Đơn phương chấm dứt | `BLDS_2015_D428` | Top 1 (0.7162) | Top 1 (0.7255) | Top 1 (0.7029) |
| Q18 | Nguyên tắc cơ bản của pháp luật dân sự | `BLDS_2015_D3` | Top 1 (0.6707) | Top 1 (0.6762) | Top 1 (0.6157) |
| Q19 | Nghị định 19 - Nguyên tắc tổ chức và chủ họ | `ND_19_2019_D3, ND_19_2019_D6` | Top 3 (0.7204) | Top 1 (0.74) | Top 2 (0.6298) |
| Q20 | Nghị định 19 - Lãi suất trong dây họ | `ND_19_2019_D21` | Top 1 (0.7588) | Top 1 (0.755) | Top 1 (0.6865) |
| Q21 | Nghị định 19 - Trách nhiệm của chủ họ | `ND_19_2019_D23` | Top 1 (0.8096) | Top 1 (0.8219) | Top 1 (0.7307) |
| Q22 | Nghị định 21 - Xử lý tài sản bảo đảm | `ND_21_2021_D51, ND_21_2021_D49` | Top 1 (0.8104) | Top 1 (0.8197) | Top 1 (0.7175) |
| Q23 | Nghị quyết 02 - Hướng dẫn Điều 601 nguồn nguy hiểm cao độ | `NQ_02_2022_D12, BLDS_2015_D601` | Top 1 (0.7473) | Top 1 (0.7677) | Top 1 (0.7115) |
| Q24 | Nghị quyết 02 - Hướng dẫn Điều 585 nguyên tắc bồi thường | `NQ_02_2022_D3` | Top 2 (0.667) | Top 2 (0.6834) | Top 1 (0.6197) |
| Q25 | Hiến pháp 2013 - Chế độ chính trị | `HIEN_PHAP_2013_D1, HIEN_PHAP_2013_D2` | Top 1 (0.8181) | Top 1 (0.8194) | Top 1 (0.6604) |

---

## 4. Kết Luận & Đóng Góp Học Thuật Cho Luận Văn

1. **Hiệu quả của Ngữ cảnh phân cấp (Context Enrichment):**
   - So sánh giữa Baseline (Plain) và Enriched trên cùng model BGE-M3: Hit@1 thay đổi **+8.0%**, MRR thay đổi **+0.0467**.
   - Việc gắn `[Document > Chapter > Section > Article]` cung cấp neo ngữ nghĩa (semantic anchor), giúp phân định rạch ròi các quy định có từ ngữ tương tự nhau giữa Bộ luật Dân sự và các Nghị định chuyên ngành.

2. **So sánh Model Quốc tế (BGE-M3) vs Model Chuyên biệt Pháp luật Việt Nam (VNLegal-LAL):**
   - Mô hình `VNLegal-LAL` đạt Hit@1 **96.0%** và MRR **0.9800** (chênh lệch +4.0% Hit@1, +0.0200 MRR so với BGE-M3 Enriched).
   - Cả 2 mô hình đều có cùng số chiều không gian (1024-d), tương thích hoàn toàn với hạ tầng Neo4j Vector Index mà không cần thay đổi kiến trúc cơ sở dữ liệu.

3. **Lựa chọn Mô hình Cho Hệ Thống Chính Thức:**
   - Cấu hình chiến thắng được chọn triển khai vào đồ án: **`VNLegal-LAL (Context-Enriched)`** (`darklethelong/vnlegal-lal` với `enriched`).
