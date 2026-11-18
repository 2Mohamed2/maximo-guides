echo "$ENTITLEMENT_KEY" | docker login cp.icr.io -u cp --password-stdin
docker run -d --name prod-bdi --restart unless-stopped \
  -p 9543:9543 \
  -v "$PWD/ports.xml:/opt/was/liberty/wlp/usr/servers/default/configDropins/overrides/ports.xml:ro" \
  -e BDI_XDB_CONNECT='jdbc:db2://dbhost:50000/BLUDB' \
  -e BDI_XDB_USER=maximo -e BDI_XDB_PASSWORD="$MAXIMO_DB_PASSWORD" \
  -e INSTANCE_ID=prod -e WORKSPACE_ID=main \
  -e BDI_INSTANCE_NAME=prod-main-bdi -e SERVICE_HOST_NAME=prod-bdi \
  cp.icr.io/cp/manage/bdi:9.3.17_11050-amd64
