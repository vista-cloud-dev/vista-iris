"""Shared configuration + connection bootstrap for the VistA install steps.

All values are overridable via environment variables so the Dockerfile / Makefile
can parameterize the build without editing code (spec §4, §11.4).
"""
import os

INSTANCE = os.environ.get("VISTA_INSTANCE", "IRIS")
NAMESPACE = os.environ.get("VISTA_NAMESPACE", "VISTA")
USERNAME = os.environ.get("VISTA_USERNAME", "_SYSTEM")
PASSWORD = os.environ.get("VISTA_PASSWORD", "SYS")
SITE_NAME = os.environ.get("VISTA_SITE_NAME", "VISTA HEALTH CARE")
SITE_NUMBER = os.environ.get("VISTA_SITE_NUMBER", "6161")
VOLUME_SET = os.environ.get("VISTA_VOLUME_SET", "ROU")
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
    return v
