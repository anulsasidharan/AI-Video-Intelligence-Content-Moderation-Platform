from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total_videos_processed: int
    total_violations_detected: int
    violation_rate_percent: float
    avg_confidence: float
    videos_approved: int
    videos_rejected: int
    videos_escalated: int
    top_violation_categories: list[dict]  # [{ category, count }]


class ViolationDataPoint(BaseModel):
    date: str  # YYYY-MM-DD
    count: int
    category: str | None = None


class ViolationBreakdown(BaseModel):
    category: str
    count: int
    percentage: float


class ViolationsResponse(BaseModel):
    time_series: list[ViolationDataPoint]
    breakdown: list[ViolationBreakdown]
    total: int
    date_from: str
    date_to: str
