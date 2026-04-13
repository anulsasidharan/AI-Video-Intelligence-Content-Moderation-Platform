"""
Pydantic v2 schemas for AI agent inputs and outputs.

These schemas are the contracts between agents and the orchestrator.
They are also used to validate the final moderation report before it
is persisted to the database.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator

# ── Enums ────────────────────────────────────────────────────────────────────


class ViolationSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ModerationDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"  # needs human review
    NEEDS_REVIEW = "needs_review"


class SceneCategory(StrEnum):
    """Flat categories (legacy). Use GarmCategory for brand-safety alignment."""

    SAFE = "safe"
    VIOLENCE = "violence"
    NUDITY = "nudity"
    DRUGS = "drugs"
    HATE_SYMBOLS = "hate_symbols"
    SELF_HARM = "self_harm"
    SPAM = "spam"
    MISINFORMATION = "misinformation"
    SYNTHETIC_MEDIA = "synthetic_media"  # AI-generated / deepfake
    OTHER = "other"


class GarmCategory(StrEnum):
    """
    GARM Brand Safety taxonomy (11 categories).
    Maps to SceneCategory where applicable.
    """

    ADULT_EXPLICIT = "adult_explicit"
    ARMS_AMMUNITION = "arms_ammunition"
    DEATH_INJURY_MILITARY = "death_injury_military"
    HATE_SPEECH_AGGRESSION = "hate_speech_aggression"
    OBSCENITY_PROFANITY = "obscenity_profanity"
    DRUGS_TOBACCO_ALCOHOL = "drugs_tobacco_alcohol"
    TERRORISM = "terrorism"
    PIRACY = "piracy"
    CRIME_HARMFUL = "crime_harmful"
    HUMAN_RIGHTS_VIOLATIONS = "human_rights_violations"
    MISINFORMATION = "misinformation"
    OTHER = "other"


class BrandSuitabilityTier(StrEnum):
    """GARM Brand Suitability Framework — 4-tier risk level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FLOOR = "floor"  # Unsuitable for any advertiser


# ── Hierarchical taxonomy ─────────────────────────────────────────────────────


class HierarchicalLabel(BaseModel):
    """3-level hierarchy e.g. Nudity > Explicit > Sexual Activity."""

    level1: str  # e.g. "Nudity"
    level2: str | None = None  # e.g. "Explicit"
    level3: str | None = None  # e.g. "Sexual Activity"


# ── Explainability / audit ────────────────────────────────────────────────────


class ViolationSource(BaseModel):
    """Per-violation explainability: which frames, rule, agent produced the finding."""

    frame_indices: list[int] = Field(default_factory=list)
    rule_id: str | None = None
    agent_name: str = "safety_checker"
    policy_trigger: str | None = None


# ── Per-agent output schemas ──────────────────────────────────────────────────


class Violation(BaseModel):
    category: SceneCategory | str  # Allow string for LLM output coercion
    severity: ViolationSeverity | str = ViolationSeverity.LOW
    timestamp: float = Field(..., description="Seconds from start of video")
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: str
    frame_index: int | None = None
    # Explainability
    source: ViolationSource | None = None
    # GARM / brand safety
    garm_category: GarmCategory | str | None = None
    hierarchical_label: HierarchicalLabel | None = None
    brand_suitability_tier: BrandSuitabilityTier | None = None

    @field_validator("category", mode="before")
    @classmethod
    def coerce_category(cls, v: Any) -> str:
        if isinstance(v, SceneCategory):
            return v.value
        s = str(v).lower().replace(" ", "_") if v else "other"
        valid = {c.value for c in SceneCategory}
        return s if s in valid else "other"

    @field_validator("severity", mode="before")
    @classmethod
    def coerce_severity(cls, v: Any) -> str:
        if isinstance(v, ViolationSeverity):
            return v.value
        s = str(v).lower() if v else "low"
        valid = {sev.value for sev in ViolationSeverity}
        return s if s in valid else "low"


class ContentAnalysisResult(BaseModel):
    summary: str
    topics: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"  # positive / negative / neutral / mixed
    language: str = "en"
    duration_seconds: float | None = None
    raw_response: str = ""


class SafetyResult(BaseModel):
    decision: ModerationDecision
    overall_severity: ViolationSeverity = ViolationSeverity.LOW
    violations: list[Violation] = Field(default_factory=list)
    policy_triggers: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reasoning: str = ""


class MetadataResult(BaseModel):
    entities: list[str] = Field(default_factory=list)
    brands: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    ocr_text: list[str] = Field(default_factory=list)
    objects_detected: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)


class SceneClassification(BaseModel):
    frame_index: int
    timestamp: float
    category: SceneCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    sub_categories: list[str] = Field(default_factory=list)


class ModerationReport(BaseModel):
    video_id: str
    decision: ModerationDecision
    overall_severity: ViolationSeverity = ViolationSeverity.LOW
    confidence: float = Field(..., ge=0.0, le=1.0)
    violations: list[Violation] = Field(default_factory=list)
    content_summary: str = ""
    reasoning: str = ""  # safety checker's plain-language explanation of the decision
    metadata: dict[str, Any] = Field(default_factory=dict)
    scene_summary: dict[str, int] = Field(default_factory=dict)  # category → count
    policy_triggers: list[str] = Field(default_factory=list)
    transcript_excerpt: str = ""
    processing_errors: list[str] = Field(default_factory=list)
    agents_completed: list[str] = Field(default_factory=list)
