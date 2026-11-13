"""Router identity and health: model, firmware, serial, MACs, uptime, CPU/mem, NAT sessions."""
from core.jsparse import records, var

PAGE = "/html/ssmp/deviceinfo/deviceinfo.asp"  # Informazioni > Dispositivo

DEVICE = ("domain", "SerialNumber", "HardwareVersion", "SoftwareVersion", "ModelName",
          "VendorID", "ReleaseTime", "Mac", "Description", "ManufactureInfo", "DeviceAlias",
          "specsn", "reuseCycles", "reuseStatus", "X_HW_WanMac")


def run(session):
    page = session.get(PAGE)
    device = records(page, "stDeviceInfo", DEVICE, min_count=1)[0]
    device["X_HW_WanMac"] = device["X_HW_WanMac"].split()
    return {
        "device": device,
        "status": {name: var(page, name) for name in
                   ("dev_uptime", "cpuUsed", "memUsed", "NatSessionInfo", "systemdsttime")},
    }
