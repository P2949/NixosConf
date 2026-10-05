# Workstation preparation snapshot

Captured: 2026-10-05T03:01:43Z

This is observed runtime state, not final acceptance or an idle/load test.

## Git identity

```text
91756e51518fcbd028fb8e11bc41b877ff6a253f Record published validation and experimental cleanliness evidence

[exit=0]
```

## Git tags

```text

[exit=0]
```

## Working tree

```text
 M README.md
A  docs/baseline-capture.md
 M flake.nix
 M plan.md
AM scripts/nixos-baseline-info.sh

[exit=0]
```

## Collector source identity

```text
fb9e65bc705da9418c2004ada3bfe477527f836c7306fdc509e297b741bb809f  scripts/nixos-baseline-info.sh

[exit=0]
```

## Lock identity

```text
340955c7076c300ea74fa32935527522feeef3eddd2d4649663650c7ee668a6d  flake.lock

[exit=0]
```

## Pinned nixpkgs revision

```text
774debe7a0d1b496e35677ad955a1011c6ff74f3

[exit=0]
```

## Nix version

```text
nix (Nix) 2.34.8

[exit=0]
```

## NixOS version

```text
26.05.20261002.774debe (Yarara)

[exit=0]
```

## Running closure

```text
/nix/store/jj4h7abqachf769dpz308v480a6srdbs-nixos-system-desktop-26.05.20261002.774debe

[exit=0]
```

## Running derivation

```text
/nix/store/vqjffmw5m9hd5g447bkvjpkkszax1mf9-nixos-system-desktop-26.05.20261002.774debe.drv

[exit=0]
```

## Running closure size

```text
/nix/store/jj4h7abqachf769dpz308v480a6srdbs-nixos-system-desktop-26.05.20261002.774debe	17138090256

[exit=0]
```

## CPU topology

```text
Architecture:                            x86_64
CPU op-mode(s):                          32-bit, 64-bit
Address sizes:                           39 bits physical, 48 bits virtual
Byte Order:                              Little Endian
CPU(s):                                  12
On-line CPU(s) list:                     0-11
Vendor ID:                               GenuineIntel
Model name:                              Intel(R) Core(TM) i5-10600K CPU @ 4.10GHz
CPU family:                              6
Model:                                   165
Thread(s) per core:                      2
Core(s) per socket:                      6
Socket(s):                               1
Stepping:                                5
Microcode version:                       0x100
CPU(s) scaling MHz:                      98%
CPU max MHz:                             5000.0000
CPU min MHz:                             800.0000
BogoMIPS:                                8199.79
Flags:                                   fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb ssbd ibrs ibpb stibp ibrs_enhanced fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid mpx rdseed adx smap clflushopt intel_pt xsaveopt xsavec xgetbv1 xsaves dtherm ida arat pln pts hwp hwp_notify hwp_act_window hwp_epp pku ospke md_clear flush_l1d arch_capabilities
L1d cache:                               192 KiB (6 instances)
L1i cache:                               192 KiB (6 instances)
L2 cache:                                1.5 MiB (6 instances)
L3 cache:                                12 MiB (1 instance)
NUMA node(s):                            1
NUMA node0 CPU(s):                       0-11
Vulnerability Gather data sampling:      Mitigation; Microcode
Vulnerability Ghostwrite:                Not affected
Vulnerability Indirect target selection: Mitigation; Aligned branch/return thunks
Vulnerability Itlb multihit:             KVM: Mitigation: VMX unsupported
Vulnerability L1tf:                      Not affected
Vulnerability Mds:                       Not affected
Vulnerability Meltdown:                  Not affected
Vulnerability Mmio stale data:           Mitigation; Clear CPU buffers; SMT vulnerable
Vulnerability Old microcode:             Not affected
Vulnerability Reg file data sampling:    Not affected
Vulnerability Retbleed:                  Mitigation; Enhanced IBRS
Vulnerability Spec rstack overflow:      Not affected
Vulnerability Spec store bypass:         Mitigation; Speculative Store Bypass disabled via prctl
Vulnerability Spectre v1:                Mitigation; usercopy/swapgs barriers and __user pointer sanitization
Vulnerability Spectre v2:                Mitigation; Enhanced / Automatic IBRS; IBPB conditional; PBRSB-eIBRS SW sequence; BHI SW loop, KVM SW loop
Vulnerability Srbds:                     Mitigation; Microcode
Vulnerability Tsa:                       Not affected
Vulnerability Tsx async abort:           Not affected
Vulnerability Vmscape:                   Mitigation; IBPB before exit to userspace

[exit=0]
```

## Microcode

```text
microcode	: 0x100

[exit=0]
```

## CPU online and SMT

```text
/sys/devices/system/cpu/online: 0-11
/sys/devices/system/cpu/smt/active: 1

[exit=0]
```

## CPU policies

```text
/sys/devices/system/cpu/cpufreq/policy0/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy0/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy0/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy1/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy1/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy1/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy10/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy10/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy10/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy11/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy11/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy11/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy2/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy2/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy2/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy3/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy3/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy3/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy4/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy4/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy4/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy5/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy5/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy5/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy6/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy6/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy6/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy7/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy7/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy7/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy8/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy8/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy8/energy_performance_preference: balance_performance
/sys/devices/system/cpu/cpufreq/policy9/scaling_driver: intel_pstate
/sys/devices/system/cpu/cpufreq/policy9/scaling_governor: powersave
/sys/devices/system/cpu/cpufreq/policy9/energy_performance_preference: balance_performance

[exit=0]
```

## Kernel command line

