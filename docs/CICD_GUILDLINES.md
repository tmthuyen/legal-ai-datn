# Hướng dẫn CI/CD trước khi push code 
- Các nhánh: main, dev, production, ci-cd

## Backend (Python FastAPI)

```
cd backend
```

- Tạo virtual environment
```
python -m venv .venv
.\.venv\Scripts\activate
```


-  Cài đặt công cụ dev (nếu chưa cài)
```
pip install black isort pytest
```

- Chạy các lệnh
| Action | Type | Branch | Commands |
|:---:|:---:|:---|:---|
| **CI** | Lint | `dev`, `ci-cd` | `isort src`<br>`isort --check-only src` <br> `black src` <br> `black --check src` |
| **CI** | Test | `dev`, `ci-cd` | `pytest tests/ -v`<br>`pytest tests/ -q` |
| **CD** | Deploy (Chưa có) | `main`, `production` | `docker-compose build backend`<br>`docker-compose up -d backend` |





## Frontend (NextJS)
- 


## Services (Java/Golang) 
-

## Docker
-