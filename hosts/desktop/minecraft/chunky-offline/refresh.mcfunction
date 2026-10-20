# UUID equality via data-modify success: unchanged means the same owner.
$execute unless data storage chunky_offline:tracking $(key).owner run return 0
$data modify storage chunky_offline:tracking sampleOwner set from storage chunky_offline:tracking $(key).owner
execute store success score #different co_control run data modify storage chunky_offline:tracking sampleOwner set from entity @s UUID
data remove storage chunky_offline:tracking sampleOwner
$execute if score #different co_control matches 0 run function chunky_offline:record {key:"$(key)",threshold:$(threshold)}
