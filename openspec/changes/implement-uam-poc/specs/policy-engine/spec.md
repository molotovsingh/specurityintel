# Policy Rule Engine Capability

## ADDED Requirements

### Requirement: Threshold-Based Detection
The system SHALL detect policy violations based on configurable thresholds.

#### Scenario: Single KPI threshold evaluation
- **WHEN** evaluating KPI against threshold
- **THEN** the system compares KPI value to configured threshold
- **AND** triggers violation if threshold exceeded
- **AND** includes threshold value and actual value in violation details

#### Scenario: Multi-level thresholds
- **WHEN** threshold configuration includes multiple severity levels (LOW/MEDIUM/HIGH/CRITICAL)
- **THEN** the system evaluates all configured thresholds
- **AND** selects highest severity level triggered
- **AND** logs all relevant thresholds in violation context

#### Scenario: Threshold override per application
- **WHEN** application-specific threshold is configured
- **THEN** the system uses application threshold instead of global default
- **AND** logs which threshold type was applied

### Requirement: Custom Banking Compliance Rules
The system SHALL support custom rule definitions for banking policies.

#### Scenario: Rule definition format
- **WHEN** custom rule is defined
- **THEN** it includes:
  - Rule ID (unique identifier)
  - Description (human-readable)
  - Evaluation logic (Python expression or LangChain chain)
  - Severity level
  - Remediation guidance
- **AND** rules are validated on load

#### Scenario: Rule evaluation
- **WHEN** custom rule is evaluated
- **THEN** the system provides rule with:
  - Current KPI values
  - Historical baseline
  - Application metadata
- **AND** executes rule logic safely (sandboxed)
- **AND** captures rule evaluation result (pass/fail/error)

#### Scenario: Failed rule evaluation
- **WHEN** rule evaluation throws error
- **THEN** the system logs error with rule ID
- **AND** does not trigger violation (fail-safe)
- **AND** alerts operations team about rule failure

### Requirement: Segregation of Duties (SoD) Rules
The system SHALL enforce Segregation of Duties policies.

#### Scenario: Conflicting permissions detection
- **WHEN** evaluating SoD rules
- **THEN** the system checks for users with conflicting permission combinations
- **AND** flags violations where user has both permission A and permission B (configured conflicts)
- **AND** categorizes as CRITICAL severity

#### Scenario: SoD rule configuration
- **WHEN** configuring SoD rules
- **THEN** the system supports:
  - Permission pair conflicts (e.g., "approve_payment" + "initiate_payment")
  - Role-based conflicts (e.g., "auditor" + "admin")
  - Application-specific SoD rules
- **AND** validates rule consistency on load

#### Scenario: Cross-application SoD
- **WHEN** user has access to multiple applications
- **THEN** the system checks SoD rules across all user's applications
- **AND** flags cross-application conflicts (e.g., access to both trading system and settlement system)

### Requirement: Severity Classification
The system SHALL classify violations by severity level.

#### Scenario: Automatic severity assignment
- **WHEN** violation is detected
- **THEN** the system assigns severity based on:
  - Rule configuration (if specified)
  - Threshold level breached (WARNING vs CRITICAL)
  - Risk amplification factors (privileged account = higher severity)
- **AND** uses hierarchy: CRITICAL > HIGH > MEDIUM > LOW

#### Scenario: Severity escalation rules
- **WHEN** multiple violations occur for same application
- **THEN** the system may escalate severity if configured
- **AND** logs escalation reason (e.g., "3+ MEDIUM violations → HIGH")

#### Scenario: Severity filtering
- **WHEN** generating violations list
- **THEN** the system supports filtering by minimum severity
- **AND** suppresses lower-severity violations if configured

### Requirement: Violation Deduplication
The system SHALL prevent duplicate violation alerts.

#### Scenario: Same violation detection
- **WHEN** violation is detected
- **THEN** the system checks for recent similar violations (same application + rule + 24-hour window)
- **AND** marks as duplicate if found
- **AND** updates existing violation with latest data instead of creating new

#### Scenario: Violation state tracking
- **WHEN** tracking violations
- **THEN** the system maintains violation state:
  - NEW (first occurrence)
  - RECURRING (seen before, still present)
  - RESOLVED (previously detected, now absent)
- **AND** only alerts on NEW and state changes

### Requirement: Evidence Collection
The system SHALL collect evidence for each violation.

#### Scenario: Violation evidence
- **WHEN** violation is detected
- **THEN** the system collects:
  - Specific data points triggering violation
  - Threshold or rule configuration
  - Historical comparison data
  - Affected users/accounts (anonymized IDs)
  - Timestamp of detection
- **AND** stores evidence with violation record

#### Scenario: Audit trail linkage
- **WHEN** violation is created
- **THEN** the system links to:
  - Source data ingestion event
  - KPI computation event
  - AI analysis event
- **AND** enables full audit trail reconstruction

### Requirement: Remediation Recommendations
The system SHALL provide actionable remediation guidance.

#### Scenario: Template-based recommendations
- **WHEN** violation is detected
- **THEN** the system provides remediation steps from rule template
- **AND** fills template with specific values (e.g., "Disable 8 privileged accounts: [list]")

#### Scenario: AI-generated recommendations
- **WHEN** GPT-4 analysis is available
- **THEN** the system includes AI-generated remediation recommendations
- **AND** combines with template recommendations
- **AND** prioritizes recommendations by impact

### Requirement: Policy Rule Configuration
The system SHALL support flexible policy rule configuration.

#### Scenario: YAML rule configuration
- **WHEN** loading policy rules
- **THEN** the system reads YAML configuration file
- **AND** validates rule syntax
- **AND** supports hot-reload on configuration file change

#### Scenario: Configuration schema validation
- **WHEN** validating rule configuration
- **THEN** the system checks:
  - Required fields present (rule_id, description, severity)
  - Valid severity values (CRITICAL/HIGH/MEDIUM/LOW)
  - Valid threshold data types
  - No duplicate rule IDs
- **AND** fails startup on invalid configuration with clear error

### Requirement: Performance Optimization
The system SHALL complete policy evaluation within 2 minutes.

#### Scenario: Parallel rule evaluation
- **WHEN** evaluating multiple rules
- **THEN** the system processes independent rules in parallel
- **AND** uses thread pool for concurrent execution
- **AND** collects results asynchronously

#### Scenario: Early termination
- **WHEN** evaluating rules with priorities
- **THEN** the system may terminate on first CRITICAL violation if configured
- **AND** logs decision to skip remaining rules

### Requirement: Error Handling
The system SHALL handle rule evaluation errors gracefully.

#### Scenario: Rule execution timeout
- **WHEN** rule evaluation exceeds timeout (10 seconds)
- **THEN** the system terminates rule execution
- **AND** logs timeout with rule ID
- **AND** does not trigger violation (fail-safe)

#### Scenario: Invalid rule logic
- **WHEN** rule contains syntax error or invalid logic
- **THEN** the system detects error during validation
- **AND** prevents system startup
- **AND** logs specific syntax error with line number

### Requirement: Audit Logging
The system SHALL log all policy evaluation events.

#### Scenario: Evaluation success logging
- **WHEN** policy evaluation completes
- **THEN** the system logs:
  - Timestamp
  - Total rules evaluated
  - Violations detected (count by severity)
  - Evaluation duration
  - Applications processed

#### Scenario: Violation logging
- **WHEN** violation is detected
- **THEN** the system logs:
  - Violation ID (unique)
  - Rule ID
  - Application ID
  - Severity
  - KPI values
  - Threshold breached
  - Evidence summary
