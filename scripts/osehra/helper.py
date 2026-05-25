"""Interactive `iris session` driver for the VistA install.

Cleaned, IRIS-only Python 3 fork of WorldVistA/VistA `Python/vista/OSEHRAHelper.py`
(submodule pin b7aecb9), per spec docs/vista-iris-container-spec-v3.md §12.

Removed from upstream:
  * Windows/telnet (`ConnectWinCache`), GT.M (`ConnectLinuxGTM`), and SSH
    (`ConnectRemoteSSH`) connection classes;
  * the `chardet` dependency and Python-2 `unicode`/`from builtins` shims;
  * the `%SYS.MONLBL` / GT.M coverage machinery (test-only, not install).
Modernized: spawns `iris session <instance> -U <namespace>` (not the legacy
`irissession`); Python 3 only; fixed ISO-8859-1 codec.

The expect surface (write / wait / wait_re / multiwait / IEN / getenv) is kept
byte-for-byte compatible so the proven install sequences in the step modules
(scripts/osehra/steps_*.py) run unchanged.
"""
import codecs
import logging
import re

import pexpect

ENCODING = "ISO-8859-1"


class InstallError(Exception):
    """Raised when VistA does not emit an expected prompt (fail loud)."""


class PROMPT(object):
    """Sentinel: wait for the namespace prompt (e.g. ``VISTA>``)."""


class IRISSession(object):
    """Drives one interactive ``iris session IRIS -U VISTA`` over pexpect."""

    def __init__(self, logfile, instance="IRIS", namespace="VISTA"):
        self.namespace = namespace or "VISTA"
        self.prompt = self.namespace + ">"
        self.type = "iris"
        self.lastconnection = ""
        self.IENumber = ""
        self.boxvol = ""
        command = "iris session %s -U %s" % (instance, self.namespace)
        self.connection = pexpect.spawn(
            command, timeout=None, encoding=ENCODING, codec_errors="ignore"
        )
        self.connection.logfile_read = codecs.open(
            logfile, "w", encoding="utf-8", errors="ignore"
        )

    # -- low-level I/O ------------------------------------------------------
    def write(self, command):
        self.connection.send(command + "\r")
        logging.debug("write: %s", command)

    def wait(self, command, tout=15):
        """Wait for a literal string (or PROMPT)."""
        if command is PROMPT:
            command = self.prompt
        if self.connection.expect_exact(command, tout) == -1:
            raise InstallError("expected: %s" % command)
        self.lastconnection = self.connection.before or ""
        return 1

    def wait_re(self, command, timeout=15):
        """Wait for a regular expression (or PROMPT)."""
        if command is PROMPT:
            command = self.prompt
        if not timeout:
            timeout = -1
        self.connection.expect(re.compile(command, re.I), timeout)
        self.lastconnection = self.connection.before or ""

    def multiwait(self, options, tout=15):
        """Wait for any of ``options`` (regex); return the matched index."""
        if not isinstance(options, list):
            raise InstallError("multiwait expects a list")
        index = self.connection.expect(options, tout)
        if index == -1:
            raise InstallError("expected one of: %s" % options)
        self.lastconnection = self.connection.before or ""
        return index

    def expect(self, command, tout=15):
        if isinstance(command, list):
            return self.multiwait(command, tout)
        return self.wait_re(command, tout)

    # -- higher-level helpers used by the step modules ----------------------
    def getenv(self, volume):
        # Query the box:volume pair from the OS layer.
        self.write("D GETENV^%ZOSV W Y")
        self.wait_re(volume + r":.+\s", None)
        self.boxvol = (self.connection.after or "").strip()

    def IEN(self, file, objectname):
        # Resolve a record's internal entry number via FileMan inquiry.
        self.write("S DUZ=1 D Q^DI")
        self.wait("OPTION")
        self.write("5")
        self.wait_re("FILE:")
        self.write(file)
        self.wait(file + " NAME")
        self.write(objectname + "\r")
        self.wait_re("CAPTIONED OUTPUT?")
        self.write("N")
        self.wait_re("PRINT FIELD")
        self.write("NUMBER\r")
        self.wait("Heading")
        self.write("")
        self.wait("DEVICE")
        self.write("")
        self.wait_re("\n[0-9]+")
        self.IENumber = (self.connection.after or "").lstrip("\r\n")
        self.write("")

    def close(self):
        """Halt the session and release its IRIS license slot.

        IRIS Community caps concurrent processes, so a step that opens several
        connections must close each before the next (else LICENSE LIMIT EXCEEDED).
        The phases drive this via :func:`session.release`, which also waits for
        EOF so the license deregisters synchronously (log E8).
        """
        try:
            self.write("h")
        except Exception:
            pass
        try:
            self.connection.close(force=True)
        except Exception:
            pass


def ConnectToMUMPS(logfile, instance="IRIS", namespace="VISTA",
                   location="127.0.0.1", remote_conn_details=None):
    """IRIS-only connection factory (upstream was multi-platform)."""
    return IRISSession(logfile, instance, namespace)
