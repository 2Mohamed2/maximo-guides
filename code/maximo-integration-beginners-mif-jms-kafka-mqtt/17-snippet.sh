$ oc exec -n mas-instdb2-manage <manage-pod> -- grep -n -i jms /config/server.xml
10:      <feature>wasJmsClient-2.0</feature>
16:      <!--feature>wmqJmsClient-2.0</feature>
17:      <feature>jmsMdb-3.2</feature-->
