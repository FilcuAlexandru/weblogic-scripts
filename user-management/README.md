# WebLogic User Management Scripts

WLST (Python/Jython) scripts for managing users in the WebLogic
**DefaultAuthenticator** (embedded LDAP):

- **`create-weblogic-user.py`** — create users and add them to groups, with
  generated passwords.
- **`delete-weblogic-user.py`** — delete users.

Both scripts share the same design: a single `USERS` list, runtime selection by
group or by username, connection via the same environment variables, and
idempotent behaviour (skip what is already in the desired state).

## Prerequisites

- Access to a WebLogic Server with admin credentials.
- Permission to manage users and groups in the security realm.
- The WebLogic Scripting Tool (**WLST**) available via `wlst.sh`.

> **Note on Python version:** `wlst.sh` runs on **Jython**, not CPython.
> Jython only implements **Python 2** (2.2.1 on WLS 12.2.1.x, 2.7.x on WLS 14.1.1).
> There is **no Python 3** for WLST, so these scripts stay Python 2 and avoid
> `argparse`, `.format()` and `random.SystemRandom` (none exist on Jython 2.2.1).
> Password randomness comes from the JVM's `java.security.SecureRandom`.

## Configuring the Users

Edit the `USERS` list near the top of each script. The values are **dummy** —
replace them with your own. Keep the list **consistent between both scripts** so
that `--group` / `--user` selection behaves the same for create and delete.

```python
USERS = [
    # --- Operators ---
    {'username': 'op_user01', 'realname': 'Operator One, ExampleOrg', 'group': 'operators'},
    {'username': 'op_user02', 'realname': 'Operator Two, ExampleOrg', 'group': 'operators'},

    # --- Administrators ---
    {'username': 'adm_user01', 'realname': 'Admin One, ExampleOrg', 'group': 'Administrators'},
    {'username': 'adm_user02', 'realname': 'Admin Two, ExampleOrg', 'group': 'Administrators'},
]
```

- The `group` field is **what kind of user** it is:
  - `operators` — a custom group (auto-created by the create script if missing).
  - `Administrators` — the built-in WebLogic admin group.
- In `create-weblogic-user.py`, an optional per-user `'password'` key overrides
  the generated password.

> **Privacy:** do not commit a `USERS` list containing real names. Keep real
> values local; commit only dummy placeholders.

## Connection Variables (shared)

Both scripts read the same optional variables from
`variables-user-management.sh`. If all three are set, the scripts connect
non-interactively; otherwise they fall back to an interactive `connect()` prompt.

```bash
export WLST_CONNECT_USER='***'
export WLST_CONNECT_PW='***'
export WLST_CONNECT_URL='***'   # t3s://<host>:<port>
```

```bash
source variables-user-management.sh
```

> **Security:** this file contains credentials. Add it to `.gitignore` and run
> `chmod 600 variables-user-management.sh`.

## Creating Users

```bash
wlst.sh create-weblogic-user.py [options]
```

| Option | Description |
| --- | --- |
| `--help`, `-h` | Show help and exit. |
| `--list` | List configured users (no connection, no changes). |
| `--dry-run` | Show what would be created, without changing anything. |
| `--group <name>` | Only act on users in this group (repeatable). |
| `--user <username>` | Only act on this user (repeatable). |
| `--show-passwords` | Also print generated passwords to the console. |
| `--length <n>` | Generated password length (min 8, default 16). |
| `--no-create-groups` | Do not auto-create a missing group (skip membership instead). |

Generated credentials are written to `created-users-<timestamp>.txt` with
`chmod 600` (`username : password : group : realname`). Existing users are
skipped, so create is safe to re-run.

```bash
wlst.sh create-weblogic-user.py --list
wlst.sh create-weblogic-user.py --dry-run
wlst.sh create-weblogic-user.py --group operators
wlst.sh create-weblogic-user.py --user adm_user01 --show-passwords
```

## Deleting Users

```bash
wlst.sh delete-weblogic-user.py [options]
```

| Option | Description |
| --- | --- |
| `--help`, `-h` | Show help and exit. |
| `--list` | List configured users (no connection, no changes). |
| `--dry-run` | Show what would be deleted, without changing anything. |
| `--group <name>` | Only act on users in this group (repeatable). |
| `--user <username>` | Only act on this user (repeatable). |
| `--force` | Skip the interactive confirmation prompt. |

Deletion is **destructive**: by default the script lists the selected users and
asks for confirmation (type `yes`). Use `--dry-run` to preview, or `--force` to
skip the prompt in automation. Users that do not exist are skipped. Deleting a
user automatically removes its group memberships.

```bash
wlst.sh delete-weblogic-user.py --list
wlst.sh delete-weblogic-user.py --dry-run
wlst.sh delete-weblogic-user.py --group operators
wlst.sh delete-weblogic-user.py --user op_user01 --force
```

## How the Scripts Work

Both are organized into small functions (no classes) and share the same helpers:

- **parse_args(argv)** — manual CLI parsing (no `argparse`).
- **select_users(...)** — filter the `USERS` list by `--group` / `--user`.
- **do_connect()** — connect from `WLST_CONNECT_*` env vars, or interactively.
- **go_to_authenticator()** — navigate to the `DefaultAuthenticator`, deriving
  the domain name with `cmo.getName()`.
- **main()** — orchestrates selection, connection and the operation; always
  `disconnect`s in a `finally` block.

Create-specific: `secure_password()` (SecureRandom + shuffle), `ensure_group()`,
`create_one_user()` (uses `cmo.userExists` to skip existing users),
`write_credentials()` (chmod 600 file).

Delete-specific: `confirm_deletion()` (interactive prompt) and
`delete_one_user()` (uses `cmo.userExists` then `cmo.removeUser`).

## Troubleshooting

- **No users matched**: your `--group` / `--user` filter excluded everything; run `--list`.
- **Create — user already exists**: reported as `SKIP`; nothing changes for it.
- **Create — group missing**: created automatically (or skipped with `--no-create-groups`). `Administrators` is built-in.
- **Create — password rejected**: WebLogic's default policy requires at least 8 characters; `--length` is floored at 8.
- **Delete — user does not exist**: reported as `SKIP`.
- **`serverConfig:` path**: both scripts navigate `serverConfig:/SecurityConfiguration/<domain>/...`. If your environment needs the path without that prefix, change the single line in `go_to_authenticator()`.
- **SSL / handshake errors on `t3s://`**: check the WLST trust store configuration — this is outside the scripts.

## Suggested `.gitignore`

```
variables-user-management.sh
created-users-*.txt
```