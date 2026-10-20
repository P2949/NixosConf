execute unless score #online co_control matches 1 run function chunky_offline:command {command:"chunky pause"}
execute unless score #online co_control matches 1 run scoreboard players set #ticks co_control 200
scoreboard players set #online co_control 1
scoreboard players add #ticks co_control 1
execute if score #ticks co_control matches 200.. run function chunky_offline:track
