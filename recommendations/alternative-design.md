# Alternative Architecture Design for UAM Compliance Intelligence

## Purpose
Provide a concrete, implementation-ready design that enforces strong modular boundaries, explicit contracts, and clean integration points. This complements the alternative plan by detailing module responsibilities, interfaces, data flows, storage/read models, and operational concerns while preserving POC velocity.

## Design Principles
- Hexagonal (ports/adapters), dependency inversion, explicit contracts
- Streamed, overlapped pipeline to meet <15m E2E and <5m alert targets
- Deterministic severity mapping (LOW/MEDIUM/HIGH/CRITICAL) end-to-end
- Configuration-driven behavior with safe defaults and hot-reload for thresholds
- Auditability by default (append-only logs + optional DB read models)

## Target Architecture (Option A: Hexagonal Modular Monolith)

Modules (Python packages):
- config: load/validate runtime configuration (pydantic), hot-reload thresholds
- ingestion: CSV staging, schema detection/validation, incremental/full detection
- kpi: compute all KPIs (vectorized), per-app aggregation
- ai: anomaly detection, risk scoring, explainability via LangChain/OpenAI
- policy: threshold/custom rule evaluation, SoD, severity classification, violation state
- alerting: alert generation, formatting, routing, dedup, channel delivery
- interfaces: shared DTOs, ports (contracts), and errors
- infra: adapters (Slack, Email, OpenAI, Storage, AuditLogger, Clock)
- orchestration: Prefect flows, pipeline coordination, concurrency

Inter-module dependencies (allowed):
- ingestion → kpi → ai → policy → alerting
- config → all
- interfaces → all
- infra adapters implement interfaces’ ports; only orchestration and modules depend on ports

## Contracts (DTOs) and Ports
Defined once in `interfaces/` and imported by all modules. Mirrors alternative-plan DTOs.

Key DTOs:
- KPIRecord, RiskAnalysisResult, Violation, Alert, AuditEvent, Thresholds, Severity

Key Ports (interfaces):
- SlackSender: send(alert: Alert) -> DeliveryResult
- EmailSender: send(alert: Alert) -> DeliveryResult
- OpenAIClient: analyze(prompt: Prompt) -> AIResponse
- AuditLogger: log(event: AuditEvent) -> None
- Storage: persist_* for alerts/violations/KPI and query read models
- Clock: now() for deterministic timestamps

Example (concise) port definitions:
```python
from typing import List, Optional
from interfaces.dto import Alert, AuditEvent

class DeliveryResult:  # simple result DTO
    def __init__(self, success: bool, retries: int = 0, error: Optional[str] = None):
        self.success = success
        self.retries = retries
        self.error = error

class SlackSender:
    def send(self, alert: Alert) -> DeliveryResult: ...

class EmailSender:
    def send(self, alert: Alert) -> DeliveryResult: ...

class AuditLogger:
    def log(self, event: AuditEvent) -> None: ...
```

## Data Flow & Concurrency
Pipeline runs daily with overlapping stages and per-application parallelism.

1) Ingestion (target 4m)
- Read CSVs (chunked if needed); validate schema; detect full vs incremental
- Output: in-memory dataframe(s); emit IngestionCompleted audit event

2) KPI (target 7m; starts immediately after first chunk)
- Compute KPIs per app; stream first 100 apps to AI
- Persist KPI daily snapshots to storage (optional in POC)

3) AI (effective ~2.5m overlapped)
- Batch apps in groups of ~50 for GPT efficiency; exponential backoff; caching
- Produce RiskAnalysisResult; attach confidence; log token/cost metrics

4) Policy (target 1.5m)
- Evaluate thresholds and custom rules; classify severity; manage violation state
- Domain dedup at violation layer (NEW/RECURRING/RESOLVED)

5) Alerting (target <3m)
- Generate alert payloads (PRD template); persona routing; severity filtering
- Dispatch via Slack first (bot token + SDK), fallback to Email; async batching
- Dispatch dedup (24h window per app + rule + severity; resend on escalation/state change)
- Persist alerts to read model; log delivery events

Critical path with overlap: ~14 minutes, meeting E2E target.

