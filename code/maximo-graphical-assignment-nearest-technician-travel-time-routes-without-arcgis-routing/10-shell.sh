oc apply -f gis-routing.yaml
oc -n gis-routing create configmap esri-adapter --from-file=esri_osrm_adapter.py=esri_osrm_adapter.py
oc -n gis-routing rollout status deploy/esri-adapter
oc -n gis-routing rollout status deploy/osrm --timeout=60m     # the first build takes a while
