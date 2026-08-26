"""Explain profile coverage without weakening exact automation support."""

from __future__ import annotations

from typing import Any

from profile_registry import load_profile_bundle, validate_profile_bundle


def describe_profile_coverage(profile_id: str) -> dict[str, Any]:
    """Return diagnostic axes for one profile; never authorize implementation."""
    bundle = load_profile_bundle(profile_id)
    profile = bundle.profile
    if not bundle.catalog_entry:
        return {
            "profile_id": profile_id,
            "catalog_fit": "not-catalogued",
            "preparation": "not-available",
            "implementation": "not-available",
            "local_verification": "not-available",
            "external_interoperability": "not-assessed",
            "delivery_evidence": "not-assessed",
            "capabilities": {"declared": [], "locked": [], "missing_from_lock": []},
            "qualification_blockers": [
                "El perfil exacto no está en el catálogo local."
            ],
            "next_step": "Definir un perfil cerrado o elegir otro perfil mediante una decisión humana confirmada.",
        }

    structural_errors = validate_profile_bundle(profile_id, require_validated=False)
    lifecycle = profile.get("lifecycle")
    lock = bundle.lock
    locked_gate_status = {
        str(item.get("id")): str(item.get("status"))
        for item in lock.get("gates", [])
        if isinstance(item, dict) and item.get("id")
    }
    declared_capabilities = sorted(
        str(item) for item in profile.get("required_capabilities", [])
    )
    locked_capabilities = sorted(
        str(item.get("id"))
        for item in lock.get("capabilities", [])
        if isinstance(item, dict) and item.get("id")
    )
    exact_supported = (
        lifecycle == "active"
        and lock.get("validated") is True
        and lock.get("composition", {}).get("status") == "passed"
        and not structural_errors
    )
    checks = [
        item
        for item in bundle.driver.get("verify", {}).get("checks", [])
        if isinstance(item, dict)
    ]
    external_gate = "GATE-OIDC-INTEGRATION"
    has_external_interop = any(item.get("id") == external_gate for item in checks)
    delivery_gate = "GATE-DELIVERY-EVIDENCE"
    has_delivery_gate = any(item.get("id") == delivery_gate for item in checks)
    qualification_blockers = list(structural_errors)
    if lifecycle == "candidate":
        qualification_blockers.extend(
            [
                "El perfil permanece candidate.",
                "El lock exacto no está validado.",
                "La composición exacta no está certificada.",
            ]
        )
        if has_external_interop and locked_gate_status.get(external_gate) != "passed":
            qualification_blockers.append(
                "La interoperabilidad externa permanece not-run."
            )

    return {
        "profile_id": profile_id,
        "catalog_fit": "exact" if lifecycle == "active" else "candidate",
        "preparation": "available"
        if checks and not structural_errors
        else "not-available",
        "implementation": "supported"
        if exact_supported
        else "candidate-not-certified"
        if lifecycle == "candidate"
        else "not-available",
        "local_verification": "certified"
        if exact_supported
        else "defined-not-certified"
        if checks and not structural_errors
        else "not-available",
        "external_interoperability": (
            "not-applicable"
            if not has_external_interop
            else "certified"
            if locked_gate_status.get(external_gate) == "passed"
            else "not-run"
        ),
        "delivery_evidence": (
            "not-applicable"
            if not has_delivery_gate
            else "certified"
            if locked_gate_status.get(delivery_gate) == "passed"
            else "not-run"
        ),
        "capabilities": {
            "declared": declared_capabilities,
            "locked": locked_capabilities,
            "missing_from_lock": sorted(
                set(declared_capabilities) - set(locked_capabilities)
            ),
        },
        "qualification_blockers": list(dict.fromkeys(qualification_blockers)),
        "next_step": (
            "El perfil exacto está certificado; evaluar ahora el lock consumidor y los gates del proyecto."
            if exact_supported
            else "Ejecutar y revisar la certificación exacta, incluida la interoperabilidad real cuando sea aplicable; no sustituir la tecnología confirmada."
        ),
    }
