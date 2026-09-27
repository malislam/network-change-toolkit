# Cisco Catalyst 3850 upgrades with Ansible

## Overview

At Fried Frank, I used Ansible to support Cisco Catalyst 3850 switch upgrades across eight office locations. The goal was to make a repeated maintenance task more consistent across sites while keeping validation, exception handling, and operator review visible.

This case study describes the work at a high level. It does not contain employer configurations, credentials, IP addresses, software images, inventory, or the original playbook. The companion files in this repository are new portfolio examples built with fictional data.

## The operational problem

Each site required the same general maintenance steps, but the work still depended on the condition of the individual switch and site. Before an upgrade, the engineer needed to confirm the installed version, available storage, hardware inventory, interface state, uplinks, and reachability. Afterward, the same areas had to be checked again so that a successful reload was not mistaken for a successful change.

Running the process manually at every location increased the chance of inconsistent evidence and made it harder to compare results across sites. Ansible provided a central way to run repeatable tasks and collect output while leaving approval and troubleshooting with the engineer.

## My role

- Built and used an Ansible workflow for Cisco Catalyst 3850 maintenance across eight sites.
- Organized the work so that pre-change collection, the upgrade activity, and post-change validation were distinct phases.
- Reviewed device output and handled site-specific exceptions rather than assuming every switch was in the same state.
- Maintained change documentation and validation steps so that the maintenance could be reviewed and handed off clearly.

## Workflow

```mermaid
flowchart LR
  A[Confirm authorized scope] --> B[Collect version inventory storage and interfaces]
  B --> C[Review readiness and exceptions]
  C --> D[Execute approved upgrade steps]
  D --> E[Wait for reachability and management access]
  E --> F[Collect post-change evidence]
  F --> G[Compare expected and observed state]
  G --> H[Close document or escalate]
```

### 1. Establish scope and recovery information

The change began with the approved device list, maintenance window, access method, software target, and recovery plan. Site contacts and escalation paths were kept available because a remote workflow still needed a practical response if a switch did not return.

### 2. Collect pre-change evidence

The workflow gathered the information needed to decide whether the device was ready for maintenance. Typical checks included software version, model and serial information, storage, interface state, and other operational observations relevant to the site.

Automation made the collection consistent. It did not decide whether an abnormal condition was safe to ignore.

### 3. Review readiness

The engineer reviewed the collected evidence before proceeding. A storage problem, unexpected version, unreachable dependency, or unexplained interface condition required investigation instead of allowing the remaining steps to continue automatically.

### 4. Perform the approved change

Only the authorized devices and approved software were in scope. Installation and reload actions were treated as controlled change steps. They were not mixed into a discovery task or triggered merely because a host appeared in inventory.

### 5. Validate service after the change

After management access returned, the workflow collected a comparable set of observations. The engineer confirmed the target version and reviewed interfaces, uplinks, and other expected state. Missing evidence remained an incomplete change rather than being counted as a pass.

### 6. Document exceptions and handoff

Results and exceptions were recorded for each site. Any unresolved condition was escalated with the collected evidence and the last confirmed state so that the next person did not have to restart the investigation.

## What the automation improved

- Applied the same collection and validation structure across eight locations.
- Reduced repetitive command entry and made device output easier to compare.
- Kept exceptions visible instead of hiding them behind a single success message.
- Supported clearer change records, escalation, and handoff.

I do not have a verified time-savings measurement from this work, so this case study does not attach a percentage or hour reduction to the result.

## Related portfolio examples

- [`ios-maintenance-checks.yml`](ios-maintenance-checks.yml) is a new, read-only example that collects IOS version, inventory, and interface information one device at a time.
- [`upgrade-runbook.md`](upgrade-runbook.md) describes planning, recovery, execution, and validation considerations for switch maintenance.
- [`review.py`](review.py) demonstrates offline before-and-after comparison for fictional Nexus evidence. It is separate from the Catalyst 3850 work.

These examples show the operational ideas without reproducing the original employer environment or presenting an untested universal firmware installer.

## What this demonstrates

This project reflects practical network automation rather than automation for its own sake: repeat the routine steps, stop when evidence is incomplete, keep disruptive actions controlled, and leave enough information for another engineer to understand the outcome.
