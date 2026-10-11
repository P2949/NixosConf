import json
from pathlib import Path
import re
import unittest


HERE = Path(__file__).parent
PROBE = HERE / 'probe'


def java_package(filename):
    text = (PROBE / filename).read_text()
    match = re.search(r'^package\s+([A-Za-z0-9_.]+);', text, re.MULTILINE)
    if match is None:
        raise ValueError('Java package declaration missing: ' + filename)
    return match.group(1)


class ProbeLayoutTests(unittest.TestCase):
    def test_runtime_helpers_are_outside_mixin_owned_packages(self):
        cases = (
            (
                'performance-client.mixins.json',
                'ClientProbeMixin.java',
                'FrameBuffer.java',
            ),
            (
                'performance-server.mixins.json',
                'ServerTickProbeMixin.java',
                'TickBuffer.java',
            ),
        )

        for config_name, mixin_source, helper_source in cases:
            with self.subTest(config=config_name):
                config = json.loads((PROBE / config_name).read_text())
                mixin_package = config['package']

                self.assertEqual(
                    java_package(mixin_source),
                    mixin_package,
                )

                helper_package = java_package(helper_source)

                self.assertNotEqual(helper_package, mixin_package)
                self.assertFalse(
                    helper_package.startswith(mixin_package + '.'),
                    msg=(
                        f'{helper_source} is inside Mixin-owned package '
                        f'{mixin_package}'
                    ),
                )


if __name__ == '__main__':
    unittest.main()
