# Hướng dẫn chạy Scripts và Server trong môi trường ảo (venv)

## Clone repo / tạo project mới

```
cd backend
```

## Tạo venv

```
python -m venv .venv
```

```
.\.venv\Scripts\activate
```

## Cài dependencies

```
pip install -e .
```

```
pip install -e ".[dev]"
```

## Chạy scripts

```
# 1. Seed graph
python scripts/seed_graph.py

# 2. Embed nodes
python scripts/embed_nodes.py

# 3. Test retrieval trước
python scripts/test_retrieval.py

# 4. Test reasoning
python scripts/test_reasoning.py

# 5. Eval full pipeline
python scripts/eval_pipeline.py

```

## Chạy server

```
uvicorn src.api.server:app --host localhost --port 8090 --reload

```
