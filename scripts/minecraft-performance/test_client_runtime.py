from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from client_runtime import Client


class ClientRuntimeTests(unittest.TestCase):
    def test_stop_restores_pack_and_controlled_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            instance = root / 'instances/no-dh'
            game = instance / 'minecraft'
            game.mkdir(parents=True)

            pack = instance / 'mmc-pack.json'
            options = game / 'options.txt'

            pack.write_text('prism-mutated-pack\n')
            options.write_text('minecraft-mutated-options\n')

            client = Client.__new__(Client)
            client.active = True
            client.instance = instance
            client.profile = 'no-dh'
            client.identity = {
                'root': str(root),
                'profiles': {
                    'no-dh': {
                        'pack': {
                            'content': 'frozen-pack\n',
                        },
                        'files': {
                            'options.txt': {
                                'content': 'frozen-options\n',
                            },
                        },
                    },
                },
            }

            with (
                patch('client_runtime.command', return_value='not-found'),
                patch(
                    'client_runtime.controlled_path',
                    side_effect=lambda path, *args, **kwargs: Path(path),
                ),
            ):
                client.stop()

            self.assertFalse(client.active)
            self.assertEqual(pack.read_text(), 'frozen-pack\n')
            self.assertEqual(options.read_text(), 'frozen-options\n')


if __name__ == '__main__':
    unittest.main()
