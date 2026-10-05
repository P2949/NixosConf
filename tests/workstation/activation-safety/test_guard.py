"""Hardware-free refusal tests; command fixtures never mount a real device."""
import os
import subprocess
import shutil
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    binaries = root / "bin"
    binaries.mkdir()
    device = root / "device"
    device.touch()
    boot_device = root / "boot-device"
    boot_device.touch()
    secret = root / "password-hash"
    secret.write_text("test-only")
    secret.chmod(0o600)
    source = Path(os.environ["GUARD_SOURCE"]).read_text()
    script = root / "guard.sh"
    script.write_text(f'''expected_device={device}
expected_boot_device={boot_device}
secret_file={secret}
root_name=@root
next_name=@root-next
persist_name=@persist
allowed_descendants=(tmp srv)
esp_reserve=268435456
''' + source)
    fixtures = {
        "findmnt": r'''target=$3
field=$5
[[ "$STATE" != missing-mount ]] || exit 1
case "$field" in
 SOURCE) if [[ "$STATE" == wrong-device ]]; then echo /nonexistent; elif [[ "$target" == /boot ]]; then echo "$BOOT_DEVICE"; else echo "$DEVICE"; fi ;;
 FSTYPE) if [[ "$STATE" == wrong-fs ]]; then echo ext4; elif [[ "$target" == /boot ]]; then echo vfat; else echo btrfs; fi ;;
 FSROOT) if [[ "$STATE" == wrong-subvolume ]]; then echo /@wrong; elif [[ "$target" == /persist ]]; then echo /@persist; else echo /@root; fi ;;
 OPTIONS) if [[ "$STATE" == read-only ]]; then echo ro; else echo rw; fi ;;
esac
''',
        "df": r'''echo Avail
if [[ "$STATE" == full-esp ]]; then echo 1; else echo 536870912; fi
''',
        "stat": r'''case "$2" in
 %u) if [[ "$STATE" == wrong-owner ]]; then echo 1000; else echo 0; fi ;;
 *) exec "$REAL_STAT" "$@" ;;
esac
''',
        "mount": r'''top=${@: -1}
mkdir "$top/@root" "$top/@persist"
if [[ "$STATE" == staging-file ]]; then touch "$top/@root-next"; fi
if [[ "$STATE" == staging-nonempty ]]; then mkdir "$top/@root-next"; touch "$top/@root-next/.hidden"; fi
if [[ "$STATE" == staging-link ]]; then ln -s "$top/@root" "$top/@root-next"; fi
''',
        "mountpoint": "exit 0\n",
        "umount": r'''# Only remove fixture files within this test's generated temporary directory.
[[ "$1" == "$TMPDIR"/nixos-activation-topology.* ]] || exit 1
rm -rf -- "$1/@root" "$1/@persist" "$1/@root-next"
''',
        "btrfs": r'''if [[ "$2" == show ]]; then
 [[ -d "$3" && "$STATE" != invalid-subvolume ]] || exit 1
elif [[ "$2" == list ]]; then
 [[ "$STATE" != inspection-failure ]] || exit 1
 if [[ "$4" == */@root ]]; then
  case "$STATE" in
   unknown-child) echo 'ID 1 gen 1 top level 5 path @root/unique' ;;
   malformed) echo 'unparseable' ;;
   nested-child|nested-inspection-failure) echo 'ID 1 gen 1 top level 5 path @root/tmp' ;;
  esac
 elif [[ "$STATE" == nested-child ]]; then echo 'ID 2 gen 1 top level 5 path @root/tmp/unique'
 elif [[ "$STATE" == nested-inspection-failure ]]; then exit 1
 fi
fi
''',
    }
    real_stat = shutil.which("stat")
    for name, body in fixtures.items():
        path = binaries / name
        path.write_text("#!" + shutil.which("bash") + "\nset -eu\n" + body)
        path.chmod(0o755)
    env = dict(os.environ, PATH=str(binaries) + ":" + os.environ["PATH"],
               DEVICE=str(device), BOOT_DEVICE=str(boot_device), REAL_STAT=real_stat,
               TMPDIR=str(root))

    def check(role, state, expected, action="switch"):
        result = subprocess.run(["bash", str(script), role, "/test-system", action],
                                env=dict(env, STATE=state), capture_output=True, text=True)
        assert (result.returncode == 0) == expected, (role, state, result.stderr)
        if not expected:
            assert f"Activation safety ({role}):" in result.stderr, result.stderr

    count = 0
    for action in ("switch", "boot", "test", "dry-activate"):
        for role in ("persistence", "credentials", "esp", "topology"):
            check(role, "valid", True, action)
            count += 1
    for role in ("persistence", "esp", "topology"):
        for state in ("missing-mount", "wrong-device", "wrong-fs", "read-only"):
            check(role, state, False)
            count += 1
    for role in ("persistence", "topology"):
        check(role, "wrong-subvolume", False)
        count += 1
    for state in ("invalid-subvolume", "staging-file", "staging-nonempty", "staging-link",
                  "inspection-failure", "unknown-child", "malformed", "nested-child",
                  "nested-inspection-failure"):
        check("topology", state, False)
        count += 1
    check("esp", "full-esp", False)
    check("credentials", "wrong-owner", False)
    secret.chmod(0o644)
    check("credentials", "valid", False)
    secret.chmod(0o600)
    secret.write_text("")
    check("credentials", "valid", False)
    secret.unlink()
    secret.symlink_to(device)
    check("credentials", "valid", False)
    secret.unlink()
    secret.write_text("test-only")
    secret.chmod(0o600)
    os.link(secret, root / "hash-alias")
    check("credentials", "valid", False)
    print(f"Activation fixtures: {count + 6} cases passed; native action dispatch still requires VM acceptance")