```text
initrd=\EFI\nixos\660303b2n94h6zrb3qfpzfpxbhjpyl8v-initrd-linux-6.18.54-initrd.efi init=/nix/store/jj4h7abqachf769dpz308v480a6srdbs-nixos-system-desktop-26.05.20261002.774debe/init root=fstab loglevel=4 lsm=landlock,yama,bpf

[exit=0]
```

## BIOS

```text
bios_version: 3201
bios_date: 11/20/2024

[exit=0]
```

ME version: not collected; firmware decision remains a separate gate.

## Memory

```text
               total        used        free      shared  buff/cache   available
Mem:            31Gi       3.1Gi        21Gi        20Mi       7.0Gi        28Gi
Swap:           31Gi          0B        31Gi

[exit=0]
```

## Swap

```text
NAME           TYPE      SIZE USED PRIO
/dev/nvme0n1p2 partition  32G   0B   -2

[exit=0]
```

## ZRAM

```text

[exit=0]
```

## Transparent huge pages

```text
always [madvise] never

[exit=0]
```

## PCI devices and drivers

```text
00:00.0 Host bridge [0600]: Intel Corporation Comet Lake-S 6c Host Bridge/DRAM Controller [8086:9b53] (rev 05)
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: skl_uncore
00:01.0 PCI bridge [0604]: Intel Corporation 6th-10th Gen Core Processor PCIe Controller (x16) [8086:1901] (rev 05)
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: pcieport
00:14.0 USB controller [0c03]: Intel Corporation Comet Lake USB 3.1 xHCI Host Controller [8086:06ed]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: xhci_hcd
	Kernel modules: xhci_pci
00:14.2 RAM memory [0500]: Intel Corporation Comet Lake PCH Shared SRAM [8086:06ef]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
00:14.3 Network controller [0280]: Intel Corporation Comet Lake PCH CNVi WiFi [8086:06f0]
	DeviceName: Onboard - Ethernet
	Subsystem: Intel Corporation Dual Band Wi-Fi 6(802.11ax) AX201 160MHz 2x2 [Harrison Peak] [8086:0074]
	Kernel driver in use: iwlwifi
	Kernel modules: iwlwifi
00:15.0 Serial bus controller [0c80]: Intel Corporation Comet Lake PCH Serial IO I2C Controller #0 [8086:06e8]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: intel-lpss
	Kernel modules: intel_lpss_pci
00:15.1 Serial bus controller [0c80]: Intel Corporation Comet Lake PCH Serial IO I2C Controller #1 [8086:06e9]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: intel-lpss
	Kernel modules: intel_lpss_pci
00:16.0 Communication controller [0780]: Intel Corporation Comet Lake HECI Controller [8086:06e0]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: mei_me
	Kernel modules: mei_me
00:17.0 SATA controller [0106]: Intel Corporation Comet Lake SATA AHCI Controller [8086:06d2]
	DeviceName: Onboard - SATA
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: ahci
	Kernel modules: ahci
00:1b.0 PCI bridge [0604]: Intel Corporation Comet Lake PCI Express Root Port #17 [8086:06c0] (rev f0)
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: pcieport
00:1c.0 PCI bridge [0604]: Intel Corporation Comet Lake PCIe Root Port #1 [8086:06b8] (rev f0)
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: pcieport
00:1c.4 PCI bridge [0604]: Intel Corporation Device [8086:06bc] (rev f0)
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: pcieport
00:1d.0 PCI bridge [0604]: Intel Corporation Comet Lake PCI Express Root Port #9 [8086:06b0] (rev f0)
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: pcieport
00:1f.0 ISA bridge [0601]: Intel Corporation Z490 Chipset LPC/eSPI Controller [8086:0685]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
00:1f.3 Audio device [0403]: Intel Corporation Comet Lake PCH cAVS [8086:06c8]
	DeviceName: Onboard - Sound
	Subsystem: ASUSTeK Computer Inc. Device [1043:87c5]
	Kernel driver in use: snd_hda_intel
	Kernel modules: snd_soc_avs, snd_sof_pci_intel_cnl, snd_hda_intel
00:1f.4 SMBus [0c05]: Intel Corporation Comet Lake PCH SMBus Controller [8086:06a3]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: i801_smbus
	Kernel modules: i2c_i801
00:1f.5 Serial bus controller [0c80]: Intel Corporation Comet Lake PCH SPI Controller [8086:06a4]
	DeviceName: Onboard - Other
	Subsystem: ASUSTeK Computer Inc. Device [1043:8694]
	Kernel driver in use: intel-spi
	Kernel modules: spi_intel_pci
01:00.0 PCI bridge [0604]: Advanced Micro Devices, Inc. [AMD/ATI] Navi 10 XL Upstream Port of PCI Express Switch [1002:1478] (rev 24)
	Subsystem: Acer Incorporated [ALI] Device [1025:1478]
	Kernel driver in use: pcieport
02:00.0 PCI bridge [0604]: Advanced Micro Devices, Inc. [AMD/ATI] Navi 10 XL Downstream Port of PCI Express Switch [1002:1479] (rev 24)
	Subsystem: Advanced Micro Devices, Inc. [AMD/ATI] Navi 10 XL Downstream Port of PCI Express Switch [1002:1479]
	Kernel driver in use: pcieport
03:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. [AMD/ATI] Navi 48 [Radeon RX 9070/9070 XT/9070 GRE] [1002:7550] (rev c0)
	Subsystem: Acer Incorporated [ALI] Device [1025:187a]
	Kernel driver in use: amdgpu
	Kernel modules: amdgpu
03:00.1 Audio device [0403]: Advanced Micro Devices, Inc. [AMD/ATI] Navi 48 HDMI/DP Audio Controller [1002:ab40]
	Subsystem: Advanced Micro Devices, Inc. [AMD/ATI] Navi 48 HDMI/DP Audio Controller [1002:ab40]
	Kernel driver in use: snd_hda_intel
	Kernel modules: snd_hda_intel
06:00.0 Ethernet controller [0200]: Intel Corporation Ethernet Controller I225-V [8086:15f3] (rev 02)
	Subsystem: ASUSTeK Computer Inc. Device [1043:87d2]
	Kernel driver in use: igc
	Kernel modules: igc
07:00.0 Non-Volatile memory controller [0108]: Phison Electronics Corporation E16 PCIe4 NVMe Controller [1987:5016] (rev 01)
	Subsystem: Phison Electronics Corporation E16 PCIe4 NVMe Controller [1987:5016]
	Kernel driver in use: nvme
	Kernel modules: nvme

[exit=0]
```

