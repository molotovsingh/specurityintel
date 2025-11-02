# UAM Compliance Intelligence System - Technical Design

## Context

The UAM Compliance Intelligence System automates security KPI analysis for banking institutions. Banks currently rely on manual CSV reviews to detect access violations across 1,200+ applications and 40,000+ users—a process that is slow, reactive, and error-prone. This POC introduces an AI-powered solution that processes daily UAM exports, computes security metrics, detects anomalies using GPT-4, and delivers explainable real-time alerts via Slack and email.

**Constraints:**
- Processing must complete in <15 minutes for daily dataset (1,200 apps × 40,000 users)
- Alerts must be dispatched in <5 minutes after detection
- On-premise deployment required for banking data privacy
- No user credentials stored—system operates on CSV exports only
- <10% false positive rate to prevent alert fatigue
- 99% availability during business hours (POC target)

**Stakeholders:**
- Primary: Bank Security Compliance Officers (need immediate violation visibility)
- Secondary: Application Owners (need app-specific alerts only)

## Goals / Non-Goals

### Goals
- Automate daily UAM KPI analysis and eliminate manual CSV review
- Enable real-time alerting (<5 min) for critical violations
- Provide explainable AI-driven intelligence (root cause, context, recommendations)
- Support persona-based alert routing (compliance officers vs app owners)
- Deliver functional POC in 4-6 weeks with measurable success metrics

### Non-Goals (Out of Scope for POC)
- Dashboard UI (planned for Phase 2 - Q1 2026)
- REST API endpoints
- User authentication & RBAC
- Historical data warehouse or long-term analytics
- Advanced ML model training (using GPT-4 API only)
- Ticketing system integrations (ServiceNow, Jira)
- Mobile notifications

## Architecture Overview

### Architecture Style: Hexagonal Modular Monolith

The system uses a **hexagonal architecture** (ports and adapters pattern) organized as a modular monolith. This approach provides strong module boundaries, dependency inversion, and testability while maintaining POC velocity with a single deployable artifact.

**Key Principles:**
- **Dependency Inversion**: Core domain logic depends on abstractions (ports), not concrete implementations (adapters)
- **Explicit Contracts**: All inter-module communication uses Pydantic DTOs for type safety and validation
- **Ports & Adapters**: External dependencies (Slack, Email, OpenAI, Storage) accessed via interface contracts
- **Testability**: Mock adapters enable unit testing without external services
- **Future-Proof**: Clean migration path to microservices via formalized contracts

**Module Structure:**
- **Core Modules** (6): data-ingestion, kpi-computation, ai-analysis, policy-engine, alerting, configuration
- **Cross-Cutting** (1): interfaces (DTOs, ports, errors)
- **Infrastructure** (adapters): Slack, Email, OpenAI, Storage, AuditLogger, Clock implementations

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestration Layer                         │
│                   (Airflow / Prefect)                           │
└────────────────────────┬────────────────────────────────────────┘
                         │ Daily Trigger
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Data Ingestion Layer                          │
│  - CSV Parser (Pandas/Polars)                                   │
│  - Schema Validation                                            │
│  - Full/Incremental Load Detection                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  KPI Computation Engine                         │
│  - Privileged Accounts, Failed Access, Provisioning Time        │
│  - Orphan Accounts, Access Reviews, Policy Violations           │
│  - Excessive Permissions, Dormant Accounts                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AI Analysis Layer                            │
│  - LangChain + GPT-4                                            │
│  - Anomaly Detection                                            │
│  - Multi-Factor Risk Scoring (0-100)                            │
│  - Trend Analysis (Week-on-Week)                                │
│  - Cross-App Pattern Detection                                  │
│  - Explainability Engine                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Policy Rule Engine                            │
│  - Threshold-Based Detection                                    │
│  - Custom Banking Compliance Rules                              │
│  - Segregation of Duties (SoD) Rules                            │
│  - Severity Classification (CRITICAL/HIGH/MEDIUM/LOW)           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Alerting System                              │
│  ┌──────────────────┐         ┌──────────────────┐            │
│  │  Slack Channel   │         │   Email (SMTP)   │            │
│  │  #security-crit  │         │   Digest Mode    │            │
│  └──────────────────┘         └──────────────────┘            │
│                                                                 │
│  - Persona-Based Routing                                       │
│  - Severity Filtering                                          │
│  - Alert Deduplication                                         │
│  - Retry Logic                                                 │
└─────────────────────────────────────────────────────────────────┘

                         ▲
                         │
