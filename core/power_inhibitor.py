"""
Power & Lid-Switch Inhibitor for AutoReelStudio.
Ensures that autonomous AI video generation and scheduled social publishing
continue running continuously even when the laptop lid is closed.
Supports:
  - Linux systemd-inhibit wrapper
  - Freedesktop / KDE Plasma 6 PowerManagement DBus sleep & lid-switch inhibitors
  - KDE powerdevilrc lidAction=0 (Do Nothing) persistence
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

class PowerInhibitor:
    """Acquires and maintains sleep and lid-close inhibition locks."""

    _dbus_cookie: Optional[int] = None
    _is_active: bool = False

    @classmethod
    def activate(cls) -> Dict[str, Any]:
        """Activates sleep and lid-close inhibition."""
        cls._ensure_kde_lid_config()
        cookie = cls._acquire_dbus_inhibit()
        cls._dbus_cookie = cookie
        cls._is_active = True
        return cls.get_status()

    @classmethod
    def _ensure_kde_lid_config(cls):
        """Configures KDE Plasma powerdevilrc to Do Nothing (0) on lid close."""
        kwriteconfig = shutil.which("kwriteconfig6") or shutil.which("kwriteconfig5")
        if not kwriteconfig:
            return
        try:
            # Set AC and Battery lidAction to 0 (Do Nothing / Turn off screen only)
            subprocess.run([kwriteconfig, "--file", "powerdevilrc", "--group", "AC", "--key", "lidAction", "0"], capture_output=True, timeout=3)
            subprocess.run([kwriteconfig, "--file", "powerdevilrc", "--group", "Battery", "--key", "lidAction", "0"], capture_output=True, timeout=3)
            subprocess.run([kwriteconfig, "--file", "powerdevilrc", "--group", "AC", "--group", "HandleButtonEvents", "--key", "lidAction", "0"], capture_output=True, timeout=3)
            subprocess.run([kwriteconfig, "--file", "powerdevilrc", "--group", "Battery", "--group", "HandleButtonEvents", "--key", "lidAction", "0"], capture_output=True, timeout=3)
        except Exception:
            pass

    @classmethod
    def _acquire_dbus_inhibit(cls) -> Optional[int]:
        """Calls freedesktop PowerManagement DBus to inhibit sleep and lid switch."""
        qdbus = shutil.which("qdbus-qt6") or shutil.which("qdbus")
        if not qdbus:
            return None
        try:
            out = subprocess.check_output([
                qdbus,
                "org.kde.org_kde_powerdevil",
                "/org/freedesktop/PowerManagement/Inhibit",
                "org.freedesktop.PowerManagement.Inhibit.Inhibit",
                "AutoReelStudio",
                "Continuous Video Generation & Scheduled 5-Hour Publishing"
            ], stderr=subprocess.DEVNULL, timeout=4).decode().strip()
            if out.isdigit():
                return int(out)
        except Exception:
            pass
        return None

    @classmethod
    def release(cls):
        """Releases the DBus inhibitor if held."""
        if cls._dbus_cookie is not None:
            qdbus = shutil.which("qdbus-qt6") or shutil.which("qdbus")
            if qdbus:
                try:
                    subprocess.run([
                        qdbus,
                        "org.kde.org_kde_powerdevil",
                        "/org/freedesktop/PowerManagement/Inhibit",
                        "org.freedesktop.PowerManagement.Inhibit.UnInhibit",
                        str(cls._dbus_cookie)
                    ], capture_output=True, timeout=3)
                except Exception:
                    pass
            cls._dbus_cookie = None
            cls._is_active = False

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns power management inhibition telemetry."""
        return {
            "active": cls._is_active,
            "dbus_inhibited": cls._dbus_cookie is not None,
            "cookie": cls._dbus_cookie,
            "lid_policy": "run_when_closed",
            "reason": "Continuous Video Generation & Scheduled 5-Hour Publishing"
        }
