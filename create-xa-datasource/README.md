# WebLogic XA JDBC Data Source Creation Script

This repository contains a WLST (Python/Jython) script for creating and
configuring an **XA JDBC Data Source** on a WebLogic Server.

The data source name is **not hardcoded throughout the script** — it is defined
once in the `DS_NAME` constant at the top of `create-xa-datasource.py` (default
placeholder: `Replace-with-WebLogic-XA-JDBC-DataSource-Name`). Change that single
line to rename the data source; every MBean path is derived from it.

## Prerequisites

- Access to a WebLogic Server with admin credentials.
- Permissions to create and configure JDBC Data Sources on the server.
- The WebLogic Scripting Tool (**WLST**) available via `wlst.sh`.

> **Note on Python version:** `wlst.sh` runs on **Jython**, not CPython.
> Jython only implements **Python 2** (2.2.1 on WLS 12.2.1.x, 2.7.x on WLS 14.1.1).
> There is **no Python 3** for WLST, so this script must stay Python 2. It is
> written to also run on the older Jython 2.2.1 (no `.format()` / f-strings,
> `print` as a statement, `try/except` nested inside `try/finally`).

## Environment Variables

Before running the script, create and source a `variables-xa-datasource.sh`
file with the following content:

```bash
# Set the username for connecting to the WebLogic server
export WLST_CONNECT_USER='***'

# Set the password for the WebLogic server connection
export WLST_CONNECT_PW='***'

# Set the connection URL for the WebLogic server (Protocol, Host, and Port)
# Use t3s:// format -> e.g. t3s://<host>:<port>
export WLST_CONNECT_URL='***'

# Set the JDBC connection URL
# Example: jdbc:oracle:thin:@//<host>:<port>/<service_name>
export DB_JDBC_URL='***'

# Set the service username for connecting to the DB
export DB_JDBC_SERVICE_USER_NAME='***'

# Set the password for the service user of the DB
export DB_JDBC_SERVICE_USER_PW='***'

# Set the schema username for connecting to the DB (used as CURRENT_SCHEMA)
export DB_JDBC_SCHEMA_USER_NAME='***'

# Set the name of the WebLogic cluster where the data source should be targeted
export WLST_CLUSTER_NAME='***'
```

> **Security:** this file contains credentials. Do **not** commit it with real
> values (add it to `.gitignore`) and restrict access with
> `chmod 600 variables-xa-datasource.sh`. For version control, keep a
> `variables-xa-datasource.sh.template` with `'***'` placeholders instead.

## Steps to Run the Script

1. **Set the data source name**: edit `create-xa-datasource.py` and set the
   `DS_NAME` constant (and optionally `TEST_TABLE_NAME`, default `SQL ISVALID`).

2. **Create `variables-xa-datasource.sh`**: set the environment variables above.

3. **Source the variables**:

    ```bash
    source variables-xa-datasource.sh
    ```

4. **Run the script** with WLST:

    ```bash
    wlst.sh create-xa-datasource.py
    ```

5. **Help option**:

    ```bash
    wlst.sh create-xa-datasource.py --help
    ```

The script validates the environment variables first and exits with a clear
list of what is missing if `variables-xa-datasource.sh` was not sourced.

## Script Overview

The script is organized into small functions (no classes):

- **print_help_message()**: Displays usage information and required environment variables.

- **get_environment_vars()**: Validates and fetches the environment variables; exits early with a list of any that are missing.

- **build_paths()**: Builds every MBean path from the single `DS_NAME` value.

- **create_jdbc_data_source(paths)**: Creates the JDBC System Resource, sets the JNDI name and the data source type (`GENERIC`).

- **configure_jdbc_driver(paths, jdbc_url, jdbc_service_user_pw)**: Configures the Oracle XA driver (`oracle.jdbc.xa.client.OracleXADataSource`), URL and password.

- **configure_connection_pool(paths, jdbc_schema_user_name)**: Sets initial/min/max capacity, connection testing (`TEST_TABLE_NAME`) and the init SQL (`ALTER SESSION SET CURRENT_SCHEMA`).

- **set_jdbc_properties(paths, jdbc_service_user_name)**: Sets the `user` and `CHARSET` driver properties.

- **configure_global_transactions(paths)**: Configures global transactions (`TwoPhaseCommit`) and XA settings.

- **set_targets(cluster_name)**: Targets the data source at the specified cluster.

- **check_data_source_created()**: Verifies the data source was created successfully.

- **main()**: Orchestrates the steps above. It opens the WebLogic connection and edit session (`connect` / `edit` / `startEdit`), applies the configuration, then `save` / `activate`. On error it cancels the edit session (`cancelEdit`) and always `disconnect`s in a `finally` block, so the edit lock is never left dangling.

## Troubleshooting

- **Missing variable errors**: re-source `variables-xa-datasource.sh`; the script lists exactly which variables are unset or empty.
- **Database connection errors**: verify `DB_JDBC_URL`, the service username and password.
- **SSL / handshake errors on `t3s://`**: check the WLST trust store configuration — this is outside the script.
- **Edit lock held by another session**: an earlier run that crashed mid-edit may have left a lock; the current version releases it automatically via `cancelEdit` on failure, but a lock from an older run may need to be released manually in the WebLogic console.
- Ensure the WebLogic server is running and reachable at the provided URL.