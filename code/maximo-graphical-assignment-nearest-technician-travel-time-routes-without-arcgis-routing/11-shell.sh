$ oc -n gis-routing get deploy,svc,pvc
NAME                           READY   UP-TO-DATE   AVAILABLE
deployment.apps/esri-adapter   1/1     1            1
deployment.apps/osrm           1/1     1            1

NAME                   TYPE        CLUSTER-IP       PORT(S)
service/esri-adapter   ClusterIP   172.30.19.19     8080/TCP
service/osrm           ClusterIP   172.30.188.174   5000/TCP

NAME                              STATUS   CAPACITY   ACCESS MODES
persistentvolumeclaim/osrm-data   Bound    20Gi       RWO
