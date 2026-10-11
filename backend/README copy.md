# AI Recommendation Service

This is a simple AI recommendation service that fetches movie data from the TMDB API and provides recommendations based on user preferences.

## Features

- Fetch movie data from TMDB API, movie metadata, and movie posters.
- Provide movie recommendations based on user preferences using a recommendation algorithm.

## Prerequisites

- Python 3.10 or higher
- FastAPI
- Vector Database (e.g., Milvus, Weaviate, or Pinecone)
- Docker

## Technologies

- FastAPI
- RabbitMQ
- BERT / phoBERT / sentence-transformers
- TF-IDF / BM25 (baseline)
- Vector Database (e.g., Milvus, Weaviate, or Pinecone)
- Docker
- OpenTelemetry (Tracer, Metrics, Logs)

## Structure folder

```
ai-service/
├── config/
├── data/
├── docs/
├── notebooks/
├── scripts/
├── test/
└── src/
    ├── api/
    ├── core/
    ├── models/
    ├── services/
    └── utils/
├── .env
├── .gitignore
├── .dockerignore
├── README.md
├── pyproject.toml
├── Dockerfile

```

## Installation

-  Hướng dẫn chạy FastAPI Service

### A. Chạy trong môi trường venv

-  Tạo môi trường ảo (để không làm rác máy tính)
```
python -m venv .venv
```


-  Kích hoạt môi trường (Lệnh riêng cho Windows PowerShell)
```
.\.venv\Scripts\activate
```

-  Cài đặt các thư viện cần thiết
```
pip install -e .
```

-  Cài đặt toàn bộ (bao gồm cả Core và nhóm Dev Tools)
```
pip install -e .[dev]
```


### B. Hướng dẫn chạy lệnh huấn luyện mô hình (Mẫu)
```
python scripts/train_baseline.py 
```

### C. Hướng dẫn chạy API
```
uvicorn src.api.server:app --host localhost --port 8082 --reload
```


## API Endpoints

- API documentation: [Swagger UI](http://localhost:8082/docs)

- Endpoints:

## Contributing
