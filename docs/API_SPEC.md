# VidShield AI — HTTP API Specification (As Implemented)

**Base path:** `/api/v1`  
**App version:** `0.1.0` (from `app/main.py`)  
**OpenAPI:** `/docs` and `/redoc` when `APP_ENV != "production"` (disabled in production config).

---

## 1. Conventions

### 1.1 Success envelope

For most JSON responses on **2xx**, `DataWrapperMiddleware` wraps the payload:

```json
{ "data": { ... } }
```

If the handler already returns `{"data": ...}` or `{"error": ...}`, it is not double-wrapped. Paths skipped: `/health`, `/docs`, `/redoc`, `/openapi.json`.

### 1.2 Error envelope

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Video not found. id=…",
    "details": {}
  }
}
```

**Common codes** (from `app/core/exceptions.py`):

| HTTP | `code` |
|------|--------|
| 401 | `UNAUTHORIZED` |
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 409 | `CONFLICT` |
| 422 | `VALIDATION_ERROR` (also FastAPI `RequestValidationError` with `details.fields[]`) |
| 429 | `RATE_LIMIT_EXCEEDED` (`details.retry_after_seconds`) |
| 500 | `INTERNAL_SERVER_ERROR` |

### 1.3 Authentication

- **Bearer JWT** header: `Authorization: Bearer <access_token>`  
- Access tokens must contain `"type": "access"` in payload (`deps.get_current_user`).
- **Roles:** `admin`, `operator`, `api_consumer` — enforced per-route via `AdminUser`, `OperatorUser`, or `CurrentUser`.

### 1.4 Pagination

- Many list endpoints use `page` / `page_size` or `skip` / `limit` as implemented in each router (defaults often align with `settings.DEFAULT_PAGE_SIZE` / `MAX_PAGE_SIZE`).

### 1.5 Rate limiting

Redis-backed per-IP tiers (`app/core/rate_limit.py`). Auth and sensitive routes use stricter tiers. **429** uses `RateLimitError` envelope; `Retry-After` header set in middleware.

---

## 2. Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | `{"status":"ok","env":...}` — not wrapped |

---

## 3. Auth (`/api/v1/auth`)

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | `/auth/register` | No | Creates user; returns token pair (`LoginResponse`) |
| POST | `/auth/login` | No | Returns `LoginResponse`; writes access audit |
| POST | `/auth/refresh` | No | Body with refresh token |
| POST | `/auth/logout` | No | Invalidates refresh session |
| GET | `/auth/me` | Bearer | Current user profile |
| POST | `/auth/forgot-password` | No | Sends reset flow |
| POST | `/auth/reset-password` | No | Consumes reset token |

**Schemas:** see `app/schemas/auth.py` (`LoginRequest`, `RegisterRequest`, `TokenPair`, `ForgotPasswordRequest`, `ResetPasswordRequest`, etc.).

---

## 4. Users (`/api/v1/users`)

| Method | Path | Auth |
|--------|------|------|
| PATCH | `/users/me/password` | Bearer |
| PATCH | `/users/me/profile` | Bearer |
| GET | `/users` | Admin |
| POST | `/users` | Admin |
| PATCH | `/users/{user_id}` | Admin |
| DELETE | `/users/{user_id}` | Admin |

**Schemas:** `app/schemas/user.py`.

---

## 5. Videos (`/api/v1/videos`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/videos` | Bearer |
| POST | `/videos/upload-url` | Bearer |
| POST | `/videos/analyze-url` | Bearer |
| POST | `/videos/check-duplicates` | Bearer |
| POST | `/videos` | Bearer |
| GET | `/videos/{video_id}` | Bearer |
| GET | `/videos/{video_id}/status` | Bearer |
| PUT | `/videos/{video_id}` | Bearer |
| POST | `/videos/bulk-delete` | Bearer |
| DELETE | `/videos/{video_id}` | Bearer |

**Notes:** Several mutations require `OperatorUser` or ownership checks inside handler — see `videos.py` for exact rules.

**Storage:** Presigned upload and playback URLs are backed by **Google Cloud Storage (GCS)** (`GCS_BUCKET_NAME`, signed URL settings in `config.py`).

---

## 6. Moderation (`/api/v1/moderation`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/moderation/queue` | Bearer |
| GET | `/moderation/videos/{video_id}` | Bearer |
| POST | `/moderation/{moderation_id}/review` | Operator |
| PUT | `/moderation/{moderation_id}/override` | Admin |
| DELETE | `/moderation/queue/clear` | Operator |
| DELETE | `/moderation/queue/{item_id}` | Operator |

**Schemas:** `app/schemas/moderation.py`.

---

## 7. Policies (`/api/v1/policies`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/policies` | Bearer |
| POST | `/policies` | Bearer |
| GET | `/policies/{policy_id}` | Bearer |
| PATCH | `/policies/{policy_id}/toggle` | Bearer |
| PUT | `/policies/{policy_id}` | Bearer |
| DELETE | `/policies/{policy_id}` | Bearer |

---

## 8. Live (`/api/v1/live`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/live/streams` | Bearer |
| POST | `/live/streams` | Bearer |
| GET | `/live/streams/{stream_id}` | Bearer |
| POST | `/live/streams/{stream_id}/stop` | Bearer |
| POST | `/live/streams/{stream_id}/start-moderation` | Bearer |
| POST | `/live/streams/{stream_id}/stop-moderation` | Bearer |
| POST | `/live/streams/{stream_id}/frames` | Bearer |
| GET | `/live/streams/{stream_id}/alerts` | Bearer |
| WS | `/live/ws/streams/{stream_id}` | WebSocket auth per handler |

