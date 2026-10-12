# Legal AI Backend

## About

Backend service (FastAPI) của đồ án **Legal AI - Knowledge Graph & Counterfactual Reasoning**. Đây là nơi chứa toàn bộ pipeline xử lý dữ liệu pháp luật, biểu diễn tri thức dạng đồ thị, truy xuất - suy luận (GraphRAG), kiểm chứng bằng phản ví dụ và đánh giá (evaluation).

## Features

- Config-Driven data pipeline: parse văn bản VBQPPL từ `.docx` theo cấu trúc phân cấp.
- Sinh `node_id` chuẩn hoá và trích xuất các quan hệ pháp lý (`REFERENCES`, `IMPLEMENTS`, `INTERPRETED_BY`, ...).
- Validator chất lượng dữ liệu V1 → V8 + Independent Audit Suite (đối chiếu 1-1 với file Word gốc).
- Knowledge Graph trên Neo4j: nodes/edges + repository/service layer truy vấn.
- Retrieval: semantic search (BGE-M3 + ChromaDB) kết hợp graph traversal (Hybrid / GraphRAG).
- Reasoning: tam đoạn luận `Facts → Conditions → Rules → Conclusion`.
- Verification: phản ví dụ (counterfactual), NLI, confidence - chống ảo giác trích dẫn.
- Evaluation: Precision@k, F1, hallucination rate.

## Prerequisites

- Python (v3.10 or higher)
- Neo4j (v5.x or higher)
- Docker (v20.10 or higher) - chạy Neo4j bằng container
- GPU CUDA (khuyến nghị) cho bước fine-tuning

## Technologies

### Web framework & configuration

- **FastAPI** - REST API
- **Uvicorn** - ASGI server
- **Pydantic** / **pydantic-settings** - schema & config (`.env`)
- **python-dotenv** - load biến môi trường

### Data & storage

- **Neo4j** (`neo4j` driver) - Knowledge Graph database
- **ChromaDB** - Vector Database
- **pandas** / **numpy** - xử lý dữ liệu
- **python-docx** / OOXML (`zipfile`, `xml.etree`) - parse file `.docx`

### NLP / AI

- **sentence-transformers** - embedding văn bản bằng **BGE-M3**
- **transformers** - suy luận mô hình **Qwen2.5** (`ntphuc149/ViLegalQwen2.5-1.5B-Base`)
- **peft** - fine-tune **LoRA**
- **PyTorch** - nền tảng huấn luyện / suy luận
- **Hugging Face Hub** - lưu trữ model fine-tuned

### Dev tooling

- **Jupyter Notebook** - pipeline ETL & thử nghiệm
- **pytest** / **pytest-cov** - testing
- **black** / **isort** - format code
- **pre-commit** - git hooks

## Structure folder

