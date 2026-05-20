"""Audio device enumeration — delegates to the platform layer."""

from __future__ import annotations

import sys

from platforms.base.device_enum import DeviceInfo, DeviceType  # re-export for convenience


def _get_platform_enum():
    if sys.platform == "win32":
        from platforms.windows.device_enum import DeviceEnum
        return DeviceEnum()
    elif sys.platform.startswith("linux"):
        from platforms.linux.device_enum import DeviceEnum
        return DeviceEnum()
    elif sys.platform == "darwin":
        from platforms.macos.device_enum import DeviceEnum
        return DeviceEnum()
    else:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")


def list_devices() -> list[DeviceInfo]:
    """Return all available audio input devices on the current platform."""
    return _get_platform_enum().list_devices()


def find_device(partial_name: str) -> DeviceInfo | None:
    """Case-insensitive partial-name match; returns the first match or None."""
    return _get_platform_enum().find_device(partial_name)


__all__ = ["DeviceInfo", "DeviceType", "list_devices", "find_device"]