## Vulkan summary

```text
WARNING: [Loader Message] Code 0 : terminator_CreateInstance: Received return code -9 from call to vkCreateInstance in ICD /nix/store/fdw09ayics8bwzb6k7vr8kfgmwmv35h5-mesa-26.1.8/lib/libvulkan_dzn.so. Skipping this driver.
WARNING: radv is not a conformant Vulkan implementation, testing use only.
WARNING: [Loader Message] Code 0 : ICD for selected physical device does not export vkGetPhysicalDeviceDisplayPlanePropertiesKHR!
WARNING: [Loader Message] Code 0 : ICD for selected physical device does not export vkGetPhysicalDeviceDisplayPropertiesKHR!
==========
VULKANINFO
==========

Vulkan Instance Version: 1.4.341


Instance Extensions: count = 26
-------------------------------
VK_EXT_acquire_drm_display             : extension revision 1
VK_EXT_acquire_xlib_display            : extension revision 1
VK_EXT_debug_report                    : extension revision 10
VK_EXT_debug_utils                     : extension revision 2
VK_EXT_direct_mode_display             : extension revision 1
VK_EXT_display_surface_counter         : extension revision 1
VK_EXT_headless_surface                : extension revision 1
VK_EXT_layer_settings                  : extension revision 2
VK_EXT_surface_maintenance1            : extension revision 1
VK_EXT_swapchain_colorspace            : extension revision 5
VK_KHR_device_group_creation           : extension revision 1
VK_KHR_display                         : extension revision 23
VK_KHR_external_fence_capabilities     : extension revision 1
VK_KHR_external_memory_capabilities    : extension revision 1
VK_KHR_external_semaphore_capabilities : extension revision 1
VK_KHR_get_display_properties2         : extension revision 1
VK_KHR_get_physical_device_properties2 : extension revision 2
VK_KHR_get_surface_capabilities2       : extension revision 1
VK_KHR_portability_enumeration         : extension revision 1
VK_KHR_surface                         : extension revision 25
VK_KHR_surface_maintenance1            : extension revision 1
VK_KHR_surface_protected_capabilities  : extension revision 1
VK_KHR_wayland_surface                 : extension revision 6
VK_KHR_xcb_surface                     : extension revision 6
VK_KHR_xlib_surface                    : extension revision 6
VK_LUNARG_direct_driver_loading        : extension revision 1

Instance Layers: count = 12
---------------------------
VK_LAYER_INTEL_nullhw               INTEL NULL HW                                                1.1.73   version 1
VK_LAYER_MANGOHUD_overlay_32_x86    Vulkan Hud Overlay                                           1.3.0    version 1
VK_LAYER_MANGOHUD_overlay_64_x86_64 Vulkan Hud Overlay                                           1.3.0    version 1
VK_LAYER_MESA_anti_lag              Open-source implementation of the VK_AMD_anti_lag extension. 1.4.303  version 1
VK_LAYER_MESA_device_select         Linux device selection layer                                 1.4.303  version 1
VK_LAYER_MESA_overlay               Mesa Overlay layer                                           1.4.303  version 1
VK_LAYER_MESA_screenshot            Mesa Screenshot layer                                        1.4.303  version 1
VK_LAYER_MESA_vram_report_limit     Limit reported VRAM                                          1.4.303  version 1
VK_LAYER_VALVE_steam_fossilize_32   Steam Pipeline Caching Layer                                 1.3.207  version 1
VK_LAYER_VALVE_steam_fossilize_64   Steam Pipeline Caching Layer                                 1.3.207  version 1
VK_LAYER_VALVE_steam_overlay_32     Steam Overlay Layer                                          1.3.207  version 1
VK_LAYER_VALVE_steam_overlay_64     Steam Overlay Layer                                          1.3.207  version 1

Devices:
========
GPU0:
	apiVersion         = 1.4.354
	driverVersion      = 26.1.8
	vendorID           = 0x1002
	deviceID           = 0x7550
	deviceType         = PHYSICAL_DEVICE_TYPE_DISCRETE_GPU
	deviceName         = AMD Radeon RX 9070 XT (RADV GFX1201)
	driverID           = DRIVER_ID_MESA_RADV
	driverName         = radv
	driverInfo         = Mesa 26.1.8
	conformanceVersion = 1.4.0.0
	deviceUUID         = 00000000-0300-0000-0000-000000000000
	driverUUID         = 414d442d-4d45-5341-2d44-525600000000
GPU1:
	apiVersion         = 1.4.354
	driverVersion      = 26.1.8
	vendorID           = 0x10005
	deviceID           = 0x0000
	deviceType         = PHYSICAL_DEVICE_TYPE_CPU
	deviceName         = llvmpipe (LLVM 21.1.8, 256 bits)
	driverID           = DRIVER_ID_MESA_LLVMPIPE
	driverName         = llvmpipe
	driverInfo         = Mesa 26.1.8 (LLVM 21.1.8)
	conformanceVersion = 1.3.1.1
	deviceUUID         = 6d657361-3236-2e31-2e38-000000000000
	driverUUID         = 6c6c766d-7069-7065-5555-494400000000

[exit=0]
```