**Schemas:** `app/schemas/live.py`.

---

## 9. Alerts (`/api/v1/alerts`)

| Method | Path | Auth |
|--------|------|------|
| POST | `/alerts` | Bearer |
| GET | `/alerts` | Bearer |
| PATCH | `/alerts/{alert_id}/dismiss` | Bearer |
| POST | `/alerts/dismiss-all` | Bearer |

---

## 10. Analytics (`/api/v1/analytics`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/analytics/summary` | Bearer |
| GET | `/analytics/violations` | Bearer |
| GET | `/analytics/export` | Bearer |

---

## 11. Webhooks (`/api/v1/webhooks`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/webhooks` | Bearer |
| POST | `/webhooks` | Bearer |
| GET | `/webhooks/{endpoint_id}` | Bearer |
| PUT | `/webhooks/{endpoint_id}` | Bearer |
| DELETE | `/webhooks/{endpoint_id}` | Bearer |
| POST | `/webhooks/test/{endpoint_id}` | Bearer |

---

## 12. Audit (`/api/v1/audit`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/audit/access` | Admin |
| GET | `/audit/moderation` | Admin |

Query params include pagination (`skip`, `limit`) and filters as defined in `audit.py`.

---

## 13. API keys (`/api/v1/api-keys`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/api-keys` | Bearer |
| POST | `/api-keys` | Bearer |
| PATCH | `/api-keys/{key_id}` | Bearer |
| DELETE | `/api-keys/{key_id}` | Bearer |

**Create response** includes **plaintext key once** (`ApiKeyCreateResponse`).

---

## 14. Agent audit (admin)

| Method | Path | Auth |
|--------|------|------|
| GET | `/admin/agent-audit` | Admin |
| GET | `/admin/agent-audit/` | Admin |

**Alias (same handler, hidden from OpenAPI duplicate):**

| Method | Path |
|--------|------|
| GET | `/api/admin/agent-audit` |
| GET | `/api/admin/agent-audit/` |

---

## 15. Reports (`/api/v1/reports`)

| Method | Path | Auth |
|--------|------|------|
| POST | `/reports/preview` | Bearer |
| POST | `/reports/generate` | Bearer |
| GET | `/reports/` | Bearer |
| GET | `/reports/templates` | Bearer |
| POST | `/reports/templates` | Bearer |
| DELETE | `/reports/templates/{template_id}` | Bearer |
| GET | `/reports/{job_id}` | Bearer |
| GET | `/reports/{job_id}/download` | Bearer |
| DELETE | `/reports/{job_id}` | Bearer |

---

## 16. Support tickets (`/api/v1/support-tickets`)

| Method | Path | Auth |
|--------|------|------|
| POST | `/support-tickets` | **Public** |
| GET | `/support-tickets` | Admin |
| PATCH | `/support-tickets/{ticket_id}` | Admin |

---

## 17. Newsletter (`/api/v1/newsletter`)

| Method | Path | Auth |
|--------|------|------|
| POST | `/newsletter` | No |

---

## 18. Billing (`/api/v1/billing`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/billing/subscription` | Bearer |
| GET | `/billing/payments` | Bearer |
| GET | `/billing/payments/{payment_id}/invoice` | Bearer |
| POST | `/billing/checkout` | Bearer |
| POST | `/billing/portal` | Bearer |
| POST | `/billing/sync-payments` | Bearer |
| POST | `/billing/sync` | Bearer |
| POST | `/billing/webhook` | Stripe signature | **Not in OpenAPI** |

---

## 19. Admin billing (`/api/v1/admin/billing`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/admin/billing/revenue` | Admin |
| GET | `/admin/billing/subscribers` | Admin |

---

## 20. Notifications (`/api/v1/notifications`)

| Method | Path | Auth |
|--------|------|------|
| GET | `/notifications` | Bearer |
| PATCH | `/notifications/{notification_id}/read` | Bearer |
| POST | `/notifications/read-all` | Bearer |
| DELETE | `/notifications/{notification_id}` | Bearer |
| GET | `/notifications/preferences` | Bearer |
| PUT | `/notifications/preferences` | Bearer |
| POST | `/notifications/send` | Operator (dependency `OperatorUser`) |
| GET | `/notifications/event-types` | Bearer |

---

## 21. Socket.IO

- **URL:** same host as API; path **`/socket.io/`** (Engine.IO handshake).
- **CORS:** uses `settings.CORS_ORIGINS`.
- **Server:** `python-socketio` async mode; events: `join`, `leave` with `{ room }` payload.

---

## 22. WebSocket (FastAPI native)

- **`/api/v1/live/ws/streams/{stream_id}`** — see `live.py` for protocol / auth.

---

## 23. Implementation notes for API consumers

1. Always expect **`{ "data": ... }`** on success unless calling `/health` or hitting an unwrapped handler.
2. Send **`Content-Type: application/json`** on JSON bodies.
3. **Stripe webhook** must receive the **raw body** for signature verification — configure Stripe to call `/api/v1/billing/webhook`.
4. OpenAPI JSON: `/openapi.json` (when docs enabled) for exhaustive schema names.

---

## 24. Related documents

- **[DEPLOYMENT.md](DEPLOYMENT.md)** — runtime topology, CI/CD, environment variables  
- **[GCP_DEPLOYMENT_RUNBOOK.md](GCP_DEPLOYMENT_RUNBOOK.md)** — manual GCP setup  
- **[GCP-ARCHITECTURE-DESIGN.md](GCP-ARCHITECTURE-DESIGN.md)** — platform diagrams
