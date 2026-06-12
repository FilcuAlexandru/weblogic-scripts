################################################################
# Environment variables for WebLogic user management           #
#   used by: create-weblogic-user.py                           #
#            delete-weblogic-user.py                           #
# Author: Filcu Alexandru                                      #
#                                                              #
# Usage:                                                       #
#   source variables-user-management.sh                        #
#   wlst.sh create-weblogic-user.py [options]                  #
#   wlst.sh delete-weblogic-user.py [options]                  #
#                                                              #
# These variables are OPTIONAL: if all three are               #
# set, the scripts connect non-interactively;                  #
# otherwise they fall back to an interactive                   #
# connect() prompt.                                            #
#                                                              #
# WARNING: this file contains credentials.                     #
#   - do NOT commit it with real values (.gitignore)           #
#   - restrict access: chmod 600 variables-user-management.sh  #
################################################################

# Set the username for connecting to the WebLogic server
export WLST_CONNECT_USER='***'

# Set the password for the WebLogic server connection
export WLST_CONNECT_PW='***'

# Set the connection URL for the WebLogic server (Protocol, Host, and Port)
# Use t3s:// format -> e.g. t3s://<host>:<port>
export WLST_CONNECT_URL='***'