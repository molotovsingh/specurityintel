# Interfaces Capability

## ADDED Requirements

### Requirement: Data Transfer Objects (DTOs)
The system SHALL define Pydantic models for all domain objects to ensure type safety and validation.

#### Scenario: Severity enum definition
- **WHEN** defining severity levels
- **THEN** the system provides Severity enum with values: LOW, MEDIUM, HIGH, CRITICAL
- **AND** enum is used consistently across all modules
- **AND** enum supports string serialization for JSON/YAML

#### Scenario: KPIRecord DTO validation
- **WHEN** KPIRecord DTO is created
- **THEN** the system validates required fields (app_id, kpi_name, value, computed_at)
- **AND** rejects invalid data types with clear error messages
- **AND** provides JSON serialization for storage and events

#### Scenario: RiskAnalysisResult DTO
- **WHEN** AI analysis produces results
- **THEN** RiskAnalysisResult DTO captures: app_id, kpi_name, risk_score (0-100), confidence (0-100), explanation, factors dictionary
- **AND** validates risk_score and confidence are within 0-100 range
- **AND** ensures explanation is non-empty string

#### Scenario: Violation DTO with state
- **WHEN** policy violation is detected
- **THEN** Violation DTO captures: violation_id, app_id, rule_id, severity, kpi_values, threshold_breached, evidence, detected_at
- **AND** includes state field (NEW/RECURRING/RESOLVED)
- **AND** validates state transitions

#### Scenario: Alert DTO for dispatch
- **WHEN** alert is generated
- **THEN** Alert DTO captures: alert_id, app_id, severity, risk_score, violation_ids list, title, description, recommendations list, created_at, persona
- **AND** validates persona is either compliance_officer or app_owner
- **AND** ensures recommendations list has 3-5 items

### Requirement: Port Interfaces
The system SHALL define port interfaces for all external dependencies to enable testability and flexibility.

#### Scenario: SlackSender port definition
- **WHEN** defining Slack integration interface
- **THEN** SlackSender port provides send(alert: Alert) -> DeliveryResult method
- **AND** DeliveryResult includes success boolean, retries count, optional error message
- **AND** port is independent of Slack SDK implementation details

#### Scenario: EmailSender port definition
- **WHEN** defining email integration interface
- **THEN** EmailSender port provides send(alert: Alert) -> DeliveryResult method
- **AND** supports both individual and digest modes
- **AND** port is independent of SMTP implementation details

#### Scenario: OpenAIClient port definition
- **WHEN** defining AI integration interface
- **THEN** OpenAIClient port provides analyze(prompt: Prompt) -> AIResponse method
- **AND** Prompt DTO includes text, max_tokens, model parameters
- **AND** AIResponse includes generated_text, token_count, cost_estimate
- **AND** port is independent of LangChain/OpenAI SDK details

#### Scenario: Storage port definition
- **WHEN** defining storage interface
- **THEN** Storage port provides methods: persist_kpi, persist_violation, persist_alert, query_* methods
- **AND** port supports both file-based (JSON Lines) and database (Postgres) implementations
- **AND** query methods return DTOs, not raw database rows

#### Scenario: AuditLogger port definition
- **WHEN** defining audit logging interface
- **THEN** AuditLogger port provides log(event: AuditEvent) method
- **AND** AuditEvent DTO includes event_type, timestamp, details dictionary
- **AND** port is independent of logging library (structlog) details

#### Scenario: Clock port definition
- **WHEN** defining time source interface
- **THEN** Clock port provides now() -> datetime method
- **AND** port enables deterministic time in tests (inject fixed clock)
- **AND** production uses system clock, tests use mock clock

### Requirement: Port Adapter Pattern
The system SHALL implement adapters for each port to decouple core logic from external dependencies.

#### Scenario: SlackAdapter implementation
- **WHEN** implementing SlackSender port
- **THEN** SlackAdapter uses slack-sdk library
- **AND** adapter handles authentication, retry logic, rate limiting
- **AND** adapter is injected into alerting module via dependency injection

#### Scenario: Adapter swapping for tests
- **WHEN** running unit tests
- **THEN** MockSlackAdapter replaces SlackAdapter
- **AND** tests verify alert formatting without making real Slack API calls
- **AND** mock adapter records calls for assertion

#### Scenario: Multiple adapter implementations
- **WHEN** Storage port is implemented
- **THEN** JsonlStorage adapter writes to JSON Lines files
- **AND** PostgresStorage adapter writes to Postgres database
- **AND** both adapters satisfy same Storage port interface
- **AND** configuration selects which adapter to use

### Requirement: DTO Validation
The system SHALL validate all DTOs on construction and deserialization.

