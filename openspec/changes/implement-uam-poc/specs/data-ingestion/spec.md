# Data Ingestion Capability

## ADDED Requirements

### Requirement: CSV File Parsing
The system SHALL parse daily UAM CSV exports with flexible schema handling to accommodate data structure variations.

#### Scenario: Valid CSV parsing
- **WHEN** a well-formed CSV file is provided with expected columns
- **THEN** the system parses all rows and columns correctly
- **AND** data types are inferred accurately
- **AND** parsing completes within 5 minutes for 1,200 apps × 40,000 users

#### Scenario: Malformed CSV handling
- **WHEN** a CSV file contains malformed rows (missing delimiters, quote issues)
- **THEN** the system logs specific parsing errors with line numbers
- **AND** continues processing valid rows
- **AND** reports malformed row count in audit log

#### Scenario: Schema drift detection
- **WHEN** CSV column names or order change from previous ingestion
- **THEN** the system detects schema changes
- **AND** logs a warning with schema diff
- **AND** attempts best-effort parsing using column name matching

### Requirement: Data Validation
The system SHALL validate CSV data quality and enforce required fields before processing.

#### Scenario: Required field validation
- **WHEN** CSV is ingested
- **THEN** the system validates presence of required fields (app_id, user_id, access_level, timestamp)
- **AND** rejects files missing required fields with clear error message

#### Scenario: Data type validation
- **WHEN** CSV data is parsed
- **THEN** the system validates data types (numeric fields contain numbers, dates are valid)
- **AND** coerces types where possible (e.g., string "123" to integer)
- **AND** logs validation warnings for coercion attempts

#### Scenario: Data quality checks
- **WHEN** validation runs
- **THEN** the system checks for duplicate records (same app_id + user_id + timestamp)
- **AND** flags records with null values in critical fields
- **AND** reports data quality metrics in audit log

### Requirement: Incremental vs Full Load Detection
The system SHALL automatically detect whether CSV represents full or incremental dataset.

#### Scenario: Full load detection
- **WHEN** CSV row count differs significantly from previous ingestion (>20% variance)
- **THEN** the system classifies as full load
- **AND** replaces entire previous dataset
- **AND** logs full load event with row count

#### Scenario: Incremental load detection
- **WHEN** CSV row count is similar to previous ingestion (within 20% variance)
- **THEN** the system classifies as incremental load
- **AND** merges new data with existing dataset
- **AND** logs incremental load event with row count delta

#### Scenario: First ingestion
- **WHEN** no previous ingestion data exists
- **THEN** the system treats as full load
- **AND** establishes baseline dataset

### Requirement: Error Handling
The system SHALL handle CSV ingestion failures gracefully with retry logic.

#### Scenario: File not found
- **WHEN** configured CSV file path does not exist
- **THEN** the system logs critical error
- **AND** alerts operations team via configured notification channel
- **AND** retries after 30 minutes
- **AND** fails job after 3 retry attempts

#### Scenario: Permission denied
- **WHEN** application lacks read permissions for CSV file
- **THEN** the system logs permission error with file path
- **AND** alerts operations team immediately
- **AND** does not retry (requires manual intervention)

#### Scenario: Corrupted file
- **WHEN** CSV file is corrupted (invalid encoding, truncated)
- **THEN** the system logs corruption details
- **AND** attempts alternate encodings (UTF-8, UTF-16, Latin-1)
- **AND** fails gracefully if all encodings fail

### Requirement: Data Staging
The system SHALL stage validated data in memory for downstream processing.

#### Scenario: Successful staging
- **WHEN** CSV parsing and validation complete successfully
- **THEN** the system loads data into Pandas DataFrame
- **AND** applies index optimization for fast lookups
- **AND** makes DataFrame available to KPI computation engine

#### Scenario: Memory pressure handling
- **WHEN** dataset exceeds available memory threshold (80% of RAM)
- **THEN** the system switches to chunked processing
- **AND** processes CSV in batches of 100,000 rows
- **AND** aggregates results incrementally

### Requirement: Audit Logging
The system SHALL log all ingestion events to audit trail.

#### Scenario: Ingestion success logging
- **WHEN** CSV ingestion completes successfully
- **THEN** the system logs structured event with:
  - Timestamp
  - File path
  - Row count
  - Column count
  - Load type (full/incremental)
  - Processing duration
  - Validation warnings count

#### Scenario: Ingestion failure logging
- **WHEN** CSV ingestion fails
- **THEN** the system logs structured error event with:
  - Timestamp
  - File path
  - Failure reason
  - Error details (line numbers, specific errors)
  - Retry attempt number

### Requirement: Configuration Support
The system SHALL support configurable ingestion settings.

#### Scenario: CSV path configuration
- **WHEN** system starts
- **THEN** it reads CSV file path from configuration
- **AND** supports environment variable substitution
- **AND** validates path exists on startup

#### Scenario: Delimiter configuration
- **WHEN** CSV uses non-standard delimiter (tab, semicolon)
- **THEN** the system reads delimiter from configuration
- **AND** applies correct delimiter during parsing

#### Scenario: Encoding configuration
- **WHEN** CSV uses specific encoding
- **THEN** the system reads encoding from configuration
- **AND** uses configured encoding as first parsing attempt
