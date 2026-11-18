$ oc create secret generic wsp-all-jms-client -n mas-instdb2-manage \
     --from-file=server-custom.xml=server-custom.xml
secret/wsp-all-jms-client created
