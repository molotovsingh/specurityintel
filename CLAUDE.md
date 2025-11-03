<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **UAM Compliance Intelligence System** - an AI-powered solution that automates the analysis of User Access Management (UAM) security KPIs for banking institutions. The system detects policy violations, highlights emerging risks, and generates real-time, explainable alerts through Slack and email.

**Current Phase:** Proof of Concept (POC)
**Target Timeline:** 4-6 weeks (5 phases)

## Architecture

The system is designed as a data pipeline with the following key components:

1. **Data Ingestion Layer**: Automated daily CSV ingestion from existing UAM dashboards
2. **KPI Computation Engine**: Calculates security metrics (privileged accounts, failed access, orphan accounts, etc.)
3. **AI Analysis Layer**: Uses LangChain + GPT-4 for anomaly detection, risk scoring, and explainable intelligence
4. **Policy Rule Engine**: Threshold-based and custom rule detection for banking compliance
5. **Alerting System**: Real-time Slack and email notifications with context-rich explanations

### Technology Stack

- **Python 3.11+** (core language)
- **Pandas/Polars** (data processing)
- **NumPy/SciPy** (statistical analysis)
- **LangChain + GPT-4** (explainable AI)
- **Slack SDK / SMTP** (alerting)
- **Docker** (deployment)
- **Airflow/Prefect** (orchestration)

## Key Requirements

### Data Processing
- Handle 1,200 apps × 40,000 users daily
- Complete daily processing in < 15 minutes
- Support both full and incremental CSV loads
- Flexible parsing to handle schema changes

### KPI Tracking
The system monitors 7 core UAM security metrics:
1. Privileged accounts
2. Failed access attempts
3. Access provisioning time
4. Orphan accounts
5. Periodic access review status
6. Policy violations
7. Additional KPIs (excessive permissions, dormant accounts)

### AI-Powered Features
- Multi-factor risk scoring (0-100 scale)
- Week-on-week trend analysis
- Cross-app pattern detection
- Explainable alerts with root cause, context, and recommended actions

### Alerting
- Alert dispatch < 5 minutes after detection
- Persona-based routing (Compliance Officers vs Application Owners)
- Severity-based filtering to prevent alert fatigue
- Target: < 10% false positive rate

## Security & Privacy

- **No credentials stored** - system reads CSV exports only
- **Encryption required** - data at rest and in transit
- **Audit logging** - all processing and alert events must be logged
- **On-premise deployment** - for banking data privacy requirements

## Configuration

The system uses YAML/JSON for threshold configuration. Example structure:

```yaml
alert_thresholds:
  orphan_accounts:
    warning: 3
    critical: 5

notification_settings:
  slack:
    enabled: true
    channels:
      critical: "#security-critical"
      general: "#compliance-alerts"
```

## POC Success Criteria

- 30 consecutive days of data processed
- < 10% false positive rate
- Alerts sent within 5 minutes of detection
- Positive feedback from 80% of compliance users
- Identify ≥ 5 previously undetected risks

## Implementation Phases (POC)

1. **Phase 1 (Week 1-2)**: CSV ingestion, validation, KPI engine
2. **Phase 2 (Week 2-3)**: AI anomaly detection, risk scoring, policy rules
3. **Phase 3 (Week 3-4)**: Slack + Email alerting
4. **Phase 4 (Week 4-5)**: Testing, threshold tuning, accuracy improvements
5. **Phase 5 (Week 5-6)**: Demo, documentation, handover

## Out of Scope for POC

- Dashboard UI
- API endpoints
- User authentication & RBAC
- Historical data warehouse
- Advanced ML model training
- Ticketing system integrations (ServiceNow/Jira)
- Mobile notifications

These features are planned for post-POC phases (Q1-Q4 2026).

## Alert Format

All alerts must include:
- Severity level (CRITICAL/HIGH/MEDIUM/LOW)
- Risk score (0-100)
- Root cause explanation
- Baseline comparison (previous week/month)
- Impact assessment
- Recommended remediation actions

See Section 14.2 of UAM-Compliance-PRD-V2.md for the complete alert template.

## Development Notes

- Prioritize explainability - every AI decision must be human-understandable
- Design for graceful degradation when AI services fail
- Implement retry logic for all external integrations
- Use flexible CSV parsing to handle schema evolution
- Log all threshold triggers for post-POC tuning
- remote is https://github.com/molotovsingh/specurityintel.git