## OpenGL version (current display)

```text
name of display: :0
display: :0  screen: 0
direct rendering: Yes
Extended renderer info (GLX_MESA_query_renderer):
    Vendor: AMD (0x1002)
    Device: AMD Radeon RX 9070 XT (radeonsi, gfx1201, ACO, DRM 3.64, 6.18.54) (0x7550)
    Version: 26.1.8
    Accelerated: yes
    Video memory: 16384MB
    Unified memory: no
    Preferred profile: core (0x1)
    Max core profile version: 4.6
    Max compat profile version: 4.6
    Max GLES1 profile version: 1.1
    Max GLES[23] profile version: 3.2
Memory info (GL_ATI_meminfo):
    VBO free memory - total: 15793 MB, largest block: 15793 MB
    VBO free aux. memory - total: 15936 MB, largest block: 15936 MB
    Texture free memory - total: 15793 MB, largest block: 15793 MB
    Texture free aux. memory - total: 15936 MB, largest block: 15936 MB
    Renderbuffer free memory - total: 15793 MB, largest block: 15793 MB
    Renderbuffer free aux. memory - total: 15936 MB, largest block: 15936 MB
Memory info (GL_NVX_gpu_memory_info):
    Dedicated video memory: 16384 MB
    Total available memory: 32381 MB
    Currently available dedicated video memory: 15793 MB
OpenGL vendor string: AMD
OpenGL renderer string: AMD Radeon RX 9070 XT (radeonsi, gfx1201, ACO, DRM 3.64, 6.18.54)
OpenGL core profile version string: 4.6 (Core Profile) Mesa 26.1.8
OpenGL core profile shading language version string: 4.60
OpenGL core profile context flags: (none)
OpenGL core profile profile mask: core profile

OpenGL version string: 4.6 (Compatibility Profile) Mesa 26.1.8
OpenGL shading language version string: 4.60
OpenGL context flags: (none)
OpenGL profile mask: compatibility profile

OpenGL ES profile version string: OpenGL ES 3.2 Mesa 26.1.8
OpenGL ES profile shading language version string: OpenGL ES GLSL ES 3.20


[exit=0]
```

32-bit Vulkan practical validation: pending; the summary above does not prove it.

## Block devices

```text
NAME        TYPE   SIZE FSTYPE MOUNTPOINTS                            MODEL                 REV
sda         disk  57.7G                                               DataTraveler 3.0     0000
|-sda1      part  57.7G exfat                                                          
`-sda2      part    32M vfat                                                           
nvme0n1     disk 931.5G                                               Force MP600      EGFM11.3
|-nvme0n1p1 part     4G vfat   /boot                                                   
|-nvme0n1p2 part    32G swap   [SWAP]                                                  
`-nvme0n1p3 part 895.5G btrfs  /var/lib/nixos-optimization                             
                               /home                                                   
                               /.snapshots                                             
                               /etc/NetworkManager/system-connections                  
                               /etc/nixos                                              
                               /etc/machine-id                                         
                               /nix/store                                              
                               /var                                                    
                               /nix                                                    
                               /persist                                                
                               /                                                       

[exit=0]
```

## Persistent mounts

```text
/ /dev/nvme0n1p3[/@root] btrfs rw,noatime,compress=zstd:1,ssd,discard=async,space_cache=v2,subvolid=292,subvol=/@root
/home /dev/nvme0n1p3[/@home] btrfs rw,noatime,compress=zstd:1,ssd,discard=async,space_cache=v2,subvolid=256,subvol=/@home
/nix /dev/nvme0n1p3[/@nix] btrfs rw,noatime,compress=zstd:1,ssd,discard=async,space_cache=v2,subvolid=257,subvol=/@nix
/var /dev/nvme0n1p3[/@var] btrfs rw,noatime,compress=zstd:1,ssd,discard=async,space_cache=v2,subvolid=261,subvol=/@var
/persist /dev/nvme0n1p3[/@persist] btrfs rw,noatime,compress=zstd:1,ssd,discard=async,space_cache=v2,subvolid=267,subvol=/@persist
/var/lib/nixos-optimization /dev/nvme0n1p3[/@optimization] btrfs rw,noatime,compress=zstd:1,ssd,discard=async,space_cache=v2,subvolid=258,subvol=/@optimization

[exit=0]
```

## Btrfs usage

```text
Overall:
    Device size:		 895.51GiB
    Device allocated:		 156.06GiB
    Device unallocated:		 739.45GiB
    Device missing:		     0.00B
    Device slack:		     0.00B
    Used:			 121.42GiB
    Free (estimated):		 762.95GiB	(min: 393.22GiB)
    Free (statfs, df):		 762.95GiB
    Data ratio:			      1.00
    Metadata ratio:		      2.00
    Global reserve:		 204.42MiB	(used: 0.00B)
    Multiple profiles:		        no

Data,single: Size:142.00GiB, Used:118.50GiB (83.45%)
   /dev/nvme0n1p3	 142.00GiB

Metadata,DUP: Size:7.00GiB, Used:1.46GiB (20.88%)
   /dev/nvme0n1p3	  14.00GiB

System,DUP: Size:32.00MiB, Used:48.00KiB (0.15%)
   /dev/nvme0n1p3	  64.00MiB

Unallocated:
   /dev/nvme0n1p3	 739.45GiB

[exit=0]
```

