"""Credential lookup, driven by <project>/router.conf. The only place that touches secrets.

New sources (OS keyring, systemd credentials) are added as another branch in load().
"""
import configparser
import os

CONFIG = "router.conf"


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
    if not cfg.read(os.path.join(root, CONFIG), encoding="utf-8"):
        raise _failure("config not found: " + CONFIG)

    host = cfg.get("router", "host", fallback="").strip()
    source = cfg.get("secrets", "source", fallback="").strip()
    if source == "file":
        path = os.path.expanduser(cfg.get("secrets", "path", fallback="").strip())
        if not path:
            raise _failure("secrets.path not set in " + CONFIG)
        path = os.path.join(root, path)  # relative paths resolve against the project root
        user, password = _from_file(path)
    elif source == "systemd":
        # The unit sets LoadCredentialEncrypted=ROUTER_USER/ROUTER_PASS; systemd decrypts
        # each to <dir>/ROUTER_USER, <dir>/ROUTER_PASS (under /run/credentials/<unit>/)
        # before this process starts. No plaintext secret ever touches the disk.
        base = cfg.get("secrets", "dir", fallback="").strip()
        if not base:
            raise _failure("secrets.dir not set in " + CONFIG)
        base = os.path.join(root, base)  # relative paths resolve against the project root
        user = _read(os.path.join(base, "ROUTER_USER"))
        password = _read(os.path.join(base, "ROUTER_PASS"))
    else:
        raise _failure("unsupported secrets source in %s: %r" % (CONFIG, source))

    missing = [name for name, value in (("router.host", host), ("ROUTER_USER", user),
                                        ("ROUTER_PASS", password)) if not value]
    if missing:
        raise _failure("missing: " + ", ".join(missing))
    return host, user, password
