#####################################################
# WLST script: create a WebLogic XA JDBC DataSource #
# Author: Filcu Alexandru                           #
# Usage:                                            #
#   source variables-xa-datasource.sh               #
#   wlst.sh create-xa-datasource.py [--help|-h]     #
#   wlst.sh create-xa-datasource.py --dry-run       #
#####################################################

######################
# Import handy tools #
######################

import os
import sys
import jarray
from java.lang import String
from javax.management import ObjectName

# WebLogic XA JDBC DataSource Name
DS_NAME = 'Replace-with-WebLogic-XA-JDBC-DataSource-Name'

# Connection-test query used when TestConnectionsOnReserve is enabled.
#   'SQL ISVALID'             -> driver-level Connection.isValid(), lightweight
#   'SQL SELECT 1 FROM DUAL'  -> real query against the DB (alternative)
TEST_TABLE_NAME = 'SQL ISVALID'

# Required environment variables (from variables-xa-datasource.sh)
REQUIRED_VARS = [
    'WLST_CONNECT_USER',
    'WLST_CONNECT_PW',
    'WLST_CONNECT_URL',
    'DB_JDBC_URL',
    'DB_JDBC_SERVICE_USER_NAME',
    'DB_JDBC_SERVICE_USER_PW',
    'DB_JDBC_SCHEMA_USER_NAME',
    'WLST_CLUSTER_NAME',
]

#####################################
# The "print_help_message" function #
#####################################

def print_help_message():
    """Prints the help message explaining how to use the script."""
    print """
    Usage: wlst.sh create-xa-datasource.py [options]

    Options:
        --help, -h    Show this help message and exit.
        --dry-run     Build the full configuration in an edit session and run
                      validate(), then discard it with cancelEdit('y').
                      Nothing is saved or activated; no data source is created.

    Description:
    Creates and configures an XA JDBC DataSource on a WebLogic server.
    All parameters are read from environment variables.

    Required Environment Variables:
        - WLST_CONNECT_USER         : WebLogic admin username
        - WLST_CONNECT_PW           : WebLogic admin password
        - WLST_CONNECT_URL          : WebLogic URL (e.g. t3s://<host>:<port>)
        - DB_JDBC_URL               : JDBC connection URL for the DB
        - DB_JDBC_SERVICE_USER_NAME : service username for the DB
        - DB_JDBC_SERVICE_USER_PW   : service password for the DB
        - DB_JDBC_SCHEMA_USER_NAME  : schema name (CURRENT_SCHEMA)
        - WLST_CLUSTER_NAME         : target WebLogic cluster name

    Note:
        Create and 'source variables-xa-datasource.sh' before running this script.
        Even in --dry-run mode the script connects to the Admin Server, so valid
        credentials and connectivity are still required.
    """

#######################################
# The "get_environment_vars" function #
#######################################

def get_environment_vars():
    """Validate and fetch required environment variables."""
    missing = []
    for name in REQUIRED_VARS:
        if name not in os.environ or os.environ[name] == '':
            missing.append(name)

    if missing:
        print 'ERROR: missing required environment variables:'
        for name in missing:
            print '  - ' + name
        print "Run 'source variables-xa-datasource.sh' before this script."
        sys.exit(1)

    return {
        'user':                   os.environ['WLST_CONNECT_USER'],
        'pw':                     os.environ['WLST_CONNECT_PW'],
        'url':                    os.environ['WLST_CONNECT_URL'],
        'jdbc_url':               os.environ['DB_JDBC_URL'],
        'jdbc_service_user_name': os.environ['DB_JDBC_SERVICE_USER_NAME'],
        'jdbc_service_user_pw':   os.environ['DB_JDBC_SERVICE_USER_PW'],
        'jdbc_schema_user_name':  os.environ['DB_JDBC_SCHEMA_USER_NAME'],
        'cluster_name':           os.environ['WLST_CLUSTER_NAME'],
    }

###############################
# The "build_paths" function  #
###############################

def build_paths():
    """Build every MBean path from a single DS_NAME."""
    resource = '/JDBCSystemResources/%s/JDBCResource/%s' % (DS_NAME, DS_NAME)
    driver_params = resource + ('/JDBCDriverParams/%s' % DS_NAME)
    props_container = driver_params + ('/Properties/%s' % DS_NAME)
    return {
        'system_resource': '/JDBCSystemResources/%s' % DS_NAME,
        'resource':        resource,
        'ds_params':       resource + ('/JDBCDataSourceParams/%s' % DS_NAME),
        'driver_params':   driver_params,
        'pool_params':     resource + ('/JDBCConnectionPoolParams/%s' % DS_NAME),
        'xa_params':       resource + ('/JDBCXAParams/%s' % DS_NAME),
        'props_container': props_container,
    }

##########################################
# The "create_jdbc_data_source" function #
##########################################