┌─────────────────────────────────────────────────────────────────┐
│               Configuration Management                          │
│  - YAML/JSON Threshold Configuration                            │
│  - Notification Settings (channels, recipients)                 │
│  - Hot-Reload Support                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Decisions

### Decision 1: Pandas vs Polars for Data Processing
**Chosen:** Use Pandas with fallback to Polars for large datasets

**Rationale:**
- Pandas is more mature with extensive community support
- Polars offers 5-10x better performance for large datasets
- Strategy: Start with Pandas, profile performance, switch to Polars if needed
- Acceptable trade-off: Both meet <15 min processing requirement

**Alternatives Considered:**
- Pure Polars: Less mature ecosystem, steeper learning curve
- Spark: Overkill for POC, adds deployment complexity

### Decision 2: GPT-4 via LangChain vs Custom ML Models
**Chosen:** GPT-4 via LangChain API

**Rationale:**
- POC timeline (4-6 weeks) prohibits custom ML training
- GPT-4 provides explainability out-of-the-box (critical requirement)
- LangChain offers prompt templating and chain-of-thought reasoning
- Acceptable cost for POC phase (<$500/month estimated)
- Graceful degradation: Fall back to rule-based detection if API fails

**Alternatives Considered:**
- scikit-learn models: Requires labeled training data (not available)
- Azure ML / AWS SageMaker: Vendor lock-in, longer setup time

### Decision 3: Airflow vs Prefect for Orchestration
**Chosen:** Prefect

**Rationale:**
- Simpler setup for POC (Python-native, no separate webserver)
- Better failure handling and retry logic
- Modern UI and monitoring
- Easier to containerize

**Alternatives Considered:**
- Airflow: More mature but heavier footprint, complex DAG syntax
- Cron: Too basic, no monitoring or retry capabilities

### Decision 4: Alert Storage Strategy
**Chosen:** Append-only file-based storage (JSON Lines) with optional PostgreSQL

**Rationale:**
- POC requirement: Focus on alerting, not historical analysis
- JSON Lines format: Simple, human-readable, grep-friendly
- Optional PostgreSQL: Enable if stakeholders need basic querying
- Defer full data warehouse to Phase 2

**Alternatives Considered:**
- SQLite: File-based but less scalable than PostgreSQL
- No storage: Alerts lost after dispatch, unacceptable for audit trail

### Decision 5: Slack vs Microsoft Teams
**Chosen:** Slack (primary) with email fallback

**Rationale:**
- PRD explicitly specifies Slack SDK
- Email provides universal fallback
- Teams integration deferred to post-POC

**Alternatives Considered:**
- Teams only: Not mentioned in PRD
- SMS: Out of scope for POC (mobile notifications excluded)

### Decision 6: Configuration Hot-Reload vs Restart Required
**Chosen:** Hot-reload for threshold changes, restart for notification settings

**Rationale:**
- Threshold tuning is iterative and frequent during POC
- Hot-reload enables faster experimentation
- Notification settings change rarely (safer to require restart)

**Alternatives Considered:**
- Always hot-reload: Adds complexity, risk of inconsistent state
- Always restart: Disrupts daily processing schedule

### Decision 7: Monolith vs Microservices
**Chosen:** Modular monolith with clear internal boundaries

**Rationale:**
- POC timeline and complexity favor simplicity
- 6 capabilities (ingestion, KPI, AI, policy, alerting, config) as Python modules
- Each module has well-defined interfaces
- Migration path: Extract modules to services post-POC if needed

**Alternatives Considered:**
- Microservices from start: Premature optimization, deployment overhead
- Tightly coupled monolith: Poor separation of concerns

## Data Flow

### Daily Processing Pipeline

**Pipeline Design:** Streaming pipeline with per-application parallelism. AI analysis can begin processing completed KPIs while later KPIs are still computing, reducing end-to-end latency.

