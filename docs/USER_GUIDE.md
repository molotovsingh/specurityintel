# UAM Compliance System - User Guide

## Overview

The User Access Management (UAM) Compliance Intelligence System automatically monitors user access across applications, calculates compliance metrics, and generates intelligent alerts for compliance teams.

## Quick Start

### 1. System Setup

#### Prerequisites
- Docker and Docker Compose installed
- Access to CSV files containing user access data
- Configuration files (thresholds.yaml, notifications.yaml)

#### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit with your values
nano .env
```

Required environment variables:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Slack Configuration  
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_COMPLIANCE_CHANNEL=#compliance-alerts
SLACK_APP_OWNERS_CHANNEL=#app-owners

# Email Configuration
SMTP_SERVER=smtp.company.com
SMTP_PORT=587
SMTP_USERNAME=alerts@company.com
SMTP_PASSWORD=your_email_password
SMTP_USE_TLS=true

# Storage Configuration
STORAGE_PATH=/data/uam
ENCRYPTION_KEY=your_base64_encryption_key  # Optional
```

### 2. Running the System

#### Using Docker Compose (Recommended)
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f uam-compliance

# Stop services
docker-compose down
```

#### Manual Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Run the system
python src/main.py
```

### 3. Data Preparation

#### CSV File Format
Your user access data should be in CSV format with the following columns:

```csv
user_id,username,email,department,app_id,role,access_level,last_login,created_at,manager_id,is_active,permissions
john.doe,john.doe@company.com,Engineering,APP-001,Admin,High,2024-10-15,2023-01-01,jane.smith,true,["read","write","delete"]
jane.smith,jane.smith@company.com,Engineering,APP-001,User,Medium,2024-10-14,2023-02-01,bob.wilson,true,["read","write"]
```

**Required Columns:**
- `user_id`: Unique user identifier
- `username`: User's username or email
- `app_id`: Application identifier
- `role`: User's role in the application
- `access_level`: Access level (Low, Medium, High, Admin)
- `last_login`: Last login date (YYYY-MM-DD format)
- `created_at`: Account creation date (YYYY-MM-DD format)
- `is_active`: Whether account is active (true/false)

**Optional Columns:**
- `department`: User's department
- `manager_id`: Manager's user ID
- `permissions`: List of specific permissions

#### File Organization
```
data/
├── incoming/          # Place new CSV files here
│   ├── app_001_users.csv
│   ├── app_002_users.csv
│   └── app_003_users.csv
├── processed/         # Files moved here after processing
└── archive/          # Old files archived here
```

## Configuration

### 1. Threshold Configuration

Edit `config/thresholds.yaml` to define alert thresholds:

```yaml
alert_thresholds:
  # Orphan Accounts - users without active managers
  orphan_accounts:
    low: 1
    medium: 3
    high: 5
    critical: 10
  
  # Privileged Accounts - users with elevated access
  privileged_accounts:
    low: 2
    medium: 5
    high: 10
    critical: 20
  
  # Failed Access Attempts - authentication failures
  failed_access_attempts:
    low: 5
    medium: 15
    high: 30
    critical: 50
  
  # Access Provisioning Time - days to grant access
  provisioning_time:
    low: 1
    medium: 3
    high: 5
    critical: 7
  
  # Access Review Status - overdue reviews
  access_reviews:
    low: 5
    medium: 15
    high: 30
    critical: 60
  
  # Policy Violations - rule violations
  policy_violations:
    low: 1
    medium: 3
    high: 5
    critical: 10
  
  # Dormant Accounts - inactive users
  dormant_accounts:
    low: 10
    medium: 25
    high: 50
    critical: 100
```

### 2. Notification Configuration

Edit `config/notifications.yaml` to configure alert delivery:

