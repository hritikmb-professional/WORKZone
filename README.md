# AI Workplace Intelligence Platform

## Stack
- **Backend**: FastAPI 0.111 · Python 3.11 · SQLAlchemy 2.0 async · PostgreSQL 15
- **Auth**: RS256 JWT · Refresh token rotation + reuse detection · RBAC
- **Cloud**: AWS S3 · Lambda · Transcribe · EC2 · RDS · DynamoDB · API Gateway
- **ML**: Random Forest · KMeans · Isolation Forest · BART · spaCy · GPT-3.5
- **Frontend**: Next.js 14 · TypeScript · TailwindCSS · Recharts · Socket.io

## Quick Start

```bash
# 1. Generate RS256 key pair
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem

# 2. Setup env
cd backend && cp .env.example .env
# Paste PEM contents into JWT_PRIVATE_KEY / JWT_PUBLIC_KEY

# 3. Install + run
pip install -r requirements.txt
alembic upgrade head
uvicorn backend.main:app --reload --port 8000

# 4. Test
pytest tests/ -v --asyncio-mode=auto
```

## Phase Status
- [x] Phase 1 — Foundation & Setup
- [ ] Phase 2 — Meeting Intelligence  
- [ ] Phase 3 — ML Engine
- [ ] Phase 4 — Frontend Dashboard
- [ ] Phase 5 — Deployment
