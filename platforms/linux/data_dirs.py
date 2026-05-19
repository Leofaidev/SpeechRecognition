from platforms.base.data_dirs import DataDirsBase

_PLATFORM = 'linux'

class DataDirs(DataDirsBase):
    def get_app_dir(self) -> str:
        raise NotImplementedError(
            f"DataDirs is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )

    def ensure_app_dir(self) -> str:
        raise NotImplementedError(
            f"DataDirs is not implemented for platform '{_PLATFORM}'. "
            "This stub exists to support future ports (Spec Section 17)."
        )
