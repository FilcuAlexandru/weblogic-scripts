# WebLogic Metrics Monitoring Script

## Overview

This Python script, `weblogic-metrics-report.py`, is designed to monitor the health and performance metrics of WebLogic servers in production environments. It retrieves and displays critical metrics from the WebLogic Console, including server status, DataSource performance, thread pool statistics, JMS server metrics, JVM heap usage, and deployment status. The script is particularly useful for automated daily health checks, such as morning assessments, to ensure the stability of WebLogic-based systems.

- **Author**: Filcu Alexandru
- **Version**: 0.1

## Purpose

The script automates the monitoring of key WebLogic components, providing a comprehensive overview of system health. It is tailored for production environments to:

Monitor the runtime status of WebLogic servers.
Track the performance and status of DataSources.
Provide detailed thread pool statistics (active, standby, queued, stuck, and hogging threads).
Monitor JMS server message queues (current, pending, peak, and total messages).
Track JVM memory usage (max heap, free heap percentage, and uptime).
Check the status of application deployments across target servers.

## Features

### Server Status Check

Displays the runtime state of each WebLogic server (e.g., RUNNING, WARNING, FAILED).
Shows the listening port for each server.

### DataSource Status Check

Monitors DataSources for each server, reporting:
State (e.g., Running, Failed).
Active connections count.
Waiting connections count.
Current and maximum capacity.
Peak active connections.

### Thread Pool Metrics

Provides thread pool statistics for each server, including:
Active threads.
Standby (inactive) threads.
Queued requests.
Stuck threads.
Hogging threads.
Throughput (requests per second).
Total completed requests.

### JMS Server Metrics

Monitors JMS server queues, reporting:
Current messages in queue (CURRENT).
Pending messages (PENDING).
Highest message count observed (HIGH COUNT).
Total messages received (TOTAL RCVD).

### JVM Heap Metrics

Tracks JVM memory usage for each server:
Java version.
Maximum heap size (MAX HEAP).
Free heap percentage (FREE HEAP).
Server uptime (UPTIME).

### Deployment Status Check

Monitors application deployments, reporting:
Application name.
Deployment status (e.g., Active, Prepared, Admin, Retired, Failed).
Target servers or clusters where the application is deployed.

## Requirements

WebLogic Server: Must be installed and configured.
WebLogic Scripting Tool (WLST): Required to execute the script.
Access to WebLogic Admin Server: Credentials and connectivity to the Admin Server.
Python: Compatible with Python 2.7.
Configuration Files: Paths to userConfigFile and userKeyFile for authentication.

## Usage

### 1. Generate Secure WebLogic Credentials
Navigate to the scripts directory:

    cd /path/to/scripts

Execute WLST and create encrypted credential files:

    ./wlst.sh

From the WLST interface, run the following commands:

    connect('weblogic','pass','t3://localhost:7001')
    storeUserConfig('/path/to/scripts/userConfig_weblogic', '/path/to/scripts/userKey_weblogic')

This will create two files in the scripts directory:

    userConfig_weblogic - encrypted user configuration
    userKey_weblogic    - decryption key

### 2. Configure Parameters
Update the following parameters in the script with your environment-specific values:
userConfigFile = '/path/to/scripts/userConfig_weblogic'   # Path to userConfig file
userKeyFile = '/path/to/scripts/userKey_weblogic'         # Path to userKey file
admin_server_url = 't3://localhost:7001'                  # Admin Server URL

### 3. Execute the Script
Run the script using the WebLogic Scripting Tool (WLST):
./wlst.sh weblogic-metrics-report.py

### 4. View Output
The script will connect to the WebLogic Admin Server and display formatted tables for each monitored component. 
Errors are highlighted in red, warnings in yellow, and successful states in green.

## Example Output
Below is an example of the script's output, showing the status of servers, DataSources, thread pools, JMS servers, JVM heap metrics, and deployment status.

### SERVER STATUS
| SERVER       | STATUS   | PORT   |
|--------------|----------|--------|
| AdminServer  | RUNNING  | 10000  |
| ms2          | RUNNING  | 10002  |
| ms1          | RUNNING  | 10001  |
| ms3          | RUNNING  | 10003  |
| ms4          | RUNNING  | 10004  |

