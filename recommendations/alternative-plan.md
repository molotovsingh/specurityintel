# Alternative Architecture & Implementation Plan for UAM Compliance Intelligence

## Executive Summary
This plan proposes a more explicitly decoupled and modular approach than the current POC “modular monolith” design, and outlines a clean migration path to a service-oriented, event-driven architecture. It introduces formal contracts (DTOs), clear ports/adapters, message schemas, and read models that enable future frontend/API layers without refactors. The plan keeps POC velocity by starting with a hexagonal modular monolith (Option A) while designing forward compatibly to a small set of services (Option B) when scale or org needs demand it.

## Objectives
- Strengthen module boundaries with explicit interfaces and DTOs
- Decouple external integrations with ports/adapters for testability
- Standardize severity mapping and Slack configuration across specs and code
- Provide a future-proof contract for a UI/API without changing core logic
- Ensure performance targets (<15 min E2E, <5 min alerts) with concurrency
- Preserve POC timelines; enable incremental migration to services

## What Changes vs Current POC
- Introduce a dedicated Interfaces layer (DTOs, ports) and enforce via types
- Define message schemas for inter-module events (JSON/Protobuf)
- Add a Read Model schema for alerts, KPIs, summaries (for future UI/API)
- Clarify dedup boundary: domain violations vs dispatch alerts
- Align configuration: Slack via bot token (SDK), severity levels LOW/MEDIUM/HIGH/CRITICAL end-to-end
- Document streaming pipeline overlap to fit the global 15-minute budget

## Architecture Options

### Option A — Hexagonal Modular Monolith (POC-First)
Keep a single deployable with strong internal boundaries and dependency injection.

- Modules (Python packages):
  - ingestion, kpi, ai, policy, alerting, config, interfaces (new)
- Ports/Adapters:
  - Ports: SlackSender, EmailSender, OpenAIClient, AuditLogger, Clock, Storage (KPI/Alert store)
  - Adapters: Slack SDK, SMTP, OpenAI SDK/LangChain, JSONL/Postgres, structlog
- Contracts (pydantic): DTOs for KPIRecord, RiskAnalysisResult, Violation, Alert, AuditEvent, Config
- Orchestration: Prefect flows coordinating per-stage tasks with overlap
- Storage: JSON Lines for audit; optional Postgres for alerts/read model
- Pros: Fast to implement, low deployment complexity, great for POC
- Cons: Scale and team autonomy limited; tight resource coupling

When to choose: POC and early production with one team, modest throughput, fast iteration.

### Option B — Service-Oriented with Event Bus (Phase-2+)
Split the monolith into 4–5 services connected by a lightweight event bus (Kafka, NATS, or Redis Streams) and shared read models.

- Services:
  - ingestion-svc → emits UAMDatasetReady
  - kpi-svc → emits KPIComputed (per-app), KPISummaryReady
  - ai-svc → emits RiskAnalyzed (per-app), TrendAnalyzed
  - policy-svc → emits ViolationDetected, ViolationsClosed
  - alerting-svc → consumes violation and sends alerts; persists AlertDispatched
- Shared Read Models (Postgres): alerts, violations, daily summaries, KPI aggregates
- Contracts: Same DTOs as Option A, shared via a typed package or schema registry
- Pros: Clear scaling per service, independent deploys, better resilience
- Cons: Higher complexity (ops, delivery semantics, schema evolution)

When to choose: Multiple teams, higher scale, stronger reliability and isolation needs, or when a UI/API and analytics become first-class.

Recommendation: Build POC using Option A, codify contracts/messages now, and maintain a small “service split” playbook to enable Option B without refactors.

## Interfaces and Contracts (Authoritative)
Define DTOs with pydantic for validation and easy JSON serialization.

```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class KPIRecord(BaseModel):
    app_id: str
    kpi_name: str  # e.g., "orphan_accounts"
    value: float
    computed_at: datetime
    meta: Dict[str, str] = {}

class RiskAnalysisResult(BaseModel):
    app_id: str
    kpi_name: str
    risk_score: float  # 0-100
    confidence: float  # 0-100
    explanation: str
    factors: Dict[str, float]  # factor->weight
    analyzed_at: datetime

class Violation(BaseModel):
    violation_id: str
    app_id: str
    rule_id: str
    severity: Severity
    kpi_values: Dict[str, float]
    threshold_breached: Dict[str, float]
    evidence: Dict[str, str]
    detected_at: datetime
    state: str = "NEW"  # NEW|RECURRING|RESOLVED

class Alert(BaseModel):
    alert_id: str
    app_id: str
    severity: Severity
    risk_score: float
    violation_ids: List[str]
    title: str
    description: str
    recommendations: List[str]
    created_at: datetime
    persona: str  # compliance_officer|app_owner

class AuditEvent(BaseModel):
    event_type: str
    timestamp: datetime
    details: Dict[str, str]

class Thresholds(BaseModel):
    # Per-KPI levels directly map to Severity
    # e.g., {"orphan_accounts": {"low":1, "medium":3, "high":5, "critical":10}}
    alert_thresholds: Dict[str, Dict[str, float]]
```

Severity mapping: configuration levels map 1:1 to alert severity (LOW/MEDIUM/HIGH/CRITICAL) to eliminate ambiguity.

## Message Schemas (Events)
Use JSON for simplicity in POC; evolve to Protobuf/Avro if adopting an event bus.

