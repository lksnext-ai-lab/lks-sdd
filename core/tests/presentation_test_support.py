"""Synthetic reviewer: inspect a real view then submit its exact receipt.

Existing workflow tests use this explicit helper to exercise their original
authority/transaction cases under the new presentation boundary. Tests of that
boundary itself call the public functions directly, without this helper.
"""
import inspect


def technical_solution():
    return {"components": [{"name": "Módulo de saludo", "responsibility": "Devolver el saludo de la aplicación",
             "current": "Función de saludo con interfaz sin parámetros", "change": "Devolver Hola conservando la función pública",
             "contracts": "Entrada sin parámetros; salida de tipo cadena; no modifica otras interfaces",
             "data": "No persiste datos ni requiere migración", "errors": "No introduce entradas externas ni permisos nuevos",
             "verification": "Invocar la función y comprobar la cadena Hola", "status": "proposed"}],
            "interactions": "Cambio aislado; los consumidores conservan la interfaz y reciben el saludo nuevo."}


def present(function, *args, **kwargs):
    original = inspect.unwrap(function)
    # Old frozen runtime experiments retain their own API and do not get upgraded
    # merely because this fixture is used by a measurement runner.
    if original is function: return function(*args, **kwargs)
    from v3_presentation_guard import call_data, required
    from v3_decision_presentation import decision_view
    event_names = {"initialize": "init", "approve": "approve", "approve_and_authorize": "authorize-plan",
                   "governance": "governance", "configure": "configure-collaboration", "record": "adopt",
                   "integrate": "integrate", "accept": "accept", "assign": "assign", "handoff": "handoff",
                   "exception": "exception", "revoke": "revoke", "upgrade": "migration-preview",
                   "define": "define-correction", "resolve": "resolve-defect", "reconcile_migrated": "migration-reconcile"}
    root, dynamic, data = call_data(original, args, kwargs)
    event = event_names.get(original.__name__, dynamic)
    if required(event, data):
        view = decision_view(root, event, data)
        kwargs["presented"] = view["receipt"]
    return function(*args, **kwargs)