## Btrfs devices

```text
/dev/nvme0n1p3, ID: 1
   Device size:           895.51GiB
   Device slack:              0.00B
   Data,single:           142.00GiB
   Metadata,DUP:           14.00GiB
   System,DUP:             64.00MiB
   Unallocated:           739.45GiB


[exit=0]
```

## Btrfs scrub status

```text
UUID:             ea02f7a4-4092-4d0a-8daa-9d6c61e12a0e
Scrub started:    Sun Oct  4 03:20:45 2026
Status:           finished
Duration:         0:00:15
Total to scrub:   121.42GiB
Rate:             2.87GiB/s
Error summary:    no errors found

[exit=0]
```

## Btrfs device error counters

```text
[/dev/nvme0n1p3].write_io_errs    0
[/dev/nvme0n1p3].read_io_errs     0
[/dev/nvme0n1p3].flush_io_errs    0
[/dev/nvme0n1p3].corruption_errs  0
[/dev/nvme0n1p3].generation_errs  0

[exit=0]
```

## NVMe SMART: nvme0

```text
Smart Log for NVME device:nvme0 namespace-id:ffffffff
critical_warning			: 0
temperature				: 34 °C (307 K, 93 °F)
available_spare				: 100%
available_spare_threshold		: 5%
percentage_used				: 18%
endurance group critical warning summary: 0
Data Units Read				: 475060001 (243.23 TB)
Data Units Written			: 290391429 (148.68 TB)
host_read_commands			: 6158130353
host_write_commands			: 2506586411
controller_busy_time			: 10768
power_cycles				: 5163
power_on_hours				: 15143
unsafe_shutdowns			: 2214
media_errors				: 0
num_err_log_entries			: 12137
Warning Temperature Time		: 0
Critical Composite Temperature Time	: 0
Thermal Management T1 Trans Count	: 0
Thermal Management T2 Trans Count	: 0
Thermal Management T1 Total Time	: 0
Thermal Management T2 Total Time	: 0

[exit=0]
```

## NVMe latest error: nvme0

```text
Error Log Entries for device:nvme0 entries:1
.................
 Entry[ 0]
.................
error_count	: 12137
sqid		: 0
cmdid		: 0x1c
status_field	: 0x2002 (Invalid Field in Command: A reserved coded value or an unsupported value in a defined field)
phase_tag	: 0
parm_err_loc	: 0x28
lba		: 0
nsid		: 0
vs		: 0
trtype		: 0 (The transport type is not indicated or the error is not transport related)
csi		: 0
opcode		: 0
cs		: 0
trtype_spec_info: 0
log_page_version: 0
.................

[exit=0]
```

## Kernel

```text
Linux desktop 6.18.54 #1-NixOS SMP PREEMPT_DYNAMIC Fri Sep 25 14:35:54 UTC 2026 x86_64 GNU/Linux

[exit=0]
```

## Boot ID

```text
da4649c0-8121-44ea-afcd-a2d0d4748681

[exit=0]
```

## systemd version

```text
systemd 260 (260.4)
+PAM +AUDIT -SELINUX +APPARMOR +IMA +IPE +SMACK +SECCOMP +GCRYPT -GNUTLS +OPENSSL +ACL +BLKID +CURL +ELFUTILS +FIDO2 +IDN2 +KMOD +LIBCRYPTSETUP +LIBCRYPTSETUP_PLUGINS +LIBFDISK +PCRE2 +PWQUALITY +P11KIT +QRENCODE +TPM2 +BZIP2 +LZ4 +XZ +ZLIB +ZSTD +BPF_FRAMEWORK -BTF -XKBCOMMON +UTMP +LIBARCHIVE

[exit=0]
```

## Failed units

```text
  UNIT LOAD ACTIVE SUB DESCRIPTION

0 loaded units listed.

[exit=0]
```

## Running services

```text
  UNIT                      LOAD   ACTIVE SUB     DESCRIPTION
  bluetooth.service         loaded active running Bluetooth service
  commander-core.service    loaded active running Corsair Commander Core cooling controller
  dbus-broker.service       loaded active running D-Bus System Message Bus
  getty@tty1.service        loaded active running Getty on tty1
  NetworkManager.service    loaded active running Network Manager
  nix-daemon.service        loaded active running Nix Daemon
  nscd.service              loaded active running Name Service Cache Daemon (nsncd)
  polkit.service            loaded active running Authorization Manager
  rtkit-daemon.service      loaded active running RealtimeKit Scheduling Policy Service
  systemd-journald.service  loaded active running Journal Service
  systemd-logind.service    loaded active running User Login Management
  systemd-oomd.service      loaded active running Userspace Out-Of-Memory (OOM) Killer
  systemd-timesyncd.service loaded active running Network Time Synchronization
  systemd-udevd.service     loaded active running Rule-based Manager for Device Events and Files
  user@1000.service         loaded active running User Manager for UID 1000
  wpa_supplicant.service    loaded active running WPA Supplicant instance

Legend: LOAD   -> Reflects whether the unit definition was properly loaded.
        ACTIVE -> The high-level unit activation state, i.e. generalization of SUB.
        SUB    -> The low-level unit activation state, values depend on unit type.

16 loaded units listed.

[exit=0]
```

## Maintenance timers