## Configuration Model
- Single YAML (or split files) validated via pydantic models
- Severity mapping is 1:1: low/medium/high/critical → LOW/MEDIUM/HIGH/CRITICAL
- Slack: `bot_token` and per-severity channels; webhook removed for consistency
- Hot-reload: thresholds only; notification settings require restart (safety)

Pydantic sample (abridged):
```python
from pydantic import BaseModel, Field, validator
from typing import Dict

class SlackCfg(BaseModel):
    enabled: bool = True
    bot_token: str
    channels: Dict[str, str]  # critical/high/medium/low → #channel
    @validator("bot_token")
    def _xoxb(cls, v):
        if not v.startswith("xoxb-"): raise ValueError("Invalid Slack bot token format")
        return v

class ThresholdCfg(BaseModel):
    alert_thresholds: Dict[str, Dict[str, float]]

class RootCfg(BaseModel):
    slack: SlackCfg
    thresholds: ThresholdCfg
```

## Adapters (Infra)
- SlackAdapter (slack-sdk, Block Kit formatting)
- EmailAdapter (smtplib, Jinja2 templates, plain-text fallback)
- OpenAIAdapter (LangChain + OpenAI SDK, token counting with tiktoken)
- JsonlStorage (append-only alerts/violations/audit), optional PostgresStorage
- StructlogAudit (structured JSON logs, 90-day retention)

All adapters implement ports and are injected via a small composition root.

## Storage & Read Models
POC Default: JSON Lines for audit trail; optional Postgres for read models.

Read model tables:
- alerts(alert_id PK, app_id, severity, risk_score, created_at, persona, title, summary, recipients JSONB, delivery_status JSONB)
- violations(violation_id PK, app_id, rule_id, severity, state, detected_at, evidence JSONB, kpi_values JSONB)
- kpi_daily(app_id, kpi_name, value, computed_at, PRIMARY KEY(app_id,kpi_name,computed_at))
- daily_summary(date PK, apps_processed, violations_by_severity JSONB, top_apps JSONB, health_score)

Indexes: `(severity, created_at)`, `(app_id, created_at)` to power UI/API queries.

## Observability
- structlog for JSON logs; include request/trace IDs
- Timers per stage; counters: alerts dispatched, retries, failures
- Optional prometheus-client for metrics; basic Grafana dashboards

## Security & Compliance
- Secrets via env vars/Docker secrets; redact in logs
- No PII to LLMs; anonymize IDs
- TLS for external calls; AES-256 at rest for CSVs/logs
- Audit trail for ingestion/KPIs/AI/policy/alerting/config events

## Testing Strategy
- Unit tests: ports, adapters (with mocks), KPI/Policy deterministic cases
- Integration: end-to-end flow with stubbed OpenAI/Slack/SMTP
- Performance: sample full dataset to confirm <15m budget; profile hotspots

## Deployment
- Docker Compose services: uam-compliance (+ optional postgres)
- Non-root containers; read-only FS where possible; bind mounts: /data, /logs, /config
- Phase-2: K8s with Helm, HPA, PVs, Vault/K8s Secrets

## Migration Path to Services (Option B)
1) Keep DTOs/ports stable; emit internal events (structured logs or in-memory bus)
2) Stand up Postgres read models; dual-write from monolith
3) Extract alerting service first (consume ViolationDetected)
4) Extract AI service if isolation/cost controls needed
5) Introduce NATS/Kafka; replace in-memory bus; keep schema versioning
6) Add read-only REST API backed by read models; add auth later

## Risks & Mitigations
- Interface drift: centralize DTOs/ports; version contracts; CI validation
- Alert fatigue: severity filtering defaults; dedup; digest mode
- AI cost/timeouts: batching, caching, degraded mode, daily cost caps
- Performance regressions: stage timers, overlap safeguards, fail-fast alerts for criticals

## Ready Checklist
- Ports and DTOs implemented and consumed by all modules
- Slack via bot token only; severity mapping unified
- Threshold hot-reload wired; notification restart required
- Read model writes present; alerts/violations persisted
- Timers and audit logging validated in test runs

