import unittest

from c2me_runtime import SHA256, VERSION, verify_startup


class ExecutorAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.mods = [{'id': 'c2me', 'version': VERSION, 'sha256': SHA256}]
        self.policy = 'version = 3\nglobalExecutorParallelism = 4\n'
        self.log = 'Global Executor Parallelism: 4 configured, 6 evaluated, 6 default evaluated'

    def test_exact_pinned_runtime(self):
        self.assertEqual(verify_startup(self.mods, self.policy, self.log)
                         ['effective_global_executor_parallelism'], 4)

    def test_rejects_missing_default_wrong_and_conflicting_startup(self):
        for log in ('', self.log.replace('4 configured', '6 configured'),
                    self.log + '\nGlobal Executor Parallelism: 3 configured,',
                    self.log + '\nConfig version mismatch, resetting config'):
            with self.subTest(log=log), self.assertRaises(RuntimeError):
                verify_startup(self.mods, self.policy, log)

    def test_rejects_wrong_artifact_and_policy(self):
        for mods in (self.mods * 2, [{'id': 'c2me', 'version': VERSION, 'sha256': 'bad'}]):
            with self.assertRaises(RuntimeError):
                verify_startup(mods, self.policy, self.log)
        for policy in ('globalExecutorParallelism = 4',
                       self.policy.replace('= 4', '= 3')):
            with self.assertRaises(RuntimeError):
                verify_startup(self.mods, policy, self.log)

    def test_without_c2me(self):
        self.assertIsNone(verify_startup([], '', ''))


if __name__ == '__main__':
    unittest.main()
