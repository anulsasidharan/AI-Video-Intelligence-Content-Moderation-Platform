# VidShield AI — Full AWS Architecture Design Document

This document synthesizes **`docs/PRD.md`**, **`docs/ARCHITECTURE.md`**, **`docs/DEPLOYMENT.md`**, **`docs/DB_SCHEMA.md`**, **`docs/API_SPEC.md`**, **`docs/HDL.md`**, and **`docs/LDL.md`** with the **Terraform modules** under `terraform/` to describe a **complete AWS-hosted architecture** for VidShield AI.

**Purpose:** Single reference for stakeholders and for importing diagrams into **[eraser.io](https://eraser.io)** (or any Mermaid-capable tool). Each diagram is in its own **fenced `mermaid` code block** — copy the block contents (including the opening ` ```mermaid ` and closing ` ``` `) into Eraser’s Mermaid import, or paste only the inner diagram source per Eraser’s UI.

**Scope note:** Third-party SaaS used by the application (**OpenAI**, **Pinecone**, **Stripe**, **SendGrid**, **Twilio**) are shown as external systems; everything else below is **AWS** or **internet clients**.

---

## Table of contents

1. [Architecture principles](#1-architecture-principles)  
2. [AWS service inventory](#2-aws-service-inventory)  
3. [Logical component map](#3-logical-component-map)  
4. [Mermaid diagrams (copy for eraser.io)](#4-mermaid-diagrams-copy-for-eraserio)  
   - [4.1 System context — users, AWS edge, compute, data](#41-diagram-1--system-context)  
   - [4.2 VPC network topology](#42-diagram-2--vpc-network-topology)  
   - [4.3 ECS Fargate services and load balancing](#43-diagram-3--ecs-fargate-services-and-load-balancing)  
   - [4.4 S3 storage and CloudFront origins](#44-diagram-4--s3-storage-and-cloudfront-origins)  
   - [4.5 Security — WAF, secrets, IAM, encryption](#45-diagram-5--security-waf-secrets-iam-encryption)  
   - [4.6 Video ingestion and presigned upload flow](#46-diagram-6--video-ingestion-sequence)  
   - [4.7 AI moderation pipeline — API, Redis, workers](#47-diagram-7--ai-moderation-pipeline-sequence)  
   - [4.8 Realtime — ALB stickiness / WebSocket and Socket.IO](#48-diagram-8--realtime-connectivity)  
   - [4.9 CI/CD — GitHub Actions, ECR, ECS](#49-diagram-9--cicd-pipeline)  
   - [4.10 Observability — CloudWatch and SNS](#410-diagram-10--observability)  
   - [4.11 High availability and failure domains](#411-diagram-11--high-availability)  
   - [4.12 Optional — SQS decoupling (Terraform module)](#412-diagram-12--optional-sqs-integration)  
5. [Data classification and boundaries](#5-data-classification-and-boundaries)  
6. [Cross-reference to repo docs](#6-cross-reference-to-repo-docs)

---

## 1. Architecture principles

| Principle | AWS expression |
|-----------|------------------|
| **Separation of tiers** | Public subnets (ALB, NAT) vs private subnets (ECS tasks, RDS, Redis) |
| **Least privilege** | IAM task roles per service; resource-based S3 policies; Secrets Manager ARNs in task definitions |
| **Encryption in transit** | TLS 1.2+ via **ACM** on **ALB** / **CloudFront**; `rediss://` to ElastiCache where TLS enabled |
| **Encryption at rest** | **RDS** storage encryption; **S3** SSE-S3 or SSE-KMS; **ElastiCache** at-rest encryption (configure in module) |
| **Defense in depth** | **WAFv2** on CloudFront + ALB (as in `terraform/main.tf`) |
| **Observable operations** | **CloudWatch** Logs/Metrics, alarms → **SNS** (monitoring module + optional email subscription) |
| **Immutable deploys** | New **ECR** image tags → new **ECS** task definitions → rolling **ECS** deployments |

---

## 2. AWS service inventory

| AWS service | Role in VidShield AI |
|-------------|----------------------|
| **Amazon VPC** | Isolated network; public/private subnets; route tables; **Internet Gateway**; **NAT Gateway(s)** |
| **Application Load Balancer (ALB)** | HTTP(S) entry for API and/or combined routing; WebSocket upgrade; target groups for ECS services |
| **Amazon ECS on AWS Fargate** | Run **API** (FastAPI + Socket.IO), **Celery worker**, **Next.js frontend** without managing EC2 |
| **Amazon ECR** | Store Docker images for API/worker/frontend; scanned on push (optional **ECR** image scanning) |
| **Amazon RDS for PostgreSQL** | Primary relational store (users, videos, moderation, billing, audits, …) per `DB_SCHEMA.md` |
| **Amazon ElastiCache for Redis** | Rate limiting, Celery broker/result backend, refresh-token / ephemeral patterns |
| **Amazon S3** | Video objects, thumbnails, generated report PDFs / artifacts (Terraform: separate buckets for videos, thumbnails, artifacts) |
| **Amazon CloudFront** | CDN for static assets / optional API caching; custom domain; origin to ALB; OAC/OAI for S3 origins where used |
| **AWS WAF** | Web ACL **CLOUDFRONT** scope + **REGIONAL** scope attached to ALB |
| **AWS Certificate Manager (ACM)** | TLS certificates for ALB and CloudFront (`certificate_arn` in Terraform) |
| **Amazon Route 53** | DNS A/AAAA alias to CloudFront and/or ALB |
| **AWS Secrets Manager** | DB password, Redis auth, `SECRET_KEY`, OpenAI/Pinecone/Sentry ARNs injected into ECS tasks |
| **AWS KMS** | Customer-managed keys for S3, RDS, Secrets Manager (recommended); envelope encryption |
| **AWS IAM** | Execution roles (pull from ECR, write logs); task roles (S3, SQS, Secrets) |
| **Amazon CloudWatch Logs** | Container logs per ECS service |
| **Amazon CloudWatch Metrics / Alarms** | ECS/RDS/Redis/ALB metrics; 5xx thresholds (monitoring module) |
| **Amazon SNS** | Alarm notifications; optional fan-out to email/Lambda |
| **Amazon SQS** | Optional durable queues for high-volume async work (Terraform `module "sqs"`; extend workers to consume) |
| **AWS Systems Manager Parameter Store** | Optional alternative to Secrets Manager for non-secret config |
| **AWS X-Ray** | Optional distributed tracing (instrument app / sidecar) |
| **Amazon GuardDuty / Security Hub** | Org-level threat and compliance (operations) |
| **AWS Backup** | RDS/S3 backup policies (operations) |
| **Amazon EventBridge** | Scheduled rules (e.g. complement Celery Beat externally) or react to S3 events |
| **AWS Lambda** | Optional: S3 trigger for virus scan, image optimization, or SQS consumer |
| **Amazon SES** | Optional alternative or supplement to SendGrid for outbound email |

**External (non-AWS) integrations (from PRD / code):** OpenAI, Pinecone, Stripe, SendGrid, Twilio.

---

## 3. Logical component map

| Product capability (PRD) | Primary AWS hosts | Supporting AWS |
|----------------------------|-------------------|------------------|
| Web UI + same-origin API | ECS Fargate (frontend + API targets), ALB, CloudFront | WAF, ACM, Route 53 |
| REST `/api/v1` + Socket.IO | ECS Fargate (API service) | ALB stickiness / WebSocket aware idle timeout |
| Celery workers | ECS Fargate (worker service) | ElastiCache Redis; optional SQS |
| PostgreSQL | RDS PostgreSQL Multi-AZ (optional) | KMS, Secrets Manager, automated backups |
| Object storage | S3 (videos, thumbnails, artifacts) | IAM task role; presigned URLs from API |
| Rate limits / cache | ElastiCache Redis | VPC security groups |
| Observability | CloudWatch Logs/Metrics, SNS | Alarm dashboards |
| IaC / drift control | Terraform state in S3 + DynamoDB lock | IAM for CI deploy role |

---

## 4. Mermaid diagrams (copy for eraser.io)

> **How to use in Eraser.io:** Create a new diagram → choose **Mermaid** (or import) → paste one full code block below. If Eraser expects **only** the diagram body, omit the outer markdown fences and paste from `flowchart` / `sequenceDiagram` onward.

---

### 4.1 Diagram 1 — System context

```mermaid
flowchart TB
  subgraph internet["Internet"]
    U[Operators and admins]
    P[Partner API clients]
  end

  subgraph aws["AWS Cloud"]
    subgraph edge["Edge and routing"]
      R53[Route 53]
      CF[CloudFront]
      WAF_CF[WAF Web ACL CloudFront scope]
      ACM[ACM Certificates]
    end
    subgraph compute["Compute"]
      ALB[Application Load Balancer]
      WAF_ALB[WAF Web ACL Regional ALB]
      ECS_API[ECS Fargate Service - FastAPI and Socket.IO]
      ECS_FE[ECS Fargate Service - Next.js]
      ECS_WK[ECS Fargate Service - Celery Worker]
    end
    subgraph data["Data services"]
      RDS[(RDS PostgreSQL)]
      REDIS[(ElastiCache Redis)]
      S3V[S3 Videos bucket]
      S3T[S3 Thumbnails bucket]
      S3A[S3 Artifacts bucket]
    end
    subgraph secops["Security and operations"]
      SM[Secrets Manager]
      CW[CloudWatch Logs and Metrics]
      SNS[SNS Alarm topic]
      KMS[KMS Keys]
    end
  end

  subgraph external["External SaaS"]
    OAI[OpenAI]
    PC[Pinecone]
    ST[Stripe]
    SG[SendGrid]
    TW[Twilio]
  end

  U --> R53
  P --> R53
  R53 --> CF
  WAF_CF --> CF
  CF --> ACM
  CF --> ALB
  WAF_ALB --> ALB
  ALB --> ECS_FE
  ALB --> ECS_API
  ECS_API --> RDS
  ECS_API --> REDIS
  ECS_API --> S3V
  ECS_API --> S3T
  ECS_API --> S3A
  ECS_WK --> RDS
  ECS_WK --> REDIS
  ECS_WK --> S3V
  ECS_WK --> S3A
  ECS_API --> SM
  ECS_WK --> SM
  ECS_API --> OAI
  ECS_WK --> OAI
  ECS_WK --> PC
  ECS_API --> ST
  ECS_API --> SG
  ECS_API --> TW
  CW --> SNS
  ECS_API --> CW
  ECS_FE --> CW
  ECS_WK --> CW
  KMS -.-> RDS
  KMS -.-> S3V
  KMS -.-> SM
```

---

### 4.2 Diagram 2 — VPC network topology

```mermaid
flowchart TB
  subgraph vpc["VPC"]
    subgraph pub["Public subnets"]
      IGW[Internet Gateway]
      NAT[NAT Gateway]
      ALB[Application Load Balancer]
    end
    subgraph priv["Private subnets - AZ A and B"]
      subgraph ecs_az["ECS Fargate tasks"]
        T_API[Task - API]
        T_FE[Task - Frontend]
        T_WK[Task - Worker]
      end
      RDS[(RDS PostgreSQL)]
      REDIS[(ElastiCache Redis)]
    end
  end

  IGW --> ALB
  ALB --> T_API
  ALB --> T_FE
  T_API --> RDS
  T_API --> REDIS
  T_WK --> RDS
  T_WK --> REDIS
  T_API --> NAT
  T_FE --> NAT
  T_WK --> NAT
  NAT --> IGW
```

---

### 4.3 Diagram 3 — ECS Fargate services and load balancing

```mermaid
flowchart LR
  CF[CloudFront]
  ALB[ALB]
  TG_FE[Target Group - Frontend port 3000]
  TG_API[Target Group - API port 8000]
  SVC_FE[ECS Service - vidshield-frontend]
  SVC_API[ECS Service - vidshield-api]
  SVC_WK[ECS Service - vidshield-worker]
  TD_FE[Task Definition - Frontend container]
  TD_API[Task Definition - API container]
  TD_WK[Task Definition - Worker container]
  ECR_FE[ECR - frontend image]
  ECR_API[ECR - backend image]
  ECR_WK[ECR - worker image same backend image]

  CF --> ALB
  ALB --> TG_FE
  ALB --> TG_API
  TG_FE --> SVC_FE
  TG_API --> SVC_API
  SVC_FE --> TD_FE
  SVC_API --> TD_API
  SVC_WK --> TD_WK
  TD_FE --> ECR_FE
  TD_API --> ECR_API
  TD_WK --> ECR_WK
```

---

### 4.4 Diagram 4 — S3 storage and CloudFront origins

```mermaid
flowchart TB
  CF[CloudFront Distribution]
  O_ALB[Origin - ALB DNS]
  O_S3T[Origin - S3 thumbnails bucket]
  OAI[Origin Access Control or OAI]
  ALB[ALB]
  S3V[S3 - videos]
  S3T[S3 - thumbnails]
  S3A[S3 - artifacts and reports]

  CF --> O_ALB
  CF --> O_S3T
  O_ALB --> ALB
  O_S3T --> OAI
  OAI --> S3T
  ALB -->|API presigned URLs| S3V
  ALB -->|API presigned URLs| S3A
```

---

### 4.5 Diagram 5 — Security (WAF, secrets, IAM, encryption)

```mermaid
flowchart TB
  subgraph client["Client"]
    BR[Browser]
  end
  subgraph edge["Edge"]
    WAF1[WAF CloudFront scope]
    CF[CloudFront]
    WAF2[WAF Regional ALB]
    ALB[ALB with ACM listener]
  end
  subgraph compute["ECS Fargate"]
    TASK[Task]
    EXEC[IAM Task Execution Role - ECR and Logs]
    ROLE[IAM Task Role - S3 SQS Secrets]
  end
  subgraph secrets["Secrets"]
    SM[Secrets Manager]
  end
  subgraph crypto["Encryption"]
    KMS[KMS CMK]
  end

  BR --> WAF1
  WAF1 --> CF
  CF --> WAF2
  WAF2 --> ALB
  ALB --> TASK
  TASK --> EXEC
  TASK --> ROLE
  ROLE --> SM
  ROLE --> KMS
  TASK --> SM
```

---

### 4.6 Diagram 6 — Video ingestion (sequence)

```mermaid
sequenceDiagram
  autonumber
  participant B as Browser
  participant CF as CloudFront
  participant ALB as ALB
  participant API as ECS API FastAPI
  participant SM as Secrets Manager
  participant S3 as S3 Videos bucket
  participant RDS as RDS PostgreSQL
  participant R as ElastiCache Redis
  participant W as ECS Celery Worker

  B->>CF: HTTPS POST /api/v1/videos/upload-url
  CF->>ALB: Forward
  ALB->>API: JWT authorized request
  API->>SM: Get AWS credentials if needed
  API->>S3: Generate presigned PUT URL
  API->>RDS: Insert or update video row
  API-->>B: Return presigned URL JSON
  B->>S3: PUT video bytes directly to S3
  B->>CF: POST /api/v1/videos or status poll
  CF->>ALB: Forward
  ALB->>API: Confirm processing
  API->>R: Enqueue Celery task metadata
  API->>W: Async via Redis broker
  W->>S3: GET object for FFmpeg processing
  W->>RDS: Update status and moderation links
```

---

### 4.7 Diagram 7 — AI moderation pipeline (sequence)

```mermaid
sequenceDiagram
  autonumber
  participant W as Celery Worker ECS
  participant RDS as RDS PostgreSQL
  participant S3 as S3
  participant OAI as OpenAI API
  participant PC as Pinecone API
  participant R as Redis broker
  participant API as ECS API
  participant WH as Customer webhook HTTPS

  W->>R: Consume moderation task
  W->>RDS: Load video and policy
  W->>S3: Fetch frames or transcript inputs
  W->>OAI: Vision and text moderation calls
  W->>PC: Similarity search optional
  W->>RDS: Persist moderation_results and queue
  W->>API: N/A async only
  W->>WH: POST webhook outbound via worker or API task
```

---

### 4.8 Diagram 8 — Realtime connectivity

```mermaid
flowchart LR
  subgraph browser["Browser"]
    APP[Next.js app]
    SIO[socket.io-client]
  end
  subgraph aws["AWS"]
    CF[CloudFront optional]
    ALB[ALB - WebSocket idle timeout configured]
    API[ECS API - ASGI Socket.IO and FastAPI WS]
    REDIS[(Redis for rooms scale-out optional)]
  end

  APP -->|HTTPS same origin /api/v1| CF
  CF --> ALB
  SIO -->|wss via ALB| ALB
  ALB -->|Upgrade WebSocket| API
  API --> REDIS
```

**Design note:** Sticky sessions on ALB target group help Socket.IO long-polling; WebSocket idle timeout on ALB should exceed expected quiet periods for live streams.

---

### 4.9 Diagram 9 — CI/CD pipeline

```mermaid
flowchart LR
  subgraph gh["GitHub"]
    REPO[Repository]
    GA[GitHub Actions]
  end
  subgraph aws_ci["AWS"]
    ECR_A[ECR API image]
    ECR_W[ECR Worker image]
    ECR_F[ECR Frontend image]
    ECS[ECS cluster services]
    CFN[CloudFront invalidation optional]
  end

  REPO --> GA
  GA -->|docker build push| ECR_A
  GA -->|docker build push| ECR_W
  GA -->|docker build push| ECR_F
  GA -->|register task def and update-service| ECS
  GA -->|create-invalidation| CFN
```

---

### 4.10 Diagram 10 — Observability

```mermaid
flowchart TB
  subgraph ecs["ECS Fargate"]
    API[API tasks]
    WK[Worker tasks]
    FE[Frontend tasks]
  end
  subgraph cw["Amazon CloudWatch"]
    LG[Log Groups per service]
    MT[Metrics - CPU Memory Request count]
    AL[Alarms on 5xx latency RDS CPU Redis evictions]
  end
  SNS[Amazon SNS topic]
  OPS[Email or Chat ops endpoint]

  API --> LG
  WK --> LG
  FE --> LG
  API --> MT
  ALB[ALB] --> MT
  MT --> AL
  AL --> SNS
  SNS --> OPS
```

---

### 4.11 Diagram 11 — High availability

```mermaid
flowchart TB
  subgraph region["Single Region - Multi AZ"]
    subgraph az1["Availability Zone 1"]
      ECS1[ECS tasks]
      RDS_PRI[RDS primary]
      REDIS1[ElastiCache shard primary]
    end
    subgraph az2["Availability Zone 2"]
      ECS2[ECS tasks]
      RDS_STBY[RDS standby replica when Multi-AZ]
      REDIS2[ElastiCache replica node]
    end
    ALB[ALB cross-zone enabled]
  end

  ALB --> ECS1
  ALB --> ECS2
  ECS1 --> RDS_PRI
  ECS2 --> RDS_PRI
  RDS_PRI -.-> RDS_STBY
  ECS1 --> REDIS1
  ECS2 --> REDIS1
  REDIS1 -.-> REDIS2
```

---

### 4.12 Diagram 12 — Optional SQS integration (Terraform)

```mermaid
flowchart LR
  API[ECS API]
  Q1[SQS queue - ingest or moderation]
  W[ECS Worker]
  DLQ[SQS DLQ]
  RDS[(RDS)]

  API -->|SendMessage| Q1
  Q1 -->|ReceiveMessage| W
  Q1 -.->|failed retries| DLQ
  W --> RDS
```

The repository includes **`module "sqs"`** in `terraform/main.tf`; Celery today uses **Redis** as broker. SQS can be used for **cross-service buffering**, **fan-out**, or future **Lambda** consumers while keeping Redis for Celery if desired.

---

## 5. Data classification and boundaries

| Data class | Examples | AWS storage / transit |
|------------|----------|-------------------------|
| **Credentials / keys** | DB password, `SECRET_KEY`, API keys | **Secrets Manager** + **KMS**; never in images |
| **PII** | User email, profile, audit logs | **RDS** encrypted; restrict IAM; retention policies |
| **Video content** | Uploads, thumbnails | **S3** buckets with lifecycle and access logging |
| **AI artifacts** | Embeddings metadata, reports | **S3 artifacts**; Pinecone vectors outside AWS |
| **Sessions / rate limits** | JWT refresh keys, rate limit counters | **Elastiache Redis** with TLS in production |

---

## 6. Cross-reference to repo docs

| Topic | Document |
|-------|----------|
| Product features | [PRD.md](PRD.md) |
| Code-level structure | [ARCHITECTURE.md](ARCHITECTURE.md), [LDL.md](LDL.md) |
| Conceptual design | [HDL.md](HDL.md) |
| HTTP API | [API_SPEC.md](API_SPEC.md) |
| Tables and migrations | [DB_SCHEMA.md](DB_SCHEMA.md) |
| Commands, compose, CI/CD names | [DEPLOYMENT.md](DEPLOYMENT.md) |
| PNG architecture pack | `docs/architecture_images/*.png` |

---

**End of document.** For Eraser.io, import diagrams **one section at a time** to tune layout (Eraser auto-layout may differ from GitHub rendering).
