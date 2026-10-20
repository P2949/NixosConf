# Axis distances match square targets and avoid overflow from squared coordinates.
$data modify storage chunky_offline:tracking $(key).pending set value 0b
$execute store result score #dx co_control run data get storage chunky_offline:tracking $(key).lastActivityX
$execute store result score #dz co_control run data get storage chunky_offline:tracking $(key).lastActivityZ
$execute store result score #cx co_control run data get storage chunky_offline:tracking $(key).centerX
$execute store result score #cz co_control run data get storage chunky_offline:tracking $(key).centerZ
scoreboard players operation #dx co_control -= #cx co_control
scoreboard players operation #dz co_control -= #cz co_control
$execute if score #dx co_control matches $(threshold).. run data modify storage chunky_offline:tracking $(key).pending set value 1b
$execute if score #dx co_control matches ..-$(threshold) run data modify storage chunky_offline:tracking $(key).pending set value 1b
$execute if score #dz co_control matches $(threshold).. run data modify storage chunky_offline:tracking $(key).pending set value 1b
$execute if score #dz co_control matches ..-$(threshold) run data modify storage chunky_offline:tracking $(key).pending set value 1b
$execute if data storage chunky_offline:tracking $(key){hasTask:0b} run data modify storage chunky_offline:tracking $(key).pending set value 1b
