# Production Roadmap (Final)

Last updated: 2026-04-17

## Current State

- Requested production-ready scope is implemented.
- This roadmap now tracks post-launch operations and continuous improvement.

## Critical (post-launch ops)

- **Managed secrets rollout**  
  Move env secrets to cloud secret manager and rotate JWT/OAuth credentials regularly.  
  Estimate: 0.5 day

- **TLS/domain enforcement in target environment**  
  Ensure all public traffic is HTTPS-only with cert auto-renewal.  
  Estimate: 0.5 day

## High

- **Add integration tests to CI**  
  Include auth -> submit -> worker -> dashboard validation path.  
  Estimate: 1 day

- **Add security/dependency scanning in CI**  
  Add `pip-audit`/`npm audit` jobs with policy thresholds.  
  Estimate: 0.5 day

## Medium

- **Observability expansion**  
  Add Prometheus metrics and alerting rules for worker queue depth/failures.  
  Estimate: 0.5-1 day

- **Operational runbooks**  
  Add incident, rollback, and queue-drain procedures.  
  Estimate: 0.5 day
