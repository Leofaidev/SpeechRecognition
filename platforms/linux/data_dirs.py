import os

from platforms.base.data_dirs import DataDirsBase


class DataDirs(DataDirsBase):

    def get_app_dir(self) -> str:
        xdg = os.environ.get("XDG_DATA_HOME", "")
        base = xdg if xdg else os.path.join(os.path.expanduser("~"), ".local", "share")
        return os.path.join(base, self.APP_NAME)

    def ensure_app_dir(self) -> str:
        path = self.get_app_dir()
        os.makedirs(path, exist_ok=True)
        return path
