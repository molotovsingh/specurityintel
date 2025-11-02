"""
Data Transfer Objects (DTOs) for UAM Compliance Intelligence System.

All inter-module communication uses these Pydantic models for type safety,
validation, and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """Alert and violation severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class KPIRecord(BaseModel):
    """
    Single KPI measurement for an application.

    Example:
        KPIRecord(
            app_id="APP-123",
            kpi_name="orphan_accounts",
            value=5.0,
            computed_at=datetime.now()
        )
    """
    app_id: str
    kpi_name: str  # e.g., "orphan_accounts", "privileged_accounts"
    value: float
    computed_at: datetime
    meta: Dict[str, str] = Field(default_factory=dict)

    model_config = {
        "frozen": True  # Immutable
    }


class RiskAnalysisResult(BaseModel):
    """
    AI-generated risk analysis for a KPI.

    Captures the risk score (0-100), confidence level, explanation,
    and contributing factors from AI analysis.
    """
    app_id: str
    kpi_name: str
    risk_score: float = Field(ge=0, le=100)  # 0-100 validation
    confidence: float = Field(ge=0, le=100)
    explanation: str
    factors: Dict[str, float]  # factor name -> contribution weight
    analyzed_at: datetime

    @field_validator('explanation')
    @classmethod
    def explanation_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Explanation cannot be empty')
        return v


class Violation(BaseModel):
    """
    Policy violation detected by rule engine.

    Tracks state transitions: NEW -> RECURRING -> RESOLVED
    """
    violation_id: str
    app_id: str
    rule_id: str
    severity: Severity
    kpi_values: Dict[str, float]
    threshold_breached: Dict[str, float]
    evidence: Dict[str, str]
    detected_at: datetime
    state: str = "NEW"  # NEW | RECURRING | RESOLVED

    @field_validator('state')
    @classmethod
    def valid_state(cls, v: str) -> str:
        if v not in ["NEW", "RECURRING", "RESOLVED"]:
            raise ValueError(f'Invalid state: {v}')
        return v


class Alert(BaseModel):
    """
    Alert to be dispatched via Slack or Email.

    Contains rich context: severity, risk score, violations,
    recommendations, and target persona.
    """
    alert_id: str
    app_id: str
    severity: Severity
    risk_score: float = Field(ge=0, le=100)
    violation_ids: List[str]
    title: str
    description: str
    recommendations: List[str] = Field(min_length=3, max_length=5)
    created_at: datetime
    persona: str  # compliance_officer | app_owner

    @field_validator('persona')
    @classmethod
    def valid_persona(cls, v: str) -> str:
        if v not in ["compliance_officer", "app_owner"]:
            raise ValueError(f'Invalid persona: {v}')
        return v


class AuditEvent(BaseModel):
    """
    Audit trail event.

    Captures all processing and alert events for compliance audit trail.
    """
    event_type: str
    timestamp: datetime
    details: Dict[str, str]


class Thresholds(BaseModel):
    """
    Alert threshold configuration.

    Example:
        {"orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10}}
    """
    alert_thresholds: Dict[str, Dict[str, float]]


class DeliveryResult(BaseModel):
    """
    Result of alert delivery attempt via Slack or Email.

    Tracks success status, delivery timestamp, retry count, and errors.
    """
    success: bool
    delivered_at: Optional[datetime] = None
    retries: int = 0
    error: Optional[str] = None


class Prompt(BaseModel):
    """
    Prompt for AI analysis via OpenAI.

    Contains text, token limits, and model parameters.
    """
    text: str
    max_tokens: int = 4000
    model: str = "gpt-4-turbo"
    temperature: float = 0.7


class AIResponse(BaseModel):
    """
    Response from AI analysis.

    Contains generated text, token usage, and cost estimate.
    """
    generated_text: str
    token_count: int
    cost_estimate: float
