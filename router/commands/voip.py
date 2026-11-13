"""Phone lines: number, registration status, call state, last register error."""
from core.jsparse import records

# Informazioni > VoIP is voipmaintain.asp, which only JS-redirects here for SIP.
PAGE = "/html/voip/status/sipvoipmaintain.asp"

LINE = ("Domain", "DirectoryNumber", "PhyReferenceList", "Status", "CallState", "RegisterError")
URI = ("Domain", "URI")
PROFILE = ("Domain", "Region")
# stAuth (SIP auth username) is deliberately not read.


def run(session):
    page = session.get(PAGE)
    return {
        "lines": records(page, "stLine", LINE),
        "uris": records(page, "stLineURI", URI),
        "profile": records(page, "stProfile", PROFILE),
    }
