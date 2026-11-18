mkdir -p /srv/osrm && cd /srv/osrm
curl -fSL -o region.osm.pbf https://download.geofabrik.de/asia/gcc-states-latest.osm.pbf
IMG=ghcr.io/project-osrm/osrm-backend:v5.27.1
podman run --rm -v /srv/osrm:/data $IMG osrm-extract -p /opt/car.lua /data/region.osm.pbf
podman run --rm -v /srv/osrm:/data $IMG osrm-partition /data/region.osrm
podman run --rm -v /srv/osrm:/data $IMG osrm-customize /data/region.osrm
podman run -d --name osrm -p 5000:5000 -v /srv/osrm:/data $IMG \
   osrm-routed --algorithm mld --max-table-size 10000 /data/region.osrm

OSRM_URL=http://localhost:5000 PORT=8080 python3 esri_osrm_adapter.py
