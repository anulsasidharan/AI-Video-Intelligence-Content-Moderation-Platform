from fastapi import APIRouter

from app.api.v1 import (
    admin_billing,
    agent_audit,
    alerts,
    analytics,
    api_keys,
    audit,
    auth,
    billing,
    live,
    moderation,
    newsletter,
    notifications,
    policies,
    reports,
    stripe_webhook,
    support_tickets,
    users,
    videos,
    webhooks,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(newsletter.router)
api_router.include_router(billing.router)
api_router.include_router(stripe_webhook.router)
api_router.include_router(admin_billing.router)
api_router.include_router(users.router)
api_router.include_router(videos.router)
api_router.include_router(moderation.router)
api_router.include_router(analytics.router)
api_router.include_router(live.router)
api_router.include_router(policies.router)
api_router.include_router(webhooks.router)
api_router.include_router(audit.router)
api_router.include_router(alerts.router)
api_router.include_router(api_keys.router)
api_router.include_router(agent_audit.router)
api_router.include_router(reports.router)
api_router.include_router(support_tickets.router)
api_router.include_router(notifications.router)