```yaml
slack:
  bot_token: "${SLACK_BOT_TOKEN}"
  channels:
    compliance: "#compliance-alerts"
    app_owners: "#app-owners"
  
email:
  smtp_server: "${SMTP_SERVER}"
  smtp_port: "${SMTP_PORT}"
  username: "${SMTP_USERNAME}"
  password: "${SMTP_PASSWORD}"
  use_tls: "${SMTP_USE_TLS}"
  templates_dir: "./templates"
  from_address: "UAM Compliance <uam@company.com>"

alerting:
  # Enable/disable channels
  slack_enabled: true
  email_enabled: true
  
  # Rate limiting
  max_alerts_per_minute: 10
  
  # Deduplication window (minutes)
  deduplication_window: 15
```

## Daily Operations

### 1. Monitoring Processing

#### Check System Status
```bash
# View recent processing logs
docker-compose logs uam-compliance --since=1h

# Check for errors
docker-compose logs uam-compliance | grep ERROR

# Monitor performance
docker-compose logs uam-compliance | grep "records/sec"
```

#### Processing Schedule
The system automatically:
1. **Monitors** the `data/incoming/` directory every 5 minutes
2. **Processes** new CSV files incrementally
3. **Calculates** KPIs for each application
4. **Evaluates** policies against thresholds
5. **Generates** AI-powered risk analysis
6. **Dispatches** alerts to appropriate channels

### 2. Reviewing Alerts

#### Slack Integration
Alerts appear in configured Slack channels:

```
#compliance-alerts
🚨 HIGH RISK: APP-001 - Excessive Orphan Accounts

Application: APP-001 (Customer Portal)
Risk Score: 85/100
Severity: HIGH

📊 Key Metrics:
• Orphan Accounts: 12 (threshold: 5)
• Privileged Accounts: 8 (threshold: 5)
• Policy Violations: 3 (threshold: 3)

🎯 Recommendations:
1. Review and assign managers to orphan accounts
2. Conduct privileged access review
3. Update access policies for APP-001

View Details: http://compliance-dashboard.company.com/app/APP-001
```

#### Email Notifications
Email alerts are sent to:
- **Compliance Officers**: All HIGH and CRITICAL alerts
- **Application Owners**: Alerts for their specific applications

### 3. Investigating Violations

#### Access Violation Details
Each alert includes:
- **Application Information**: App ID, name, owner
- **Violation Details**: Which KPIs breached thresholds
- **Risk Analysis**: AI-generated risk score and explanation
- **Evidence**: Specific users and values causing violations
- **Recommendations**: Actionable remediation steps

#### Investigation Workflow
1. **Acknowledge Alert**: Mark as being investigated
2. **Review Evidence**: Examine specific user access records
3. **Assess Impact**: Determine business risk level
4. **Plan Remediation**: Create action plan with timelines
5. **Implement Changes**: Update user access as needed
6. **Document Resolution**: Record actions taken

## Advanced Features

### 1. AI-Powered Risk Analysis

The system uses OpenAI GPT-4 to provide:
- **Risk Scoring**: 0-100 scale with confidence levels
- **Contextual Analysis**: Understanding of business impact
- **Contributing Factors**: Identification of root causes
- **Recommendations**: Specific, actionable remediation steps

#### Example AI Analysis
```
Risk Score: 85/100 (Confidence: 92%)

Key Risk Factors:
• High concentration of orphaned accounts (12 users)
• Elevated privileged access without proper review
• Historical pattern of access violations

Business Impact:
- Potential unauthorized access to sensitive data
- Compliance violations (SOX, GDPR)
- Increased audit risk

Recommended Actions:
1. Immediate review of all orphaned accounts
2. Implement manager assignment workflow
3. Schedule quarterly access reviews
4. Consider automated access provisioning
```

### 2. Graceful Degradation

If AI services are unavailable, the system:
- **Falls back** to template-based risk scoring
- **Continues processing** without interruption
- **Logs degradation events** for monitoring
- **Restores AI analysis** when services recover

### 3. Data Encryption

All sensitive data is encrypted at rest:
- **Algorithm**: AES-256-GCM
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **Key Rotation**: Automatic with re-encryption
- **Audit Trail**: All key changes logged

## Troubleshooting

### 1. Common Issues

#### Files Not Processing
**Symptoms**: CSV files in `data/incoming/` not being processed

