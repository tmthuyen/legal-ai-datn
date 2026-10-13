# Các task con phục vụ cho hệ thống pháp lý

- Base Model: `ntphuc149/ViLegalQwen2.5-1.5B-Base` (Hugging Face)
- Link Base Model: [https://huggingface.co/ntphuc149/ViLegalQwen2.5-1.5B-Base](https://huggingface.co/ntphuc149/ViLegalQwen2.5-1.5B-Base)

## 1. Legal Query Reference & Hierarchy Extraction

- legal-query-hierarchy-reference-extraction: LegalQRHE

- Trích xuất các trích dẫn luật từ truy vấn pháp lý (Legal Query Reference Extraction) và xác định cấu trúc phân cấp của luật (Legal Hierarchy Extraction) để hỗ trợ truy vấn pháp lý chính xác hơn.

- Đầu vào: **query_text** (truy vấn pháp lý của người dùng)

- Đầu ra: **extracted_hierarchy** (cấu trúc phân cấp của luật), đầy đủ các trường: document, part, chapter, section, subsection, article, clause, point. Các trường có thể null nếu không được xác định.

- Ví dụ:
  - Đầu vào:

  ```json
  {
    "query_text": "Điều 1 Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013"
  }
  ```

  - Đầu ra:

  ```json
  {
    "document": "Hiến pháp nước Cộng hòa xã hội chủ nghĩa Việt Nam năm 2013",
    "part": null,
    "chapter": "I",
    "section": null,
    "subsection": null,
    "article": null,
    "clause": null,
    "point": null
  }
  ```

- Thông tin mô hình:

  | Attribute           | Value                                                                                 |
  | ------------------- | ------------------------------------------------------------------------------------- |
  | Architecture        | Qwen2 (decoder-only, causal LM)                                                       |
  | Parameters          | 1.54B                                                                                 |
  | Base model          | [Qwen2.5-1.5B](https://huggingface.co/Qwen/Qwen2.5-1.5B)                              |
  | VnLegal Base model  | [ViLegalQwen2.5-1.5B-Base](https://huggingface.co/ntphuc149/ViLegalQwen2.5-1.5B-Base) |
  | Max sequence length | 2048 tokens                                                                           |
  | Tokenizer           | Qwen2 tokenizer                                                                       |
  | Training objective  | Causal Language Modeling (CLM)                                                        |
  | Training domain     | Vietnamese legal text                                                                 |

- Thông tin dữ liệu:

  | Attribute       | Value                                                                          |
  | --------------- | ------------------------------------------------------------------------------ |
  | Dataset         | [legal-extraction](https://huggingface.co/datasets/tmtdev/vn-legal-extraction) |
  | Train size      | X                                                                              |
  | Validation size | X                                                                              |
  | Test size       | X                                                                              |

- Cấu hình huấn luyện

  | Attribute     | Value |
  | ------------- | ----- |
  | Dataset       | X     |
  | Epochs        | 1     |
  | Learning rate | X     |
  | Dropout       | X     |

- Metric:
  | Attribute | Value |
  | --------- | ----- |
  |
