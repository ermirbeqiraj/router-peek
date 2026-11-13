"""DSL line: sync rates, noise margins, attenuation, profile, error counters."""
from core.jsparse import records

PAGE = "/html/ssmp/deviceinfo/dslinfo.asp"  # Informazioni > DSL

LINE = ("domain", "Status", "UpstreamCurrRate", "DownstreamCurrRate", "UpstreamMaxRate",
        "DownstreamMaxRate", "UpstreamNoiseMargin", "DownstreamNoiseMargin", "StandardUsed",
        "ModulationType", "UpstreamAttenuation", "DownstreamAttenuation", "UpstreamPower",
        "DownstreamPower", "ShowtimeStart", "X_Sra", "VectoringState", "X_AllowedProfiles",
        "X_ConfigMode", "DataPath", "X_UpInterleaveDepth", "InterleaveDepth",
        "X_InterleaveDelayUs", "X_InterleaveDelayDs", "ACTINP", "ACTINPus")
ERRORS = ("domain", "SeverelyErroredSecs", "ATUCSeverelyErroredSecs", "ErroredSecs",
          "ATUCErroredSecs", "ATUCCRCErrors", "CRCErrors", "ATUCFECErrors", "FECErrors")
SNR = ("domain", "UpstreamNoiseMargin", "DownstreamNoiseMargin")
PROFILE = ("domain", "CurrentProfile", "FirmwareVersion", "X_ATUCACTINPROC", "X_ATURACTINPROC")
CHANNEL = ("domain", "DataPath", "X_UpInterleaveDepth", "InterleaveDepth")


def run(session):
    page = session.get(PAGE)
    return {
        "line": records(page, "DSLInfo", LINE, min_count=1),
        "errors": records(page, "DSLInfoTEST", ERRORS),
        "snr": records(page, "DSLInfoSNR", SNR),
        "profile": records(page, "DSLInfoADD", PROFILE),
        "channel": records(page, "stDSLInfoChannelType", CHANNEL),
    }
