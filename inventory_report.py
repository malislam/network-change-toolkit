"""Offline inventory review against supplied version and renewal baselines."""
import argparse
import csv
from datetime import date
from pathlib import Path
import sys

FIELDS = ['asset_id', 'platform', 'version', 'approved_version', 'owner',
          'last_verified', 'support_end', 'license_renewal']


def parse_date(value):
    return date.fromisoformat(value) if value else None


def review(rows, as_of, horizon=90):
    if horizon < 0:
        raise ValueError('horizon must not be negative')
    seen, results = set(), []
    for row in rows:
        if set(row) != set(FIELDS) or any(not isinstance(v, str) for v in row.values()):
            raise ValueError('CSV must contain exactly the documented columns and complete rows')
        row = {key: value.strip() for key, value in row.items()}
        asset = row['asset_id']
        if not asset or asset in seen:
            raise ValueError('Each row needs a unique, nonempty asset_id')
        seen.add(asset)
        issues = []
        if not row['platform']:
            issues.append('UNKNOWN: platform missing')
        if not row['owner']:
            issues.append('UNKNOWN: owner missing')
        verified = parse_date(row['last_verified'])
        if verified and verified > as_of:
            raise ValueError(f'{asset}: last_verified is later than the review date')
        if verified is None:
            issues.append('UNKNOWN: inventory verification date missing')
        elif (as_of - verified).days > 30:
            issues.append('REVIEW: inventory observation is over 30 days old')
        if not row['version'] or not row['approved_version']:
            issues.append('UNKNOWN: observed or approved version missing')
        elif row['version'] != row['approved_version']:
            issues.append('REVIEW: version differs from supplied baseline')
        else:
            issues.append('MATCH: version matches supplied baseline')
        for key in ('support_end', 'license_renewal'):
            deadline = parse_date(row[key])
            if deadline is None:
                issues.append(f'UNKNOWN: {key} not supplied')
            else:
                days = (deadline - as_of).days
                if days < 0:
                    issues.append(f'OVERDUE: {key} passed {abs(days)} days ago')
                elif days <= horizon:
                    issues.append(f'DUE: {key} in {days} days')
                else:
                    issues.append(f'LATER: {key} in {days} days')
        results.append({'asset': asset, 'owner': row['owner'] or 'Unknown', 'findings': issues})
    if not results:
        raise ValueError('Inventory contains no assets')
    return results


def escape(value):
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    for char in '\\`*_{}[]()#+-.!|':
        value = value.replace(char, '\\' + char)
    return value.replace('\n', ' ').replace('\r', ' ')


def markdown(results, as_of, horizon):
    lines = ['# Inventory baseline and renewal review', '',
             f'Review date: {as_of.isoformat()} | Renewal horizon: {horizon} days', '',
             'This compares supplied inventory with a supplied baseline. It does not query vendors, verify license entitlement, scan vulnerabilities, or certify regulatory compliance.', '',
             '| Asset | Owner | Findings |', '| --- | --- | --- |']
    for result in results:
        findings = '<br>'.join(escape(s) for s in result['findings'])
        lines.append(f"| {escape(result['asset'])} | {escape(result['owner'])} | {findings} |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('inventory', type=Path)
    parser.add_argument('--as-of', required=True, type=date.fromisoformat)
    parser.add_argument('--horizon', type=int, default=90)
    args = parser.parse_args()
    try:
        with args.inventory.open(encoding='utf-8-sig', newline='') as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != FIELDS:
                raise ValueError('CSV headers must match the sample, in order')
            results = review(list(reader), args.as_of, args.horizon)
        print(markdown(results, args.as_of, args.horizon), end='')
    except (OSError, ValueError, csv.Error) as error:
        print(f'Cannot review inventory: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
