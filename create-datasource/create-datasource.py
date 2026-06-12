##################################################################
# Python script for creating a WebLogic XA-DataSource            #
# Author: Filcu Alexandru                                        #
##################################################################

######################
# Import handy tools #
######################

import os
import sys
from java.lang import String    
from javax.management import ObjectName  

#####################################
# The "print_help_message" function #
#####################################

def print_help_message():
    """Prints the help message explaining how to use the script."""
    print """
    Usage: wlst.sh <script-name>.py [options]

    Options:
        --help, -h    Show this help message and exit.

    Description:
    This script is used to create and configure the 'DbDmsDataSource' on a WebLogic server.
    It reads the connection and configuration parameters from the environment variables.

    Required Environment Variables:
        - WLST_CONNECT_USER: WebLogic admin username
        - WLST_CONNECT_PW: WebLogic admin password
        - WLST_CONNECT_URL: WebLogic URL (e.g., t3s://<host>:<port>)
        - DMS_JDBC_URL: JDBC connection URL for the DMS database
        - DMS_JDBC_SERVICE_USER_NAME: Service username for the DMS database
        - DMS_JDBC_SERVICE_USER_PW: Service password for the DMS database
        - DMS_JDBC_SCHEMA_USER_NAME: Schema username for the DMS database
        - WLST_CLUSTER_NAME: The WebLogic cluster name where the data source should be targeted

    Note:
        A new file 'variables.sh' needs to be created and sourced before running this script.
        The 'variables.sh' file should export all the required environment variables listed above.
    """

#######################################
# The "get_environment_vars" function #
#######################################

def get_environment_vars():
    """Fetch environment variables."""
    return {
        'user': os.environ['WLST_CONNECT_USER'],
        'pw': os.environ['WLST_CONNECT_PW'],
        'url': os.environ['WLST_CONNECT_URL'],
        'jdbc_url': os.environ['DMS_JDBC_URL'],
        'jdbc_service_user_name': os.environ['DMS_JDBC_SERVICE_USER_NAME'],
        'jdbc_service_user_pw': os.environ['DMS_JDBC_SERVICE_USER_PW'],
        'jdbc_schema_user_name': os.environ['DMS_JDBC_SCHEMA_USER_NAME'],
        'cluster_name': os.environ['WLST_CLUSTER_NAME']
    }

######################################
# The "connect_to_weblogic" function #
######################################

def connect_to_weblogic(user, pw, url):
    """Connect to WebLogic server."""
    connect(user, pw, url)
    edit()
    startEdit()

##########################################
# The "create_jdbc_data_source" function #
##########################################

def create_jdbc_data_source():
    """Create JDBC Data Source '{Replace-with-XA-DataSource-Name}'."""
    cd('/')
    cmo.createJDBCSystemResource('{Replace-with-XA-DataSource-Name}')

    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}')
    cmo.setName('{Replace-with-XA-DataSource-Name}')

    # Set JNDI name
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDataSourceParams/{Replace-with-XA-DataSource-Name}')
    set('JNDINames', jarray.array([String('jdbc/{Replace-with-XA-DataSource-Name}')], String))

    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}')
    cmo.setDatasourceType('GENERIC')

########################################
# The "configure_jdbc_driver" function #
########################################

def configure_jdbc_driver(jdbc_url, jdbc_service_user_pw):
    """Configure JDBC driver parameters."""
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDriverParams/{Replace-with-XA-DataSource-Name}')
    cmo.setUrl(jdbc_url)
    cmo.setDriverName('oracle.jdbc.xa.client.OracleXADataSource')
    cmo.setPassword(jdbc_service_user_pw)

############################################
# The "configure_connection_pool" function #
############################################

