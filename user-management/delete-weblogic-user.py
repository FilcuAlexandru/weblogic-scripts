#############################################################################
# WLST script: delete WebLogic users (DefaultAuthenticator)                 #
# Author: Filcu Alexandru                                                   #
# Usage:                                                                    #
#   source variables-user-management.sh   # optional (connection env vars)  #
#   wlst.sh delete-weblogic-user.py [options]                               #
#                                                                           #
# Examples:                                                                 #
#   wlst.sh delete-weblogic-user.py --list                                  #
#   wlst.sh delete-weblogic-user.py --dry-run                               #
#   wlst.sh delete-weblogic-user.py --group operators                       #
#   wlst.sh delete-weblogic-user.py --user adm_user01 --user op_user02      #
#   wlst.sh delete-weblogic-user.py --group operators --force               #
#############################################################################

######################
# Import handy tools #
######################

import os
import sys

# Security realm and authentication provider (defaults for WebLogic)
REALM = 'myrealm'
AUTHENTICATOR = 'DefaultAuthenticator'

# USERS - dummy values, replace with your own.
# Keep this list consistent with create-weblogic-user.py so that
# --group / --user selection behaves the same for create and delete.
# 'group' is only used here for --group filtering; deleting a user
# automatically removes its group memberships.

USERS = [
    # --- Operators ---
    {'username': 'op_user01', 'realname': 'Operator One, ExampleOrg', 'group': 'operators'},
    {'username': 'op_user02', 'realname': 'Operator Two, ExampleOrg', 'group': 'operators'},

    # --- Administrators ---
    {'username': 'adm_user01', 'realname': 'Admin One, ExampleOrg', 'group': 'Administrators'},
    {'username': 'adm_user02', 'realname': 'Admin Two, ExampleOrg', 'group': 'Administrators'},
]

#####################################
# The "print_help_message" function #
#####################################

def print_help_message():
    """Prints usage information."""
    print """
    Usage: wlst.sh delete-weblogic-user.py [options]

    Options:
        --help, -h          Show this help message and exit.
        --list              List the configured users (no connection, no changes).
        --dry-run           Show what WOULD be deleted, without changing anything.
        --group <name>      Only act on users in this group (repeatable).
        --user <username>   Only act on this user (repeatable).
        --force             Skip the interactive confirmation prompt.

    Connection (optional environment variables; falls back to interactive connect()):
        - WLST_CONNECT_USER : WebLogic admin username
        - WLST_CONNECT_PW   : WebLogic admin password
        - WLST_CONNECT_URL  : WebLogic URL (e.g. t3s://<host>:<port>)

    Safety:
        Deletion is destructive. By default the script lists the selected users
        and asks for confirmation. Use --dry-run to preview, or --force to skip
        the prompt (e.g. in automation). Users that do not exist are skipped.
    """

#########################################
# Argument parsing (manual, 2.2.1-safe) #
#########################################

def _need_value(argv, i, flag):
    if i + 1 >= len(argv):
        print "ERROR: option %s requires a value." % flag
        sys.exit(1)
    return argv[i + 1]


def parse_args(argv):
    """Parse CLI options without argparse (Jython 2.2.1 has no argparse)."""
    args = {
        'help': False, 'list': False, 'dry_run': False,
        'groups': [], 'users': [], 'force': False,
    }
    i = 0
    n = len(argv)
    while i < n:
        a = argv[i]
        if a == '--help' or a == '-h':
            args['help'] = True
        elif a == '--list':
            args['list'] = True
        elif a == '--dry-run':
            args['dry_run'] = True
        elif a == '--force':
            args['force'] = True
        elif a == '--group':
            args['groups'].append(_need_value(argv, i, a)); i += 1
        elif a == '--user':
            args['users'].append(_need_value(argv, i, a)); i += 1
        else:
            print "Unknown option: %s (use --help)" % a
            sys.exit(1)
        i += 1
    return args

########################################
# User selection / WebLogic operations #
########################################

def select_users(users, only_groups, only_users):
    """Filter the configured users by --group and/or --user."""
    selected = []
    for u in users:
        if only_users and u['username'] not in only_users:
            continue
        if only_groups and u['group'] not in only_groups:
            continue
        selected.append(u)
    return selected

def do_connect():
    """Connect from env vars if all set, otherwise interactive connect()."""
    user = os.environ.get('WLST_CONNECT_USER')
    pw = os.environ.get('WLST_CONNECT_PW')
    url = os.environ.get('WLST_CONNECT_URL')
    if user and pw and url:
        connect(user, pw, url)
    else:
        print 'WLST connect env vars not fully set -> using interactive connect()...'
        connect()

def go_to_authenticator():
    """Navigate to the DefaultAuthenticator, deriving the domain name."""
    cd('serverConfig:/')
    domain_name = cmo.getName()
    path = ('serverConfig:/SecurityConfiguration/%s/Realms/%s'
            '/AuthenticationProviders/%s') % (domain_name, REALM, AUTHENTICATOR)
    cd(path)
    return domain_name

def confirm_deletion(selected):
    """Show the selection and ask for explicit confirmation."""
    print 'About to DELETE the following user(s):'
    for u in selected:
        print "  %-22s (%s)" % (u['username'], u['group'])
    answer = raw_input("Type 'yes' to proceed: ")
    return answer.strip().lower() == 'yes'

def delete_one_user(user, dry_run):
    """Delete a single user if it exists. Returns True if deleted."""
    username = user['username']

    if not cmo.userExists(username):
        print "SKIP: user '%s' does not exist." % username
        return False

    if dry_run:
        print "DRY-RUN: would delete user '%s'." % username
        return False

    try:
        cmo.removeUser(username)
        print "Deleted user '%s'." % username
        return True
    except Exception, e:
        print "ERROR deleting user '%s': %s" % (username, str(e))
        return False

#######################
# The "main" function #
#######################

def main():
    args = parse_args(sys.argv[1:])

    if args['help']:
        print_help_message()
        sys.exit(0)

    selected = select_users(USERS, args['groups'], args['users'])
    if not selected:
        print 'No users matched your selection. Use --list to see configured users.'
        sys.exit(0)

    # --list does not need a server connection
    if args['list']:
        print 'Configured users matching selection:'
        for u in selected:
            print "  %-22s %-15s %s" % (u['username'], u['group'], u.get('realname', ''))
        sys.exit(0)

    # Confirmation (skipped for --dry-run and --force)
    if not args['dry_run'] and not args['force']:
        if not confirm_deletion(selected):
            print 'Aborted. No users were deleted.'
            sys.exit(0)

    do_connect()
    try:
        go_to_authenticator()
        deleted = 0
        for u in selected:
            if delete_one_user(u, args['dry_run']):
                deleted += 1
        if not args['dry_run']:
            print 'Done. %d user(s) deleted.' % deleted
    finally:
        try:
            disconnect()
        except Exception, e:
            pass

# Execute the script
main()