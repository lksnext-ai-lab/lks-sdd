"""Fresh source observations remain authoritative after load optimizations."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from v2_contract import ContractError, read_bytes
import source_inventory


class LoadRegressionTests(unittest.TestCase):
    def test_replacement_between_observation_and_read_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'source.py'; source.write_bytes(b'before')
            replacement = root/'replacement.py'; replacement.write_bytes(b'after!')
            original = source_inventory.read
            def swap(entry, **kwargs):
                replacement.replace(source)
                return original(entry, **kwargs)
            with patch.object(source_inventory,'read',side_effect=swap):
                with self.assertRaisesRegex(ContractError,'Source changed'):
                    read_bytes(root,'source.py')

    def test_growth_between_observation_and_read_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root/'source.py'; source.write_bytes(b'before')
            original = source_inventory.read
            def grow(entry, **kwargs):
                with source.open('ab') as output: output.write(b'growth')
                return original(entry, **kwargs)
            with patch.object(source_inventory,'read',side_effect=grow):
                with self.assertRaisesRegex(ContractError,'Source changed'):
                    read_bytes(root,'source.py')

    def test_permission_failure_is_not_replaced_by_success_or_empty_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root/'source.py').write_bytes(b'before')
            failure = PermissionError('synthetic inaccessible source')
            with patch.object(source_inventory,'read',side_effect=failure):
                with self.assertRaises(PermissionError) as caught: read_bytes(root,'source.py')
            self.assertIs(failure,caught.exception)


if __name__ == '__main__': unittest.main()
