# Chebyshev distance matches square targets without squaring coordinates.
$execute store result score #cx co_control run data get storage chunky_offline:tracking $(key).centerX
$execute store result score #cz co_control run data get storage chunky_offline:tracking $(key).centerZ
scoreboard players operation #dx co_control -= #cx co_control
scoreboard players operation #dz co_control -= #cz co_control
scoreboard players set #negative co_control -1
execute if score #dx co_control matches ..-1 run scoreboard players operation #dx co_control *= #negative co_control
execute if score #dz co_control matches ..-1 run scoreboard players operation #dz co_control *= #negative co_control
scoreboard players operation #distance co_control = #dx co_control
scoreboard players operation #distance co_control > #dz co_control