1. **Ingestion Phase** (Target: 4 minutes)
   - Orchestrator triggers daily job at configured time
   - CSV files read from configured directory
   - Schema validation (handle schema drift gracefully)
   - Data loaded into Pandas/Polars DataFrames
   - Incremental vs full load detection
   - Output: Validated UAM dataset in memory

2. **KPI Computation Phase** (Target: 7 minutes, overlaps with AI)
   - Calculate 7 core KPIs per application
   - Aggregate user-level metrics to app-level
   - Store KPI results with timestamp
   - Output: KPI metrics DataFrame (streaming to AI layer)
   - **Note:** AI analysis starts when first 100 apps complete (~2 min)

3. **AI Analysis Phase** (Target: 2.5 minutes effective, starts at T+6)
   - Anomaly detection algorithms identify deviations
   - GPT-4 via LangChain generates risk scores (0-100)
   - Trend analysis (week-on-week comparison)
   - Cross-app pattern detection
   - Explainability layer generates context
   - Output: Risk-scored KPIs with explanations
   - **Concurrency:** Processes apps in batches of 50 for GPT-4 efficiency

4. **Policy Evaluation Phase** (Target: 1.5 minutes)
   - Load threshold configuration
   - Evaluate each KPI against thresholds
   - Apply custom banking compliance rules
   - Classify severity (CRITICAL/HIGH/MEDIUM/LOW)
   - Output: Violations list with severity

5. **Alert Dispatch Phase** (Target: <3 minutes)
   - Generate alert messages using PRD template
   - Route by persona (compliance officers vs app owners)
   - Filter by severity
   - Deduplicate similar alerts
   - Dispatch via Slack and/or email (parallel)
   - Log alert events to audit trail
   - Retry failed deliveries (3 attempts, exponential backoff)
   - Output: Alerts delivered, audit log updated

**Total Pipeline Time:** <15 minutes end-to-end
- Sequential critical path: Ingestion (4) + KPI (7) + Policy (1.5) + Alert (3) = 15.5 min
- With AI overlap starting at T+6: Actual = 4 + 7 + max(2.5-5, 0) + 1.5 + 3 = ~14 minutes
- Includes buffer for retries and variance

## Technology Stack Details

### Core Python Stack
- **Python 3.11+**: Latest stable version with performance improvements
- **Poetry**: Dependency management and packaging
- **pytest**: Testing framework with fixtures and mocking
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Fast linting

### Data Processing
- **Pandas 2.x**: Primary data manipulation library
- **Polars**: Optional performance upgrade (lazy evaluation)
- **NumPy**: Numerical operations for KPI calculations
- **SciPy**: Statistical analysis (anomaly detection)

### AI & ML
- **LangChain**: LLM orchestration, prompt templates, chains
- **OpenAI Python SDK**: GPT-4 API client (GPT-4: 8k context, GPT-4-turbo: 128k context)
- **tiktoken**: Token counting for cost estimation

### Alerting
- **slack-sdk**: Official Slack SDK for Python
- **smtplib**: Built-in Python SMTP client
- **Jinja2**: Email HTML template rendering

### Orchestration
- **Prefect**: Workflow orchestration, scheduling, monitoring

### Configuration
- **PyYAML**: YAML parsing
- **pydantic**: Configuration validation and type safety

### Deployment
- **Docker**: Containerization
- **docker-compose**: Multi-container orchestration (POC)
- **PostgreSQL** (optional): Alert storage database

### Observability
- **structlog**: Structured logging
- **prometheus-client** (optional): Metrics export

## Data Transfer Objects (DTOs) and Contracts

All inter-module communication uses Pydantic models for type safety, validation, and serialization.

### Core DTOs

