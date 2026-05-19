import os

from platform.base.data_dirs import DataDirsBase


class DataDirs(DataDirsBase):

    def get_app_dir(self) -> str:
        local_app_data = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(local_app_data, self.APP_NAME)

    def ensure_app_dir(self) -> str:
        path = self.get_app_dir()
        os.makedirs(path, exist_ok=True)
        return path
