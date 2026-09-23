# Nexus change evidence review

**Result: FAIL**

Before: 2026-01-01T01:00:00Z
After: 2026-01-01T02:00:00Z

Offline evidence review only. PASS is not authorization or proof of traffic health or upgrade compatibility.

| Result | Evidence | Finding |
| --- | --- | --- |
| PASS | captured_at | Evidence is in chronological order. |
| PASS | lab-nexus-a/model | Nexus-demo-no-PID -> Nexus-demo-no-PID; hardware identity must remain unchanged. |
| PASS | lab-nexus-a/version | DEMO-OLD -> DEMO-TARGET; expected target DEMO-TARGET. |
| PASS | lab-nexus-a/before/vpc/peer_link | Observed up. |
| PASS | lab-nexus-a/after/vpc/peer_link | Observed up. |
| PASS | lab-nexus-a/before/vpc/peer_keepalive | Observed alive. |
| PASS | lab-nexus-a/after/vpc/peer_keepalive | Observed alive. |
| PASS | lab-nexus-a/before/vpc/consistency | Observed success. |
| PASS | lab-nexus-a/after/vpc/consistency | Observed success. |
| PASS | lab-nexus-a/interfaces/Ethernet1/1 | Remained up. |
| ACCEPTED | lab-nexus-a/interfaces/Ethernet1/2 | up -> down; planned: Fictional change LAB-001: unused lab connection decommissioned. |
| PASS | lab-nexus-a/port_channels/port-channel10 | Remained up. |
| PASS | lab-nexus-a/vlans/110 | Remained up. |
| FAIL | lab-nexus-a/vlans/120 | up -> None; state is degraded or changed without an exact approved transition. |
| FAIL | lab-nexus-a/neighbors/bgp\|default\|192.0.2.10 | up -> down; state is degraded or changed without an exact approved transition. |
| PASS | lab-nexus-a/neighbors/ospf\|default\|192.0.2.20 | Remained up. |
| PASS | lab-nexus-b/model | Nexus-demo-no-PID -> Nexus-demo-no-PID; hardware identity must remain unchanged. |
| FAIL | lab-nexus-b/version | DEMO-OLD -> DEMO-OLD; expected target DEMO-TARGET. |
| PASS | lab-nexus-b/before/vpc/peer_link | Observed up. |
| FAIL | lab-nexus-b/after/vpc/peer_link | Observed down; expected up. |
| PASS | lab-nexus-b/before/vpc/peer_keepalive | Observed alive. |
| PASS | lab-nexus-b/after/vpc/peer_keepalive | Observed alive. |
| PASS | lab-nexus-b/before/vpc/consistency | Observed success. |
| PASS | lab-nexus-b/after/vpc/consistency | Observed success. |
| PASS | lab-nexus-b/interfaces/Ethernet1/1 | Remained up. |
| PASS | lab-nexus-b/interfaces/Ethernet1/2 | Remained up. |
| FAIL | lab-nexus-b/port_channels/port-channel10 | up -> None; state is degraded or changed without an exact approved transition. |
| PASS | lab-nexus-b/vlans/110 | Remained up. |
| PASS | lab-nexus-b/vlans/120 | Remained up. |
| PASS | lab-nexus-b/neighbors/bgp\|default\|192.0.2.10 | Remained up. |
| PASS | lab-nexus-b/neighbors/ospf\|default\|192.0.2.20 | Remained up. |