### DATASOURCE STATUS
| SERVER | DATASOURCE        | STATE   | ACTIVE | WAITING | CAPACITY | PEAK |
|--------|-------------------|---------|--------|---------|----------|------|
| ms1    | DmsDataSource     | Running | 0      | 0       | 15       | 1    |
| ms1    | AppDataSource     | Running | 4      | 0       | 22       | 48   |
| ms2    | DmsDataSource     | Running | 0      | 0       | 15       | 1    |
| ms2    | AppDataSource     | Running | 7      | 0       | 26       | 38   |
| ms3    | DmsDataSource     | Running | 0      | 0       | 15       | 1    |
| ms3    | AppDataSource     | Running | 7      | 0       | 28       | 47   |
| ms4    | DmsDataSource     | Running | 0      | 0       | 15       | 1    |
| ms4    | AppDataSource     | Running | 5      | 0       | 22       | 57   |

### THREAD POOL METRICS
| SERVER | ACTIVE | STANDBY | QUEUED | STUCK | HOGGING | THROUGHPUT | COMPLETED  |
|--------|--------|---------|--------|-------|---------|------------|------------|
| ms1    | 50     | 47      | 0      | 0     | 0       | 550.5      | 48443524   |
| ms4    | 51     | 77      | 0      | 0     | 3       | 558.0      | 45522039   |
| ms2    | 50     | 48      | 0      | 0     | 5       | 954.5      | 45428586   |
| ms3    | 55     | 46      | 0      | 0     | 4       | 1095.5     | 45723887   |

### JMS SERVER METRICS
| SERVER | JMS SERVER                          | CURRENT | PENDING | HIGH COUNT | TOTAL RCVD |
|--------|-------------------------------------|---------|---------|------------|------------|
| ms2    | WorklistEventServiceJmsServer@ms2   | 0       | 1       | 53         | 2180702    |
| ms4    | WorklistEventServiceJmsServer@ms4   | 22      | 1       | 121        | 2180723    |
| ms3    | WorklistEventServiceJmsServer@ms3   | 158     | 1       | 173        | 2180757    |
| ms1    | WorklistEventServiceJmsServer@ms1   | 0       | 0       | 342        | 2180780    |

### JVM HEAP METRICS
| SERVER | JAVA VER  | MAX HEAP | FREE HEAP | UPTIME    |
|--------|-----------|----------|-----------|-----------|
| ms4    | 1.8.0_431 | 65536 MB | 45%       | 102:46:06 |
| ms3    | 1.8.0_431 | 65536 MB | 45%       | 102:47:40 |
| ms1    | 1.8.0_431 | 65536 MB | 49%       | 102:50:54 |
| ms2    | 1.8.0_431 | 65536 MB | 51%       | 102:49:18 |

### DEPLOYMENT STATUS
| APPLICATION                           | STATUS  | TARGETS        |
|---------------------------------------|---------|----------------|
| jolokia-deployment                    | Active  | ms4            |
| jolokia-deployment                    | Active  | ms1            |
| jolokia-deployment                    | Active  | ms3            |
| jolokia-deployment                    | Active  | ms2            |
| com.example.app.all.service_2.3.3.1   | Active  | app_cluster00  |
| com.example.app.mock.service_2.3.3.1  | Active  | app_cluster00  |

Notes

Color Coding: The script uses ANSI color codes to highlight statuses:
Green: Indicates healthy states (e.g., RUNNING, Active, zero stuck/hogging threads).
Yellow: Indicates warnings (e.g., non-zero active connections, low heap memory).
Red: Indicates errors or critical states (e.g., FAILED, stuck threads, high pending messages).


Error Handling: The script includes robust error handling to report issues with connections, MBean access, or data retrieval.
Environment: Ensure the WebLogic environment is properly configured, and the wlst.sh script is accessible in the execution path.

Troubleshooting

Connection Issues: Verify that the userConfigFile, userKeyFile, and admin_server_url are correctly specified and accessible.
WLST Errors: Ensure WLST is properly configured and that the user has sufficient permissions to access runtime MBeans.
Missing Metrics: If certain metrics are not displayed, check that the corresponding WebLogic components (e.g., JMS servers, DataSources) are configured and running.
Python Version: The script is compatible with Python 2.7, as required by older WebLogic WLST environments.