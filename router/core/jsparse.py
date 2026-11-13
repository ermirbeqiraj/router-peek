"""Pull data out of the router's pages, which embed it as JavaScript.

Data comes as `new Ctor("..", "..")` calls. Field names are pinned per command rather than
read from the page's `function Ctor(...)`, because the firmware defines some constructors
twice behind ISP-specific branches and neither copy matches the data.

Strings are double-quoted with every non-alphanumeric byte \\xNN-escaped,
e.g. new stDeviceInfo("InternetGatewayDevice.DeviceInfo","3F1A\\x2eA",...).
"""
import re

_ARG = re.compile(r'\s*"((?:[^"\\]|\\.)*)"\s*([,)])')

# Field names that may carry credentials. Matching fields are dropped, never output.
SECRET = re.compile(r"pass|pwd|psk|secret|key|token|username", re.I)


class FormatError(Exception):
    """The page no longer has the shape the parser was written for."""


def unescape(s):
    out = bytearray()
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            n = s[i + 1]
            if n == "x" and re.fullmatch(r"[0-9a-fA-F]{2}", s[i + 2:i + 4]):
                out.append(int(s[i + 2:i + 4], 16))
                i += 4
                continue
            out += {"n": b"\n", "r": b"\r", "t": b"\t"}.get(n, n.encode("utf-8"))
            i += 2
            continue
        out += c.encode("utf-8")
        i += 1
    return out.decode("utf-8", "replace")


def new_objects(text, ctor):
    """Argument lists of every `new <ctor>("..", "..")` in text, unescaped.

    Only calls whose arguments are all string literals are returned; the pages also
    contain `new Ctor(variable, ...)` inside their own JS logic, which is not data.
    """
    result = []
    for m in re.finditer(r"new\s+%s\s*\(" % re.escape(ctor), text):
        args, pos, closed = [], m.end(), False
        while True:
            a = _ARG.match(text, pos)
            if not a:
                break
            args.append(unescape(a.group(1)))
            pos = a.end()
            if a.group(2) == ")":
                closed = True
                break
        if closed:
            result.append(args)
    return result


def records(text, ctor, fields, min_count=0):
    """Instances of ctor as dicts, keyed by the command's pinned `fields`.

    Strict: every instance must have exactly len(fields) arguments, and there must be at
    least min_count instances. Fields named None, or whose name looks like a secret,
    are dropped.
    """
    out = []
    for args in new_objects(text, ctor):
        if len(args) != len(fields):
            raise FormatError("%s(): %d args, expected %d" % (ctor, len(args), len(fields)))
        out.append({f: v for f, v in zip(fields, args) if f and not SECRET.search(f)})
    if len(out) < min_count:
        raise FormatError("%s(): %d instances, expected at least %d" % (ctor, len(out), min_count))
    return out


def var(text, name):
    """Value of the first `var <name> = '...'` (single-quoted). Strict: must exist."""
    m = re.search(r"var\s+%s\s*=\s*'((?:[^'\\]|\\.)*)'" % re.escape(name), text)
    if not m:
        raise FormatError("var %s not found" % name)
    return unescape(m.group(1))
