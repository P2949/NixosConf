import unittest

from assemble_functional_acceptance import REQUIRED, qualification_exit_code


class FunctionalExitStatusTests(unittest.TestCase):
    def test_complete_bundle_passes_and_failed_gate_fails(self):
        bundle = {'outcomes': dict.fromkeys(REQUIRED, 'PASS')}
        self.assertEqual(qualification_exit_code(bundle), 0)
        bundle['outcomes']['restore'] = 'FAIL'
        self.assertEqual(qualification_exit_code(bundle), 1)

    def test_missing_unknown_and_inconclusive_outcomes_do_not_pass(self):
        self.assertEqual(qualification_exit_code({}), 2)
        bundle = {'outcomes': dict.fromkeys(REQUIRED, 'PASS')}
        bundle['outcomes']['backup'] = 'INCONCLUSIVE'
        self.assertEqual(qualification_exit_code(bundle), 2)
        bundle['outcomes']['backup'] = 'UNPROVEN'
        self.assertEqual(qualification_exit_code(bundle), 2)
        bundle['outcomes']['backup'] = 'PASS'
        bundle['outcomes']['unexpected'] = 'PASS'
        self.assertEqual(qualification_exit_code(bundle), 2)


if __name__ == '__main__':
    unittest.main()
