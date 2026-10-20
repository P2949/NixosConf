execute store result score #dx co_control run data get entity @s Pos[0] 1
execute store result score #dz co_control run data get entity @s Pos[2] 1
$function chunky_offline:distance {key:"$(key)"}
$execute if score #distance co_control > #best co_control run function chunky_offline:record {key:"$(key)",threshold:$(threshold)}
execute if score #distance co_control > #best co_control run scoreboard players operation #best co_control = #distance co_control
