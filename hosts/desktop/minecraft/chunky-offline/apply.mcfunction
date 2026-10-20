$execute unless data storage chunky_offline:tracking $(key){enabled:1b} run return 0
$function chunky_offline:evaluate {key:"$(key)",threshold:$(threshold)}
$execute unless data storage chunky_offline:tracking $(key){pending:1b} run return 0
$data modify storage chunky_offline:tracking target set from storage chunky_offline:tracking $(key)
$data modify storage chunky_offline:tracking target.key set value "$(key)"
$data modify storage chunky_offline:tracking target.world set value "$(world)"
$data modify storage chunky_offline:tracking target.radius set value $(radius)
function chunky_offline:replace with storage chunky_offline:tracking target
data remove storage chunky_offline:tracking target
