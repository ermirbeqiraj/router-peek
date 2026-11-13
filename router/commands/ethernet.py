"""Physical ports: LAN port link state/speed and counters, Ethernet-WAN port, router LAN MACs."""
from core.jsparse import records

PAGE = "/html/amp/ethinfo/ethinfo.asp"  # Informazioni > Ethernet

PORT = ("domain", "Mode", "Speed", "Status", "OptEthMode")
TRAFFIC = ("domain", "txPackets", "txPackets_H", "txGoodBytes", "txGoodBytes_H", "txBadBytes",
           "txBadBytes_H", "rxPackets", "rxPackets_H", "rxGoodBytes", "rxGoodBytes_H",
           "rxBadBytes", "rxBadBytes_H")
COUNTERS = ("domain", "ErrorsReceived", "ErrorsSent", "MulticastPacketsReceived",
            "MulticastPacketsSent")
BAD_FRAMES = ("domain", "RcvFrame_Undersize", "RcvTooLong", "RcvFragmentFrame", "RcvJabbersFrame",
              "RcvFcsErrFrame", "RcvAlignErrFrame", "MacRxErrFrame", "CarrierSenseErrCnt",
              "ExcessCollisionFrame", "MacSendErrFrame")
WAN_PORT = ("domain", "Mode", "Speed", "Status")
WAN_TRAFFIC = ("domain", "BytesReceived", "PacketsReceived", "BytesSent", "PacketsSent")
MACS = ("domain", "LanMac", "WLanMac")


def run(session):
    page = session.get(PAGE)
    return {
        "lan_ports": records(page, "GEInfo", PORT, min_count=1),
        "lan_traffic": records(page, "LANStats", TRAFFIC),
        "lan_counters": records(page, "userLanStates", COUNTERS),
        "lan_bad_frames": records(page, "IncorrectStats", BAD_FRAMES),
        "wan_port": records(page, "WanEthInfo", WAN_PORT),
        "wan_traffic": records(page, "WanEthStats", WAN_TRAFFIC),
        "macs": records(page, "DeviceLanMAC", MACS),
    }
