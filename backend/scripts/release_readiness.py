"""Offline release readiness inspection. No secrets or network access required."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def check_files():
    required = [
        ROOT / "Dockerfile", ROOT / "railway.json", ROOT / ".gitignore",
        BACKEND / "manage.py", BACKEND / "requirements.txt",
        BACKEND / "config/settings/build.py", BACKEND / "config/settings/production.py",
        BACKEND / "core/management/commands/deployment_check.py",
        BACKEND / "core/readiness/tests/test_security.py",
    ]
    return [str(p.relative_to(ROOT)) for p in required if not p.is_file()]


def check_railway():
    try:
        config = json.loads((ROOT / "railway.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"Invalid railway.json: {exc}"]
    errors = []
    if config.get("build", {}).get("builder") != "DOCKERFILE":
        errors.append("Railway builder is not DOCKERFILE")
    if config.get("deploy", {}).get("healthcheckPath") != "/api/health/":
        errors.append("Railway healthcheckPath does not match /api/health/")
    return errors


def check_git_tracking():
    if not (ROOT / ".git").exists():
        return ["Git repository not initialized (informational; run git init later)"]
    try:
        proc = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return ["Unable to inspect Git-tracked files"]
    bad = []
    for name in proc.stdout.decode("utf-8", errors="replace").split("\0"):
        if not name:
            continue
        parts = name.replace("\\", "/").split("/")
        filename = parts[-1].lower()
        if filename in {".env", ".env.production", "id_rsa", "id_ed25519"} or filename.endswith((".pem", ".key", ".p12", ".pfx")) or any(part in {".venv", "node_modules"} for part in parts):
            bad.append(name)
    return bad


def main():
    parser = argparse.ArgumentParser(description="StudentStore offline release readiness report")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text")
    args = parser.parse_args()
    missing = check_files()
    railway = check_railway() if not (ROOT / "railway.json") in [ROOT / p for p in missing] else []
    tracked = check_git_tracking()
    # These are manual blockers, never falsely marked as verified.
    manual = [
        "PostgreSQL connection and all migrations",
        "Razorpay test payments, signature/webhook verification and reconciliation",
        "OTP provider end-to-end delivery and rate limiting",
        "Cloudflare R2 upload, retrieval and access policy",
        "Expo SDK compatibility, Android/iOS device flows and API URL",
        "Railway Docker build, static assets and live HTTPS health endpoint",
        "Production permissions, order totals, inventory and refund workflows",
        "GitHub CI results, monitoring, backups and rollback rehearsal",
    ]
    result = {"offline_pass": not (missing or railway or any(x for x in tracked if not x.startswith('Git repository not initialized'))), "missing_files": missing, "railway_issues": railway, "git_tracking_findings": tracked, "manual_release_blockers": manual}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("StudentStore Phase 16 — offline readiness")
        for key in ("missing_files", "railway_issues", "git_tracking_findings"):
            print(f"{key}: {result[key] or 'none'}")
        print("Manual verification still required:")
        for item in manual:
            print(" - " + item)
        print("Offline inspection:", "PASS" if result["offline_pass"] else "FAIL")
        print("Launch approval: NOT GRANTED (manual checks outstanding)")
    return 0 if result["offline_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
