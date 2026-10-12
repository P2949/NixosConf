from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

from functional_runtime import Lab, mode_fields
from qualification_manifest import sha256


class MaintenanceModeTests(unittest.TestCase):
    def test_real_policy_install_transitions_preserve_identity_and_restore_normal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            server = root / 'survival'
            (server / 'config').mkdir(parents=True)
            (server / 'config/DistantHorizons.toml').write_text('[server]\nserverId = 42\n')
            inventories = {}
            for mode, names in [('mods', ['c2me']), ('pregen_mods', ['c2me', 'chunky']),
                                ('dh_pregen_mods', ['c2me'])]:
                inventories[mode] = []
                for name in names:
                    jar = root / (mode + '-' + name + '.jar')
                    jar.write_text(name)
                    inventories[mode].append(dict(filename=name + '.jar', path=str(jar), sha256=sha256(jar)))
            def policy(mode, plan):
                return '[server]\nsynchronizeOnLoad = true\n[common.worldGenerator]\n' + \
                       f'chunkGeneratorMode = "{mode}"\ngeneratorPlan = "{plan}"\n'
            lab = Lab.__new__(Lab)
            lab.active = False
            lab.root, lab.server = root, server
            lab.manifest = dict(**inventories,
                policies={'config/DistantHorizons.toml': dict(content=policy('PRE_EXISTING_ONLY', 'CHUNKS_ONLY')),
                          'config/c2me.toml': dict(content='version = 3\nglobalExecutorParallelism = 4\n')},
                pregen_policy=dict(content=policy('PRE_EXISTING_ONLY', 'DISABLED')),
                dh_pregen_policy=dict(content=policy('INTERNAL_SERVER', 'CHUNKS_ONLY')),
                pregen_pause_seconds=-1, dh_pregen_pause_seconds=-1,
                controlled_server_properties={'pause-when-empty-seconds': 60})
            with patch('functional_runtime.subprocess.run'):
                for mode, expected in [('normal', ('PRE_EXISTING_ONLY', 'CHUNKS_ONLY', 60)),
                                       ('chunky', ('PRE_EXISTING_ONLY', 'DISABLED', -1)),
                                       ('normal', ('PRE_EXISTING_ONLY', 'CHUNKS_ONLY', 60)),
                                       ('dh_pregen', ('INTERNAL_SERVER', 'CHUNKS_ONLY', -1)),
                                       ('normal', ('PRE_EXISTING_ONLY', 'CHUNKS_ONLY', 60))]:
                    lab.install(mode=mode)
                    parsed = tomllib.loads((server / 'config/DistantHorizons.toml').read_text())
                    self.assertEqual(parsed['server']['serverId'], 42)
                    self.assertEqual(parsed['common']['worldGenerator'],
                                     dict(chunkGeneratorMode=expected[0], generatorPlan=expected[1]))
                    self.assertIn(f'pause-when-empty-seconds={expected[2]}\n',
                                  (server / 'server.properties').read_text())
                    self.assertEqual(tomllib.loads((server / 'config/c2me.toml').read_text())['globalExecutorParallelism'], 4)
                    self.assertEqual({p.name for p in (server / 'mods').iterdir()},
                                     {'c2me.jar', 'chunky.jar'} if mode == 'chunky' else {'c2me.jar'})
            self.assertEqual((server / 'config/distant-horizons-server-id').read_text(), '42\n')

    def test_ambiguous_mode_rejected(self):
        self.assertEqual(mode_fields(True), mode_fields(mode='chunky'))
        for mode in ('unknown', 'normal', 'dh_pregen'):
            with self.assertRaises(ValueError):
                mode_fields(True, mode)
