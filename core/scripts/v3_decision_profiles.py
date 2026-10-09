"""Finite presentation/routing catalog shared by both hosts. No consumer plugins."""
from pathlib import Path
from v3_contract import ContractError, sha

VERSION = "lks-sdd-presentation/2"
PROFILES = {
    "clarification": ("conditional-design", "Qué falta decidir|Opciones y efecto"),
    "configuration": ("project-setup", "Objetivo|Configuración propuesta|Personas y responsabilidades|Controles y condiciones|Cambios respecto a la situación actual|Impacto y pendientes"),
    "adoption": ("project-setup", "Alcance revisado|Comportamiento observado|Intención que se propone confirmar|Diferencias y desconocidos|Documentación que se incorporará|Decisiones pendientes"),
    "migration": ("project-setup", "Situación actual y destino|Cambios previstos|Información y acuerdos que se conservan|Trabajo afectado|Comprobaciones y recuperación|Decisiones pendientes"),
    "specification": ("specifications", "Objetivo|Alcance incluido y excluido|Comportamiento esperado|Solución técnica|Impacto|Criterios de aceptación|Decisiones pendientes"),
    "technology": ("conditional-design", "Necesidad|Alternativas|Solución recomendada|Componentes y contratos afectados|Consecuencias y comprobación|Decisiones pendientes"),
    "visual": ("conditional-design", "Pantallas y estados|Propuestas visuales|Diferencias y recomendación|Alcance de la selección|Pendientes"),
    "correction": ("corrections", "Acuerdo o resultado esperado|Diferencia observada|Tratamiento propuesto|Cambios y alcance|Comprobación|Pendientes"),
    "planning": ("planning", "Objetivo y entregables|Tareas y responsables|Orden y dependencias|Criterios y pruebas|Alcance de la ejecución|Riesgos y pendientes"),
    "assignment": ("assignments", "Resultado esperado|Alcance y responsabilidades|Estado recibido y entregables|Contratos y dependencias|Pruebas y condiciones de inicio|Pendientes"),
    "verification": ("verification", "Resultado que se comprueba|Criterios y pruebas|Evidencia observada|Fallos y límites|Tratamiento y siguiente acción"),
    "integration": ("verification", "Resultado integrado|Componentes y compatibilidad|Comprobaciones del conjunto|Incidencias y reservas|Alcance de la conformidad|Pendientes"),
    "acceptance": ("verification", "Resultado entregado|Acceso y revisión|Cumplimiento de criterios|Limitaciones y reservas|Alcance de la aceptación|Pendientes"),
    "exception": ("exceptions-continuity", "Condición pendiente|Motivo y alternativas|Alcance de la excepción|Consecuencias y medidas|Responsable y vencimiento|Efecto de la decisión"),
    "continuity": ("exceptions-continuity", "Situación actual|Cambio solicitado|Trabajo y decisiones afectados|Consecuencias|Continuación y pendientes"),
    "recovery": ("exceptions-continuity", "Operación y estado observado|Cambios que se aplicarán o revertirán|Información conservada|Riesgos y conflictos|Comprobación del resultado|Pendientes"),
    "delivery": ("external-delivery", "Contenido y resultado|Destino y audiencia|Cambios o envío previstos|Comprobaciones y límites|Alcance del permiso|Pendientes"),
    "information": (None, "Resultado|Impedimentos y siguiente paso"),
}
GROUPS = {
    "configuration": "init governance configure-collaboration",
    "adoption": "adopt adopt-inspect",
    "migration": "migration-preview migration-diagnose migration-continuation migration-reconcile old-branch",
    "specification": "review review-proposal close-proposal",
    "planning": "authorize-plan",
    "assignment": "review-task assign handoff",
    "correction": "review-comment resolve-comment reject-result define-correction resolve-defect",
    "verification": "evidence analysis analysis-run analysis-findings verify close",
    "integration": "integrate",
    "acceptance": "accept",
    "exception": "exception propose-exception review-exception",
    "continuity": "revoke pause cancel reopen",
    "recovery": "apply recover rollback",
    "delivery": "prepare-delivery external-action client-view",
    "clarification": "clarify identity",
    "technology": "technology-choice",
    "visual": "visual-choice",
    "information": "validate status trace context readiness interventions checkpoint implement start resume catalog history state-history reindex author decision-view",
}
ACTIONS = {action: profile for profile, actions in GROUPS.items() for action in actions.split()}
ACTIONS["approve"] = "specification"
HISTORICAL = set("tracking-project tracking-authorize tracking-result tracking-reconcile tracking-milestone retention-compact retention-restore visual-request visual-accept visual-cancel visual-observe authorize-delivery".split())
INFORMATION = set("validate status trace context readiness interventions checkpoint implement catalog history state-history reindex author decision-view adopt-inspect migration-diagnose migration-continuation old-branch evidence analysis analysis-run analysis-findings verify close prepare-delivery".split())


def profiles(event, data):
    if event in HISTORICAL: return ["recovery" if event.startswith("retention-") else "delivery"]
    if event not in ACTIONS: raise ContractError("Evento desconocido; concrete la decisión antes de continuar")
    profile = ACTIONS[event]
    if event == "approve":
        purpose = data.get("purpose")
        if purpose not in {"proposal", "plan", "execution", "technology"}:
            raise ContractError("Indique si se revisa propuesta, plan, ejecución o tecnología")
        profile = {"proposal": "specification", "plan": "planning", "execution": "planning", "technology": "technology"}[purpose]
    if event in {"start", "resume"} and (data.get("review") or data.get("offer")): profile = "assignment"
    result = [profile]
    if event == "authorize-plan" and data.get("review_tasks"): result.append("assignment")
    if event == "integrate" and data.get("accept_result"): result.append("acceptance")
    if event == "resolve-defect": result.append("verification")
    return list(dict.fromkeys(result))


def instruction_refs(selected, runtime=None):
    runtime = Path(runtime or Path(__file__).resolve().parents[1]).resolve()
    names = ["docs/V3-COMMON.md", "docs/USER-DECISIONS.md"]
    names += ["docs/decision-guides/" + PROFILES[p][0] + ".md" for p in selected if PROFILES[p][0]]
    result = []
    for name in dict.fromkeys(names):
        path = runtime / name
        if path.resolve().is_relative_to(runtime) is False or not path.is_file():
            raise ContractError("Recurso de instrucciones ausente o fuera del runtime: " + name)
        result.append({"path": name, "sha256": sha(path.read_bytes()), "reason": "Reglas comunes" if "/decision-guides/" not in name else "Decisión aplicable"})
    return result
