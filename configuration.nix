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
		sandbox = true;
		experimental-features = [ 
			"nix-command" 
			"flakes" 
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

	enableAllFirmware = true;

	cpu.x86.msr.enable = true;

	sensor.iio.enable = false;

	graphics = {
		enable = true;
		enable32Bit = true;

    	extraPackages = with pkgs; [
			mesa.opencl
			intel-media-driver 
			wlr-protocols
			intel-gpu-tools
			intel-graphics-compiler
			intel-media-sdk
			spirv-tools
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
			vpl-gpu-rt
			vaapi-intel-hybrid
			intel-gmmlib
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
			libvdpau-va-gl
			libvdpau
			vulkan-extension-layer
			vulkan-utility-libraries
			vaapiVdpau
			libvdpau-va-gl
			nvidia-vaapi-driver
			libva
			vaapiVdpau
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
			libva
			freetype
			intel-gpu-tools
			libvpl
			cairo
			libdrm
			mangohud
			virtualglLib
			libvdpau-va-gl
			libvdpau
			cairo
			pixman
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
		opencl.enable = false;
		amdvlk = {
	 		supportExperimental.enable = false;
	 		support32Bit.enable = false;
	 		enable = false;
	 	};
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
		power-daemon.enable = false;
		kernel-modules.enable = false;
		firmware-daemon.enable = true;
		enableAll = true;
	};

	nvidia = {
		forceFullCompositionPipeline = true;
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
		dynamicBoost.enable = false;
		gsp.enable = true;
		nvidiaPersistenced = true;
		# Modesetting is required.
		modesetting.enable = true;
		# Nvidia power management. Experimental, and can cause sleep/suspend to fail.
		powerManagement.enable = true;
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
		open = true;
		# Enable the Nvidia settings menu,
		# accessible via `nvidia-settings`.
		nvidiaSettings = true;
		# Optionally, you may need to select the appropriate driver version for your specific GPU.
		#package = config.boot.kernelPackages.nvidiaPackages.stable;
		package = config.boot.kernelPackages.nvidiaPackages.beta;
  	};
	nvidiaOptimus.disable = false;

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
		GDK_BACKEND = "wayland,x11";
		QT_QPA_PLATFORM="wayland;xcb";
		QT_AUTO_SCREEN_SCALE_FACTOR = "1";
		XDG_CURRENT_DESKTOP = "Hyprland";
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
		#VK_DRIVER_FILES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver-32/share/vulkan/icd.d/intel_icd.i686.json";
		#VK_ICD_FILENAMES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver-32/share/vulkan/icd.d/intel_icd.i686.json";
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
		steamcmd
		spotifyd
		spotify-tray
		spotify-player
		librespot 
		yt-dlp
		godot_4
		godot_4-export-templates
		dotnet-sdk_9
		xorg_sys_opengl
		elegant-sddm
		lxappearance
		cairo
		gh
		pixman
		lxappearance-gtk2
		adwaita-qt
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
		xorg.xrdb
		lm_sensors
		wlr-protocols
		libusbp
		librewolf
		google-chrome
		libusb1
		inputs.envycontrol.packages.x86_64-linux.default
		adwaita-icon-theme
		unrar-wrapper
		unrar
		unar
		tailscale-systray
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
		gnome2.GConf
		glibc
		steamtinkerlaunch
		vaapi-intel-hybrid
		clang
		direnv
		clang-tools
		intel-gmmlib
		clang_multi
		libclang
		qt6.qtsvg
		xorg.xf86videonv
		intel-vaapi-driver
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
		gnat
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
		libgcc
		libgccjit
		gccgo
		gcc_multi
		gcc
		nautilus
		libcdada
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
		librespot
		winetricks
		waybar
		mako
		vulkan-tools
		vulkan-loader
		vulkan-headers
		vulkan-tools-lunarg
		vulkan-extension-layer
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
		"kernel/sched_autogroup_enabled" = 1;
		"vm.swappiness" = 90; # when swapping to ssd, otherwise change to 1
		"vm.vfs_cache_pressure" = 50;
		"vm.dirty_background_ratio" = 20;
		"vm.dirty_ratio" = 50;
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
    ./cachix.nix
];

systemd = {

	network.enable = false;

	globalEnvironment = {
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
        GDK_BACKEND = "wayland,x11";
        QT_QPA_PLATFORM="wayland;xcb";
        QT_AUTO_SCREEN_SCALE_FACTOR = "1";
        XDG_CURRENT_DESKTOP = "Hyprland";
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
		#VK_DRIVER_FILES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver-32/share/vulkan/icd.d/intel_icd.i686.json";
		#VK_ICD_FILENAMES = "/run/opengl-driver/share/vulkan/icd.d/intel_icd.x86_64.json:/run/opengl-driver-32/share/vulkan/icd.d/intel_icd.i686.json";
		__GLX_VENDOR_LIBRARY_NAME = "mesa";
		AMD_VULKAN_ICD = "RADV";
		NVD_BACKEND = "direct";
		NIXPKGS_ALLOW_UNFREE = "1";

	};

	services = {
		systemd-udev-settle.enable = true;
		NetworkManager-wait-online.enable = true;
	};

	extraConfig = ''
		DefaultCPUAccounting=yes
		DefaultMemoryAccounting=yes
		DefaultIOAccounting=yes
    '';

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

	users.p2949 = {
		shell = pkgs.zsh;
		useDefaultShell = true;
		isNormalUser = true;
		description = "Pedro Goraieb Fernandes";
		extraGroups = [ 
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
			spotifyd
			steamcmd
			spotify-tray
			spotify-player
			librespot
			adwaita-qt
			direnv
			bc
			godot_4
			godot_4-export-templates
			dotnet-sdk_9
			yt-dlp 
			lxappearance
			xorg_sys_opengl
			vencord
			vencord-web-extension
			webcord-vencord
			(discord-canary.override {
      			withOpenASAR = true;
    			withVencord = true; # can do this here too
    		})
			discord-gamesdk
			discord-rpc
			cairo
			pixman
			discord-canary
			lxappearance-gtk2
			adwaita-qt6
			adwaita-icon-theme
			ventoy-full
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
			librewolf
			clang
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.hyprland
			inputs.hyprland.packages.${pkgs.stdenv.hostPlatform.system}.xdg-desktop-portal-hyprland
			inputs.envycontrol.packages.x86_64-linux.default
			tailscale-systray
			xorg.xhost
			unrar-wrapper
			unrar
			unar
			libusbp
			libusb1
			spirv-tools
			google-chrome
			unrar-free
			adwaita-icon-theme
			gnomeExtensions.appindicator
			gnome-settings-daemon
			gnome2.GConf
			clang-tools
			clang_multi
			libgcc
			libgccjit
			gccgo
			gcc_multi
			gcc
			gnat
			libclang
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
			libsForQt5.kdenlive
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
			libvdpau-va-gl
			oh-my-zsh
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
			obs-studio
			obs-studio-plugins.wlrobs
			obs-studio-plugins.obs-backgroundremoval
			obs-studio-plugins.obs-pipewire-audio-capture
			obs-studio-plugins.waveform
			obs-studio-plugins.obs-websocket
			mangohud
			pkgsi686Linux.mangohud
			nv-codec-headers-12
			curl
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
	pulseaudio.enable = false;

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


	dbus.packages = with pkgs; [ gnome2.GConf ];
	fwupd.enable = true;
	upower.enable = true;


	tailscale.enable = true;

	jack.loopback.enable = true;

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
			wayland.enable = true;
			autoNumlock = true;
			enableHidpi = true;
			theme = "Elegant";
			settings = {
				Theme = {
					Current = "Elegant";
				};
			};
			extraPackages = with pkgs;[	
				#qt6.full
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
		# If you want to use JACK applications, uncomment this
		jack.enable = true;

		# use the example session manager (no others are packaged yet so this is enabled by default,
		# no need to redefine it in your config for now)
		#media-session.enable = true;
	};

	hypridle.enable = true;

	udisks2.enable = true;

	power-profiles-daemon.enable = false;

	cpupower-gui.enable = true;

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
			xorg.xrdb
			xorg.xf86videonv
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			xorg_sys_opengl
		];
		enable = true;
		#display = 1;
		desktopManager.gnome.enable = false;
		displayManager.gdm.enable = false;
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
				mesa
				intel-media-driver 
				wlr-protocols
				intel-vaapi-driver
				intel-gpu-tools
				intel-graphics-compiler
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
				wlr-protocols
				egl-wayland
				nvidia-vaapi-driver
				xorg.xf86inputevdev
				xorg.xf86inputlibinput
				mangohud
				pkgsi686Linux.mangohud
				vaapiVdpau
				vaapiIntel
				intel-gmmlib
				xorg.xf86videonv
				intel-vaapi-driver
				vaapi-intel-hybrid
				nv-codec-headers-12
				vulkan-tools
				vulkan-loader
				vulkan-headers
				vulkan-tools-lunarg
				vulkan-extension-layer
				spirv-tools
				vulkan-utility-libraries
				nvidia_cg_toolkit
				nvidia-optical-flow-sdk
				nv-codec-headers-12
			];
			#privateTmp = false; 
			extraLibraries = pkgs: with pkgs; [
				mesa
				intel-media-driver 
				wlr-protocols
				intel-vaapi-driver
				intel-gpu-tools
				intel-graphics-compiler
				spirv-tools
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
				wlr-protocols
				egl-wayland
				nvidia-vaapi-driver
				winetricks
				xorg.xf86inputevdev
				xorg.xf86inputlibinput
				mangohud
				pkgsi686Linux.mangohud
				vaapiVdpau
				vaapiIntel
				intel-gmmlib
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
			wlr-protocols
			egl-wayland
			ffmpeg-full
			nvidia-vaapi-driver
			winetricks
			wineWowPackages.waylandFull
			mesa
			xorg.xf86inputevdev
			xorg.xf86inputlibinput
			libnvidia-container
			mangohud
			pkgsi686Linux.mangohud
			intel-compute-runtime
			pango
			libthai
			harfbuzz
			vaapiVdpau
			vaapiIntel
			intel-gmmlib
			intel-ocl
			intel-media-driver
			xorg.xf86videonv
			intel-vaapi-driver
			vaapi-intel-hybrid
			nv-codec-headers-12
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
			spotifyd
			spotify-tray
			spotify-player
			librespot
			lxappearance
			xorg_sys_opengl
			libadwaita
			gtk4
			elegant-sddm
			gtk3-x11
			libgtkflow4
			libgtkflow3
			yt-dlp
			discord-rpc
			vencord
			vencord-web-extension
			webcord-vencord
			direnv
			bc
			cairo
			pixman
			discord-canary
			godot_4
			godot_4-export-templates
			dotnet-sdk_9 
			betterdiscordctl
			betterdiscord-installer
			discord-gamesdk
			lxappearance-gtk2
			pango
			libthai
			harfbuzz
			adwaita-qt
			adwaita-qt6
			adwaita-icon-theme
			inputs.envycontrol.packages.x86_64-linux.default
			clang
			cachix
			xsettingsd
			xorg.xrdb
			wlr-protocols
			lm_sensors
			libusbp
			libusb1
			xorg.xhost
			google-chrome
			librewolf
			unrar-wrapper
			unrar
			unar
			unrar-free
			tailscale-systray
			adwaita-icon-theme
			gnomeExtensions.appindicator
			gnome-settings-daemon
			gh
			gnome2.GConf
			clang-tools
			clang_multi
			libclang
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
			gitFull
			baobab
			gimp
			gnome-text-editor
			pavucontrol
			yad
			unzip
			wget
			xdotool
			libsForQt5.kdenlive
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
			oh-my-zsh
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
			obs-studio
			obs-studio-plugins.wlrobs
			obs-studio-plugins.obs-backgroundremoval
			obs-studio-plugins.obs-pipewire-audio-capture
			obs-studio-plugins.waveform
			obs-studio-plugins.obs-websocket
			mangohud
			pkgsi686Linux.mangohud
			curl
			glibc
			xorg.xf86videonv
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
			gnat
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
			libgcc
			libgccjit
			gccgo
			gcc_multi
			gcc
			nautilus
			libcdada
			vulkan-tools
			wireplumber
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
			vulkan-extension-layer
			vulkan-utility-libraries
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
		capSysNice = true;
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
		package = pkgs.librewolf;
		enable = false;
		preferencesStatus = "user";
		preferences = {
			"media.ffmpeg.vaapi.enabled" = true;
			"media.ffvpx.enabled" = true;
			"media.av1.enabled" = true;
			"gfx.webrender.all" = true;
			"widget.wayland.opaque-region.enabled" = false;
			"layout.frame_rate" = 75;
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
			update = "cd /etc/nixos && sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair && sudo nix flake update --accept-flake-config --refresh --repair && sudo nix-channel --update && sudo nix-store --optimise && sudo nix-store --verify --check-contents --repair && sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --upgrade-all --verbose --keep-going --fallback --recreate-lock-file --flake '/etc/nixos#nixos' && sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --repair --verbose --keep-going --fallback && sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair && sudo nix-channel --update && sudo nixos-rebuild boot --accept-flake-config --cores 11 -j 1 --show-trace --upgrade-all --repair --fallback --verbose --keep-going && sudo nix-collect-garbage --delete-older-than 2d && sudo nix-store --gc && sudo nix-store --optimise && sudo nix flake check --accept-flake-config --all-systems --recreate-lock-file --refresh --repair && sudo nix flake update --accept-flake-config --refresh --repair && sudo nix-channel --update && sudo nix-store --verify --check-contents --repair && sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --upgrade-all --verbose --keep-going --fallback --recreate-lock-file --flake '/etc/nixos#nixos' && sudo nixos-rebuild switch --accept-flake-config --cores 11 -j 1 --show-trace --repair --fallback --verbose --keep-going && sudo nixos-rebuild boot --accept-flake-config --cores 11 -j 1 --show-trace --repair --fallback --verbose --keep-going";
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
