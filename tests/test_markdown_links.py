import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('checker', Path(__file__).parents[1] / 'scripts/check-markdown-links.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class MarkdownLinks(unittest.TestCase):
    def test_rendered_local_targets_and_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs').mkdir()
            (root / 'docs/a b.md').write_text('# Present')
            (root / 'README.md').write_text('''[ok](docs/a%20b.md#heading)
[absolute](/docs/a%20b.md)
[external](https://invalid.example/no-network)
[heading](#heading)
`[example](missing.md)`
```markdown
[example](missing.md)
```
![broken](image.png)
[reference]: docs/missing.md
''')
            errors = checker.check(root)
            self.assertEqual(len(errors), 2)
            self.assertTrue(any('image.png' in error for error in errors))
            self.assertTrue(any('docs/missing.md' in error for error in errors))

    def test_relative_paths_and_repository_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'docs').mkdir()
            (root / 'README.md').write_text('# Index')
            (root / 'docs/index.md').write_text('[ok](../README.md)\n[escape](../../outside.md)')
            self.assertEqual(len(checker.check(root)), 1)
            self.assertIn('outside repository', checker.check(root)[0])


if __name__ == '__main__':
    unittest.main()
