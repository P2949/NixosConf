from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from functional_runtime import Lab


class FunctionalLifecycleTests(unittest.TestCase):
    def test_identity_failure_still_removes_owned_slice(self):
        lab = Lab.__new__(Lab)
        lab.active = True
        lab.owns_slice = True
        lab.server = Path('/persist/private-clone/survival')
        with patch('functional_runtime.command', return_value='not-found'), \
             patch('functional_runtime.identity_helper') as helper, \
             patch('functional_runtime.maintenance.cleanup_slice') as cleanup:
            helper.return_value.capture.side_effect = ValueError('identity drift')
            with self.assertRaises(ValueError):
                lab.stop()
            cleanup.assert_called_once()
            self.assertFalse(lab.active)
            self.assertFalse(lab.owns_slice)

    def test_occupied_slice_and_service_never_replace_policy(self):
        lab = Lab.__new__(Lab)
        with patch('functional_runtime.command', return_value='loaded'), \
             patch.object(lab, 'install') as install:
            with self.assertRaises(RuntimeError):
                lab.start()
            install.assert_not_called()


if __name__ == '__main__':
    unittest.main()
