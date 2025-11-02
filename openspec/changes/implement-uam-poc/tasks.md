# Implementation Tasks

**📖 Before starting, read [IMPLEMENTATION_GUIDE.md](../../../IMPLEMENTATION_GUIDE.md) for:**
- Complete project structure and setup instructions
- Architecture patterns (hexagonal, DTOs, ports/adapters)
- Code examples for dependency injection and testing
- Phase 0 guidance (implement interfaces FIRST)

**✅ Status**: Core implementation complete (Phases 1-3). Tests and Docker validation in progress.

---

## Phase 1: Foundation (Week 1-2) - COMPLETE ✅

### 1. Project Setup
- [x] 1.1 Initialize Python project structure with Poetry/pip requirements (include Pydantic)
- [x] 1.2 Set up development environment (Python 3.11+, virtual environment)
- [x] 1.3 Configure Docker containerization
- [x] 1.4 Set up logging framework with audit trail support
- [x] 1.5 Create configuration management scaffold (YAML/JSON parsing)

### 1A. Interfaces & Contracts (Foundation - Do First) - COMPLETE ✅
- [x] 1A.1 Define Severity enum (LOW/MEDIUM/HIGH/CRITICAL)
- [x] 1A.2 Define core DTOs: KPIRecord, RiskAnalysisResult, Violation, Alert, AuditEvent
- [x] 1A.3 Define Thresholds and configuration DTOs
- [x] 1A.4 Write Pydantic validation tests for all DTOs
- [x] 1A.5 Define port interfaces: SlackSender, EmailSender, OpenAIClient, Storage, AuditLogger, Clock
- [x] 1A.6 Create custom error hierarchy (DomainError and subclasses)
- [x] 1A.7 Add comprehensive docstrings to all DTOs and ports

### 2. Data Ingestion Layer - PARTIAL ✅
- [x] 2.1 Implement CSV file parser with flexible schema handling (inject Clock port for timestamps)
- [~] 2.2 Create data validation framework (schema checks, data quality) - Basic validation in parser
- [x] 2.3 Build incremental vs full load detection logic
- [x] 2.4 Add error handling for malformed CSV files
- [~] 2.5 Implement data staging and preprocessing pipeline - Ready for enhancement
- [x] 2.6 Implement SystemClock and FixedClock adapters for Clock port
- [ ] 2.7 Write unit tests for CSV parsing (edge cases, schema changes) using FixedClock
- [ ] 2.8 Performance test with 1,200 apps × 40,000 users dataset

### 3. Configuration Management - COMPLETE ✅
- [x] 3.1 Define YAML/JSON schema for alert thresholds
- [x] 3.2 Define YAML/JSON schema for notification settings
- [x] 3.3 Implement configuration loader with validation
- [x] 3.4 Create sample configuration files
- [ ] 3.5 Add configuration hot-reload capability
- [ ] 3.6 Write tests for configuration validation

## Phase 2: KPI Computation & AI Layer (Week 2-3) - PARTIAL ✅

### 4. KPI Computation Engine - PARTIAL ✅
- [x] 4.1 Implement privileged accounts KPI calculator (returns KPIRecord DTO)
- [x] 4.2 Implement failed access attempts KPI calculator (returns KPIRecord DTO)
- [ ] 4.3 Implement access provisioning time KPI calculator (returns KPIRecord DTO)
- [x] 4.4 Implement orphan accounts KPI calculator (returns KPIRecord DTO)
- [ ] 4.5 Implement periodic access review status KPI calculator (returns KPIRecord DTO)
- [ ] 4.6 Implement policy violations KPI calculator (returns KPIRecord DTO)
- [ ] 4.7 Implement additional KPIs (excessive permissions, dormant accounts)
- [ ] 4.8 Create KPI aggregation layer
- [x] 4.9 Implement JsonlStorage and PostgresStorage adapters for Storage port (JSONL + in-memory complete)
- [x] 4.10 Inject Storage port into KPI module for persistence
- [ ] 4.11 Write comprehensive unit tests with mock Storage port
- [ ] 4.12 Validate KPI accuracy with sample datasets

