# CLAUDE.md — AI Video Intelligence & Content Moderation Platform

## Project Overview

VidShield AI is an enterprise-grade AI Video Intelligence & Content Moderation Platform that analyzes live and recorded videos for content safety, metadata extraction, object/scene recognition, and actionable insights. It targets YouTube-like platforms, edtech, social media, and surveillance use cases. The entire system is designed for **fully autonomous operation** — zero human intervention from ingestion to moderation decisions to deployment.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router), React 18, Tailwind CSS 3, shadcn/ui, Zustand, React Query, Socket.IO client |
| Backend | Python 3.12, FastAPI, Uvicorn, Celery, Redis, SQLAlchemy 2.0, Alembic |
| AI/ML | OpenAI GPT-4o / GPT-4o-mini (vision + text), OpenAI Whisper, LangChain 0.2+, LangGraph |
| Video Processing | FFmpeg, OpenCV, PyAV |
| Database | PostgreSQL 16, Redis 7 (cache + broker), Pinecone (vector store) |
| Storage | AWS S3 (video + thumbnails + artifacts) |
| Infrastructure | AWS ECS Fargate, ALB, CloudFront, RDS, ElastiCache, SQS, Lambda, ECR |
| CI/CD | GitHub Actions, Docker, Terraform, AWS CDK |
| Monitoring | CloudWatch, Prometheus, Grafana, Sentry |

## Project Structure

```
vidshield-ai/
├── CLAUDE.md
├── PRD.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── modules/
│   │   ├── vpc/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── elasticache/
│   │   ├── s3/
│   │   ├── cloudfront/
│   │   ├── sqs/
│   │   └── monitoring/
│   └── environments/
│       ├── dev.tfvars
│       ├── staging.tfvars
│       └── prod.tfvars
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   ├── Dockerfile
│   ├── public/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── (auth)/
│   │   │   │   ├── login/page.tsx
│   │   │   │   └── register/page.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── analytics/page.tsx
│   │   │   │   └── settings/page.tsx
│   │   │   ├── videos/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── [id]/page.tsx
│   │   │   │   └── upload/page.tsx
│   │   │   ├── moderation/
│   │   │   │   ├── page.tsx
│   │   │   │   ├── queue/page.tsx
│   │   │   │   └── policies/page.tsx
│   │   │   ├── live/
│   │   │   │   ├── page.tsx
│   │   │   │   └── [streamId]/page.tsx
│   │   │   └── api/
│   │   │       └── [...proxy]/route.ts
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui primitives
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Footer.tsx
│   │   │   ├── video/
│   │   │   │   ├── VideoPlayer.tsx
│   │   │   │   ├── VideoCard.tsx
│   │   │   │   ├── UploadDropzone.tsx
│   │   │   │   ├── TimelineAnnotation.tsx
│   │   │   │   └── FrameInspector.tsx
│   │   │   ├── moderation/
│   │   │   │   ├── ModerationBadge.tsx
│   │   │   │   ├── PolicyEditor.tsx
│   │   │   │   ├── ViolationCard.tsx
│   │   │   │   └── ReviewPanel.tsx
│   │   │   ├── analytics/
│   │   │   │   ├── InsightChart.tsx
│   │   │   │   ├── HeatmapOverlay.tsx
│   │   │   │   └── StatCard.tsx
│   │   │   └── live/
│   │   │       ├── StreamMonitor.tsx
│   │   │       ├── AlertBanner.tsx
│   │   │       └── LiveFeed.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useVideo.ts
│   │   │   ├── useModeration.ts
│   │   │   ├── useWebSocket.ts
│   │   │   └── useAnalytics.ts
│   │   ├── stores/
│   │   │   ├── authStore.ts
│   │   │   ├── videoStore.ts
│   │   │   └── moderationStore.ts
│   │   ├── lib/
│   │   │   ├── api.ts
│   │   │   ├── socket.ts
│   │   │   ├── utils.ts
│   │   │   └── constants.ts
│   │   └── types/
│   │       ├── video.ts
│   │       ├── moderation.ts
│   │       ├── analytics.ts
│   │       └── user.ts
│   └── tests/
│       ├── components/
│       └── e2e/
├── backend/
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── videos.py
│   │   │   │   ├── moderation.py
│   │   │   │   ├── analytics.py
│   │   │   │   ├── live.py
│   │   │   │   ├── policies.py
│   │   │   │   └── webhooks.py
│   │   │   └── deps.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── video.py
│   │   │   ├── moderation.py
│   │   │   ├── policy.py
│   │   │   ├── analytics.py
│   │   │   └── alert.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── video.py
│   │   │   ├── moderation.py
│   │   │   ├── policy.py
│   │   │   └── analytics.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── video_service.py
│   │   │   ├── moderation_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── storage_service.py
│   │   │   ├── notification_service.py
│   │   │   └── stream_service.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── orchestrator.py
│   │   │   │   ├── content_analyzer.py
│   │   │   │   ├── safety_checker.py
│   │   │   │   ├── metadata_extractor.py
│   │   │   │   ├── scene_classifier.py
│   │   │   │   └── report_generator.py
│   │   │   ├── chains/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── moderation_chain.py
│   │   │   │   ├── insight_chain.py
│   │   │   │   └── summary_chain.py
│   │   │   ├── graphs/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── video_analysis_graph.py
│   │   │   │   └── moderation_workflow.py
│   │   │   ├── tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── frame_extractor.py
│   │   │   │   ├── audio_transcriber.py
│   │   │   │   ├── ocr_tool.py
│   │   │   │   ├── object_detector.py
│   │   │   │   └── similarity_search.py
│   │   │   └── prompts/
│   │   │       ├── __init__.py
│   │   │       ├── moderation_prompts.py
│   │   │       ├── analysis_prompts.py
│   │   │       └── summary_prompts.py
│   │   ├── workers/
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py
│   │   │   ├── video_tasks.py
│   │   │   ├── moderation_tasks.py
│   │   │   ├── analytics_tasks.py
│   │   │   └── cleanup_tasks.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── exceptions.py
│   │   │   ├── middleware.py
│   │   │   └── logging.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── video_utils.py
│   │       ├── image_utils.py
│   │       └── time_utils.py
│   └── tests/
│       ├── conftest.py
│       ├── test_api/
│       ├── test_services/
│       ├── test_ai/
│       └── test_workers/
└── .github/
    └── workflows/
        ├── ci.yml
        ├── cd-staging.yml
        └── cd-prod.yml
```

