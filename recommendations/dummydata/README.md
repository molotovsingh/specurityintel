# UAM Dev Dummy Data (CSV)

This folder contains a small, representative CSV dataset to develop and test the UAM Compliance Intelligence POC locally. Files are designed to exercise all KPIs and major flows (ingestion → KPI → AI → policy → alerting).

## Files
- applications.csv — Application catalog with criticality and sensitivity
- users.csv — Directory with employment status for orphan detection
- uam_access.csv — Minimal access snapshot to satisfy basic ingestion (app_id, user_id, access_level, timestamp)
- access_assignments.csv — Current access states (role, assigned_at, last_login_at)
- access_events.csv — Login successes/failures for failed-access KPIs
- access_requests.csv — Access request/grant pairs for provisioning-time KPI
- access_reviews.csv — Per-user review completion and timestamps
- user_permissions.csv — Effective permissions per user for “excessive permissions” KPI
- role_baseline.csv — Role baseline permission counts (and privileged flag)
- login_activity.csv — Last-login snapshot for dormant account detection

## Notes
- Timestamps are ISO-8601 with Z (UTC) where applicable.
- Data intentionally includes: privileged roles, orphan accounts, MFA/credential failures, pending requests, stale reviews, dormant accounts, and excessive permissions.
- Scale is small for dev; generate more rows as needed for performance tests.

## KPI Coverage Map
- Privileged accounts → access_assignments.csv (access_level/role) + role_baseline.csv(privileged)
- Failed access attempts → access_events.csv
- Provisioning time → access_requests.csv
- Orphan accounts → users.csv(terminated) + access_assignments.csv(active)
- Access review status/freshness → access_reviews.csv
- Policy violations → derived from thresholds and KPIs (not provided as input)
- Excessive permissions → user_permissions.csv vs role_baseline.csv
- Dormant accounts → login_activity.csv (or derive from access_events)

