# V1 — LegalAI CI/CD Split Workflows (backend/services/frontend CI-CD riêng)

## Trạng thái
- [ ] Chưa thực hiện
- [ ] Đang thực hiện
- [x] Hoàn thành (đã tạo workflows, YAML hợp lệ)

## Người thực hiện & thời gian
- Agent: Big Pickle (opencode/big-pickle)
- Ngày tạo: 2025-10-18
- Thời gian dự kiến: ~1–2h

## Mục tiêu
Tích hợp CI/CD khi push code lên `dev` hoặc `main`:
- `main`: có **CI + CD**
- `dev`: có **CI** (không CD)
- Chia riêng từng file workflow như yêu cầu:
  - `backend-CI.yml`
  - `backend-CD.yml`
  - `services-CI.yml`
  - `services-CD.yml`
  - `frontend-CI.yml`
  - `frontend-CD.yml`

## Phạm vi (scope)
- Tạo `.github/workflows/` (nếu chưa có)
- Tạo 6 workflow files trên
- Trigger: push/PR theo nhánh `dev`, `main`; path filters để chạy chỉ khi thay đổi phần liên quan (tối ưu)
- Tuân thủ repo: Python backend (FastAPI), frontend Next.js TS, services Java/Go (theo README). Chưa có code → dùng cấu trúc hiện trạng, thêm checks an toàn (skip build nếu không có Dockerfile/package.json hoặc path không tồn tại)
- Không sửa code nghiệp vụ, chỉ thêm workflows

## Cấu trúc & công nghệ hiện tại (tham khảo)
- Backend: Python 3.10+, FastAPI, pyproject.toml (deps + dev: pytest, black/isort), chạy ở `backend/`, editable install `pip install -e .` / `.[dev]`. Scripts thủ công (`scripts/test_*.py`), chưa có pytest suite. Neo4j cần env.
- Frontend: Next.js TS (chỉ README) — có thể có `package.json` sau; workflow cần detect.
- Services: Java/Go (README) — có thể multi-module; workflow cần linh hoạt (detect `pom.xml`, `build.gradle`, `go.mod`).

## Thiết kế Workflows

### 1) backend-CI.yml
Triggers:
- push: `dev`, `main` (paths: `backend/**`, `.github/workflows/backend-CI.yml`)
- pull_request: `dev`, `main` (paths tương tự)

Jobs (Ubuntu, Python 3.10):
1. Checkout
2. Setup Python + cache pip (pip + .venv cache optional)
3. Install deps: `cd backend && pip install -e ".[dev]"`
4. Lint: `black --check .` và `isort --check-only .` (theo pyproject)
5. Type/check nhẹ (pyright/pyrefly có trong config) — có thể chạy `pyright --project backend` nếu có tool, hoặc skip nếu chưa cài
6. Tests: ưu tiên `pytest` nếu có test, fallback `python -m pytest || python scripts/test_graph.py` (an toàn)
7. Build check: validate import `python -c "import src.api.server"` (smoke)

### 2) backend-CD.yml
Triggers:
- push: `main` (paths: `backend/**`, `.github/workflows/backend-CD.yml`)
- manual dispatch (tùy chọn)

Jobs: build + deploy (placeholder). Repo chưa có Dockerfile/K8s/compose deploy rõ ràng. Tạo job có điều kiện, dùng secrets: `BACKEND_IMAGE`, `REGISTRY`, `DEPLOY_HOST`, `DEPLOY_SSH_KEY` (nếu có). Mặc định skip deploy nếu secrets thiếu (echo log). Có thể build Docker nếu tìm thấy `backend/Dockerfile`.

### 3) services-CI.yml
Triggers: push/PR `dev,main` với paths `services/**`, workflows
Detect Java/Go:
- Java: `services/**/pom.xml` hoặc `build.gradle*` → setup JDK, mvn/gradle test
- Go: `services/**/go.mod` → setup Go, `go build ./...`, `go test ./...`
Matrix hoặc per-path? Hoặc detect root (services có thể nhiều module). Linh hoạt: tìm file, chạy jobs tương ứng (conditional).

### 4) services-CD.yml
Push `main`, paths services/** → build image (nếu Dockerfile) + deploy placeholder, có manual.

### 5) frontend-CI.yml
Next.js TS: detect `frontend/package.json`. Setup Node 20+, npm/pnpm/yarn cache, `npm ci`, `npm run lint` (nếu có), `npm run type-check` (nếu có), `npm run test --if-present`, `npm run build` (nếu có).

### 6) frontend-CD.yml
Push `main`, frontend/** → build/deploy (Vercel/Netlify/SSH) placeholder, manual.

## Path filters & concurrency
Thêm `paths-ignore` hoặc chỉ paths liên quan. Concurrency cancel in-progress.

## Secrets (tài liệu)
Liệt kê cần thiết: DOCKER_REGISTRY_*, SSH_*, DEPLOY_* (chưa bắt buộc, có continue-on-error/skip).

## Phases thực hiện
Phase 1: Tạo `.github/workflows/` + 6 files (template an toàn, có điều kiện detect)
Phase 2: Kiểm tra cú pháp YAML (yaml.safe_load OK)
Phase 3: Commit (khi được yêu cầu) — tuân thủ AGENTS (chỉ commit khi yêu cầu). Ở đây chỉ tạo file.

## Rủi ro & giảm thiểu
- Chưa có code → workflows dùng `if: test -f ...` / `hashFiles()` (GitHub Actions) tránh fail
- Repo Python: tránh Unicode cp1252 (set `PYTHONIOENCODING=utf-8`, `LANG=C.UTF-8`)
- Tuân thủ RULES: không động src/, chỉ workflows.

## Kết quả
- 6 files YAML tạo tại `.github/workflows/`: backend-CI.yml, backend-CD.yml, services-CI.yml, services-CD.yml, frontend-CI.yml, frontend-CD.yml
- YAML hợp lệ (pyyaml safe_load)
- Trigger: dev+main cho CI, main+workflow_dispatch cho CD
- Chạy an toàn khi thiếu code (detect + skip)