def configure_connection_pool(jdbc_schema_user_name):
    """Configure connection pool parameters."""
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCConnectionPoolParams/{Replace-with-XA-DataSource-Name}')
    cmo.setInitialCapacity(15)
    cmo.setMinCapacity(15)
    cmo.setMaxCapacity(60)
    cmo.setTestConnectionsOnReserve(True)
    cmo.setInitSql('SQL ALTER SESSION SET CURRENT_SCHEMA=' + jdbc_schema_user_name)

######################################
# The "set_jdbc_properties" function #
######################################

def set_jdbc_properties(jdbc_service_user_name):
    """Set user and charset properties."""
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDriverParams/{Replace-with-XA-DataSource-Name}/Properties/{Replace-with-XA-DataSource-Name}')
    cmo.createProperty('user')

    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDriverParams/DbDmsDataSource/Properties/{Replace-with-XA-DataSource-Name}/Properties/user')
    cmo.setValue(jdbc_service_user_name)

    # Set charset property
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDriverParams/{Replace-with-XA-DataSource-Name}/Properties/{Replace-with-XA-DataSource-Name}')
    cmo.createProperty('CHARSET')

    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDriverParams/{Replace-with-XA-DataSource-Name}/Properties/{Replace-with-XA-DataSource-Name}/Properties/CHARSET')
    cmo.setValue('utf8')

################################################
# The "configure_global_transactions" function #
################################################

def configure_global_transactions():
    """Configure global transactions and XA settings."""
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDataSourceParams/{Replace-with-XA-DataSource-Name}')
    cmo.setGlobalTransactionsProtocol('TwoPhaseCommit')

    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCDriverParams/{Replace-with-XA-DataSource-Name}')
    cmo.setUseXaDataSourceInterface(True)

    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}/JDBCResource/{Replace-with-XA-DataSource-Name}/JDBCXAParams/{Replace-with-XA-DataSource-Name}')
    cmo.setXaSetTransactionTimeout(True)

#############################
# The "set_target" function #
#############################

def set_targets(cluster_name):
    """Set targets for the data source based on the specified cluster."""
    cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}')
    set('Targets', jarray.array([ObjectName('com.bea:Name=' + cluster_name + ',Type=Cluster')], ObjectName))

####################################
# The "save_and_activate" function #
####################################

def save_and_activate():
    """Save and activate changes."""
    save()
    activate()

##########################################
# The "check_data_source_created" function #
##########################################

def check_data_source_created():
    """Check if the {Replace-with-XA-DataSource-Name} was created successfully."""
    try:
        cd('/JDBCSystemResources/{Replace-with-XA-DataSource-Name}')
        return cmo.getName() == '{Replace-with-XA-DataSource-Name}'
    except Exception, e:  
        print "Error checking data source:", str(e)
        return False

#######################
# The "main" function #
#######################

def main():
    """Main function to create and configure the {Replace-with-XA-DataSource-Name}."""
    # Check for --help or -h argument
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help_message()
        sys.exit(0)

    # Fetch environment variables
    env_vars = get_environment_vars()

    # Connect to WebLogic
    connect_to_weblogic(env_vars['user'], env_vars['pw'], env_vars['url'])

    # Create JDBC Data Source
    create_jdbc_data_source()

    # Configure JDBC Driver
    configure_jdbc_driver(env_vars['jdbc_url'], env_vars['jdbc_service_user_pw'])

    # Configure connection pool
    configure_connection_pool(env_vars['jdbc_schema_user_name'])

    # Set JDBC properties
    set_jdbc_properties(env_vars['jdbc_service_user_name'])

    # Configure Global Transactions and XA settings
    configure_global_transactions()

    # Set the targets for the data source
    set_targets(env_vars['cluster_name'])

    # Save and activate the changes
    save_and_activate()

    # Check if the data source was created successfully
    if check_data_source_created():
        print "The {Replace-with-XA-DataSource-Name} was created successfully."
    else:
        print "Failed to create the {Replace-with-XA-DataSource-Name}."

    # Disconnect from WebLogic
    disconnect()
# Execute the script
main()
