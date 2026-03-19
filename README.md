# AI Workplace Intelligence Platform

Full-stack enterprise platform that automatically transcribes meetings, generates AI-powered summaries, extracts action items, and computes ML-driven workforce analytics. The complete audio-to-dashboard pipeline runs in under 3 minutes for a 30-minute meeting with zero manual steps.

**Stack:** Next.js 14 · FastAPI · AWS (S3, Lambda, Transcribe, EC2, RDS, DynamoDB) · scikit-learn · HuggingFace · PostgreSQL

---

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Running Locally](#running-locally)
- [Running with Docker](#running-with-docker)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [ML Models](#ml-models)
- [AWS Architecture](#aws-architecture)
- [Security Architecture](#security-architecture)
- [Testing](#testing)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)

---

## Project Overview

Four technical domains demonstrated simultaneously:

- **AI / ML** — BART abstractive summarization, spaCy + GPT-3.5 hybrid NLP, Random Forest productivity scoring, KMeans clustering, Isolation Forest burnout detection
- **Full-Stack** — Next.js 14 App Router frontend, FastAPI async backend, RS256 JWT with refresh token rotation, WebSocket real-time updates
- **AWS Cloud** — S3, Lambda x3, Transcribe, EC2, RDS, DynamoDB, API Gateway, CloudFront, CloudWatch, IAM
- **Data Engineering** — Event-driven Lambda pipeline, 6-table PostgreSQL schema, ML feature engineering, weekly analytics automation

---

## Repository Structure

```
workplace-intelligence-platform/
├── backend/
│   ├── main.py                   # FastAPI entry, lifespan, CORS, rate limiting
│   ├── api/routes/               # auth.py  meetings.py  analytics.py  websocket.py
│   ├── core/                     # config.py  database.py  security.py
│   ├── models/models.py          # SQLAlchemy ORM: Employee  Team  Meeting  ...
│   ├── services/                 # s3_service  meeting_service  analytics_service
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                      # dashboard  meetings  analytics  employee  manager  login
│   ├── components/layout/        # DashboardLayout  Header  Sidebar  Topbar
│   ├── components/ui/            # BurnoutGauge  ClusterBadge  StatCard
│   ├── lib/                      # api.ts  auth.ts  theme.tsx
│   ├── package.json
│   └── .env.local
├── ml_models/
│   ├── productivity_model.py     # Random Forest inference pipeline
│   ├── burnout_model.py          # Isolation Forest inference
│   ├── clustering.py             # KMeans employee segmentation
│   └── training/                 # Notebooks and training scripts
├── meeting_ai/
│   ├── transcription.py          # Whisper local + AWS Transcribe
│   ├── summarization.py          # BART-large-CNN
│   ├── action_item_extractor.py  # spaCy + GPT-3.5 hybrid
│   └── diarization.py            # pyannote.audio speaker ID
├── lambda_functions/
│   ├── transcription_trigger/
│   ├── nlp_processor/
│   └── analytics_pipeline/
├── database/
│   ├── schema.sql
│   └── migrations/               # Alembic scripts
└── cloud/                        # Terraform IaC
```

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required for FastAPI, SQLAlchemy 2.0, ML libraries |
| Node.js | 18+ | Required for Next.js 14 |
| PostgreSQL | 15+ | Local install or Docker instance on port 5432 |
| AWS CLI | 2.x | Configured with IAM credentials for S3, Lambda, Transcribe |
| Docker | 24+ | Optional: containerised backend and compose-based local stack |
| Terraform | 1.7+ | Optional: one-command AWS infrastructure provisioning |

---

## Environment Setup

### Backend

Copy the example file and fill in values before starting the server:

```bash
cp backend/.env.example backend/.env
```

| Variable | Example / Notes |
|----------|----------------|
| `APP_ENV` | `development` — set to `production` to disable `/docs` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@localhost:5432/workplace_intel` |
| `JWT_PRIVATE_KEY` | RS256 PEM private key. A working dev keypair is pre-filled in `core/config.py` and works immediately. Generate a new pair for production (see below). |
| `JWT_PUBLIC_KEY` | RS256 PEM public key matching `JWT_PRIVATE_KEY` |
| `AWS_REGION` | `us-east-1` |
| `S3_BUCKET` | `workplace-intel` |
| `DYNAMODB_TABLE` | `workplace-events` |
| `GROQ_API_KEY` | Optional. Groq LPU inference for faster summarization. Falls back to BART on CPU if unset. |
| `OPENAI_API_KEY` | Required for GPT-3.5-turbo action item extraction |

Generate a new RS256 keypair for production:

```bash
openssl genrsa -out private.pem 2048
openssl rsa -in private.pem -pubout -out public.pem
# Paste contents (including header/footer lines) into JWT_PRIVATE_KEY and JWT_PUBLIC_KEY in .env
```

### Frontend

The file is pre-configured at `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=change-me-in-production
```

`NEXTAUTH_SECRET` must be a strong random string (minimum 32 characters) in any non-local environment:

```bash
openssl rand -hex 32
```

---

## Database Setup

Create the database:

```bash
psql -U postgres -c "CREATE DATABASE workplace_intel;"
```

Apply schema migrations:

```bash
cd backend
alembic upgrade head
```

If Alembic migrations are not yet initialised, the FastAPI lifespan hook calls `Base.metadata.create_all` on first startup and creates all tables automatically.

### Schema

| Table | Primary Key | Key Relationships |
|-------|-------------|-------------------|
| `employees` | `employee_id UUID` | `team_id FK` to teams, `role ENUM(employee, manager)` |
| `teams` | `team_id UUID` | `manager_id FK` to employees |
| `meetings` | `meeting_id UUID` | `created_by FK`, `audio_s3_key`, `transcript_s3_key`, `duration_mins` |
| `meeting_analysis` | `analysis_id UUID` | `meeting_id FK UNIQUE`, `summary TEXT`, `decisions JSONB`, `action_items JSONB` |
| `productivity_metrics` | `metric_id UUID` | `employee_id FK`, `week_start DATE`, `productivity_score`, `burnout_risk`, `cluster_label` |
| `action_items` | `item_id UUID` | `meeting_id FK`, `assignee_id FK`, `status ENUM`, `confidence FLOAT` |

---

## Running Locally

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy language model (required on first run)
python -m spacy download en_core_web_lg

# Start development server with hot reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> Run `uvicorn` from the **repo root**, not from inside `backend/`. The module path `backend.main:app` requires the repo root to be in `PYTHONPATH`.

The API is available at `http://localhost:8000`. Swagger UI is at `http://localhost:8000/docs` when `APP_ENV=development`.

Verify the server is healthy:

```bash
curl http://localhost:8000/health
# {"status": "ok", "env": "development", "phase": "3"}
```

### Frontend

```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:3000`. Login page at `http://localhost:3000/login`.

### Port Reference

| Service | Port | Address |
|---------|------|---------|
| FastAPI backend | 8000 | `http://localhost:8000` |
| Swagger UI (dev only) | 8000 | `http://localhost:8000/docs` |
| Next.js frontend | 3000 | `http://localhost:3000` |
| PostgreSQL | 5432 | `postgresql://localhost:5432/workplace_intel` |
| WebSocket | 8000 | `ws://localhost:8000/ws/transcript/{meeting_id}` |

### Creating the First User

Register a manager account:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"name": "Admin", "email": "admin@company.com", "password": "SecurePass123!", "role": "manager"}'
```

Login and retrieve tokens:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email": "admin@company.com", "password": "SecurePass123!"}'
```

The response contains `access_token` (15-minute TTL) and `refresh_token` (7-day TTL). Pass the access token as `Authorization: Bearer {access_token}` on all protected endpoints.

---

## Running with Docker

```bash
# Build and start both services
docker compose up --build

# Backend only
docker build -t workplace-backend ./backend
docker run -p 8000:8000 --env-file backend/.env workplace-backend
```

The compose file mounts `.env` automatically. On macOS and Windows use `host.docker.internal` as the PostgreSQL host. On Linux add a `postgres` service to the compose file or use `--network host`.

---

## API Reference

All REST endpoints are prefixed with `/api/v1`. Protected endpoints require `Authorization: Bearer {access_token}`.

| Method + Path | Auth | Description |
|---------------|------|-------------|
| `POST /api/v1/auth/register` | None | Create employee or manager account |
| `POST /api/v1/auth/login` | None | Returns `access_token` (15 min) and `refresh_token` (7 days) |
| `POST /api/v1/auth/refresh` | Refresh token | Rotates refresh token, issues new access token. Reuse detection revokes entire token family. |
| `POST /api/v1/meetings/upload` | Bearer | Validate audio, store to S3, trigger Lambda pipeline, return `job_id` |
| `GET /api/v1/meetings/{id}/summary` | Bearer | Transcript, BART summary, action items JSON, decisions |
| `GET /api/v1/meetings/search` | Bearer | Full-text search via PostgreSQL `tsvector` |
| `GET /api/v1/analytics/employee/{id}` | Bearer | Productivity score, burnout risk, cluster label, 12-week trend |
| `GET /api/v1/analytics/team/{id}` | Manager | Aggregated team metrics, cluster distribution, at-risk list |
| `WS /ws/transcript/{meeting_id}` | Token query param | Streams transcription tokens to dashboard in real time |

Rate limits: 100 req/min authenticated, 20 req/min unauthenticated. Exceeded requests return HTTP 429 with `Retry-After` header.

---

## Frontend Pages

| Route | File | Description |
|-------|------|-------------|
| `/login` | `app/login/page.tsx` | NextAuth credential login. Redirects to `/dashboard` on success. |
| `/dashboard` | `app/dashboard/page.tsx` | KPI stat cards, team activity feed, quick upload widget |
| `/meetings` | `app/meetings/page.tsx` | Drag-and-drop upload, WebSocket progress bar, transcript + summary split-pane, action items list |
| `/analytics` | `app/analytics/page.tsx` | 12-week productivity trend, workload heatmap, team radar chart |
| `/employee` | `app/employee/page.tsx` | Productivity timeline, BurnoutGauge dial, action item history, ClusterBadge label |
| `/manager` | `app/manager/page.tsx` | Cluster scatter plot, at-risk alerts, decision log, PDF/CSV export. Manager role required. |

---

## ML Models

| Model | Algorithm | Key Metric | Notes |
|-------|-----------|------------|-------|
| Productivity Scoring | Random Forest (`n_estimators=200`, `max_depth=12`) | R2=0.89, RMSE=6.2 | 8 engineered features. Top feature: `consecutive_meeting_ratio` (importance=0.24) |
| Employee Clustering | KMeans `k=4` | Silhouette=0.67 | 4 archetypes: Meeting-Heavy Contributor, Deep Focus Worker, Balanced Performer, At-Risk Employee |
| Burnout Detection | Isolation Forest (`contamination=0.08`) | Precision@k=0.78 | Unsupervised. No labeled data required. Anomaly threshold `< -0.15`. Runs weekly via Lambda. |
| Summarization | BART-large-CNN (HuggingFace) | ROUGE-1=0.44, BERTScore F1=0.87 | Loaded into EC2 memory at startup. Inference ~8s per 30-min meeting. |
| Action Item Extraction | spaCy rules + GPT-3.5 hybrid | F1=0.81, Precision=0.84, Recall=0.79 | Items below confidence 0.7 flagged for human review in dashboard. |
| Speech Recognition | AWS Transcribe (primary) | WER ~7% | Async with speaker diarization. Whisper (WER ~3%) used as local dev fallback. |

Model artifacts are serialised with `joblib` and stored to S3 under `s3://{S3_BUCKET}/model-artifacts/`. The `analytics-pipeline` Lambda loads them at invocation time. Re-inference runs every Monday via CloudWatch Events.

---

## AWS Architecture

### Event-Driven Pipeline

1. User POSTs audio to `POST /api/v1/meetings/upload`
2. FastAPI validates format, stores to S3: `s3://workplace-intel/meetings/{meeting_id}/audio.mp3`
3. S3 `PutObject` event auto-triggers Lambda: `transcription-trigger`
4. Lambda submits async job to AWS Transcribe with speaker diarization (max 10 speakers)
5. Transcribe writes transcript JSON to S3, triggering Lambda: `nlp-processor`
6. NLP Lambda runs BART summarization and spaCy/GPT-3.5 action item extraction, stores to RDS `meeting_analysis`
7. `analytics-pipeline` Lambda re-scores productivity metrics with Random Forest and Isolation Forest
8. DynamoDB stream fires WebSocket notification to frontend. Total pipeline time under 3 minutes.

### Services

| Service | Role | Key Config |
|---------|------|------------|
| S3 | Audio, transcripts, model artifacts | 3 prefixes: `/meetings/` `/transcripts/` `/model-artifacts/`. SSE-KMS mandatory via bucket policy. |
| AWS Transcribe | Async ASR + speaker diarization | Triggered by S3 event. Up to 10 speakers. |
| Lambda x3 | Serverless compute chain | `transcription-trigger`, `nlp-processor`, `analytics-pipeline`. Pay-per-invocation. |
| EC2 t3.medium | FastAPI app server | BART loaded in memory at startup. Private subnet. No port 22. SSM Session Manager only. |
| RDS PostgreSQL | Primary relational DB | 6 tables. Private subnet. Accessible from EC2 security group only. |
| DynamoDB | Real-time events + WebSocket sessions | Low-latency key-value. WebSocket session registry. Encrypted by default. |
| API Gateway | Public API proxy | JWT authorizer, CORS, 429 throttling, full request logging. |
| CloudFront | CDN | Edge caching for Next.js assets. HTTP to HTTPS redirect. TLS 1.3. ACM certificate. |
| CloudWatch | Monitoring | Alarms: Lambda error rate > 1%, API P99 > 2s, RDS CPU > 80%, failed logins > 5/min. |

### IAM Roles

| Role | Allowed | Denied |
|------|---------|--------|
| `EC2InstanceRole` | s3:Get/Put on `meetings/` and `transcripts/`, rds:Connect, dynamodb:Get/Put, secretsmanager:GetSecretValue | s3:DeleteObject, rds:DeleteDBInstance, iam:* |
| `LambdaTranscribeRole` | s3:GetObject (`meetings/` only), transcribe:StartTranscriptionJob, s3:PutObject (`transcripts/` only) | All other S3 ops, RDS, EC2, IAM |
| `LambdaNLPRole` | s3:GetObject (`transcripts/` only), rds:Connect, dynamodb:PutItem, secretsmanager:GetSecretValue | s3:PutObject on `audio/`, Transcribe:*, EC2:* |
| `LambdaAnalyticsRole` | s3:GetObject (`model-artifacts/` only), rds:Connect, dynamodb:PutItem | s3:PutObject, Transcribe:*, secretsmanager:* |
| `APIGatewayRole` | lambda:InvokeFunction (JWT authorizer Lambda only) | All other actions |

---

## Security Architecture

| Layer | Controls | Service |
|-------|----------|---------|
| Perimeter | HTTPS enforcement, TLS 1.3, SQL injection blocking, XSS filtering, DDoS rate rules | CloudFront + WAF + Shield |
| API Gateway | JWT authorizer on every request, 429 throttling, CORS to allowed origins, full request logging | API Gateway + CloudWatch |
| Application | RBAC per endpoint, Pydantic v2 input validation, SQLAlchemy ORM parameterised queries only | FastAPI + slowapi |
| Network | RDS and EC2 in private subnets, ALB only public resource, Security Groups deny-all default, VPC endpoints for S3 and DynamoDB | VPC + SGs + VPC Endpoints |
| Data at Rest | S3 SSE-KMS mandatory, RDS AES-256, DynamoDB encrypted by default, all secrets in Secrets Manager with 30-day rotation | KMS + Secrets Manager |
| Audit | CloudTrail immutable logging (90-day retention), GuardDuty ML threat detection, CloudWatch anomaly alarms | CloudTrail + GuardDuty |

**Token details:** RS256 JWT (asymmetric). Private key never leaves Secrets Manager. Access token TTL = 15 minutes. Refresh token TTL = 7 days with rotation on every use. Token reuse detection revokes the entire token family. RBAC enforced in FastAPI: employees see only their own data; managers are restricted to their `team_id`.

---

## Testing

### Unit tests

```bash
cd backend
pytest tests/ -v --cov=backend --cov-report=term-missing
```

AWS services (S3, DynamoDB, Transcribe) are mocked with `moto`. Target coverage: 80%+.

### Integration smoke test

```bash
pytest tests/integration/test_pipeline.py -v
```

Uploads a 2-minute sample audio file and asserts the meeting summary is stored in the database within 5 minutes.

### Load test

```bash
locust -f tests/locustfile.py --headless -u 50 -r 5 --run-time 60s --host http://localhost:8000
```

Target: P95 API response under 500ms at 50 concurrent users.

---

## Production Deployment

### Terraform

```bash
cd cloud/
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Provisions all resources: S3 with KMS policy, RDS in private subnet, 3 Lambda functions with IAM roles, EC2 with SSM access, API Gateway with JWT authorizer, CloudFront distribution, CloudWatch alarms, GuardDuty.

### GitHub Actions CI/CD

Pipeline triggers on push to `main`:

1. Run pytest suite with coverage check
2. Build Docker image
3. Push to Amazon ECR
4. Deploy to EC2 via AWS SSM
5. Invalidate CloudFront distribution cache

Required GitHub Actions secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `JWT_PRIVATE_KEY`, `OPENAI_API_KEY`.

### Environment Differences

| Variable | Development | Production |
|----------|-------------|------------|
| `APP_ENV` | `development` | `production` (disables `/docs`) |
| `DATABASE_URL` | `localhost:5432` | RDS private endpoint from Terraform output |
| `JWT_PRIVATE_KEY` | Dev keypair pre-filled in `config.py` | New RS256 keypair from Secrets Manager |
| `NEXTAUTH_SECRET` | `change-me-in-production` | Strong random string, minimum 32 characters |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | `https://api.yourdomain.com` |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | `wss://api.yourdomain.com` |

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ModuleNotFoundError: No module named 'backend'` | uvicorn run from inside `backend/` directory | Run from repo root: `uvicorn backend.main:app --reload` |
| `asyncpg InvalidCatalogNameError` | Database does not exist | `psql -U postgres -c "CREATE DATABASE workplace_intel;"` |
| `OSError: Can't find model 'en_core_web_lg'` | spaCy model not downloaded | `python -m spacy download en_core_web_lg` |
| HTTP 401 on all endpoints | JWT keys not set in `.env` | Dev keypair is pre-filled in `core/config.py` and works immediately without `.env` config |
| CORS error in browser | Frontend origin not in `allow_origins` | Add your frontend URL to `allow_origins` in `backend/main.py` |
| S3 upload returns 403 | AWS credentials not configured | Run `aws configure` or set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in `.env` |
| NextAuth error: no secret | `NEXTAUTH_SECRET` not set | Set `NEXTAUTH_SECRET` in `frontend/.env.local` |
| CUDA / out of memory loading BART | Insufficient RAM on EC2 | Use EC2 `t3.large` (8GB RAM) or load model lazily per request |
| WebSocket connection refused locally | Lambda pipeline not deployed | In local dev, poll `GET /api/v1/meetings/{id}/summary` instead. WS requires deployed Lambda stack. |

---

## Known Limitations

- AWS Transcribe is unavailable locally. OpenAI Whisper runs as the local fallback when AWS credentials are absent or the `transcription-trigger` Lambda is not deployed.
- Meeting audio is not automatically deleted from S3 in local development. In production, an S3 lifecycle rule removes audio after transcript generation to enforce data minimisation.
- Without `GROQ_API_KEY`, summarization falls back to BART on CPU, adding approximately 8 seconds per meeting.
- ML models are trained on synthetic data (500 employees x 12 weeks). Replace with real organisational data before production use.
- WebSocket live transcription requires the full Lambda pipeline to be deployed. In local development, use polling on `GET /api/v1/meetings/{id}/summary` for status updates.

---

*AI Workplace Intelligence Platform — Version 1.0 — 2025*
