BOOT = "maskafka-kafka-tls-bootstrap-strimzi.apps.<your-cluster-domain>:443"
def cfg():
    return dict(bootstrap_servers=BOOT, security_protocol="SASL_SSL", sasl_mechanism="SCRAM-SHA-512",
                sasl_plain_username=open("user.txt").read().strip(),
                sasl_plain_password=open("password.txt").read().strip(),
                ssl_cafile="kafka-ca.crt")
