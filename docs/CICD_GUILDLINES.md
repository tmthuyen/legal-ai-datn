# Hướng dẫn CI/CD trước khi push code 
- Các nhánh: main, dev, production, ci-cd

## Backend (Python FastAPI)

```
cd backend
```

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