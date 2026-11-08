"""Protect experiment attribution, unavailable-feature handling and report honesty."""
import importlib.machinery
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

lab = importlib.machinery.SourceFileLoader('proton_lab', 'scripts/proton-lab').load_module()
FEATURES = json.loads(Path('packages/proton/features.json').read_text())
MANIFEST = {'features': FEATURES}


class ProtonLabTests(unittest.TestCase):
    def test_manifest_rejects_colliding_tools_and_unmeasured_claims(self):
        data = {'tools':{key:{'id':key, 'displayName':key, 'path':'/nix/store/'+key} for key in ['cachyos','cachyosV3','ge','em']},
                'features':{'wayland':{'runtime_status':'NOT_TESTED'}}}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'manifest.json'
            path.write_text(json.dumps(data))
            self.assertEqual(set(lab.load_manifest(path)['tools']), set(data['tools']))
            data['tools']['cachyosV3']['path'] = data['tools']['cachyos']['path']
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                lab.load_manifest(path)
            data['tools']['cachyosV3']['path'] = '/nix/store/distinct-v3'
            data['features']['wayland']['runtime_status'] = 'PASS'
            path.write_text(json.dumps(data))
            with self.assertRaises(ValueError):
                lab.load_manifest(path)

    def test_isolated_latency_cases(self):
        dxvk = lab.select_case(MANIFEST, 'cachyos', 'dxvk-lowlatency')
        vkd3d = lab.select_case(MANIFEST, 'cachyos', 'vkd3d-lowlatency')
        self.assertEqual(dxvk, {'PROTON_DXVK_LOWLATENCY': '1'})
        self.assertNotIn('PROTON_DXVK_LOWLATENCY', vkd3d)
        self.assertNotEqual(lab.select_case(MANIFEST, 'cachyos', 'dxvk'), dxvk)

    def test_wrong_fork_and_unavailable_features_rejected(self):
        for fork, case in [('ge','dxvk-lowlatency'),('em','nvidia'),('cachyos','zluda'),('cachyos','mlfg-cachyos')]:
            with self.assertRaises(ValueError):
                lab.select_case(MANIFEST, fork, case)

    def test_inherited_experiments_do_not_contaminate_baseline(self):
        env = {'PATH':'/bin', 'WAYLAND_DISPLAY':'wayland-1', 'DISPLAY':':0',
               'PROTON_ENABLE_WAYLAND':'1', 'DXVK_HDR':'1', 'MLFG_UPGRADE':'1',
               'WINE_FULLSCREEN_FSR':'1', 'DXIL_SPIRV_CONFIG':'wmma_rdna3_workaround'}
        self.assertEqual(lab.clean_environment(env), {'PATH':'/bin','WAYLAND_DISPLAY':'wayland-1','DISPLAY':':0'})

    def test_runtime_copy_preserves_steam_and_freezes_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root/'.local/share/Steam/steamapps/common/SteamLinuxRuntime_4'
            source.mkdir(parents=True)
            (source/'toolmanifest.vdf').write_text('runtime')
            (source/'VERSIONS.txt').write_text('runtime-version-123')
            tool = root/'proton'; tool.mkdir()
            (tool/'toolmanifest.vdf').write_text('"require_tool_appid" "4183110"')
            with mock.patch.object(lab.Path, 'home', return_value=root), mock.patch.object(lab, 'ROOT', root/'workspace'):
                env, identity = lab.prepare_runtime({'path':str(tool)})
            self.assertEqual(env['UMU_RUNTIME_UPDATE'], '0')
            self.assertEqual(identity['versions'], 'runtime-version-123')
            self.assertFalse((source/'umu').exists())
            dest = Path(identity['path'])
            self.assertTrue((dest/'umu').is_symlink())
            (dest/'VERSIONS.txt').write_text('changed private copy')
            self.assertEqual((source/'VERSIONS.txt').read_text(), 'runtime-version-123')

    def test_launch_results_do_not_imply_feature_success(self):
        self.assertEqual(lab.classify(0, False), 'PASS')
        self.assertEqual(lab.classify(0, True), 'INCONCLUSIVE')
        self.assertEqual(lab.classify(None, False), 'FAIL')
        self.assertTrue(all(f['runtime_status']=='NOT_TESTED' for f in FEATURES.values()))
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/'sample').mkdir()
            record={'id':'sample','fork':'em','case':'hdr','launch_status':'PASS','feature_status':'NOT_TESTED','exit_code':0,'duration_seconds':1}
            (root/'sample/run.json').write_text(json.dumps(record))
            lab.report(root)
            self.assertIn('| PASS | NOT_TESTED |', (root/'summary.md').read_text())


if __name__ == '__main__':
    unittest.main()