```text
NEXT                                  LEFT LAST                              PASSED UNIT                         ACTIVATES
Mon 2026-10-05 05:00:00 IST          58min Mon 2026-10-05 04:00:00 IST 1min 43s ago logrotate.timer              logrotate.service
Tue 2026-10-06 03:48:30 IST            23h Mon 2026-10-05 03:48:30 IST    13min ago systemd-tmpfiles-clean.timer systemd-tmpfiles-clean.service
Mon 2026-10-12 00:23:27 IST         6 days Mon 2026-10-05 00:22:44 IST            - fstrim.timer                 fstrim.service
Sun 2026-11-01 00:00:00 GMT 3 weeks 5 days Sun 2026-10-04 03:16:10 IST            - btrfs-scrub--.timer          btrfs-scrub--.service

4 timers listed.

[exit=0]
```

## Loaded modules

```text
Module                  Size  Used by
rfcomm                102400  4
snd_seq_dummy          16384  0
snd_hrtimer            16384  1
snd_seq               118784  7 snd_seq_dummy
af_packet              69632  6
cmac                   16384  3
algif_hash             16384  1
algif_skcipher         12288  1
af_alg                 32768  6 algif_hash,algif_skcipher
bnep                   28672  2
nls_iso8859_1          12288  1
nls_cp437              16384  1
vfat                   28672  1
fat                   114688  1 vfat
amdgpu              16031744  22
snd_sof_pci_intel_cnl    20480  0
snd_sof_intel_hda_generic    40960  1 snd_sof_pci_intel_cnl
soundwire_intel        94208  1 snd_sof_intel_hda_generic
snd_sof_intel_hda_sdw_bpt    24576  1 soundwire_intel
snd_sof_intel_hda_common   204800  3 snd_sof_intel_hda_sdw_bpt,snd_sof_intel_hda_generic,snd_sof_pci_intel_cnl
snd_soc_hdac_hda       24576  1 snd_sof_intel_hda_common
snd_sof_intel_hda_mlink    36864  4 snd_sof_intel_hda_sdw_bpt,soundwire_intel,snd_sof_intel_hda_common,snd_sof_intel_hda_generic
snd_sof_intel_hda      20480  2 snd_sof_intel_hda_common,snd_sof_intel_hda_generic
eeepc_wmi              12288  0
soundwire_cadence      57344  1 soundwire_intel
asus_wmi              110592  1 eeepc_wmi
snd_sof_pci            24576  2 snd_sof_intel_hda_generic,snd_sof_pci_intel_cnl
intel_rapl_msr         20480  0
snd_sof_xtensa_dsp     16384  1 snd_sof_intel_hda_generic
iwlmvm                626688  0
ofpart                 16384  0
snd_sof               499712  6 snd_sof_intel_hda_sdw_bpt,snd_sof_pci,snd_sof_intel_hda_common,snd_sof_intel_hda_generic,snd_sof_intel_hda,snd_sof_pci_intel_cnl
intel_rapl_common      53248  1 intel_rapl_msr
battery                28672  1 asus_wmi
cmdlinepart            16384  0
i8042                  57344  1 asus_wmi
intel_uncore_frequency    16384  0
spi_nor               180224  0
iTCO_wdt               16384  0
intel_uncore_frequency_common    16384  1 intel_uncore_frequency
mtd                   114688  5 spi_nor,cmdlinepart,ofpart
mei_pxp                20480  0
mei_hdcp               28672  0
ee1004                 16384  0
intel_pmc_bxt          16384  1 iTCO_wdt
snd_sof_utils          16384  1 snd_sof
sparse_keymap          12288  1 asus_wmi
intel_tcc_cooling      12288  0
snd_soc_acpi_intel_match   143360  2 snd_sof_intel_hda_generic,snd_sof_pci_intel_cnl
mac80211             1708032  1 iwlmvm
x86_pkg_temp_thermal    16384  0
snd_soc_acpi_intel_sdca_quirks    12288  1 snd_soc_acpi_intel_match
soundwire_generic_allocation    20480  1 soundwire_intel
intel_powerclamp       20480  0
snd_soc_acpi           16384  2 snd_soc_acpi_intel_match,snd_sof_intel_hda_generic
polyval_clmulni        12288  0
wmi_bmof               12288  0
drm_buddy              12288  1 amdgpu
ghash_clmulni_intel    12288  0
amdxcp                 12288  1 amdgpu
soundwire_bus        1208320  3 soundwire_intel,soundwire_generic_allocation,soundwire_cadence
drm_panel_backlight_quirks    12288  1 amdgpu
aesni_intel            98304  3
snd_soc_sdca          102400  2 snd_soc_acpi_intel_sdca_quirks,soundwire_bus
intel_wmi_thunderbolt    16384  0
mxm_wmi                12288  0
snd_hda_codec_alc882    20480  1
gpu_sched              69632  1 amdgpu
drm_exec               16384  1 amdgpu
snd_hda_codec_realtek_lib    65536  1 snd_hda_codec_alc882
crc8                   12288  1 soundwire_cadence
drm_suballoc_helper    16384  1 amdgpu
snd_hda_codec_atihdmi    20480  1
rapl                   24576  0
drm_ttm_helper         20480  2 amdgpu
snd_hda_codec_generic   114688  2 snd_hda_codec_realtek_lib,snd_hda_codec_alc882
libarc4                12288  1 mac80211
snd_hda_codec_hdmi     61440  1 snd_hda_codec_atihdmi
snd_soc_avs           274432  0
input_leds             16384  0
intel_cstate           20480  0
ttm                   131072  2 amdgpu,drm_ttm_helper
snd_soc_hda_codec      28672  1 snd_soc_avs
snd_hda_intel          69632  2
snd_hda_ext_core       36864  7 snd_sof_intel_hda_sdw_bpt,snd_soc_avs,snd_soc_hda_codec,snd_sof_intel_hda_common,snd_soc_hdac_hda,snd_sof_intel_hda_mlink,snd_sof_intel_hda
iwlwifi               593920  1 iwlmvm
snd_hda_codec         217088  10 snd_hda_codec_generic,snd_soc_avs,snd_hda_codec_hdmi,snd_soc_hda_codec,snd_hda_intel,snd_hda_codec_realtek_lib,snd_soc_hdac_hda,snd_hda_codec_alc882,snd_sof_intel_hda,snd_hda_codec_atihdmi
drm_display_helper    319488  1 amdgpu
igc                   217088  0
snd_hda_core          147456  12 snd_hda_codec_generic,snd_soc_avs,snd_hda_codec_hdmi,snd_soc_hda_codec,snd_hda_intel,snd_hda_ext_core,snd_hda_codec,snd_sof_intel_hda_common,snd_hda_codec_realtek_lib,snd_soc_hdac_hda,snd_sof_intel_hda,snd_hda_codec_atihdmi
snd_soc_core          442368  7 snd_soc_avs,snd_soc_hda_codec,soundwire_intel,snd_sof,snd_soc_sdca,snd_sof_intel_hda_common,snd_soc_hdac_hda
cec                    77824  2 drm_display_helper,amdgpu
joydev                 28672  0
ptp                    57344  2 iwlmvm,igc
mousedev               28672  0
snd_intel_dspcfg       45056  5 snd_soc_avs,snd_hda_intel,snd_sof,snd_sof_intel_hda_common,snd_sof_intel_hda_generic
uas                    36864  0
intel_uncore          274432  0
i2c_algo_bit           24576  1 amdgpu
snd_compress           36864  2 snd_soc_avs,snd_soc_core
snd_intel_sdw_acpi     16384  2 snd_intel_dspcfg,snd_sof_intel_hda_generic
rtc_cmos               28672  1
mei_me                 57344  2
i2c_i801               40960  0
cfg80211             1474560  3 iwlmvm,iwlwifi,mac80211
pps_core               32768  1 ptp
ac97_bus               12288  1 snd_soc_core
i2c_smbus              20480  1 i2c_i801
mei                   208896  5 mei_hdcp,mei_pxp,mei_me
snd_pcm_dmaengine      20480  1 snd_soc_core
led_class              24576  5 snd_hda_codec_generic,input_leds,iwlmvm,asus_wmi,igc
spi_intel_pci          12288  0
i2c_mux                20480  1 i2c_i801
spi_intel              36864  1 spi_intel_pci
intel_lpss_pci         28672  0
thermal                28672  0
intel_lpss             12288  1 intel_lpss_pci
idma64                 24576  0
fan                    28672  0
virt_dma               16384  1 idma64
video                  81920  2 asus_wmi,amdgpu
intel_pmc_core        159744  0
pmt_telemetry          20480  1 intel_pmc_core
intel_oc_wdt           12288  0
pmt_discovery          16384  1 pmt_telemetry
pmt_class              20480  2 pmt_telemetry,pmt_discovery
watchdog               49152  2 iTCO_wdt,intel_oc_wdt
wmi                    36864  5 video,intel_wmi_thunderbolt,asus_wmi,wmi_bmof,mxm_wmi
intel_pmc_ssram_telemetry    16384  1 intel_pmc_core
tiny_power_button      12288  0
intel_vsec             28672  2 intel_pmc_ssram_telemetry,pmt_telemetry
button                 28672  0
acpi_pad               24576  0
btusb                  86016  0
btrtl                  36864  1 btusb
btintel                73728  1 btusb
btmtk                  32768  1 btusb
btbcm                  28672  1 btusb
snd_usb_audio         614400  1
bluetooth            1118208  34 btrtl,btmtk,btintel,btbcm,bnep,btusb,rfcomm
snd_ump                36864  1 snd_usb_audio
snd_usbmidi_lib        53248  1 snd_usb_audio
snd_hwdep              24576  2 snd_usb_audio,snd_hda_codec
snd_rawmidi            57344  2 snd_usbmidi_lib,snd_ump
snd_seq_device         20480  3 snd_seq,snd_ump,snd_rawmidi
snd_pcm               200704  15 snd_soc_avs,snd_hda_codec_hdmi,snd_hda_intel,snd_usb_audio,snd_hda_codec,soundwire_intel,snd_sof,snd_soc_sdca,snd_sof_intel_hda_common,snd_compress,snd_sof_intel_hda_generic,snd_soc_core,snd_sof_utils,snd_hda_core,snd_pcm_dmaengine
snd_timer              57344  3 snd_seq,snd_hrtimer,snd_pcm
xt_conntrack           12288  2
snd                   159744  26 snd_hda_codec_generic,snd_seq,snd_seq_device,snd_hda_codec_hdmi,snd_hwdep,snd_hda_intel,snd_usb_audio,snd_usbmidi_lib,snd_hda_codec,snd_sof,snd_soc_sdca,snd_timer,snd_hda_codec_realtek_lib,snd_compress,snd_soc_core,snd_ump,snd_pcm,snd_rawmidi
ecdh_generic           20480  2 bluetooth
nf_conntrack          196608  1 xt_conntrack
rfkill                 45056  8 iwlmvm,asus_wmi,bluetooth,cfg80211
ecc                    49152  1 ecdh_generic
evdev                  32768  15
soundcore              20480  1 snd
crc16                  12288  2 bluetooth,amdgpu
mac_hid                16384  0
mc                     90112  1 snd_usb_audio
nf_defrag_ipv6         24576  1 nf_conntrack
onboard_usb_dev        28672  0
nf_defrag_ipv4         12288  1 nf_conntrack
sd_mod                 86016  0
xt_tcpudp              16384  3
ip6t_rpfilter          12288  1
ipt_rpfilter           12288  1
xt_pkttype             12288  2
nft_compat             28672  9
x_tables               53248  6 xt_conntrack,ip6t_rpfilter,nft_compat,xt_tcpudp,ipt_rpfilter,xt_pkttype
nf_tables             393216  89 nft_compat
nfnetlink              24576  2 nft_compat,nf_tables
sch_fq_codel           28672  5
atkbd                  40960  0
libps2                 24576  1 atkbd
uinput                 24576  0
serio                  32768  2 atkbd,i8042
loop                   49152  0
coretemp               24576  0
vivaldi_fmap           12288  1 atkbd
fuse                  282624  5
configfs               69632  1
dmi_sysfs              28672  0
usb_storage            94208  1 uas
hid_generic            12288  0
usbhid                 90112  0
hid                   286720  4 usbhid,snd_soc_sdca,hid_generic
crc32c_cryptoapi       12288  1
ahci                   57344  0
libahci                65536  1 ahci
libata                499712  2 libahci,ahci
nvme                   73728  3
nvme_core             266240  4 nvme
xhci_pci               28672  0
scsi_mod              339968  4 sd_mod,usb_storage,uas,libata
nvme_keyring           20480  1 nvme_core
nvme_auth              32768  1 nvme_core
xhci_hcd              430080  1 xhci_pci
hkdf                   12288  1 nvme_auth
scsi_common            16384  5 scsi_mod,sd_mod,usb_storage,uas,libata
btrfs                2269184  1
blake2b_generic        20480  0
xor                    24576  1 btrfs
dm_mod                241664  0
raid6_pq              126976  1 btrfs
efivarfs               40960  1
autofs4                65536  0

[exit=0]
```