#### Scenario: Invalid field type rejection
- **WHEN** DTO is constructed with wrong type (e.g., string for numeric field)
- **THEN** Pydantic raises ValidationError with specific field name
- **AND** error message includes expected type and actual value
- **AND** system logs validation error before rejecting

#### Scenario: Missing required field rejection
- **WHEN** DTO is constructed without required field
- **THEN** Pydantic raises ValidationError listing missing fields
- **AND** system does not allow partial DTOs in module boundaries

#### Scenario: Range validation
- **WHEN** risk_score or confidence is outside 0-100 range
- **THEN** Pydantic raises ValidationError
- **AND** error specifies valid range

#### Scenario: Enum validation
- **WHEN** severity value is not in Severity enum
- **THEN** Pydantic raises ValidationError
- **AND** error lists valid severity values

### Requirement: DTO Serialization
The system SHALL support JSON serialization for all DTOs.

#### Scenario: DTO to JSON
- **WHEN** DTO.json() is called
- **THEN** system returns valid JSON string
- **AND** datetime fields are ISO 8601 formatted
- **AND** enum fields are string values

#### Scenario: JSON to DTO
- **WHEN** DTO.parse_raw(json_str) is called
- **THEN** system constructs DTO from JSON
- **AND** validates all fields during deserialization
- **AND** raises ValidationError if JSON is invalid

#### Scenario: DTO to dict
- **WHEN** DTO.dict() is called
- **THEN** system returns Python dictionary
- **AND** nested DTOs are converted to nested dicts
- **AND** useful for logging and debugging

### Requirement: DTO Versioning
The system SHALL support backward-compatible evolution of DTOs.

#### Scenario: Optional field addition
- **WHEN** new optional field is added to existing DTO
- **THEN** old serialized data can still be deserialized
- **AND** new field has default value
- **AND** system logs schema version in metadata

#### Scenario: Field deprecation
- **WHEN** field is deprecated but not removed
- **THEN** DTO still accepts old field for deserialization
- **AND** system logs deprecation warning
- **AND** DTO does not include deprecated field in new serializations

### Requirement: Error Definitions
The system SHALL define custom exceptions for domain errors.

#### Scenario: Domain error hierarchy
- **WHEN** defining custom exceptions
- **THEN** system provides base DomainError exception
- **AND** specific errors inherit from DomainError: ValidationError, ConfigurationError, IntegrationError, ProcessingError
- **AND** each error includes error_code, message, context dictionary

#### Scenario: Error serialization
- **WHEN** error needs to be logged or returned in API
- **THEN** error provides to_dict() method
- **AND** includes error_code, message, timestamp, context
- **AND** does not expose sensitive information (credentials, PII)

### Requirement: Type Hints
The system SHALL use Python type hints throughout interfaces module.

#### Scenario: Port method signatures
- **WHEN** defining port interfaces
- **THEN** all methods have complete type hints (parameters and return types)
- **AND** use typing module for complex types (List, Dict, Optional)
- **AND** mypy type checking passes without errors

#### Scenario: DTO field types
- **WHEN** defining DTO fields
- **THEN** all fields have explicit type annotations
- **AND** optional fields use Optional[T] type
- **AND** Pydantic uses type hints for validation

### Requirement: Dependency Injection
The system SHALL support dependency injection for ports.

#### Scenario: Module initialization with ports
- **WHEN** module (e.g., alerting) is initialized
- **THEN** ports are passed as constructor parameters (SlackSender, EmailSender, Storage)
- **AND** module does not instantiate adapters directly
- **AND** composition root wires concrete adapters

#### Scenario: Test setup with mocks
- **WHEN** setting up unit tests
- **THEN** test passes mock implementations of ports to module
- **AND** module behavior is tested in isolation
- **AND** no external services are called

### Requirement: Documentation
The system SHALL document all DTOs and ports with docstrings.

#### Scenario: DTO docstring
- **WHEN** DTO is defined
- **THEN** class has docstring describing purpose
- **AND** each field has description comment
- **AND** examples provided in docstring

#### Scenario: Port docstring
- **WHEN** port interface is defined
- **THEN** class has docstring describing responsibility
- **AND** each method has docstring with parameters, return value, and exceptions
- **AND** usage example provided

### Requirement: Immutability Preference
The system SHALL prefer immutable DTOs for value objects where appropriate.

#### Scenario: Frozen DTO
- **WHEN** DTO represents immutable domain object (e.g., KPIRecord)
- **THEN** DTO is defined with frozen=True in Pydantic config
- **AND** attempts to modify fields after construction raise error
- **AND** DTO can be safely shared across modules

#### Scenario: Mutable DTO for state
- **WHEN** DTO represents stateful object (e.g., Violation with state transitions)
- **THEN** DTO allows field modification
- **AND** state transitions are validated via methods
- **AND** mutation is logged for audit trail
