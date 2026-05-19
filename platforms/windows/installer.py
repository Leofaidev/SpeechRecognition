import shutil

from platforms.base.installer import InstallerBase


class Installer(InstallerBase):

    def build_installer(self, spec_file: str, output_dir: str) -> str:
        raise NotImplementedError("Installer.build_installer will be implemented in Phase 7")

    def check_disk_space(self, path: str, required_bytes: int) -> bool:
        usage = shutil.disk_usage(path)
        return usage.free >= required_bytes
