"""Non-invasive repository hygiene checks. Run from the backend folder."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BAD_SUFFIXES = {'.pem', '.p12', '.pfx', '.key'}


def tracked_files():
    try:
        result = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z'],
                                capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print('ERROR: Git not initialized or unavailable. Cannot audit tracked files.')
        return None
    return [Path(name.decode('utf-8', errors='replace')) for name in result.stdout.split(b'\0') if name]


def main():
    tracked = tracked_files()
    if tracked is None:
        return 2
    findings = []
    for p in tracked:
        low = p.name.lower()
        if low == '.env' or (low.startswith('.env.') and not low.endswith('.example')):
            findings.append(str(p))
        if p.suffix.lower() in BAD_SUFFIXES:
            findings.append(str(p))
        if any(part in ('node_modules', '.venv', 'venv', '__pycache__') for part in p.parts):
            findings.append(str(p))
    if findings:
        print('FAIL: potentially sensitive/unwanted tracked files:')
        for item in sorted(set(findings)):
            print(' -', item)
        return 1
    print(f'PASS: {len(tracked)} tracked paths; no obvious credentials or environment folders tracked.')
    print('This is not a secret-scanning substitute; inspect commits before pushing.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
