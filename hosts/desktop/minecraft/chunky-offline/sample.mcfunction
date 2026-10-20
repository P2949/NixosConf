# Sample one player per occupied dimension; random selection avoids list-order bias.
$execute in $(world) as @a[distance=0..,sort=random,limit=1] run function chunky_offline:record {key:"$(key)",threshold:$(threshold)}
