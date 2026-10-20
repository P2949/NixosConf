$data modify storage chunky_offline:tracking $(key).enabled set value 1b
$execute store result storage chunky_offline:tracking $(key).lastActivityX int 1 run data get entity @s Pos[0] 1
$execute store result storage chunky_offline:tracking $(key).lastActivityZ int 1 run data get entity @s Pos[2] 1
$function chunky_offline:evaluate {key:"$(key)",threshold:$(threshold)}
