oc -n mas-<instance>-manage get pods | grep -- -all-
oc -n mas-<instance>-manage exec <manage-all-pod> -- curl -s http://esri-adapter.gis-routing.svc:8080/healthz
