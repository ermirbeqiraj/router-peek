"""Internet-side connections (IP and PPP), their addresses, state, uptime and traffic counters."""
from core.jsparse import records

PAGE = "/html/bbsp/waninfo/waninfo.asp"                        # Informazioni > WAN
CONNECTIONS = "/html/bbsp/common/wan_list_cache_wan.asp"       # data feed of that page
IP_STATS = "/html/bbsp/common/get_wan_list_ipwanstat.asp"
PPP_STATS = "/html/bbsp/common/get_wan_list_pppwanstat.asp"

# Both carry one trailing argument beyond the page's own definition (unidentified: None).
# Credentials (IPoE name/password, PPP username/password) are pinned as None: never output.
WAN_IP = ("domain", "X_HW_VXLAN_Enable", "X_HW_OperateDisable", "ConnectionTrigger", "MACAddress",
          "Status", "LastConnErr", "RemoteWanInfo", "Name", "Enable", "EnableLanDhcp",
          "DstIPForwardingList", "ConnectionStatus", "Mode", "IPMode", "IPAddress", "SubnetMask",
          "Gateway", "NATEnable", "X_HW_NatType", "dnsstr", "VlanId", "MultiVlanID", "Pri8021",
          "VenderClassID", "ClientID", "ServiceList", "ExServiceList", "Tr069Flag", "MacId",
          "IPv4Enable", "IPv6Enable", "IPv6MultiCastVlan", "PriPolicy", "DefaultPri", "MaxMTUSize",
          "DHCPLeaseTime", "NTPServer", "TimeZoneInfo", "SIPServer", "StaticRouteInfo",
          "VendorInfo", "DHCPLeaseTimeRemaining", "Uptime", "DNSOverrideAllowed",
          "X_HW_LowerLayers", None, None, "X_HW_IGMPEnable", "X_HW_DscpToPbitTbl",
          "IPv4IPAddressSecond", "IPv4SubnetMaskSecond", "IPv4IPAddressThird",
          "IPv4SubnetMaskThird", "X_HW_NPTv6Enable", "X_HW_SpeedLimit_UP", "X_HW_SpeedLimit_DOWN",
          "X_HW_LteProfile", "X_HW_PingResponseEnable", "X_HW_PingResponseWhiteList",
          "IPForwardModeEnabled", "X_HW_EffectiveDNSServers", None)
WAN_PPP = ("domain", "X_HW_VXLAN_Enable", "X_HW_OperateDisable", "ConnectionTrigger", "MACAddress",
           "Status", "LastConnErr", "RemoteWanInfo", "Name", "Enable", "EnableLanDhcp",
           "DstIPForwardingList", "ConnectionStatus", "Mode", "IPAddress", "Gateway", "NATEnable",
           "X_HW_NatType", "dnsstr", None, None, "DialMode", "ConnectionControl", "VlanId",
           "MultiVlanID", "Pri8021", "LcpEchoReqCheck", "ServiceList", "ExServiceList",
           "Tr069Flag", "IdleDisconnectTime", "MacId", "IPv4Enable", "IPv6Enable",
           "IPv6MultiCastVlan", "PriPolicy", "DefaultPri", "MaxMRUSize", "PPPoEACName",
           "X_HW_IdleDetectMode", "Uptime", "DNSOverrideAllowed", "X_HW_LowerLayers",
           "PPPoESessionID", "X_HW_IGMPEnable", "StaticRouteInfo", "X_HW_DscpToPbitTbl", "Hurl",
           "Motm", "X_HW_BridgeEnable", "X_HW_NPTv6Enable", "X_HW_SpeedLimit_UP",
           "X_HW_SpeedLimit_DOWN", "X_HW_PingResponseEnable", "X_HW_PingResponseWhiteList",
           "IPForwardModeEnabled", "X_HW_EffectiveDNSServers", None)
# Only the first 11 of the definition's 15 parameters are sent.
STATS = ("domain", "BytesSent", "BytesReceived", "PacketsSent", "PacketsReceived", "UnicastSent",
         "UnicastReceived", "MulticastSent", "MulticastReceived", "BroadcastSent",
         "BroadcastReceived")


def run(session):
    session.get(PAGE)  # confirms the menu page still exists
    feed = session.get(CONNECTIONS)
    return {
        "ip": records(feed, "WanIP", WAN_IP),
        "ppp": records(feed, "WanPPP", WAN_PPP),
        "stats": records(session.get(IP_STATS), "WaninfoStats", STATS)
                 + records(session.get(PPP_STATS), "WaninfoStats", STATS),
    }
