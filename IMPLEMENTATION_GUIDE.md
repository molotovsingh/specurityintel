# UAM Compliance Intelligence System - Implementation Guide

**Status**: ✅ Proposal Approved - Ready for Implementation
**OpenSpec Change ID**: `implement-uam-poc`
**Architecture**: Hexagonal Modular Monolith with Ports & Adapters
**Timeline**: 5-7 weeks (POC)

---

## 📋 Quick Start

### Prerequisites
- Python 3.11+
- Poetry or pip
- Docker & Docker Compose
- PostgreSQL 15 (optional for POC)
- Access to: OpenAI API, Slack workspace, SMTP server

### Initial Setup

```bash
# 1. Clone/navigate to project
cd /Users/aks/seccomp

# 2. Create project structure
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies (create requirements.txt from proposal)
pip install pydantic pandas numpy scipy langchain openai slack-sdk pyyaml jinja2 structlog prefect pytest

# 4. Review the specs
openspec show implement-uam-poc
openspec list --specs
```

---

## 🏗️ Project Structure (Recommended)

```
uam-compliance/
├── src/
│   ├── interfaces/              # IMPLEMENT FIRST (Foundation)
│   │   ├── __init__.py
│   │   ├── dto.py              # All Pydantic DTOs (Severity, KPIRecord, Alert, etc.)
│   │   ├── ports.py            # Port interfaces (SlackSender, EmailSender, etc.)
│   │   └── errors.py           # Custom exception hierarchy
│   │
│   ├── modules/                # Core domain modules
│   │   ├── ingestion/
│   │   │   ├── __init__.py
│   │   │   ├── parser.py       # CSV parsing logic
│   │   │   └── validator.py    # Data validation
│   │   ├── kpi/
│   │   │   ├── __init__.py
│   │   │   ├── calculators.py  # KPI computation (returns KPIRecord DTOs)
│   │   │   └── aggregator.py
│   │   ├── ai/
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py     # Uses OpenAIClient port
│   │   │   └── scoring.py      # Risk scoring (returns RiskAnalysisResult DTOs)
│   │   ├── policy/
│   │   │   ├── __init__.py
│   │   │   ├── rules.py        # Rule evaluation (creates Violation DTOs)
│   │   │   └── thresholds.py
│   │   ├── alerting/
│   │   │   ├── __init__.py
│   │   │   ├── generator.py    # Alert generation (uses Alert DTO)
│   │   │   └── router.py       # Persona-based routing
│   │   └── config/
│   │       ├── __init__.py
│   │       ├── loader.py       # Pydantic config models
│   │       └── validator.py
│   │
│   ├── adapters/               # Infrastructure implementations
│   │   ├── __init__.py
│   │   ├── slack_adapter.py    # Implements SlackSender port
│   │   ├── email_adapter.py    # Implements EmailSender port
│   │   ├── openai_adapter.py   # Implements OpenAIClient port
│   │   ├── storage/
│   │   │   ├── jsonl.py        # Implements Storage port (JSON Lines)
│   │   │   └── postgres.py     # Implements Storage port (PostgreSQL)
│   │   ├── audit.py            # Implements AuditLogger port
│   │   └── clock.py            # SystemClock and FixedClock
│   │
│   ├── composition_root.py     # Dependency injection wiring
│   └── main.py                 # Entry point
│
├── tests/
│   ├── unit/                   # Unit tests with mocks
│   │   ├── test_dto.py         # Pydantic validation tests
│   │   ├── test_kpi.py         # KPI calculators with mock Storage
│   │   └── test_alerting.py    # Alerting with mock ports
│   ├── integration/            # Integration tests with in-memory adapters
│   │   └── test_pipeline.py
│   └── fixtures/
│       ├── mock_adapters.py    # Mock implementations for testing
│       └── sample_data.csv
│
├── config/                     # Configuration files
│   ├── thresholds.yaml
│   ├── notifications.yaml
│   └── examples/               # Example configs with comments
│
├── data/                       # CSV input directory (gitignored)
├── logs/                       # Audit logs (gitignored)
├── orchestration/              # Prefect flows
│   └── daily_pipeline.py
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Poetry config (optional)
├── README.md
└── .env.example                # Example environment variables
```

