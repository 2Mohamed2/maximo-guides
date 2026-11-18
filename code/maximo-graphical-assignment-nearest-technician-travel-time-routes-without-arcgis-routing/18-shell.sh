NS=mas-<instance>-manage
POD=$(oc -n $NS get pods -o name | grep maxinst | head -1 | cut -d/ -f2)
oc -n $NS cp mas_map_osrm_routing_1.0.0.dbc $POD:/opt/IBM/SMP/maximo/tools/maximo/en/script/
oc -n $NS exec $POD -- bash -c \
   'cd /opt/IBM/SMP/maximo/tools/maximo/internal && ./runscriptfile.sh -cscript -fmas_map_osrm_routing_1.0.0'
