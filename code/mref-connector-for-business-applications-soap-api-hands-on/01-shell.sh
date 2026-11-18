curl -s "https://<mref-host>/ws/TririgaWS?wsdl" -o tririgaws.wsdl
grep -o '<wsdl:operation name="[^"]*"' tririgaws.wsdl | sort -u | wc -l
