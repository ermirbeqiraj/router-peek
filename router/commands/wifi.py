"""The router's own Wi-Fi: global switch, radios, SSIDs, per-SSID traffic, associated clients."""
from core.jsparse import records

PAGE = "/html/amp/wlaninfo/wlaninfo.asp"            # Informazioni > Wi-Fi
LIST = "/html/amp/common/wlan_list.asp"             # included by that page
CLIENTS = "/html/amp/wlaninfo/getassociateddeviceinfo.asp"

ENABLE = ("domain", "enable")
RADIO = ("domain", "OperatingFrequencyBand", "Enable")
SSID = ("domain", "enable", "name", "ssid", "BeaconType", "BasicEncrypt", "BasicAuth",
        "WPAEncrypt", "WPAAuth", "IEEE11iEncrypt", "IEEE11iAuth", "WPAand11iEncrypt",
        "WPAand11iAuth", "Channel", "LowerLayers", "X_HW_Standard", "RegulatoryDomain",
        "X_HW_HT20", "TransmitPower", "X_HW_ServiceEnable", "wlHide", "wmmEnable", "DeviceNum",
        "AutoChannelEnable")
PACKETS = ("domain", "totalBytesSent", "totalPacketsSent", "totalBytesReceived",
           "totalPacketsReceived")
ERRORS = ("domain", "errorsSent", "errorsReceived", "discardPacketsSent", "discardPacketsReceived")
CLIENT = ("domain", "AssociatedDeviceMACAddress", "X_HW_Uptime", "X_HW_RxRate", "X_HW_TxRate",
          "X_HW_RSSI", "X_HW_Noise", "X_HW_SNR", "X_HW_SingalQuality", "X_HW_WorkingMode",
          "X_HW_WMMStatus", "X_HW_PSMode", "X_HW_HighBandFlag", "AssociatedDeviceIPAddress",
          "HW_AssociatedDevicedescriptions", "X_HW_AntennaNum", "X_HW_11kSupported",
          "X_HW_11vSupported", "X_HW_DualBandSupported", "X_HW_BeamFormingSupported",
          "X_HW_11RSupported")


def run(session):
    page, lst = session.get(PAGE), session.get(LIST)
    radios = {r["domain"]: r for r in records(lst, "stRadio", RADIO, min_count=1)}  # listed twice
    return {
        "enabled": records(lst, "stWlanEnable", ENABLE, min_count=1)[0]["enable"],
        "radios": list(radios.values()),
        "ssids": records(page, "stWlan", SSID, min_count=1),
        "traffic": records(page, "stPacketInfo", PACKETS),
        "errors": records(page, "stStats", ERRORS),
        "clients": records(session.get(CLIENTS), "stAssociatedDevice", CLIENT),
    }
