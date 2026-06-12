"""CHK-03: non-Windows platform modules — Linux implemented, macOS still stubs."""

import os
import pytest


# ── Linux platform (fully implemented) ────────────────────────────────────────

class TestLinuxPlatform:
    def test_data_dirs_get_app_dir_returns_string(self):
        from platforms.linux.data_dirs import DataDirs
        result = DataDirs().get_app_dir()
        assert isinstance(result, str)
        assert "SpeechRecognition" in result

    def test_data_dirs_ensure_app_dir_returns_string(self, tmp_path):
        from platforms.linux.data_dirs import DataDirs
        old_xdg = os.environ.get("XDG_DATA_HOME")
        os.environ["XDG_DATA_HOME"] = str(tmp_path)
        try:
            result = DataDirs().ensure_app_dir()
            assert isinstance(result, str)
            assert os.path.isdir(result)
        finally:
            if old_xdg is None:
                os.environ.pop("XDG_DATA_HOME", None)
            else:
                os.environ["XDG_DATA_HOME"] = old_xdg

    def test_installer_build_raises(self):
        from platforms.linux.installer import Installer
        with pytest.raises(NotImplementedError):
            Installer().build_installer("wsp.spec", "out/")

    def test_auto_start_roundtrip(self, tmp_path):
        from platforms.linux.auto_start import AutoStart
        old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(tmp_path)
        try:
            a = AutoStart()
            assert a.is_enabled() is False
            a.enable("/usr/bin/app")
            assert a.is_enabled() is True
            a.disable()
            assert a.is_enabled() is False
        finally:
            if old_xdg is None:
                os.environ.pop("XDG_CONFIG_HOME", None)
            else:
                os.environ["XDG_CONFIG_HOME"] = old_xdg

    def test_tray_create_no_raise(self):
        from platforms.linux.tray import Tray
        Tray().create("icon.png", [])  # wrapped in try/except, must not raise

    def test_hotkeys_register_no_raise(self):
        from platforms.linux.hotkeys import Hotkeys
        Hotkeys().register("ctrl+r", lambda: None)  # wrapped in try/except

    def test_accelerator_list_devices_returns_list(self):
        from platforms.linux.accelerator import Accelerator
        result = Accelerator().list_devices()
        assert isinstance(result, list)

    def test_device_enum_list_devices(self):
        pyaudio = pytest.importorskip("pyaudio")  # skip if pyaudio not installed
        from platforms.linux.device_enum import DeviceEnum
        result = DeviceEnum().list_devices()
        assert isinstance(result, list)


# ── macOS stubs ────────────────────────────────────────────────────────────────

class TestMacOSStubs:
    def test_data_dirs_get_app_dir(self):
        from platforms.macos.data_dirs import DataDirs
        with pytest.raises(NotImplementedError, match="macos"):
            DataDirs().get_app_dir()

    def test_data_dirs_ensure_app_dir(self):
        from platforms.macos.data_dirs import DataDirs
        with pytest.raises(NotImplementedError, match="macos"):
            DataDirs().ensure_app_dir()

    def test_installer_build(self):
        from platforms.macos.installer import Installer
        with pytest.raises(NotImplementedError, match="macos"):
            Installer().build_installer("wsp.spec", "out/")

    def test_auto_start_enable(self):
        from platforms.macos.auto_start import AutoStart
        with pytest.raises(NotImplementedError, match="macos"):
            AutoStart().enable("/app/app")

    def test_tray_create(self):
        from platforms.macos.tray import Tray
        with pytest.raises(NotImplementedError, match="macos"):
            Tray().create("icon.png", [])

    def test_hotkeys_register(self):
        from platforms.macos.hotkeys import Hotkeys
        with pytest.raises(NotImplementedError, match="macos"):
            Hotkeys().register("ctrl+r", lambda: None)

    def test_accelerator_list_devices(self):
        from platforms.macos.accelerator import Accelerator
        with pytest.raises(NotImplementedError):
            Accelerator().list_devices()

    def test_device_enum_list_devices(self):
        from platforms.macos.device_enum import DeviceEnum
        with pytest.raises(NotImplementedError, match="macos"):
            DeviceEnum().list_devices()


# ── Windows stubs (methods not yet implemented) ────────────────────────────────

class TestWindowsStubs:
    def test_installer_build_raises(self):
        from platforms.windows.installer import Installer
        with pytest.raises(NotImplementedError):
            Installer().build_installer("wsp.spec", "out/")

    def test_auto_start_enable_raises(self):
        from platforms.windows.auto_start import AutoStart
        with pytest.raises(NotImplementedError):
            AutoStart().enable("C:\\app\\app.exe")

    def test_tray_create_raises(self):
        from platforms.windows.tray import Tray
        with pytest.raises(NotImplementedError):
            Tray().create("icon.png", [])

    def test_hotkeys_register_raises(self):
        from platforms.windows.hotkeys import Hotkeys
        with pytest.raises(NotImplementedError):
            Hotkeys().register("ctrl+r", lambda: None)

    def test_accelerator_list_raises(self):
        from platforms.windows.accelerator import Accelerator
        with pytest.raises(NotImplementedError):
            Accelerator().list_devices()


# ── platforms.__init__ ─────────────────────────────────────────────────────────

class TestPlatformInit:
    def test_get_platform_name_returns_string(self):
        from platforms import get_platform_name
        name = get_platform_name()
        assert isinstance(name, str)
        assert name in ("windows", "linux", "macos", "win32", "darwin")