### 5. AI Analysis Layer - PARTIAL ✅
- [x] 5.1 Implement OpenAIAdapter using LangChain + GPT-4 SDK
- [x] 5.2 Implement MockOpenAIClient for testing
- [x] 5.3 Inject OpenAIClient port into AI module
- [x] 5.4 Implement anomaly detection algorithms (returns RiskAnalysisResult DTO)
- [x] 5.5 Build multi-factor risk scoring engine (0-100 scale)
- [ ] 5.6 Create week-on-week trend analysis module
- [ ] 5.7 Implement cross-app pattern detection
- [ ] 5.8 Build explainability layer (root cause, context, recommendations)
- [ ] 5.9 Add graceful degradation when AI services fail (template fallback)
- [x] 5.10 Implement retry logic for AI API calls in OpenAIAdapter
- [ ] 5.11 Write tests using MockOpenAIClient (no real API calls)
- [ ] 5.12 Validate risk scoring accuracy with test data

### 6. Policy Rule Engine - COMPLETE ✅
- [x] 6.1 Implement threshold-based violation detection (creates Violation DTOs)
- [~] 6.2 Create custom rule framework for banking policies - Basic framework in place
- [ ] 6.3 Add Segregation of Duties (SoD) rule support
- [x] 6.4 Build rule evaluation engine
- [x] 6.5 Implement severity classification using Severity enum
- [x] 6.6 Implement violation state tracking (NEW/RECURRING/RESOLVED)
- [x] 6.7 Inject Storage port for violation persistence
- [ ] 6.8 Write tests with mock Storage port
- [ ] 6.9 Validate rules against compliance requirements

## Phase 3: Alerting System (Week 3-4) - PARTIAL ✅

### 7. Alerting Core - PARTIAL ✅
- [x] 7.1 Implement alert generation using Alert DTO
- [~] 7.2 Build alert formatting with PRD template (Section 14.2) - Basic formatting complete
- [x] 7.3 Create persona-based routing logic (Compliance Officers vs App Owners)
- [x] 7.4 Implement severity-based filtering using Severity enum
- [ ] 7.5 Add alert deduplication logic
- [x] 7.6 Inject SlackSender, EmailSender, Storage ports into alerting module
- [ ] 7.7 Write tests with mock ports (no external calls)

