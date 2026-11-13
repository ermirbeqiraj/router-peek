"""Credential lookup, driven by router.conf + router.local.conf. The only place that touches secrets.

Sources: file (KEY=VALUE file) and systemd (encrypted credentials). New sources are added
as another branch in load().
"""
import configparser
import os

CONFIG = "router.conf"
LOCAL_CONFIG = "router.local.conf"  # per machine, gitignored, read after CONFIG


def _failure(msg):
    from core.client import failure
    return failure(msg)


def _read(path):
    """One credential file's contents, stripped. systemd delivers one value per file."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            return f.read().strip()
    except OSError:
        return ""  # missing or unreadable: reported by load() as a missing value


def _from_file(path):
    """ROUTER_USER / ROUTER_PASS from a KEY=VALUE file. Other keys are ignored."""
    if not os.path.exists(path):
        raise _failure("secrets file not found: " + path)
    values = {}
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values.get("ROUTER_USER", ""), values.get("ROUTER_PASS", "")


def load(root):
    """(host, user, password) according to router.conf."""
    cfg = configparser.ConfigParser(interpolation=None)
    try:
        if not cfg.read(os.path.join(root, CONFIG), encoding="utf-8"):
            raise _failure("config not found: " + CONFIG)
        cfg.read(os.path.join(root, LOCAL_CONFIG), encoding="utf-8")  # optional
    except configparser.Error as e:  # e.g. both secrets blocks uncommented: duplicate `source`
        raise _failure("bad config: %s" % e)

    host = cfg.get("router", "host", fallback="").strip()
    source = cfg.get("secrets", "source", fallback="").strip()
    if source == "file":
        path = os.path.expanduser(cfg.get("secrets", "path", fallback="").strip())
        if not path:
            raise _failure("secrets.path not set in " + CONFIG)
        path = os.path.join(root, path)  # relative paths resolve against the project root
        user, password = _from_file(path)
        names = ("ROUTER_USER", "ROUTER_PASS")
    elif source == "systemd":
        # The unit loads each named credential with LoadCredentialEncrypted=<name>; systemd
        # decrypts them into a RAM-only folder private to the unit and passes that folder
        # in $CREDENTIALS_DIRECTORY. No plaintext ever touches the disk.
        names = (cfg.get("secrets", "user_credential", fallback="").strip() or "router-user",
                 cfg.get("secrets", "pass_credential", fallback="").strip() or "router-pass")
        base = os.environ.get("CREDENTIALS_DIRECTORY", "")
        if not base:
            raise _failure("source = systemd but $CREDENTIALS_DIRECTORY is not set: run under a "
                           "unit with LoadCredentialEncrypted=%s and %s" % names)
        user, password = (_read(os.path.join(base, name)) for name in names)
    else:
        raise _failure("secrets.source must be file or systemd (got %r); set it in %s"
                       % (source, LOCAL_CONFIG))

    missing = [name for name, value in (("router.host", host), (names[0], user),
                                        (names[1], password)) if not value]
    if missing:
        raise _failure("missing: " + ", ".join(missing))
    return host, user, password
