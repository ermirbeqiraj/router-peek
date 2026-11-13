"""Devices the router knows on the LAN: name, IP, MAC, online state, port, link speed, lease."""
from core.jsparse import records

PAGE = "/html/bbsp/userdevinfo/getuserdevinfo.asp"  # Informazioni > Hosts (data feed)

# Neither of the page's two stUserDevInfoPTVDF() definitions matches the 14 args sent;
# names follow the TIM branch, 12 is the negotiated port speed, 13 is unidentified.
HOST = ("HostName", "DevType", "IpAddr", "MacAddr", "DevStatus", "Port", "Time", "Leasetion",
        "domain", "RealMacAddr", "TrafficRecvRate", "TrafficSendRate", "PortSpeed", None)


def run(session):
    return {"hosts": records(session.get(PAGE), "stUserDevInfoPTVDF", HOST, min_count=1)}
