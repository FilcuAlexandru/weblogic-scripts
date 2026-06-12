# Set the username for connecting to the WebLogic server
export WLST_CONNECT_USER='***'

# Set the password for the WebLogic server connection
export WLST_CONNECT_PW='***'

# Set the connection URL for the WebLogic server (Protocol, Host, and Port)
# Use t3s:// format
export WLST_CONNECT_URL='***'

# Set the JDBC connection URL
# Example: jdbc:oracle:thin:@//<host>:<port>/<service_name>
export DMS_JDBC_URL='***'

# Set the service username for connecting to the DB 
export DMS_JDBC_SERVICE_USER_NAME='***'

# Set the password for the service user of the DB 
export DMS_JDBC_SERVICE_USER_PW='***'

# Set the schema username for connecting to the DB
export DMS_JDBC_SCHEMA_USER_NAME='***'

# Set the name of the WebLogic cluster where the data source should be targeted
export WLST_CLUSTER_NAME='***'
