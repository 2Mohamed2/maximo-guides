git clone https://github.com/confluentinc/cp-all-in-one.git
cd cp-all-in-one/cp-all-in-one
git checkout 7.9.10-post
docker compose up -d        # or: podman compose up -d
docker compose ps           # wait until every service is "running"
