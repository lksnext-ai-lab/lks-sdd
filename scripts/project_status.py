#!/usr/bin/env python3
"""Render management, developer or audit project status without side effects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from experience_engine import (
    ExperienceError,
    load_status,
    render_developer,
    render_management,
    view_json,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_root", type=Path)
    parser.add_argument("--task")
    parser.add_argument(
        "--view", choices=("management", "developer", "audit"), default="management"
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        status = load_status(args.project_root, task_id=args.task)
        payload = view_json(status, args.view)
        visual_handoffs = []
        if (args.project_root / ".lks-sdd/handoffs/visual").is_dir():
            from manage_visual_handoff import run as handoff_status
            visual_handoffs = handoff_status(args.project_root, argparse.Namespace(action="status"))["handoffs"]
            payload["visual_handoffs"] = visual_handoffs
        if args.as_json or args.view == "audit":
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        elif args.view == "developer":
            print(render_developer(status))
        else:
            print(render_management(status))
        if not args.as_json and args.view != "audit" and visual_handoffs:
            print("Relevos visuales: " + "; ".join(f"{item['id']}: {item['status']}" for item in visual_handoffs))
        return 0
    except ExperienceError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