```
backend/
├── data/                       # Dữ liệu
│   ├── van_ban/                #   file văn bản luật nguồn (.doc/.docx)
│   ├── processed/              #   nodes.json, relations.json, unresolved_references.json
│   ├── graph/                  #   node/edge export từ Neo4j
│   ├── qa/                     #   bộ dữ liệu hỏi đáp (qa_data.json)
│   ├── retrieval/              #   dataset truy xuất / dẫn chiếu
│   ├── phan_vi_du/             #   dataset phản ví dụ (counterfactual)
│   └── metadata/               #   metadata file nguồn
│
├── docs/                       # Tài liệu nội bộ (cấu trúc dự án, plan)
│   └── plans/                  #   kế hoạch triển khai theo version
│
├── experiments/                # Log thí nghiệm theo model + timestamp
│
├── graph/                      # Script nạp Knowledge Graph
│   └── import_neo4j.py         #   import nodes/relations vào Neo4j
│
├── notebooks/                  # Pipeline ETL & thử nghiệm
│   ├── 01_parse_data.ipynb     #   parse cấu trúc VBQPPL từ .docx
│   ├── 02_transform.ipynb      #   chuẩn hoá id, trích xuất dẫn chiếu, validator
│   ├── 03_explore_graph.ipynb  #   khám phá đồ thị
│   ├── 04_retrieval.ipynb      #   dataset truy xuất, test GraphRAG
│   └── 05_fine-tuning.ipynb    #   fine-tune Qwen2.5 bằng LoRA
│
├── scripts/                    # Script chạy lẻ
│   ├── seed_graph.py           #   seed dữ liệu luật vào Neo4j
│   ├── test_graph.py           #   test kết nối & truy vấn graph
│   ├── test_retrieval.py       #   test truy xuất
│   ├── test_reasoning.py       #   test tam đoạn luận
│   └── eval_pipeline.py        #   chạy full evaluation
│
├── src/                        # Mã nguồn chính
│   ├── main.py
│   ├── api/                    # FastAPI
│   │   ├── server.py           #   khởi tạo app
│   │   ├── api_schemas.py      #   request/response schema
│   │   └── routes/
│   │       └── health.py       #   GET /api/health
│   ├── common/                 # Dùng chung
│   │   ├── setting_config.py   #   cấu hình từ .env
│   │   ├── schemas.py          #   LegalHierarchy, pattern phân cấp
│   │   └── custom_exception.py #   exception tuỳ chỉnh
│   ├── graph/                  # Bước 1 - Biểu diễn tri thức
│   │   ├── neo4j_client.py     #   wrapper kết nối Neo4j
│   │   ├── graph_repository.py #   repository truy vấn (labels, relationship types)
│   │   ├── graph_service.py    #   service layer cho repository
│   │   ├── builder_graph.py    #   build graph
│   │   └── embedder.py         #   embed node → ChromaDB
│   ├── retrieval/              # Bước 2a - Truy xuất
│   │   ├── semantic.py         #   BGE-M3 + ChromaDB search
│   │   ├── graph_traverse.py   #   traverse Neo4j theo edges
│   │   ├── hybrid.py           #   merge semantic + graph
│   │   ├── reranker.py         #   rerank bằng hard negative model
│   │   └── legal_query.py      #   trích xuất Điều/Khoản/Điểm từ câu hỏi
│   ├── reasoning/              # Bước 2b - Suy luận
│   │   ├── extractor.py        #   extract facts từ input
│   │   ├── condition_checker.py#   check facts vs conditions
│   │   ├── syllogism.py        #   tam đoạn luận
│   │   └── generator.py         #   sinh câu trả lời + trích dẫn (LLM)
│   ├── verification/           # Bước 3 - Kiểm chứng
│   │   ├── counterfactual.py   #   tạo + kiểm tra phản ví dụ
│   │   ├── nli.py              #   NLI check
│   │   └── confidence.py       #   độ tin cậy kết luận
│   ├── eval/                   # Evaluation
│   │   ├── metrics_eval.py     #   Precision@k, F1, hallucination rate
│   │   ├── dataset_eval.py     #   load test set
│   │   └── runner_eval.py      #   chạy eval từng bước
│   └── utils/                  # Tiện ích
│       ├── logger.py           #   logging ra logs/
│       ├── config_loader.py    #   load YAML config
│       ├── file_utils.py       #   đọc/ghi file
│       ├── clean_text_utils.py #   làm sạch văn bản tiếng Việt
│       ├── teencode_dict.py    #   từ điển teencode
│       ├── checkpoint_manager.py # quản lý checkpoint training
│       └── experiment_tracker.py # tracking thí nghiệm
│
├── logs/                       # Log runtime
├── pyproject.toml              # Dependencies & tool config
├── .env / .env.example         # Biến môi trường
├── .gitignore
└── README.md
```

### Knowledge Graph Schema

- **Node labels (`LegalHierarchyLabels`):** `Document`, `Part`, `Chapter`, `Section`, `SubSection`, `Article`, `Clause`, `Point` (tất cả dùng label chung `LegalNode`).
- **Relationship types (`LegalRelationshipTypes`):** `RELATED_TO`, `CONTAINS`, `REFERENCES`, `IMPLEMENTS`, `INTERPRETED_BY`, `AMENDS`, `REPLACES`.

## Installation

### A. Môi trường ảo (venv)

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
pip install -e ".[dev]"
```

### B. Cấu hình `.env`

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=123456
NEO4J_DATABASE=legalai
```

### C. Chạy Neo4j

```bash
docker run -d --name neo4j-legal-ai -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/123456 neo4j:5
```

### D. Nạp Knowledge Graph

```bash
python graph/import_neo4j.py
```

### E. Chạy server

```bash
uvicorn src.api.server:app --host localhost --port 8090 --reload
```

## Usage

```bash
python scripts/test_graph.py
python scripts/test_retrieval.py
python scripts/test_reasoning.py
python scripts/eval_pipeline.py
```

## Api Documentation

- Swagger UI: http://localhost:8090/docs
- Health check: http://localhost:8090/api/health

## Contributing

- Thuyendev
- other

## License
