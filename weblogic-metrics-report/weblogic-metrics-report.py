###############################################################
# Python script for gathering and monitoring WebLogic metrics #
# Author: Filcu Alexandru                                     #
###############################################################

# Import standard library for system-specific parameters and functions
import sys

# Define ANSI color codes for styled terminal output
class Colors:
    HEADER = '\033[95m'  # Purple color for headers
    OKBLUE = '\033[94m'  # Blue color for information
    OKGREEN = '\033[92m'  # Green color for success
    WARNING = '\033[93m'  # Yellow color for warnings
    FAIL = '\033[91m'    # Red color for errors
    ENDC = '\033[0m'     # Reset color
    BOLD = '\033[1m'     # Bold text

def color_text(text, color):
    '''Apply specified ANSI color to text for terminal output'''
    return color + text + Colors.ENDC

def print_header(title):
    '''Display a formatted section header with borders'''
    border = '#' * 80
    print '\n' + color_text(border, Colors.HEADER)
    print color_text('### ' + title.center(72) + ' ###', Colors.HEADER)
    print color_text(border + '\n', Colors.HEADER)

def print_table(headers, data):
    '''Print a formatted table with headers and data, handling column widths and colors'''
    if not data:
        print color_text("No data available", Colors.WARNING)
        return

    # Calculate maximum width for each column based on content
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(header)
        for row in data:
            if i < len(row):
                clean_text = str(row[i])
                # Strip ANSI codes for accurate width calculation
                for code in [Colors.HEADER, Colors.OKBLUE, Colors.OKGREEN,
                             Colors.WARNING, Colors.FAIL, Colors.ENDC, Colors.BOLD]:
                    clean_text = clean_text.replace(code, '')
                if len(clean_text) > max_width:
                    max_width = len(clean_text)
        col_widths.append(max_width + 2)  # Add padding

    # Create table border
    border = '+' + '+'.join(['-' * (w + 2) for w in col_widths]) + '+'
    print color_text(border, Colors.OKBLUE)

    # Print header row with centered text
    header_row = '|'
    for i, header in enumerate(headers):
        header_row += ' ' + color_text(header.center(col_widths[i]), Colors.OKBLUE) + ' |'
    print header_row
    print color_text(border, Colors.OKBLUE)

    # Print data rows with proper alignment and padding
    for row in data:
        row_str = '|'
        for i in range(len(headers)):
            if i < len(row):
                cell = str(row[i])
                clean_cell = cell
                # Remove ANSI codes for width calculation
                for code in [Colors.HEADER, Colors.OKBLUE, Colors.OKGREEN,
                             Colors.WARNING, Colors.FAIL, Colors.ENDC, Colors.BOLD]:
                    clean_cell = clean_cell.replace(code, '')

                # Calculate padding for centered text
                padding = col_widths[i] - len(clean_cell)
                left_pad = padding // 2
                right_pad = padding - left_pad

                aligned_cell = (' ' * left_pad) + cell + (' ' * right_pad)
                row_str += ' ' + aligned_cell + ' |'
            else:
                row_str += ' ' + ' '.ljust(col_widths[i]) + ' |'
        print row_str

    print color_text(border + '\n', Colors.OKBLUE)

def print_help_message():
    '''Display help message with usage instructions'''
    print """
eIP WebLogic Monitoring Script
Usage: ./wlst.sh eIPweblogicServerHealth.py [options]

Options:
  --help, -h        Show this help message and exit.

Description:
  Gathers and monitors eIP WebLogic metrics:
    - Server status
    - DataSource stats
    - Thread pools
    - JMS servers
    - JVM Heap metrics
    - Deployment status
"""

def connect_to_admin_server(userConfigFile, userKeyFile, admin_server_url):
    '''Establish connection to WebLogic Admin Server'''
    try:
        print color_text("\nConnecting to Admin Server at: " + admin_server_url, Colors.OKBLUE)
        connect(userConfigFile=userConfigFile, userKeyFile=userKeyFile, url=admin_server_url)
        print color_text("Successfully connected to Admin Server", Colors.OKGREEN)
    except Exception, e:
        print color_text("Connection failed: " + str(e), Colors.FAIL)
        exit()

def check_servers_status():
    '''Retrieve and display status of WebLogic servers'''
    try:
        print_header('SERVER STATUS')
        domainConfig()
        servers = cmo.getServers()
        domainRuntime()

        table_data = []
        for server in servers:
            serverName = server.getName()
            try:
                cd('/ServerRuntimes/' + serverName)
                state = cmo.getState()
                status_color = state == 'RUNNING' and Colors.OKGREEN or Colors.FAIL
                table_data.append([
                    color_text(serverName.ljust(15), Colors.BOLD),
                    color_text(state.center(10), status_color),
                    str(cmo.getListenPort()).center(10)
                ])
            except:
                table_data.append([
                    color_text(serverName.ljust(15), Colors.BOLD),
                    color_text('UNKNOWN'.center(10), Colors.WARNING),
                    'N/A'.center(10)
                ])

        print_table(['      SERVER      ', '  STATUS  ', '  PORT  '], table_data)

    except Exception, e:
        print color_text("Error checking server status: " + str(e), Colors.FAIL)

