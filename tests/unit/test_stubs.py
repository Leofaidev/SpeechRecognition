"""CHK-03: all non-Windows stub modules raise NotImplementedError with a message."""

import pytest


# ── Linux stubs ────────────────────────────────────────────────────────────────

class TestLinuxStubs:
    def test_data_dirs_get_app_dir(self):
        from platforms.linux.data_dirs import DataDirs
        with pytest.raises(NotImplementedError, match="linux"):
            DataDirs().get_app_dir()

    def test_data_dirs_ensure_app_dir(self):
        from platforms.linux.data_dirs import DataDirs
        with pytest.raises(NotImplementedError, match="linux"):
            DataDirs().ensure_app_dir()

    def test_installer_build(self):
        from platforms.linux.installer import Installer
        with pytest.raises(NotImplementedError, match="linux"):
            Installer().build_installer("wsp.spec", "out/")

    def test_auto_start_enable(self):
        from platforms.linux.auto_start import AutoStart
        with pytest.raises(NotImplementedError, match="linux"):
            AutoStart().enable("/app/app")

    def test_auto_start_disable(self):
        from platforms.linux.auto_start import AutoStart
        with pytest.raises(NotImplementedError, match="linux"):
            AutoStart().disable()

    def test_auto_start_is_enabled(self):
        from platforms.linux.auto_start import AutoStart
        with pytest.raises(NotImplementedError, match="linux"):
            AutoStart().is_enabled()

    def test_tray_create(self):
        from platforms.linux.tray import Tray
        with pytest.raises(NotImplementedError, match="linux"):
            Tray().create("icon.png", [])

    def test_hotkeys_register(self):
        from platforms.linux.hotkeys import Hotkeys
        with pytest.raises(NotImplementedError, match="linux"):
            Hotkeys().register("ctrl+r", lambda: None)

    def test_accelerator_list_devices(self):
        from platforms.linux.accelerator import Accelerator
        with pytest.raises(NotImplementedError):
            Accelerator().list_devices()

    def test_device_enum_list_devices(self):
        from platforms.linux.device_enum import DeviceEnum
        with pytest.raises(NotImplementedError, match="linux"):
            DeviceEnum().list_devices()


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