## Observed temperatures

```text
acpitz-acpi-0
Adapter: ACPI interface
temp1:        +27.8 C  

nvme-pci-0700
Adapter: PCI adapter
Composite:    +33.9 C  (low  = -60.1 C, high = +89.8 C)
                       (crit = +94.8 C)

amdgpu-pci-0300
Adapter: PCI adapter
vddgfx:       48.00 mV 
fan1:           0 RPM  (min =    0 RPM, max = 4350 RPM)
edge:         +39.0 C  (crit = +110.0 C, hyst = -273.1 C)
                       (emerg = +115.0 C)
junction:     +40.0 C  (crit = +110.0 C, hyst = -273.1 C)
                       (emerg = +115.0 C)
mem:          +43.0 C  (crit = +108.0 C, hyst = -273.1 C)
                       (emerg = +113.0 C)
PPT:          23.00 W  (cap = 340.00 W)
pwm1:              0%
sclk:        1000 kHz 
mclk:         772 MHz 

iwlwifi_1-virtual-0
Adapter: Virtual device
temp1:        +30.0 C  

coretemp-isa-0000
Adapter: ISA adapter
Package id 0:  +56.0 C  (high = +80.0 C, crit = +100.0 C)
Core 0:        +38.0 C  (high = +80.0 C, crit = +100.0 C)
Core 1:        +39.0 C  (high = +80.0 C, crit = +100.0 C)
Core 2:        +39.0 C  (high = +80.0 C, crit = +100.0 C)
Core 3:        +36.0 C  (high = +80.0 C, crit = +100.0 C)
Core 4:        +38.0 C  (high = +80.0 C, crit = +100.0 C)
Core 5:        +37.0 C  (high = +80.0 C, crit = +100.0 C)


[exit=0]
```

