"""Command registry: name -> module with run(session) returning JSON-serialisable data.

Each module's docstring first line is its description in `router help`.
"""
from commands import dsl, ethernet, hosts, info, mabr, voip, wan, wifi

COMMANDS = {
    "info": info,
    "hosts": hosts,
    "wifi": wifi,
    "wan": wan,
    "dsl": dsl,
    "ethernet": ethernet,
    "voip": voip,
    "mabr": mabr,
}