---

## 🎯 Implementation Order (Critical Path)

### Phase 0: Interfaces Foundation ⚠️ **DO THIS FIRST**

**Why**: All other modules depend on DTOs and ports. Implementing this first prevents rework.

**Steps**:
1. Create `src/interfaces/dto.py` with all Pydantic models from design.md lines 315-402
2. Create `src/interfaces/ports.py` with all ABC interfaces from design.md lines 417-488
3. Create `src/interfaces/errors.py` with custom exception hierarchy
4. Write validation tests for each DTO (`tests/unit/test_dto.py`)

**Validation**: Run `pytest tests/unit/test_dto.py` - all DTOs should validate correctly

**Estimated Time**: 4-6 hours

**Reference**:
- design.md lines 309-410 (DTOs)
- design.md lines 411-488 (Ports)
- specs/interfaces/spec.md (15 requirements, 39 scenarios)

---

### Phase 1: Project Setup (Week 1)

**Tasks 1.1-1.5**: Standard Python project setup
- Create virtual environment
- Set up Poetry/pip dependencies
- Configure Docker (use design.md lines 832-841 for docker-compose template)
- Set up structlog for audit logging

**Tasks 1A.1-1A.7**: Implement interfaces module (see Phase 0 above)

**Deliverables**:
- ✅ All DTOs defined and tested
- ✅ All port interfaces defined
- ✅ Project structure created
- ✅ Dependencies installed

---

### Phase 2-5: Module Implementation (Weeks 2-6)

**Key Principle**: Each module should:
1. Accept ports via constructor (dependency injection)
2. Return DTOs (never raw dicts or None types crossing boundaries)
3. Have unit tests using mock ports
4. Not import adapters directly

**Example Pattern**:
```python
# modules/kpi/calculators.py
from interfaces.dto import KPIRecord
from interfaces.ports import Storage, Clock

class OrphanAccountsCalculator:
    def __init__(self, storage: Storage, clock: Clock):
        self.storage = storage
        self.clock = clock

    def compute(self, data: pd.DataFrame, app_id: str) -> KPIRecord:
        orphan_count = # ... calculation logic

        kpi = KPIRecord(
            app_id=app_id,
            kpi_name="orphan_accounts",
            value=float(orphan_count),
            computed_at=self.clock.now()
        )

        self.storage.persist_kpi(kpi)
        return kpi
```

---

## 🧪 Testing Strategy

### Unit Tests (Mock Everything External)

```python
# tests/unit/test_kpi.py
from unittest.mock import Mock
from datetime import datetime
from interfaces.ports import Storage, Clock
from modules.kpi.calculators import OrphanAccountsCalculator

def test_orphan_accounts_calculation():
    # Arrange
    mock_storage = Mock(spec=Storage)
    fixed_clock = FixedClock(datetime(2025, 11, 2, 9, 0))
    calculator = OrphanAccountsCalculator(storage=mock_storage, clock=fixed_clock)

    data = create_test_dataframe()  # Sample data

    # Act
    result = calculator.compute(data, "APP-123")

    # Assert
    assert result.kpi_name == "orphan_accounts"
    assert result.value == 2  # Expected count
    assert result.computed_at == datetime(2025, 11, 2, 9, 0)
    mock_storage.persist_kpi.assert_called_once()
```

### Integration Tests (In-Memory Adapters)

```python
# tests/integration/test_pipeline.py
from adapters.in_memory import InMemoryStorage, InMemorySlackSender

def test_end_to_end_pipeline():
    # Use in-memory adapters (no external calls)
    storage = InMemoryStorage()
    slack = InMemorySlackSender()

    # Run pipeline
    pipeline.run('tests/fixtures/critical_violation.csv')

    # Assert
    alerts = slack.get_sent_alerts()
    assert len(alerts) == 1
    assert alerts[0].severity == Severity.CRITICAL
```