- KPIComputed
```json
{
  "type": "KPIComputed",
  "app_id": "APP-1234",
  "kpi_name": "orphan_accounts",
  "value": 7,
  "computed_at": "2025-11-02T09:00:00Z"
}
```

- RiskAnalyzed
```json
{
  "type": "RiskAnalyzed",
  "app_id": "APP-1234",
  "kpi_name": "orphan_accounts",
  "risk_score": 82.5,
  "confidence": 78.0,
  "analyzed_at": "2025-11-02T09:02:00Z"
}
```

- ViolationDetected
```json
{
  "type": "ViolationDetected",
  "violation_id": "V-20251102-0001",
  "app_id": "APP-1234",
  "rule_id": "SOD-001",
  "severity": "CRITICAL",
  "detected_at": "2025-11-02T09:03:00Z"
}
```

- AlertDispatched
```json
{
  "type": "AlertDispatched",
  "alert_id": "A-20251102-0001",
  "app_id": "APP-1234",
  "severity": "CRITICAL",
  "channel": "slack",
  "recipients": ["#security-critical"],
  "dispatched_at": "2025-11-02T09:04:30Z"
}
```

## Read Model (for Frontend/API Readiness)
Postgres tables with pragmatic indexes; can be built alongside POC.

- alerts(alert_id PK, app_id, severity, risk_score, created_at, persona, title, summary, recipients JSONB, delivery_status JSONB)
- violations(violation_id PK, app_id, rule_id, severity, state, detected_at, evidence JSONB, kpi_values JSONB)
- kpi_daily(app_id, kpi_name, value, computed_at, PRIMARY KEY(app_id, kpi_name, computed_at))
- daily_summary(date PK, apps_processed, violations_by_severity JSONB, top_apps JSONB, health_score)

These power endpoints without coupling to processing internals.

## API Surface (Phase-2)
- GET /api/v1/alerts?severity=HIGH&app_id=APP-1234
- GET /api/v1/alerts/{alert_id}
- GET /api/v1/violations?state=NEW
- GET /api/v1/kpis?app_id=APP-1234&kpi=orphan_accounts
- GET /api/v1/summary/daily?date=YYYY-MM-DD
- GET /api/v1/health

## Configuration Alignment
- Slack: single strategy using bot token + Slack SDK; remove webhook mentions for consistency.
- Severity: thresholds defined as low/medium/high/critical; direct mapping to alert severities; dedup and routing key off Severity.
- Hot reload: thresholds hot-reloaded; notification settings require restart (as in design).

## Performance Plan
- Overlap stages: AI begins as soon as first 100 apps’ KPIs are ready; dispatch starts per-batch.
- Budgets (with overlap): Ingestion 4m + KPI 7m + AI effective 2.5m + Policy 1.5m + Alert 3m → ~14m E2E.
- Concurrency:
  - Ingestion: chunked I/O, multi-threaded parsing (Pandas + pyarrow) or Polars
  - KPI: vectorized ops; per-app partition; thread/process pool
  - AI: batch 50 apps per call; exponential backoff; caching
  - Policy: parallel rule evaluation with timeouts
  - Alerting: async I/O for Slack/SMTP; bounded queues and rate limits

## Security & Compliance
- Secrets via environment variables or Docker/K8s secrets; never log secrets
- No PII in AI prompts; tokenize/anonymize identifiers
- TLS for external calls; AES-256 at rest for logs and CSVs
- Audit trail: append-only JSONL; 90-day retention

## Dedup Boundaries (Explicit)
- Domain dedup: policy engine tracks violation state (NEW/RECURRING/RESOLVED)
- Dispatch dedup: alerting suppresses re-sends within 24h unless severity/risk escalates or state changes

## Migration Plan (A → B)
1) Codify DTOs and ports; refactor modules to depend on interfaces
2) Introduce event messages internally (in-memory bus); log them for visibility
3) Stand up Postgres read model; write from monolith
4) Extract alerting-svc first (lowest coupling); consume ViolationDetected
5) Extract ai-svc if necessary (cost/perf isolation)
6) Switch in-memory events to Kafka/NATS; keep DTO/versioning discipline
7) Introduce REST API atop read models; add auth later

## Implementation Roadmap (Incremental)
Week 1-2
- Add interfaces package (DTOs, ports), refactor modules to use ports
- Standardize config (severity mapping, Slack token)
- Implement read model writes for alerts/violations

Week 3-4
- Add internal event emission (structured logs → in-memory bus)
- Harden AI degradation and caching; add cost caps and metrics
- Finalize alert templates; enforce dedup boundaries

Week 5-6
- Optional: Extract alerting to its own container (compose) consuming logged events
- Add minimal REST endpoints for read-only views (alerts, summaries)
- Prepare Phase-2 plan for full event bus adoption

## Risks & Mitigations
- Scope creep: Keep Option B extractions optional until metrics demand it
- Contract drift: Enforce DTOs with versioning and validation
- Perf regressions: Instrument timings per stage; budget gates in CI
- Cost spikes: Token counting, daily budget switch to degraded mode

## Ready-to-Build Checklist
- DTOs committed and used end-to-end
- Ports/adapters implemented for Slack, Email, OpenAI, Storage
- Severity and Slack config aligned across specs and code
- Read model schema created; alerts/violations persisted
- Perf instrumentation added; overlap verified with sample data

