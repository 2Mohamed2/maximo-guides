# MLD (car, truck, bike): live speed updates possible
osrm-extract -p /opt/truck.lua ma.osm.pbf
osrm-partition ma.osrm
osrm-customize ma.osrm

# CH (foot): fastest queries, no live updates
osrm-extract -p /opt/foot.lua ma.osm.pbf
osrm-contract ma.osrm