---

## 📐 Architecture Patterns

### Dependency Injection (Composition Root)

All adapters are wired in `src/composition_root.py`:

```python
# composition_root.py
from adapters.slack_adapter import SlackAdapter
from adapters.openai_adapter import OpenAIAdapter
from modules.alerting.generator import AlertingService
from config.loader import load_config

def build_production_services():
    config = load_config()

    # Instantiate adapters
    slack = SlackAdapter(bot_token=config.slack_bot_token)
    openai = OpenAIAdapter(api_key=config.openai_api_key)
    storage = PostgresStorage(config.db_url) if config.db_url else JsonlStorage()

    # Inject into services
    alerting = AlertingService(
        slack_sender=slack,
        storage=storage
    )

    return {
        'alerting': alerting,
        'slack': slack,
        'openai': openai,
        'storage': storage
    }
```

### Port Interface Example

```python
# interfaces/ports.py
from abc import ABC, abstractmethod
from interfaces.dto import Alert, DeliveryResult

class SlackSender(ABC):
    """Port for Slack alert delivery."""

    @abstractmethod
    def send(self, alert: Alert) -> DeliveryResult:
        """
        Send alert to Slack channel based on severity.

        Args:
            alert: Alert DTO containing message and routing info

        Returns:
            DeliveryResult with success status and retry count

        Raises:
            IntegrationError: If delivery fails after retries
        """
        pass
```

### Adapter Implementation Example

```python
# adapters/slack_adapter.py
from slack_sdk import WebClient
from interfaces.ports import SlackSender
from interfaces.dto import Alert, DeliveryResult, Severity

class SlackAdapter(SlackSender):
    """Concrete Slack implementation using slack-sdk."""

    def __init__(self, bot_token: str):
        self.client = WebClient(token=bot_token)
        self.channel_map = {
            Severity.CRITICAL: "#security-critical",
            Severity.HIGH: "#security-critical",
            Severity.MEDIUM: "#compliance-alerts",
            Severity.LOW: "#compliance-alerts"
        }

    def send(self, alert: Alert) -> DeliveryResult:
        channel = self.channel_map[alert.severity]

        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=self._format_blocks(alert)
            )
            return DeliveryResult(success=True, delivered_at=datetime.now())
        except SlackApiError as e:
            # Retry logic here
            return DeliveryResult(success=False, error=str(e))

    def _format_blocks(self, alert: Alert) -> list:
        # Slack Block Kit formatting
        pass
```

---

## 🔐 Security Checklist

Before deploying:

- [ ] No API keys in code (use environment variables)
- [ ] Secrets redacted in logs (use structlog processors)
- [ ] TLS for external calls (OpenAI, Slack)
- [ ] CSV files encrypted at rest (AES-256)
- [ ] Audit logs append-only (JSONL with file permissions)
- [ ] Container runs as non-root user
- [ ] No PII sent to OpenAI (anonymize IDs in prompts)

---

## 📊 Performance Targets

Monitor these during implementation:

| Stage | Target | How to Measure |
|-------|--------|---------------|
| Ingestion | <4 min | Time CSV load to DataFrame ready |
| KPI Computation | <7 min | Time all 7 KPIs calculated |
| AI Analysis | <2.5 min effective | Time first analysis to last (overlapping) |
| Policy Evaluation | <1.5 min | Time threshold checks + rule eval |
| Alert Dispatch | <3 min | Time alert generated to delivered |
| **Total E2E** | **<15 min** | Ingestion start to last alert dispatched |

**Optimization Tips**:
- Use Polars instead of Pandas if >15 min
- Batch GPT-4 calls (50 apps per call)
- Parallel alert dispatch (Slack + Email concurrently)
- Profile with cProfile if slow

---

## 🚀 Deployment

### POC Deployment (Docker Compose)

