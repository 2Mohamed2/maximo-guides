oc -n gis-routing create configmap esri-adapter --from-file=esri_osrm_adapter.py=esri_osrm_adapter.py \
   --dry-run=client -o yaml | oc apply -f -
oc -n gis-routing rollout restart deploy/esri-adapter
