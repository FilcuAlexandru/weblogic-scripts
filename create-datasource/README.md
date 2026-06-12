# WebLogic JDBC Data Source Creation Script

This repository contains a Python script for creating and configuring a JDBC Data Source named `Replace-With-Name` on a WebLogic Server. 

This script is particularly useful for setting up an XA-DataSource.
 
## Prerequisites

- Ensure you have access to a WebLogic Server with the appropriate credentials.
- You should have the necessary permissions to create and configure JDBC Data Sources on the server.
- Python must be installed, and the WebLogic Scripting Tool (WLST) should be available.

## Environment Variables

Before running the script, you need to create and source a `variables.sh` file with the following content:

```bash
# Set the username for connecting to the WebLogic server
export WLST_CONNECT_USER='***'

# Set the password for the WebLogic server connection
export WLST_CONNECT_PW='***'

# Set the connection URL for the WebLogic server (Protocol, Host, and Port)
# Use t3s://
export WLST_CONNECT_URL='***'

# Set the JDBC connection URL
# Example: jdbc:oracle:thin:@//<host>:<port>/<service_name>
export DB_JDBC_URL='***'

# Set the service username for connecting to the DB
export DB_JDBC_SERVICE_USER_NAME='***'

# Set the password for the service user of the DB
export DB_JDBC_SERVICE_USER_PW='***'

# Set the schema username for connecting to the DB
export DB_JDBC_SCHEMA_USER_NAME='***'

# Set the name of the WebLogic cluster where the data source should be targeted
export WLST_CLUSTER_NAME='***'
```

## Steps to Run the Script

1. **Create the `variables.sh` file**: Ensure that the above environment variables are correctly set in a file named `variables.sh`.

2. **Source the variables**: Open a terminal and navigate to the directory where `variables.sh` is located, then run the following command to load the environment variables:

    ```bash
    source variables.sh
    ```

3. **Run the script**: Use the following command to execute the script using WLST:

    ```bash
    ./wlst.sh create_datasource.py
    ```

4. **Help Option**: To see help options for the script, you can run:

    ```bash
    ./wlst.sh create_datasource.py --help
    ```
    
## Script Overview

The script contains the following key functions:

- **print_help_message()**: Displays usage information and required environment variables.

- **get_environment_vars()**: Fetches environment variables needed for the database connection.

- **connect_to_weblogic(user, pw, url)**: Establishes a connection to the WebLogic server.

- **create_jdbc_data_source()**: Creates a JDBC Data Source named `Replace-With-Name`.

- **configure_jdbc_driver(jdbc_url, jdbc_service_user_pw)**: Configures the JDBC driver parameters.

- **configure_connection_pool(jdbc_schema_user_name)**: Sets connection pool parameters, such as initial, minimum, and maximum capacity.

- **set_jdbc_properties(jdbc_service_user_name)**: Sets user and charset properties for the JDBC Data Source.

- **configure_global_transactions()**: Configures global transactions and XA settings.

- **set_targets(cluster_name)**: Sets the targets for the Data Source based on the specified cluster.

- **save_and_activate()**: Saves and activates the changes made to the Data Source.

- **check_data_source_created()**: Verifies whether the Data Source was created successfully.

- **main()**: The main execution point of the script, orchestrating the steps above.

## Troubleshooting

If you encounter errors related to database connection, verify that your JDBC URL, username, and password are correct. 

Ensure that the WebLogic server is running and accessible at the provided URL.
