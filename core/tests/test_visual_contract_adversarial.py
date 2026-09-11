from __future__ import annotations

import unittest

import test_visual_contract as visual_contract
from eval_support import (
    READINESS_SCRIPT,
    _append_row,
    _replace_row,
    confirm_planning_change,
    run_json,
)


VALIDATE_SCRIPT = visual_contract.VALIDATE_SCRIPT


class VisualContractAdversarialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = visual_contract.VisualContractTests(
            methodName="test_confirmed_visual_contract_is_ready_and_fingerprinted"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.asset, self.digest = self.fixture._materialize_visual_contract()
        self.root = self.fixture.root
        self.docs = self.fixture.docs

    def _assert_project_valid(self) -> None:
        code, result = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={0, 2}
        )
        self.assertEqual(code, 0, result.get("errors", []))
        self.assertTrue(result["valid"], result.get("errors", []))

    def test_none_cannot_hide_reuse_in_reason(self) -> None:
        self._assert_project_valid()
        self.fixture._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-002, UX-003 | none | "
            "not-applicable: no new visual prototype | "
            "Reuse confirmed baseline VIS-001 without visual changes |"
        )

        code, result = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={0, 2}
        )

        self.assertEqual(code, 2, result)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any(
                "Visual mode=none" in error
                and ("reutil" in error.casefold() or "reuse" in error.casefold())
                for error in result.get("errors", [])
            ),
            result.get("errors", []),
        )

    def test_current_contract_flow_must_cover_current_contract_screen(self) -> None:
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        _append_row(
            ux_path,
            "| ID | State | Screen",
            "| UX-010 | confirmed | Other screen | Other purpose | synthetic user | "
            "Other content | Continue | FR-001 | AC-001 | INC-001 |",
        )
        _append_row(
            ux_path,
            "| Screen | Entry and exit",
            "| UX-010 | Other entry and exit | Other hierarchy | "
            "not-applicable: no secondary action | not-applicable: one role | "
            "Desktop | Labels and keyboard | not-applicable: fixed content |",
        )
        _append_row(
            ux_path,
            "| Screen | Loading | Empty",
            "| UX-010 | Progress | Empty | Error | not-applicable: public | "
            "Confirmation | Recovery |",
        )
        _append_row(
            ux_path,
            "| ID | State | Flow or interaction",
            "| UX-011 | confirmed | Unrelated flow | synthetic user | UX-010 | "
            "Enter other | Continue | Recover | not-applicable: no dialog | "
            "Keyboard | AC-001 | INC-001 |",
        )
        self.fixture._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-011, UX-003 | new | "
            "VIS-001 | Contract links a screen and an unrelated flow |"
        )

        code, result = run_json(
            VALIDATE_SCRIPT, str(self.root), expected_codes={0, 2}
        )

        self.assertEqual(code, 2, result)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any(
                "UX-001" in error
                and "cubiert" in error.casefold()
                and "flujo" in error.casefold()
                for error in result.get("errors", [])
            ),
            result.get("errors", []),
        )

    def test_confirmed_baseline_can_be_reused_across_increments(self) -> None:
        increments_path = self.docs / "04-delivery" / "increments.md"
        ux_path = self.docs / "03-solution" / "ux-accessibility.md"
        _append_row(
            increments_path,
            "| ID | State | In scope",
            "| INC-000 | proposed | Historical visual baseline | none | FR-001 | "
            "AC-001 | ADR-001 | TEST-001 |",
        )
        _append_row(
            ux_path,
            "| ID | State | Screen",
            "| UX-010 | confirmed | Historical request screen | Historical baseline | "
            "synthetic user | Historical content | Submit | FR-001 | AC-001 | INC-000 |",
        )
        _append_row(
            ux_path,
            "| Screen | Entry and exit",
            "| UX-010 | Historical entry and exit | Historical hierarchy | "
            "not-applicable: no secondary action | not-applicable: one role | "
            "Desktop baseline | Labels and keyboard | not-applicable: fixed content |",
        )
        _append_row(
            ux_path,
            "| Screen | Loading | Empty",
            "| UX-010 | Progress | Empty form | Error feedback | "
            "not-applicable: public | Confirmation | Recovery |",
        )
        _append_row(
            ux_path,
            "| ID | State | Flow or interaction",
            "| UX-011 | confirmed | Historical submit | synthetic user | UX-010 | "
            "Open form | Submit | Recoverable error | "
            "not-applicable: no destructive action | Keyboard flow | AC-001 | INC-000 |",
        )
        _replace_row(
            ux_path,
            "VIS-001",
            "| VIS-001 | confirmed | ![Request screen](ui-prototypes/VIS-001.png) | "
            "PNG | 1440x900 | UX-010, UX-011 | FR-001 | ImageGen synthetic fixture | "
            f"2026-08-20 | synthetic UI brief | {self.digest} | "
            "user-confirmed; role=synthetic-reviewer; date=2026-08-20; ref=ADR-001 | "
            "Hierarchy, density and primary-action treatment | Static image does not "
            "prove responsive behavior or accessibility | ADR-001 | INC-000 |",
        )
        self.fixture._replace_interface_row(
            "| INC-001 | applicable | UX-001, UX-002, UX-003 | reuse | "
            "VIS-001 | Reuse the confirmed visual ADR from INC-000 |"
        )
        planning_path = self.docs / "04-delivery/planning-coverage.md"
        planning_path.write_text(
            planning_path.read_text(encoding="utf-8").replace(
                ", UX-001, UX-002, UX-003, VIS-001 | TASK-001 |",
                ", UX-001, UX-002, UX-003, UX-010, UX-011, VIS-001 | TASK-001 |",
                1,
            ),
            encoding="utf-8",
            newline="\n",
        )
        self._assert_project_valid()
        confirm_planning_change(
            self.root,
            change_id="PCH-002",
            affected_contract="UX-010, UX-011, VIS-001",
            affected_tasks="TASK-001",
            decision="ADR-001",
            reason="Human-confirmed reuse of the historical visual baseline",
        )

        code, result = run_json(
            READINESS_SCRIPT,
            str(self.root),
            "--increment",
            "INC-001",
            expected_codes={0, 3},
        )

        self.assertEqual(code, 0, result.get("blockers", []))
        self.assertEqual(
            result["status"],
            "ready-for-implementation-authorization",
            result.get("blockers", []),
        )
        self.assertEqual(result["visual_mode"], "reuse")
        self.assertEqual(result["visual_prototypes"], ["VIS-001"])


if __name__ == "__main__":
    unittest.main()