```python
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

class Severity(str, Enum):
    """Alert and violation severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class KPIRecord(BaseModel):
    """Single KPI measurement for an application."""
    app_id: str
    kpi_name: str  # e.g., "orphan_accounts", "privileged_accounts"
    value: float
    computed_at: datetime
    meta: Dict[str, str] = Field(default_factory=dict)

    class Config:
        frozen = True  # Immutable

class RiskAnalysisResult(BaseModel):
    """AI-generated risk analysis for a KPI."""
    app_id: str
    kpi_name: str
    risk_score: float = Field(ge=0, le=100)  # 0-100 validation
    confidence: float = Field(ge=0, le=100)
    explanation: str
    factors: Dict[str, float]  # factor name -> contribution weight
    analyzed_at: datetime

    @validator('explanation')
    def explanation_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Explanation cannot be empty')
        return v

class Violation(BaseModel):
    """Policy violation detected by rule engine."""
    violation_id: str
    app_id: str
    rule_id: str
    severity: Severity
    kpi_values: Dict[str, float]
    threshold_breached: Dict[str, float]
    evidence: Dict[str, str]
    detected_at: datetime
    state: str = "NEW"  # NEW | RECURRING | RESOLVED

    @validator('state')
    def valid_state(cls, v):
        if v not in ["NEW", "RECURRING", "RESOLVED"]:
            raise ValueError(f'Invalid state: {v}')
        return v

class Alert(BaseModel):
    """Alert to be dispatched via Slack or Email."""
    alert_id: str
    app_id: str
    severity: Severity
    risk_score: float = Field(ge=0, le=100)
    violation_ids: List[str]
    title: str
    description: str
    recommendations: List[str] = Field(min_items=3, max_items=5)
    created_at: datetime
    persona: str  # compliance_officer | app_owner

    @validator('persona')
    def valid_persona(cls, v):
        if v not in ["compliance_officer", "app_owner"]:
            raise ValueError(f'Invalid persona: {v}')
        return v

class AuditEvent(BaseModel):
    """Audit trail event."""
    event_type: str
    timestamp: datetime
    details: Dict[str, str]

class Thresholds(BaseModel):
    """Alert threshold configuration."""
    alert_thresholds: Dict[str, Dict[str, float]]
    # e.g., {"orphan_accounts": {"low": 1, "medium": 3, "high": 5, "critical": 10}}
```

### Benefits
- **Type Safety**: Pydantic validates at runtime, prevents invalid data crossing module boundaries
- **JSON Serialization**: Built-in .json() and .parse_raw() for persistence and events
- **Documentation**: Field types serve as living documentation
- **Versioning**: Optional fields enable backward-compatible evolution
- **Testability**: DTOs can be easily constructed in tests with known-good values

## Ports and Adapters

External dependencies are accessed via interface contracts (ports) with concrete implementations (adapters) injected at runtime.

### Port Definitions

```python
from abc import ABC, abstractmethod
from typing import Optional

class DeliveryResult(BaseModel):
    """Result of alert delivery attempt."""
    success: bool
    retries: int = 0
    error: Optional[str] = None
    delivered_at: Optional[datetime] = None

class SlackSender(ABC):
    """Port for Slack alert delivery."""
    @abstractmethod
    def send(self, alert: Alert) -> DeliveryResult:
        """Send alert to Slack channel based on severity."""
        pass

class EmailSender(ABC):
    """Port for email alert delivery."""
    @abstractmethod
    def send(self, alert: Alert) -> DeliveryResult:
        """Send alert via email to configured recipients."""
        pass

    @abstractmethod
    def send_digest(self, alerts: List[Alert]) -> DeliveryResult:
        """Send batched digest of alerts."""
        pass

class OpenAIClient(ABC):
    """Port for AI analysis."""
    @abstractmethod
    def analyze(self, prompt: str, max_tokens: int) -> str:
        """Generate AI analysis for given prompt."""
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Count tokens in text for cost estimation."""
        pass

class Storage(ABC):
    """Port for persistent storage."""
    @abstractmethod
    def persist_kpi(self, kpi: KPIRecord) -> None:
        pass

    @abstractmethod
    def persist_violation(self, violation: Violation) -> None:
        pass

    @abstractmethod
    def persist_alert(self, alert: Alert) -> None:
        pass

    @abstractmethod
    def query_violations(self, app_id: str, state: str) -> List[Violation]:
        pass

class AuditLogger(ABC):
    """Port for audit logging."""
    @abstractmethod
    def log(self, event: AuditEvent) -> None:
        pass

class Clock(ABC):
    """Port for time source (enables deterministic testing)."""
    @abstractmethod
    def now(self) -> datetime:
        pass
```

### Adapter Implementations