def check_datasources_status():
    '''Retrieve and display status of WebLogic DataSources'''
    try:
        print_header('DATASOURCE STATUS')
        domainRuntime()
        cd('/')
        servers = ls('ServerRuntimes', returnMap='true')

        table_data = []
        for server in servers:
            if 'AdminServer' in server:
                continue
            try:
                cd('/ServerRuntimes/' + server + '/JDBCServiceRuntime/' + server)
                datasources = cmo.getJDBCDataSourceRuntimeMBeans()
                for ds in datasources:
                    state = ds.getState()
                    active = ds.getActiveConnectionsCurrentCount()
                    waiting = ds.getWaitingForConnectionCurrentCount()
                    state_color = state == 'Running' and Colors.OKGREEN or Colors.FAIL
                    active_color = active > 0 and Colors.WARNING or Colors.OKGREEN
                    waiting_color = waiting > 0 and Colors.FAIL or Colors.OKGREEN
                    table_data.append([
                        color_text(server.ljust(12), Colors.BOLD),
                        color_text(ds.getName().ljust(25), Colors.BOLD),
                        color_text(state.center(10), state_color),
                        color_text(str(active).center(8), active_color),
                        color_text(str(waiting).center(8), waiting_color),
                        str(ds.getCurrCapacity()).center(10),
                        str(ds.getActiveConnectionsHighCount()).center(8)
                    ])
            except Exception, e:
                print color_text("Error on server " + server + ": " + str(e), Colors.WARNING)

        print_table([
            '   SERVER   ', '        DATASOURCE        ', '  STATE  ',
            ' ACTIVE ', ' WAITING ', ' CAPACITY ', ' PEAK '
        ], table_data)

    except Exception, e:
        print color_text("Error checking DataSources: " + str(e), Colors.FAIL)

def check_thread_pool_metrics():
    '''Retrieve and display thread pool metrics for WebLogic servers'''
    try:
        print_header('THREAD POOL METRICS')
        domainRuntime()
        servers = domainRuntimeService.getServerRuntimes()

        table_data = []
        for server in servers:
            serverName = server.getName()
            if serverName == 'AdminServer':
                continue

            threadPool = server.getThreadPoolRuntime()
            if threadPool:
                stuck = threadPool.getStuckThreadCount()
                hogging = threadPool.getHoggingThreadCount()
                active = threadPool.getExecuteThreadTotalCount() - threadPool.getStandbyThreadCount()

                stuck_color = stuck > 0 and Colors.FAIL or Colors.OKGREEN
                hogging_color = hogging > 0 and Colors.WARNING or Colors.OKGREEN

                try:
                    throughput = "%.1f" % threadPool.getThroughput()
                except:
                    throughput = 'N/A'

                table_data.append([
                    color_text(serverName.ljust(12), Colors.BOLD),
                    str(active).center(8),
                    str(threadPool.getStandbyThreadCount()).center(8),
                    str(threadPool.getQueueLength()).center(8),
                    color_text(str(stuck).center(8), stuck_color),
                    color_text(str(hogging).center(8), hogging_color),
                    throughput.center(10),
                    str(threadPool.getCompletedRequestCount()).center(12)
                ])

        print_table([
            '   SERVER   ', ' ACTIVE ', ' STANDBY ', ' QUEUED ',
            ' STUCK ', ' HOGGING ', ' THROUGHPUT ', ' COMPLETED '
        ], table_data)

    except Exception, e:
        print color_text("Error checking thread metrics: " + str(e), Colors.FAIL)

def check_jms_server_metrics():
    '''Retrieve and display JMS server metrics'''
    try:
        print_header('JMS SERVER METRICS')
        domainRuntime()
        servers = domainRuntimeService.getServerRuntimes()

        table_data = []
        for server in servers:
            server_name = server.getName()
            try:
                jms_runtime = server.getJMSRuntime()
                if not jms_runtime:
                    continue

                jms_servers = jms_runtime.getJMSServers()
                if not jms_servers:
                    continue

                for jms_server in jms_servers:
                    jms_name = jms_server.getName()
                    if 'eIPWorklistEventServiceJmsServer' not in jms_name:
                        continue

                    current = pending = high = received = 0
                    for dest in jms_server.getDestinations():
                        current += dest.getMessagesCurrentCount()
                        pending += dest.getMessagesPendingCount()
                        high = max(high, dest.getMessagesHighCount())
                        received += dest.getMessagesReceivedCount()

                    current_color = current > 0 and Colors.WARNING or Colors.OKGREEN
                    pending_color = pending > 0 and Colors.FAIL or Colors.OKGREEN

                    table_data.append([
                        color_text(server_name.ljust(12), Colors.BOLD),
                        color_text(jms_name.ljust(25), Colors.BOLD),
                        color_text(str(current).center(10), current_color),
                        color_text(str(pending).center(10), pending_color),
                        str(high).center(10),
                        str(received).center(12)
                    ])

            except Exception, e:
                print color_text("Error checking JMS on " + server_name + ": " + str(e), Colors.WARNING)

        print_table([
            '   SERVER   ', '      JMS SERVER      ',
            ' CURRENT ', ' PENDING ', ' HIGH COUNT ', ' TOTAL RCVD '
        ], table_data)

    except Exception, e:
        print color_text("Error checking JMS metrics: " + str(e), Colors.FAIL)

