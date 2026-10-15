# Legal AI - Knowledge Graph & Counterfactual Reasoning

## About

A legal AI system built with Python, FastAPI, Neo4j and Vector Database.

### Tên đề tài

Ứng dụng kỹ thuật Biểu diễn tri thức cấu trúc phân cấp của luật và Suy luận kiểm chứng bằng Phản ví dụ vào hệ thống trợ đáp pháp lý

### Mô tả

Nhóm đặt trọng tâm nghiên cứu kỹ thuật vào bài toán **Biểu diễn tri thức cấu trúc phân cấp của luật**, **Truy vấn Luật có trích dẫn cụ thể** và **Suy luận kiểm chứng bằng Phản ví dụ**:

- Văn bản liên quan: Hiến pháp 2013, Bộ Luật Dân sự 2015 và các Nghị định, Nghị quyết có liên quan.
- Tránh xử lý nhiều văn bản vì biểu diễn quá nhiều trên graph sẽ gây khó khăn và loãng thông tin, mất trọng tâm và vượt phạm vi đề tài. Nhóm sẽ tập trung vào một số luật/bộ luật cụ thể để triển khai kỹ thuật.

**1. Biểu diễn tri thức với đồ thị Neuro Symbolic Graph**

- **Mục tiêu:** Mô hình hóa cấu trúc văn bản pháp luật và giải quyết bài toán cấu trúc phân cấp của luật (Chương => Điều => Khoản => Điểm thay vì cắt đoạn phẳng - _Flat Chunking_) và các liên hệ từ Luật khung sang Nghị định, Thông tư hay giao thoa giữa các luật/bộ luật trong phạm vi các luật/bộ luật cụ thể.
- **Kỹ thuật triển khai:** xây dựng trên cơ sở dữ liệu đồ thị biểu diễn các nút quy định và hệ thống cạnh (edges) và nút (nodes) quan hệ.
- **Kết quả:** Hệ thống có khả năng truy vấn, trích xuất các luật liên quan, kiểm tra tính hợp lệ (thời gian hiệu lực) để đưa ra dẫn chứng Luật chống bịa đặt.

**2. Truy vấn & Lập luận kiểm chứng bằng Phản ví dụ với khai thác mẫu âm khó (Hard Negative Mining)**

- **Mục tiêu:** Suy luận logic khách quan từ sự kiện thực tế, triệt tiêu thiên vị và ảo giác trích dẫn.
- **Kỹ thuật triển khai:**
  - **Khung lập luận:** Sử dụng mô hình tam đoạn luận ở mức cơ bản để liên kết dữ kiện thực tế với các quy định trên Graph nhằm sinh giải trình minh bạch.
  - Tạo bộ dữ liệu sinh tổng hợp với các cặp ví dụ - phản chứng là đầu vào huấn luyện của model nhận biết sự khác nhau các tình tiết và không thiên vị, nhầm lẫn khi kết luận tình huống.
  - Không kết luận khi không đủ căn cứ, thông tin từ tình huống hay điều luật trích xuất.

### 3 bước đồ án

1. **Biểu diễn tri thức:** dùng đồ thị phân cấp (Chương => Điều => Khoản => Điểm) thay cho cắt đoạn phẳng.
2. **Truy xuất và suy luận:** từ tình huống đầu vào, hệ thống truy xuất các quy định liên quan trên đồ thị và liên kết `Facts → Conditions → Rules → Conclusion` để tạo kết luận có căn cứ và có thể truy vết (GraphRAG + dữ liệu phản ví dụ để finetune/rerank).
3. **Kiểm chứng:** định nghĩa rõ phản ví dụ, kiểm tra điều luật có đủ căn cứ hay không trước khi kết luận.

<!-- image Screenshots -->

<!--
(![Screenshot](assets/screenshot.png))
-->

## Features

