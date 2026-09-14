# Site Reliability Engineering (SRE), Incident Response & Resilience Curriculum

## 1. What
Site Reliability Engineering (SRE) is what happens when you treat operations as if it were a software problem. It applies software engineering principles to infrastructure and operational challenges.

## 2. Why
Modern distributed cloud systems cannot achieve 100% reliability. SRE replaces unrealistic zero-downtime fantasies with mathematically sound reliability targets, error budgets, blameless post-mortems, and structured incident management (SEV-1/SEV-2).

## 3. Architecture
```
Business Objective ---> SLI (Service Level Indicator, e.g. 99.5% success rate)
                              |
                              v
                        SLO (Service Level Objective, e.g. 99.9% over 30d)
                              |
                              +---> Error Budget (0.1% allowed failure)
                                       |
                   +-------------------+-------------------+
                   |                                       |
          Budget Healthy:                         Budget Exhausted:
     Release new product features             Freeze releases, focus on reliability
```

## 4. Internals
- **SLI / SLO Mathematics**:
  $$\text{SLI} = \frac{\text{Good Events}}{\text{Total Events}} \times 100\%$$
  $$\text{Error Budget} = 100\% - \text{SLO}$$
  For an SLO of 99.9% over a 30-day window ($43,200\text{ minutes}$), the allowable downtime error budget is $43.2\text{ minutes}$.
- **Multi-Window Multi-Burn-Rate Alerting**: Traditional threshold alerts cause false positives during short blips and page too late on slow leaks. Google SRE multi-burn-rate alerting monitors 1-hour and 6-hour windows:
  - 14.4x burn rate over 1 hour consumes 2% of budget in 1 hour $\rightarrow$ **Page on-call immediately**.
  - 6x burn rate over 6 hours consumes 5% of budget in 6 hours $\rightarrow$ **Page on-call**.
- **Incident Commander (IC) System**:
  - `Incident Commander (IC)`: Leads the call, coordinates actions, assigns roles.
  - `Operations Lead (Ops)`: Executes diagnostic commands and remediations.
  - `Communications Lead (Comms)`: Posts customer updates on status page every 15 minutes.
  - `Scribe`: Logs timestamps, hypotheses, and actions in the incident timeline.

## 5. Commands & Tools
- Incident triage commands:
  - Check error budget burn rate in Prometheus:
    `sum(rate(http_requests_total{status=~"5.."}[1h])) / sum(rate(http_requests_total[1h])) > (1 - 0.999) * 14.4`
  - Blast radius containment:
    `kubectl scale deployment/unstable-feature --replicas=0`
    `kubectl set env deployment/gateway FEATURE_FLAGS_ENABLE_NEW_CHECKOUT=false`

## 6. Hands-on Lab
- **Lab 1: Calculating Multi-Window SLO Burn Rates in PromQL**: Author production PromQL alerts for 99.9% availability SLO with 14.4x and 6x burn rates.
- **Lab 2: SEV-1 Outage Incident Commander Simulation**: Lead response to cascading checkout failure; assign tasks; isolate blast radius; mitigate under 15 minutes.
- **Lab 3: Blameless Post-Mortem & Timeline Construction**: Formulate Root Cause Analysis (RCA), identify contributing systemic factors, and author 3 preventative Jira action items with measurable owners.

## 7. Common Errors
- Paging on-call engineers for non-actionable warnings or single failed health checks.
- Blaming individuals ("human error") instead of fixing systemic engineering gaps (missing safeguards, confusing UIs, lack of automated rollbacks).
- Skipping post-mortems after resolving incidents.

## 8. Troubleshooting
1. Assess Blast Radius: Who is impacted? Which tier is failing?
2. Mitigate First, Root-Cause Later: Restart, shed load, rollback, disable feature flag. Do not spend 2 hours debugging while customers are down.
3. Verify Remediation: Watch P99 latency and 5xx error rate return to baseline before closing the incident call.

## 9. Production Design
- Implement Chaos Engineering (Chaos Mesh, Gremlin, Litmus) to inject synthetic node kills and network latency in staging.
- Enforce automated canary analysis (Kayenta, Flagger) to rollback degrading versions before full rollout.

## 10. Security & Resilience
- Graceful degradation: If recommendations service is down, render static fallback items rather than breaking the entire webpage.
- Implement rate limiting and shedding at edge API gateways.

## 11. Performance
- Establish capacity planning models based on historic peak QPS, CPU/memory scaling factors, and database connection limits.

## 12. Interview Scenarios
- **Scenario**: What is the difference between an SLA, an SLO, and an SLI?
  - **Answer**: 
    - **SLI (Service Level Indicator)**: The quantitative measurement of service performance in real time (e.g. "99.4% of HTTP requests returned status code < 500 in the last 5 minutes").
    - **SLO (Service Level Objective)**: The internal target reliability level agreed upon by engineering and product teams (e.g. "99.9% of requests must succeed over a rolling 30-day window").
    - **SLA (Service Level Agreement)**: The external legal contract with customers specifying penalties (e.g. financial credits) if reliability drops below a threshold (e.g. "If monthly uptime drops below 99.5%, customers receive a 10% credit").
