$data modify storage chunky_offline:tracking $(key).pending set value 0b
$execute store result score #dx co_control run data get storage chunky_offline:tracking $(key).lastActivityX
$execute store result score #dz co_control run data get storage chunky_offline:tracking $(key).lastActivityZ
$function chunky_offline:distance {key:"$(key)"}
$execute if score #distance co_control matches $(threshold).. run data modify storage chunky_offline:tracking $(key).pending set value 1b
$execute if data storage chunky_offline:tracking $(key){hasTask:0b} run data modify storage chunky_offline:tracking $(key).pending set value 1b