```bash
# 1. Build image
docker-compose build

# 2. Set environment variables
cp .env.example .env
# Edit .env with API keys

# 3. Run
docker-compose up -d

# 4. Check logs
docker-compose logs -f uam-compliance

# 5. Manual trigger (for testing)
docker-compose exec uam-compliance python -m orchestration.daily_pipeline
```

### Production Deployment (Future)

See design.md lines 848-853 for Kubernetes with Helm charts.

---

## 📖 Reference Documentation

| Document | Location | Purpose |
|----------|----------|---------|
| **Proposal** | `openspec/changes/implement-uam-poc/proposal.md` | Why, what, impact |
| **Design** | `openspec/changes/implement-uam-poc/design.md` | Architecture, DTOs, ports, read model (937 lines) |
| **Tasks** | `openspec/changes/implement-uam-poc/tasks.md` | Implementation checklist (171 tasks) |
| **Specs** | `openspec/changes/implement-uam-poc/specs/` | 7 capabilities, 83 requirements, 195 scenarios |
| **PRD** | `UAM-Compliance-PRD-V2.md` | Original requirements |

**Key Design Sections**:
- Lines 39-53: Architecture style (hexagonal)
- Lines 309-410: DTOs (copy these to code)
- Lines 411-488: Ports (copy these to code)
- Lines 580-663: Read model schema (PostgreSQL DDL)
- Lines 729-829: Testing strategy with examples

---

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**
- Ensure `src/` is in PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:src`

**Pydantic validation errors**
- Check DTO field types match exactly
- Use `.dict()` to debug: `print(kpi_record.dict())`

**Mock adapter not working in tests**
- Verify mock is created with `spec=PortInterface`
- Example: `Mock(spec=SlackSender)` not just `Mock()`

**OpenAI API rate limits**
- Implement caching (see design.md line 336)
- Use GPT-4-turbo (cheaper, faster)
- Add exponential backoff in OpenAIAdapter

**Alerts not dispatching**
- Check Slack bot token format (should start with `xoxb-`)
- Verify channel exists and bot is invited
- Check SMTP credentials in .env

---

## ✅ Acceptance Criteria (POC Success)

Before marking POC complete, verify:

- [ ] All 7 KPIs calculate correctly (validated with test data)
- [ ] Alerts dispatch to Slack within 5 minutes
- [ ] Email fallback works when Slack fails
- [ ] Processing completes in <15 minutes for full dataset
- [ ] Unit test coverage >80%
- [ ] Integration tests pass with in-memory adapters
- [ ] False positive rate measured (target <10%)
- [ ] Audit logs capture all events (JSONL format)
- [ ] Configuration hot-reload works for thresholds
- [ ] Docker Compose deployment successful
- [ ] Violation state tracking works (NEW/RECURRING/RESOLVED)
- [ ] Persona-based routing correct (compliance vs app owner)

---

## 🎓 For New Developers

**Start Here**:
1. Read this guide (you are here)
2. Read `design.md` lines 39-53 (architecture overview)
3. Implement `src/interfaces/dto.py` from design.md lines 315-402
4. Implement `src/interfaces/ports.py` from design.md lines 417-488
5. Write tests for one DTO, run `pytest`
6. Ask questions in team channel

**Learning Path**:
- Day 1: DTOs and ports
- Day 2: One KPI calculator with tests
- Day 3: One adapter (SlackAdapter or EmailAdapter)
- Day 4: Wire one end-to-end flow

**Get Help**:
- Slack: #uam-compliance-dev
- Docs: This file + design.md
- Specs: `openspec show implement-uam-poc`

---

## 📞 Support

**Technical Questions**: Review design.md first, then ask team lead
**OpenSpec Questions**: Run `openspec show <capability> --type spec`
**Architecture Questions**: See design.md "Architecture Overview" section

---

**Last Updated**: 2025-11-02
**OpenSpec Status**: ✅ Validated (`openspec validate implement-uam-poc --strict`)
**Ready to Implement**: Yes - all specs defined, architecture documented, tasks planned
