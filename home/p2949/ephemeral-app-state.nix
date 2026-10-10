# Relative application paths whose contents are root-local even though the
# surrounding profile is persistent. Keep this metadata-only list audited.
[
  {
    parent = "Development";
    children = [
      "Unity/VR-AR-project/Logs"
      "Unity/VR-AR-project/Temp"
      "Unity/VR-AR-project-2/Logs"
      "Unity/VR-AR-project-2/Temp"
      "Unreal/Projects/AI_Gavin_Project/Intermediate"
      "Unreal/Projects/AI_Gavin_Project/Saved/Logs"
      "Unreal/Projects/AI_Gavin_Project/Saved/ShaderDebugInfo"
      "Unreal/Projects/AI_Gavin_Project/Saved/UnrealBuildTool"
    ];
  }
  {
    parent = ".codex";
    children = [
      ".tmp"
      "tmp"
      "cache"
      "ipc"
      "shell_snapshots"
      "thread-writer-locks"
    ];
  }
  {
    parent = ".android";
    children = [ "cache" ];
  }
  {
    parent = ".config/Code";
    children = [
      "Cache"
      "CachedData"
      "CachedConfigurations"
      "CachedExtensionVSIXs"
      "CachedProfilesData"
      "Code Cache"
      "Crashpad"
      "DawnGraphiteCache"
      "DawnWebGPUCache"
      "GPUCache"
      "logs"
      "blob_storage"
      "Service Worker/CacheStorage"
      "Service Worker/ScriptCache"
      "Shared Dictionary/cache"
    ];
  }
  {
    parent = ".config/mozilla/firefox";
    children = [
      "Crash Reports"
      "Pending Pings"
      "firefox-mpris"
      "y34aofre.default/cache2"
      "y34aofre.default/startupCache"
      "y34aofre.default/shader-cache"
      "y34aofre.default/thumbnails"
      "y34aofre.default/minidumps"
      "y34aofre.default/crashes"
      "y34aofre.default/datareporting"
      "y34aofre.default/saved-telemetry-pings"
    ];
  }
  {
    parent = ".config/unityhub";
    children = [
      "Cache"
      "Code Cache"
      "Crashpad"
      "DawnGraphiteCache"
      "DawnWebGPUCache"
      "GPUCache"
      "logs"
      "sentry"
      "graphqlCache"
      "VideoDecodeStats"
      "Service Worker/CacheStorage"
      "Service Worker/ScriptCache"
      "Shared Dictionary/cache"
    ];
  }
  {
    parent = ".config/Epic";
    children = [
      "UnrealBuildTool"
      "UnrealEngine/Intermediate"
      "UnrealEngine/5.8/Intermediate"
      "UnrealEngine/5.8/Saved/Logs"
      "UnrealEngine/5.8/Saved/ShaderDebugInfo"
      "UnrealEngine/Common/Analytics"
      "UnrealEngine/Editor/webcache_6613/ShaderCache"
      "UnrealEngine/Editor/webcache_6613/GrShaderCache"
      "UnrealEngine/Editor/webcache_6613/GraphiteDawnCache"
      "UnrealEngine/Editor/webcache_6613/Default/Cache"
      "UnrealEngine/Editor/webcache_6613/Default/Code Cache"
      "UnrealEngine/Editor/webcache_6613/Default/GPUCache"
      "UnrealEngine/Editor/webcache_6613/Default/Shared Dictionary/cache"
    ];
  }
  {
    parent = ".local/share/Steam";
    children = [
      "appcache"
      "depotcache"
      "logs"
      "config/avatarcache"
      "config/htmlcache/ShaderCache"
      "config/htmlcache/GrShaderCache"
      "config/htmlcache/GraphiteDawnCache"
      "config/htmlcache/Default/Cache"
      "config/htmlcache/Default/Code Cache"
      "config/htmlcache/Default/GPUCache"
      "steamapps/downloading"
      "steamapps/temp"
      "userdata/1031954223/ugcmsgcache"
      "userdata/1031954223/inventorymsgcache"
      "userdata/1031954223/ugsmsgcache"
    ];
  }
]
