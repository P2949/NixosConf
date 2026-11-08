"""Protect experiment attribution, unavailable-feature handling and report honesty."""
import importlib.machinery
import json
from pathlib import Path
import tempfile
import unittest

lab = importlib.machinery.SourceFileLoader('proton_lab', 'scripts/proton-lab').load_module()
FEATURES = json.loads(Path('packages/proton/features.json').read_text())
MANIFEST = {'features': FEATURES}


class ProtonLabTests(unittest.TestCase):
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
