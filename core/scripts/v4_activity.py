"""Bounded opt-in CLI heartbeats and cooperative stops; never business authority."""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import os
import signal
import sys
import threading
import time

_ACTIVE = ContextVar("lks_sdd_activity", default=None)
PHASES = frozenset(("start", "prepare", "guard", "apply", "inspect", "capture", "output", "stop"))
INTERVAL = 1.5
MAX_BYTES = 16384
COOPERATIVE = frozenset(("work-prepare", "work-continue", "work-record-results"))


class OperationInterrupted(KeyboardInterrupt):
    def __init__(self, controller):
        super().__init__("Cooperative interruption; preserve receipts and inspect technical state")
        self.interruption = {"requested": True, "phase": controller.phase,
                             "recognition_seconds": controller.recognized - controller.requested,
                             "checkpoint_seconds": time.monotonic() - controller.requested,
                             "business_cancel": False,
                             "io_limit": "Native calls, IO and material writes may defer until their next safe boundary"}


class Controller:
    def __init__(self, stream, *, activity=False):
        self.stream, self.activity = stream, activity
        self.phase = "start"
        self.requested = self.recognized = None
        self.handled = False
        self.deferred = 0
        self.bytes = self.events = 0
        self.stop = threading.Event()
        self.thread = None

    def request(self, *_):
        if self.requested is None:
            self.requested = self.recognized = time.monotonic()

    def check(self):
        if self.requested is not None and not self.handled and not self.deferred:
            self.handled = True
            raise OperationInterrupted(self)

    def emit(self):
        raw = (json.dumps({"activity": self.phase}, separators=(",", ":")) + "\n").encode("ascii")
        if not self.activity or self.bytes + len(raw) > MAX_BYTES:
            return False
        try:
            try: descriptor = self.stream.fileno()
            except (AttributeError, OSError, ValueError): descriptor = None
            # No TextIO buffer lock: an unread pipe must not block CLI shutdown.
            if descriptor is None:
                self.stream.write(raw.decode("ascii")); self.stream.flush()
            elif os.write(descriptor, raw) != len(raw):
                return False
        except (OSError, ValueError):
            return False
        self.bytes += len(raw); self.events += 1
        return True

    def heartbeat(self):
        while not self.stop.is_set():
            if not self.emit(): break
            if self.stop.wait(INTERVAL): break


@contextmanager
def session(action, *, activity=False, stream=None):
    existing = _ACTIVE.get()
    controller = existing or Controller(sys.stderr if stream is None else stream, activity=activity)
    token = _ACTIVE.set(controller)
    previous = None
    cooperative = action in COOPERATIVE and threading.current_thread() is threading.main_thread()
    try:
        if cooperative:
            previous = signal.getsignal(signal.SIGINT)
            signal.signal(signal.SIGINT, controller.request)
        if activity and existing is None:
            controller.thread = threading.Thread(target=controller.heartbeat, daemon=True, name="lks-sdd-activity")
            controller.thread.start()
        yield controller
    finally:
        if existing is None:
            controller.stop.set()
            if controller.thread is not None: controller.thread.join(timeout=0.05)
        if cooperative: signal.signal(signal.SIGINT, previous)
        _ACTIVE.reset(token)


def checkpoint():
    controller = _ACTIVE.get()
    if controller is not None: controller.check()


def phase(name):
    if name not in PHASES: raise ValueError("Unknown activity phase")
    controller = _ACTIVE.get()
    if controller is not None:
        controller.phase = name
        controller.check()


@contextmanager
def defer():
    """Finish the existing durable write, then let its caller retain its receipt."""
    controller = _ACTIVE.get()
    if controller is not None: controller.deferred += 1
    try: yield
    finally:
        if controller is not None: controller.deferred -= 1
