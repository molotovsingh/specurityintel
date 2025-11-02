# KPI Computation Capability

## ADDED Requirements

### Requirement: Privileged Accounts KPI
The system SHALL calculate privileged accounts count per application.

#### Scenario: Count privileged accounts
- **WHEN** KPI computation runs
- **THEN** the system counts users with privileged access levels (admin, root, superuser)
- **AND** groups counts by application
- **AND** stores timestamp and application identifier with each KPI value

#### Scenario: Privileged role mapping
- **WHEN** determining privileged status
- **THEN** the system uses configurable role mapping (e.g., "ADMIN" → privileged)
- **AND** supports case-insensitive matching
- **AND** logs unmapped roles as warnings

### Requirement: Failed Access Attempts KPI
The system SHALL calculate failed access attempts per application.

#### Scenario: Count failed access
- **WHEN** KPI computation runs
- **THEN** the system counts access attempts with failure status
- **AND** groups counts by application
- **AND** separately tracks MFA failures vs credential failures

#### Scenario: Time window filtering
- **WHEN** calculating failed access attempts
- **THEN** the system uses configurable time window (default: 24 hours)
- **AND** filters events to specified time range
- **AND** handles timezone conversions correctly

### Requirement: Access Provisioning Time KPI
The system SHALL calculate average time to provision user access.

#### Scenario: Calculate provisioning duration
- **WHEN** KPI computation runs
- **THEN** the system calculates duration between access request and grant timestamps
- **AND** computes average provisioning time per application
- **AND** identifies outlier requests (>95th percentile)

#### Scenario: Pending requests
- **WHEN** access requests have no grant timestamp
- **THEN** the system calculates time since request
- **AND** flags requests pending >30 days as policy violations

### Requirement: Orphan Accounts KPI
The system SHALL identify orphan accounts (active after user exit).

#### Scenario: Detect orphan accounts
- **WHEN** KPI computation runs
- **THEN** the system cross-references active accounts with user employment status
- **AND** flags accounts active after user termination date
- **AND** counts orphan accounts per application

#### Scenario: Privileged orphan accounts
- **WHEN** orphan accounts are detected
- **THEN** the system separately counts privileged orphan accounts
- **AND** flags privileged orphans as critical risk

### Requirement: Periodic Access Review Status KPI
The system SHALL track access review completion status.

#### Scenario: Calculate review completion rate
- **WHEN** KPI computation runs
- **THEN** the system calculates percentage of users with completed reviews
- **AND** groups by application
- **AND** flags applications with <80% review completion

#### Scenario: Review freshness
- **WHEN** tracking reviews
- **THEN** the system checks review timestamp against policy window (e.g., quarterly)
- **AND** flags stale reviews (>90 days old) as incomplete

### Requirement: Policy Violations KPI
The system SHALL count total policy violations per application.

#### Scenario: Aggregate violations
- **WHEN** KPI computation runs
- **THEN** the system aggregates all policy violation types
- **AND** categorizes by severity (CRITICAL/HIGH/MEDIUM/LOW)
- **AND** provides violation breakdown by type

### Requirement: Excessive Permissions KPI
The system SHALL identify users with excessive permissions.

#### Scenario: Detect excessive permissions
- **WHEN** KPI computation runs
- **THEN** the system identifies users with permissions exceeding role requirements
- **AND** counts excessive permission instances per application
- **AND** calculates percentage of users with excessive permissions

#### Scenario: Role baseline comparison
- **WHEN** determining excessive permissions
- **THEN** the system compares user permissions to role baseline
- **AND** uses configurable threshold (e.g., >20% more permissions than baseline)

### Requirement: Dormant Accounts KPI
The system SHALL identify dormant accounts (no activity for extended period).

#### Scenario: Detect dormant accounts
- **WHEN** KPI computation runs
- **THEN** the system identifies accounts with no login activity for >90 days
- **AND** counts dormant accounts per application
- **AND** separately tracks privileged dormant accounts

#### Scenario: Configurable dormancy threshold
- **WHEN** detecting dormant accounts
- **THEN** the system uses configurable inactivity threshold (default: 90 days)
- **AND** supports different thresholds for privileged vs standard accounts

### Requirement: KPI Aggregation
The system SHALL aggregate computed KPIs for reporting and analysis.

#### Scenario: Per-application aggregation
- **WHEN** all KPIs are computed
- **THEN** the system creates aggregated view per application
- **AND** includes all 7 core KPIs plus additional KPIs
- **AND** timestamps aggregation with computation time

#### Scenario: Cross-application aggregation
- **WHEN** generating enterprise-level metrics
- **THEN** the system aggregates KPIs across all applications
- **AND** calculates percentiles (50th, 90th, 95th) for each KPI
- **AND** identifies top 10 applications by each KPI metric

### Requirement: KPI Storage
The system SHALL persist computed KPIs for trend analysis.

#### Scenario: Store daily KPIs
- **WHEN** KPI computation completes
- **THEN** the system stores KPI values with timestamp
- **AND** maintains historical data for trend analysis
- **AND** indexes by application and timestamp for fast retrieval

#### Scenario: Storage format
- **WHEN** persisting KPIs
- **THEN** the system uses structured format (JSON or database)
- **AND** includes metadata (computation version, data source)

### Requirement: Performance Optimization
The system SHALL compute all KPIs within 8 minutes for full dataset.

#### Scenario: Vectorized computation
- **WHEN** calculating KPIs
- **THEN** the system uses vectorized operations (NumPy/Pandas)
- **AND** avoids row-by-row iteration
- **AND** leverages parallel processing where applicable

#### Scenario: Incremental computation
- **WHEN** processing incremental data loads
- **THEN** the system recomputes only affected applications
- **AND** reuses previous KPI values for unchanged applications

### Requirement: Error Handling
The system SHALL handle KPI computation errors gracefully.

#### Scenario: Missing data fields
- **WHEN** required fields are missing from input data
- **THEN** the system skips affected KPI calculation
- **AND** logs warning with missing field details
- **AND** proceeds with other KPI computations

#### Scenario: Invalid data values
- **WHEN** data contains invalid values (negative counts, future timestamps)
- **THEN** the system logs data quality issue
- **AND** excludes invalid records from calculation
- **AND** reports affected record count

### Requirement: Audit Logging
The system SHALL log KPI computation events.

#### Scenario: Computation success logging
- **WHEN** KPI computation completes
- **THEN** the system logs structured event with:
  - Timestamp
  - KPI type
  - Application count processed
  - Computation duration
  - KPI value ranges (min/max/avg)

#### Scenario: Computation failure logging
- **WHEN** KPI computation fails
- **THEN** the system logs error details
- **AND** includes failed KPI type and application context
