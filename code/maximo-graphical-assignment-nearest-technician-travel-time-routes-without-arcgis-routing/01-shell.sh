osrm-extract   -p /opt/car.lua region.osm.pbf     # read roads, speeds, turn rules
osrm-partition region.osrm                         # split the graph into cells
osrm-customize region.osrm                         # pre-compute travel costs per cell
osrm-routed --algorithm mld --max-table-size 10000 region.osrm   # serve on port 5000
