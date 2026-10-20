# World storage survives restarts; adopt the running Overworld job unchanged.
scoreboard objectives add co_control dummy
scoreboard players set #online co_control -1
scoreboard players set #ticks co_control 0
execute unless data storage chunky_offline:tracking overworld run data modify storage chunky_offline:tracking overworld set value {enabled:1b,hasTask:1b,centerX:0,centerZ:0,lastActivityX:0,lastActivityZ:0,pending:0b}
execute unless data storage chunky_offline:tracking nether run data modify storage chunky_offline:tracking nether set value {enabled:0b,hasTask:0b,centerX:0,centerZ:0,lastActivityX:0,lastActivityZ:0,pending:0b}
execute unless data storage chunky_offline:tracking end run data modify storage chunky_offline:tracking end set value {enabled:0b,hasTask:0b,centerX:0,centerZ:0,lastActivityX:0,lastActivityZ:0,pending:0b}
