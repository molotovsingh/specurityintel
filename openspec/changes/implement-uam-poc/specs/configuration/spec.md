# Configuration Management Capability

## ADDED Requirements

### Requirement: YAML Configuration Support
The system SHALL support YAML format for all configuration files.

#### Scenario: YAML parsing
- **WHEN** loading configuration
- **THEN** the system parses YAML files using safe loader (no code execution)
- **AND** validates YAML syntax
- **AND** reports line number for syntax errors

#### Scenario: Environment variable substitution
- **WHEN** YAML contains environment variable references (${VAR_NAME})
- **THEN** the system substitutes with environment variable values
- **AND** fails with clear error if variable not defined
- **AND** supports default values (${VAR_NAME:-default})

### Requirement: JSON Configuration Support
The system SHALL support JSON format as alternative to YAML.

#### Scenario: JSON parsing
- **WHEN** configuration file has .json extension
- **THEN** the system parses as JSON
- **AND** validates JSON syntax
- **AND** reports parsing errors with context

#### Scenario: Format auto-detection
- **WHEN** configuration file extension is ambiguous
- **THEN** the system attempts JSON parsing first, then YAML
- **AND** logs which format was successfully parsed

### Requirement: Alert Threshold Configuration
The system SHALL support configurable alert thresholds for each KPI.

#### Scenario: Per-KPI threshold configuration
- **WHEN** defining thresholds
- **THEN** the system supports structure:
```yaml
alert_thresholds:
  orphan_accounts:
    low: 1
    medium: 3
    high: 5
    critical: 10
  privileged_accounts:
    medium: 10
    high: 20
    critical: 30
  failed_access:
    medium: 50
    high: 100
    critical: 200
```
- **AND** validates threshold values are numeric
- **AND** validates low < medium < high < critical (when multiple levels defined)
- **AND** maps threshold levels directly to alert severity (LOW/MEDIUM/HIGH/CRITICAL)

#### Scenario: Application-specific thresholds
- **WHEN** configuring application overrides
- **THEN** the system supports per-application thresholds:
```yaml
application_thresholds:
  APP-1234:
    orphan_accounts:
      medium: 1  # Stricter for critical apps
      high: 2
      critical: 5
```
- **AND** application threshold overrides global threshold

#### Scenario: Percentage-based thresholds
- **WHEN** threshold is percentage increase
- **THEN** the system supports syntax:
```yaml
  orphan_accounts:
    low_pct: 20  # 20% increase
    medium_pct: 50  # 50% increase
    high_pct: 100  # 100% increase
    critical_pct: 200  # 200% increase
```
- **AND** calculates threshold dynamically from baseline

### Requirement: Notification Settings Configuration
The system SHALL support configurable notification channels and recipients.

#### Scenario: Slack configuration
- **WHEN** configuring Slack notifications
- **THEN** the system reads:
```yaml
notification_settings:
  slack:
    enabled: true
    bot_token: ${SLACK_BOT_TOKEN}
    channels:
      critical: "#security-critical"
      high: "#security-critical"
      medium: "#compliance-alerts"
      low: "#compliance-alerts"
```
- **AND** validates token format (xoxb-*)
- **AND** validates channel names start with #

#### Scenario: Email configuration
- **WHEN** configuring email notifications
- **THEN** the system reads:
```yaml
  email:
    enabled: true
    smtp_host: ${SMTP_HOST}
    smtp_port: 587
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from_address: "uam-compliance@bank.com"
    compliance_officers:
      - officer1@bank.com
      - officer2@bank.com
```
- **AND** validates email address format
- **AND** validates SMTP port range (1-65535)

#### Scenario: Digest mode configuration
- **WHEN** configuring digest settings
- **THEN** the system reads:
```yaml
  email:
    digest_mode:
      enabled: true
      schedule: "09:00"  # Daily at 9 AM
      min_severity: MEDIUM  # Only batch MEDIUM and below
```
- **AND** validates schedule format (HH:MM)

### Requirement: AI Configuration
The system SHALL support configurable AI analysis settings.

#### Scenario: AI model configuration
- **WHEN** configuring AI settings
- **THEN** the system reads:
```yaml
ai_settings:
  model: "gpt-4-turbo"  # or "gpt-4"
  max_tokens:
    gpt-4: 8000
    gpt-4-turbo: 128000
  api_timeout: 30  # seconds
  cost_limit_daily: 50  # USD
```
- **AND** validates model name is supported
- **AND** validates max_tokens per model

#### Scenario: Token limit validation
- **WHEN** validating AI configuration
- **THEN** the system checks max_tokens value is positive integer
- **AND** warns if exceeds model's actual context window
- **AND** uses model-specific default if not configured

### Requirement: Application Ownership Mapping
The system SHALL support configurable application ownership for routing.

#### Scenario: Owner mapping configuration
- **WHEN** configuring application owners
- **THEN** the system reads:
```yaml
application_owners:
  APP-1234:
    team: "Core Banking"
    email: corebanking-team@bank.com
    slack_channel: "#team-corebanking"
  APP-5678:
    team: "Trading Systems"
    email: trading-team@bank.com
```
- **AND** validates email format
- **AND** validates Slack channel format

### Requirement: Policy Rule Configuration
The system SHALL support configurable policy rules.