def create_jdbc_data_source(paths):
    """Create the JDBC System Resource and set JNDI name / type."""
    cd('/')
    cmo.createJDBCSystemResource(DS_NAME)

    cd(paths['resource'])
    cmo.setName(DS_NAME)

    # JNDI name
    cd(paths['ds_params'])
    set('JNDINames', jarray.array([String('jdbc/%s' % DS_NAME)], String))

    cd(paths['resource'])
    cmo.setDatasourceType('GENERIC')

########################################
# The "configure_jdbc_driver" function #
########################################

def configure_jdbc_driver(paths, jdbc_url, jdbc_service_user_pw):
    """Configure the Oracle XA JDBC driver parameters."""
    cd(paths['driver_params'])
    cmo.setUrl(jdbc_url)
    cmo.setDriverName('oracle.jdbc.xa.client.OracleXADataSource')
    cmo.setPassword(jdbc_service_user_pw)

############################################
# The "configure_connection_pool" function #
############################################

def configure_connection_pool(paths, jdbc_schema_user_name):
    """Configure connection pool parameters."""
    cd(paths['pool_params'])
    cmo.setInitialCapacity(15)
    cmo.setMinCapacity(15)
    cmo.setMaxCapacity(60)
    cmo.setTestConnectionsOnReserve(True)
    cmo.setTestTableName(TEST_TABLE_NAME)
    cmo.setInitSql('SQL ALTER SESSION SET CURRENT_SCHEMA=' + jdbc_schema_user_name)

######################################
# The "set_jdbc_properties" function #
######################################

def set_jdbc_properties(paths, jdbc_service_user_name):
    """Set the 'user' and 'CHARSET' driver properties."""
    # user
    cd(paths['props_container'])
    cmo.createProperty('user')
    cd(paths['props_container'] + '/Properties/user')
    cmo.setValue(jdbc_service_user_name)

    # charset
    cd(paths['props_container'])
    cmo.createProperty('CHARSET')
    cd(paths['props_container'] + '/Properties/CHARSET')
    cmo.setValue('utf8')

################################################
# The "configure_global_transactions" function #
################################################

def configure_global_transactions(paths):
    """Configure global transactions and XA settings."""
    cd(paths['ds_params'])
    cmo.setGlobalTransactionsProtocol('TwoPhaseCommit')

    cd(paths['driver_params'])
    cmo.setUseXaDataSourceInterface(True)

    cd(paths['xa_params'])
    cmo.setXaSetTransactionTimeout(True)

##############################
# The "set_targets" function #
##############################

def set_targets(cluster_name):
    """Set the data source target to the given cluster."""
    cd('/JDBCSystemResources/%s' % DS_NAME)
    set('Targets',
        jarray.array([ObjectName('com.bea:Name=%s,Type=Cluster' % cluster_name)],
                     ObjectName))

############################################
# The "build_data_source" function         #
############################################

def build_data_source(env, paths):
    """Run every configuration step inside the current edit session."""
    create_jdbc_data_source(paths)
    configure_jdbc_driver(paths, env['jdbc_url'], env['jdbc_service_user_pw'])
    configure_connection_pool(paths, env['jdbc_schema_user_name'])
    set_jdbc_properties(paths, env['jdbc_service_user_name'])
    configure_global_transactions(paths)
    set_targets(env['cluster_name'])

############################################
# The "check_data_source_created" function #
############################################

def check_data_source_created():
    """Check whether the data source was created successfully."""
    try:
        cd('/JDBCSystemResources/%s' % DS_NAME)
        return cmo.getName() == DS_NAME
    except Exception, e:
        print 'Error checking data source: ' + str(e)
        return False

#######################
# The "main" function #
#######################

def main():
    """Create and configure the XA DataSource, with cleanup on failure."""
    if '--help' in sys.argv or '-h' in sys.argv:
        print_help_message()
        sys.exit(0)

    dry_run = ('--dry-run' in sys.argv)

    env = get_environment_vars()
    paths = build_paths()

    connected = 0
    in_edit = 0

    if dry_run:
        print "DRY-RUN mode: changes will be validated and then discarded."

    # try/finally + nested try/except -> compatible with Jython 2.2.1
    try:
        try:
            connect(env['user'], env['pw'], env['url'])
            connected = 1

            edit()
            startEdit()
            in_edit = 1

            build_data_source(env, paths)

            if dry_run:
                # Validate the pending changes, then throw them away.
                print "DRY-RUN: validating pending changes for '%s'." % DS_NAME
                validate()
                cancelEdit('y')
                in_edit = 0  # no edit session left open
                print "DRY-RUN OK: changes validated and discarded. " \
                      "No data source was created."
            else:
                save()
                activate()
                in_edit = 0  # no edit session left open

                if check_data_source_created():
                    print "OK: data source '%s' created successfully." % DS_NAME
                else:
                    print "WARNING: could not verify data source '%s'." % DS_NAME

        except Exception, e:
            print 'ERROR while creating the data source: ' + str(e)
            if in_edit:
                try:
                    cancelEdit('y')
                except Exception, ce:
                    print 'Could not cancel the edit session: ' + str(ce)
            sys.exit(1)
    finally:
        if connected:
            disconnect()

# Execute the script
main()