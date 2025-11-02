# Alerting System Capability

## ADDED Requirements

### Requirement: Alert Generation
The system SHALL generate structured alerts from detected policy violations.

#### Scenario: Alert message formatting
- **WHEN** violation is detected
- **THEN** the system generates alert following PRD template (Section 14.2):
  - Severity indicator with emoji (🚨 CRITICAL, ⚠️ HIGH, 📊 MEDIUM, ℹ️ LOW)
  - Application name and ID
  - Risk score (0-100)
  - Issue description with violation details
  - Baseline comparison (previous week value + percentage change)
  - Impact assessment
  - Root cause explanation (from AI analysis)
  - Recommended actions (numbered list of 3-5 steps)
- **AND** formats consistently across all alert channels

#### Scenario: Alert metadata
- **WHEN** alert is created
- **THEN** the system includes metadata:
  - Alert ID (unique)
  - Timestamp
  - Violation ID(s)
  - Application ID
  - Severity
  - Risk score
  - Persona target (compliance officer / app owner)
- **AND** stores metadata for deduplication and audit

### Requirement: Slack Integration via Port
The system SHALL deliver alerts via Slack using SlackSender port for testability and flexibility.

#### Scenario: SlackSender port usage
- **WHEN** alerting module dispatches alert
- **THEN** the system calls SlackSender.send(alert: Alert) port method
- **AND** does not directly import or call slack-sdk
- **AND** port is injected via dependency injection

### Requirement: Slack Delivery
The system SHALL deliver alerts via Slack with channel-based routing.

#### Scenario: Slack channel routing
- **WHEN** dispatching Slack alert
- **THEN** the system routes by severity:
  - CRITICAL → #security-critical
  - HIGH → #security-critical
  - MEDIUM → #compliance-alerts
  - LOW → #compliance-alerts
- **AND** uses configured channel mapping from configuration

#### Scenario: Slack message formatting
- **WHEN** sending Slack alert
- **THEN** the system formats using Slack Block Kit:
  - Header block with severity and application
  - Context block with risk score
  - Section blocks for issue details
  - Divider blocks for readability
  - Footer block with timestamp and alert ID
- **AND** applies syntax highlighting for readability

#### Scenario: Slack delivery retry
- **WHEN** Slack API call fails
- **THEN** the system retries up to 3 times with exponential backoff (5s, 10s, 20s)
- **AND** logs each retry attempt
- **AND** falls back to email if all retries fail

#### Scenario: Slack rate limiting
- **WHEN** approaching Slack rate limits
- **THEN** the system queues messages
- **AND** dispatches with rate limiting compliance
- **AND** logs delayed messages

### Requirement: Email Integration via Port
The system SHALL deliver alerts via email using EmailSender port.

#### Scenario: EmailSender port usage
- **WHEN** alerting module dispatches email alert
- **THEN** the system calls EmailSender.send(alert: Alert) port method
- **AND** does not directly import or configure SMTP
- **AND** port is injected via dependency injection

### Requirement: Email Delivery
The system SHALL deliver alerts via email with HTML formatting.

#### Scenario: Email recipient routing
- **WHEN** dispatching email alert
- **THEN** the system routes to:
  - Compliance officers for CRITICAL/HIGH severity
  - Application owners for app-specific alerts (all severities)
- **AND** uses persona mapping from configuration

#### Scenario: Email HTML formatting
- **WHEN** sending email alert
- **THEN** the system generates HTML email with:
  - Branded header with severity color coding
  - Tabular format for KPI values
  - Highlighted risk score
  - Formatted action list
  - Footer with alert metadata
- **AND** includes plain-text fallback version

#### Scenario: Email digest mode
- **WHEN** digest mode is enabled for non-critical alerts
- **THEN** the system batches MEDIUM/LOW severity alerts
- **AND** sends single daily digest email
- **AND** delivers CRITICAL/HIGH alerts immediately

#### Scenario: Email delivery retry
- **WHEN** SMTP delivery fails
- **THEN** the system retries up to 5 times with exponential backoff (30s, 1m, 2m, 4m, 8m)
- **AND** logs each retry attempt
- **AND** alerts operations team if all retries fail

### Requirement: Persona-Based Routing
The system SHALL route alerts based on recipient persona.

#### Scenario: Compliance officer routing
- **WHEN** routing to compliance officers
- **THEN** the system sends:
  - All CRITICAL severity alerts
  - All HIGH severity alerts
  - Cross-application pattern alerts
  - Daily summary reports
- **AND** uses global compliance officer contact list

#### Scenario: Application owner routing
- **WHEN** routing to application owners
- **THEN** the system sends only alerts for owned applications
- **AND** filters by application ownership mapping
- **AND** respects owner's severity preference (if configured)

#### Scenario: Escalation routing
- **WHEN** CRITICAL alert is not acknowledged within 1 hour
- **THEN** the system escalates to secondary contacts
- **AND** logs escalation event

### Requirement: Severity-Based Filtering
The system SHALL filter alerts by severity to prevent fatigue.

