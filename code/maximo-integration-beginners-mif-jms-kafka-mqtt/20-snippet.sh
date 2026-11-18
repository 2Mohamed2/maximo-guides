$ oc patch manageworkspace instdb2-wsp -n mas-instdb2-manage --type merge -p '
spec:
  settings:
    deployment:
      defaultJMS: true                         # message beans for the continuous queues
      persistentVolumes:
        - pvcName: manage-jms
          mountPath: /jmsstore                 # the path the JMS server writes its store to
          size: 5Gi
          storageClassName: ocs-external-storagecluster-cephfs
          accessModes: [ReadWriteMany]
      serverBundles:
        - name: all                            # the existing Manage server bundle ...
          bundleType: all
          isDefault: true
          isMobileTarget: true
          isUserSyncTarget: true
          replica: 1
          routeSubDomain: all
          additionalServerConfig:
            secretName: wsp-all-jms-client     # ... now with the client XML of step 1
        - name: jms                            # new: the JMS server
          bundleType: standalonejms
          isDefault: false
          isMobileTarget: false
          isUserSyncTarget: false
          replica: 1
          routeSubDomain: jms
'
