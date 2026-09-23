"""Offline allow-list comparison. No device access or configuration changes."""
import argparse
import json
import sys
from itertools import product
from pathlib import Path


def unique(values):
    if len(values) != len(set(values)):
        raise ValueError('duplicate identifiers')


def validate(design, policy):
    if set(design) != {'zones', 'services', 'approved_flows'}:
        raise ValueError('design requires zones, services and approved_flows')
    if set(policy) != {'rules'}:
        raise ValueError('policy requires rules')
    for key in ('zones', 'services'):
        values = design[key]
        if not isinstance(values, list) or not values or not all(isinstance(v, str) and v.strip() and v != '*' for v in values):
            raise ValueError('nonempty named zones/services required')
        unique(values)
    if not isinstance(design['approved_flows'], list) or not design['approved_flows']:
        raise ValueError('approved flows must be a nonempty list')
    if not isinstance(policy['rules'], list):
        raise ValueError('rules must be a list')
    ids = []
    flows = []
    for flow in design['approved_flows']:
        if set(flow) != {'source', 'destination', 'service', 'reason'} or not isinstance(flow['reason'], str) or not flow['reason'].strip():
            raise ValueError('each approved flow needs a reason and exact endpoints/service')
        for field, domain in [('source', 'zones'), ('destination', 'zones'), ('service', 'services')]:
            if flow[field] not in design[domain]:
                raise ValueError('unknown approved flow value')
        flows.append((flow['source'], flow['destination'], flow['service']))
    unique(flows)
    for rule in policy['rules']:
        if set(rule) != {'id', 'source', 'destination', 'service', 'action', 'log'}:
            raise ValueError('unexpected or missing rule fields')
        if not isinstance(rule['id'], str) or not rule['id'].strip():
            raise ValueError('rule id required')
        ids.append(rule['id'])
        for field, domain in [('source', 'zones'), ('destination', 'zones'), ('service', 'services')]:
            if rule[field] != '*' and rule[field] not in design[domain]:
                raise ValueError('unknown policy zone/service')
        if rule['action'] not in ('allow', 'deny') or type(rule['log']) is not bool:
            raise ValueError('action must be allow/deny and log must be boolean')
    unique(ids)


def review(design, policy):
    validate(design, policy)
    approved = {(f['source'], f['destination'], f['service']) for f in design['approved_flows']}
    findings = []
    used = set()
    # Exhaustive within the finite named model, not within real IP/port space.
    for flow in product(design['zones'], design['zones'], design['services']):
        match = next((r for r in policy['rules'] if all(r[k] in ('*', v) for k, v in zip(('source', 'destination', 'service'), flow))), None)
        allowed = match is not None and match['action'] == 'allow'
        if match:
            used.add(match['id'])
        path = ' -> '.join(flow)
        if allowed and flow not in approved:
            findings.append(f'UNAPPROVED: {path} permitted by {match["id"]}')
        elif not allowed and flow in approved:
            findings.append(f'BLOCKED: {path}; matched {match["id"] if match else "implicit deny"}')
        if allowed and not match['log']:
            findings.append(f'NO LOGGING: {path}; rule {match["id"]}')
    for rule in policy['rules']:
        if rule['id'] not in used:
            findings.append(f'UNREACHED: {rule["id"]}; review order/shadowing within this model')
    return findings


def load(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding='utf-8'), object_pairs_hook=pairs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('design')
    parser.add_argument('policy')
    args = parser.parse_args()
    try:
        findings = review(load(args.design), load(args.policy))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(f'INVALID INPUT: {exc}', file=sys.stderr)
        return 2
    print('# Security policy review\n')
    print('Result: ' + ('REVIEW REQUIRED' if findings else 'PASS within the supplied model'))
    print('\n'.join('- ' + f for f in findings))
    print('\nOffline design check only; not proof of live enforcement or compliance.')
    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
