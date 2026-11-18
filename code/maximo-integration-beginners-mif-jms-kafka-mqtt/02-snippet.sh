$ oc apply -f topic.yaml
kafkatopic.kafka.strimzi.io/demo.pump.alerts created
$ oc get kafkatopic -n strimzi
NAME               CLUSTER    PARTITIONS   REPLICATION FACTOR   READY
demo.pump.alerts   maskafka   3            3                    True