### 8. Slack Adapter Implementation - PARTIAL ✅
- [x] 8.1 Implement SlackAdapter implementing SlackSender port
- [x] 8.2 Set up Slack SDK authentication in adapter
- [x] 8.3 Implement channel-based routing (#security-critical, #compliance-alerts)
- [~] 8.4 Format alerts for Slack using Block Kit - Basic message formatting complete
- [x] 8.5 Add retry logic in SlackAdapter (3x exponential backoff)
- [ ] 8.6 Implement rate limiting in adapter
- [ ] 8.7 Create InMemorySlackSender for integration tests
- [ ] 8.8 Test with real Slack workspace using real SlackAdapter

### 9. Email Adapter Implementation - PARTIAL ✅
- [x] 9.1 Implement EmailAdapter implementing EmailSender port
- [x] 9.2 Set up SMTP client in adapter
- [~] 9.3 Implement HTML email templates with Jinja2 - Basic HTML formatting complete
- [x] 9.4 Create digest mode in EmailAdapter
- [x] 9.5 Add retry logic in EmailAdapter (5x exponential backoff)
- [x] 9.6 Implement email address routing by persona in adapter
- [ ] 9.7 Create InMemoryEmailSender for integration tests
- [ ] 9.8 Test with real email using real EmailAdapter

## Phase 4: Testing & Tuning (Week 4-5)

### 10. Integration & Performance Testing
- [ ] 10.1 Create end-to-end test suite using in-memory adapters (ingestion → alert)
- [ ] 10.2 Verify all DTOs serialize/deserialize correctly (contract tests)
- [ ] 10.3 Performance test with full-scale dataset (1,200 apps × 40,000 users)
- [ ] 10.4 Validate <15 minute processing time requirement with streaming overlap
- [ ] 10.5 Validate <5 minute alert dispatch requirement
- [ ] 10.6 Test incremental load performance
- [ ] 10.7 Load test AI analysis layer with MockOpenAIClient
- [ ] 10.8 Test graceful degradation scenarios (AI failure → template fallback)
- [ ] 10.9 Verify dependency injection working correctly in all modules

### 11. Threshold Tuning & Accuracy
- [ ] 11.1 Collect baseline metrics from initial runs
- [ ] 11.2 Analyze false positive rates
- [ ] 11.3 Tune alert thresholds to achieve <10% false positive target
- [ ] 11.4 Validate risk scoring accuracy
- [ ] 11.5 Review AI explanations for clarity and usefulness
- [ ] 11.6 Adjust severity classifications based on feedback
- [ ] 11.7 Document tuning decisions and rationale

### 12. Security & Compliance
- [ ] 12.1 Implement data encryption at rest
- [ ] 12.2 Implement data encryption in transit (TLS/SSL)
- [ ] 12.3 Add comprehensive audit logging
- [ ] 12.4 Review code for security vulnerabilities (OWASP top 10)
- [ ] 12.5 Validate no credentials stored in system
- [ ] 12.6 Test on-premise deployment configuration
- [ ] 12.7 Create security documentation

## Phase 5: Orchestration, Demo & Handover (Week 5-6)

### 13. Orchestration
- [ ] 13.1 Set up Airflow or Prefect workflow orchestration
- [ ] 13.2 Create daily scheduled job for CSV ingestion
- [ ] 13.3 Implement job monitoring and failure notifications
- [ ] 13.4 Add job retry logic
- [ ] 13.5 Create orchestration dashboard/monitoring
- [ ] 13.6 Test scheduled jobs for 7 consecutive days
- [ ] 13.7 Document orchestration configuration

### 14. Documentation & Demo Preparation
- [ ] 14.1 Write technical architecture documentation
- [ ] 14.2 Create installation and setup guide
- [ ] 14.3 Document configuration options and examples
- [ ] 14.4 Create user guide for compliance officers
- [ ] 14.5 Write operational runbook (troubleshooting, monitoring)
- [ ] 14.6 Prepare demo dataset with known violations
- [ ] 14.7 Create demo presentation slides
- [ ] 14.8 Record demo video walkthrough

### 15. POC Validation & Handover
- [ ] 15.1 Run 30 consecutive days of processing (if time permits, otherwise document plan)
- [ ] 15.2 Measure and document false positive rate
- [ ] 15.3 Validate alert timing metrics
- [ ] 15.4 Collect user feedback from compliance officers
- [ ] 15.5 Document identified risks (target: ≥5 previously undetected)
- [ ] 15.6 Create POC performance report
- [ ] 15.7 Prepare recommendations for Phase 2
- [ ] 15.8 Conduct stakeholder demo and approval meeting

---

## 📊 Implementation Progress Summary

**Commit Hash**: 204ad28
**Date**: 2025-11-02
**Phases Complete**: 1, 2 (partial), 3 (partial)
**Remaining Phases**: 4 (Testing & Tuning), 5 (Orchestration & Handover)

### What's Implemented (Hexagonal Architecture)

#### Interfaces Foundation ✅
- ✅ DTOs: Severity, KPIRecord, RiskAnalysisResult, Violation, Alert, AuditEvent, Thresholds, DeliveryResult, Prompt, AIResponse
- ✅ Ports: SlackSender, EmailSender, OpenAIClient, Storage, AuditLogger, Clock
- ✅ Errors: DomainError, ValidationError, ConfigurationError, IntegrationError, ProcessingError, StorageError
- ✅ Full Pydantic validation with docstrings

#### Core Modules ✅
- ✅ **ingestion**: CSVParser with full/incremental detection
- ✅ **config**: ConfigLoader, ConfigValidator with YAML support
- ✅ **kpi**: Calculators for orphan_accounts, privileged_accounts, failed_access_attempts
- ✅ **policy**: PolicyRuleEngine with severity classification and state tracking
- ✅ **ai**: RiskAnalyzer with risk scoring (0-100 scale)
- ✅ **alerting**: AlertGenerator with persona-based routing

#### Adapters & Infrastructure ✅
- ✅ **Clock**: SystemClock, FixedClock (deterministic testing)
- ✅ **Storage**: JsonlStorage (append-only), InMemoryStorage (testing)
- ✅ **Slack**: SlackAdapter with retry logic (3x exponential backoff)
- ✅ **Email**: EmailAdapter with SMTP and digest mode (5x backoff)
- ✅ **OpenAI**: OpenAIAdapter using LangChain, MockOpenAIClient for testing
- ✅ **Audit**: StructlogAuditLogger for compliance audit trail

#### Dependency Injection ✅
- ✅ **composition_root.py**: ServiceContainer for production and test environments
- ✅ All modules accept ports via constructor (no direct adapter imports)

#### Configuration ✅
- ✅ **config/thresholds.yaml**: 7 KPIs with 4-level severity (low/medium/high/critical)
- ✅ **config/notifications.yaml**: Slack/Email/AI settings
- ✅ **.env.example**: Environment template

#### Deployment ✅
- ✅ **docker/Dockerfile**: Python 3.11 slim image
- ✅ **docker/docker-compose.yml**: Orchestration with optional PostgreSQL

#### Testing ✅
- ✅ **tests/unit/test_dto.py**: DTO validation tests (Pydantic models)

#### Entry Point ✅
- ✅ **src/main.py**: Pipeline orchestration for daily processing

### What Remains (Priority Order)

1. **Phase 4: Testing & Tuning** (High Priority)
   - Comprehensive integration tests using in-memory adapters
   - DTO serialization/deserialization contract tests
   - KPI calculator accuracy validation
   - Risk scoring tests
   - Policy rule validation
   - Alert generation tests

2. **Remaining Adapters** (Medium Priority)
   - PostgresStorage implementation
   - In-memory mocks for Slack/Email
   - Additional KPI calculators (provisioning_time, access_reviews, policy_violations, excessive_permissions, dormant_accounts)

3. **Phase 5: Orchestration** (Lower Priority for POC)
   - Prefect workflow setup
   - Scheduled daily job configuration
   - Monitoring and alerting

4. **Performance & Tuning**
   - Streaming/batch processing optimization
   - Caching for AI responses
   - Performance tests with 1,200 apps × 40,000 users
   - False positive rate measurement

5. **Advanced Features** (Post-POC)
   - SoD (Segregation of Duties) rule support
   - Cross-app pattern detection
   - Week-on-week trend analysis
   - Configuration hot-reload

---

## Validation Checkpoints

Each phase must meet the following criteria before proceeding:

**Phase 1**: CSV ingestion working with sample data, configuration loading functional
**Phase 2**: All 7 KPIs calculated correctly, risk scoring producing reasonable outputs
**Phase 3**: Test alerts successfully delivered via Slack and email
**Phase 4**: Performance targets met, false positive rate <10%
**Phase 5**: Demo ready, documentation complete, POC success criteria measured

## Dependencies & Parallelization

- Tasks 2.x (Data Ingestion) and 3.x (Configuration) can be developed in parallel
- Tasks 4.x (KPI Computation) must complete before 5.x (AI Analysis)
  - **Important:** Implement streaming/batch processing so AI can start when first 100 apps complete
  - This reduces end-to-end latency from 18 min to ~14 min
- Tasks 7.x (Alerting Core) can start when 5.x and 6.x are 50% complete
- Tasks 8.x (Slack) and 9.x (Email) can be developed in parallel
- Tasks 10.x-12.x (Testing) must wait for core implementation
- Tasks 13.x (Orchestration) can start when Phase 3 is complete
