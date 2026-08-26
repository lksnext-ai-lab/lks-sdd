#!/usr/bin/env python3
"""Verify reusable exact profile certifications without executing Docker gates."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from profile_registry import load_catalog, load_profile_bundle, validate_profile_bundle


def verify(*, evaluated_on: date, max_age_days: int) -> tuple[int, dict[str, Any]]:
    catalog, catalog_errors = load_catalog()
    errors = list(catalog_errors)
    profiles: list[dict[str, Any]] = []
    for entry in catalog.get("profiles", []):
        if not isinstance(entry, dict) or entry.get("lifecycle") != "active":
            continue
        profile_id = str(entry.get("id", ""))
        profile_errors = validate_profile_bundle(profile_id, require_validated=True)
        bundle = load_profile_bundle(profile_id)
        evidence_path = (
            bundle.root / "certification-evidence.json"
            if bundle.root is not None
            else Path("missing")
        )
        certified_at: str | None = None
        age_days: int | None = None
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            certified_at = evidence.get("certified_at")
            certified_date = date.fromisoformat(str(certified_at))
            age_days = (evaluated_on - certified_date).days
            if age_days < 0:
                profile_errors.append(
                    f"{profile_id}: certified_at no puede quedar en el futuro."
                )
            elif age_days > max_age_days:
                profile_errors.append(
                    f"{profile_id}: certificación de {age_days} días supera el máximo de {max_age_days}."
                )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            profile_errors.append(
                f"{profile_id}: no se pudo fechar la certificación exacta: {exc}"
            )
        profiles.append(
            {
                "profile_id": profile_id,
                "status": "passed" if not profile_errors else "failed",
                "certified_at": certified_at,
                "age_days": age_days,
                "errors": list(dict.fromkeys(profile_errors)),
            }
        )
        errors.extend(profile_errors)
    if not profiles:
        errors.append("No hay perfiles active que acreditar.")
    passed = not errors
    payload = {
        "profile_id": "ALL-ACTIVE",
        "evidence_mode": "reused-exact-certifications",
        "evaluated_on": evaluated_on.isoformat(),
        "maximum_age_days": max_age_days,
        "profiles": profiles,
        "passed": passed,
        "complete_gate": passed,
        "runtime": "recorded-docker",
        "containers_executed": False,
        "errors": list(dict.fromkeys(errors)),
    }
    return (0 if passed else 2), payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", required=True)
    parser.add_argument("--max-age-days", type=int, default=90)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        evaluated_on = date.fromisoformat(args.date)
    except ValueError:
        parser.error("--date debe usar AAAA-MM-DD.")
    if args.max_age_days < 1:
        parser.error("--max-age-days debe ser positivo.")
    code, payload = verify(
        evaluated_on=evaluated_on, max_age_days=args.max_age_days
    )
    if args.as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print("PASSED" if payload["passed"] else "FAILED")
        print("evidence_mode=reused-exact-certifications")
        for profile in payload["profiles"]:
            print(f"{profile['status'].upper()}: {profile['profile_id']}")
    return code


if __name__ == "__main__":
    sys.exit(main())
