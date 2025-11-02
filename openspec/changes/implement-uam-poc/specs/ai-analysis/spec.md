# AI Analysis Capability

## ADDED Requirements

### Requirement: Anomaly Detection
The system SHALL detect anomalies in KPI values using statistical and AI-powered methods.

#### Scenario: Statistical anomaly detection
- **WHEN** KPI values are analyzed
- **THEN** the system calculates standard deviation from baseline
- **AND** flags values exceeding 2 standard deviations as anomalies
- **AND** uses rolling window for baseline calculation (7-day minimum)

#### Scenario: Week-on-week spike detection
- **WHEN** comparing current vs previous week KPI values
- **THEN** the system identifies spikes >50% increase
- **AND** flags spikes with percentage change
- **AND** provides previous week baseline for context

#### Scenario: Cross-application pattern detection
- **WHEN** analyzing KPIs across applications
- **THEN** the system identifies patterns affecting multiple apps simultaneously
- **AND** detects correlated anomalies (e.g., 5+ apps with similar spike pattern)
- **AND** flags systemic issues vs isolated incidents

### Requirement: Multi-Factor Risk Scoring
The system SHALL compute risk scores (0-100) using multiple factors.

#### Scenario: Base risk score calculation
- **WHEN** computing risk score
- **THEN** the system weights each KPI by severity
- **AND** applies multiplicative factors for risk amplification
- **AND** normalizes to 0-100 scale

#### Scenario: Risk amplification factors
- **WHEN** multiple high-risk conditions exist
- **THEN** the system applies amplification (e.g., privileged account + failed MFA = 1.5x multiplier)
- **AND** uses configurable amplification rules
- **AND** caps risk score at 100

#### Scenario: Risk score breakdown
- **WHEN** risk score is computed
- **THEN** the system provides breakdown showing contribution of each factor
- **AND** identifies top 3 risk contributors
- **AND** includes factor weights in explanation

### Requirement: GPT-4 Integration via OpenAIClient Port
The system SHALL use GPT-4 via OpenAIClient port for testability and abstraction.

#### Scenario: OpenAIClient port usage
- **WHEN** AI module performs analysis
- **THEN** the system calls OpenAIClient.analyze(prompt, max_tokens) port method
- **AND** does not directly import LangChain or OpenAI SDK
- **AND** port is injected via dependency injection
- **AND** enables testing with MockOpenAIClient

### Requirement: GPT-4 Analysis
The system SHALL use GPT-4 for explainable analysis.

#### Scenario: Explainability prompt generation
- **WHEN** anomaly is detected
- **THEN** the system constructs prompt with:
  - KPI values (current and baseline)
  - Detected anomaly type
  - Application context
  - Historical trend summary
- **AND** sends prompt to GPT-4 via LangChain
- **AND** requests root cause explanation and recommendations

#### Scenario: Response parsing
- **WHEN** GPT-4 returns analysis
- **THEN** the system extracts:
  - Root cause explanation
  - Impact assessment
  - Recommended actions (3-5 specific steps)
- **AND** validates response completeness
- **AND** falls back to template if parsing fails

#### Scenario: Token management
- **WHEN** calling GPT-4 API
- **THEN** the system counts tokens before sending
- **AND** truncates prompts exceeding configured token limit (model-specific: GPT-4: 8k, GPT-4-turbo: 128k)
- **AND** logs token usage and estimated cost

### Requirement: Graceful Degradation
The system SHALL continue operating when AI services fail.

#### Scenario: GPT-4 API timeout
- **WHEN** GPT-4 API call times out after 30 seconds
- **THEN** the system retries up to 3 times with exponential backoff
- **AND** falls back to rule-based explanation templates
- **AND** logs degraded mode event

#### Scenario: GPT-4 API error
- **WHEN** GPT-4 API returns error (rate limit, service unavailable)
- **THEN** the system uses cached similar analysis if available
- **AND** falls back to template-based explanations
- **AND** alerts operations team if degraded for >1 hour