**SlackAdapter** (uses slack-sdk):
- Formats alerts using Slack Block Kit
- Routes to channels by severity (#security-critical, #compliance-alerts)
- Implements retry logic with exponential backoff
- Handles rate limiting

**EmailAdapter** (uses smtplib + Jinja2):
- Renders HTML emails from Jinja2 templates
- Includes plain-text fallback
- Supports digest mode (batch multiple alerts)
- Implements retry logic

**OpenAIAdapter** (uses LangChain + OpenAI SDK):
- Manages prompt templating via LangChain
- Counts tokens with tiktoken
- Implements caching for similar prompts
- Falls back to template-based explanations on failure

**JsonlStorage** (file-based):
- Appends DTOs to JSON Lines files
- Separate files for alerts, violations, KPIs, audit events
- Simple, grep-friendly for POC

**PostgresStorage** (database):
- Writes DTOs to relational tables (read model schema below)
- Supports queries for future UI/API
- Optional for POC, recommended for production

**StructlogAdapter**:
- Writes structured JSON logs
- Includes request/trace IDs for correlation
- 90-day retention policy

**SystemClock** (production) / **FixedClock** (tests):
- SystemClock returns actual datetime.now()
- FixedClock returns fixed time for deterministic tests

### Dependency Injection

Adapters are instantiated in a composition root and injected into modules:

```python
# Composition root (simplified)
from interfaces.ports import SlackSender, EmailSender, Storage
from adapters.slack_adapter import SlackAdapter
from adapters.email_adapter import EmailAdapter
from adapters.postgres_storage import PostgresStorage
from modules.alerting import AlertingService

# Instantiate adapters
slack = SlackAdapter(bot_token=config.slack_bot_token)
email = EmailAdapter(smtp_host=config.smtp_host, ...)
storage = PostgresStorage(connection_string=config.db_url)

# Inject into service
alerting_service = AlertingService(
    slack_sender=slack,
    email_sender=email,
    storage=storage
)
```

### Testing with Mocks

```python
# Unit test example
from unittest.mock import Mock
from interfaces.ports import SlackSender
from interfaces.dto import Alert, Severity

def test_alert_formatting():
    mock_slack = Mock(spec=SlackSender)
    alerting_service = AlertingService(slack_sender=mock_slack, ...)

    alert = Alert(
        alert_id="A-001",
        app_id="APP-123",
        severity=Severity.CRITICAL,
        ...
    )

    alerting_service.dispatch(alert)

    mock_slack.send.assert_called_once()
    args = mock_slack.send.call_args[0]
    assert args[0].severity == Severity.CRITICAL
```

## Read Model Schema (PostgreSQL)

Tables designed for efficient queries by future UI/API while processing pipeline writes to them during POC.

```sql
-- Alerts table
CREATE TABLE alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    app_id VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,  -- LOW/MEDIUM/HIGH/CRITICAL
    risk_score NUMERIC(5,2) NOT NULL CHECK (risk_score >= 0 AND risk_score <= 100),
    created_at TIMESTAMP NOT NULL,
    persona VARCHAR(50) NOT NULL,  -- compliance_officer/app_owner
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recommendations JSONB NOT NULL,  -- Array of recommendation strings
    violation_ids JSONB NOT NULL,    -- Array of violation IDs
    recipients JSONB,                -- Delivery targets
    delivery_status JSONB,           -- {slack: {success: true, ...}, email: {...}}
    INDEX idx_alerts_severity_time (severity, created_at DESC),
    INDEX idx_alerts_app_time (app_id, created_at DESC)
);

-- Violations table
CREATE TABLE violations (
    violation_id VARCHAR(50) PRIMARY KEY,
    app_id VARCHAR(50) NOT NULL,
    rule_id VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    state VARCHAR(20) NOT NULL,  -- NEW/RECURRING/RESOLVED
    detected_at TIMESTAMP NOT NULL,
    kpi_values JSONB NOT NULL,
    threshold_breached JSONB NOT NULL,
    evidence JSONB,
    INDEX idx_violations_app_state (app_id, state),
    INDEX idx_violations_severity_time (severity, detected_at DESC),
    INDEX idx_violations_state_time (state, detected_at DESC)
);

-- KPI daily snapshots
CREATE TABLE kpi_daily (
    app_id VARCHAR(50) NOT NULL,
    kpi_name VARCHAR(50) NOT NULL,
    value NUMERIC NOT NULL,
    computed_at TIMESTAMP NOT NULL,
    meta JSONB,
    PRIMARY KEY (app_id, kpi_name, computed_at),
    INDEX idx_kpi_name_time (kpi_name, computed_at DESC)
);

-- Daily summary report
CREATE TABLE daily_summary (
    date DATE PRIMARY KEY,
    apps_processed INTEGER NOT NULL,
    violations_by_severity JSONB NOT NULL,  -- {CRITICAL: 5, HIGH: 12, ...}
    top_apps_by_risk JSONB NOT NULL,       -- [{app_id, risk_score}, ...]
    health_score NUMERIC(5,2),             -- Overall compliance score 0-100
    created_at TIMESTAMP NOT NULL
);
```

### Query Patterns (Future API/UI)

```sql
-- Get recent critical alerts for an app
SELECT * FROM alerts
WHERE app_id = 'APP-1234' AND severity = 'CRITICAL'
ORDER BY created_at DESC LIMIT 10;

-- Get unresolved violations
SELECT * FROM violations
WHERE state IN ('NEW', 'RECURRING')
ORDER BY severity DESC, detected_at DESC;

-- Get KPI trend for orphan accounts
SELECT computed_at, value FROM kpi_daily
WHERE app_id = 'APP-1234' AND kpi_name = 'orphan_accounts'
ORDER BY computed_at DESC LIMIT 30;

-- Get daily compliance health
SELECT date, health_score, violations_by_severity
FROM daily_summary
ORDER BY date DESC LIMIT 7;
```

## Security Architecture

### Data Handling
- **At Rest**: AES-256 encryption for stored CSV files and alert logs
- **In Transit**: TLS 1.2+ for all external API calls (Slack, OpenAI)
- **No Credentials**: System reads CSV exports only, no IAM integration

### Secrets Management
- **Environment Variables**: For API keys (Slack, OpenAI)
- **Docker Secrets**: In containerized deployment
- **Rotation Policy**: Document manual rotation process for POC

### Audit Trail
- **What to Log**:
  - CSV ingestion events (file name, timestamp, row count)
  - KPI computation results
  - AI API calls (request ID, token count, cost)
  - Policy violations detected
  - Alert dispatch events (recipient, channel, timestamp, success/failure)
  - Configuration changes (threshold updates)
- **Format**: Structured JSON logs
- **Retention**: 90 days (configurable)

### Access Control
- **File System**: Restrict CSV directory to application user only
- **Docker**: Run container as non-root user
- **Secrets**: Restrict environment variable access

## Performance Optimization Strategy

### Phase 1: Baseline Measurement
- Instrument each pipeline stage with timing
- Identify bottlenecks with profiling (cProfile, line_profiler)

### Phase 2: Optimization Priorities
1. **CSV Parsing**: Use chunked reading for large files
2. **KPI Computation**: Vectorized operations with NumPy/Pandas
3. **AI Analysis**: Batch API calls, use GPT-4-turbo for speed
4. **Alert Dispatch**: Parallel delivery to Slack and email

### Phase 3: Scaling Strategies (if needed)
- Switch Pandas → Polars for lazy evaluation
- Implement multiprocessing for per-app KPI calculations
- Cache GPT-4 responses for similar anomalies

## Error Handling & Graceful Degradation

### Failure Scenarios

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| CSV file missing | Critical - no data to process | Alert operations team, retry after 30 min |
| CSV schema change | High - parsing fails | Flexible schema detection, log warning, attempt best-effort parse |
| GPT-4 API timeout | Medium - no AI explanations | Fall back to rule-based detection, simpler explanations |
| Slack API failure | Medium - alerts not delivered | Retry 3x with exponential backoff, fall back to email |
| Email SMTP failure | High - no alerts delivered | Queue alerts, retry hourly, escalate after 3 failures |
| Threshold config invalid | Critical - no violation detection | Validate config on load, fail fast with clear error message |

### Retry Logic
- **AI API Calls**: 3 retries, exponential backoff (1s, 2s, 4s)
- **Slack Delivery**: 3 retries, exponential backoff (5s, 10s, 20s)
- **Email Delivery**: 5 retries, exponential backoff (30s, 1m, 2m, 4m, 8m)
- **CSV Ingestion**: 1 retry after 30 minutes

## Testing Strategy

### Unit Tests (with Mocks and Ports)
- **Coverage Target**: >80% for core logic
- **Approach**: Test modules in isolation using mock adapters
- **Focus Areas**:
  - **CSV parsing**: Edge cases (malformed data, schema changes) - no external I/O
  - **KPI calculation**: Accuracy with known inputs - use FixedClock for deterministic timestamps
  - **Policy rule evaluation**: Threshold and custom rule logic - mock Storage port
  - **Alert message formatting**: PRD template compliance - mock SlackSender/EmailSender ports
  - **Configuration validation**: Pydantic model validation - test invalid configs
  - **DTO validation**: Pydantic validators reject invalid data

**Example Unit Test:**
```python
def test_kpi_computation_orphan_accounts():
    mock_storage = Mock(spec=Storage)
    mock_clock = FixedClock(datetime(2025, 11, 2, 9, 0, 0))

    kpi_service = KPIService(storage=mock_storage, clock=mock_clock)

    # Given: Sample UAM data
    data = pd.DataFrame({
        'user_id': ['U1', 'U2', 'U3'],
        'app_id': ['APP-1', 'APP-1', 'APP-1'],
        'status': ['active', 'active', 'active'],
        'exit_date': [None, '2025-10-01', '2025-10-15']  # 2 orphans
    })

    # When: Computing orphan accounts KPI
    result = kpi_service.compute_orphan_accounts(data)

    # Then: Correct KPIRecord returned
    assert result.kpi_name == 'orphan_accounts'
    assert result.value == 2
    assert result.computed_at == datetime(2025, 11, 2, 9, 0, 0)
    mock_storage.persist_kpi.assert_called_once()
```

### Integration Tests (with In-Memory/File Adapters)
- **End-to-End Flow**: Ingestion → KPI → AI → Policy → Alert pipeline
- **Adapter Strategy**:
  - **Slack/Email**: Use `InMemoryAlertSender` that records calls instead of sending
  - **OpenAI**: Use `MockOpenAIClient` with canned responses
  - **Storage**: Use `InMemoryStorage` or temporary file-based storage
- **Performance**: Validate <15 min processing with full-scale test dataset (1,200 apps)
- **Scenario Coverage**: Happy path, error recovery, degraded mode (AI failure)

**Example Integration Test:**
```python
def test_end_to_end_critical_alert_dispatch():
    # Given: In-memory adapters
    in_memory_slack = InMemorySlackSender()
    in_memory_storage = InMemoryStorage()
    mock_ai = MockOpenAIClient(canned_response="High risk due to spike")

    # Build pipeline with test adapters
    pipeline = build_pipeline(
        slack_sender=in_memory_slack,
        storage=in_memory_storage,
        ai_client=mock_ai
    )

    # When: Processing CSV with critical violation
    csv_path = 'test_data/critical_orphan_spike.csv'
    pipeline.run(csv_path)

    # Then: Alert dispatched to in-memory sender
    alerts = in_memory_slack.get_sent_alerts()
    assert len(alerts) == 1
    assert alerts[0].severity == Severity.CRITICAL
    assert alerts[0].risk_score > 90

    # And: Violation persisted to storage
    violations = in_memory_storage.query_violations(app_id='APP-1234', state='NEW')
    assert len(violations) == 1
```

### Contract Tests
- **DTO Serialization**: Verify all DTOs can serialize to/from JSON without data loss
- **Port Implementations**: Verify all adapters satisfy their port interface contracts
- **Backward Compatibility**: Ensure old serialized DTOs can still be deserialized after schema changes

### Acceptance Tests
- **User Stories**: Test each US-1 through US-6 from PRD with real adapters (Slack sandbox, test email)
- **Success Criteria Validation**:
  - Measure false positive rate over test period
  - Verify alert timing (<5 min)
  - Validate all 7 KPIs calculated correctly
- **Compliance Scenarios**: Test SoD rules, threshold breaches, severity classification

### Performance Tests
- **Load Testing**: Full dataset (1,200 apps × 40,000 users)
- **Profiling**: Identify bottlenecks using cProfile
- **Budget Verification**: Measure per-stage timings against targets (4+7+2.5+1.5+3 = ~14 min)
- **Concurrency Testing**: Verify AI starts when first 100 apps complete

### Test Data Strategy
- **Synthetic Data**: Generate realistic CSV files with known violations
- **Seed Data**: Fixed random seed for reproducible test runs
- **Edge Cases**: Missing fields, malformed data, schema changes, orphan spikes, SoD conflicts

## Deployment Model

### POC Deployment (Docker Compose)
```yaml
services:
  uam-compliance:
    build: .
    volumes:
      - ./data:/data  # CSV input directory
      - ./logs:/logs  # Audit logs
      - ./config:/config  # Threshold configuration
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}

  postgres:  # Optional alert storage
    image: postgres:15
    environment:
      - POSTGRES_DB=uam_alerts
```

### On-Premise Production (Post-POC)
- Kubernetes deployment with Helm charts
- Persistent volumes for audit logs
- Secrets management via Vault or Kubernetes Secrets
- High availability: 2+ replicas with leader election

## Migration Plan

N/A - Greenfield implementation. No existing system to migrate from.

## Risks / Trade-offs

### Risk 1: GPT-4 API Cost Escalation
- **Likelihood**: Medium
- **Impact**: Medium
- **Mitigation**:
  - Implement token counting and cost monitoring
  - Set daily cost limits ($50/day for POC)
  - Cache GPT-4 responses for similar anomalies
  - Use GPT-4-turbo (cheaper, faster) instead of GPT-4

### Risk 2: High False Positive Rate
- **Likelihood**: High (expected during tuning)
- **Impact**: High (alert fatigue, user rejection)
- **Mitigation**:
  - Iterative threshold tuning with feedback loop
  - Implement confidence scoring (only alert high-confidence violations)
  - Add severity filtering (start with CRITICAL only, expand gradually)
  - Weekly review meetings with compliance officers

### Risk 3: CSV Schema Changes Break Parsing
- **Likelihood**: Medium
- **Impact**: Critical (data processing stops)
- **Mitigation**:
  - Flexible schema detection (infer column types)
  - Required vs optional columns configuration
  - Alert on schema drift detection
  - Comprehensive error logging

### Risk 4: Performance Targets Missed
- **Likelihood**: Low (dataset manageable for modern hardware)
- **Impact**: Medium (delays daily insights)
- **Mitigation**:
  - Early performance testing with full dataset
  - Pandas → Polars migration path ready
  - Multiprocessing for parallelizable tasks
  - Incremental loading optimization

### Risk 5: Alert Fatigue
- **Likelihood**: Medium
- **Impact**: High (users ignore alerts)
- **Mitigation**:
  - Strict severity filtering (start conservative)
  - Digest mode for non-critical alerts
  - Deduplication logic
  - Weekly trend summary instead of daily noise

## Open Questions

1. **CSV Delivery Mechanism**: How will daily CSV files be delivered? (Shared drive, SFTP, S3 bucket?)
   - **Assumption for POC**: Files placed in mounted directory by external process

2. **Slack Workspace Setup**: Who will provide Slack bot credentials and channel access?
   - **Assumption for POC**: Credentials provided by stakeholder before Phase 3

3. **Email Recipients**: How to map application ownership to email addresses?
   - **Assumption for POC**: Static configuration file with app → email mappings

4. **Historical Baseline Data**: Is historical UAM data available for trend analysis?
   - **Assumption for POC**: Start tracking from Day 1, no historical baseline initially

5. **Compliance Policy Rules**: Which specific banking policies need to be encoded?
   - **Assumption for POC**: Start with threshold-based rules, add custom rules based on feedback

6. **Data Retention**: How long should alert logs and CSV files be retained?
   - **Assumption for POC**: 90 days, configurable

7. **Disaster Recovery**: What are RTO/RPO requirements?
   - **Assumption for POC**: Best-effort recovery, no strict SLA (production to define)

8. **GPT-4 Data Privacy**: Is sending anonymized KPI data to OpenAI API acceptable?
   - **Assumption for POC**: Yes, with data anonymization (no PII in prompts)
   - **Blocker if No**: Must use on-premise LLM (adds significant complexity)
