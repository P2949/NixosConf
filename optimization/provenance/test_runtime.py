import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
spec=importlib.util.spec_from_file_location('runtime',Path(__file__).with_name('runtime.py'))
runtime=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

class RuntimeContract(unittest.TestCase):
    def fixture(self,root):
        data={'/proc/cpuinfo':'vendor_id: GenuineIntel\ncpu family: 6\nmodel: 165\nstepping: 5\nmicrocode: 0xff', '/proc/sys/kernel/hostname':'fixture','/proc/sys/kernel/random/boot_id':'fixture-boot','/proc/sys/kernel/osrelease':'fixture-kernel','/proc/cmdline':'quiet','/proc/meminfo':'MemTotal: 32','/proc/swaps':'Filename Type Size Used Priority','/proc/sys/kernel/numa_balancing':'0','/sys/kernel/mm/transparent_hugepage/enabled':'always [madvise] never','/sys/devices/system/cpu/online':'0','/sys/devices/system/cpu/smt/active':'1','/sys/class/powercap/intel-rapl:0/name':'package-0','/sys/class/powercap/intel-rapl:0/enabled':'1','/sys/class/powercap/intel-rapl:0/constraint_0_name':'long_term','/sys/class/powercap/intel-rapl:0/constraint_1_name':'short_term','/sys/class/powercap/intel-rapl:0/constraint_0_power_limit_uw':'125000000','/sys/class/powercap/intel-rapl:0/constraint_1_power_limit_uw':'125000000','/sys/class/hwmon/hwmon0/name':'coretemp','/sys/class/hwmon/hwmon0/temp1_input':'85000','/sys/class/hwmon/hwmon0/temp1_crit':'100000','/sys/class/hwmon/hwmon0/temp1_label':'Package id 0','/sys/devices/system/cpu/cpu0/thermal_throttle/package_throttle_count':'0'}
        for key in ('affected_cpus','scaling_driver','scaling_governor','scaling_min_freq','scaling_max_freq','energy_performance_preference'):data['/sys/devices/system/cpu/cpufreq/policy0/'+key]='fixture'
        for name,value in data.items():
            p=root/name.lstrip('/');p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
        (root/'run').mkdir()
        for name in ('current','booted'):(root/'run'/f'{name}-system').symlink_to('/nix/store/fixture-system')
    def snapshot(self,root):return runtime.capture(root,lambda *a,**k:SimpleNamespace(stdout='inactive\n'))
    def test_real_capture_and_required_field_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);before=self.snapshot(root)
            runtime.validate_interval(before,copy.deepcopy(before)) # 85 C is below observed hardware critical.
            (root/'sys/devices/system/cpu/cpufreq/policy0/scaling_governor').unlink()
            with self.assertRaisesRegex(ValueError,'unreadable'):self.snapshot(root)
    def test_control_rejects_switch_without_boot_and_wrong_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);snapshot=self.snapshot(root)
            target={'hostname':'fixture','cpuVendor':'GenuineIntel','cpuFamily':'6','cpuModel':'165'}
            runtime.validate_control(snapshot,'/nix/store/fixture-system',target)
            changed=copy.deepcopy(snapshot);changed['systems']['current']='/nix/store/switched-system'
            with self.assertRaisesRegex(ValueError,'declared control'):
                runtime.validate_control(changed,'/nix/store/switched-system',target)
            with self.assertRaisesRegex(ValueError,'physical target'):
                runtime.validate_control(snapshot,'/nix/store/fixture-system',{**target,'hostname':'other'})

    def test_interval_rejects_identity_policy_throttling_and_maintenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.fixture(root);before=self.snapshot(root)
            for key,value in [('bootId',{'status':'observed','value':'changed'}),('maintenance',{'nix-gc.service':'active'}),('thermalThrottleCounters',{'cpu0/thermal_throttle/package_throttle_count':{'status':'observed','value':1}})]:
                after=copy.deepcopy(before);after[key]=value
                with self.assertRaises(ValueError):runtime.validate_interval(before,after)
            after=copy.deepcopy(before);after['temperatures'][0]['milliCelsius']['value']=100000
            with self.assertRaisesRegex(ValueError,'critical'):runtime.validate_interval(before,after)
            after=copy.deepcopy(before);after['memory']['numaBalancing']['value']='1'
            with self.assertRaisesRegex(ValueError,'memory policy'):runtime.validate_interval(before,after)

if __name__=='__main__':unittest.main()
