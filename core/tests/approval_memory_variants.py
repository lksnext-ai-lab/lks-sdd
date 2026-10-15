"""Independent, reproducible experiments over the immutable rc.3 package.

Variants are temporary development payloads, never installed or registered.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
import tempfile

from approval_performance_support import ROOT
from approval_cli_support import core_files

BASELINE = ROOT / 'tests/reports/lks-sdd-3.4.3-rc.3-development/lks-sdd-plugin-v3.4.3-rc.3.zip'
BASELINE_SHA = '85c9eeda1df605028b3f32a49bad063482fb38ffe29d4c943b7b4bde4a23eff4'
VARIANTS = ('rc3', 'slots', 'uid', 'combined')


def transform(source, variant):
    assert variant in VARIANTS
    if variant in ('slots', 'combined'):
        assert source.count('@dataclass(init=False)\nclass Element:') == 1
        source = source.replace('@dataclass(init=False)\nclass Element:',
                                '@dataclass(init=False, slots=True, weakref_slot=True)\nclass Element:')
    if variant in ('uid', 'combined'):
        start = source.index('    def _index_identities(self):')
        end = source.index('    def require_valid(self):', start)
        source = source[:start] + '''    def _index_identities(self):
        if self._identities is not None: return
        identities, kinds = {}, {}
        canonical_keys = all(key == e.uid for key, e in self.elements.items())
        for e in self.elements.values():
            # Canonical UID keys already live in elements. Alias entries include
            # any collision with that table, so get can retain one lookup for
            # aliases and reject ambiguity before the UID fallback.
            keys = (e.id,) if canonical_keys else {e.uid, e.id}
            for key in keys:
                previous = identities.get(key)
                if previous is None and canonical_keys:
                    previous = self.elements.get(key)
                    if previous is e: previous = None
                identities[key] = e if previous is None else (*previous, e) if isinstance(previous, tuple) else (previous, e)
            kinds.setdefault(e.kind, []).append(e)
        self._canonical_identity_keys = canonical_keys
        self._kinds, self._identities = kinds, identities

''' + source[end:]
        old = '        try: found = self._identities.get(identifier)\n'
        assert source.count(old) == 1
        source = source.replace(old, '''        try:
            found = self._identities.get(identifier)
            if found is None and self._canonical_identity_keys:
                found = self.elements.get(identifier)
''')
    return source


def files(variant, package=None):
    if variant == 'candidate':
        assert package is not None
        return core_files('candidate', package)
    assert hashlib.sha256(BASELINE.read_bytes()).hexdigest() == BASELINE_SHA
    result = core_files('rc3', BASELINE)
    result['scripts/v3_contract.py'] = transform(result['scripts/v3_contract.py'].decode(), variant).encode()
    if variant != 'rc3':
        sys.path.insert(0, str(ROOT / 'scripts'))
        from build_candidate_package import _package_integrity_bytes
        result['package-integrity.json'] = _package_integrity_bytes(
            [(k,v) for k,v in result.items() if k != 'package-integrity.json'], '3.4.3-rc.3', 'memory-experiment-' + variant)
    return result


@contextmanager
def runtime(variant, package=None):
    assert 'v3_contract' not in sys.modules
    with tempfile.TemporaryDirectory(prefix='approval-memory-runtime-') as temporary:
        root = Path(temporary)
        for name, raw in files(variant, package).items():
            if name.startswith(('scripts/', 'schemas/', 'specs/', 'docs/')):
                path = root / name
                assert path.resolve().is_relative_to(root.resolve())
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
        sys.path.insert(0, str(root / 'scripts'))
        import v3_contract
        assert Path(v3_contract.__file__).is_relative_to(root)
        yield


def source_binding():
    return {name: hashlib.sha256(files(name)['scripts/v3_contract.py']).hexdigest() for name in VARIANTS}
