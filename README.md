# UAM Compliance Intelligence System

An AI-powered solution that automates User Access Management (UAM) compliance monitoring for banking institutions. This system detects policy violations, analyzes security risks, and provides real-time alerts with explainable insights.

## 🚀 Overview

The UAM Compliance Intelligence System transforms manual CSV-based security reviews into automated, intelligent monitoring. It processes daily access data, computes security KPIs, detects anomalies using AI, and sends actionable alerts through Slack and email.

### Key Features

- **🔄 Automated Data Processing** - Daily CSV ingestion and validation
- **📊 KPI Monitoring** - Track privileged accounts, failed access, orphan accounts, and more
- **🤖 AI-Powered Analysis** - Anomaly detection and risk scoring with explainable insights
- **⚡ Real-Time Alerting** - Slack and email notifications with context and remediation steps
- **🔒 Enterprise Security** - Encrypted data handling and audit logging
- **📈 Trend Analysis** - Weekly and monthly pattern detection

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CSV Data      │───▶│   Data Ingestion │───▶│   KPI Engine    │
│   Exports       │    │   & Validation   │    │   & Analysis    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack &       │◀───│   Alert Engine   │◀───│   AI Analysis   │
│   Email Alerts  │    │   & Routing      │    │   & Risk Scoring│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Tech Stack

- **Python 3.11+** - Core language
- **Pandas/Polars** - Data processing
- **NumPy/SciPy** - Statistical analysis  
- **LangChain + GPT-4** - Explainable AI
- **Slack SDK / SMTP** - Alerting
- **Prefect** - Workflow orchestration
- **Docker** - Containerization
- **Pydantic** - Data validation

## 📋 Supported KPIs

1. **Privileged Accounts** - Monitor high-risk access levels
2. **Failed Access Attempts** - Detect security breaches
3. **Access Provisioning Time** - Track onboarding efficiency
4. **Orphan Accounts** - Identify post-termination access risks
5. **Access Review Status** - Ensure compliance reviews are current
6. **Policy Violations** - Custom rule-based detection
7. **Excessive Permissions** - Permission creep analysis
8. **Dormant Accounts** - Inactive account monitoring

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional)
- Slack Bot Token (for Slack alerts)
- SMTP configuration (for email alerts)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/uam-compliance.git
   cd uam-compliance
   ```

2. **Install dependencies**
   ```bash
   # Using uv (recommended)
   uv sync
   
   # Or using pip
   pip install -e .
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Set up configuration**
   ```bash
   # Copy and edit configuration files
   cp config/thresholds.yaml.example config/thresholds.yaml
   cp config/notifications.yaml.example config/notifications.yaml
   ```

### Running the System

**Option 1: Direct execution**
```bash
python -m src.main
```

**Option 2: Docker**
```bash
docker-compose up -d
```

**Option 3: Prefect (for production)**
```bash
prefect deployment apply src/orchestration/prefect_flows.py
```

## 📁 Project Structure

```
├── src/
│   ├── adapters/          # External integrations (Slack, email, storage)
│   ├── modules/           # Core business logic
│   │   ├── ai/           # AI analysis and risk scoring
│   │   ├── alerting/     # Alert generation and routing
│   │   ├── config/       # Configuration management
│   │   ├── ingestion/    # Data parsing and validation
│   │   ├── kpi/          # KPI calculations
│   │   └── policy/       # Policy rule engine
│   └── orchestration/     # Workflow management
├── config/                # Configuration files
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scripts/               # Utility scripts
└── recommendations/       # Sample data and analysis
```

## ⚙️ Configuration

### Threshold Configuration (`config/thresholds.yaml`)

```yaml
alert_thresholds:
  orphan_accounts:
    warning: 3
    critical: 5
  failed_access_attempts:
    warning: 10
    critical: 25
  privileged_accounts:
    warning: 50
    critical: 100
```

### Notification Configuration (`config/notifications.yaml`)

```yaml
notification_settings:
  slack:
    enabled: true
    channels:
      critical: "#security-critical"
      general: "#compliance-alerts"
  email:
    enabled: true
    recipients:
      - compliance@bank.com
      - security@bank.com
```

## 📊 Sample Alert

```
🚨 CRITICAL UAM VIOLATION DETECTED

Application: Core Banking Platform (APP-1234)
Severity: CRITICAL
Risk Score: 95/100

Issue: 23 Orphan Accounts Detected (Threshold: 5)
Previous Week: 6 (+383%)

Why Flagged: Violates policy requiring cleanup within 30 days. 
Spike suggests offboarding failure.
Impact: 8 privileged orphan accounts pose critical risk.

Actions:
1. Disable 8 privileged accounts immediately
2. Review all 23 orphan accounts
3. Investigate offboarding workflow failure
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

## 📈 Performance

- **Data Processing**: < 15 minutes for daily CSV ingestion
- **Alert Dispatch**: < 5 minutes after violation detection
- **Availability**: 99% during business hours
- **Scale**: Supports 1,200+ applications and 40,000+ users

## 🔒 Security

- ✅ No sensitive credentials stored in code
- ✅ Encrypted data handling (at rest + in transit)
- ✅ Comprehensive audit logging
- ✅ Graceful degradation on failures
- ✅ Role-based alert routing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add tests for new functionality
- Update documentation as needed
- Use `black`, `ruff`, and `mypy` for code quality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions and support:

- 📧 Email: team@uam.com
- 📖 Documentation: See `docs/` directory
- 🐛 Issues: Use GitHub Issues

## 🗺️ Roadmap

### Phase 1: POC ✅
- [x] Basic data ingestion and KPI computation
- [x] AI-powered anomaly detection
- [x] Slack and email alerting
- [x] Docker deployment

### Phase 2: Dashboard (Q1 2026)
- [ ] Web-based KPI dashboards
- [ ] Historical analysis and drilldowns
- [ ] User management and RBAC

### Phase 3: Advanced Analytics (Q2 2026)
- [ ] Predictive modeling
- [ ] User behavior analytics
- [ ] Cross-application correlation

### Phase 4: Enterprise Integration (Q3 2026)
- [ ] ServiceNow/Jira integration
- [ ] IAM system connectors
- [ ] SIEM integration

---

**Built with ❤️ for banking security and compliance teams**