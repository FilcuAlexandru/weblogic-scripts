#####################################################
# WLST script: create WebLogic users (DefaultAuthenticator)
# Author: Filcu Alexandru
#
# Usage:
#   source variables-weblogic-user.sh   # optional (connection env vars)
#   wlst.sh create-weblogic-user.py [options]
#
# Examples:
#   wlst.sh create-weblogic-user.py --list
#   wlst.sh create-weblogic-user.py --dry-run
#   wlst.sh create-weblogic-user.py --group operators
#   wlst.sh create-weblogic-user.py --user adm_user01 --user op_user02
#   wlst.sh create-weblogic-user.py --group Administrators --show-passwords
#####################################################

######################
# Import handy tools #
######################

import os
import sys
import time
import string
from java.security import SecureRandom

# Security realm and authentication provider (defaults for WebLogic)
REALM = 'myrealm'
AUTHENTICATOR = 'DefaultAuthenticator'

# Minimum password length accepted (WebLogic default policy is 8)
MIN_PASSWORD_LENGTH = 8
DEFAULT_PASSWORD_LENGTH = 16

# Punctuation kept "shell/SQL safe" (no quotes, backslash, backtick, space)
SAFE_PUNCTUATION = '!#$%*+-=?@_'

# USERS - dummy values, replace with your own.
# 'group' tells WebLogic what KIND of user this is:
#   - 'operators'      -> custom group (created automatically if missing)
#   - 'Administrators' -> built-in WebLogic admin group
# Optional per-user 'password' overrides the generated one.

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
    Usage: wlst.sh create-weblogic-user.py [options]

    Options:
        --help, -h          Show this help message and exit.
        --list              List the configured users (no connection, no changes).
        --dry-run           Show what WOULD be created, without changing anything.
        --group <name>      Only act on users in this group (repeatable).
        --user <username>   Only act on this user (repeatable).
        --show-passwords    Also print generated passwords to the console.
        --length <n>        Generated password length (min %d, default %d).
        --no-create-groups  Do not auto-create a missing group (skip membership instead).

    Connection (optional environment variables; falls back to interactive connect()):
        - WLST_CONNECT_USER : WebLogic admin username
        - WLST_CONNECT_PW   : WebLogic admin password
        - WLST_CONNECT_URL  : WebLogic URL (e.g. t3s://<host>:<port>)

    Output:
        Generated credentials are written to 'created-users-<timestamp>.txt'
        with chmod 600. Existing users are skipped (idempotent).
    """ % (MIN_PASSWORD_LENGTH, DEFAULT_PASSWORD_LENGTH)

######################################
# Password generation (SecureRandom) #
######################################

_RNG = SecureRandom()
_LOWER = string.ascii_lowercase
_UPPER = string.ascii_uppercase
_DIGITS = string.digits
_ALL = _LOWER + _UPPER + _DIGITS + SAFE_PUNCTUATION

def _pick(seq):
    """Pick one element using SecureRandom."""
    return seq[_RNG.nextInt(len(seq))]

def secure_password(length):
    """Generate a password with at least one of each class, then shuffle."""
    if length < MIN_PASSWORD_LENGTH:
        length = MIN_PASSWORD_LENGTH
    chars = [_pick(_LOWER), _pick(_UPPER), _pick(_DIGITS), _pick(SAFE_PUNCTUATION)]
    while len(chars) < length:
        chars.append(_pick(_ALL))
    # Fisher-Yates shuffle with SecureRandom so positions are not predictable
    i = len(chars) - 1
    while i > 0:
        j = _RNG.nextInt(i + 1)
        chars[i], chars[j] = chars[j], chars[i]
        i -= 1
    return ''.join(chars)

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
        'groups': [], 'users': [], 'show_passwords': False,
        'length': DEFAULT_PASSWORD_LENGTH, 'create_groups': True,
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
        elif a == '--show-passwords':
            args['show_passwords'] = True
        elif a == '--no-create-groups':
            args['create_groups'] = False
        elif a == '--group':
            args['groups'].append(_need_value(argv, i, a)); i += 1
        elif a == '--user':
            args['users'].append(_need_value(argv, i, a)); i += 1
        elif a == '--length':
            args['length'] = int(_need_value(argv, i, a)); i += 1
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

def ensure_group(group, create_missing):
    """Make sure the group exists (optionally create it). Returns True if usable."""
    if cmo.groupExists(group):
        return True
    if create_missing:
        print "Group '%s' does not exist -> creating it." % group
        cmo.createGroup(group, 'Created by create-weblogic-user.py')
        return True
    print "WARNING: group '%s' does not exist; skipping membership for it." % group
    return False

def create_one_user(user, length, dry_run, create_groups):
    """Create a single user and add it to its group. Returns a creds dict or None."""
    username = user['username']
    realname = user.get('realname', '')
    group = user['group']
    explicit_pw = user.get('password')

    if cmo.userExists(username):
        print "SKIP: user '%s' already exists." % username
        return None

    if dry_run:
        print "DRY-RUN: would create '%s' (%s) in group '%s'." % (username, realname, group)
        return None

    password = explicit_pw
    if not password:
        password = secure_password(length)

    cmo.createUser(username, password, realname)
    if ensure_group(group, create_groups):
        cmo.addMemberToGroup(group, username)
        print "Created user '%s' in group '%s'." % (username, group)
    else:
        print "Created user '%s' (no group membership)." % username

    return {'username': username, 'password': password,
            'group': group, 'realname': realname}

def write_credentials(created, show_passwords):
    """Write generated credentials to a chmod-600 file."""
    if not created:
        print 'No new users were created.'
        return
    fname = 'created-users-%s.txt' % time.strftime('%Y%m%d-%H%M%S')
    f = open(fname, 'w')
    try:
        f.write('# username : password : group : realname\n')
        for c in created:
            f.write('%s : %s : %s : %s\n' %
                    (c['username'], c['password'], c['group'], c['realname']))
    finally:
        f.close()
    try:
        os.chmod(fname, 0600)
    except Exception, e:
        print 'Could not chmod credentials file: ' + str(e)
    print "Credentials written to '%s' (chmod 600)." % fname
    if show_passwords:
        for c in created:
            print '  %s / %s  (%s)' % (c['username'], c['password'], c['group'])

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

    do_connect()
    try:
        go_to_authenticator()
        created = []
        for u in selected:
            result = create_one_user(u, args['length'], args['dry_run'], args['create_groups'])
            if result:
                created.append(result)
        if not args['dry_run']:
            write_credentials(created, args['show_passwords'])
    finally:
        try:
            disconnect()
        except Exception, e:
            pass

# Execute the script
main()