def check_jvm_heap_metrics():
    '''Retrieve and display JVM heap metrics for WebLogic servers'''
    try:
        print_header('JVM HEAP METRICS')
        domainRuntime()
        servers = domainRuntimeService.getServerRuntimes()

        table_data = []
        for server in servers:
            serverName = server.getName()
            if serverName == 'AdminServer':
                continue

            try:
                cd("/ServerRuntimes/" + serverName + "/JVMRuntime/" + serverName)
                java_version = get('JavaVersion')
                max_heap = int(get('HeapSizeMax')) / (1024 * 1024)
                free_percent = int(get('HeapFreePercent'))
                uptime_sec = get('Uptime') / 1000

                if free_percent < 20:
                    heap_color = Colors.FAIL
                elif free_percent < 40:
                    heap_color = Colors.WARNING
                else:
                    heap_color = Colors.OKGREEN

                uptime_str = "%d:%02d:%02d" % (
                    uptime_sec / 3600,
                    (uptime_sec % 3600) / 60,
                    uptime_sec % 60
                )

                table_data.append([
                    color_text(serverName.ljust(12), Colors.BOLD),
                    java_version.split('-')[0].ljust(10),
                    ("%d MB" % max_heap).center(12),
                    color_text(("%d%%" % free_percent).center(10), heap_color),
                    uptime_str.center(12)
                ])

            except Exception, e:
                print color_text("Error checking JVM on " + serverName + ": " + str(e), Colors.WARNING)

        print_table([
            '   SERVER   ', ' JAVA VER ', ' MAX HEAP ', ' FREE HEAP ', '   UPTIME   '
        ], table_data)

    except Exception, e:
        print color_text("Error checking JVM metrics: " + str(e), Colors.FAIL)

def check_deployment_status():
    '''Retrieve and display status of application deployments'''
    try:
        print_header('DEPLOYMENT STATUS')
        domainConfig()
        deployments = cmo.getAppDeployments()
        domainRuntime()
        cd('/AppRuntimeStateRuntime/AppRuntimeStateRuntime')
        app_runtime = cmo

        table_data = []
        for deployment in deployments:
            app_name = deployment.getName()
            try:
                targets = [target.getName() for target in deployment.getTargets()]
                for target in targets:
                    if target == 'AdminServer':
                        continue
                    state = app_runtime.getCurrentState(app_name, target)
                    # Map WebLogic deployment states to user-friendly terms
                    state_map = {
                        'STATE_ACTIVE': 'Active',
                        'STATE_PREPARED': 'Prepared',
                        'STATE_ADMIN': 'Admin',
                        'STATE_RETIRED': 'Retired',
                        'STATE_FAILED': 'Failed'
                    }
                    display_state = state_map.get(state, 'Unknown')
                    # Assign color based on deployment state
                    if display_state == 'Active':
                        state_color = Colors.OKGREEN
                    elif display_state in ['Prepared', 'Admin']:
                        state_color = Colors.WARNING
                    else:
                        state_color = Colors.FAIL
                    table_data.append([
                        color_text(app_name.ljust(25), Colors.BOLD),
                        color_text(display_state.center(10), state_color),
                        target.ljust(20)
                    ])
            except Exception, e:
                table_data.append([
                    color_text(app_name.ljust(25), Colors.BOLD),
                    color_text('UNKNOWN'.center(10), Colors.WARNING),
                    'N/A'.ljust(20)
                ])

        print_table(['     DEPLOYMENT     ', '  STATUS  ', '      TARGETS      '], table_data)

    except Exception, e:
        print color_text("Error checking deployment status: " + str(e), Colors.FAIL)

# Main execution logic
if '--help' in sys.argv or '-h' in sys.argv:
    print_help_message()
    sys.exit()

userConfigFile = '' # Replace with actual userConfig file path
userKeyFile = '' # Replace with actual userKey file path
admin_server_url = '' # Replace with actual Admin Server URL

print color_text("\nStarting eIP WebLogic Monitoring Script", Colors.HEADER)
print color_text("=" * 60, Colors.HEADER)

try:
    connect_to_admin_server(userConfigFile, userKeyFile, admin_server_url)
    check_servers_status()
    check_datasources_status()
    check_thread_pool_metrics()
    check_jms_server_metrics()
    check_jvm_heap_metrics()
    check_deployment_status()
except Exception, e:
    print color_text("\nCritical error: " + str(e), Colors.FAIL)
    sys.exit(1)

try:
    disconnect()
    print color_text("\nDisconnected from Admin Server", Colors.OKGREEN)
except:
    pass

print color_text("\nMonitoring completed successfully", Colors.OKGREEN)
print color_text("=" * 60 + "\n", Colors.HEADER)