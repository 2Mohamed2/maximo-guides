for f in gisnt_emres_distance_1.0.0 gisnt_emres_traveltime_1.0.2; do
  oc -n $NS cp $f.dbc $POD:/opt/IBM/SMP/maximo/tools/maximo/en/script/
  oc -n $NS exec $POD -- bash -c "cd /opt/IBM/SMP/maximo/tools/maximo/internal && ./runscriptfile.sh -cscript -f$f"
done
oc -n $NS delete pod $(oc -n $NS get pods -o name | grep -- -all- | cut -d/ -f2)   # OpenShift starts a fresh one
