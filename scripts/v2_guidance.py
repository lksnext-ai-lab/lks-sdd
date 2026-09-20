"""Functional, actionable explanations for blocked v2 operations."""
from __future__ import annotations


def _messages(value: dict) -> str:
    parts = []
    for key in ("error", "reason"):
        item = value.get(key)
        if isinstance(item, str):
            parts.append(item)
    for key in ("blockers", "diagnostics", "reasons", "missing_critical_gates"):
        items = value.get(key, [])
        if isinstance(items, list):
            parts.extend(str(item) for item in items)
    return " ".join(parts).casefold()


def explain(value: dict, *, operation: str) -> dict:
    """Translate a runtime block without hiding its machine-readable diagnostics."""
    message = _messages(value)
    common = {
        "operation": operation,
        "decision_required": True,
        "technical_details_available": True,
    }
    if any(token in message for token in ("authorization", "auth ", "revoked", "expired", "stale")):
        return {
            **common,
            "kind": "authorization",
            "summary": "La autorización para continuar ya no representa el trabajo actual.",
            "impact": "La tarea sigue registrada y no se ha dado por completada ni entregada.",
            "next_step": "Revise qué cambió en el alcance y solicite una nueva autorización cuando vuelva a estar conforme.",
            "options": [
                "Corregir o confirmar el alcance actual y autorizar una nueva ejecución.",
                "Cancelar y replanificar si este trabajo ya no debe continuar con la decisión anterior.",
            ],
        }
    if any(token in message for token in ("input hash", "hash", "integrity", "engine changed",
                                          "evidence altered", "evidence integrity", "artifact altered")):
        return {
            **common,
            "kind": "integrity",
            "summary": "El resultado guardado ya no coincide de forma fiable con el trabajo que se quiere continuar.",
            "impact": "No se pierde el historial, pero no puede usarse para cerrar ni entregar la tarea.",
            "next_step": "Revise el cambio que produjo la diferencia y vuelva a verificar el trabajo actual.",
            "options": [
                "Corregir la diferencia y ejecutar una verificación nueva.",
                "Cancelar y replanificar si el resultado anterior ya no es el objetivo.",
            ],
        }
    if any(token in message for token in ("observer", "approved observer", "requires explicit --containers",
                                          "required gate", "gate ")):
        return {
            **common,
            "kind": "verification-availability",
            "summary": "Falta una comprobación acordada o no está disponible para evaluar esta tarea.",
            "impact": "La implementación puede seguir documentada, pero todavía no se considera verificada.",
            "next_step": "Acordar o reparar la comprobación aprobada para esta tarea; no se debe sustituir por un script casual.",
            "options": [
                "Completar la definición aprobada y ejecutar la comprobación.",
                "Aceptar reservas solo si la política del proyecto lo permite.",
                "Cancelar y replanificar si esa comprobación ya no aplica al nuevo alcance.",
            ],
        }
    if any(token in message for token in ("outside authorized", "diff", "baseline", "scope", "contract differs")):
        return {
            **common,
            "kind": "scope",
            "summary": "El trabajo actual ya no coincide con lo que se había acordado para esta tarea.",
            "impact": "No se ha descartado el trabajo, pero no puede verificarse ni cerrarse con el alcance anterior.",
            "next_step": "Decida si el cambio pertenece a esta tarea y revíselo, o cree una nueva decisión para el alcance actualizado.",
            "options": [
                "Revisar el cambio exacto y continuar dentro del alcance aprobado.",
                "Cancelar y replanificar para conservar el trabajo y acordar el nuevo alcance.",
            ],
        }
    if any(token in message for token in ("unfinished dependency", "dependency", "depends_on")):
        return {
            **common,
            "kind": "dependency",
            "summary": "Esta tarea necesita una decisión o un resultado previo antes de poder continuar.",
            "impact": "La tarea dependiente no se ha modificado ni se ha marcado como completada.",
            "next_step": "Finalice la dependencia o revise explícitamente sus reservas antes de continuar.",
            "options": [
                "Completar y verificar la tarea de la que depende.",
                "Tomar una decisión explícita para continuar con las reservas heredadas, cuando la política lo permita.",
                "Cancelar y replanificar la tarea dependiente.",
            ],
        }
    if any(token in message for token in ("invalid", "schema", "document", "technology declaration", "reconciliation")):
        return {
            **common,
            "kind": "contract",
            "summary": "Falta una decisión o información necesaria para saber qué debe hacerse y cómo comprobarlo.",
            "impact": "El proyecto conserva su historial, pero no puede avanzar con una definición ambigua.",
            "next_step": "Complete o corrija la documentación del proyecto antes de autorizar otra ejecución.",
            "options": [
                "Completar la decisión, el alcance o la comprobación que falta.",
                "Replanificar después de corregir la documentación.",
            ],
        }
    return {
        **common,
        "kind": "review-needed",
        "summary": "La tarea necesita una revisión antes de continuar.",
        "impact": "No se han perdido cambios ni se ha declarado la tarea como completada.",
        "next_step": "Revise el motivo registrado y elija entre corregirlo, verificar de nuevo o replanificar.",
        "options": [
            "Corregir el motivo pendiente y volver a ejecutar el siguiente paso seguro.",
            "Cancelar y replanificar si el objetivo o las condiciones han cambiado.",
        ],
    }


def enrich(value: dict, *, operation: str) -> dict:
    """Attach guidance to blocked and reconciliation responses only."""
    if value.get("status") not in {"blocked", "invalid", "conflict", "reconcile-recommended"}:
        return value
    return {**value, "guidance": explain(value, operation=operation)}
