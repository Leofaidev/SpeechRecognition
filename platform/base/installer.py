import abc


class InstallerBase(abc.ABC):

    @abc.abstractmethod
    def build_installer(self, spec_file: str, output_dir: str) -> str:
        """Build a distributable installer and return the path to the produced file."""

    @abc.abstractmethod
    def check_disk_space(self, path: str, required_bytes: int) -> bool:
        """Return True if at least required_bytes are available at path."""
