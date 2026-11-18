osrm-routed --algorithm mld --port 5001 --max-table-size 10000 --max-matching-size 5000 \
            --max-trip-size 500 --max-alternatives 3 /data/truck/ma.osrm

# car: shared memory, so new weights can be swapped in without a restart
osrm-datastore --dataset-name car /data/car/ma.osrm
osrm-routed --shared-memory --dataset-name car --algorithm mld --port 5000 ...