**Solutions**:
```bash
# Check file permissions
ls -la data/incoming/

# Verify file format
head -5 data/incoming/your_file.csv

# Check system logs
docker-compose logs uam-compliance | grep "CSV parsing"
```

#### Missing Alerts
**Symptoms**: No alerts generated despite violations

**Solutions**:
```bash
# Check threshold configuration
cat config/thresholds.yaml

# Verify notification settings
cat config/notifications.yaml

# Test Slack integration
curl -X POST "https://slack.com/api/auth.test" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN"
```

#### Performance Issues
**Symptoms**: Slow processing, high memory usage

**Solutions**:
```bash
# Monitor resource usage
docker stats uam-compliance

# Check dataset size
du -sh data/incoming/

# Review performance logs
docker-compose logs uam-compliance | grep "performance"
```

### 2. Error Messages

#### Configuration Errors
```
ERROR: Missing required configuration: OPENAI_API_KEY
```
**Solution**: Add the missing environment variable to `.env`

#### Data Validation Errors
```
ERROR: Invalid CSV format: missing required column 'user_id'
```
**Solution**: Ensure CSV files have all required columns

#### Integration Errors
```
ERROR: Slack API failed: invalid_auth
```
**Solution**: Verify Slack bot token is valid and has required permissions

### 3. Getting Help

#### System Logs
```bash
# Full system logs
docker-compose logs uam-compliance

# Error-only logs
docker-compose logs uam-compliance | grep ERROR

# Recent logs (last hour)
docker-compose logs uam-compliance --since=1h
```

#### Support Information
When reporting issues, include:
- System version (`docker-compose exec uam-compliance python --version`)
- Configuration files (sanitized)
- Sample data (sanitized)
- Error logs
- Steps to reproduce

## Best Practices

### 1. Data Management
- **Regular Cleanup**: Archive processed files monthly
- **Backup Strategy**: Daily backups of configuration and data
- **Validation**: Test CSV files before production deployment
- **Version Control**: Track configuration changes in Git

### 2. Security
- **Key Rotation**: Rotate encryption keys quarterly
- **Access Control**: Limit access to system configuration
- **Audit Review**: Regular review of audit logs
- **Network Security**: Use VPN for remote access

### 3. Performance
- **File Organization**: Keep datasets under 100K records per file
- **Processing Schedule**: Run during off-peak hours
- **Resource Monitoring**: Monitor memory and CPU usage
- **Threshold Tuning**: Adjust based on false positive analysis

### 4. Compliance
- **Documentation**: Maintain compliance procedure documentation
- **Training**: Regular training for compliance teams
- **Review Process**: Monthly review of alert effectiveness
- **Reporting**: Quarterly compliance reports to management

## Integration Guide

### 1. SIEM Integration
Forward audit logs to your SIEM system:

```python
# Example: Send to Splunk
import requests

def forward_to_siem(log_entry):
    response = requests.post(
        'https://splunk.company.com:8088/services/collector',
        json={'event': log_entry},
        headers={'Authorization': f'Splunk {SPLUNK_TOKEN}'}
    )
    return response.status_code == 200
```

### 2. Identity Provider Integration
Connect with Active Directory or LDAP:

```python
# Example: LDAP user validation
import ldap

def validate_user_with_ad(user_id):
    conn = ldap.initialize('ldap://company.com')
    conn.simple_bind_s(LDAP_USER, LDAP_PASSWORD)
    
    result = conn.search_s(
        'ou=users,dc=company,dc=com',
        ldap.SCOPE_SUBTREE,
        f'(sAMAccountName={user_id})'
    )
    
    return len(result) > 0
```

### 3. Dashboard Integration
Create custom dashboards using the audit data:

```python
# Example: Power BI data source
import pandas as pd

def get_compliance_metrics():
    # Load from encrypted storage
    storage = EncryptedStorage('/data/uam')
    kpis = storage.load_kpis()
    
    # Convert to DataFrame
    df = pd.DataFrame([kpi.model_dump() for kpi in kpis])
    return df
```

---

For additional support or questions, contact the compliance team or refer to the technical documentation.