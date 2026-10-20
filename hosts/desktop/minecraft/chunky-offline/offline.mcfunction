# Recheck latest samples at departure; never change a task while players are online.
execute if entity @a run return 0
function chunky_offline:policy {operation:"apply"}
function chunky_offline:command {command:"chunky continue"}
scoreboard players set #online co_control 0