## Key Commands

```bash
# Local Development
make dev                    # Start all services via docker-compose
make dev-frontend           # Frontend only (next dev on port 3000)
make dev-backend            # Backend only (uvicorn on port 8000)
make dev-worker             # Celery worker

# Testing
make test                   # Run all tests
make test-backend           # pytest backend/
make test-frontend          # jest + playwright frontend/
make lint                   # ruff + eslint

# Database
make db-migrate             # alembic upgrade head
make db-revision MSG="..."  # alembic revision --autogenerate

# Infrastructure
make tf-plan ENV=dev        # terraform plan
make tf-apply ENV=dev       # terraform apply
make deploy ENV=staging     # full deploy pipeline

# Docker
make build                  # build all images
make push                   # push to ECR
```

## Coding Conventions

- **Python**: ruff formatter + linter, type hints on all public functions, async-first
- **TypeScript**: strict mode, no `any`, prefer `interface` over `type` for objects
- **API**: REST with `/api/v1/` prefix, consistent error envelope `{ error: { code, message, details } }`
- **Commits**: conventional commits (`feat:`, `fix:`, `chore:`, etc.)
- **Branches**: `feat/*`, `fix/*`, `chore/*` off `main`
- **env vars**: never committed, all secrets via AWS Secrets Manager, local via `.env` files (gitignored)

## AI Agent Architecture

The system uses **LangGraph** to orchestrate a multi-agent pipeline:

1. **Orchestrator Agent** — receives video analysis requests, delegates to specialist agents
2. **Content Analyzer** — GPT-4o vision on sampled frames for scene/content understanding
3. **Safety Checker** — policy-aware moderation using configurable rule sets
4. **Metadata Extractor** — pulls entities, topics, brands, text (OCR) from frames + transcript
5. **Scene Classifier** — categorizes scenes (violence, nudity, drugs, hate symbols, etc.)
6. **Report Generator** — synthesizes all agent outputs into structured moderation report

All agents are autonomous — no human-in-the-loop required for standard moderation decisions. Escalation to human review is optional and configurable per policy.
