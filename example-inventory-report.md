# Inventory baseline and renewal review

Review date: 2026-09-23 | Renewal horizon: 90 days

This compares supplied inventory with a supplied baseline. It does not query vendors, verify license entitlement, scan vulnerabilities, or certify regulatory compliance.

| Asset | Owner | Findings |
| --- | --- | --- |
| lab\-switch\-a | Network team | REVIEW: version differs from supplied baseline<br>LATER: support\_end in 280 days<br>DUE: license\_renewal in 22 days |
| lab\-switch\-b | Network team | REVIEW: inventory observation is over 30 days old<br>MATCH: version matches supplied baseline<br>OVERDUE: support\_end passed 22 days ago<br>LATER: license\_renewal in 159 days |
| lab\-firewall\-a | Unknown | UNKNOWN: owner missing<br>MATCH: version matches supplied baseline<br>UNKNOWN: support\_end not supplied<br>UNKNOWN: license\_renewal not supplied |
