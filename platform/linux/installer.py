from platform.base.installer import InstallerBase

_PLATFORM = 'linux'

class Installer(InstallerBase):
    def build_installer(self, spec_file: str, output_dir: str) -> str:
        raise NotImplementedError(
            f"Installer is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def check_disk_space(self, path: str, required_bytes: int) -> bool:
        raise NotImplementedError(
            f"Installer is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )
