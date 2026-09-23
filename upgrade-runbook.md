# Switch upgrade planning and validation

This new portfolio runbook reflects the way I approach network maintenance. It is not a copy of an employer's change plan or the Ansible upgrade playbooks I used at work. Exact upgrade commands and sequencing depend on the hardware, topology, installed release and target release.

## 1. Build the change record

Record model, serial/asset reference, software, redundancy/topology, affected services, owner, maintenance window and remote-hands contacts. Validate inventory against the device and approved records. Check support entitlement and renewal dates separately from the software baseline. Identify dependent hosts, port channels, FEX connections and routing peers.

## 2. Confirm the supported path

Read the vendor guide and release notes for the actual model and release pair. Confirm image type, intermediate releases, feature/FEX support, storage space and published image checksum. Establish whether disruption is expected; do not promise a hitless upgrade simply because a pair has vPC.

For Nexus, Cisco documents version-specific compatibility/impact checks and upgrade restrictions in its [Nexus 9000 upgrade guide](https://www.cisco.com/c/en/us/td/docs/dcn/nx-os/nexus9000/105x/upgrade/cisco-nexus-9000-series-nx-os-software-upgrade-and-downgrade-guide-105x/m-upgrading-or-downgrading-the-cisco-nexus-9000-series-nx-os-software.html). This reference is an example release guide, not an approved upgrade path for the fictional fixtures.

## 3. Capture the baseline and recovery plan

- Save configuration backups and recovery materials in approved restricted storage.
- Verify console/out-of-band access and who can intervene onsite.
- Record vPC peer/link/consistency health, port channels, interfaces, VLANs, route neighbors and representative application tests.
- Resolve unhealthy baseline conditions before proceeding, or document their reviewed disposition.
- Define stop conditions, a latest rollback decision time, and the supported recovery/downgrade procedure. A downgrade is not always a simple reversal.

## 4. Execute the approved method

Follow the model/release-specific sequence. Upgrade only the approved scope and stop on unexpected evidence. In an automated workflow, separate evidence collection from installation/reload approval and halt remaining devices if validation fails. The included Ansible example demonstrates the collection phase only. It is not a universal firmware installer.

## 5. Validate before closing

Capture the same observations after each approved stage, verify expected versions and redundancy, and repeat application tests with users or the service owner. Normalize the observations into the sample JSON schema only after checking completeness. Run the comparison tool and investigate every FAIL or INCOMPLETE result. Document deliberately changed ports in the plan; never add an exception merely to hide a failure.

Record actual downtime, evidence locations, deviations, final service checks and the monitoring period. Close the change only after human review and handoff; a script returning PASS is one input, not the decision.
