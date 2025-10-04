# Edit this configuration file to define what should be installed on
# your system.  Help is available in the configuration.nix(5) man page
# and in the NixOS manual (accessible by running ‘nixos-help’).

{ self, nixpkgs, config, pkgs, lib, inputs, ... }:
{

networking = {
	useDHCP = true;
	dhcpcd = {
		enable = true;
		persistent = true;
	};
	useNetworkd = false;

	hostName = "nixos"; # Define your hostname.
	# networking.wireless.enable = true;  # Enables wireless support via wpa_supplicant.

	# Configure network proxy if necessary
	# networking.proxy.default = "http://user:password@proxy:port/";
	# networking.proxy.noProxy = "127.0.0.1,localhost,internal.domain";

	# Enable networking
	networkmanager.enable = false;

	nftables.enable = true;

	firewall.enable = false;

};


nix = {
	settings = {
		substituters = [
			"https://hyprland.cachix.org/"
			"https://cache.nixos.org/"
			"https://cachix.cachix.org/"
			"https://nix-community.cachix.org/"
		];
		trusted-public-keys = [
			"hyprland.cachix.org-1:a7pgxzMz7+chwVL3/pzj6jIBMioiJM7ypFP8PwtkuGc="
			"cachix.cachix.org-1:eWNHQldwUO7G2VkjpnjDbWwy4KQ/HNxht7H4SSoMckM="
			"cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY="
			"nix-community.cachix.org-1:mB9FSh9qf2dCimDSUo8Zy7bkq5CX+/rkCWyvRCYg3Fs="
		];
		trusted-substituters = [
			"https://hyprland.cachix.org/"
			"https://cache.nixos.org/"
			"https://cachix.cachix.org/"
			"https://nix-community.cachix.org/"
		];
		sandbox = true;
		experimental-features = [ 
			"nix-command" 
			"flakes" 
			"auto-allocate-uids"
		];
		auto-optimise-store = true;
		trusted-users = [
			"root"
			"p2949"
			"@wheel"
			"*"
		];
	};
	optimise.automatic = true;
	gc = {
		persistent = true;
		automatic = true;
		options = "--delete-older-than 1d";
	};
};



hardware = {

	bluetooth = {
		enable = true;
		hsphfpd.enable = false;
	};

	enableAllFirmware = true;

	cpu.x86.msr.enable = true;

	sensor.iio.enable = false;

	graphics = {
		enable = true;
		enable32Bit = true;

    	extraPackages = with pkgs; [
			mesa.opencl
			SDL
			xorg.libXdamage
			gamescope-wsi
			libavif
			goldberg-emu
			bubblewrap
			extest
			libsForQt5.kwindowsystem
			kdePackages.kwindowsystem
      gamescope
      gamemode
			npins
			sdl3
			libinput
			SDL2
			libcap
			libxcursor
			seatd
			libxfixes
			xorg.libXcomposite
			intel-media-driver 
			libGL
			libxkbcommon
			libarchive
			openssl
			xorg.libXi
			wlr-protocols
			nvidia-modprobe
			intel-gpu-tools
			intel-graphics-compiler
			spirv-tools
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
			vpl-gpu-rt
			vaapi-intel-hybrid
			intel-gmmlib
			libx11
			gnome-software
			vaapiIntel        
			vaapiVdpau
			xed
			mangohud
			libva
			libdrm
			egl-wayland
			libnvidia-container
			libvdpau-va-gl
			libvdpau
			virtualglLib
			intel-compute-runtime
			nv-codec-headers-12
			libvpl
			intel-ocl
			ffmpeg-full
			nvidia-vaapi-driver
			vulkan-extension-layer
			vulkan-utility-libraries
			mesa
			libdrm
			glfw3-minecraft
			intel-ocl
			xorg.xf86videonv
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			libxrender
			xorg.libXres
			xorg.libXtst
			libxmu
			libvdpau-va-gl
			libvdpau
			vulkan-extension-layer
			vulkan-utility-libraries
			vaapiVdpau
			libei
			libvdpau-va-gl
			nvidia-vaapi-driver
			libdecor
			libva
			luajit
			vaapiVdpau
			xorg.libXxf86vm
			libvdpau-va-gl
			cairo
			pixman
			mesa
			config.boot.kernelPackages.nvidia_x11_beta
			config.boot.kernelPackages.nvidia_x11_beta_open
			intel-cmt-cat
			freetype
    	];
    
    	extraPackages32 = with pkgs.pkgsi686Linux; [ 
			spirv-tools
			xorg.libXxf86vm
			SDL
			luajit
			sdl3
			libinput
			gamemode
			libxfixes
			libavif
			libxmu
			xorg.libXcomposite
			SDL2
			libcap
			xorg.libXres
			extest
			libxrender
			libva
			goldberg-emu
			bubblewrap
			seatd
			libsForQt5.kwindowsystem
			#kdePackages.kwindowsystem
			freetype
			xorg.libXi
			xorg.libXdamage
			intel-gpu-tools
			libx11
			libvpl
			libxcursor
			cairo
			libdrm
			mangohud
			virtualglLib
			libvdpau-va-gl
			libvdpau
			cairo
			nvidia-modprobe
			pixman
			libdecor
			libGL
			libxkbcommon
			openssl
			libarchive
			vulkan-extension-layer
			vulkan-utility-libraries
			vaapiVdpau
			libvdpau-va-gl
			nvidia-vaapi-driver
			libva
			vaapiVdpau
			libvdpau-va-gl
			mesa
			glfw3-minecraft
			xorg.libXtst
			vaapi-intel-hybrid
			intel-graphics-compiler
			xed
			intel-gmmlib
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			vaapiVdpau
			vaapiIntel
			intel-media-driver
			nvidia-vaapi-driver
			xorg.xf86videonv
			nv-codec-headers-12
		];
	};


	amdgpu = {
		opencl.enable = true;
	};
	steam-hardware.enable = true;

	intel-gpu-tools.enable = true;

	cpu.intel = {
		updateMicrocode = true;
		sgx = {
			enableDcapCompat = true;
			provision.enable = true;
			provision.group = "wheel";
		};
	};



	system76 = {
		power-daemon.enable = true;
		kernel-modules.enable = true;
		firmware-daemon.enable = true;
		enableAll = true;
	};

	bumblebee = {
		enable = false;
		pmMethod = "none";
		driver = "nvidia";
		connectDisplay = true;
	};

	nvidia = {
		forceFullCompositionPipeline = lib.mkForce true;
		prime = {
			allowExternalGpu = lib.mkForce true;
			offload = {
				enable = lib.mkForce true;
				enableOffloadCmd = lib.mkForce true;
			};
			reverseSync = {
				enable = lib.mkForce true;
				setupCommands.enable = lib.mkForce true;
			};
			sync.enable = lib.mkForce false;
			# Make sure to use the correct Bus ID values for your system!
			intelBusId = "PCI:0:2:0";
			nvidiaBusId = "PCI:1:0:0";
		};
		videoAcceleration = lib.mkForce true;
		dynamicBoost.enable = lib.mkForce false;
		gsp.enable = lib.mkForce true;
		nvidiaPersistenced = lib.mkForce false;
		# Modesetting is required.
		modesetting.enable = lib.mkForce true;
		# Nvidia power management. Experimental, and can cause sleep/suspend to fail.
		powerManagement.enable = lib.mkForce true;
		# Fine-grained power management. Turns off GPU when not in use.
		# Experimental and only works on modern Nvidia GPUs (Turing or newer).
		powerManagement.finegrained = lib.mkForce true;
		# Use the NVidia open source kernel module (not to be confused with the
		# independent third-party "nouveau" open source driver).
		# Support is limited to the Turing and later architectures. Full list of 
		# supported GPUs is at: 
		# https://github.com/NVIDIA/open-gpu-kernel-modules#compatible-gpus 
		# Only available from driver 515.43.04+
		# Do not disable this unless your GPU is unsupported or if you have a good reason to.
		open = lib.mkForce true;
		# Enable the Nvidia settings menu,
		# accessible via `nvidia-settings`.
		nvidiaSettings = lib.mkForce true;
		# Optionally, you may need to select the appropriate driver version for your specific GPU.
		#package = config.boot.kernelPackages.nvidiaPackages.stable;
		package = config.boot.kernelPackages.nvidiaPackages.beta;
  	};
	nvidiaOptimus.disable = lib.mkForce false;

};



xdg = {
    autostart.enable = true;
	sounds.enable = true;
	mime.enable = true;
	menus.enable = true;
	icons.enable = true;
    portal = {
		configPackages = [
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
		];
		wlr.enable = true;
    	enable = true;
		xdgOpenUsePortal = true;
		extraPortals = [
        	pkgs.xdg-desktop-portal
			pkgs.xdg-desktop-portal-wlr
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
      	];
    };
};

security = {
	pam.loginLimits = [
	{
    	domain = "*";
    	item = "nice";
    	type = "hard";
    	value = "-20";
	}];

	sudo = {
		wheelNeedsPassword = false;
		enable = true;
		configFile = "Defaults:root,%wheel env_keep+=DISPLAY";
	};

	rtkit.enable = true;

	doas = {
		enable = true;
		wheelNeedsPassword = false;
	};

	polkit = {
		enable = true;
		adminIdentities = [
			"unix-group:wheel"
			"unix-user:p2949"
		];
	};
};

environment = { 

	shells = with pkgs; [ zsh ];

    sessionVariables = {
		LD_LIBRARY_PATH = "$LD_LIBRARY_PATH:${pkgs.linuxPackages.nvidia_x11}/lib/:${pkgs.wayland}/lib/:${pkgs.sdl3}/lib/:${pkgs.xorg.libXdamage}/lib/";
    __GLSHADER_DISK_CACHE = "1";
    fully_kms_output = "TRUE";
		FULLY_KMS_OUTPUT = "TRUE";
		__GL_PRESENT= "0";
		NIXOS_OZONE_WL = "1";
		DOTNET_ROOT = "${pkgs.dotnet-sdk_9}/share/dotnet/";
		POLKIT_AUTH_AGENT = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
		XDG_SESSION_TYPE = "wayland";
		WLR_NO_HARDWARE_CURSORS = "1";
		XCURSOR_SIZE = "24";
		HYPRCURSOR_SIZE = "24";	
		XCURSOR_THEME = "Adwaita:dark";
		HYPRCURSOR_THEME = "Adwaita:dark";
		WLR_DRM_NO_ATOMIC = "1";
		SDL_VIDEODRIVER = "wayland";
		MOZ_ENABLE_WAYLAND = "1";
		_JAVA_AWT_WM_NONREPARENTING = "1";
		CLUTTER_BACKEND = "wayland";
		GTK_USE_PORTAL = "1";
		NIXOS_XDG_OPEN_USE_PORTAL = "1";
		GDK_BACKEND = "wayland";
		QT_QPA_PLATFORM="wayland";
		QT_AUTO_SCREEN_SCALE_FACTOR = "1";
		XDG_CURRENT_DESKTOP = "Hyprland";
		XDG_SESSION_DESKTOP = "Hyprland";
		__GL_VRR_ALLOWED = "1";
		AQ_FORCE_LINEAR_BLIT="1";
		AQ_MGPU_NO_EXPLICIT="0";
		AQ_NO_MODIFIERS="0";
		AQ_NO_ATOMIC="0";
		__GL_GSYNC_ALLOWED = "1";
		QT_WAYLAND_DISABLE_WINDOWDECORATION = "1";
		GTK_THEME = "Adwaita:dark";
		WLR_DRM_DEVICES = "/dev/dri/card1";
		__GL_SHADER_DISK_CACHE_SKIP_CLEANUP = "1";
		__GL_MaxFramesAllowed = "3";
		#__GL_THREADED_OPTIMIZATIONS = "1";
		__GL_MAX_FRAMES_ALLOWED = "3";
		__GL_YIELD = "USLEEP";
		LIBVA_DRIVER_NAME = "iHD";
		VDPAU_DRIVER = "va_gl";
		VAAPI_MPEG4_ENABLED = "true";
		MOZ_DRM_DEVICE = "/dev/dri/card1";
		MOZ_X11_EGL = "1";
		MOZ_DISABLE_CONTENT_SANDBOX = "1";
		MOZ_DISABLE_GMP_SANDBOX = "1";
		MOZ_FAKE_NO_SANDBOX = "1";
		MOZ_DISABLE_RDD_SANDBOX = "1";
		__GL_FSAA_MODE = "5";
		__GL_ALLOW_FXAA_USAGE = "1";
		__GL_LOG_MAX_ANISO = "4";
		__GL_SYNC_TO_VBLANK = "0";
		__GL_ALLOW_UNOFFICIAL_PROTOCOL = "1";
		RADV_PERFTEST = "gpl";
		AQ_DRM_DEVICES = "/dev/dri/card1";
		VK_DRIVER_FILES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver/share/vulkan/icd.d/*:/run/opengl-driver-32/share/vulkan/icd.d/*";
		VK_ICD_FILENAMES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver/share/vulkan/icd.d/*:/run/opengl-driver-32/share/vulkan/icd.d/*";
		__GLX_VENDOR_LIBRARY_NAME = "mesa";
		AMD_VULKAN_ICD = "RADV";
		NVD_BACKEND = "direct";
		NIXPKGS_ALLOW_UNFREE = "1";
	};

	pathsToLink = [
		"/share"
		"/bin"
		"/etc"
		"/dev"
		"/home/p2949"
		"/nix"
		"/proc"
		"/root"
		"/run"
		"/srv"
		"/sys"
		"/tmp"
		"/usr"
		"/"
		"/org"
		"/var"
		"/usr/share/vulkan/icd.d"
	];

	systemPackages = with pkgs; [
		(discord-canary.override {
      		withOpenASAR = true;
    		withVencord = true; # can do this here too
    	})
		bc
		nvtopPackages.full
		steamcmd
		spotifyd
		xorg.libXdamage
		libxfixes
		gamemode
		extest
		npins
		luajit
		gamemode
		xorg.libXcomposite
		libei
		gamescope-wsi
		libavif
		xorg.libXres
		spotify-tray
		SDL
		seatd
		sdl3
		libcap
		SDL2
		libx11
		libinput
		kdePackages.kwin
    kdePackages.kwin-x11
		libxmu
    libsForQt5.kwindowsystem
    kdePackages.kwindowsystem
    gamescope
    bubblewrap
    goldberg-emu
		spotify-player
		nvidia_oc
		librespot 
		nvidia-modprobe
		xorg.libXi
		yt-dlp
		bumblebee
		dotnet-sdk_9
		xorg_sys_opengl
		elegant-sddm
		lxappearance
		cairo
		gh
		pixman
		lxappearance-gtk2
		libGL
		libxkbcommon
		libarchive
		openssl
		adwaita-qt6
		adwaita-icon-theme
		spirv-tools
		discord-gamesdk
		vencord
		vencord-web-extension
		webcord-vencord
		lutris
		discord-rpc
		discord-canary
		cachix
		xsettingsd
		gnumake
		xorg.xrdb
		lm_sensors
		wlr-protocols
		libusbp
		librewolf-bin
		google-chrome
		libusb1
		#inputs.envycontrol.packages.x86_64-linux.default
		adwaita-icon-theme
		unrar-wrapper
		unrar
		unar
		unrar-free
		pkgsi686Linux.mangohud
		libadwaita
		gtk3-x11
		libgtkflow4
		libgtkflow3
		gtk4
		mangohud
		gnomeExtensions.appindicator
		intel-ocl
		gnome-settings-daemon
		glibc
		steamtinkerlaunch
		vaapi-intel-hybrid
		direnv
		intel-gmmlib
		qt6.qtsvg
		xorg.xf86videonv
		intel-vaapi-driver
		chiaki-ng
		libnvidia-container
		glib
		virtualglLib
		glibmm
		libglibutil
		glibcInfo
		betterdiscordctl
		betterdiscord-installer
		glibc_multi
		glibcLocales
		libdrm
		mesa
		glibc_memusage
		glibcLocalesUtf8
		iconv
		libiconv
		gfortran
		gdb
		polkit_gnome
		libva-utils
		nvidia-vaapi-driver
		nvidia-docker
		liquidctl
		nodejs_22
		nvidia_cg_toolkit
		nvidia-texture-tools
		nvidia-optical-flow-sdk
		nv-codec-headers-12
		xdg-utils
		xdg-desktop-portal
		inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
		inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
		nautilus
		libcdada
		xorg.libXtst
		vulkan-tools
		coolercontrol.coolercontrol-gui
		coolercontrol.coolercontrold
		coolercontrol.coolercontrol-ui-data
		coolercontrol.coolercontrol-liqctld
		wireplumber
		ffmpeg-full
		onlyoffice-bin
		wineWowPackages.stable
		ncspot
		libdecor
		librespot
		libei
		winetricks
		waybar
		libxrender
		mako
		vulkan-tools
		qbittorrent-nox
		vulkan-loader
		vulkan-headers
		vulkan-tools-lunarg
		vulkan-extension-layer
		libxcursor
		vulkan-utility-libraries
		libvdpau
		config.boot.kernelPackages.nvidia_x11_beta
		config.boot.kernelPackages.nvidia_x11_beta_open
		libnvidia-container
		nvidia-vaapi-driver
		nvidia-vaapi-driver
		xorg.xhost
		nvidia-docker
		nvidia_cg_toolkit
		nvidia-texture-tools
		nvidia-optical-flow-sdk
	];

};

virtualisation.kvmgt.enable = true;
   
boot = {

	kernel.sysctl = {
		"kernel.sched_autogroup_enabled" = 1;
		"kernel.sched_bore" = 1;
		"kernel/sched_bore" = 1;
		"kernel/sched_autogroup_enabled" = 1;
		"vm.swappiness" = 1; # when swapping to ssd, otherwise change to 1
		"vm.vfs_cache_pressure" = 50;
		"vm.dirty_background_ratio" = 5;
		"vm.dirty_ratio" = 90;
		"net.ipv4.tcp_low_latency" = 1;
    	# these are the zen-kernel tweaks to CFS defaults (mostly)
    	"kernel.sched_latency_ns" = 4000000;
    	# should be one-eighth of sched_latency (this ratio is not
    	# configurable, apparently -- so while zen changes that to
    	# one-tenth, we cannot):
    	"kernel.sched_min_granularity_ns" = 500000;
    	"kernel.sched_wakeup_granularity_ns" = 50000;
    	"kernel.sched_migration_cost_ns" = 250000;
    	"kernel.sched_cfs_bandwidth_slice_us" = 3000;
    	"kernel.sched_nr_migrate" = 128;
	};

	tmp.cleanOnBoot = true;

	kernelPackages = pkgs.linuxKernel.packages.linux_xanmod_latest;

	loader = {
		efi = {
			canTouchEfiVariables = true;
			efiSysMountPoint = "/boot";
		};

		systemd-boot = {
			enable = true;
			configurationLimit = 5;
		};
	};
	plymouth.enable = true;
	initrd = {
		network = {
			enable = true;
			udhcpc.enable = false;
		};
		services.resolved.enable = true;
		systemd = {
			dbus.enable = true;
			enable = true;
		};
		kernelModules = [ 
			"i915" 
			"nvidia_modeset"
			"nvidia"  
			"nvidia_modeset"
			"nvidia_uvm" 
			"nvidia_drm"
			"msr"
		];
	};
	extraModprobeConfig = ''
		options v4l2loopback devices=1 video_nr=1 card_label="OBS Cam" exclusive_caps=1
		options kvm_intel nested=1
		options nvidia-drm modeset=1
		options nvidia NVreg_PowerMizerDefaultAC=0x3
		options nvidia NVreg_PowerMizerDefault=0x3
		options nvidia NVreg_PowerMizerLevel=0x3
		options nvidia NVreg_PerfLevelSrc=0x2222
		options nvidia NVreg_PowerMizerEnable=0x1
		options nvidia NVreg_EnableStreamMemOPs=1
		options nvidia NVreg_InitializeSystemMemoryAllocations=0
		options nvidia NVreg_UsePageAttributeTable=1
		options i915 force_probe=9bc5
		options nvidia NVreg_EnableGpuFirmware=1
		options nvidia NVreg_EnableResizableBar=1
		options nvidia NVreg_PreserveVideoMemoryAllocations=1
		options i915 enable_guc=3
		options i915 enable_fbc=1
		options i915 fastboot=1
		options nvidia-drm fbdev=1
	'';

	kernelModules = [
		"i915"
		"nvidia_modeset"
		"nvidia"  
		"nvidia_modeset"
		"nvidia_uvm" 
		"nvidia_drm"
		"msr"
	];
	extraModulePackages = [ 
		config.boot.kernelPackages.nvidia_x11_beta
		config.boot.kernelPackages.nvidia_x11_beta_open
		config.boot.kernelPackages.v4l2loopback 
	];

	kernelParams = [ 
		"nvidia.nvidia_drm.modeset=1" 
		"pcie_aspm=off"
		"nvme_core.default_ps_max_latency_us=0"
		"nvidia.NVreg_PowerMizerDefaultAC=0x3" 
		"nvidia.NVreg_PowerMizerDefault=0x3" 
		"nvidia.NVreg_PowerMizerLevel=0x3" 
		"nvidia.NVreg_PerfLevelSrc=0x2222" 
		"nvidia.NVreg_PowerMizerEnable=0x1" 
		"nvidia.NVreg_EnableStreamMemOPs=1" 
		"nvidia.NVreg_InitializeSystemMemoryAllocations=0" 
		"nvidia.NVreg_UsePageAttributeTable=1" 
		"nvidia_drm.modeset=1" 
		"i915.force_probe=9bc5" 
		"nvidia.NVreg_EnableGpuFirmware=1" 
		"nvidia.NVreg_EnableResizableBar=1" 
		"module_blacklist=amdgpu" 
		"nvidia.NVreg_PreserveVideoMemoryAllocations=1" 
		"i915.enable_guc=3" 
		"i915.enable_fbc=1" 
		"i915.fastboot=1" 
		"nvidia-drm.fbdev=1"
		"module_blacklist=nouveau"
		"cgroup_no_v1=all" 
		"systemd.unified_cgroup_hierarchy=yes"
	];
	blacklistedKernelModules = [ "nouveau" "amdgpu" ];



};
  
imports = [ 
	./hardware-configuration.nix
  ./cachix.nix];

systemd = {

	network.enable = false;

	globalEnvironment = {
		__GL_SHADER_DISK_CACHE = "1";
		fully_kms_output = "TRUE";
		FULLY_KMS_OUTPUT = "TRUE";
		__GL_PRESENT= "0";
		NIXOS_OZONE_WL = "1";
		POLKIT_AUTH_AGENT = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
		DOTNET_ROOT = "${pkgs.dotnet-sdk_9}/share/dotnet/";
		XDG_SESSION_TYPE = "wayland";
		WLR_NO_HARDWARE_CURSORS = "1";
		XCURSOR_SIZE = "24";
		HYPRCURSOR_SIZE = "24";	
		XCURSOR_THEME = "Adwaita:dark";
		HYPRCURSOR_THEME = "Adwaita:dark";
    		WLR_DRM_NO_ATOMIC = "1";
		SDL_VIDEODRIVER = "wayland";
		MOZ_ENABLE_WAYLAND = "1";
		_JAVA_AWT_WM_NONREPARENTING = "1";
		CLUTTER_BACKEND = "wayland";
		GTK_USE_PORTAL = "1";
		NIXOS_XDG_OPEN_USE_PORTAL = "1";
		GDK_BACKEND = "wayland";
		LD_LIBRARY_PATH = "$LD_LIBRARY_PATH:${pkgs.linuxPackages.nvidia_x11}/lib/:${pkgs.wayland}/lib/:${pkgs.sdl3}/lib/:${pkgs.xorg.libXdamage}/lib/";
		QT_QPA_PLATFORM="wayland";
		QT_AUTO_SCREEN_SCALE_FACTOR = "1";
		XDG_CURRENT_DESKTOP = "Hyprland";
		PROTON_VERSION="GE-Proton10-17";
		XDG_SESSION_DESKTOP = "Hyprland";
		__GL_VRR_ALLOWED = "1";
		__GL_GSYNC_ALLOWED = "1";
		QT_WAYLAND_DISABLE_WINDOWDECORATION = "1";
		GTK_THEME = "Adwaita:dark";
		WLR_DRM_DEVICES = "/dev/dri/card1";
		__GL_SHADER_DISK_CACHE_SKIP_CLEANUP = "1";
		__GL_MaxFramesAllowed = "3";
		#__GL_THREADED_OPTIMIZATIONS = "1";
		__GL_MAX_FRAMES_ALLOWED = "3";
		__GL_YIELD = "USLEEP";
		LIBVA_DRIVER_NAME = "iHD";
		VDPAU_DRIVER = "va_gl";
		VAAPI_MPEG4_ENABLED = "true";
		MOZ_DRM_DEVICE = "/dev/dri/card1";
		MOZ_X11_EGL = "1";
		MOZ_DISABLE_CONTENT_SANDBOX = "1";
		MOZ_DISABLE_GMP_SANDBOX = "1";
		MOZ_FAKE_NO_SANDBOX = "1";
		MOZ_DISABLE_RDD_SANDBOX = "1";
		__GL_FSAA_MODE = "5";
		__GL_ALLOW_FXAA_USAGE = "1";
		__GL_LOG_MAX_ANISO = "4";
		__GL_SYNC_TO_VBLANK = "0";
		__GL_ALLOW_UNOFFICIAL_PROTOCOL = "1";
		RADV_PERFTEST = "gpl";
		AQ_DRM_DEVICES = "/dev/dri/card1";
		VK_DRIVER_FILES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver/share/vulkan/icd.d/*:/run/opengl-driver-32/share/vulkan/icd.d/*";
		VK_ICD_FILENAMES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver/share/vulkan/icd.d/*:/run/opengl-driver-32/share/vulkan/icd.d/*";
		__GLX_VENDOR_LIBRARY_NAME = "mesa";
		AMD_VULKAN_ICD = "RADV";
		NVD_BACKEND = "direct";
		NIXPKGS_ALLOW_UNFREE = "1";

	};

	services = {
		systemd-udev-settle.enable = true;
		NetworkManager-wait-online.enable = true;
	};

	user.extraConfig = ''
		DefaultCPUAccounting=yes
		DefaultMemoryAccounting=yes
		DefaultIOAccounting=yes
    '';

	user.services.polkit-gnome-authentication-agent-1 = {
		description = "polkit-gnome-authentication-agent-1";
		wantedBy = [ "graphical-session.target" ];
		wants = [ "graphical-session.target" ];
		after = [ "graphical-session.target" ];
		serviceConfig = {
			Type = "simple";
			ExecStart = "${pkgs.polkit_gnome}/libexec/polkit-gnome-authentication-agent-1";
			Restart = "on-failure";
			RestartSec = 1;
			TimeoutStopSec = 10;
		};
	};
	user.services.nvidia_oc = {
		description = "NVIDIA Overclocking Service";
		wantedBy = [ "graphical-session.target" ];
		wants = [ "graphical-session.target" ];
		after = [ "network.target" ];
		serviceConfig = {
			Type = "simple";
			User = "root";
			ExecStart = "${pkgs.nvidia_oc}/nvidia_oc set --index 0 --power-limit 187000 --freq-offset 235 --mem-offset 305 --min-clock 300 --max-clock 4000";
			Restart = "on-failure";
			RestartSec = 1;
			TimeoutStopSec = 10;
		};
	};
};


# Set your time zone.
time.timeZone = "Europe/Dublin";

# Select internationalisation properties.
i18n.defaultLocale = "en_GB.UTF-8";

i18n.extraLocaleSettings = {
    LC_ADDRESS = "en_IE.UTF-8";
    LC_IDENTIFICATION = "en_IE.UTF-8";
    LC_MEASUREMENT = "en_IE.UTF-8";
    LC_MONETARY = "en_IE.UTF-8";
    LC_NAME = "en_IE.UTF-8";
    LC_NUMERIC = "en_IE.UTF-8";
    LC_PAPER = "en_IE.UTF-8";
    LC_TELEPHONE = "en_IE.UTF-8";
    LC_TIME = "en_IE.UTF-8";
};

 

i18n.inputMethod.fcitx5.waylandFrontend = true;

# Configure console keymap
console.keyMap = "uk";

# swap
zramSwap = {
    enable = true;
    memoryPercent = 150;
    algorithm = "zstd";
};  

qt = {
	enable = true;
	style = "adwaita-dark";
};
# Define a user account. Don't forget to set a password with ‘passwd’.

users = {
 #normal users declaration here
  mutableUsers = true;
	extraUsers = {
		root = {};
		p2949 = {};
	};

	allowNoPasswordLogin = true;

	defaultUserShell = pkgs.zsh;

	users = { 
		p2949 = {
		shell = pkgs.zsh;
		useDefaultShell = true;
		isNormalUser = true;
		description = "Pedro Goraieb Fernandes";
		extraGroups = [ 
			"qbittorrent"
			"sddm" 
			"systemd-journal" 
			"keys" 
			"utmp" 
			"dialout" 
			"tape" 
			"cdrom" 
			"lp" 
			"uucp" 
			"floppy" 
			"messagebus" 
			"kmem" 
			"root" 
			"libvirtd" 
			"nixbld" 
			"pipewire" 
			"gamemode" 
			"networkmanager" 
			"wheel" 
			"adbusers" 
			"users" 
			"gdm" 
			"audio" 
			"disk" 
			"video" 
			"adm" 
			"kvm" 
			"sgx" 
			"render" 
			"tty" 
			"input" 
			"polkituser" 
			"nixbld" 
			"msr"
		];
    	packages = with pkgs; [
			(lutris.override {
      			extraLibraries =  pkgs: [
					# List library dependencies here
					gamemode
					meson
					mangohud
					pango
					libadwaita
					gtk3-x11
					libgtkflow4
					libgtkflow3
					gtk4
					libthai
					harfbuzz
      			];
    		})
    			(discord-canary.override {
      			withOpenASAR = true;
    			withVencord = true; # can do this here too
    		})
			spotifyd
			steamcmd
			SDL
			npins
			libinput
			xorg.libXdamage
			sdl3
			libxmu
			kdePackages.kwin
			gamescope-wsi
			gamemode
			luajit
			extest
			xorg.libXres
			xorg.libXcomposite
      		kdePackages.kwin-x11
      		libsForQt5.kwindowsystem
      		kdePackages.kwindowsystem
      		gamescope
      		bubblewrap
	  		libavif
      		goldberg-emu
			SDL2
			libxfixes
			spotify-tray
			spotify-player
			librespot
			xorg.libXi
			bumblebee
			direnv
			qbittorrent-nox
			bc
			dotnet-sdk_9
			flatpak
      gnome-software
			yt-dlp 
			lxappearance
			libx11
			xorg_sys_opengl
			vencord
			vencord-web-extension
			webcord-vencord
			nvidia_oc
			libGL
			libxkbcommon
			libarchive
			openssl
			gnumake
			discord-gamesdk
			nvtopPackages.full
			discord-rpc
			cairo
			pixman
			discord-canary
			lxappearance-gtk2
			adwaita-qt6
			adwaita-icon-theme
			pango
			libthai
			harfbuzz
			cachix
			lm_sensors
			wlr-protocols
			xsettingsd
			libadwaita
			libgtkflow4
			libgtkflow3
			gtk4
			gtk3-x11
			xorg.xrdb
			librewolf-bin
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
			#inputs.envycontrol.packages.x86_64-linux.default
			xorg.xhost
			unrar-wrapper
			unrar
			unar
			libusbp
			libusb1
			spirv-tools
			chiaki-ng
			google-chrome
			unrar-free
			adwaita-icon-theme
			gnomeExtensions.appindicator
			gnome-settings-daemon			
			spotify
			qt6.qtsvg
			coolercontrol.coolercontrol-gui
			coolercontrol.coolercontrold
			coolercontrol.coolercontrol-ui-data
			coolercontrol.coolercontrol-liqctld
			liquidctl		
			nodejs_22
			zsh
			intel-gmmlib
			meson
			ninja
			jq
			lshw
			gparted
			gnome-disk-utility
			vaapi-intel-hybrid
			hyprcursor
			vim
			prismlauncher
			openal
			mlx42
			glfw
			glfw3-minecraft
			qt6.qtwayland
			protonup-qt
			lutris	
			betterdiscordctl
			betterdiscord-installer
			ncspot
			librespot
			gamemode
			goverlay
			vscode.fhs
			gitFull
			baobab
			gimp
			gnome-text-editor
			pavucontrol
			steamtinkerlaunch
			yad
			unzip
			wget
			xdotool
			kdePackages.kdenlive
			protontricks
			winetricks
			wineWowPackages.waylandFull
			elegant-sddm
			file-roller
			xorg.xwininfo
			alacritty
			wofi
			wl-clipboard
			btop
			helvum
			grim
			grimblast
			gh
			mpv
			audacity
			stacer
			libvdpau
			libxcursor
			libvdpau-va-gl
			xorg.libXtst
			libei
			oh-my-zsh
			seatd
			pciutils
			zsh-syntax-highlighting
			libcap
			fastfetch
			slurp
			util-linux
			wl-clipboard
			libdecor
			polkit_gnome
			polkit
			jdk23
			libglvnd
			glew
			hyprlock
			hypridle
			eglexternalplatform
			egl-wayland
			mangohud
			pkgsi686Linux.mangohud
			nv-codec-headers-12
			curl
			config.boot.kernelPackages.nvidia_x11_beta
			config.boot.kernelPackages.nvidia_x11_beta_open
			libnvidia-container
			nvidia-vaapi-driver
			libxrender
			nvidia-vaapi-driver
			nvidia-docker
			nvidia_cg_toolkit
			nvidia-texture-tools
			nvidia-optical-flow-sdk
    	];
  	};
};
};


  





powerManagement = {
	scsiLinkPolicy = "max_performance";	
	enable = true;
	cpufreq = {
		min = 800;
		max = 5000;
	};
	cpuFreqGovernor = "performance";
	powertop.enable = false;
};




system = {
	autoUpgrade.enable = true;
	autoUpgrade.allowReboot = false;
	autoUpgrade.channel = "https://channels.nixos.org/nixos-unstable";
	stateVersion ="24.11";
};

services = {
	ananicy = {
    enable = true;
    package = pkgs.ananicy-cpp;
    rulesProvider = pkgs.ananicy-cpp;
    extraRules = [
      {
        "name" = "gamescope";
        "nice" = -20;
      }
    ];
  };
	blueman.enable = true;
	flatpak.enable = true;
	xrdp.audio.enable = true;
	gpsd.readonly = true;
	pulseaudio = {
		enable = false;
		package = pkgs.pulseaudioFull;
	};
	desktopManager.plasma6.enable = false;

	auto-cpufreq = {
		enable = true;
		settings = {
			battery = {
				governor = "performance";
				turbo = "always";
			};
			charger = {
				governor = "performance";
				turbo = "always";
			};
		};
	};



	cachix-watch-store = {
		enable = false;
		compressionLevel = 9;
	};

	userdbd.enable = true;
	sysprof.enable = true;

	udev = {
		packages = with pkgs; [ gnome-settings-daemon android-udev-rules];
		extraRules =  ''ACTION=="add|change", KERNEL=="sd[a-z]*[0-9]*|mmcblk[0-9]*p[0-9]*|nvme[0-9]*n[0-9]*p[0-9]*", ENV{ID_FS_TYPE}=="ext4", ATTR{../queue/scheduler}="mq-deadline"'';
		enable = true;
	};

	akkoma.extraPackages = with pkgs;[
		exiftool 
		graphicsmagick-imagemagick-compat
		nv-codec-headers-12
		ffmpeg-full
	];

	aesmd.enable = false;

	throttled.enable = true;

	undervolt = {
		enable = true;
		turbo = 0;
		useTimer = true;
		tempBat = 80;
		tempAc = 80;
		temp = 80;
	};

	epgstation.ffmpeg = pkgs.ffmpeg-full;

	system76-scheduler = {
		enable = true;
	};


	dbus = {
		packages = with pkgs; [
		glfw
		SDL
		inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
		inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
		xdg-desktop-portal
		xdg-desktop-portal-wlr
		sdl3
		SDL2
		gamescope
		gamescope-wsi
		pass-secret-service
		dbus
		kdePackages.kwin
    kdePackages.kwin-x11
		libxmu
    libsForQt5.kwindowsystem
    kdePackages.kwindowsystem
	 ];
	};
	fwupd.enable = true;
	upower.enable = true;


	tailscale.enable = false;

	#jack.loopback.enable = true;

	resolved = {
		enable = true;
		extraConfig = "DNS=194.242.2.4#base.dns.mullvad.net\n
				   	   DNSSEC=no\n
				   	   DNSOverTLS=yes\n
				   	   Domains=~\n";	
	};

	fstrim.enable = true;

	zfs.trim = {
		enable = true;	
	};

	printing.enable = false;

	avahi = {
  		enable = true;
  		nssmdns4 = true;
  		openFirewall = true;
	};

	displayManager = { 

		defaultSession = "hyprland-uwsm";

		sddm = {
			enable = true;
			wayland = {
				enable = true;
				#compositor = "kwin";
			};
			autoNumlock = true;
			enableHidpi = true;
			theme = "Elegant";
			settings = {
				Theme = {
					Current = "Elegant";
				};
			};
			extraPackages = with pkgs;[	
				qt6.full
				#elegant-sddm
			];
		};
	};


	pipewire = {
		enable = true;
		audio.enable = true;
		wireplumber.enable = true;
		systemWide = true;
		alsa.enable = true;
		alsa.support32Bit = true;
		pulse.enable = true;
		socketActivation = true;
		raopOpenFirewall = true;
		# If you want to use JACK applications, uncomment this
		#jack.enable = true;

		# use the example session manager (no others are packaged yet so this is enabled by default,
		# no need to redefine it in your config for now)
		#media-session.enable = true;
	};

	hypridle.enable = true;

	udisks2.enable = true;

	power-profiles-daemon.enable = false;

	cpupower-gui.enable = true;

	desktopManager.gnome.enable = false;
	
	displayManager.gdm.enable = false;
	# Enable the X11 windowing system.
	xserver = {

		xkb.layout = "gb";

		# Load nvidia driver for Xorg and Wayland
		videoDrivers = [ 
			"modesetting"   
			"i915" 
			"i965"
			"nvidia"
		];

		deviceSection = '''';

		modules = with pkgs; [
			xorg.xwininfo
			xorg.xhost
			xorg.libXres
			xorg.xrdb
			gamescope
			xorg.xf86videonv
			libavif
			libdecor
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			libei
			xorg_sys_opengl
			libcap
			xorg.libXcomposite
			xorg.libXi
			libxmu
			libxrender
			xorg.libXtst
			libxfixes
		];
		enable = true;
		#display = 1;
		desktopManager.runXdgAutostartIfNone = true;
		updateDbusEnvironment = true;
	};
};

nixpkgs = {
	config = {
		permittedInsecurePackages = [
                "dotnet-sdk-6.0.428"
              ];
		allowUnfreePredicate = pkg: 
		builtins.elem (lib.getName pkg) [
			"steam"
			"steam-original"
			"steam-run"
			"corefonts"
			"steamcmd"
		];

		packageOverrides = pkgs: {
    		vaapiIntel = pkgs.vaapiIntel.override { enableHybridCodec = true; };
  		};
		allowUnfree = true;
		nvidia.acceptLicense = true;
	};

	overlays = [
    	(final: prev: {
      		steam = prev.steam.override ({extraPkgs ? pkgs': [], ... }: {extraPkgs = pkgs': (extraPkgs pkgs') ++ (with pkgs'; [
	  	  		mangohud
          		libgdiplus
        	]);});
    	})
  	];
};


programs = {
	opengamepadui = {
		gamescopeSession = {
			enable = true;
		};
	};
	cdemu.enable = true;

	ssh.askPassword = lib.mkForce"${pkgs.x11_ssh_askpass}/libexec/x11-ssh-askpass}";

	tuxclocker = {
		enable = true; 
		useUnfree = true;
		enabledNVIDIADevices = 
			[
				0
				31
			];
	};

	obs-studio = {
		enableVirtualCamera = true;
		enable = true;
		plugins = with pkgs; [
		obs-studio-plugins.wlrobs
		obs-studio-plugins.obs-vkcapture
		obs-studio-plugins.obs-vaapi
		#obs-studio-plugins.obs-nvfbc
		]; 
		
		package = (pkgs.obs-studio.override {
            		cudaSupport = true;
        		});
	};

	coolercontrol = {
		enable = true;
		nvidiaSupport = true;
	};

	steam = {
		extest.enable = true;
		enable = true;
		remotePlay.openFirewall = true; # Open ports in the firewall for Steam Remote Play
		gamescopeSession.enable = true;
		localNetworkGameTransfers.openFirewall = true;
		protontricks.enable = true;

		package = pkgs.steam.override { 
			extraPkgs = pkgs: with pkgs; [
				xorg.libXcursor
				xorg.libXi
				xorg.libXinerama
				gamescope-wsi
				extest
				xorg.libXScrnSaver
				libpng
				libpulseaudio
				libvorbis
				stdenv.cc.cc.lib
				libkrb5
				keyutils
				gamescope
				mesa
				intel-media-driver 
				SDL
				gamemode
				sdl3
				xorg.libXi
				libxfixes
				libavif
				libcap
				xorg.libXres
				luajit
				libxmu
				libinput
				SDL2
        		bubblewrap
				xorg.libXcomposite
        		goldberg-emu
				wlr-protocols
				intel-vaapi-driver
				nvidia_oc
				nvidia-modprobe
				intel-gpu-tools
				libGL
				libxkbcommon
				libarchive
				openssl
				intel-graphics-compiler
				libx11
				spirv-tools
				inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
				inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
				vaapi-intel-hybrid
				cairo
				pixman
				intel-gmmlib
				vaapiIntel        
				vaapiVdpau
				xed
				mangohud
				libva
				libdrm
				egl-wayland
				libvdpau-va-gl
				libvdpau
				virtualglLib
				nv-codec-headers-12
				libvpl
				nvidia-vaapi-driver
				vulkan-extension-layer
				vulkan-utility-libraries
				mesa
				libdrm
				glfw
				glfw3-minecraft
				xorg.xf86videonv
				xorg.xf86inputevdev
				xorg.xf86inputlibinput
				seatd
				wlr-protocols
				egl-wayland
				nvidia-vaapi-driver
				libxrender
				xorg.xf86inputevdev
				xorg.xf86inputlibinput
				mangohud
				xorg.libXdamage
				pkgsi686Linux.mangohud
				vaapiVdpau
				libei
				vaapiIntel
				intel-gmmlib
				libdecor
				xorg.xf86videonv
				intel-vaapi-driver
				vaapi-intel-hybrid
				libxcursor
				nv-codec-headers-12
				vulkan-tools
				vulkan-loader
				vulkan-headers
				vulkan-tools-lunarg
				vulkan-extension-layer
				xorg.libXtst
				spirv-tools
				vulkan-utility-libraries
				nvidia_cg_toolkit
				nvidia-optical-flow-sdk
				nv-codec-headers-12
			];
			privateTmp = false; 
			extraLibraries = pkgs: with pkgs; [
				xorg.libXcursor
				xorg.libXi
				xorg.libXinerama
				xorg.libXScrnSaver
				gamemode
				gamescope-wsi
				libpng
				libpulseaudio
				libvorbis
				stdenv.cc.cc.lib
				libkrb5
				keyutils
				mesa
				intel-media-driver
				extest
				wlr-protocols
				intel-vaapi-driver
				libxmu
				intel-gpu-tools
				libinput
				xorg.libXres
				luajit
				seatd
				SDL
				libxfixes
				libavif
				bubblewrap
				xorg.libXcomposite
				goldberg-emu
				libcap
				sdl3
				SDL2
				intel-graphics-compiler
				spirv-tools
				vaapi-intel-hybrid
				cairo
				pixman
				intel-gmmlib
				vaapiIntel        
				vaapiVdpau
				libx11
				xed
				nvidia_oc
				mangohud
				libva
				libdrm
				egl-wayland
				libvdpau-va-gl
				libGL
				libxkbcommon
				libarchive
				openssl
				libvdpau
				virtualglLib
				nv-codec-headers-12
				libvpl
				nvidia-vaapi-driver
				vulkan-extension-layer
				vulkan-utility-libraries
				mesa
				libdrm
				glfw
				nvidia-modprobe
				glfw3-minecraft
				xorg.xf86videonv
				xorg.xf86inputevdev
				xorg.xf86inputlibinput
				wlr-protocols
				libdecor
				egl-wayland
				nvidia-vaapi-driver
				winetricks
				xorg.xf86inputevdev
				xorg.xf86inputlibinput
				libxrender
				mangohud
				pkgsi686Linux.mangohud
				vaapiVdpau
				libxcursor
				vaapiIntel
				intel-gmmlib
				xorg.libXtst
				xorg.xf86videonv
				intel-vaapi-driver
				vaapi-intel-hybrid
				nv-codec-headers-12
				vulkan-tools
				vulkan-loader
				vulkan-headers
				vulkan-extension-layer
				vulkan-validation-layers
				spirv-tools
				vulkan-utility-libraries
				nvidia_cg_toolkit
				nvidia-optical-flow-sdk
				nv-codec-headers-12
			];
		};

		extraPackages = with pkgs; [
			xorg.libXcursor
			xorg.libXi
			xorg.libXinerama
			gamescope-wsi
			xorg.libXScrnSaver
			libpng
			libpulseaudio
			libvorbis
			stdenv.cc.cc.lib
			libkrb5
			keyutils
			wlr-protocols
			egl-wayland
			seatd
			ffmpeg-full
			extest
			SDL
			libinput
			libxmu
			luajit
			libei
			libcap
			libavif
			gamemode
			libxfixes
			xorg.libXcomposite
			xorg.libXdamage
			sdl3
			SDL2
			xorg.libXres
			bubblewrap
			goldberg-emu
			nvidia-vaapi-driver
			winetricks
			wineWowPackages.waylandFull
			mesa
			xorg.xf86inputevdev
			libx11
			xorg.libXi
			xorg.xf86inputlibinput
			libnvidia-container
			mangohud
			libdecor
			libGL
			libxkbcommon
			libarchive
			openssl
			pkgsi686Linux.mangohud
			intel-compute-runtime
			pango
			libthai
			harfbuzz
			vaapiVdpau
			nvidia-modprobe
			vaapiIntel
			nvidia_oc
			intel-gmmlib
			intel-ocl
			intel-media-driver
			xorg.xf86videonv
			intel-vaapi-driver
			vaapi-intel-hybrid
			xorg.libXtst
			nv-codec-headers-12
			libxcursor
			vulkan-tools
			vulkan-loader
			vulkan-headers
			vulkan-tools-lunarg
			vulkan-extension-layer
			spirv-tools
			vulkan-utility-libraries
			cairo
			pixman
			config.boot.kernelPackages.nvidia_x11_beta
			config.boot.kernelPackages.nvidia_x11_beta_open
			nvidia-docker
			nvidia_cg_toolkit
			libadwaita
			libgtkflow4
			libgtkflow3
			gtk4
			libxrender
			gtk3-x11
			nvidia-texture-tools
			nvidia-optical-flow-sdk
			nv-codec-headers-12
		];

		extraCompatPackages =  with pkgs;[
			proton-ge-bin
		]; 
	};

	nix-ld = {
		enable = true;
		libraries =  with pkgs;[
			(discord-canary.override {
				withOpenASAR = true;
				withVencord = true; # can do this here too
			})
			steamcmd
			seatd
			libei
			spotifyd
			spotify-tray
			xorg.libXcomposite
			nvtopPackages.full
			npins
			extest
			gamemode
			libxmu
			gamescope-wsi
			gnome-software
			libcap
			xorg.libXi
			spotify-player
			librespot
			xorg.libXdamage
			xorg.libXres
			lxappearance
			kdePackages.kwin
			luajit
      		kdePackages.kwin-x11
	  		libinput
			libsForQt5.kwindowsystem
			kdePackages.kwindowsystem
			libxfixes
			gamescope
			xorg.libXcursor
			xorg.libXi
			xorg.libXinerama
			xorg.libXScrnSaver
			libpng
			libpulseaudio
			libvorbis
			stdenv.cc.cc.lib
			libkrb5
			keyutils
			libavif
			xorg.libXtst
			bubblewrap
			goldberg-emu
			libx11
			xorg_sys_opengl
			SDL
			sdl3
			SDL2
			libGL
			libxkbcommon
			libarchive
			openssl
			qbittorrent-nox
			libadwaita
			gtk4
			elegant-sddm
			gtk3-x11
			bumblebee
			nvidia-modprobe
			libgtkflow4
			libgtkflow3
			yt-dlp
			nvidia_oc
			discord-rpc
			vencord
			vencord-web-extension
			webcord-vencord
			direnv
			bc
			cairo
			pixman
			discord-canary
			dotnet-sdk_9 
			betterdiscordctl
			betterdiscord-installer
			discord-gamesdk
			lxappearance-gtk2
			pango
			libthai
			harfbuzz
			adwaita-qt6
			adwaita-icon-theme
			#inputs.envycontrol.packages.x86_64-linux.default
			cachix
			xsettingsd
			xorg.xrdb
			wlr-protocols
			lm_sensors
			libusbp
			libusb1
			xorg.xhost
			google-chrome
			librewolf-bin
			unrar-wrapper
			unrar
			unar
			unrar-free
			adwaita-icon-theme
			gnomeExtensions.appindicator
			gnome-settings-daemon
			gh
			coolercontrol.coolercontrol-gui
			coolercontrol.coolercontrold
			coolercontrol.coolercontrol-ui-data
			coolercontrol.coolercontrol-liqctld
			intel-media-driver 
			vaapiIntel        
			vaapiVdpau
			intel-gmmlib
			vaapi-intel-hybrid
			nodejs_22
			libva
			qt6.qtsvg
			libdrm
			egl-wayland
			libnvidia-container
			libvdpau-va-gl
			libvdpau
			virtualglLib
			intel-compute-runtime
			intel-compute-runtime
			nv-codec-headers-12
			intel-ocl
			ffmpeg-full
			nvidia-vaapi-driver
			vulkan-extension-layer
			spirv-tools
			vulkan-utility-libraries
			mesa
			libdrm
			xorg.xf86videonv
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			intel-vaapi-driver
			spotify
			zsh
			meson
			ninja
			jq
			lshw
			gparted
			gnome-disk-utility
			hyprcursor
			vim
			prismlauncher
			openal
			mlx42
			glfw
			glfw3-minecraft
			qt6.qtwayland
			protonup-qt
			lutris	
			ncspot
			librespot
			gamemode
			goverlay
			vscode.fhs
			gnumake
			gitFull
			baobab
			gimp
			gnome-text-editor
			pavucontrol
			yad
			libxrender
			unzip
			wget
			xdotool
			kdePackages.kdenlive
			protontricks
			winetricks
			wineWowPackages.waylandFull
			file-roller
			xorg.xwininfo
			alacritty
			wofi
			wl-clipboard
			btop
			helvum
			grim
			grimblast
			mpv
			audacity
			stacer
			libva
			virtualglLib
			libvdpau-va-gl
			vulkan-extension-layer
			vulkan-utility-libraries
			mesa
			glfw
			glfw3-minecraft
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			libnvidia-container
			intel-compute-runtime
			vaapiVdpau
			libxcursor
			vaapiIntel
			intel-media-driver
			nvidia-vaapi-driver
			xorg.xf86videonv
			intel-vaapi-driver
			nv-codec-headers-12
			ffmpeg-full
			config.boot.kernelPackages.nvidia_x11_beta
			config.boot.kernelPackages.nvidia_x11_beta_open
			libnvidia-container
			nvidia-vaapi-driver
			nvidia-vaapi-driver
			nvidia-docker
			nvidia_cg_toolkit
			nvidia-texture-tools
			nvidia-optical-flow-sdk
			pciutils
			zsh-syntax-highlighting
			fastfetch
			slurp
			util-linux
			wl-clipboard
			polkit_gnome
			polkit
			jdk23
			libglvnd
			glew
			hyprlock
			hypridle
			eglexternalplatform
			egl-wayland
			mangohud
			pkgsi686Linux.mangohud
			curl
			glibc
			xorg.xf86videonv
			chiaki-ng
			intel-vaapi-driver
			libnvidia-container
			glib
			virtualglLib
			glibmm
			libglibutil
			glibcInfo
			glibc_multi
			glibcLocales
			libdrm
			mesa
			glibc_memusage
			glibcLocalesUtf8
			liquidctl
			iconv
			libiconv
			gfortran
			gdb
			polkit_gnome
			libva-utils
			nvidia-vaapi-driver
			nvidia-docker
			nvidia_cg_toolkit
			nvidia-texture-tools
			nvidia-optical-flow-sdk
			nv-codec-headers-12
			xdg-utils
			xdg-desktop-portal
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
			nautilus
			libcdada
			vulkan-tools
			libva
			virtualglLib
			libvdpau-va-gl
			vulkan-extension-layer
			vulkan-utility-libraries
			mesa
			glfw
			glfw3-minecraft
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			libnvidia-container
			intel-compute-runtime
			vaapiVdpau
			libxcursor
			vaapiIntel
			intel-media-driver
			nvidia-vaapi-driver
			xorg.xf86videonv
			intel-vaapi-driver
			nv-codec-headers-12
			ffmpeg-full
			config.boot.kernelPackages.nvidia_x11_beta
			config.boot.kernelPackages.nvidia_x11_beta_open
			libnvidia-container
			nvidia-vaapi-driver
			nvidia-vaapi-driver
			nvidia-docker
			nvidia_cg_toolkit
			nvidia-texture-tools
			nvidia-optical-flow-sdk
			ffmpeg-full
			onlyoffice-bin
			wineWowPackages.stable
			winetricks
			waybar
			mako
			vulkan-tools
			vulkan-loader
			vulkan-headers
			vulkan-tools-lunarg
			flatpak
			vulkan-extension-layer
			vulkan-utility-libraries
			libva
			virtualglLib
			libvdpau-va-gl
			vulkan-extension-layer
			libdecor
			vulkan-utility-libraries
			mesa
			glfw
			glfw3-minecraft
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			libnvidia-container
			intel-compute-runtime
			vaapiVdpau
			libxcursor
			vaapiIntel
			intel-media-driver
			nvidia-vaapi-driver
			xorg.xf86videonv
			intel-vaapi-driver
			nv-codec-headers-12
			ffmpeg-full
			config.boot.kernelPackages.nvidia_x11_beta
			config.boot.kernelPackages.nvidia_x11_beta_open
			libnvidia-container
			nvidia-vaapi-driver
			nvidia-vaapi-driver
			nvidia-docker
			nvidia_cg_toolkit
			nvidia-texture-tools
			nvidia-optical-flow-sdk
		]; 
	};

	gamescope = {
		enable = true; 
		capSysNice = false;
		package = pkgs.gamescope;
	};

	adb.enable = true;

	xwayland.enable = true;

	iio-hyprland.enable = false;

	hyprland = {
		withUWSM = true;
		# Install the packages from nixpkgs
		enable = true;
		# Whether to enable XWayland
		xwayland.enable = true;
		package = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland;
		portalPackage = inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland;
		systemd.setPath.enable = true;
	};

	waybar.enable = true;

	dconf.enable = true;

	hyprlock.enable = true;

	gamemode = {
		enable = true;
		enableRenice = true;
		settings = {
			general = {
				desiredgov = "performance";
				igpu_desiredgov = "performance";
				igpu_power_threshold = 0.9;
				softrealtime = "on";
				renice = 20;
				ioprio = 0;
				inhibit_screensaver = 1;
				disable_splitlock = 1;
			};
			gpu = {
				apply_gpu_optimisations = "accept-responsibility";
				gpu_device = 1;
				nv_powermizer_mode= 1;
			};
			cpu = {
				park_cores = 1;
				pin_cores = 1;		
			};
		};
	};

	chromium = {
		enable = true;
	};



	firefox = {
		package = pkgs.librewolf-bin;
		enable = false;
		preferencesStatus = "user";
		preferences = {
		 	"media.ffmpeg.vaapi.enabled" = true;
		 	"media.ffvpx.enabled" = true;
		 	"media.av1.enabled" = true;
		 	"gfx.webrender.all" = true;
		 	"widget.wayland.opaque-region.enabled" = true;
		 	"layout.frame_rate" = 100;
		 	"browser.tabs.tabmanager.enabled" = true;
		 };
		 nativeMessagingHosts = {
		 	packages =  with pkgs; [
				uget-integrator 
		 		tridactyl-native
		 		passff-host 
		 		jabref  
		 		fx-cast-bridge 
		 		ff2mpv 
		 		web-eid-app 
		 		browserpass 
		 	];
		 };
	};

	gnome-disks.enable = true;

	appimage = {
		enable = true;
		binfmt = true;
		package = pkgs.appimage-run.override {
			extraPkgs = pkgs: [ pkgs.ffmpeg-full ];
		};	
	};

	zsh = {
		enable = true;
		shellAliases = {
			ssteam = "nohup steam-run steam -no-cef-sandbox --vgui --no-cef-sandbox -vgui &";
			update = "cd /etc/nixos &&
			 sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair &&
			 sudo nix flake update --accept-flake-config --refresh --repair &&
			 sudo nix-channel --update &&
			 sudo nix-store --optimise &&
			 sudo nix-store --verify --check-contents --repair";
			buildupdate = "sudo nixos-rebuild switch --accept-flake-config --cores 10 --max-jobs --show-trace --upgrade-all --verbose --keep-going --fallback --recreate-lock-file --flake '/etc/nixos#nixos' ";
			ultraupdate = "cd /etc/nixos &&
			 sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair &&
			 sudo nix flake update --accept-flake-config --refresh --repair &&
			 sudo nix-channel --update &&
			 sudo nix-store --optimise &&
			 sudo nix-store --verify --check-contents --repair &&
			 sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --upgrade-all --verbose --keep-going --fallback --recreate-lock-file --flake '/etc/nixos#nixos' &&
			 sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --repair --verbose --keep-going --fallback &&
			 sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair &&
			 sudo nix-channel --update &&
			 sudo nixos-rebuild boot --accept-flake-config --cores 11 -j 1 --show-trace --upgrade-all --repair --fallback --verbose --keep-going &&
			 sudo nix-collect-garbage --delete-older-than 2d &&
			 sudo nix-store --gc &&
			 sudo nix-store --optimise &&
			 sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair &&
			 sudo nix flake update --accept-flake-config --refresh --repair &&
			 sudo nix-channel --update &&
			 sudo nix-store --verify --check-contents --repair &&
			 sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --upgrade-all --verbose --keep-going --fallback --recreate-lock-file --flake '/etc/nixos#nixos' &&
			 sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --repair --fallback --verbose --keep-going &&
			 sudo nixos-rebuild boot --accept-flake-config --cores 11 -j 1 --show-trace --repair --fallback --verbose --keep-going";
		};
		histSize = 10000;
		histFile = "/home/p2949/zsh/history";
		syntaxHighlighting = { 
			enable = true;
		};
		ohMyZsh = {
			enable = true;
			theme = "robbyrussell";
		};
	};

	uwsm = {
		enable = true;
		waylandCompositors = {
			hyprland = {
  				prettyName = "Hyprland";
  				comment = "Hyprland compositor managed by UWSM";
  				binPath = "/run/current-system/sw/bin/Hyprland";
			};
		};
	};

	java = { 
		enable = true; 
		package = pkgs.jdk23; 
	};		
};

}