#### Scenario: Custom rule definition
- **WHEN** defining custom policy rules
- **THEN** the system reads:
```yaml
policy_rules:
  - rule_id: "orphan-cleanup-30days"
    description: "Orphan accounts must be cleaned up within 30 days"
    severity: CRITICAL
    type: threshold
    kpi: orphan_accounts
    threshold:
      critical: 5
    remediation: |
      1. Disable all orphan accounts immediately
      2. Investigate offboarding process failure
      3. Update offboarding automation
```
- **AND** validates rule_id uniqueness
- **AND** validates severity enum (CRITICAL/HIGH/MEDIUM/LOW)

#### Scenario: SoD rule definition
- **WHEN** defining Segregation of Duties rules
- **THEN** the system reads:
```yaml
sod_rules:
  - rule_id: "sod-payment-approval"
    description: "Users cannot both initiate and approve payments"
    severity: CRITICAL
    conflicts:
      - ["PAYMENT_INITIATE", "PAYMENT_APPROVE"]
      - ["PAYMENT_INITIATE", "ADMIN"]
```
- **AND** validates conflicts structure (array of pairs)

### Requirement: Configuration Validation
The system SHALL validate all configuration on load.

#### Scenario: Schema validation
- **WHEN** loading configuration
- **THEN** the system validates against Pydantic schema
- **AND** checks required fields present
- **AND** validates field data types
- **AND** fails fast on validation error with specific message

#### Scenario: Cross-field validation
- **WHEN** validating configuration
- **THEN** the system checks:
  - Warning thresholds < critical thresholds
  - Referenced application IDs exist (if master list available)
  - Email addresses well-formed
  - No duplicate rule IDs
- **AND** reports all validation errors (not just first)

#### Scenario: Startup validation failure
- **WHEN** configuration validation fails
- **THEN** the system prevents startup
- **AND** logs all validation errors clearly
- **AND** exits with error code 1

### Requirement: Hot-Reload Support
The system SHALL support hot-reloading threshold configuration without restart.

#### Scenario: File watch for changes
- **WHEN** system is running
- **THEN** it watches threshold configuration file for modifications
- **AND** detects changes within 10 seconds
- **AND** logs reload trigger event

#### Scenario: Reload execution
- **WHEN** configuration file changes
- **THEN** the system validates new configuration
- **AND** applies new thresholds if valid
- **AND** logs successful reload with timestamp
- **AND** keeps old configuration if validation fails

#### Scenario: Reload failure handling
- **WHEN** hot-reload validation fails
- **THEN** the system logs validation errors
- **AND** continues using previous valid configuration
- **AND** alerts operations team of failed reload

### Requirement: Configuration File Locations
The system SHALL support configurable paths for configuration files.

#### Scenario: Default configuration paths
- **WHEN** no custom paths specified
- **THEN** the system looks for configuration in:
  - /config/thresholds.yaml
  - /config/notifications.yaml
  - /config/policy_rules.yaml
  - /config/application_owners.yaml
- **AND** falls back to bundled defaults if not found

#### Scenario: Custom configuration paths
- **WHEN** custom paths specified via environment variables
- **THEN** the system reads from:
  - CONFIG_THRESHOLDS_PATH
  - CONFIG_NOTIFICATIONS_PATH
  - CONFIG_POLICY_RULES_PATH
  - CONFIG_APP_OWNERS_PATH
- **AND** validates paths exist and are readable

### Requirement: Configuration Examples
The system SHALL provide example configuration files.

#### Scenario: Example file generation
- **WHEN** system starts for first time
- **THEN** it generates example configuration files in /config/examples/
- **AND** includes comprehensive comments explaining each field
- **AND** provides realistic values for POC

#### Scenario: Documentation references
- **WHEN** validation error occurs
- **THEN** error message references relevant example file
- **AND** suggests correction based on schema

### Requirement: Secrets Management
The system SHALL handle sensitive configuration securely.

#### Scenario: Environment variable secrets
- **WHEN** loading secrets (API keys, passwords)
- **THEN** the system reads from environment variables only
- **AND** never logs secret values
- **AND** redacts secrets in error messages

#### Scenario: Secret validation
- **WHEN** validating secret configuration
- **THEN** the system checks secrets are non-empty
- **AND** validates format where applicable (e.g., token prefix)
- **AND** does not validate actual credentials (defer to runtime)

### Requirement: Configuration Versioning
The system SHALL track configuration version for audit trail.

#### Scenario: Version tagging
- **WHEN** configuration is loaded
- **THEN** the system computes hash of configuration content
- **AND** logs configuration version (hash) with timestamp
- **AND** includes version in audit events

#### Scenario: Version comparison
- **WHEN** configuration changes
- **THEN** the system compares new vs old version hash
- **AND** logs which sections changed (thresholds/notifications/rules)

### Requirement: Error Handling
The system SHALL provide clear error messages for configuration issues.

#### Scenario: Missing required field
- **WHEN** required field is missing
- **THEN** error message specifies:
  - Field name
  - Expected location (YAML path)
  - Example value
- **AND** references documentation

#### Scenario: Invalid field value
- **WHEN** field value is invalid
- **THEN** error message specifies:
  - Field name
  - Actual value
  - Expected format/type
  - Validation rule violated

### Requirement: Audit Logging
The system SHALL log all configuration events.

#### Scenario: Configuration load logging
- **WHEN** configuration is loaded
- **THEN** the system logs:
  - Timestamp
  - Configuration file paths
  - Configuration version (hash)
  - Validation success/failure
  - Load duration

#### Scenario: Hot-reload logging
- **WHEN** configuration is hot-reloaded
- **THEN** the system logs:
  - Timestamp
  - Changed sections
  - Old vs new version hash
  - Reload success/failure