#### Scenario: Template-based explanations
- **WHEN** operating in degraded mode
- **THEN** the system generates explanations using predefined templates
- **AND** fills templates with computed KPI values
- **AND** includes disclaimer about simplified analysis

### Requirement: Trend Analysis
The system SHALL analyze KPI trends over time.

#### Scenario: Week-on-week comparison
- **WHEN** analyzing trends
- **THEN** the system compares current week to previous week
- **AND** calculates percentage change for each KPI
- **AND** identifies increasing vs decreasing trends

#### Scenario: Multi-week trend detection
- **WHEN** sufficient historical data exists (>4 weeks)
- **THEN** the system identifies sustained trends (consistent direction for 3+ weeks)
- **AND** flags accelerating trends (rate of change increasing)

#### Scenario: Seasonality detection
- **WHEN** historical data spans >8 weeks
- **THEN** the system detects repeating patterns (e.g., Friday spikes)
- **AND** adjusts anomaly thresholds for known patterns

### Requirement: Context Enrichment
The system SHALL enrich analysis with contextual information.

#### Scenario: Application metadata enrichment
- **WHEN** analyzing application-level anomalies
- **THEN** the system includes application metadata:
  - Criticality level (production/test)
  - Owner team
  - User count
  - Data sensitivity classification
- **AND** weights risk score by criticality

#### Scenario: Historical incident correlation
- **WHEN** anomaly detected
- **THEN** the system checks for similar historical incidents
- **AND** includes reference to previous occurrences if found
- **AND** notes whether previous incident was false positive

### Requirement: Confidence Scoring
The system SHALL provide confidence scores for AI-generated analysis.

#### Scenario: Confidence calculation
- **WHEN** GPT-4 analysis is generated
- **THEN** the system calculates confidence based on:
  - Data completeness (100% = all required fields present)
  - Historical baseline availability
  - GPT-4 response quality indicators
- **AND** assigns confidence level (HIGH/MEDIUM/LOW)

#### Scenario: Low confidence handling
- **WHEN** confidence score is LOW (<60%)
- **THEN** the system includes confidence disclaimer in alert
- **AND** may suppress alert if configured (severity < HIGH)

### Requirement: Performance Optimization
The system SHALL complete AI analysis within 3 minutes.

#### Scenario: Batch API calls
- **WHEN** analyzing multiple applications
- **THEN** the system batches similar anomalies into single GPT-4 call
- **AND** uses GPT-4-turbo model for faster response
- **AND** processes responses concurrently

#### Scenario: Caching strategy
- **WHEN** analyzing similar anomaly patterns
- **THEN** the system checks cache for recent similar analysis
- **AND** reuses cached explanation if match found (60% similarity threshold)
- **AND** expires cache entries after 24 hours

### Requirement: Cost Management
The system SHALL monitor and control GPT-4 API costs.

#### Scenario: Cost tracking
- **WHEN** GPT-4 API is called
- **THEN** the system logs token usage and estimated cost
- **AND** aggregates daily cost totals
- **AND** alerts if daily cost exceeds threshold ($50/day for POC)

#### Scenario: Cost limit enforcement
- **WHEN** daily cost threshold is reached
- **THEN** the system switches to degraded mode (template-based)
- **AND** alerts operations team
- **AND** resumes AI analysis next day

### Requirement: Audit Logging
The system SHALL log all AI analysis events.

#### Scenario: API call logging
- **WHEN** GPT-4 API is called
- **THEN** the system logs:
  - Timestamp
  - Request ID
  - Prompt (truncated if >500 chars)
  - Token count
  - Response time
  - Success/failure status
  - Estimated cost

#### Scenario: Analysis result logging
- **WHEN** AI analysis completes
- **THEN** the system logs:
  - Application analyzed
  - Risk score computed
  - Confidence level
  - Anomalies detected
  - Recommendations generated
