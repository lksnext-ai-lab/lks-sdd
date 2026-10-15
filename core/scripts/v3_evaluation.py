"""Bounded, context-local calculations for one immutable in-memory model.

No disk cache or cached authority across commands. Physical input checks at prepare
and apply remain the responsibility of the existing storage/transaction guards.
"""
from collections import OrderedDict
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import asyncio
import threading

from v3_contract import ContractError

_ACTIVE = ContextVar("lks_sdd_calculations", default=())
MAX_ENTRIES = 256
MAX_UNITS = 131072
MAX_SOURCE_BYTES = 16 * 1024 * 1024


def _owner():
    try: task = asyncio.current_task()
    except RuntimeError: task = None
    return threading.get_ident(), task


class Evaluation:
    def __init__(self, model):
        self.model, self.owner = model, _owner()
        self.revision = model._revision
        self.cache = OrderedDict()
        self.units = self.source_bytes = 0

    def memo(self, key, create, weight=lambda value: (1, 0)):
        self.require_unchanged()
        try: hash(key)
        except TypeError:
            # Malformed provenance must keep the uncached reader's own outcome.
            return create()
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key][0]
        result = create()  # failures and missing identities are never memoized
        units, size = weight(result)
        if units > MAX_UNITS or size > MAX_SOURCE_BYTES: return result
        while self.cache and (len(self.cache) >= MAX_ENTRIES or self.units + units > MAX_UNITS or self.source_bytes + size > MAX_SOURCE_BYTES):
            _, (_, old_units, old_size) = self.cache.popitem(last=False)
            self.units -= old_units; self.source_bytes -= old_size
        self.cache[key] = (result, units, size)
        self.units += units; self.source_bytes += size
        return result

    def require_unchanged(self):
        if self.model._revision != self.revision:
            raise ContractError("El modelo cambió durante la evaluación; repita sobre una revisión inmutable")

    def clear(self):
        self.cache.clear(); self.units = self.source_bytes = 0
        # Inherited async contexts can outlive the parent evaluation.
        self.model = self.owner = None


def current(model):
    owner = _owner()
    return next((s for s in reversed(_ACTIVE.get()) if s.model is model and s.owner == owner), None)


@contextmanager
def evaluation(model):
    existing = current(model)
    if existing is not None:
        existing.require_unchanged()
        yield existing
        return
    state = Evaluation(model)
    model._evaluations += 1
    token = _ACTIVE.set((*_ACTIVE.get(), state))
    try:
        yield state
        state.require_unchanged()
    finally:
        model._evaluations -= 1
        state.clear()
        _ACTIVE.reset(token)


def evaluated(function):
    @wraps(function)
    def call(model, *args, **kwargs):
        with evaluation(model): return function(model, *args, **kwargs)
    return call


def memo(model, key, create, weight=lambda value: (1, 0)):
    state = current(model)
    return state.memo(key, create, weight) if state is not None else create()
