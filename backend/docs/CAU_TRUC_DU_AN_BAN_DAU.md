# Cấu trúc thư mục dụ án ban đầu

```
legal-ai/
├── pyproject.toml
├── .env
├── .env.example
├── README.md
│
├── scripts/
│   ├── seed_graph.py        # seed data luật vào Neo4j
│   ├── embed_nodes.py       # embed các node bằng BGE-M3 → ChromaDB
│   ├── test_retrieval.py    # test GraphRAG trước khi tích hợp
│   ├── test_reasoning.py    # test tam đoạn luận
│   ├── test_counterfactual.py
│   └── eval_pipeline.py     # chạy full evaluation
│
├── data/
│   ├── raw/                 # văn bản luật thô crawl về
│   ├── processed/           # đã parse thành JSON có cấu trúc
│   ├── graph/               # node/edge export từ Neo4j
│   └── counterfactual/      # dataset phản ví dụ
│
├── src/
│   ├── __init__.py
│   │
│   ├── graph/               # Bước 1 — Biểu diễn tri thức
│   │   ├── schema.py        # định nghĩa node/edge schema
│   │   ├── builder.py       # build graph từ data đã parse
│   │   ├── embedder.py      # embed node → ChromaDB
│   │   └── neo4j_client.py  # wrapper kết nối Neo4j
│   │
│   ├── retrieval/           # Bước 2a — Truy xuất
│   │   ├── semantic.py      # BGE-M3 + ChromaDB search
│   │   ├── graph_traverse.py # traverse Neo4j theo edges
│   │   ├── hybrid.py        # merge semantic + graph results
│   │   └── reranker.py      # rerank bằng hard negative model
│   │
│   ├── reasoning/           # Bước 2b — Suy luận
│   │   ├── extractor.py     # extract facts từ input (NER)
│   │   ├── condition_checker.py  # check facts vs conditions
│   │   ├── syllogism.py     # tam đoạn luận: facts→rules→conclusion
│   │   └── generator.py     # sinh câu trả lời + trích dẫn (LLM)
│   │
│   ├── verification/        # Bước 3 — Kiểm chứng
│   │   ├── counterfactual.py # tạo + kiểm tra phản ví dụ
│   │   ├── nli.py           # NLI check: điều luật đủ căn cứ không
│   │   └── confidence.py    # tính độ tin cậy kết luận
│   │
│   ├── pipeline.py          # gộp cả 3 bước thành 1 pipeline
│   │
│   ├── api/                 # FastAPI endpoints
│   │   ├── main.py
│   │   └── routes/
│   │       ├── query.py     # POST /query — nhận tình huống
│   │       └── health.py
│   │
│   └── eval/                # Evaluation
│       ├── metrics.py       # Precision@k, F1, hallucination rate
│       ├── dataset.py       # load test set
│       └── runner.py        # chạy eval từng bước
│
└── notebooks/               # thử nghiệm, EDA
    ├── explore_graph.ipynb
    └── test_models.ipynb
```