- Legal Domain - VBQPPL Việt Nam (Hiến pháp 2013, BLDS 2015, Luật Hôn nhân và Gia đình 2014, ...)
- Hierarchical Knowledge Graph (Document → Part → Chapter → Section → SubSection → Article → Clause → Point)
- GraphRAG: Semantic Search + Graph Traversal
- Counterfactual Verification (Hard Negative Mining)
- Anti-hallucination: không kết luận khi thiếu căn cứ
- Trích xuất dẫn chứng Luật chống bịa đặt (có kiểm tra hiệu lực thời gian)

## Prerequisites

- Python (v3.10 or higher)
- Neo4j (v5.x or higher)
- GPU CUDA (khuyến nghị) cho bước fine-tuning

## Technologies

- Python
- FastAPI
- Neo4j (Knowledge Graph)
- Vector Database (Neo4j Vector Index)
- sentence-transformers / transformers (Text Embedding: `darklethelong/vnlegal-lal`)
- Qwen2.5 + LoRA/PEFT (Fine-tuning)
- PyTorch
- pandas / numpy 
- Jupyter Notebook (Pipeline ETL & Experiment)

## Structure folder

```
datn-legal-ai/
├── backend/
│   ├── data/                   # văn bản luật thô + dữ liệu đã parse (nodes, relations, QA, retrieval)
│   │   ├── van_ban/            # file .doc/.docx nguồn
│   │   ├── processed/          # nodes.json, relations.json, unresolved_references.json
│   │   ├── qa/                 # bộ dữ liệu QA
│   │   └── retrieval/          # dataset truy xuất / dẫn chiếu
│   ├── docs/                   # tài liệu nội bộ (cấu trúc dự án, plan)
│   ├── experiments/            # log experiment theo model + timestamp
│   ├── graph/                  # import_neo4j.py - nạp KG vào Neo4j
│   ├── notebooks/              # pipeline 01→05 (parse, transform, retrieval, fine-tuning)
│   ├── scripts/                # seed / test / eval
│   ├── src/                    # mã nguồn service (api, graph, retrieval, reasoning, verification, eval)
│   ├── pyproject.toml          # dependencies & tool config
│   └── README.md               # tài liệu kỹ thuật của backend
├── docs/
├── README Movie App.md
├── README.md
└── tom_tat_sua_doi.md          # tóm tắt thay đổi code
```

## Installation

- Clone the repository:

```bash
git clone github link
```

- Create virtual environment & install dependencies: root folder `backend`

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
pip install -e ".[dev]"
```

- Configure environment variables: copy `.env.example` → `.env`

```bash
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=123456
NEO4J_DATABASE=legalai
```


- Import Knowledge Graph vào Neo4j:

```bash
python graph/import_neo4j.py
```

- Run backend server:

```bash
uvicorn src.api.server:app --host localhost --port 8090 --reload
```

- Health check: http://localhost:8090/api/health

## Usage

- Pipeline xử lý dữ liệu (chạy theo thứ tự trong `backend/notebooks/`):

| Bước | Notebook                 | Công việc                                                                  |
| ---- | ------------------------ | -------------------------------------------------------------------------- |
| 1    | `01_parse_data.ipynb`    | Parse cấu trúc VBQPPL từ `.docx` (Config-Driven)                           |
| 2    | `02_transform.ipynb`     | Chuẩn hoá số thứ tự, sinh `node_id`, trích xuất dẫn chiếu, validator V1→V8 |
| 3    | `03_explore_graph.ipynb` | Exploratory data analysis trên đồ thị                                      |
| 4    | `04_retrieval.ipynb`     | Xây dựng dataset truy xuất, test GraphRAG                                  |
| 5    | `05_fine-tuning.ipynb`   | Fine-tune mô hình Qwen2.5 bằng LoRA                                        |

- Chạy script (trong `backend/`):

```bash
python scripts/test_graph.py
python scripts/test_retrieval.py
python scripts/test_reasoning.py
python scripts/eval_pipeline.py
```

## Api Documentation

- Backend APIs (Swagger UI): http://localhost:8090/docs

- Health check: http://localhost:8090/api/health

## Contributing

- Thuyendev
- other

## License