## Commander Core service

```text
ActiveState=active
SubState=running
FragmentPath=/etc/systemd/system/commander-core.service
WatchdogUSec=35s
MainPID=912

[exit=0]
```

## Declared cooling policy source

```text
26ede8dc0c2a8528a3f849a87d0bb822a31275a993888f5498bb569875bea58d  modules/hardware/commander-core/default.nix
23993376746bc070ceb99e2a447603aa28ea6ce0183670942ccc474f99abea22  modules/hardware/commander-core/keeper.py
d1214dbaeda578c51b3c5d64c78b58ef36233d9aedd1de38a3eba97eede5fe57  hosts/desktop/default.nix

[exit=0]
```

## Cooling runtime state

```text
status=active
pid=912
cpu_package_temp=56.0
fan_mode=base
fan_duty=60
pump_duty=100
last_wake_epoch=1791169301

[exit=0]
```

## Root subvolume

```text
@root
	Name: 			@root
	UUID: 			c3bd4143-fb98-fa4b-bbcc-38fd501459b4
	Parent UUID: 		-
	Received UUID: 		-
	Creation time: 		2026-10-05 03:33:31 +0100
	Subvolume ID: 		292
	Generation: 		2955
	Gen at creation: 	2900
	Parent ID: 		5
	Top level ID: 		5
	Flags: 			-
	Send transid: 		0
	Send time: 		2026-10-05 03:33:31 +0100
	Receive transid: 	0
	Receive time: 		-
	Snapshot(s):
	Quota group:		n/a

[exit=0]
```

## Machine ID

```text
7b6c4bf063b24630b936513576e361a7

[exit=0]
```

## Reset diagnostic metadata

```text
600 root:root 4571 bytes 2026-10-05 03:33:31.375502872 +0100

[exit=0]
```

## Reset diagnostic counts

```text
boot records=3 reset completions=3 recovery completions=0

[exit=0]
```

Privileged reset log and secret files are deliberately not copied into this report.
Failed commands above are missing evidence and must be resolved before final acceptance.
