execute if entity @a run return 0
# Never use global cancel or implicit selection. Confirm each dimension independently.
$function chunky_offline:command {command:"chunky cancel $(world)"}
function chunky_offline:command {command:"chunky confirm"}
$function chunky_offline:command {command:"chunky start $(world) square $(lastActivityX) $(lastActivityZ) $(radius)"}
function chunky_offline:command {command:"chunky confirm"}
$data modify storage chunky_offline:tracking $(key).centerX set from storage chunky_offline:tracking $(key).lastActivityX
$data modify storage chunky_offline:tracking $(key).centerZ set from storage chunky_offline:tracking $(key).lastActivityZ
$data modify storage chunky_offline:tracking $(key).hasTask set value 1b
$data modify storage chunky_offline:tracking $(key).pending set value 0b
$data remove storage chunky_offline:tracking $(key).owner
