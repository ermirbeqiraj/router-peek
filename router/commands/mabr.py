"""IPTV multicast ABR status: sessions and multicast bitrates."""
from core.jsparse import records

PAGE = "/html/bbsp/mabr/mabr.asp"  # Informazioni > M-ABR

MABR = ("Domain", "Status", "SessionsNumber", "MinSessionsNumber", "MaxSessionsNumber",
        "MulticastBitrate", "MinMulticastBitrate", "MaxMulticastBitrate", "Mcast_frame")


def run(session):
    return {"mabr": records(session.get(PAGE), "stMabr", MABR, min_count=1)}
