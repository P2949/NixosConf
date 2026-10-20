# Only transitions run Chunky commands. Position work runs every 200 online ticks.
execute if entity @a run function chunky_offline:online
execute unless entity @a unless score #online co_control matches 0 run function chunky_offline:offline
# Discover a first visit immediately, even if it lasts less than the sample interval.
execute in minecraft:the_nether unless data storage chunky_offline:tracking nether{enabled:1b} if entity @a[distance=0..] run function chunky_offline:track
execute in minecraft:the_end unless data storage chunky_offline:tracking end{enabled:1b} if entity @a[distance=0..] run function chunky_offline:track
