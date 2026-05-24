"""Shared configuration + connection bootstrap for the VistA install steps.

All values are overridable via environment variables so the Dockerfile / Makefile
can parameterize the build without editing code (spec §4, §11.4).
"""
import os

INSTANCE = os.environ.get("VISTA_INSTANCE", "IRIS")
NAMESPACE = os.environ.get("VISTA_NAMESPACE", "VISTA")
USERNAME = os.environ.get("VISTA_USERNAME", "_SYSTEM")
PASSWORD = os.environ.get("VISTA_PASSWORD", "SYS")
# DOMAIN is the messaging domain / DINIT site name (file #4.2) -- it must be
# punctuation-restricted (dots/dashes, NO spaces). INSTITUTION is the facility
# name (file #4), where spaces are fine. These are distinct in VistA.
DOMAIN = os.environ.get("VISTA_DOMAIN", "DEMO.OSEHRA.ORG")
INSTITUTION = os.environ.get("VISTA_INSTITUTION", "VISTA HEALTH CARE")
SITE_NUMBER = os.environ.get("VISTA_SITE_NUMBER", "6161")
# Volume-set name; on IRIS GETENV^%ZOSV reports "...^VISTA:IRIS", so "VISTA" is
# the anchor that yields box:volume pair "VISTA:IRIS".
VOLUME_SET = os.environ.get("VISTA_VOLUME_SET", "VISTA")
RPC_PORT = os.environ.get("VISTA_RPC_PORT", "9430")
HL7_PORT = os.environ.get("VISTA_HL7_PORT", "5026")
HFS_DIR = os.environ.get("VISTA_HFS_DIR", "/tmp")
VISTA_M_TAG = os.environ.get("VISTA_M_TAG", "FOIA")
LOG_DIR = os.environ.get("VISTA_LOG_DIR", "/tmp")


def connect(logname):
    """Spawn an ``iris session``, sign in if prompted, return at the prompt."""
    from helper import ConnectToMUMPS
    v = ConnectToMUMPS(os.path.join(LOG_DIR, logname), INSTANCE, NAMESPACE)
    # A local `iris session` may either drop straight to the namespace prompt
    # (OS authentication) or ask for credentials, depending on IRIS security.
    idx = v.multiwait(["Username:", v.prompt], 120)
    if idx == 0:
        v.write(USERNAME)
        v.wait("Password")
        v.write(PASSWORD)
        v.wait(v.prompt, 120)
    # The initial prompt was just consumed above. Emit a bare CR so exactly one
    # fresh prompt is pending: the OSEHRA steps assume each is entered at a
    # prompt, and the first one (e.g. startFileman) is wait-first. Harmless to
    # write-first steps -- their next non-prompt match skips this extra prompt.
    v.write("")
    return v
