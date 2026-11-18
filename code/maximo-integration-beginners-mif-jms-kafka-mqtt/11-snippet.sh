$ podman run -d --name nodered -p 1880:1880 -v nodered-data:/data docker.io/nodered/node-red:latest
$ podman logs nodered | grep -E "version|Started"
13 Oct 10:46:10 - [info] Node-RED version: v5.0.8
13 Oct 10:46:10 - [info] Node.js  version: v24.21.0
13 Oct 10:46:11 - [info] Started flows
