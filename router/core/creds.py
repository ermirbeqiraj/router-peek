"""Credential lookup, driven by <project>/router.conf. The only place that touches secrets.

New sources (OS keyring, systemd credentials) are added as another branch in load().
"""
import configparser
import os

CONFIG = "router.conf"


def _failure(msg):
    from core.client import failure
    return failure(msg)


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
    else:
        raise _failure("unsupported secrets source in %s: %r" % (CONFIG, source))

    missing = [name for name, value in (("router.host", host), ("ROUTER_USER", user),
                                        ("ROUTER_PASS", password)) if not value]
    if missing:
        raise _failure("missing: " + ", ".join(missing))
    return host, user, password