#### Scenario: Minimum severity threshold
- **WHEN** filtering alerts for dispatch
- **THEN** the system applies minimum severity threshold from configuration
- **AND** suppresses alerts below threshold
- **AND** logs suppressed alerts for audit

#### Scenario: Persona-specific thresholds
- **WHEN** different personas have different severity preferences
- **THEN** the system applies persona-specific thresholds
- **AND** may send same violation to some personas but not others

### Requirement: Alert Deduplication
The system SHALL prevent duplicate alert deliveries.

#### Scenario: Duplicate detection
- **WHEN** alert is about to be dispatched
- **THEN** the system checks for identical alerts in last 24 hours (same app + rule + severity)
- **AND** marks as duplicate if found
- **AND** does not re-dispatch duplicate

#### Scenario: Alert state updates
- **WHEN** duplicate violation is detected
- **THEN** the system updates existing alert with:
  - Latest KPI value
  - Updated risk score
  - "Still present as of [timestamp]" note
- **AND** may re-dispatch if risk score increased significantly (>20 points)

### Requirement: Alert Timing
The system SHALL dispatch alerts within 5 minutes of detection.

#### Scenario: Immediate dispatch for critical
- **WHEN** CRITICAL severity violation is detected
- **THEN** the system dispatches alert immediately
- **AND** prioritizes delivery over other processing
- **AND** logs dispatch latency

#### Scenario: Batch dispatch for lower severity
- **WHEN** MEDIUM/LOW severity violations are detected
- **THEN** the system may batch for up to 5 minutes
- **AND** dispatches batch when size threshold reached (10 alerts) or time elapsed

### Requirement: Daily Summary Reports
The system SHALL generate daily compliance summary reports.

#### Scenario: Summary report generation
- **WHEN** daily processing completes
- **THEN** the system generates summary report including:
  - Total applications processed
  - Total violations detected (by severity)
  - Top 5 applications by risk score
  - New violations vs recurring
  - Resolved violations
  - Overall compliance health score
- **AND** delivers by 9 AM to compliance officers

#### Scenario: Summary report format
- **WHEN** formatting summary report
- **THEN** the system uses concise tabular format
- **AND** includes visualizations (text-based charts for email/Slack)
- **AND** links to individual alerts if available

### Requirement: Alert Storage via Port
The system SHALL persist all alerts using Storage port.

#### Scenario: Storage port for alerts
- **WHEN** alert is generated
- **THEN** the system calls Storage.persist_alert(alert: Alert)
- **AND** storage implementation (JSON Lines or Postgres) is injected
- **AND** alerting module does not know storage details

### Requirement: Alert Persistence
The system SHALL persist all alerts to audit trail.

#### Scenario: Alert persistence
- **WHEN** alert is generated
- **THEN** the system stores to audit trail with:
  - Alert ID
  - Timestamp
  - Violation details
  - Recipients
  - Delivery status
  - Dispatch latency
- **AND** uses append-only storage (JSON Lines)

#### Scenario: Delivery status tracking
- **WHEN** alert delivery completes
- **THEN** the system updates alert record with:
  - Delivery timestamp
  - Success/failure status
  - Retry count
  - Error details (if failed)

### Requirement: Error Handling
The system SHALL handle alert dispatch failures gracefully.

#### Scenario: Partial delivery failure
- **WHEN** Slack delivery succeeds but email fails
- **THEN** the system logs partial success
- **AND** continues retrying failed channel
- **AND** does not re-send to successful channel

#### Scenario: Total delivery failure
- **WHEN** all delivery channels fail after retries
- **THEN** the system logs critical error
- **AND** stores alert in failure queue
- **AND** attempts re-delivery on next scheduled run

#### Scenario: Channel degradation
- **WHEN** one channel consistently fails (>80% failure rate)
- **THEN** the system alerts operations team
- **AND** may disable failing channel if configured

### Requirement: Configuration Support
The system SHALL support configurable alerting settings.

#### Scenario: Channel configuration
- **WHEN** configuring alerting
- **THEN** the system reads configuration for:
  - Slack bot token and channels
  - SMTP server and credentials
  - Email recipients by persona
  - Severity-to-channel mapping
- **AND** validates configuration on startup

#### Scenario: Template customization
- **WHEN** alert templates are customized
- **THEN** the system loads custom templates from configuration directory
- **AND** falls back to default templates if custom not found
- **AND** supports Jinja2 template syntax

### Requirement: Audit Logging
The system SHALL log all alerting events.

#### Scenario: Dispatch event logging
- **WHEN** alert is dispatched
- **THEN** the system logs:
  - Alert ID
  - Timestamp
  - Channel (Slack/Email)
  - Recipients
  - Delivery latency
  - Success/failure status

#### Scenario: Suppression logging
- **WHEN** alert is suppressed (deduplication or severity filtering)
- **THEN** the system logs:
  - Suppressed alert details
  - Suppression reason
  - Original violation ID
