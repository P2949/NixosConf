# Refresh the candidate owner first, then compare every player in this dimension.
$execute in $(world) unless entity @a[distance=0..] run return 0
$execute in $(world) as @a[distance=0..] run function chunky_offline:refresh {key:"$(key)",threshold:$(threshold)}
$function chunky_offline:evaluate {key:"$(key)",threshold:$(threshold)}
scoreboard players set #best co_control -1
$execute if data storage chunky_offline:tracking $(key){enabled:1b,pending:1b} run scoreboard players operation #best co_control = #distance co_control
$execute in $(world) as @a[distance=0..] run function chunky_offline:candidate {key:"$(key)",threshold:$(threshold)}
